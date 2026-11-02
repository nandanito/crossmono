"""Check the flash-size gate's thresholds and output (ADR 0005, ADR 0010).

Run with python3 test/mono/test_size_gate.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import size_gate  # noqa: E402

SLOT = 0x7F0000


class Verdict(unittest.TestCase):
    def test_thresholds(self):
        warn = -(-SLOT * 85 // 100)  # first size at or above 85 %
        fail = -(-SLOT * 95 // 100)
        self.assertEqual(size_gate.verdict(warn - 1, SLOT), "ok")
        self.assertEqual(size_gate.verdict(warn, SLOT), "warn")
        self.assertEqual(size_gate.verdict(fail - 1, SLOT), "warn")
        self.assertEqual(size_gate.verdict(fail, SLOT), "fail")
        self.assertEqual(size_gate.verdict(SLOT + 1, SLOT), "fail")


class Main(unittest.TestCase):
    def run_gate(self, app_size):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / "firmware.bin"
            app.write_bytes(b"\0" * app_size)
            summary = Path(tmp) / "summary.md"
            out = io.StringIO()
            with redirect_stdout(out):
                code = size_gate.main(["--env", "papermono-gh_release", "--app", str(app), "--summary", str(summary)])
            return code, out.getvalue(), summary.read_text()

    def test_base_image_passes(self):
        code, out, summary = self.run_gate(5_360_752)
        self.assertEqual(code, 0)
        self.assertIn("size gate ok", out)
        self.assertIn("(64.4 %) in app0 of partitions_papermono.csv", out)
        self.assertTrue(summary.startswith("- Size gate: **ok**"))

    def test_warning_passes(self):
        code, out, _ = self.run_gate(SLOT * 90 // 100)
        self.assertEqual(code, 0)
        self.assertIn("size gate warning", out)

    def test_failure_exits_1(self):
        code, out, summary = self.run_gate(SLOT)
        self.assertEqual(code, 1)
        self.assertIn("size gate FAILED", out)
        self.assertIn("**FAILED**", summary)

    def test_missing_image_exits_1(self):
        with redirect_stderr(io.StringIO()), tempfile.TemporaryDirectory() as tmp:
            code = size_gate.main(["--env", "papermono", "--app", str(Path(tmp) / "none.bin")])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
