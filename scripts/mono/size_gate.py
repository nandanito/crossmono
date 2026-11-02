"""Flash-size gate (ADR 0005, ADR 0010): the app image against its ota_0 slot.

    python3 scripts/mono/size_gate.py --env papermono-gh_release [--summary "$GITHUB_STEP_SUMMARY"]

Reads the partition table that platformio.ini sets for the environment. Warns at
85 % of the slot and exits 1 at 95 %. --summary appends one Markdown line.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import partitions

ROOT = Path(__file__).resolve().parents[2]
WARN_PERCENT = 85
FAIL_PERCENT = 95


def verdict(app_size: int, slot_size: int) -> str:
    if app_size * 100 >= slot_size * FAIL_PERCENT:
        return "fail"
    if app_size * 100 >= slot_size * WARN_PERCENT:
        return "warn"
    return "ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env", required=True, help="PlatformIO environment, e.g. papermono-gh_release")
    parser.add_argument("--app", type=Path, help="app image (default: .pio/build/<env>/firmware.bin)")
    parser.add_argument("--summary", type=Path, help="file to append a Markdown line to")
    args = parser.parse_args(argv)

    table_file = partitions.env_partitions_file(ROOT / "platformio.ini", args.env)
    slot = partitions.app_slot(partitions.load(ROOT / table_file))
    app = args.app or ROOT / ".pio" / "build" / args.env / "firmware.bin"
    if not app.is_file():
        print(f"size gate: {app} is missing; build {args.env} first", file=sys.stderr)
        return 1
    size = app.stat().st_size
    result = verdict(size, slot.size)

    # Rounded down, so the printed figure never reaches a threshold the verdict has not.
    percent = size * 1000 // slot.size / 10
    detail = (
        f"{size:,} B of {slot.size:,} B ({percent:.1f} %) in {slot.name} of {table_file}; "
        f"warning at {WARN_PERCENT} %, failure at {FAIL_PERCENT} %"
    )
    label = {"ok": "ok", "warn": "warning", "fail": "FAILED"}[result]
    annotation = {"ok": "", "warn": "::warning::", "fail": "::error::"}[result]
    if os.environ.get("GITHUB_ACTIONS") != "true":
        annotation = ""
    print(f"{annotation}size gate {label} for {args.env}: {detail}")
    if args.summary:
        with args.summary.open("a") as summary:
            summary.write(f"- Size gate: **{label}**, {detail}\n")
    return 1 if result == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
