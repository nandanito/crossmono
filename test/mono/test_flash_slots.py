"""Check the flash read-back decoder on synthetic tables and otadata (scripts/mono/flash_slots.py).

Run with python3 test/mono/test_flash_slots.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import binascii
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import flash_slots  # noqa: E402

# partitions_papermono.csv
TABLE = [
    ("nvs", 0x01, 0x02, 0x9000, 0x5000),
    ("otadata", 0x01, 0x00, 0xE000, 0x2000),
    ("app0", 0x00, 0x10, 0x10000, 0x7F0000),
    ("app1", 0x00, 0x11, 0x800000, 0x7F0000),
    ("coredump", 0x01, 0x03, 0xFF0000, 0x10000),
]
EMPTY = None
UNDEFINED = 0xFFFFFFFF
NEW, PENDING_VERIFY, VALID, INVALID, ABORTED = range(5)


def table_bytes(rows=TABLE):
    out = b""
    for name, ptype, subtype, offset, size in rows:
        out += b"\xaa\x50" + struct.pack("<BBII", ptype, subtype, offset, size)
        out += name.encode().ljust(16, b"\0") + b"\0" * 4
    out += b"\xeb\xeb" + b"\xff" * 14 + b"\0" * 16  # MD5 row, as gen_esp32part.py writes it
    return out.ljust(0x1000, b"\xff")


def ota_sector(entry, crc=None):
    if entry is EMPTY:
        return b"\xff" * 0x1000
    seq, state = entry
    if crc is None:
        crc = binascii.crc32(struct.pack("<I", seq), 0xFFFFFFFF)
    return (struct.pack("<I", seq) + b"\xff" * 20 + struct.pack("<II", state, crc)).ljust(0x1000, b"\xff")


def readback(first, second, crc_second=None):
    """0x8000-0xFFFF as esptool read-flash 0x8000 0x8000 returns it."""
    nvs = b"\xff" * (0xE000 - 0x9000)
    return table_bytes() + nvs + ota_sector(first) + ota_sector(second, crc_second)


def full_image(first, second):
    return b"\xe9" + b"\0" * (0x8000 - 1) + readback(first, second) + b"\xe9" * 64


def last_line(data):
    return flash_slots.report(data)[-1]


class Table(unittest.TestCase):
    def test_reads_the_crossmono_table(self):
        lines = flash_slots.report(readback((1, UNDEFINED), EMPTY))
        self.assertEqual(lines[0], "Partition table at 0x8000:")
        self.assertEqual(lines[1], "  nvs       type 0x01 subtype 0x02 offset 0x0009000 size 0x0005000")
        self.assertEqual(lines[3], "  app0      type 0x00 subtype 0x10 offset 0x0010000 size 0x07f0000")
        self.assertEqual(lines[4], "  app1      type 0x00 subtype 0x11 offset 0x0800000 size 0x07f0000")
        self.assertEqual(len(lines), 1 + len(TABLE) + 2 + 1)  # header, rows, two otadata lines, verdict

    def test_full_image_reads_like_a_readback(self):
        self.assertEqual(flash_slots.report(full_image((1, UNDEFINED), EMPTY)),
                         flash_slots.report(readback((1, UNDEFINED), EMPTY)))


class NextBoot(unittest.TestCase):
    def test_usb_install_boots_app0(self):
        self.assertEqual(last_line(readback((1, UNDEFINED), EMPTY)),
                         "Boots ota_0 (app0 at 0x10000), image state UNDEFINED.")

    def test_after_ota_boots_app1(self):
        lines = flash_slots.report(readback((1, VALID), (2, VALID)))
        self.assertEqual(lines[-1], "Boots ota_1 (app1 at 0x800000), image state VALID.")
        self.assertIn("otadata 0xf000: seq 0x2 state VALID, usable", lines)

    def test_new_image_not_yet_booted(self):
        self.assertEqual(last_line(readback((1, VALID), (2, NEW))),
                         "Boots ota_1 (app1 at 0x800000), image state NEW.")

    def test_sequence_wraps_over_the_slots(self):
        self.assertEqual(last_line(readback((3, VALID), (2, VALID))),
                         "Boots ota_0 (app0 at 0x10000), image state VALID.")

    def test_rolled_back_entry(self):
        for state, name in ((INVALID, "INVALID"), (ABORTED, "ABORTED")):
            with self.subTest(state=name):
                lines = flash_slots.report(readback((1, VALID), (2, state)))
                self.assertIn(f"otadata 0xf000: seq 0x2 state {name}, skipped ({name} at boot)", lines)
                self.assertEqual(lines[-2], "Boots ota_0 (app0 at 0x10000), image state VALID.")
                self.assertEqual(lines[-1], "Rolled back: the newest entry (seq 0x2) was rejected.")

    def test_pending_verify_is_aborted_at_the_next_boot(self):
        lines = flash_slots.report(readback((1, VALID), (2, PENDING_VERIFY)))
        self.assertIn("otadata 0xf000: seq 0x2 state PENDING_VERIFY, skipped (ABORTED at boot)", lines)
        self.assertEqual(lines[-2], "Boots ota_0 (app0 at 0x10000), image state VALID.")
        self.assertEqual(lines[-1], "Rolled back: the newest entry (seq 0x2) was rejected.")

    def test_bad_crc_is_skipped(self):
        lines = flash_slots.report(readback((1, VALID), (2, VALID), crc_second=0x12345678))
        self.assertIn("otadata 0xf000: seq 0x2 state VALID, bad CRC, skipped", lines)
        self.assertEqual(lines[-1], "Boots ota_0 (app0 at 0x10000), image state VALID.")

    def test_empty_otadata_starts_ota_0(self):
        lines = flash_slots.report(readback(EMPTY, EMPTY))
        self.assertIn("otadata 0xe000: seq 0xffffffff state UNDEFINED, unused", lines)
        self.assertEqual(lines[-1], "No usable otadata entry: the bootloader starts ota_0 (app0 at 0x10000).")

    def test_both_rejected_starts_ota_0(self):
        lines = flash_slots.report(readback((1, INVALID), (2, ABORTED)))
        self.assertEqual(lines[-2], "No usable otadata entry: the bootloader starts ota_0 (app0 at 0x10000).")
        self.assertEqual(lines[-1], "Rolled back: the newest entry (seq 0x2) was rejected.")


class Main(unittest.TestCase):
    def run_main(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "readback.bin"
            path.write_bytes(data)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = flash_slots.main([str(path)])
            return code, out.getvalue(), err.getvalue()

    def test_prints_the_report(self):
        code, out, _ = self.run_main(readback((1, VALID), (2, VALID)))
        self.assertEqual(code, 0)
        self.assertTrue(out.endswith("Boots ota_1 (app1 at 0x800000), image state VALID.\n"))

    def test_rejects_a_file_without_a_table(self):
        code, out, err = self.run_main(b"\xff" * 0x10000)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("no partition table", err)

    def test_rejects_a_readback_that_misses_otadata(self):
        code, _, err = self.run_main(table_bytes())
        self.assertEqual(code, 1)
        self.assertIn("0xe000-0xe01f is not in the file", err)


if __name__ == "__main__":
    unittest.main()
