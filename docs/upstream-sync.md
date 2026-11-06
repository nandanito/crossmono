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

Known for the next sync (CrossPoint changes on `develop` after 2.0.0):

- CrossPoint's licence notices (crosspoint-reader#4064, `136c2655`): the `licenses/` folder, a paragraph at the end
  of `LICENSE`, and `scripts/build_release_license.py`, which writes a release `LICENSE` asset.
  - Our `licenses/*.txt` are CrossPoint's files from `136c2655`, unchanged, so they merge without a conflict (see
    "Carried ahead of a sync"); `licenses/README.md` arrives as a new file. If CrossPoint changed one of them, take
    CrossPoint's.
  - Replace `scripts/mono/release_license.py` with CrossPoint's script: in `release.yml`, run it with `--output
    "$RUNNER_TEMP/LICENSE.txt"` (our asset name stays `crossmono-<version>-LICENSE.txt`), check that its library
    list has AnimatedGIF and every library in `.pio/libdeps/papermono-gh_release`, and keep a check in
    `package_release.py` that fits its output. Then delete our script and `test/mono/test_release_license.py`.
  - Point `THIRD-PARTY-NOTICES` at CrossPoint's notices and keep only what CrossMono adds
    ([ADR 0011](decisions/0011-community-launch.md), addenda 2026-11-05 and 2026-11-06).
- The touch bring-up carry in `src/main.cpp` goes when the SDK pin reaches `1e1cec2` (seams table).

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
   gate (`python3 scripts/mono/size_gate.py --env papermono-gh_release`) and the stack budget
   (`scripts/mono/stack-budget.sh`). The host tests check that each task in `scripts/mono/stack_budget.py` still
   finds its stack size; if CrossPoint or the SDK added a task, add it to that table.
6. Commit the merge, push the branch, open a PR titled `chore: sync CrossPoint <version>`. Note in the PR the new
   base commit, the new SDK pin and any seam that needed rework.
7. Merge with a **merge commit**. Never squash or rebase a sync.
8. In the sync PR, update the **Upstream** block of `[Unreleased]` in `CHANGELOG.md`: the new CrossPoint base
   (version and commit), the SDK pin, and a link to CrossPoint's release notes.

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
| `src/network/OtaUpdater.cpp` | Release URL (`22`) is `CROSSMONO_OTA_RELEASE_URL` from `src/mono/OtaRelease.h`: our `releases/latest`, so a `0.y.z` build is never offered a CrossPoint release; a build flag can point a test build at a tag. In `checkForUpdate()` the asset name is `crossmono-<tag>-<board>.bin` from `mono::formatAssetName` (`41`, `57`), which refuses a name longer than the 48-byte buffer | edited |
| `src/network/OtaUpdater.cpp` | In `checkForUpdate()`, a 404 from the release URL returns `NO_UPDATE` (`65-68`): with no release yet the screen says "No update available", not "Update failed" | edited |
| `src/network/OtaUpdater.cpp` | In `installUpdate()`, before `esp_ota_begin` (`156`): `otaSize` from the release JSON against the slot size, `TOO_LARGE_ERROR`. We carry it; it is not offered to CrossPoint yet (on hold: offer it when CrossPoint nears its slot or this seam conflicts at a sync). Drop ours if theirs lands | edited |
| `src/network/OtaUpdater.h` | `TOO_LARGE_ERROR` added as the last error value, after `WRONG_DEVICE_ERROR` (`24`) | edited |
| `src/activities/settings/OtaUpdateActivity.cpp` | `TOO_LARGE_ERROR` shows the existing `STR_FIRMWARE_TOO_LARGE` under "Update failed" (`195`); the `NO_UPDATE` comment (`30-31`) also names the no-release case | edited |
| `src/network/HttpDownloader.cpp` | User-Agent (`33`): `CrossMono-ESP32-<version>` instead of `CrossPoint-ESP32-<version>` | edited |
| `src/activities/boot_sleep/BootActivity.cpp` | Our logo and name: the include (`7`) and the two draw lines (`16-17`) use `MonoLogo120` (`src/mono/images/`) and `mono::NAME` (`src/mono/Brand.h`) instead of `Logo120` and `tr(STR_CROSSPOINT)` | edited |
| `src/activities/boot_sleep/SleepActivity.cpp` | The same on the default sleep screen: the include (`31`) and the two draw lines (`827-828` at the 2.0.0 base) | edited |
| `src/activities/settings/AboutActivity.cpp`, `.h` | On PaperMono builds: a "Model" row after "Device" ([ADR 0012](decisions/0012-boot-model-probe.md)), and "CrossPoint base" and "FreeInk SDK" rows after "Firmware" (`CROSSMONO_UPSTREAM_VERSION`, `CROSSMONO_SDK_COMMIT`; `version_flags.py` defines them only in files that name them). Enum entries, names, values, `ITEM_COUNT` 14, and a `static_assert` that every row has a name. clang-format put the name list one per line, so an upstream change there conflicts. The "Firmware" row already shows the CrossMono version | edited |
| `src/network/html/shared/Header.html.inc`, `Footer.html.inc` | The name "CrossMono" (header `11`, footer `4`); in the footer also the tagline, the links (our site, our repository, CrossPoint) and the bottom line with [ADR 0002](decisions/0002-identity-and-scope.md)'s wording (`4-7`) | edited |
| `src/network/html/*.html` | `<title>` of the six pages (`6`); in `FilesPage.html` also the folder title (`1220`) and the conversion log header (`3179`). Lines at the 2.0.0 base | edited |
| `src/network/html/assets/crosspoint-icon.svg` | Content replaced by our logo, a copy of `src/mono/images/logo.svg` written by `scripts/mono/make_logo.py`; the path and its route stay | edited |
| `src/main.cpp` | One include, and `gpio.begin()` (`593`) replaced by `mono::beginInput(gpio)` from `src/mono/InputBringUp.cpp`: on the PaperMono it waits for the IO expander and retries the touch bring-up, so touch comes up after sleep and wake (GitHub #4). Go back to `gpio.begin()` once the FreeInk SDK makes the bring-up reliable itself | edited |
| `src/main.cpp` | One include, and `mono::probeAtBoot()` right after `halTiltSensor.begin()` (`630` at the 2.0.0 base `42d58daa`): detects the model and holds the radio pins low ([ADR 0012](decisions/0012-boot-model-probe.md)) | edited |
| `src/main.cpp` | PaperMono power-click handling (`1040-1050`), only if the alternative bindings need a power-off path | to decide |
| `.github/workflows/ci.yml` | Rewritten ([ADR 0010](decisions/0010-quality-and-ci.md)): runs on `main` and pull requests; cppcheck on `papermono`; builds `papermono` and `papermono-gh_release` only; checks the full image and uploads it with the app image; runs the flash-size gate. A `stack-budget` job builds `papermono-gh_release` with `-fstack-usage -fcallgraph-info=su` and runs `scripts/mono/stack-budget.sh`; `Test Status` needs it | edited |
| `test/CMakeLists.txt` | One line after `include(GoogleTest)` (`39`), `add_subdirectory(mono)`, adds our host tests in `test/mono/` | edited |
| `.github/workflows/pr-firmware-links.yml` | Follows the `CI` workflow; links only the PaperMono development build, with an esptool command instead of CrossPoint's flasher | edited |
| `.github/workflows/release.yml` | Rewritten ([ADR 0009](decisions/0009-install.md), [RELEASING.md](../RELEASING.md#the-release-workflow)): runs on a pushed `N.N.N` or `N.N.N-rc.N` tag, or by hand with `tag` and `dry_run`; builds `papermono-gh_release` or `papermono-gh_release_rc`, packages and checks the assets with `scripts/mono/package_release.py`, takes the notes from `CHANGELOG.md` and creates the GitHub release. After the build, `scripts/mono/release_license.py` writes the licence asset `crossmono-<version>-LICENSE.txt`, which `package_release.py` checks and lists in `SHA256SUMS` ([ADR 0009](decisions/0009-install.md), addendum 2026-11-06). Upstream's attached assets to a release published by hand, for eight boards, and passes an LCP release key secret that we do not have. On `develop` after 2.0.0, upstream's also attaches a `LICENSE` asset from `scripts/build_release_license.py`; at the sync, that script replaces ours (above) | edited |
| `README.md` | A four-line note at the top (`1-4`) says the repository is CrossMono and points at `.github/README.md`, our README, which GitHub shows first. The rest stays CrossPoint's, so its changes merge cleanly ([ADR 0011](decisions/0011-community-launch.md), addendum 2026-11-05) | edited |
| `LICENSE` | Our copyright line below upstream's (`4`); upstream's MIT text unchanged. On `develop` after 2.0.0, upstream adds a paragraph at the end (the combined image is GPLv3 because of wolfSSL, crosspoint-reader#4064); it merges below the MIT text | edited |
| `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md` | Rewritten as CrossMono templates: our links, our labels (`bug`, `enhancement`), the model instead of CrossPoint's device list. At a sync keep ours and read upstream's diff for anything worth copying | edited |
| `.github/FUNDING.yml` | Emptied (a comment only), so GitHub no longer shows CrossPoint's sponsor link on our repository | edited |
| `src/activities/home/HomeActivity.cpp` | Model badge on Home. The header's right-hand label was tried and rejected in 0.1.0 ([ADR 0012](decisions/0012-boot-model-probe.md)) | planned 0.2.0 |
| `src/SettingsList.cpp` | The "Model" setting at the end of System, PaperMono builds only (`212-217` at the 2.0.0 base); later the cue settings | edited |
| `src/CrossPointSettings.h` | Field `modelOverride` after `slideSwitchAction` (`415-416` at the 2.0.0 base); later the cue settings | edited |
| `lib/I18n/translations/english.yaml` | New keys only, after `STR_MOVE_FINISHED_TO_READ` (`178-181` at the 2.0.0 base): `STR_MODEL`, `STR_MODEL_AUTO`, `STR_MODEL_PAPERMONO`, `STR_MODEL_PAPERMONO_LITE`. Other languages fall back to English | edited |
| `src/components/UITheme.cpp` | Register the CrossMono theme | planned 0.3.0 |

Not seams:

- `partitions.csv` stays upstream's. The PaperMono environments use our own `partitions_papermono.csv`
  ([ADR 0005](decisions/0005-partitions.md)).
- `src/images/Logo120.h` and `STR_CROSSPOINT` stay upstream's. Our screens draw `src/mono/images/MonoLogo120.h` and
  `mono::NAME`; `STR_CROSSPOINT` also labels CrossPoint's KOReader sync server.
- `src/util/FirmwareIdentity.h` keeps the plugin family `"crosspoint"` (0.1.0 plan): the catalog filters plugins by
  it (`src/activities/plugins/PluginCatalogActivity.cpp:135`), so another family would hide CrossPoint's plugins.
- `USER_GUIDE.md` stays CrossPoint's, although it says "CrossPoint logo" where CrossMono shows its own; our README
  lists what differs on CrossMono ([ADR 0011](decisions/0011-community-launch.md), addendum 2026-11-05).
- Network and storage names stay CrossPoint's: the `CrossPoint-Reader` access point, the `crosspoint` mDNS name,
  `window.CrossPoint` for plugins and the `/.crosspoint/` folder on the SD card.

Upstream workflows we keep unchanged: `pr-formatting-check.yml` checks semantic PR titles and is used as is.
`release_candidate.yml` and `release-fonts.yml` run only by hand and need CrossPoint's secrets, so they never run
here. Step 3 of the procedure still applies to all three.

## Carried ahead of a sync

Upstream files that we copied unchanged from CrossPoint's `develop` before the release that brings them. Because
they are byte for byte the same, the sync merges them without a conflict. Do not edit them; if the sync shows a
conflict, CrossPoint changed the file, so take CrossPoint's version. Before the merge,
`git diff main refs/tags/upstream/<version> -- licenses/` shows what CrossPoint changed in them (only
`licenses/README.md` should appear as new).

| Files | From | Why |
|---|---|---|
| `licenses/*.txt` (all but `licenses/README.md`) | `136c2655` (crosspoint-reader#4064), unchanged on `develop` since | Licence texts for the release licence file ([ADR 0009](decisions/0009-install.md), addendum 2026-11-06). `README.md` is left out: it describes CrossPoint's release script |

## Files we own outright

These are new files; upstream never touches them.

- `src/mono/`, `lib/mono-*`, `scripts/mono/`, `test/mono/`
- `partitions_papermono.csv`
- `.github/README.md` (upstream has no file there; if it adds one, the merge conflicts on it and the sync decides)
- `docs/decisions/`, `docs/roadmap.md`, `docs/upstream-sync.md`, `docs/hardware-test-checklist.md`,
  `docs/install.md`
- `VERSIONING.md`, `RELEASING.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `THIRD-PARTY-NOTICES`
