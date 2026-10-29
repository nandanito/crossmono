# 0004. Versioning

- Status: Accepted
- Date: 2026-10-28

## Context

CrossPoint versions its firmware `1.6.5`, `2.0.0`, with pre-release tags like `2.0.0rc`. The version string is the
`CROSSPOINT_VERSION` build flag. The OTA updater compares it with the tag of the newest GitHub release
(`src/network/OtaUpdater.cpp:94-135`):

- equal strings → no update;
- otherwise both strings are parsed with `sscanf("%d.%d.%d")` (lines 105-106) and compared as major, minor, patch;
- if all three are equal and the current version contains `-rc` (line 130), the release counts as newer.

If parsing fails, the integers are left uninitialised, so a tag like `v0.1.0` would compare garbage. The updater
asks for `releases/latest` (line 22), which never returns a GitHub pre-release.

CrossMono is a different product from CrossPoint and is not yet stable.

## Options considered

1. **Continue CrossPoint's numbers with a suffix** (for example `2.0.0-mono.1`). Shows the base, but suggests a
   maturity we do not have, and our releases would not line up with upstream's anyway.
2. **Own SemVer from 0.1.0** (chosen). Shows clearly that this is a new, pre-1.0 product. The CrossPoint base is
   recorded next to it.
3. **Calendar versions** (`2026.11`). Says nothing about compatibility, and does not suit the updater's
   three-number comparison.

## Decision

- SemVer `0.y.z`. Tags have no `v`: `0.1.0`, and pre-releases `0.1.0-rc.1` (published with GitHub's pre-release
  flag).
- Version strings: release `0.1.0`; release candidate `0.1.0-rc.1`; development build `0.1.0-dev+<short sha>`.
- The updater's `-rc` rule already offers `0.1.0` to a device running `0.1.0-rc.1`. Release-candidate testers
  install candidates by hand until an opt-in "release candidate" update channel exists (planned for 0.3.0, see
  [docs/roadmap.md](../roadmap.md)).
- The CrossPoint base version and the FreeInk SDK commit are recorded in About, in the release notes and in the
  CHANGELOG.
- `CHANGELOG.md` follows Keep a Changelog.

Details (build flags per environment, CHANGELOG sections, updater behaviour) are in
[VERSIONING.md](../../VERSIONING.md).

## Consequences

- No `v` prefix, ever: the updater cannot parse it.
- Development builds (`-dev+<sha>`) are not offered the release with the same number, only higher ones. That is
  fine for builds made from source.
- When the `0.1.0` final is published, devices on `0.1.0-rc.N` are offered it through OTA.

## Sources

- `src/network/OtaUpdater.cpp:22,94-135` at `60d3c8bb`
- `platformio.ini:584,603,620` (`CROSSPOINT_VERSION` for the three PaperMono environments)
- SemVer 2.0.0: https://semver.org
- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- GitHub REST API, latest release (pre-releases excluded):
  https://docs.github.com/en/rest/releases/releases#get-the-latest-release
