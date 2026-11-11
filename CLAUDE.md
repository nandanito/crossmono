# CrossMono agent guide

@AGENTS.md

The import above is CrossPoint's agent guide, unchanged. Its technical guidance applies here: HAL and SDK
contracts, memory and allocation rules, coding standards, testing, translations, generated files, and its skills
under `.agents/skills/`. Where it conflicts with the CrossMono rules below, **the CrossMono rules win in this
repository**. When preparing work for CrossPoint itself, follow `AGENTS.md` as written.

## What CrossMono is

- Reading-first open-source firmware for the M5Stack **PaperMono** (C153) and **PaperMono-Lite** (C153-Lite),
  built on CrossPoint Reader and the FreeInk SDK. One build serves both models.
- Repository `nandanito/crossmono`; website and web flasher `crossmono/crossmono.github.io`.
- Independent community firmware, not affiliated with or supported by M5Stack. Use that wording
  ([ADR 0002](docs/decisions/0002-identity-and-scope.md)).
- Not a place to develop general CrossPoint features. Something useful to every CrossPoint board is offered
  upstream; we carry it only until it lands.
- Maintainer: Nandan.

## Decisions

Full records in [docs/decisions/](docs/decisions/README.md). Do not re-open a decision in passing; propose a new
record that supersedes it.

| # | Decision |
|---|---|
| 0001 | New repo with CrossPoint's full history (not a GitHub fork); base `60d3c8bb` on `develop`; merge upstream at each release via `sync/crosspoint-<ver>` → PR → merge commit |
| 0002 | Name CrossMono; firmware at `nandanito/crossmono`, site in the `crossmono` org |
| 0003 | One build for both models; boot probe for NFC (0x50) and SX1262; override setting; board tag `papermono` |
| 0004 | SemVer `0.y.z`, tags without `v`, rc `0.1.0-rc.1`, dev `0.1.0-dev+<sha>`; Keep a Changelog |
| 0005 | CrossPlay partition table (2 × 0x7F0000, no spiffs); size gate 85 % warn / 95 % fail; first install is a full flash |
| 0006 | Remove features by flags, `lib_deps` and env only; never delete upstream files |
| 0007 | 1-bit fast UI, AA text, own theme, visible nav bar; grey only on hero surfaces; 0.1.0 is branding only |
| 0008 | Cues and sensors → theme → NFC → LoRa → mic + AI; drivers in SDK style in `lib/mono-*`; SDK pin follows upstream; 0.2.0 part replaced by 0014 |
| 0009 | OTA bin + full bin + elf + SHA256SUMS + manifest + LICENSE.txt; ESP Web Tools on GitHub Pages; esptool fallback |
| 0010 | Own GitHub Actions: format, cppcheck, builds, host tests, size gate, stack budget, release, Pages |
| 0011 | MIT with upstream text kept (the image as a whole is GPLv3, wolfSSL); our README is `.github/README.md`; launch channels |
| 0012 | Model probe = NFC identity register only (M5Stack's sequence), once per boot, no NVS; radio pins held low at boot; shown in About, on Home from the 0.3.0 badge (0014); replaces 0003's probe bullet |
| 0013 | 0.1.0 ships with the Lite marked untested (no device; on backorder); reports welcome after the release; replaces the Lite-tester gate in 0003 and 0012; no 0.1.0 announcement, the tester request moves to 0.2.0 |
| 0014 | 0.2.0 = Home from the keys (#5), LED and sound cues, `crossmono.local` (#16); SDK's `LedManager`/`Buzzer`, policy in `src/mono/`, no `lib/mono-*` drivers; badge → 0.3.0; rotation and RTC timer wake out |

Plans: [docs/roadmap.md](docs/roadmap.md) (the root `ROADMAP.md` is CrossPoint's). Versions:
[VERSIONING.md](VERSIONING.md). Releases: [RELEASING.md](RELEASING.md). Upstream merges:
[docs/upstream-sync.md](docs/upstream-sync.md).

## Repository layout

- **Ours:** `src/mono/`, `lib/mono-*`, `scripts/mono/`, `test/mono/`, `partitions_papermono.csv`,
  `.github/README.md`, `docs/decisions/`, `docs/roadmap.md`, `docs/upstream-sync.md`, `docs/install.md`,
  `docs/hardware-test-checklist.md`, `VERSIONING.md`, `RELEASING.md`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, `THIRD-PARTY-NOTICES`.
- **Upstream:** everything else, including `README.md` (a seam only for its note at the top), `SCOPE.md`, `ROADMAP.md`, `AGENTS.md`, `GOVERNANCE.md`,
  `USER_GUIDE.md` and `.github/`. Never delete an upstream file. `licenses/*.txt` are CrossPoint's, copied unchanged
  ahead of a sync; do not edit them (docs/upstream-sync.md, "Carried ahead of a sync").
- **Seams:** upstream files we edit, listed in [docs/upstream-sync.md](docs/upstream-sync.md). Prefer a new file
  in our folders over an edit. When an edit is unavoidable, keep it small and add or update its row in the seams
  table in the same PR. This `CLAUDE.md` is itself a seam.
- `freeink-sdk/` is a submodule at the commit upstream pins. Do not move the pin ourselves.

## Where these rules override AGENTS.md

| AGENTS.md | In CrossMono |
|---|---|
| Integration work targets `develop` | Work targets `main`. Branch from `main`; `develop` exists only upstream |
| Never open or close a PR | Open PRs in `nandanito/crossmono` when Nandan asks. Never open, close or comment on PRs or issues in other projects |
| The human writes PR descriptions | In our repo a short, plain, factual PR body is fine. For other projects (CrossPoint, FreeInk SDK, M5Stack), draft short plain text for Nandan to post or edit |
| Local commits need explicit approval | An approved plan, or an explicit request to commit, covers commits on its branch |
| Hardware testing before a PR is opened | Hardware testing is Nandan's: for firmware PRs, list what to test on the device; the PR is merged only after that. Releases use [docs/hardware-test-checklist.md](docs/hardware-test-checklist.md) |

`firmware-handoff` (with its four review subagents) still applies to firmware and build changes. The Codex review
on the PR comes on top of it.

## Workflow

- Branch → PR → Codex review → merge with a **merge commit**. Never squash, never rebase `main` (it shares
  history with CrossPoint).
- PR titles are semantic (`feat:`, `fix:`, `docs:`, `chore:` …).
- Commits are SSH-signed through 1Password. If signing fails, ask Nandan to unlock 1Password. Never bypass
  signing (`--no-gpg-sign`, `-c commit.gpgsign=false`).
- Ask first, every time, before: forking, creating a repository, pushing, tagging, publishing a release, or posting
  anywhere (GitHub comments, forums, social media). Approval for one of these does not carry over to the next.
- Push tags one by one (`git push origin <tag>`), never `git push --tags`: the clone holds CrossPoint's tags as
  `upstream/*`.
- `upstream` is fetch-only. Never push to CrossPoint.

## Build and test

```sh
~/.local/bin/pio run -e papermono                  # development build
~/.local/bin/pio run -e papermono-gh_release       # release build (about 3 min from clean)
CROSSMONO_RC=1 ~/.local/bin/pio run -e papermono-gh_release_rc   # release-candidate build; fails without CROSSMONO_RC
python3 scripts/mono/version_flags.py --env papermono   # print the version macros without building
~/.local/bin/pio run -e papermono -t upload        # flash bootloader, table, otadata reset and app; keeps NVS
~/.local/bin/pio run -t unit-tests                 # host tests (CMake + GoogleTest)
python3 scripts/mono/size_gate.py --env papermono-gh_release   # flash-size gate, after a build
python3 scripts/mono/release_license.py --tag 0.1.0 --env papermono-gh_release --out <file>   # licence asset; CI only
python3 scripts/mono/package_release.py --tag 0.1.0 --license <file> --out <empty dir>   # release assets; CI only (RELEASING.md)
PIO=~/.local/bin/pio scripts/mono/stack-budget.sh --verbose   # instrumented build in .pio/stack-budget, then the stack budget
bin/clang-format-fix                               # format; needs clang-format 21 (~/.local/bin/clang-format)
~/.platformio/penv/bin/esptool --chip esp32s3 write-flash 0x0 <full.bin>   # full flash, erases NVS (esptool 5.3)
```

Release image after the CrossPoint 2.0.0 sync: 5,387,152 B (64.7 % of a 0x7F0000 slot, 82.2 % of upstream's
0x640000 slot). At the bootstrap base it was 5,360,752 B.

## Verify before relying

Earlier notes got these wrong. Check the source instead of trusting a summary:

- **SD bus is 4-bit SDMMC.** The SDK profile sets bus width 4
  (`freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:1199`). The comment "Native 1-bit SDMMC" in
  `platformio.ini:596` is out of date. The card mounts MBR partition 1 only. The data clock is 40 MHz since SDK
  `5e94fe7` (`freeink-sdk/libs/hardware/SDCardManager/src/SdmmcBlockDevice.cpp:52`); before, it was 20 MHz.
- **Grey is 3-level.** The panel is sold as 4-grey, but the SDK driver offers 3-level overlay grey only.
- **Input is two keys plus touch.** `InputStyle::DigitalTwoButton` (`BoardConfig.h:1177`): KEY1 (GPIO2) → Up,
  KEY2 (GPIO3) → Down; hold 650 ms → Back / Confirm; both keys → `BTN_POWER` in the SDK, which CrossMono turns into
  Home (`src/mono/KeyChord.h`). The power button is a PMIC click, polled. There is no Home key.
- **Text anti-aliasing is on by default** (`src/CrossPointSettings.h:298`).
- **The IMU is already supported** at the pinned SDK (`BoardConfig.h:1206`, BMI270), and CrossPoint's tilt page
  turn shows when the IMU probe succeeds; it worked on the full model in the PR #10 device test. The BMI270
  power-down after a failed start (SDK PR #159, `f676024`) is in the pin since the 2.0.0 sync; it was not at the
  bootstrap base, although ADR 0008 said so (erratum 2026-11-05). Check both models before writing IMU code.
- **The settings tab is "System".** The code calls it `SettingsSection::General`, but its title
  `STR_SETTINGS_GENERAL` is "System" (`lib/I18n/translations/english.yaml:97`). Check for Updates and About are
  under Settings → System.
- **The firmware image is GPLv3 as a whole**, because it links wolfSSL (GPLv2 or later); the code is MIT.
  `THIRD-PARTY-NOTICES` lists every bundled component ([ADR 0011](docs/decisions/0011-community-launch.md),
  addendum 2026-11-05).
- Line numbers in this section are as of the CrossPoint `2.0.0` sync (base `42d58daa`, SDK `5e94fe7`).
  Elsewhere in the docs (ADRs, the seams table) they are at the bootstrap base `60d3c8bb`. They drift after each
  sync.
