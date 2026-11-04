"""Check the release packager on synthetic images (scripts/mono/package_release.py, ADR 0009).

Run with python3 test/mono/test_package_release.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import binascii
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import package_release  # noqa: E402
import partitions  # noqa: E402
import version_flags  # noqa: E402

VERSION, _ = version_flags.read_versions(ROOT / "platformio.ini")
RC_TAG = f"{VERSION}-rc.1"
SLOT = 0x7F0000
TYPES = {"app": 0x00, "data": 0x01}
SUBTYPES = {"ota_0": 0x10, "ota_1": 0x11, "nvs": 0x02, "ota": 0x00, "coredump": 0x03, "spiffs": 0x82}


def table_bytes(csv: Path) -> bytes:
    rows = b""
    for p in partitions.load(csv):
        label = p.name.encode().ljust(16, b"\0")
        rows += b"\xaa\x50" + struct.pack("<BBII", TYPES[p.type], SUBTYPES[p.subtype], p.offset, p.size) + label
        rows += b"\0" * 4
    return rows + b"\xeb\xeb" + b"\xff" * 14 + hashlib.md5(rows).digest()


def otadata_entry(seq: int) -> bytes:
    """One esp_ota_select_entry_t as boot_app0.bin has it: seq, 20 FF label bytes, state UNDEFINED, CRC."""
    return struct.pack("<I", seq) + b"\xff" * 24 + struct.pack("<I", binascii.crc32(struct.pack("<I", seq), 0xFFFFFFFF))


# esp_image_header_t up to the chip ID: magic, segments, DIO, 16 MB + 80 MHz, entry, WP pin, drive, ESP32-S3.
HEADER = b"\xe9\x07\x02\x4f" + b"\0" * 4 + b"\xee\0\0\0" + b"\x09\x00"


def app_image(version: str, size: int = 0x40000, board: bytes = b"papermono") -> bytes:
    body = HEADER + b"\0" * 0x100
    body += b"CrossMono-ESP32-" + version.encode() + b"\0" + b"CROSSPOINT-BOARD-V1:" + board + b";\0"
    filler = bytes(range(256)) * ((size - len(body)) // 256 + 1)
    return body + filler[: size - len(body)]


def full_image(app: bytes, csv: Path = ROOT / "partitions_papermono.csv", seq: int = 1) -> bytearray:
    image = bytearray(b"\xff" * (0x10000 + len(app)))
    image[0 : len(HEADER)] = b"\xe9\x03" + HEADER[2:]  # 3 segments, DIO, 16 MB, 80 MHz, ESP32-S3
    image[0x20:0x1000] = b"\x5a" * (0x1000 - 0x20)
    table = table_bytes(csv)
    image[0x8000 : 0x8000 + len(table)] = table
    image[0xE000:0xE020] = otadata_entry(seq)
    image[0x10000:] = app
    return image


class Build:
    """A fake .pio/build/<env> folder."""

    def __init__(self, root: Path, version: str = VERSION, app: bytes | None = None):
        self.dir = root / "build"
        self.dir.mkdir()
        self.app = app if app is not None else app_image(version)
        self.full = full_image(self.app)
        self.elf = b"\x7fELF" + b"\0" * 60

    def write(self) -> "Build":
        (self.dir / "firmware.bin").write_bytes(self.app)
        (self.dir / "firmware.factory.bin").write_bytes(bytes(self.full))
        (self.dir / "firmware.elf").write_bytes(self.elf)
        return self


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "dist"

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = package_release.main(args)
        return code, out.getvalue(), err.getvalue()

    def package(self, build: Build, tag: str = VERSION):
        build.write()
        return self.run_main(["--tag", tag, "--out", str(self.out), "--build-dir", str(build.dir)])

    def assert_refused(self, build: Build, message: str, tag: str = VERSION):
        code, _, err = self.package(build, tag)
        self.assertEqual(code, 1, err)
        self.assertIn(message, err)
        self.assertFalse(self.out.exists(), "nothing is written when a check fails")


class Tags(unittest.TestCase):
    def test_final_and_candidate(self):
        self.assertEqual(package_release.build_for_tag("0.1.0", "0.1.0"), ("papermono-gh_release", None))
        self.assertEqual(package_release.build_for_tag("0.1.0-rc.12", "0.1.0"), ("papermono-gh_release_rc", "12"))

    def test_refused(self):
        for tag in ("v0.1.0", "0.1", "0.1.0rc", "0.1.0-rc.0", "0.1.0-rc.01", "0.1.0-beta.1", "0.1.0-rc.1+x", " 0.1.0"):
            with self.subTest(tag=tag), self.assertRaisesRegex(package_release.PackageError, "is not N.N.N"):
                package_release.build_for_tag(tag, "0.1.0")

    def test_must_match_the_configured_version(self):
        with self.assertRaisesRegex(package_release.PackageError, r"does not match \[crossmono\] version = 0.1.0"):
            package_release.build_for_tag("0.2.0-rc.1", "0.1.0")

    def test_check_tag_prints_the_build(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(package_release.main(["--tag", RC_TAG, "--check-tag"]), 0)
        self.assertEqual(out.getvalue(), "env=papermono-gh_release_rc\nrc=1\n")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(package_release.main(["--tag", VERSION, "--check-tag"]), 0)
        self.assertEqual(out.getvalue(), "env=papermono-gh_release\nrc=\n")

    def test_ota_asset_name_limit(self):
        # VERSIONING.md: tags up to 23 characters fit the updater's buffer.
        longest = f"{VERSION}-rc.".ljust(23, "1")
        self.assertEqual(len(package_release.asset_names(longest)["app"]), package_release.OTA_ASSET_NAME_SIZE - 1)
        with self.assertRaisesRegex(package_release.PackageError, "longer than the updater"):
            package_release.asset_names(longest + "1")

    def test_limit_matches_the_updater(self):
        source = (ROOT / "src" / "network" / "OtaUpdater.cpp").read_text()
        self.assertRegex(source, rf"char assetName\[{package_release.OTA_ASSET_NAME_SIZE}\]")


class Package(Case):
    def test_good_build(self):
        build = Build(self.root)
        code, out, err = self.package(build)
        self.assertEqual(code, 0, err)
        self.assertIn("size gate ok", out)
        app, full, elf = (f"crossmono-{VERSION}-papermono{suffix}" for suffix in (".bin", "-full.bin", ".elf"))
        written = sorted(p.name for p in self.out.iterdir())
        self.assertEqual(written, sorted([app, full, elf, "manifest.json", "SHA256SUMS"]))
        self.assertEqual((self.out / app).read_bytes(), build.app)
        self.assertEqual((self.out / full).read_bytes(), bytes(build.full))
        self.assertEqual((self.out / elf).read_bytes(), build.elf)

        sums = {}
        for line in (self.out / "SHA256SUMS").read_text().splitlines():
            digest, name = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line).groups()
            sums[name] = digest
        self.assertEqual(sorted(sums), sorted([app, full, elf, "manifest.json"]))
        for name, digest in sums.items():
            self.assertEqual(hashlib.sha256((self.out / name).read_bytes()).hexdigest(), digest, name)

        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(manifest["name"], "CrossMono")
        self.assertEqual(manifest["version"], VERSION)
        self.assertEqual(manifest["new_install_improv_wait_time"], 0)
        self.assertNotIn("new_install_prompt_erase", manifest)
        self.assertEqual(manifest["builds"], [{"chipFamily": "ESP32-S3", "parts": [{"path": full, "offset": 0}]}])

    def test_release_candidate(self):
        code, _, err = self.package(Build(self.root, RC_TAG), RC_TAG)
        self.assertEqual(code, 0, err)
        self.assertTrue((self.out / f"crossmono-{RC_TAG}-papermono-full.bin").is_file())

    def test_existing_empty_folder_is_used(self):
        self.out.mkdir()
        code, _, err = self.package(Build(self.root))
        self.assertEqual(code, 0, err)

    def test_folder_with_files_is_refused(self):
        self.out.mkdir()
        (self.out / "crossmono-0.0.9-papermono.bin").write_bytes(b"old")
        code, _, err = self.package(Build(self.root))
        self.assertEqual(code, 1)
        self.assertIn("is not an empty folder", err)

    def test_missing_full_image(self):
        build = Build(self.root).write()
        (build.dir / "firmware.factory.bin").unlink()
        code, _, err = self.run_main(["--tag", VERSION, "--out", str(self.out), "--build-dir", str(build.dir)])
        self.assertEqual(code, 1)
        self.assertIn("firmware.factory.bin", err)
        self.assertFalse(self.out.exists())


class AppImage(Case):
    def test_wrong_version(self):
        self.assert_refused(Build(self.root, RC_TAG), f"is not version {VERSION} (found {RC_TAG})")

    def test_development_build_is_not_the_release(self):
        # "CrossMono-ESP32-0.1.0" is a prefix of the development build's string.
        self.assert_refused(Build(self.root, f"{VERSION}-dev+3f2a1c9"), f"(found {VERSION}-dev+3f2a1c9)")

    def test_no_version_string(self):
        build = Build(self.root, app=app_image(VERSION).replace(b"CrossMono-ESP32-", b"CrossPoint-ESP32"))
        self.assert_refused(build, "(found no CrossMono version string)")

    def test_no_magic_byte(self):
        build = Build(self.root, app=b"\0" + app_image(VERSION)[1:])
        self.assert_refused(build, "does not start with the 0xE9 image magic byte")

    def test_other_chip(self):
        app = bytearray(app_image(VERSION))
        app[12] = 0x05  # ESP32-C3
        self.assert_refused(Build(self.root, app=bytes(app)), "firmware.bin is not an ESP32-S3 image (chip ID 5)")

    def test_other_board(self):
        build = Build(self.root, app=app_image(VERSION, board=b"x3-x4"))
        self.assert_refused(build, "has no CROSSPOINT-BOARD-V1:papermono; board tag")

    def test_not_an_elf(self):
        build = Build(self.root)
        build.elf = b"\0" * 64
        self.assert_refused(build, "firmware.elf is not an ELF file")

    def test_size_gate(self):
        build = Build(self.root, app=app_image(VERSION, size=SLOT * 95 // 100 + 1))
        code, out, err = self.package(build)
        self.assertEqual(code, 1)
        self.assertIn("size gate FAILED", out)
        self.assertIn("fails the flash-size gate", err)
        self.assertFalse(self.out.exists())


class FullImage(Case):
    def test_stale_tail(self):
        build = Build(self.root)
        build.full[-1] ^= 0xFF
        self.assert_refused(build, "does not end with this firmware.bin at 0x10000")

    def test_stale_size(self):
        build = Build(self.root)
        build.full = build.full[:-256]
        self.assert_refused(build, f"expected {0x10000 + len(build.app):,} B (0x10000 + firmware.bin)")

    def test_truncated(self):
        build = Build(self.root)
        build.full = bytearray()
        self.assert_refused(build, "firmware.factory.bin is 0 B")

    def test_no_bootloader(self):
        build = Build(self.root)
        build.full[0] = 0xFF
        self.assert_refused(build, "no bootloader at 0x0")

    def test_bootloader_for_4mb_flash(self):
        build = Build(self.root)
        build.full[3] = 0x2F
        self.assert_refused(build, "not 16 MB")

    def test_bootloader_for_another_chip(self):
        build = Build(self.root)
        build.full[12] = 0x00  # ESP32
        self.assert_refused(build, "the bootloader at 0x0 is not for the ESP32-S3 (chip ID 0)")

    def test_no_partition_table(self):
        build = Build(self.root)
        build.full[0x8000:0x8002] = b"\xff\xff"
        self.assert_refused(build, "no partition table")

    def test_upstream_partition_table(self):
        build = Build(self.root)
        build.full = full_image(build.app, ROOT / "partitions.csv")
        self.assert_refused(build, "is not the one platformio.ini names")

    def test_nvs_not_blank(self):
        build = Build(self.root)
        build.full[0xA000] = 0x00
        self.assert_refused(build, "NVS (0x9000-0xdfff) is not blank")

    def test_otadata_selects_app1(self):
        build = Build(self.root)
        build.full = full_image(build.app, seq=2)
        self.assert_refused(build, "does not select the app at 0x10000 (it starts ota_1)")

    def test_otadata_missing(self):
        build = Build(self.root)
        build.full[0xE000:0xE020] = b"\xff" * 32
        self.assert_refused(build, "does not select the app at 0x10000")

    def test_reports_every_problem(self):
        build = Build(self.root, RC_TAG)
        build.full = full_image(build.app, seq=2)
        build.full[0xA000] = 0x00
        code, _, err = self.package(build)
        self.assertEqual(code, 1)
        for message in ("is not version", "NVS", "otadata"):
            self.assertIn(message, err)


if __name__ == "__main__":
    unittest.main()
