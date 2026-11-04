"""Check scripts/mono/make_logo.py and the logo files it writes (ADR 0007).

Run with python3 test/mono/test_make_logo.py. The rendering tests need cairosvg and Pillow and are skipped without
them.
"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import make_logo  # noqa: E402


def can_rasterize() -> bool:
    try:
        import cairosvg  # noqa: F401
        import PIL  # noqa: F401
    except (ImportError, OSError):  # OSError: cairosvg is installed but the cairo library is not found
        return False
    return True


def shown_in_portrait(stored: list[list[int]]) -> list[list[int]]:
    """What the UI shows for a stored image: in Portrait, logical (x, y) is panel (y, panelHeight - 1 - x)
    (rotateCoordinates in lib/GfxRenderer/GfxRenderer.cpp), and drawImage copies the bytes unrotated."""
    width = len(stored)
    return [[stored[width - 1 - x][y] for x in range(width)] for y in range(len(stored[0]))]


class Pack(unittest.TestCase):
    def test_first_pixel_is_the_high_bit_and_white_is_one(self):
        self.assertEqual(make_logo.pack([[255, 0, 0, 0, 0, 0, 0, 0]]), b"\x80")
        self.assertEqual(make_logo.pack([[0, 0, 0, 0, 0, 0, 0, 255]]), b"\x01")

    def test_threshold(self):
        self.assertEqual(make_logo.pack([[127, 128, 0, 0, 0, 0, 0, 0]]), b"\x40")

    def test_row_by_row(self):
        rows = [[255] * 8 + [0] * 8, [0] * 8 + [255] * 8]
        self.assertEqual(make_logo.pack(rows), b"\xff\x00\x00\xff")

    def test_width_must_be_a_multiple_of_eight(self):
        with self.assertRaises(ValueError):
            make_logo.pack([[0] * 12])
        with self.assertRaises(ValueError):
            make_logo.pack([[0] * 8, [0] * 16])


class ToPanel(unittest.TestCase):
    def test_turns_counter_clockwise(self):
        self.assertEqual(make_logo.to_panel([[1, 2, 3], [4, 5, 6]]), [[3, 6], [2, 5], [1, 4]])

    def test_shown_upright(self):
        rows = [[x * 10 + y for x in range(8)] for y in range(3)]
        self.assertEqual(shown_in_portrait(make_logo.to_panel(rows)), rows)


class Header(unittest.TestCase):
    def test_round_trip(self):
        data = bytes(range(40))
        text = make_logo.header("TestLogo", data, 16, 20)
        self.assertEqual(make_logo.parse_header(text), ("TestLogo", 16, 20, data))

    def test_fits_the_column_limit(self):
        text = make_logo.header("TestLogo", bytes(1800), 120, 120)
        self.assertLessEqual(max(len(line) for line in text.splitlines()), 120)

    def test_committed_logo(self):
        name, width, height, data = make_logo.parse_header(make_logo.HEADER.read_text(encoding="utf-8"))
        self.assertEqual((name, width, height), ("MonoLogo120", 120, 120))
        self.assertEqual(len(data), 120 * 120 // 8)

    def test_favicon_is_the_logo(self):
        self.assertEqual(make_logo.FAVICON.read_bytes(), make_logo.SVG.read_bytes(), "run scripts/mono/make_logo.py")


@unittest.skipUnless(can_rasterize(), "needs cairosvg and Pillow (scripts/requirements.txt)")
class Rasterize(unittest.TestCase):
    def test_transparent_is_white(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><rect width="8" height="8"/></svg>'
        rows = make_logo.rasterize(svg, 16)
        self.assertEqual(len(rows), 16)
        self.assertEqual(rows[2][:8], [0] * 8)
        self.assertEqual(rows[2][8:], [255] * 8)
        self.assertEqual(rows[12], [255] * 16)

    def test_committed_logo_matches_the_svg(self):
        expected = make_logo.pack(make_logo.to_panel(make_logo.rasterize(make_logo.SVG.read_bytes(), make_logo.SIZE)))
        _, _, _, data = make_logo.parse_header(make_logo.HEADER.read_text(encoding="utf-8"))
        self.assertEqual(data, expected, "run scripts/mono/make_logo.py")


if __name__ == "__main__":
    unittest.main()
