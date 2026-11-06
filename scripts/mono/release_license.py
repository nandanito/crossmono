"""Write the licence file of a CrossMono release (ADR 0009, ADR 0011): one text file with every licence.

    python3 scripts/mono/release_license.py --tag 0.1.0 --env papermono-gh_release --out <file>

Run it after the build of that environment: the library texts come from .pio/libdeps/<env> and the platform
versions from the PlatformIO packages. The file has a header (tag, source and SDK commits, source links, the
GPLv3 statement), LICENSE, THIRD-PARTY-NOTICES, and then the full texts that THIRD-PARTY-NOTICES names. It stops
when a text is missing, or when .pio/libdeps/<env> holds a library that is not listed here, so a new library
cannot ship without its licence. package_release.py checks the file with check().

licenses/*.txt are CrossPoint's texts, copied ahead of the sync that brings them. CrossPoint's
scripts/build_release_license.py replaces this script at that sync (docs/upstream-sync.md).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "https://github.com/nandanito/crossmono"
SDK_REPOSITORY = "https://github.com/Free-Ink/freeink-sdk"
GPL_STATEMENT = "The combined firmware image is distributed under the GNU General Public License, version 3"
# Headings use "#" rules: the included texts use "=" and "-" rules of their own.
RULE = "#" * 72
LICENSE_TITLE = "LICENSE (CrossMono and CrossPoint, MIT)"
NOTICES_TITLE = "THIRD-PARTY-NOTICES"
GPL_TITLE = "GPL-3.0 (the combined image)"

# Libraries that PlatformIO downloads (.pio/libdeps/<env>), with their top-level licence files.
# Licence files under a library's src/ are added as found (NimBLE's tinycrypt, WebSockets' libb64).
LIBRARIES = {
    "Arduino-wolfSSL": ("LICENSING", "COPYING"),
    "WebSockets": ("LICENSE",),
    "NimBLE-Arduino": ("LICENSE", "NOTICE"),
    "PNGdec": ("LICENSE",),
    "JPEGDEC": ("LICENSE",),
    "AnimatedGIF": ("LICENSE",),
    "ArduinoJson": ("LICENSE.txt",),
    "SdFat": ("LICENSE.md",),
    "QRCode": ("LICENSE.txt",),
}
NESTED = re.compile(r"(LICEN[CS]E|NOTICE|COPYING)(\.(txt|md|rst))?", re.I)  # not LicenseManager.cpp

# Platform packages (PLATFORMIO_CORE_DIR/packages), at the versions whose link map was checked for
# third-party code (2026-11-06). Another version stops the script: check the new image's firmware.map,
# update PACKAGE_TEXTS and THIRD-PARTY-NOTICES section 4, then the versions here.
PACKAGES = {
    "framework-arduinoespressif32": "3.3.11",
    "framework-arduinoespressif32-libs": "5.5.5+sha.b774170ff46",
    "toolchain-xtensa-esp-elf": "14.2.0+20260121",
}
# Third-party parts of the prebuilt libraries with code in the image and with no text in licenses/platform.txt:
# (title, path in the packages folder, marker), read like TREE_TEXTS. Notices that no package has (TinyUSB's
# linked sources, TLSF, fast_float) are in THIRD-PARTY-NOTICES section 4.
IDF_INCLUDE = "framework-arduinoespressif32-libs/esp32s3/include"
PACKAGE_TEXTS = [
    # TinyUSB's headers have only SPDX lines; the MIT terms are the ones in LICENSE.
    ("TinyUSB (MIT, the terms in LICENSE above)", f"{IDF_INCLUDE}/arduino_tinyusb/tinyusb/src/tusb.h", "SPDX"),
    ("cJSON", f"{IDF_INCLUDE}/espressif__cjson/cJSON/cJSON.h", "Permission is hereby granted"),
    ("Xtensa runtime (Cadence)", f"{IDF_INCLUDE}/xtensa/include/xtensa_context.h", "Permission is hereby granted"),
    ("Xtensa HAL (Cadence)", f"{IDF_INCLUDE}/xtensa/include/xtensa/hal.h", "Permission is hereby granted"),
]
# The Arduino-ESP32 sources this build compiles keep their copyright lines in comments; the notices are
# collected from them, as CrossPoint's build_release_license.py does. The libraries are the framework
# libraries in the .pio/build/<env> folder of the papermono-gh_release build.
ARDUINO = "framework-arduinoespressif32"
ARDUINO_LIBRARIES = (
    "AsyncUDP", "DNSServer", "ESPmDNS", "Ethernet", "FS", "Hash", "Network", "NetworkClientSecure", "Preferences",
    "SPI", "WebServer", "WiFi", "Wire",
)
ARDUINO_NOTICES_TITLE = "Arduino-ESP32: copyright notices in its sources"
NOTICE_COMMENT = re.compile(r"copyright|permission is", re.I)

# Texts in this repository: (title, path, marker). With a marker, only the first /* */ comment that
# contains it is taken (the licence in a source file's header).
TREE_TEXTS = {
    "platform": [
        ("Arduino-ESP32: LGPL-2.1", "licenses/LGPL-2.1.txt", None),
        ("ESP-IDF: Apache-2.0", "licenses/Apache-2.0.txt", None),
        ("ESP-IDF components and the GCC runtime: licenses/platform.txt", "licenses/platform.txt", None),
    ],
    "crosspoint": [
        ("Expat: lib/expat/xmlparse.c", "lib/expat/xmlparse.c", "Licensed under the MIT license"),
        ("miniz: lib/miniz/third_party/miniz.c", "lib/miniz/third_party/miniz.c", "Permission is hereby granted"),
        ("uzlib: lib/uzlib/src/tinflate.c", "lib/uzlib/src/tinflate.c", "Permission is granted"),
        ("Copied code and data: licenses/borrowed-code.txt", "licenses/borrowed-code.txt", None),
        ("EPDiy font data layouts: LGPL-3.0", "licenses/LGPL-3.0.txt", None),
        ("Hyphenation patterns: licenses/hyphenation.txt", "licenses/hyphenation.txt", None),
        ("Hyphenation patterns: LPPL-1.3c", "licenses/LPPL-1.3c.txt", None),
        ("Fonts: licenses/fonts.txt", "licenses/fonts.txt", None),
    ],
    "sdk": [
        ("FreeInk SDK: LICENSE", "freeink-sdk/LICENSE", None),
        ("FreeInk SDK: NOTICE (OpenX4, Bosch BMI270)", "freeink-sdk/NOTICE", None),
        ("FreeType: FTL.TXT", "freeink-sdk/libs/font/FreeInkFont/third_party/freetype/FTL.TXT", None),
        ("FreeType: LICENSE.TXT", "freeink-sdk/libs/font/FreeInkFont/third_party/freetype/LICENSE.TXT", None),
        ("stb_truetype", "freeink-sdk/libs/font/FreeInkFont/third_party/stb/stb_truetype.h", "ALTERNATIVE A"),
        ("miniz (ContentProtection)", "freeink-sdk/libs/book/ContentProtection/third_party/miniz/LICENSE", None),
        ("Lucide icons", "freeink-sdk/libs/assets/Icons/lucide/LICENSE", None),
    ],
}
PARTS = {
    "platform": "Platform: Arduino-ESP32, ESP-IDF and the toolchain",
    "crosspoint": "CrossPoint's libraries, data and fonts",
    "sdk": "FreeInk SDK",
}


class LicenseError(Exception):
    """The licence file cannot be written; the message says why."""


def section(title: str, body: str) -> str:
    return f"\n{RULE}\n# {title}\n{RULE}\n\n{body.strip()}\n"


def part(title: str) -> str:
    return f"\n\n{RULE}\n## {title}\n{RULE}\n"


def titles() -> list[str]:
    """Every section that a release licence file must have (the nested library files vary)."""
    fixed = [LICENSE_TITLE, NOTICES_TITLE, GPL_TITLE]
    libraries = [f"{name}: {file}" for name, files in LIBRARIES.items() for file in files]
    packages = [title for title, _, _ in PACKAGE_TEXTS] + [ARDUINO_NOTICES_TITLE]
    return fixed + libraries + packages + [title for texts in TREE_TEXTS.values() for title, _, _ in texts]


def git(cwd: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise LicenseError(f"git {' '.join(args)} failed in {cwd}: {error}") from error


def commits(root: Path) -> tuple[str, str]:
    """(source commit, SDK commit). The SDK checkout must be the commit that the source records."""
    commit = git(root, "rev-parse", "HEAD")
    sdk = git(root, "rev-parse", "HEAD:freeink-sdk")
    checked_out = git(root / "freeink-sdk", "rev-parse", "HEAD")
    if checked_out != sdk:
        raise LicenseError(f"freeink-sdk is at {checked_out}, but the source records {sdk}: git submodule update")
    return commit, sdk


def read(path: Path, marker: str | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise LicenseError(f"cannot read {path}: {error}") from error
    if marker:
        block = next((m.group() for m in re.finditer(r"/\*.*?\*/", text, re.S) if marker in m.group()), None)
        if block is None:
            raise LicenseError(f"{path} has no comment with {marker!r}")
        text = block
    if not text.strip():
        raise LicenseError(f"{path} is empty")
    return text


def library_source(directory: Path) -> str:
    """Where PlatformIO took the library from: the registry package, or a git commit."""
    metadata = directory / ".piopm"
    if metadata.is_file():
        try:
            package = json.loads(metadata.read_text())
            spec = package["spec"]
            if spec.get("uri"):
                return spec["uri"]
            owner, name, version = spec["owner"], package["name"], package["version"]
        except (ValueError, KeyError, TypeError) as error:
            raise LicenseError(f"cannot read {metadata}: {error!r}") from error
        return f"https://dl.registry.platformio.org/download/{owner}/library/{name}/{version}/{name}-{version}.tar.gz"
    if (directory / ".git").exists():
        url = git(directory, "config", "--get", "remote.origin.url")
        return f"{url} at commit {git(directory, 'rev-parse', 'HEAD')}"
    raise LicenseError(f"{directory} has neither .piopm nor .git; cannot name its source")


def library_texts(libdeps: Path) -> str:
    if not libdeps.is_dir():
        raise LicenseError(f"{libdeps} is missing; build the environment first")
    found = sorted(path.name for path in libdeps.iterdir() if path.is_dir())
    unlisted = sorted(set(found) - set(LIBRARIES))
    missing = sorted(set(LIBRARIES) - set(found))
    if unlisted or missing:
        raise LicenseError(
            f"the libraries in {libdeps} do not match LIBRARIES in release_license.py "
            f"(not listed: {', '.join(unlisted) or 'none'}; not downloaded: {', '.join(missing) or 'none'}); "
            "update the list and THIRD-PARTY-NOTICES"
        )
    text = ""
    for name, files in LIBRARIES.items():
        directory = libdeps / name
        text += section(f"{name}: source", library_source(directory))
        for file in files:
            text += section(f"{name}: {file}", read(directory / file))
        src = directory / "src"
        for path in sorted(src.rglob("*")) if src.is_dir() else []:
            if path.is_file() and NESTED.fullmatch(path.name):
                text += section(f"{name}: {path.relative_to(directory)}", read(path))
    return text


def package_versions(packages: Path) -> str:
    lines = []
    for name, checked in PACKAGES.items():
        try:
            info = json.loads((packages / name / "package.json").read_text())
        except (OSError, ValueError) as error:
            raise LicenseError(f"cannot read the {name} package in {packages}: {error}") from error
        if not isinstance(info, dict) or "version" not in info:
            raise LicenseError(f"the {name} package in {packages} has no version")
        if info["version"] != checked:
            raise LicenseError(
                f"{name} is {info['version']}, but the third-party notices were checked for {checked}: check the "
                "link map, PACKAGE_TEXTS and THIRD-PARTY-NOTICES section 4, then update PACKAGES"
            )
        url = (info.get("repository") or {}).get("url", "")
        lines.append(f"{name} {info['version']}" + (f" ({url})" if url else ""))
    lines.append("ESP-IDF: https://github.com/espressif/esp-idf, at the version in framework-arduinoespressif32-libs")
    return "\n".join(lines)


def arduino_notices(packages: Path) -> str:
    """Each distinct /* */ comment with a copyright or permission notice in the Arduino sources, with its file."""
    framework = packages / ARDUINO
    files = [*framework.glob("cores/esp32/**/*.[ch]"), *framework.glob("cores/esp32/**/*.cpp")]
    for name in ARDUINO_LIBRARIES:
        source = framework / "libraries" / name / "src"
        if not source.is_dir():
            raise LicenseError(f"{source} is missing")
        files += [*source.rglob("*.h"), *source.rglob("*.c"), *source.rglob("*.cpp")]
    seen: set[str] = set()
    notices = []
    for path in sorted(files):
        for match in re.finditer(r"/\*.*?\*/", path.read_text(encoding="utf-8", errors="replace"), re.S):
            comment = match.group()
            if NOTICE_COMMENT.search(comment) and comment not in seen:
                seen.add(comment)
                notices.append(f"{ARDUINO}/{path.relative_to(framework)}:\n{comment}")
    if not notices:
        raise LicenseError(f"no copyright notices found in {framework}")
    return "\n\n".join(notices)


def header(tag: str, env: str, commit: str, sdk: str) -> str:
    return f"""CrossMono {tag} firmware licences
{"=" * len(f"CrossMono {tag} firmware licences")}

Release: {tag}
Source commit: {commit}
FreeInk SDK commit: {sdk}
Build environment: {env}
Source: {REPOSITORY}/tree/{commit}
SDK source: {SDK_REPOSITORY}/tree/{sdk}

CrossMono's and CrossPoint's own code is under the MIT licence (LICENSE, below).
Third-party code, fonts and data keep their own licences (THIRD-PARTY-NOTICES, below).
The firmware image includes wolfSSL, which is licensed under the GNU GPL version 2
or, at your option, any later version.
{GPL_STATEMENT}.
Its text follows THIRD-PARTY-NOTICES.

How to get the source and rebuild this release: THIRD-PARTY-NOTICES, section 2.
GitHub's source archive of the tag does not contain the FreeInk SDK submodule or
the libraries that PlatformIO downloads; their sources are named in this file.

This software is based in part on the work of the FreeType Team.
"""


def render(tag: str, env: str, commit: str, sdk: str, root: Path, libdeps: Path, packages: Path) -> str:
    text = header(tag, env, commit, sdk)
    text += section(LICENSE_TITLE, read(root / "LICENSE"))
    text += section(NOTICES_TITLE, read(root / "THIRD-PARTY-NOTICES"))
    text += section(GPL_TITLE, read(root / "licenses" / "GPL-3.0.txt"))
    text += part("Libraries that PlatformIO downloads") + library_texts(libdeps)
    for key, texts in TREE_TEXTS.items():
        text += part(PARTS[key])
        if key == "platform":
            text += section("Platform packages", package_versions(packages))
            for title, path, marker in PACKAGE_TEXTS:
                text += section(title, read(packages / path, marker))
            text += section(ARDUINO_NOTICES_TITLE, arduino_notices(packages))
        for title, path, marker in texts:
            text += section(title, read(root / path, marker))
    return text


def sections(text: str) -> dict[str, str]:
    """Section title -> body, as section() writes them."""
    pattern = re.compile(rf"^{RULE}\n# ([^\n]+)\n{RULE}\n(.*?)(?=^{RULE}\n|\Z)", re.M | re.S)
    return {m.group(1): m.group(2) for m in pattern.finditer(text)}


def check(text: str, tag: str, commit: str, sdk: str) -> list[str]:
    """What package_release.py checks in a licence file; an empty list means it is good."""
    if not text.strip():
        return ["the licence file is empty"]
    errors = [
        f"the licence file does not say {line!r}"
        for line in (f"Release: {tag}", f"Source commit: {commit}", f"FreeInk SDK commit: {sdk}")
        if f"\n{line}\n" not in text
    ]
    if GPL_STATEMENT not in text:
        errors.append("the licence file has no GPLv3 statement")
    found = sections(text)
    errors += [f"the licence file has no text for {title!r}" for title in titles() if not found.get(title, "").strip()]
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", required=True, help="release tag, e.g. 0.1.0 or 0.1.0-rc.1")
    parser.add_argument("--env", required=True, help="the environment that was built, e.g. papermono-gh_release")
    parser.add_argument("--out", type=Path, required=True, help="the file to write")
    parser.add_argument(
        "--packages-dir",
        type=Path,
        default=Path(os.environ.get("PLATFORMIO_CORE_DIR", Path.home() / ".platformio")) / "packages",
    )
    args = parser.parse_args(argv)
    try:
        commit, sdk = commits(ROOT)
        libdeps = ROOT / ".pio" / "libdeps" / args.env
        text = render(args.tag, args.env, commit, sdk, ROOT, libdeps, args.packages_dir)
        errors = check(text, args.tag, commit, sdk)
        if errors:
            raise LicenseError("; ".join(errors))
        args.out.write_text(text, encoding="utf-8")
    except (LicenseError, OSError) as error:
        print(f"release_license.py: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {args.out} ({len(text.encode()):,} B) for CrossMono {args.tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
