"""Read an ESP-IDF partition table and check the rules CrossMono relies on (ADR 0005).

Used by scripts/mono/size_gate.py and test/mono/test_partitions.py.
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

FLASH_SIZE = 0x1000000  # 16 MB on both models (board_upload.flash_size)
TABLE_END = 0x9000  # the table itself is at 0x8000-0x8FFF
APP_ALIGN = 0x10000  # the ESP32-S3 maps app images in 64 KB pages
DATA_ALIGN = 0x1000


@dataclass(frozen=True)
class Partition:
    name: str
    type: str
    subtype: str
    offset: int
    size: int

    @property
    def end(self) -> int:
        return self.offset + self.size


def parse_size(text: str) -> int:
    """Parse an offset or size as ESP-IDF writes them: 0x7F0000, 8323072, 20K or 1M."""
    text = text.strip()
    scale = {"K": 1024, "M": 1024 * 1024}.get(text[-1:].upper(), 1)
    return int(text[:-1] if scale > 1 else text, 0) * scale


def parse(text: str) -> list[Partition]:
    """Parse the CSV text. Every row needs an explicit offset."""
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 5 or not fields[3] or not fields[4]:
            raise ValueError(f"line {number}: expected name, type, subtype, offset and size")
        name, type_, subtype, offset, size = fields[:5]
        result.append(Partition(name, type_, subtype, parse_size(offset), parse_size(size)))
    return result


def load(path: Path | str) -> list[Partition]:
    return parse(Path(path).read_text())


def check(table: list[Partition], flash_size: int = FLASH_SIZE) -> list[str]:
    """Return one message per broken rule; an empty list means the table is sound."""
    errors = []
    previous_end = TABLE_END
    for part in table:
        if part.offset < previous_end:
            errors.append(f"{part.name} at {part.offset:#x} overlaps the region before it (ends {previous_end:#x})")
        align = APP_ALIGN if part.type == "app" else DATA_ALIGN
        if part.offset % align:
            errors.append(f"{part.name} at {part.offset:#x} is not {align:#x}-aligned")
        previous_end = max(previous_end, part.end)
    if previous_end > flash_size:
        errors.append(f"the table ends at {previous_end:#x}, past the end of the {flash_size:#x}-byte flash")

    apps = [part for part in table if part.type == "app"]
    if [part.subtype for part in apps] != ["ota_0", "ota_1"]:
        errors.append(f"expected app slots ota_0 and ota_1, found {[part.subtype for part in apps]}")
    elif apps[0].size != apps[1].size:
        errors.append(f"app slots differ in size ({apps[0].size:#x}, {apps[1].size:#x}); an image might fit only one")

    if any(part.subtype == "spiffs" for part in table):
        errors.append("the table has a spiffs partition; nothing mounts it, and ADR 0005 gives its space to the apps")
    return errors


def app_slot(table: list[Partition]) -> Partition:
    """The ota_0 slot, which every app image (USB or OTA) must fit."""
    for part in table:
        if part.type == "app" and part.subtype == "ota_0":
            return part
    raise ValueError("the table has no ota_0 slot")


def env_partitions_file(ini: Path | str, env: str) -> str:
    """The `board_build.partitions` file of `[env:<env>]` in platformio.ini, following `extends`.

    platformio.local.ini is not read.
    """
    # Inline comment prefixes as PlatformIO's own parser has them.
    config = configparser.ConfigParser(interpolation=None, strict=False, inline_comment_prefixes=("#", ";"))
    if not config.read(ini):
        raise FileNotFoundError(ini)
    section = f"env:{env}"
    if not config.has_section(section):
        raise ValueError(f"{ini} has no [{section}]")

    def lookup(name: str) -> str | None:
        if config.has_option(name, "board_build.partitions"):
            return config.get(name, "board_build.partitions").strip()
        for parent in config.get(name, "extends", fallback="").split(","):
            if parent.strip() and (value := lookup(parent.strip())):
                return value
        return None

    value = lookup(section) or (lookup("env") if config.has_section("env") else None)
    if not value:
        raise ValueError(f"[{section}] sets no board_build.partitions")
    return value
