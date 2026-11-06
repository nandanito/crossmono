"""Check the release licence file writer on a synthetic tree (scripts/mono/release_license.py, ADR 0009).

Run with python3 test/mono/test_release_license.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import release_license  # noqa: E402

COMMIT, SDK = "a" * 40, "b" * 40
ENV = "papermono-gh_release"


class Tree:
    """A repository, .pio/libdeps/<env> and a PlatformIO packages folder with every text the writer reads."""

    def __init__(self, base: Path):
        self.root = base / "repo"
        self.libdeps = self.root / ".pio" / "libdeps" / ENV
        self.packages = base / "packages"
        self.write("LICENSE", "MIT License\nCopyright (c) 2026 Nandan and the CrossMono contributors\n")
        self.write("THIRD-PARTY-NOTICES", "CrossMono third-party notices\n")
        self.write("licenses/GPL-3.0.txt", "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n")
        for texts in release_license.TREE_TEXTS.values():
            for title, path, marker in texts:
                if marker:
                    body = f"/* other comment */\nint x;\n/* Copyright someone.\n   {marker} to all. */\nint y;\n"
                else:
                    body = f"Text of {title}.\n"
                self.write(path, body)
        for name, files in release_license.LIBRARIES.items():
            for file in files:
                self.write(f".pio/libdeps/{ENV}/{name}/{file}", f"{name} {file} text\n")
            spec = {"owner": "someone", "id": 1, "name": name, "requirements": None, "uri": None}
            piopm = {"name": name, "version": "1.2.3", "spec": spec}
            self.write(f".pio/libdeps/{ENV}/{name}/.piopm", json.dumps(piopm))
        self.write(f".pio/libdeps/{ENV}/BoardConfig.pio-link", "{}")  # an SDK library: a link file, not a folder
        self.write(f".pio/libdeps/{ENV}/integrity.dat", "x")
        for title, path, marker in release_license.PACKAGE_TEXTS:
            file = self.packages / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(f"#pragma once\n/* Copyright {title}.\n   {marker} to all. */\n")
        for name in release_license.PACKAGES:
            repository = {"type": "git", "url": f"https://example.com/{name}"}
            self.write_package(name, {"name": name, "version": "9.9.9", "repository": repository})

    def write(self, path: str, text: str) -> Path:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        return file

    def write_package(self, name: str, info: dict) -> None:
        (self.packages / name).mkdir(parents=True, exist_ok=True)
        (self.packages / name / "package.json").write_text(json.dumps(info))

    def render(self, tag: str = "0.1.0") -> str:
        return release_license.render(tag, ENV, COMMIT, SDK, self.root, self.libdeps, self.packages)


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tree = Tree(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def assert_error(self, message: str):
        with self.assertRaises(release_license.LicenseError) as caught:
            self.tree.render()
        self.assertIn(message, str(caught.exception))


class Render(Case):
    def test_complete_tree_passes_the_check(self):
        text = self.tree.render()
        self.assertEqual(release_license.check(text, "0.1.0", COMMIT, SDK), [])
        sections = release_license.sections(text)
        license_text = (self.tree.root / "LICENSE").read_text().strip()
        self.assertEqual(sections[release_license.LICENSE_TITLE].strip(), license_text)
        self.assertIn("GNU GENERAL PUBLIC LICENSE", sections[release_license.GPL_TITLE])

    def test_header(self):
        text = self.tree.render("0.1.0-rc.2")
        for line in (
            "CrossMono 0.1.0-rc.2 firmware licences",
            "Release: 0.1.0-rc.2",
            f"Source commit: {COMMIT}",
            f"FreeInk SDK commit: {SDK}",
            f"Build environment: {ENV}",
            f"Source: https://github.com/nandanito/crossmono/tree/{COMMIT}",
            f"SDK source: https://github.com/Free-Ink/freeink-sdk/tree/{SDK}",
            release_license.GPL_STATEMENT + ".",
            "This software is based in part on the work of the FreeType Team.",
        ):
            self.assertIn(f"\n{line}\n", "\n" + text, line)

    def test_marker_takes_only_that_comment(self):
        expat = release_license.sections(self.tree.render())["Expat: lib/expat/xmlparse.c"]
        self.assertIn("Licensed under the MIT license to all.", expat)
        self.assertNotIn("other comment", expat)
        self.assertNotIn("int y", expat)

    def test_sections_in_order(self):
        titles = list(release_license.sections(self.tree.render()))
        expected = release_license.titles()
        self.assertEqual([t for t in titles if t in expected], expected, "every expected text, in the documented order")

    def test_library_sources(self):
        (self.tree.libdeps / "PNGdec" / ".piopm").write_text(
            json.dumps(
                {"name": "PNGdec", "version": "1.1.6", "spec": {"owner": "bitbank2", "name": "PNGdec", "uri": None}}
            )
        )
        (self.tree.libdeps / "QRCode" / ".piopm").write_text(
            json.dumps({"name": "QRCode", "version": "0.0.1", "spec": {"uri": "https://example.com/qr.zip"}})
        )
        (self.tree.libdeps / "JPEGDEC" / ".piopm").unlink()
        (self.tree.libdeps / "JPEGDEC" / ".git").mkdir()

        def git(cwd, *args):
            if cwd == self.tree.libdeps / "JPEGDEC":
                return {"config": "https://github.com/bitbank2/JPEGDEC.git", "rev-parse": "86282979"}[args[0]]
            raise AssertionError(f"unexpected git call in {cwd}")

        with mock.patch.object(release_license, "git", git):
            sections = release_license.sections(self.tree.render())
        self.assertEqual(
            sections["PNGdec: source"].strip(),
            "https://dl.registry.platformio.org/download/bitbank2/library/PNGdec/1.1.6/PNGdec-1.1.6.tar.gz",
        )
        self.assertEqual(sections["QRCode: source"].strip(), "https://example.com/qr.zip")
        self.assertEqual(
            sections["JPEGDEC: source"].strip(), "https://github.com/bitbank2/JPEGDEC.git at commit 86282979"
        )

    def test_nested_licences_under_src_only(self):
        self.tree.write(f".pio/libdeps/{ENV}/NimBLE-Arduino/src/nimble/ext/tinycrypt/LICENSE", "tinycrypt licence\n")
        self.tree.write(f".pio/libdeps/{ENV}/WebSockets/src/libb64/LICENSE", "libb64 licence\n")
        self.tree.write(f".pio/libdeps/{ENV}/AnimatedGIF/examples/demo/LICENSE.txt", "example licence\n")
        sections = release_license.sections(self.tree.render())
        self.assertEqual(sections["NimBLE-Arduino: src/nimble/ext/tinycrypt/LICENSE"].strip(), "tinycrypt licence")
        self.assertEqual(sections["WebSockets: src/libb64/LICENSE"].strip(), "libb64 licence")
        self.assertFalse([t for t in sections if "examples" in t])

    def test_prebuilt_component_notices(self):
        sections = release_license.sections(self.tree.render())
        tinyusb = sections["TinyUSB (MIT, the terms in LICENSE above)"]
        self.assertIn("SPDX", tinyusb)
        self.assertNotIn("#pragma", tinyusb)
        for title in ("cJSON", "http_parser", "protobuf-c"):
            self.assertIn(f"Copyright {title}.", sections[title])

    def test_package_versions(self):
        packages = release_license.sections(self.tree.render())["Platform packages"]
        self.assertIn("framework-arduinoespressif32 9.9.9 (https://example.com/framework-arduinoespressif32)", packages)
        self.assertIn("toolchain-xtensa-esp-elf 9.9.9", packages)


class Refused(Case):
    def test_missing_text(self):
        (self.tree.root / "licenses" / "hyphenation.txt").unlink()
        self.assert_error("licenses/hyphenation.txt")

    def test_empty_text(self):
        self.tree.write("freeink-sdk/NOTICE", "\n")
        self.assert_error("freeink-sdk/NOTICE is empty")

    def test_marker_not_found(self):
        self.tree.write("freeink-sdk/libs/font/FreeInkFont/third_party/stb/stb_truetype.h", "/* no licence */\n")
        self.assert_error("has no comment with 'ALTERNATIVE A'")

    def test_unlisted_library(self):
        self.tree.write(f".pio/libdeps/{ENV}/NewLib/LICENSE", "x")
        self.assert_error("not listed: NewLib")

    def test_library_not_downloaded(self):
        for path in sorted((self.tree.libdeps / "SdFat").rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        (self.tree.libdeps / "SdFat").rmdir()
        self.assert_error("not downloaded: SdFat")

    def test_no_libdeps(self):
        self.tree.libdeps = self.tree.root / "missing"
        self.assert_error("build the environment first")

    def test_broken_package_metadata(self):
        (self.tree.libdeps / "PNGdec" / ".piopm").write_text("{not json")
        self.assert_error("cannot read")
        (self.tree.libdeps / "PNGdec" / ".piopm").write_text('{"name": "PNGdec"}')
        self.assert_error("cannot read")

    def test_source_files_named_like_licences_are_not_texts(self):
        self.tree.write(f".pio/libdeps/{ENV}/SdFat/src/LicenseManager.cpp", "int x;\n")
        self.tree.write(f".pio/libdeps/{ENV}/SdFat/src/COPYING.txt", "SdFat copying\n")
        sections = release_license.sections(self.tree.render())
        self.assertNotIn("SdFat: src/LicenseManager.cpp", sections)
        self.assertEqual(sections["SdFat: src/COPYING.txt"].strip(), "SdFat copying")

    def test_library_without_source(self):
        (self.tree.libdeps / "PNGdec" / ".piopm").unlink()
        self.assert_error("has neither .piopm nor .git")

    def test_missing_package_text(self):
        (self.tree.packages / release_license.PACKAGE_TEXTS[0][1]).unlink()
        self.assert_error("arduino_tinyusb/tinyusb/src/tusb.h")

    def test_missing_package(self):
        (self.tree.packages / "toolchain-xtensa-esp-elf" / "package.json").unlink()
        self.assert_error("cannot read the toolchain-xtensa-esp-elf package")


class Check(Case):
    def test_reports_every_problem(self):
        text = self.tree.render().replace(release_license.GPL_STATEMENT, "")
        text = text.replace("# FreeType: FTL.TXT\n", "# FreeType\n")
        errors = release_license.check(text, "0.2.0", "c" * 40, SDK)
        self.assertEqual(len(errors), 4, errors)
        self.assertIn("does not say 'Release: 0.2.0'", errors[0])
        self.assertIn(f"does not say 'Source commit: {'c' * 40}'", errors[1])
        self.assertIn("no GPLv3 statement", errors[2])
        self.assertIn("no text for 'FreeType: FTL.TXT'", errors[3])

    def test_a_prefix_of_the_tag_is_not_the_tag(self):
        self.assertTrue(release_license.check(self.tree.render("0.1.0-rc.1"), "0.1.0", COMMIT, SDK))


class Commits(unittest.TestCase):
    def test_sdk_checkout_must_match(self):
        answers = {("rev-parse", "HEAD"): [COMMIT, "c" * 40], ("rev-parse", "HEAD:freeink-sdk"): [SDK]}

        def git(cwd, *args):
            return answers[args].pop(0)

        with mock.patch.object(release_license, "git", git):
            message = f"freeink-sdk is at {'c' * 40}, but the source records {SDK}"
            with self.assertRaisesRegex(release_license.LicenseError, message):
                release_license.commits(ROOT)

    def test_this_checkout(self):
        commit, sdk = release_license.commits(ROOT)
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertRegex(sdk, r"^[0-9a-f]{40}$")


class Main(Case):
    def test_writes_the_file(self):
        out = Path(self.tmp.name) / "LICENSE.txt"
        stdout = io.StringIO()
        with (
            mock.patch.object(release_license, "ROOT", self.tree.root),
            mock.patch.object(release_license, "commits", lambda root: (COMMIT, SDK)),
            redirect_stdout(stdout),
        ):
            code = release_license.main(
                ["--tag", "0.1.0", "--env", ENV, "--out", str(out), "--packages-dir", str(self.tree.packages)]
            )
        self.assertEqual(code, 0)
        self.assertEqual(release_license.check(out.read_text(), "0.1.0", COMMIT, SDK), [])
        self.assertIn("for CrossMono 0.1.0", stdout.getvalue())

    def test_error_writes_nothing(self):
        (self.tree.root / "LICENSE").unlink()
        out = Path(self.tmp.name) / "LICENSE.txt"
        stderr = io.StringIO()
        with (
            mock.patch.object(release_license, "ROOT", self.tree.root),
            mock.patch.object(release_license, "commits", lambda root: (COMMIT, SDK)),
            redirect_stderr(stderr),
        ):
            code = release_license.main(
                ["--tag", "0.1.0", "--env", ENV, "--out", str(out), "--packages-dir", str(self.tree.packages)]
            )
        self.assertEqual(code, 1)
        self.assertIn("LICENSE", stderr.getvalue())
        self.assertFalse(out.exists())


class RepositoryTexts(unittest.TestCase):
    """Every text that comes from this repository is there and has its marker (checked again at each sync).

    Needs the nested Lucide submodule: git submodule update --init --recursive.
    """

    def test_tree_texts(self):
        for path in ("LICENSE", "THIRD-PARTY-NOTICES", "licenses/GPL-3.0.txt"):
            with self.subTest(path=path):
                self.assertTrue(release_license.read(ROOT / path).strip())
        for texts in release_license.TREE_TEXTS.values():
            for title, path, marker in texts:
                with self.subTest(title=title):
                    self.assertTrue(release_license.read(ROOT / path, marker).strip())

    def test_carried_licences_are_crosspoints(self):
        # licenses/*.txt are CrossPoint's files from 136c2655, unchanged, so the sync merges them cleanly.
        names = sorted(path.name for path in (ROOT / "licenses").iterdir())
        self.assertEqual(
            names,
            sorted(
                ["Apache-2.0.txt", "GPL-3.0.txt", "LGPL-2.1.txt", "LGPL-3.0.txt", "LPPL-1.3c.txt", "borrowed-code.txt"]
                + ["fonts.txt", "hyphenation.txt", "platform.txt"]
            ),
        )


if __name__ == "__main__":
    unittest.main()
