# Releasing CrossMono

Status: the release workflow and the flasher page are built in the 0.1.0 work. This file is the procedure they
must support. Version rules are in [VERSIONING.md](VERSIONING.md).

Nothing here is done without Nandan's go-ahead: tagging, publishing and announcing are each confirmed.

## 1. Pre-flight

- [ ] **Upstream.** Is there a CrossPoint release we have not merged? If yes, sync first or note in the release
      notes why not ([docs/upstream-sync.md](docs/upstream-sync.md)).
- [ ] **CHANGELOG.** Move the `[Unreleased]` entries to the new version with today's date. Fill **Upstream**
      (CrossPoint base version and commit, SDK commit).
- [ ] **Version.** Bump `[crossmono] version` in `platformio.ini` in a PR. The tag must match it.
- [ ] **CI green** on `main` for the commit to be tagged, including the flash-size gate and host tests.
- [ ] **Hardware.** Run [docs/hardware-test-checklist.md](docs/hardware-test-checklist.md) with a build of that
      commit, on the full model. For a final release, the Lite as well (or a tester's report).

## 2. Release candidate

1. Tag the commit on `main`: `git tag -s 0.2.0-rc.1 <commit>` and push the tag (`git push origin 0.2.0-rc.1`;
   never `--tags`, which would push the `upstream/*` tags).
2. The release workflow builds and attaches the assets, and creates the GitHub release with the **pre-release**
   flag.
3. Ask testers to install it by hand (web flasher or esptool). OTA does not offer pre-releases.
4. Fixes go to `main` through PRs; the next candidate is `-rc.2`.

## 3. Final release

1. Tag the same commit as the last good candidate, or a later one that passed the checklist: `git tag -s 0.2.0`.
2. The release workflow publishes a normal release, marked as latest. Devices on `0.2.0-rc.N` and older versions
   are offered it through OTA.

## What CI produces

| Asset | Contents |
|---|---|
| `crossmono-<version>-papermono.bin` | OTA app image (written to an app slot) |
| `crossmono-<version>-papermono-full.bin` | Merged image for offset 0x0: bootloader, partition table, OTA data, app |
| `crossmono-<version>-papermono.elf` | Symbols for decoding crash backtraces |
| `SHA256SUMS` | SHA-256 of every asset above |
| `manifest.json` | ESP Web Tools manifest pointing at the full image |

Before upload the workflow checks that the full image starts with the 0xE9 magic byte, that the version string
inside the app matches the tag, and that the app fits the slot.

## 4. Flasher site

- Copy the full image and `manifest.json` into `crossmono/crossmono.github.io` (same origin, no CORS), under a
  folder per version, and point the "current" manifest at it.
- Pre-releases get their own manifest, offered on the page with a clear "test build" label.
- Check the page in Chrome or Edge with a device: connect, flash, boot.

## 5. After the release

- Announce in the channels from [ADR 0011](docs/decisions/0011-community-launch.md), with the standard wording.
- Ask M5Stack to update the PaperMono docs listing, if we are listed.
- Close the milestone; open the next one from [docs/roadmap.md](docs/roadmap.md).

## Hotfix

1. Branch `hotfix/<version>` from the release tag, fix, PR into `main` first if `main` has the same bug.
2. Release the patch version (`0.2.1`) from the hotfix branch with the same pre-flight (checklist items that the
   fix touches, plus boot and OTA).
3. If the fix is for an older line (a newer minor is already out), publish it with "Set as latest release" turned
   off (`gh release edit <tag> --latest=false`). Otherwise devices on the newer line would be pointed at an older
   release.
