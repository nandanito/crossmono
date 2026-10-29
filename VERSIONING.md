# Versioning

How CrossMono numbers its releases, and how the firmware's update check uses those numbers. The decision behind
this is [ADR 0004](docs/decisions/0004-versioning.md).

Status: the scheme is decided; the build changes below are made in the 0.1.0 work. Until then the build still
reports CrossPoint's version.

## Scheme

- [SemVer](https://semver.org) `MAJOR.MINOR.PATCH`, starting at `0.1.0`.
- Before 1.0, a minor release (`0.2.0`) is a roadmap milestone and a patch release (`0.2.1`) is fixes only.
- Release candidates: `0.2.0-rc.1`, `0.2.0-rc.2`, …

## Tags

- Tags have **no `v` prefix**: `0.1.0`, `0.1.0-rc.1`. The updater parses versions with `sscanf("%d.%d.%d")`
  (`src/network/OtaUpdater.cpp:105-106`) and cannot read a leading `v`.
- A release candidate is published on GitHub with the **pre-release** flag; a final release without it.
- Upstream tags are fetched as `upstream/<tag>` and never pushed ([docs/upstream-sync.md](docs/upstream-sync.md)).

## Version string per environment

The firmware reads its version from the `CROSSPOINT_VERSION` define everywhere (boot screen, About, OTA,
User-Agent). We keep that define name, so upstream code works unchanged, and fill it from our own version.

| Environment | `CROSSPOINT_VERSION` | Example |
|---|---|---|
| `papermono` (development) | `<version>-dev+<short sha>` | `0.1.0-dev+3f2a1c9` |
| `papermono-gh_release_rc` | `<version>-rc.<n>` | `0.1.0-rc.1` |
| `papermono-gh_release` | `<version>` | `0.1.0` |

Planned changes in `platformio.ini` (0.1.0):

- A new `[crossmono]` section with `version = 0.1.0`. This is the one place the version is bumped.
- The three PaperMono environments set `-DCROSSPOINT_VERSION` from `${crossmono.version}` (today:
  `platformio.ini:584,603,620`, from `${crosspoint.version}`).
- `-DCROSSMONO_UPSTREAM_VERSION=\"${crosspoint.version}\"` records the CrossPoint base. Upstream maintains
  `[crosspoint] version`, so it follows each sync with no work from us.
- The rc number comes from the release workflow (environment variable), like upstream's `CROSSPOINT_RC_HASH`.
- The development suffix (`-dev+<sha>`) comes from a pre-build script in our own files. Upstream's
  `scripts/git_branch.py` only stamps the `default` and `sticky` environments.
- The FreeInk SDK commit (`git -C freeink-sdk rev-parse --short HEAD`) is injected at build time as
  `CROSSMONO_SDK_COMMIT`.

About shows all three: CrossMono version, CrossPoint base, SDK commit.

## How the updater decides

The updater fetches `releases/latest` of our repository, which never returns a pre-release, and compares its tag
with `CROSSPOINT_VERSION` (`src/network/OtaUpdater.cpp:94-135`):

1. Equal strings: no update.
2. Otherwise compare major, then minor, then patch; a higher number wins.
3. If all three are equal and the current version contains `-rc`, the release counts as newer.

| Device runs | Latest release | Offered? |
|---|---|---|
| `0.1.0-rc.1` | `0.1.0` | yes (rule 3) |
| `0.1.0` | `0.1.1` | yes |
| `0.1.0` | `0.1.0` | no |
| `0.1.0-dev+3f2a1c9` | `0.1.0` | no (dev builds only get higher versions) |
| `0.1.0-dev+3f2a1c9` | `0.1.1` | yes |
| any | `0.2.0-rc.1` | never: pre-releases are not "latest" |
| `0.2.0` | `0.1.5` | no: older |

Rules that follow from this:

- Never put `-rc` in a development version string.
- Release candidates are installed by hand until the opt-in "release candidate" channel exists (planned for 0.3.0,
  [docs/roadmap.md](docs/roadmap.md)).
- A fix for an older line (for example `0.1.5` after `0.2.0`) must be published with "Set as latest release"
  turned off, or every device on `0.2.x` is told to look at an older release.

## Asset names and the board tag

- OTA image: `crossmono-<version>-papermono.bin`. Full image: `crossmono-<version>-papermono-full.bin`.
- The board tag stays `papermono` (`src/network/FirmwareBoardTag.cpp:19`), embedded as
  `CROSSPOINT-BOARD-V1:papermono;` (line 50). The OTA asset suffix buffer allows board names up to 18 characters
  (`src/network/OtaUpdater.cpp:44`); `assetName` is 48 bytes (line 49), enough for `crossmono-<tag>-papermono.bin`
  with tags up to 23 characters.
- Because the tag is shared, the board-tag check does not stop a CrossMono app image on a CrossPoint device, or the
  other way round. The size check still applies: CrossPoint's SD flasher rejects an image larger than the
  device's app slot as `TOO_LARGE` (`src/network/FirmwareFlasher.cpp:125-129`), and a CrossPoint device has
  6,553,600-byte slots. Once a CrossMono image passes that size, it can only be installed with a full flash. The
  partition tables differ ([ADR 0005](docs/decisions/0005-partitions.md)), which is why the first install is
  always a full flash.

## CHANGELOG

`CHANGELOG.md` follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/):

```markdown
## [Unreleased]

## [0.1.0] - 2026-MM-DD

### Added
### Changed
### Fixed
### Upstream
- CrossPoint base: 2.0.0 (`<commit>`)
- FreeInk SDK: `<commit>`
- Notable upstream changes in this release
```

Use the standard sections (Added, Changed, Deprecated, Removed, Fixed, Security) as needed. **Upstream** is always
present.
