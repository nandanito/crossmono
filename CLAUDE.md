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
| 0008 | Cues and sensors → theme → NFC → LoRa → mic + AI; drivers in SDK style in `lib/mono-*`; SDK pin follows upstream |
| 0009 | OTA bin + full bin + elf + SHA256SUMS + manifest; ESP Web Tools on GitHub Pages; esptool fallback |
| 0010 | Own GitHub Actions: format, cppcheck, builds, host tests, size gate, stack budget, release, Pages |
| 0011 | MIT with upstream text kept; README for strangers; launch channels |

Plans: [docs/roadmap.md](docs/roadmap.md) (the root `ROADMAP.md` is CrossPoint's). Versions:
[VERSIONING.md](VERSIONING.md). Releases: [RELEASING.md](RELEASING.md). Upstream merges:
[docs/upstream-sync.md](docs/upstream-sync.md).

## Repository layout

- **Ours:** `src/mono/`, `lib/mono-*`, `docs/decisions/`, `docs/roadmap.md`, `docs/upstream-sync.md`,
  `docs/hardware-test-checklist.md`, `VERSIONING.md`, `RELEASING.md`, and later `CHANGELOG.md` and
  `THIRD-PARTY-NOTICES`.
- **Upstream:** everything else, including `README.md`, `SCOPE.md`, `ROADMAP.md`, `AGENTS.md`, `GOVERNANCE.md`,
  `USER_GUIDE.md` and `.github/`. Never delete an upstream file.
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
~/.local/bin/pio run -e papermono -t upload        # flash the app only (needs the CrossMono table already)
~/.local/bin/pio run -t unit-tests                 # host tests (CMake + GoogleTest)
bin/clang-format-fix                               # format; needs clang-format 21 (~/.local/bin/clang-format)
~/.platformio/penv/bin/esptool --chip esp32s3 write-flash 0x0 <full.bin>   # full flash (esptool 5.3)
```

Release image at the base: 5,360,752 B (64.4 % of a 0x7F0000 slot, 81.8 % of upstream's 0x640000 slot).

## Verify before relying

Earlier notes got these wrong. Check the source instead of trusting a summary:

- **SD bus is 4-bit SDMMC.** The SDK profile sets bus width 4
  (`freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h:1176`). The comment "Native 1-bit SDMMC" in
  `platformio.ini:588` is out of date. The card mounts MBR partition 1 only.
- **Grey is 3-level.** The panel is sold as 4-grey, but the SDK driver offers 3-level overlay grey only.
- **Input is two keys plus touch.** `InputStyle::DigitalTwoButton` (`BoardConfig.h:1154`): KEY1 (GPIO2) → Up,
  KEY2 (GPIO3) → Down; hold 650 ms → Back / Confirm; both keys → Power. The power button is a PMIC click, polled.
  There is no Home key.
- **Text anti-aliasing is on by default** (`src/CrossPointSettings.h:298`).
- **The IMU is already supported** at the pinned SDK (`BoardConfig.h:1183`, BMI270), and CrossPoint's tilt page
  turn shows when the IMU probe succeeds. Check on the device before writing IMU code.
- Line numbers in the docs are at the bootstrap base `60d3c8bb`; they drift after each sync.
