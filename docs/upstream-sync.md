# Syncing with CrossPoint

CrossMono's `main` shares history with CrossPoint's `develop` ([ADR 0001](decisions/0001-repo-and-upstream.md)).
We merge upstream at each CrossPoint release. This file is the procedure, and the list of upstream files we edit
(the seams).

## One-time setup in a new clone

```sh
git remote add upstream https://github.com/crosspoint-reader/crosspoint-reader.git
git remote set-url --push upstream DISABLED        # never push to CrossPoint by accident
git config remote.upstream.tagOpt --no-tags        # keep upstream tags out of our tag namespace...
git config --add remote.upstream.fetch '+refs/tags/*:refs/tags/upstream/*'   # ...and fetch them as upstream/<tag>
git fetch upstream
git submodule update --init
```

Push our own tags one by one (`git push origin 0.1.0`), never with `--tags`.

## When to sync

- At every CrossPoint release (a new tag, final or `rc`). Last sync: `2.0.0` (`42d58daa`, FreeInk SDK
  `5e94fe7`).
- Between releases only for a fix we need; merge `upstream/develop` at a known commit, the same way.
- Goal for 1.0: never more than one CrossPoint release behind.

## Procedure

```sh
git fetch upstream
git switch main && git pull --ff-only
git switch -c sync/crosspoint-<version>
git merge --no-ff --log refs/tags/upstream/<version>   # or upstream/develop for a between-release sync
git submodule update --init                            # take upstream's SDK pin
```

Then:

1. Resolve conflicts with the rules below.
2. Check every seam in the table (`grep` for the CrossMono change in each file; it must still be there and still
   make sense).
3. Read the upstream changes to `.github/workflows/*`, `partitions.csv` and `platformio.ini` even if they merged
   cleanly; copy useful CI changes into our workflows by hand. Git can also merge an upstream hunk into our
   rewritten `ci.yml` without a conflict (the 2.0.0 sync did); check that result too. A change to `partitions.csv`
   does not change the PaperMono builds, but compare it with `partitions_papermono.csv`.
4. Read the SDK changes since the old pin (`git -C freeink-sdk log --oneline <old>..<new>`), especially anything
   for the PaperMono.
5. Build the development and release environments, run the host tests (`pio run -t unit-tests`), and run the size
   gate (`python3 scripts/mono/size_gate.py --env papermono-gh_release`).
6. Commit the merge, push the branch, open a PR titled `chore: sync CrossPoint <version>`. Note in the PR the new
   base commit, the new SDK pin and any seam that needed rework.
7. Merge with a **merge commit**. Never squash or rebase a sync.
8. Add the new base to the **Upstream** section of `CHANGELOG.md` under `[Unreleased]`. Until `CHANGELOG.md`
   exists (it comes with the release workflow), the PR from step 6 is the record.

### Conflict rules

- **Upstream wins in files it owns.** Outside the seams table we take upstream's version as is.
- **In a seam, take upstream's version first, then re-apply our change on top.** Keep our change as small as
  before; if upstream now offers a hook or a flag that makes our change unnecessary, drop ours and use theirs.
- **Never resolve a conflict by deleting an upstream file** ([ADR 0006](decisions/0006-stripping.md)).
- Files we own outright (below) do not conflict; if upstream adds a file with the same path, rename ours.

## Seams: upstream files we edit

Line numbers are at the bootstrap base `60d3c8bb`. Update this table in the same PR that adds, moves or removes a
seam.

| File | What we change | Status |
|---|---|---|
| `CLAUDE.md` | Was a symlink to `AGENTS.md`; now a real file that imports `@AGENTS.md` and adds CrossMono rules | edited |
| `platformio.ini` | PaperMono environments (`571-623`): `board_build.partitions = partitions_papermono.csv` in each ([ADR 0005](decisions/0005-partitions.md)) | edited |
| `platformio.ini` | A `[crossmono]` version section inserted below `[crosspoint]` (`6-7`); PaperMono environments (`571-623`): `extra_scripts` adds `pre:scripts/mono/version_flags.py`, the `-DCROSSPOINT_VERSION` lines are removed (`584,603,620`), USB strings are CrossMono's (`582-583,601-602,618-619`) ([VERSIONING.md](../VERSIONING.md)) | edited |
| `src/network/OtaUpdater.cpp` | Release URL (`22`) points at `nandanito/crossmono`, so a build with a `0.y.z` version is never offered a CrossPoint release; asset name `crossmono-…` (`41-57`) and maybe a size check before `esp_ota_begin` (`156`) still to come | edited, more planned 0.1.0 |
| `src/util/FirmwareIdentity.h` | Plugin family (`5`, `"crosspoint"`). The catalog filters plugins by it (`src/activities/plugins/PluginCatalogActivity.cpp:135`), so changing it hides CrossPoint plugins. Decide in 0.1.0 whether to change it at all | to decide |
| `src/network/HttpDownloader.cpp` | User-Agent (`33`): `CrossMono-ESP32-<version>` instead of `CrossPoint-ESP32-<version>` | edited |
| `src/activities/boot_sleep/BootActivity.cpp`, `src/images/Logo120.h` | Boot logo and name (`16-17`) | planned 0.1.0 |
| `lib/I18n/translations/*.yaml` | Product name strings (`STR_CROSSPOINT` and others) | planned 0.1.0 |
| `src/activities/settings/AboutActivity.cpp` | CrossMono version, CrossPoint base, SDK commit, model | planned 0.1.0 |
| `src/network/html/*` | Web UI header and name | planned 0.1.0 |
| `src/main.cpp` | One include, and `gpio.begin()` (`593`) replaced by `mono::beginInput(gpio)` from `src/mono/InputBringUp.cpp`: on the PaperMono it waits for the IO expander and retries the touch bring-up, so touch comes up after sleep and wake (GitHub #4). Go back to `gpio.begin()` once the FreeInk SDK makes the bring-up reliable itself | edited |
| `src/main.cpp` | PaperMono power-click handling (`1040-1050`), only if the alternative bindings need a power-off path | to decide |
| `.github/workflows/ci.yml` | Rewritten ([ADR 0010](decisions/0010-quality-and-ci.md)): runs on `main` and pull requests; cppcheck on `papermono`; builds `papermono` and `papermono-gh_release` only; checks the full image and uploads it with the app image; runs the flash-size gate | edited |
| `test/CMakeLists.txt` | One line after `include(GoogleTest)` (`39`), `add_subdirectory(mono)`, adds our host tests in `test/mono/` | edited |
| `.github/workflows/pr-firmware-links.yml` | Follows the `CI` workflow; links only the PaperMono development build, with an esptool command instead of CrossPoint's flasher | edited |
| `.github/workflows/release.yml` | Our release workflow replaces upstream's ([ADR 0009](decisions/0009-install.md)) | planned 0.1.0 |
| `README.md` | Rewritten for CrossMono, with a credit to CrossPoint | planned 0.1.0 |
| `LICENSE` | Our copyright line added below upstream's | planned 0.1.0 |
| `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md` | CrossMono templates | planned 0.1.0 |
| `src/activities/home/HomeActivity.cpp` | Model shown on Home | planned 0.1.0 |
| `src/SettingsList.cpp`, `src/CrossPointSettings.h` | Model override setting; later the cue settings | planned 0.1.0 |
| `src/components/UITheme.cpp` | Register the CrossMono theme | planned 0.3.0 |

Not a seam: `partitions.csv` stays upstream's. The PaperMono environments use our own `partitions_papermono.csv`
([ADR 0005](decisions/0005-partitions.md)).

Upstream workflows we keep unchanged: `pr-formatting-check.yml` checks semantic PR titles and is used as is.
`release_candidate.yml` and `release-fonts.yml` run only by hand and need CrossPoint's secrets, so they never run
here. Step 3 of the procedure still applies to all three.

## Files we own outright

These are new files; upstream never touches them.

- `src/mono/`, `lib/mono-*`, `scripts/mono/`, `test/mono/`
- `partitions_papermono.csv`
- `docs/decisions/`, `docs/roadmap.md`, `docs/upstream-sync.md`, `docs/hardware-test-checklist.md`
- `VERSIONING.md`, `RELEASING.md`, `CHANGELOG.md`, `THIRD-PARTY-NOTICES`
