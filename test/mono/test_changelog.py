"""Check the release-notes extraction from CHANGELOG.md (scripts/mono/changelog.py, ADR 0004).

Run with python3 test/mono/test_changelog.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import changelog  # noqa: E402

TEXT = textwrap.dedent(
    """\
    # Changelog

    Intro text.

    ## [Unreleased]

    ### Upstream

    - CrossPoint base: 2.1.0 (`aaaaaaaa`)

    ## [0.1.0] - 2026-11-20

    ### Fixed

    - Something.

    ### Upstream

    - CrossPoint base: 2.0.0 (`42d58daa`)

    ## [0.1.0-rc.1] - 2026-11-10

    ### Added

    - First candidate.

    ### Upstream

    - FreeInk SDK: `5e94fe7`

    [0.1.0]: https://github.com/nandanito/crossmono/releases/tag/0.1.0
    """
)


class Section(unittest.TestCase):
    def test_middle_section(self):
        notes = changelog.section(TEXT, "0.1.0")
        self.assertTrue(notes.startswith("### Fixed\n"), notes)
        self.assertTrue(notes.endswith("- CrossPoint base: 2.0.0 (`42d58daa`)\n"), notes)
        self.assertNotIn("## [", notes)

    def test_candidate_is_its_own_section(self):
        notes = changelog.section(TEXT, "0.1.0-rc.1")
        self.assertIn("First candidate.", notes)
        self.assertNotIn("Something.", notes)

    def test_last_section_stops_at_link_definitions(self):
        notes = changelog.section(TEXT, "0.1.0-rc.1")
        self.assertTrue(notes.endswith("- FreeInk SDK: `5e94fe7`\n"), notes)

    def test_unreleased_needs_no_date(self):
        self.assertIn("2.1.0", changelog.section(TEXT, "Unreleased"))

    def test_missing(self):
        for version in ("0.2.0", "0.1", "0.1.0-rc"):
            with self.subTest(version=version), self.assertRaisesRegex(changelog.ChangelogError, "no ## \\["):
                changelog.section(TEXT, version)

    def test_no_date(self):
        with self.assertRaisesRegex(changelog.ChangelogError, "has no date"):
            changelog.section("## [0.1.0]\n\n### Upstream\n\n- x\n", "0.1.0")

    def test_empty(self):
        with self.assertRaisesRegex(changelog.ChangelogError, "is empty"):
            changelog.section("## [0.1.0] - 2026-11-20\n\n\n## [0.0.9] - 2026-11-01\n", "0.1.0")

    def test_no_upstream_block(self):
        with self.assertRaisesRegex(changelog.ChangelogError, "no ### Upstream block"):
            changelog.section("## [0.1.0] - 2026-11-20\n\n### Fixed\n\n- x\n", "0.1.0")

    def test_upstream_of_the_next_section_does_not_count(self):
        text = "## [0.1.0] - 2026-11-20\n\n- x\n\n## [0.0.9] - 2026-11-01\n\n### Upstream\n"
        with self.assertRaisesRegex(changelog.ChangelogError, "no ### Upstream block"):
            changelog.section(text, "0.1.0")


class Main(unittest.TestCase):
    def run_main(self, version):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(TEXT)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = changelog.main([version, "--file", str(path)])
            return code, out.getvalue(), err.getvalue()

    def test_prints_the_section(self):
        code, out, _ = self.run_main("0.1.0")
        self.assertEqual(code, 0)
        self.assertEqual(out, changelog.section(TEXT, "0.1.0"))

    def test_missing_exits_1(self):
        code, out, err = self.run_main("9.9.9")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("no ## [9.9.9] section", err)


class Repository(unittest.TestCase):
    def test_unreleased_has_the_upstream_block(self):
        # docs/upstream-sync.md step 8: each sync adds its base here.
        notes = changelog.section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), "Unreleased")
        self.assertIn("### Upstream", notes)


if __name__ == "__main__":
    unittest.main()
