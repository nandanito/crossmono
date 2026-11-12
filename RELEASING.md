# Releasing CrossMono

Status: the release workflow is in place ([below](#the-release-workflow)), and the install page is live at
https://crossmono.github.io ([4. Flasher site](#4-flasher-site)). The first release, `0.1.0`, was published on
2026-11-07 (after `0.1.0-rc.1` on 2026-11-06); the install page offers it, and devices on `0.1.0-rc.1` are offered it
over Wi-Fi. Version rules are in [VERSIONING.md](VERSIONING.md).

Nothing here is done without Nandan's go-ahead: tagging, publishing and announcing are each confirmed.

## 1. Pre-flight

- [ ] **Upstream.** Is there a CrossPoint release we have not merged? If yes, sync first or note in the release
      notes why not ([docs/upstream-sync.md](docs/upstream-sync.md)).
- [ ] **CHANGELOG.** Move the `[Unreleased]` entries to a section named exactly as the tag, with today's date:
      `## [0.2.0-rc.1] - YYYY-MM-DD`. Every candidate gets its own section. Fill **Upstream** (CrossPoint base
      version and commit, SDK commit). The workflow takes the release notes from this section and stops without
      it.
- [ ] **Version.** Bump `[crossmono] version` in `platformio.ini` in a PR. The tag must match it.
- [ ] **CI green** on `main` for the commit to be tagged, including the flash-size gate and host tests.
- [ ] **Dry run** of the release workflow on that commit (below); download the artifact and check it.
- [ ] **Hardware.** Run [docs/hardware-test-checklist.md](docs/hardware-test-checklist.md) with a build of that
      commit, on the full model. For a final release, the Lite as well (or a tester's report). Without either, the
      release notes say that the Lite has not been tested ([ADR 0013](docs/decisions/0013-lite-untested-at-0-1-0.md)).

## 2. Release candidate

1. Tag the commit on `main`: `git tag -s 0.2.0-rc.1 <commit>` and push the tag (`git push origin 0.2.0-rc.1`;
   never `--tags`, which would push the `upstream/*` tags).
2. The release workflow builds and checks the assets, and creates the GitHub release with them and the
   **pre-release** flag.
3. Ask testers to install it by hand (web flasher or esptool). OTA does not offer pre-releases.
4. Fixes go to `main` through PRs; the next candidate is `-rc.2`.

### Testing OTA with a candidate

OTA reads `releases/latest`, which never returns a pre-release. To install a candidate over OTA before the final:

1. Point a development build at the candidate's release in `platformio.local.ini` (never committed):

   ```ini
   [env:papermono]
   build_src_flags = -DCROSSMONO_OTA_RELEASE_URL=\"https://api.github.com/repos/nandanito/crossmono/releases/tags/0.1.0-rc.1\"
   ```

2. Give that build a lower version: set `[crossmono] version = 0.0.0` in `platformio.ini` locally, without
   committing it. A development build of the same version (`0.1.0-dev+<sha>`) is never offered `0.1.0-rc.1`
   ([VERSIONING.md](VERSIONING.md#how-the-updater-decides)).
3. `pio run -e papermono -t upload`, then Settings → System → Check for Updates → Update. About shows the
   candidate after the restart.
4. In download mode, `esptool --chip esp32s3 read-flash 0x8000 0x8000 readback.bin` and
   `python3 scripts/mono/flash_slots.py readback.bin`. After `pio run -t upload` the device runs app0, so expect
   `Boots ota_1 (app1 at 0x800000)`; a `Rolled back` line means the bootloader rejected the new image.
5. Undo the local version change and remove the override.

## 3. Final release

1. Tag the same commit as the last good candidate, or a later one that passed the checklist: `git tag -s 0.2.0`.
2. The release workflow publishes a normal release, marked as latest. Devices on `0.2.0-rc.N` and older versions
   are offered it through OTA, except 0.1.0 and 0.2.0-rc.1: they cannot update over Wi-Fi and need a USB install
   ([ADR 0015](docs/decisions/0015-sdk-pin-ahead-of-a-release.md)).

## The release workflow

`.github/workflows/release.yml` runs when a tag `N.N.N` or `N.N.N-rc.N` is pushed:

1. `scripts/mono/package_release.py --check-tag` checks the tag against `[crossmono] version` in `platformio.ini`
   and picks the build: `papermono-gh_release`, or `papermono-gh_release_rc` with `CROSSMONO_RC=N`.
   `scripts/mono/changelog.py <tag>` takes the release notes from `CHANGELOG.md`. Either one stops the run before
   the build.
2. The build runs without a PlatformIO cache.
3. `scripts/mono/release_license.py` writes the licence file: every licence text of the image, from the
   libraries this build downloaded, the platform packages and the repository.
4. `package_release.py` checks the build and the licence file and writes the assets (below), then runs the
   flash-size gate.
5. The assets are uploaded as a workflow artifact, `crossmono-<tag>`, kept for 7 days.
6. `gh release create --verify-tag` creates the release from the existing tag with the assets and the notes:
   `--prerelease` for a candidate, `--latest` for a final release.

It can also be started by hand with a `tag` and `dry_run`. A **dry run** builds the branch it is started on,
names the assets after `tag`, and stops after step 5; a missing CHANGELOG section is only a warning there.
Without `dry_run` it builds the existing tag and publishes it, as a push would.

```sh
gh workflow run release.yml --repo nandanito/crossmono -f tag=0.1.0 -f dry_run=true
gh run list --repo nandanito/crossmono --workflow release.yml --limit 1
gh run download <run id> --repo nandanito/crossmono --name crossmono-0.1.0 --dir dry-run
(cd dry-run/dist && shasum -a 256 -c SHA256SUMS)
```

Build releases in CI only. Locally, `firmware.bin` can come from the build cache (`build_cache_dir = .cache` in
`platformio.ini`); then PlatformIO does not write the full image again, and the packager refuses a missing or
stale one. To check the packager locally, build with a new, empty `PLATFORMIO_BUILD_CACHE_DIR` and use the same
value for every `pio` command in that session. The licence file needs the nested Lucide submodule
(`git submodule update --init --recursive`), as CI has it:

```sh
export PLATFORMIO_BUILD_CACHE_DIR="$(mktemp -d)"
~/.local/bin/pio run -e papermono-gh_release
python3 scripts/mono/release_license.py --tag 0.1.0 --env papermono-gh_release --out /tmp/LICENSE.txt
python3 scripts/mono/package_release.py --tag 0.1.0 --license /tmp/LICENSE.txt --out "$(mktemp -d)/dist"
```

## What the workflow produces

| Asset | Contents |
|---|---|
| `crossmono-<version>-papermono.bin` | OTA app image (written to an app slot) |
| `crossmono-<version>-papermono-full.bin` | Merged image for offset 0x0: bootloader, partition table, OTA data, app |
| `crossmono-<version>-papermono.elf` | Symbols for decoding crash backtraces |
| `manifest.json` | ESP Web Tools manifest: one part, the full image at offset 0 |
| `crossmono-<version>-LICENSE.txt` | Every licence: a header with the tag, the source and SDK commits, the source links and the GPLv3 statement; `LICENSE`; `THIRD-PARTY-NOTICES`; the GPL-3.0 text; then the full text of each licence that `THIRD-PARTY-NOTICES` names, and where each downloaded library came from |
| `SHA256SUMS` | SHA-256 of the five assets above, for `sha256sum -c` |

Before writing them, `package_release.py` checks:

- the app image starts with the 0xE9 magic byte and the ESP32-S3 chip ID, and holds `CrossMono-ESP32-<tag>` (the
  User-Agent, so the version is exactly the tag) and the `CROSSPOINT-BOARD-V1:papermono;` board tag;
- the full image is exactly 0x10000 + the app size and ends with that app (so it is not stale);
- its bootloader at 0x0 has the 0xE9 magic byte, a 16 MB flash size and the ESP32-S3 chip ID; the partition table
  at 0x8000 is `partitions_papermono.csv`; NVS is blank; the otadata starts the app at 0x10000;
- the licence file names the tag and both commits, has the GPLv3 statement, and has every text that
  `release_license.py` lists (`release_license.check`);
- the `.elf` is an ELF file, and the app passes the flash-size gate.

The full image has NVS (0x9000-0xDFFF) blank, so an install from it erases the device secret and the Bluetooth
pairings; settings and books on the SD card stay ([ADR 0005](docs/decisions/0005-partitions.md)). The manifest
does not set `new_install_prompt_erase`, so ESP Web Tools also erases the whole flash before a new install, and
`new_install_improv_wait_time` is 0 because the firmware has no Improv Serial.

## 4. Flasher site

After the release workflow has published the release (ask first; this publishes the site):

```sh
gh workflow run publish-firmware.yml --repo crossmono/crossmono.github.io -f tag=<tag>
gh run list --repo crossmono/crossmono.github.io --workflow publish-firmware.yml --limit 1
```

- The workflow checks that the release exists (a pre-release for `-rc.N`, a normal release otherwise), downloads
  the full image, `manifest.json` and `SHA256SUMS`, checks them, and copies them to `firmware/<tag>/` on the site
  (same origin as the page, so no CORS). It points `manifest.json` (final release) or `manifest-rc.json` (release
  candidate, the page's "test build") at that folder, commits to the site's `main` and deploys it.
- **Keep-previous rule:** it keeps the folders that the two manifests use now and used just before this run, and
  deletes the rest. GitHub Pages caches files for 10 minutes, so leave 10 minutes between publishes of different
  tags. Publishing the same tag again deletes nothing.
- If the push fails because the site's `main` moved during the run, run it again.
- Wait up to 10 minutes for the cache, then check the page in Chrome or Edge with a device. **The device must be
  awake**: a sleeping PaperMono does not show up on USB. Install, let it restart, and check that About shows the
  tag.

Details: ADR 0009's 2026-11-05 addendum, and `firmware/README.md` in the site repository.

## 5. After the release

- Announce in the channels from [ADR 0011](docs/decisions/0011-community-launch.md), with the standard wording.
- Ask M5Stack to update the PaperMono docs listing, if we are listed.
- Close the milestone; open the next one from [docs/roadmap.md](docs/roadmap.md).

## Hotfix

1. Branch `hotfix/<version>` from the release tag, fix, PR into `main` first if `main` has the same bug.
2. Release the patch version (`0.2.1`) from the hotfix branch with the same pre-flight (checklist items that the
   fix touches, plus boot and OTA).
3. If the fix is for an older line (a newer minor is already out), turn off "Set as latest release" as soon as the
   workflow has published it (`gh release edit <tag> --latest=false`): the workflow marks every final release as
   latest. Otherwise devices on the newer line would be pointed at an older release.
