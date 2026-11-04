"""Decode a flash read-back: the partition table and the app slot the bootloader starts next.

    esptool --chip esp32s3 read-flash 0x8000 0x8000 readback.bin
    python3 scripts/mono/flash_slots.py readback.bin

Also reads a full image that starts at offset 0x0, such as firmware.factory.bin. Follows the
ESP-IDF bootloader with app rollback on (CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE in the prebuilt
sdkconfig; bootloader_utility.c, bootloader_common_loader.c): an otadata entry marked INVALID or
ABORTED is skipped, and an entry still PENDING_VERIFY is marked ABORTED at the next boot.
"""

from __future__ import annotations

import argparse
import binascii
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

TABLE_OFFSET = 0x8000
TABLE_SIZE = 0xC00
ENTRY_SIZE = 32
ENTRY_MAGIC = b"\xaa\x50"
SECTOR = 0x1000
UNUSED = 0xFFFFFFFF

APP, DATA = 0x00, 0x01
FACTORY, OTA_FIRST, OTA_LAST = 0x00, 0x10, 0x1F
DATA_OTA = 0x00

NEW, PENDING_VERIFY, VALID, INVALID, ABORTED = range(5)
STATES = {NEW: "NEW", PENDING_VERIFY: "PENDING_VERIFY", VALID: "VALID", INVALID: "INVALID", ABORTED: "ABORTED",
          UNUSED: "UNDEFINED"}


class DecodeError(Exception):
    """The file is not a read-back this script understands."""


@dataclass(frozen=True)
class Partition:
    name: str
    type: int
    subtype: int
    offset: int
    size: int


@dataclass(frozen=True)
class OtaEntry:
    address: int
    seq: int
    state: int
    crc: int

    @property
    def crc_ok(self) -> bool:
        # esp_rom_crc32_le(UINT32_MAX, &ota_seq, 4)
        return self.crc == binascii.crc32(struct.pack("<I", self.seq), UNUSED)

    @property
    def state_at_boot(self) -> int:
        return ABORTED if self.state == PENDING_VERIFY else self.state

    @property
    def skipped(self) -> bool:
        """bootloader_common_ota_select_invalid(), after the PENDING_VERIFY step."""
        return self.seq == UNUSED or self.state_at_boot in (INVALID, ABORTED)

    @property
    def usable(self) -> bool:
        """bootloader_common_ota_select_valid()."""
        return not self.skipped and self.crc_ok


class Flash:
    """A read-back that starts at the partition table (0x8000), or a full image from 0x0."""

    def __init__(self, data: bytes):
        if data[:2] == ENTRY_MAGIC:
            self.start = TABLE_OFFSET
        elif data[TABLE_OFFSET : TABLE_OFFSET + 2] == ENTRY_MAGIC:
            self.start = 0
        else:
            raise DecodeError("no partition table at the start of the file or at 0x8000")
        self.data = data

    def read(self, address: int, length: int) -> bytes:
        begin = address - self.start
        if begin < 0 or begin + length > len(self.data):
            raise DecodeError(f"{address:#x}-{address + length - 1:#x} is not in the file")
        return self.data[begin : begin + length]


def partitions(flash: Flash) -> list[Partition]:
    found = []
    for i in range(0, TABLE_SIZE, ENTRY_SIZE):
        entry = flash.read(TABLE_OFFSET + i, ENTRY_SIZE)
        if entry[:2] != ENTRY_MAGIC:  # 0xEBEB (MD5 row) or 0xFFFF ends the table
            break
        ptype, subtype, offset, size = struct.unpack_from("<BBII", entry, 2)
        name = entry[12:28].split(b"\0", 1)[0].decode("ascii", "replace")
        found.append(Partition(name, ptype, subtype, offset, size))
    return found


def otadata(flash: Flash, table: list[Partition]) -> list[OtaEntry]:
    ota = next((p for p in table if p.type == DATA and p.subtype == DATA_OTA), None)
    if ota is None:
        return []
    entries = []
    for address in (ota.offset, ota.offset + SECTOR):
        seq, state, crc = struct.unpack_from("<I20xII", flash.read(address, 32))
        entries.append(OtaEntry(address, seq, state, crc))
    return entries


def ota_apps(table: list[Partition]) -> dict[int, Partition]:
    return {p.subtype - OTA_FIRST: p for p in table if p.type == APP and OTA_FIRST <= p.subtype <= OTA_LAST}


def next_boot(table: list[Partition], entries: list[OtaEntry]) -> tuple[str, Partition | None, OtaEntry | None]:
    """The slot label, its partition and the otadata entry that selects it."""
    apps = ota_apps(table)
    usable = [e for e in entries if e.usable]
    if apps and usable:
        active = max(usable, key=lambda e: e.seq)
        slot = (active.seq - 1) % len(apps)
        return f"ota_{slot}", apps.get(slot), active
    factory = next((p for p in table if p.type == APP and p.subtype == FACTORY), None)
    if factory is not None:
        return "factory", factory, None
    return "ota_0", apps.get(0), None


def report(data: bytes) -> list[str]:
    flash = Flash(data)
    table = partitions(flash)
    lines = [f"Partition table at {TABLE_OFFSET:#x}:"]
    for p in table:
        lines.append(f"  {p.name:9} type {p.type:#04x} subtype {p.subtype:#04x} offset {p.offset:#09x} "
                     f"size {p.size:#09x}")
    entries = otadata(flash, table)
    if not entries:
        lines.append("No otadata partition.")
    for e in entries:
        if e.seq == UNUSED:
            verdict = "unused"
        elif not e.crc_ok:
            verdict = "bad CRC, skipped"
        elif e.skipped:
            verdict = f"skipped ({STATES[e.state_at_boot]} at boot)"
        else:
            verdict = "usable"
        state = STATES.get(e.state, hex(e.state))
        lines.append(f"otadata {e.address:#x}: seq {e.seq:#x} state {state}, {verdict}")
    label, app, active = next_boot(table, entries)
    where = f"{app.name} at {app.offset:#x}" if app else "not in the table"
    if active is None:
        lines.append(f"No usable otadata entry: the bootloader starts {label} ({where}).")
    else:
        lines.append(f"Boots {label} ({where}), image state {STATES.get(active.state, hex(active.state))}.")
    newest = max((e for e in entries if e.seq != UNUSED and e.crc_ok), key=lambda e: e.seq, default=None)
    if newest is not None and newest.skipped:
        lines.append(f"Rolled back: the newest entry (seq {newest.seq:#x}) was rejected.")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path, help="read-back of 0x8000-0xFFFF, or a full image from 0x0")
    args = parser.parse_args(argv)
    try:
        print("\n".join(report(args.file.read_bytes())))
    except (OSError, DecodeError) as error:
        print(f"flash_slots.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
