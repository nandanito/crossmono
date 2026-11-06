"""Package a CrossMono release (ADR 0009, RELEASING.md): check the build, then write the release assets.

    python3 scripts/mono/package_release.py --tag 0.1.0-rc.1 --check-tag   # prints env= and rc= for the build
    CROSSMONO_RC=1 pio run -e papermono-gh_release_rc
    python3 scripts/mono/release_license.py --tag 0.1.0-rc.1 --env papermono-gh_release_rc --out LICENSE.txt
    python3 scripts/mono/package_release.py --tag 0.1.0-rc.1 --license LICENSE.txt --out dist [--summary <file>]

The tag picks the build: N.N.N is papermono-gh_release, N.N.N-rc.N is papermono-gh_release_rc with
CROSSMONO_RC=N. N.N.N must equal [crossmono] version in platformio.ini.

Before writing anything it checks the app image (magic byte, ESP32-S3 chip ID, "CrossMono-ESP32-<tag>", board tag),
the ELF, the full image (bootloader, partition table, blank NVS, otadata, and firmware.bin at
0x10000), the licence file (release_license.check: tag, both commits, the GPLv3 statement, every text), and
the flash-size gate. PlatformIO only prints a warning when it cannot write
firmware.factory.bin, and leaves an old one in place when firmware.bin comes from the build cache,
so a missing or stale full image fails here. The output folder must be new or empty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from pathlib import Path

import flash_slots
import partitions
import release_license
import size_gate
import version_flags

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ENV = "papermono-gh_release"
RC_ENV = "papermono-gh_release_rc"
BOARD = "papermono"  # src/network/FirmwareBoardTag.cpp
TAG = re.compile(r"(?P<version>\d+\.\d+\.\d+)(?:-rc\.(?P<rc>[1-9]\d*))?")
# assetName in OtaUpdater::checkForUpdate() (src/network/OtaUpdater.cpp); a longer name never matches.
OTA_ASSET_NAME_SIZE = 48

IMAGE_MAGIC = 0xE9
APP_OFFSET = 0x10000
FLASH_SIZE_16MB = 0x4  # high nibble of header byte 3 (esptool's flash size code)
ESP32S3_CHIP_ID = 0x0009  # esp_image_header_t.chip_id, bytes 12-13
USER_AGENT = b"CrossMono-ESP32-"  # src/network/HttpDownloader.cpp
BOARD_TAG = b"CROSSPOINT-BOARD-V1:" + BOARD.encode() + b";"
ELF_MAGIC = b"\x7fELF"


class PackageError(Exception):
    """The release cannot be packaged; the message says why."""


def chip_id(header: bytes) -> int | None:
    return struct.unpack_from("<H", header, 12)[0] if len(header) >= 14 else None


def build_for_tag(tag: str, version: str) -> tuple[str, str | None]:
    """(environment, release-candidate number or None) for a tag."""
    match = TAG.fullmatch(tag)
    if not match:
        raise PackageError(f"tag {tag!r} is not N.N.N or N.N.N-rc.N (VERSIONING.md: no 'v', rc from 1)")
    if match["version"] != version:
        raise PackageError(f"tag {tag} does not match [crossmono] version = {version} in platformio.ini")
    rc = match["rc"]
    return (RC_ENV if rc else RELEASE_ENV), rc


def asset_names(tag: str) -> dict[str, str]:
    names = {
        "app": f"crossmono-{tag}-{BOARD}.bin",
        "full": f"crossmono-{tag}-{BOARD}-full.bin",
        "elf": f"crossmono-{tag}-{BOARD}.elf",
        "license": f"crossmono-{tag}-LICENSE.txt",
    }
    if len(names["app"]) >= OTA_ASSET_NAME_SIZE:
        raise PackageError(f"{names['app']} is longer than the updater's {OTA_ASSET_NAME_SIZE - 1} characters")
    return names


def check_app(app: bytes, tag: str) -> list[str]:
    errors = []
    if app[:1] != bytes([IMAGE_MAGIC]):
        errors.append("firmware.bin does not start with the 0xE9 image magic byte")
    elif chip_id(app) != ESP32S3_CHIP_ID:
        errors.append(f"firmware.bin is not an ESP32-S3 image (chip ID {chip_id(app)})")
    # With the NUL, 0.1.0 does not match a 0.1.0-rc.1 or 0.1.0-dev+<sha> build.
    if USER_AGENT + tag.encode() + b"\0" not in app:
        versions = re.finditer(re.escape(USER_AGENT) + rb"([^\0]{1,40})\0", app)
        found = ", ".join(sorted({m.group(1).decode(errors="replace") for m in versions}))
        errors.append(f"firmware.bin is not version {tag} (found {found or 'no CrossMono version string'})")
    if BOARD_TAG not in app:
        errors.append(f"firmware.bin has no {BOARD_TAG.decode()} board tag")
    return errors


def check_full(full: bytes, app: bytes, table: list[partitions.Partition]) -> list[str]:
    """The checks in the 0.1.0 plan, question 4: what firmware.factory.bin must hold."""
    if len(full) != APP_OFFSET + len(app):
        return [
            f"firmware.factory.bin is {len(full):,} B, expected {APP_OFFSET + len(app):,} B "
            f"(0x10000 + firmware.bin): stale or not rebuilt; build without the cache (RELEASING.md)"
        ]
    errors = []
    if full[APP_OFFSET:] != app:
        errors.append("firmware.factory.bin does not end with this firmware.bin at 0x10000: stale or not rebuilt")
    if full[0] != IMAGE_MAGIC:
        errors.append("no bootloader at 0x0 of the full image (no 0xE9 magic byte)")
    elif full[3] >> 4 != FLASH_SIZE_16MB:
        errors.append(f"the bootloader header gives flash size code {full[3] >> 4:#x}, not 16 MB")
    elif chip_id(full) != ESP32S3_CHIP_ID:
        errors.append(f"the bootloader at 0x0 is not for the ESP32-S3 (chip ID {chip_id(full)})")
    try:
        flash = flash_slots.Flash(full)
        found = flash_slots.partitions(flash)
    except flash_slots.DecodeError as error:
        return errors + [f"full image: {error}"]
    if [(p.name, p.offset, p.size) for p in found] != [(p.name, p.offset, p.size) for p in table]:
        errors.append("the partition table at 0x8000 is not the one platformio.ini names for this environment")
        return errors
    nvs = next((p for p in table if p.subtype == "nvs"), None)
    if nvs and full[nvs.offset : nvs.end].count(0xFF) != nvs.size:
        errors.append(f"NVS ({nvs.offset:#x}-{nvs.end - 1:#x}) is not blank in the full image")
    label, slot, active = flash_slots.next_boot(found, flash_slots.otadata(flash, found))
    if active is None or slot is None or slot.offset != APP_OFFSET:
        errors.append(f"the otadata in the full image does not select the app at 0x10000 (it starts {label})")
    return errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(tag: str, full_name: str) -> dict:
    """ESP Web Tools manifest: one part, the full image at 0x0 (ADR 0009)."""
    return {
        "name": "CrossMono",
        "version": tag,
        "new_install_improv_wait_time": 0,  # the firmware has no Improv Serial
        "builds": [{"chipFamily": "ESP32-S3", "parts": [{"path": full_name, "offset": 0}]}],
    }


def package(
    tag: str,
    build_dir: Path | None,
    out: Path,
    summary: Path | None,
    license_file: Path,
    commits: tuple[str, str] | None = None,
) -> list[str]:
    """Check the build and the licence file, and write the assets; returns the asset names.

    commits is (source, SDK); by default the checkout's (release_license.commits).
    """
    version, _ = version_flags.read_versions(ROOT / "platformio.ini")
    env, _ = build_for_tag(tag, version)
    names = asset_names(tag)
    build_dir = build_dir or ROOT / ".pio" / "build" / env
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise PackageError(f"{out} is not an empty folder; old assets could be uploaded with the new ones")

    files = {
        "app": build_dir / "firmware.bin",
        "full": build_dir / "firmware.factory.bin",
        "elf": build_dir / "firmware.elf",
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        raise PackageError(f"missing from the {env} build: {', '.join(missing)}")
    if not license_file.is_file():
        raise PackageError(f"the licence file {license_file} is missing (scripts/mono/release_license.py)")
    commit, sdk = commits or release_license.commits(ROOT)
    app = files["app"].read_bytes()
    table = partitions.load(ROOT / partitions.env_partitions_file(ROOT / "platformio.ini", env))
    errors = check_app(app, tag) + check_full(files["full"].read_bytes(), app, table)
    if files["elf"].read_bytes()[:4] != ELF_MAGIC:
        errors.append("firmware.elf is not an ELF file")
    errors += release_license.check(license_file.read_text(encoding="utf-8"), tag, commit, sdk)
    if errors:
        raise PackageError("\n  ".join(["the build is not releasable:"] + errors))

    gate = ["--env", env, "--app", str(files["app"])] + (["--summary", str(summary)] if summary else [])
    if size_gate.main(gate) != 0:
        raise PackageError("the app image fails the flash-size gate")

    out.mkdir(parents=True, exist_ok=True)
    for key, source in [*files.items(), ("license", license_file)]:
        shutil.copyfile(source, out / names[key])
    (out / "manifest.json").write_text(json.dumps(manifest(tag, names["full"]), indent=2) + "\n")
    assets = sorted([*names.values(), "manifest.json"])
    (out / "SHA256SUMS").write_text("".join(f"{sha256(out / name)}  {name}\n" for name in assets))
    return assets + ["SHA256SUMS"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", required=True, help="release tag, e.g. 0.1.0 or 0.1.0-rc.1")
    parser.add_argument("--check-tag", action="store_true", help="only check the tag; print env= and rc=")
    parser.add_argument("--out", type=Path, help="new or empty folder for the assets")
    parser.add_argument("--license", type=Path, help="the licence file from release_license.py")
    parser.add_argument("--build-dir", type=Path, help="default: .pio/build/<env>")
    parser.add_argument("--summary", type=Path, help="file the size gate appends a Markdown line to")
    args = parser.parse_args(argv)
    try:
        if args.check_tag:
            version, _ = version_flags.read_versions(ROOT / "platformio.ini")
            env, rc = build_for_tag(args.tag, version)
            asset_names(args.tag)
            print(f"env={env}\nrc={rc or ''}")
            return 0
        if args.out is None or args.license is None:
            parser.error("--out and --license are required unless --check-tag is given")
        assets = package(args.tag, args.build_dir, args.out, args.summary, args.license)
    except (PackageError, release_license.LicenseError, version_flags.VersionError, OSError, ValueError) as error:
        print(f"package_release.py: {error}", file=sys.stderr)
        return 1
    print(f"Packaged CrossMono {args.tag} in {args.out}: {', '.join(assets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
