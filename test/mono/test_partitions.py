"""Check partitions_papermono.csv and its use in platformio.ini (ADR 0005).

Run with python3 test/mono/test_partitions.py.
"""

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import partitions  # noqa: E402

TABLE = "partitions_papermono.csv"
PAPERMONO_ENVS = ("papermono", "papermono-gh_release", "papermono-gh_release_rc")

# ADR 0005, also the starting point for the rule tests below.
ADR_TABLE = """\
# Name, Type, SubType, Offset, Size, Flags
nvs,      data, nvs,      0x9000,   0x5000,
otadata,  data, ota,      0xe000,   0x2000,
app0,     app,  ota_0,    0x10000,  0x7F0000,
app1,     app,  ota_1,    0x800000, 0x7F0000,
coredump, data, coredump, 0xFF0000, 0x10000,
"""


class PaperMonoTable(unittest.TestCase):
    def setUp(self):
        self.table = partitions.load(ROOT / TABLE)

    def test_rules_hold(self):
        self.assertEqual(partitions.check(self.table), [])

    def test_matches_adr_0005(self):
        # Fixed offsets matter beyond the rules: pioarduino writes boot_app0.bin at 0xe000 and the
        # app at 0x10000, and NVS survives `pio run -t upload` only while it stays at 0x9000.
        self.assertEqual(self.table, partitions.parse(ADR_TABLE))

    def test_papermono_envs_use_the_table(self):
        # Guards against a sync that drops the line from an environment.
        for env in PAPERMONO_ENVS:
            with self.subTest(env=env):
                self.assertEqual(partitions.env_partitions_file(ROOT / "platformio.ini", env), TABLE)

    def test_env_lookup_follows_extends_and_drops_inline_comments(self):
        ini = "[base]\nboard_build.partitions = base.csv\n[env:a]\nextends = base\n"
        ini += "[env:b]\nextends = base\nboard_build.partitions = own.csv ; CrossMono\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "platformio.ini"
            path.write_text(ini)
            self.assertEqual(partitions.env_partitions_file(path, "a"), "base.csv")
            self.assertEqual(partitions.env_partitions_file(path, "b"), "own.csv")


class Rules(unittest.TestCase):
    def assertBreaks(self, text, fragment):
        errors = partitions.check(partitions.parse(text))
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_good_table_passes(self):
        self.assertEqual(partitions.check(partitions.parse(ADR_TABLE)), [])

    def test_overlap(self):
        self.assertBreaks(ADR_TABLE.replace("0x800000, 0x7F0000", "0x7F0000, 0x7F0000"), "overlaps the region")

    def test_out_of_order(self):
        lines = ADR_TABLE.splitlines()
        lines[3], lines[4] = lines[4], lines[3]
        self.assertBreaks("\n".join(lines), "overlaps the region")

    def test_overlaps_the_table(self):
        self.assertBreaks(ADR_TABLE.replace("0x9000,", "0x8000,"), "overlaps the region")

    def test_unaligned_app(self):
        self.assertBreaks(ADR_TABLE.replace("0x800000, 0x7F0000", "0x801000, 0x7F0000"), "not 0x10000-aligned")

    def test_past_end_of_flash(self):
        self.assertBreaks(ADR_TABLE.replace("0xFF0000, 0x10000", "0xFF0000, 0x20000"), "past the end")

    def test_unequal_app_slots(self):
        self.assertBreaks(ADR_TABLE.replace("0x800000, 0x7F0000", "0x800000, 0x700000"), "differ in size")

    def test_one_app_slot(self):
        self.assertBreaks(ADR_TABLE.replace("app1,     app,  ota_1", "app1,     data, nvs  "), "expected app slots")

    def test_spiffs(self):
        self.assertBreaks(ADR_TABLE.replace("coredump, data, coredump", "spiffs,   data, spiffs  "), "spiffs")

    def test_size_suffixes(self):
        self.assertEqual(partitions.parse_size("20K"), 0x5000)
        self.assertEqual(partitions.parse_size("1M"), 0x100000)
        self.assertEqual(partitions.parse_size("8323072"), 0x7F0000)

    def test_missing_offset(self):
        with self.assertRaises(ValueError):
            partitions.parse("nvs, data, nvs, , 0x5000,\n")


if __name__ == "__main__":
    unittest.main()
