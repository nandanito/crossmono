"""CrossMono version flags (ADR 0004, VERSIONING.md): a PlatformIO pre-build script.

    extra_scripts =
      ${base.extra_scripts}
      pre:scripts/mono/version_flags.py

Defines three macros in the translation units that mention one of them, the way upstream's
scripts/git_branch.py does, so a new commit rebuilds a few files and not the tree:

    CROSSPOINT_VERSION          0.1.0-dev+<sha> | 0.1.0-rc.<CROSSMONO_RC> | 0.1.0, by environment
    CROSSMONO_UPSTREAM_VERSION  the CrossPoint base, [crosspoint] version
    CROSSMONO_SDK_COMMIT        short commit of the checked-out freeink-sdk submodule

The environment name picks the form: `-gh_release_rc` is a release candidate and needs CROSSMONO_RC
in the environment, `-gh_release` a release, anything else a development build. An environment that
runs this script must not set -DCROSSPOINT_VERSION itself.

    python3 scripts/mono/version_flags.py [--env papermono]    # print the values without building
"""

from __future__ import annotations

import argparse
import configparser
import os
import re
import subprocess
import sys
from pathlib import Path

MACROS = ("CROSSPOINT_VERSION", "CROSSMONO_UPSTREAM_VERSION", "CROSSMONO_SDK_COMMIT")
RC_VARIABLE = "CROSSMONO_RC"
# What the updater's sscanf("%d.%d.%d") reads (src/network/OtaUpdater.cpp): no "v", no suffix.
VERSION = re.compile(r"\d+\.\d+\.\d+")
RC_NUMBER = re.compile(r"[1-9]\d*")
SHORT_SHA = 7  # at least 7 characters (git lengthens an ambiguous one); the same locally and in CI


class VersionError(Exception):
    """The flags cannot be composed; the message ends the build."""


def kind(env_name: str) -> str:
    """'rc', 'release' or 'dev' from the environment's suffix (upstream's naming)."""
    if env_name.endswith("-gh_release_rc"):
        return "rc"
    if env_name.endswith("-gh_release"):
        return "release"
    return "dev"


def compose(env_name: str, version: str, rc: str | None, sha: str) -> str:
    """The CROSSPOINT_VERSION value: the table in VERSIONING.md."""
    if not VERSION.fullmatch(version):
        raise VersionError(f"[crossmono] version {version!r} is not MAJOR.MINOR.PATCH")
    form = kind(env_name)
    if form == "release":
        return version
    if form == "rc":
        if not rc:
            raise VersionError(f"{env_name} needs the candidate number: set {RC_VARIABLE}=1 for {version}-rc.1")
        if not RC_NUMBER.fullmatch(rc):
            raise VersionError(f"{RC_VARIABLE}={rc!r} is not a whole number from 1 up")
        return f"{version}-rc.{rc}"
    return f"{version}-dev+{sha}"


def read_versions(ini: Path | str) -> tuple[str, str]:
    """([crossmono] version, [crosspoint] version) from platformio.ini."""
    config = configparser.ConfigParser(interpolation=None, strict=False, inline_comment_prefixes=("#", ";"))
    if not config.read(ini, encoding="utf-8"):
        raise VersionError(f"{ini} not found")
    found = []
    for section in ("crossmono", "crosspoint"):
        if not config.has_option(section, "version"):
            raise VersionError(f"{ini} has no [{section}] version")
        found.append(config.get(section, "version").strip())
    return found[0], found[1]


def git_short_sha(repo: Path) -> str:
    """HEAD of the checkout at `repo`, or "unknown" without one (a source archive, an empty submodule)."""
    if not (repo / ".git").exists():  # a directory, or a file in a submodule
        print(f"version_flags.py: {repo.name} is not a git checkout; its commit is 'unknown'", file=sys.stderr)
        return "unknown"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", f"--short={SHORT_SHA}", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = (getattr(error, "stderr", "") or str(error)).strip()
        print(f"version_flags.py: git failed for {repo.name} ({detail}); its commit is 'unknown'", file=sys.stderr)
        return "unknown"
    return result.stdout.strip()


def clean(value: str) -> str:
    """Drop the characters that would break the C string literal."""
    return "".join(c for c in value if c not in '"\\')


def values(env_name: str, rc: str | None, root: Path) -> dict[str, str]:
    """The three macro values for one environment; `root` is the repository."""
    version, upstream = read_versions(root / "platformio.ini")
    sha = git_short_sha(root) if kind(env_name) == "dev" else ""
    return {
        "CROSSPOINT_VERSION": compose(env_name, version, rc, sha),
        "CROSSMONO_UPSTREAM_VERSION": clean(upstream),
        "CROSSMONO_SDK_COMMIT": git_short_sha(root / "freeink-sdk"),
    }


def uses_version_macros(source: bytes) -> bool:
    return any(macro.encode() in source for macro in MACROS)


def inject(env) -> None:
    """SCons entry point: define the macros in the units that use them."""
    try:
        flags = values(env["PIOENV"], os.environ.get(RC_VARIABLE), Path(env["PROJECT_DIR"]))
    except VersionError as error:
        print(f"Error [version_flags.py]: {error}", file=sys.stderr)
        sys.exit(1)
    defines = [(name, f'\\"{value}\\"') for name, value in flags.items()]

    def add_defines(build_env, node):
        if not uses_version_macros(node.srcnode().get_contents()):
            return node
        unit_env = build_env.Clone()
        unit_env.Append(CPPDEFINES=defines)
        return unit_env.Object(node)

    env.AddBuildMiddleware(add_defines)
    print(
        f"CrossMono build version: {flags['CROSSPOINT_VERSION']} "
        f"(CrossPoint {flags['CROSSMONO_UPSTREAM_VERSION']}, SDK {flags['CROSSMONO_SDK_COMMIT']})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env", default="papermono", help="PlatformIO environment (default: papermono)")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]  # __file__ is undefined under SCons; inject() uses PROJECT_DIR
    try:
        for name, value in values(args.env, os.environ.get(RC_VARIABLE), root).items():
            print(f"{name}={value}")
    except VersionError as error:
        print(f"version_flags.py: {error}", file=sys.stderr)
        return 1
    return 0


try:
    Import("env")  # noqa: F821  SCons defines Import only inside a PlatformIO build
except NameError:
    if __name__ == "__main__":
        sys.exit(main())
else:
    inject(env)  # noqa: F821
