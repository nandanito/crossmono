"""Check the CrossMono version flags and their use in platformio.ini (ADR 0004).

Run with python3 test/mono/test_version_flags.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import configparser
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import version_flags  # noqa: E402

PAPERMONO_ENVS = ("papermono", "papermono-gh_release", "papermono-gh_release_rc")
SCRIPT = "pre:scripts/mono/version_flags.py"


class Compose(unittest.TestCase):
    """The table in VERSIONING.md, one row per environment."""

    def test_development(self):
        self.assertEqual(version_flags.compose("papermono", "0.1.0", None, "3f2a1c9"), "0.1.0-dev+3f2a1c9")

    def test_release_candidate(self):
        self.assertEqual(version_flags.compose("papermono-gh_release_rc", "0.1.0", "1", ""), "0.1.0-rc.1")
        self.assertEqual(version_flags.compose("papermono-gh_release_rc", "0.1.0", "12", ""), "0.1.0-rc.12")

    def test_release(self):
        self.assertEqual(version_flags.compose("papermono-gh_release", "0.1.0", None, ""), "0.1.0")

    def test_release_and_development_ignore_the_rc_number(self):
        # VERSIONING.md: never put -rc in a development version string.
        self.assertEqual(version_flags.compose("papermono-gh_release", "0.1.0", "3", "3f2a1c9"), "0.1.0")
        self.assertEqual(version_flags.compose("papermono", "0.1.0", "3", "3f2a1c9"), "0.1.0-dev+3f2a1c9")

    def test_release_candidate_needs_a_number(self):
        for rc in (None, "", "0", "01", "1a", "-1", "rc.1"):
            with self.subTest(rc=rc), self.assertRaises(version_flags.VersionError) as raised:
                version_flags.compose("papermono-gh_release_rc", "0.1.0", rc, "")
            self.assertIn("CROSSMONO_RC", str(raised.exception))

    def test_version_is_three_numbers(self):
        # The updater parses "%d.%d.%d"; a prefix or suffix in the base version would confuse it.
        for version in ("v0.1.0", "0.1", "0.1.0-rc.1", "0.1.0.1", ""):
            with self.subTest(version=version), self.assertRaises(version_flags.VersionError):
                version_flags.compose("papermono-gh_release", version, None, "")

    def test_kind_follows_the_suffix(self):
        self.assertEqual(version_flags.kind("papermono"), "dev")
        self.assertEqual(version_flags.kind("papermono-gh_release"), "release")
        self.assertEqual(version_flags.kind("papermono-gh_release_rc"), "rc")
        self.assertEqual(version_flags.kind("anything-else"), "dev")


class Ini(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            ini = Path(tmp) / "platformio.ini"
            ini.write_text(text)
            return version_flags.read_versions(ini)

    def test_reads_both_versions(self):
        text = "[crosspoint]\nversion = 2.0.0\n\n[crossmono]\nversion = 0.1.0 ; bumped in release PRs\n"
        self.assertEqual(self.read(text), ("0.1.0", "2.0.0"))

    def test_missing_section_is_an_error(self):
        with self.assertRaises(version_flags.VersionError) as raised:
            self.read("[crosspoint]\nversion = 2.0.0\n")
        self.assertIn("crossmono", str(raised.exception))

    def test_missing_file_is_an_error(self):
        with self.assertRaises(version_flags.VersionError):
            version_flags.read_versions(Path("/nonexistent/platformio.ini"))

    def test_clean_strips_literal_breakers(self):
        self.assertEqual(version_flags.clean('2.0.0"\\x'), "2.0.0x")


class PlatformioIni(unittest.TestCase):
    """The seam in platformio.ini: the PaperMono environments run the script and set no version themselves."""

    @classmethod
    def setUpClass(cls):
        cls.config = configparser.ConfigParser(interpolation=None, strict=False, inline_comment_prefixes=("#", ";"))
        cls.config.read(ROOT / "platformio.ini")

    def test_crossmono_version(self):
        version, upstream = version_flags.read_versions(ROOT / "platformio.ini")
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertTrue(upstream)

    def test_papermono_environments_run_the_script(self):
        for env in PAPERMONO_ENVS:
            with self.subTest(env=env):
                scripts = self.config.get(f"env:{env}", "extra_scripts").split()
                self.assertIn("${base.extra_scripts}", scripts)
                self.assertIn(SCRIPT, scripts)

    def test_papermono_environments_define_no_version(self):
        # Set in build_flags as well, a macro would be defined twice.
        for env in PAPERMONO_ENVS:
            with self.subTest(env=env):
                flags = self.config.get(f"env:{env}", "build_flags")
                for macro in version_flags.MACROS:
                    self.assertNotIn(f"-D{macro}", flags)

    def test_papermono_usb_strings(self):
        for env in PAPERMONO_ENVS:
            with self.subTest(env=env):
                flags = self.config.get(f"env:{env}", "build_flags").split()
                self.assertIn('-DUSB_PRODUCT=\\"CrossMono_PaperMono\\"', flags)
                self.assertIn('-DUSB_MANUFACTURER=\\"CrossMono\\"', flags)

    def test_other_environments_keep_upstream_versions(self):
        for section in self.config.sections():
            if not section.startswith("env:") or section[len("env:"):] in PAPERMONO_ENVS:
                continue
            with self.subTest(env=section):
                self.assertNotIn(SCRIPT, self.config.get(section, "extra_scripts", fallback=""))


class Middleware(unittest.TestCase):
    def test_selects_units_that_use_a_macro(self):
        for macro in version_flags.MACROS:
            self.assertTrue(version_flags.uses_version_macros(b"const char* v = " + macro.encode() + b";\n"))
        self.assertFalse(version_flags.uses_version_macros(b"#include <Arduino.h>\nint x;\n"))


class Main(unittest.TestCase):
    def run_main(self, args, rc=None):
        environ = {key: value for key, value in os.environ.items() if key != "CROSSMONO_RC"}
        if rc is not None:
            environ["CROSSMONO_RC"] = rc
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, environ, clear=True), redirect_stdout(out), redirect_stderr(err):
            code = version_flags.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_prints_the_three_values(self):
        version, upstream = version_flags.read_versions(ROOT / "platformio.ini")
        code, out, _ = self.run_main(["--env", "papermono-gh_release"])
        self.assertEqual(code, 0)
        printed = dict(line.split("=", 1) for line in out.splitlines())
        self.assertEqual(printed["CROSSPOINT_VERSION"], version)
        self.assertEqual(printed["CROSSMONO_UPSTREAM_VERSION"], upstream)
        if (ROOT / "freeink-sdk" / ".git").exists():  # a checkout must not fall back to "unknown"
            self.assertRegex(printed["CROSSMONO_SDK_COMMIT"], r"^[0-9a-f]{7,}$")
        else:
            self.assertEqual(printed["CROSSMONO_SDK_COMMIT"], "unknown")

    def test_release_candidate(self):
        version, _ = version_flags.read_versions(ROOT / "platformio.ini")
        code, out, _ = self.run_main(["--env", "papermono-gh_release_rc"], rc="2")
        self.assertEqual(code, 0)
        self.assertIn(f"CROSSPOINT_VERSION={version}-rc.2\n", out)

    def test_release_candidate_without_number_fails(self):
        code, out, err = self.run_main(["--env", "papermono-gh_release_rc"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("CROSSMONO_RC", err)

    def test_development_carries_a_commit(self):
        code, out, _ = self.run_main(["--env", "papermono"])
        self.assertEqual(code, 0)
        sha = r"[0-9a-f]{7,}" if (ROOT / ".git").exists() else "unknown"
        self.assertRegex(out, r"CROSSPOINT_VERSION=\d+\.\d+\.\d+-dev\+" + sha + r"\n")


if __name__ == "__main__":
    unittest.main()
