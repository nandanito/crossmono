"""Print one version's section of CHANGELOG.md, for the release notes (ADR 0004, Keep a Changelog).

    python3 scripts/mono/changelog.py 0.1.0-rc.1 > release-notes.md

Prints the body under "## [<version>] - YYYY-MM-DD", without the heading, up to the next "## ["
heading or the link definitions at the end. Exits 1 when the section is missing, empty, has no date
or has no "### Upstream" block (VERSIONING.md). "Unreleased" needs no date.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADING = re.compile(r"## \[(?P<version>[^\]]+)\](?:\s+-\s+(?P<date>\d{4}-\d{2}-\d{2}))?\s*")
LINK_DEFINITION = re.compile(r"\[[^\]]+\]:\s")
UNRELEASED = "Unreleased"


class ChangelogError(Exception):
    """The section cannot be used as release notes."""


def section(text: str, version: str) -> str:
    """The body of the version's section, stripped of blank lines at both ends."""
    body = None
    for line in text.splitlines():
        if body is not None:
            if line.startswith("## ") or LINK_DEFINITION.match(line):
                break
            body.append(line)
            continue
        heading = HEADING.fullmatch(line)
        if heading and heading["version"] == version:
            if version != UNRELEASED and not heading["date"]:
                raise ChangelogError(f"## [{version}] has no date; write it as ## [{version}] - YYYY-MM-DD")
            body = []
    if body is None:
        raise ChangelogError(f"CHANGELOG.md has no ## [{version}] section (written as ## [{version}] - YYYY-MM-DD)")
    notes = "\n".join(body).strip("\n")
    if not notes.strip():
        raise ChangelogError(f"## [{version}] is empty")
    if not re.search(r"^### Upstream\s*$", notes, re.MULTILINE):
        raise ChangelogError(f"## [{version}] has no ### Upstream block (VERSIONING.md)")
    return notes + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="the release tag, e.g. 0.1.0 or 0.1.0-rc.1, or Unreleased")
    parser.add_argument("--file", type=Path, default=ROOT / "CHANGELOG.md", help="default: CHANGELOG.md")
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(section(args.file.read_text(encoding="utf-8"), args.version))
    except (ChangelogError, OSError) as error:
        print(f"changelog.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
