# 0010. Quality and CI

- Status: Accepted
- Date: 2026-10-28

## Context

CrossPoint's workflows, inherited with the history:

| Workflow | What it does |
|---|---|
| `ci.yml` | clang-format 21 check, cppcheck on the default environment, build of 8 environments, host tests (CTest) |
| `pr-formatting-check.yml` | Semantic PR titles (`feat:`, `fix:`, `docs:` …) |
| `pr-firmware-links.yml` | Posts firmware download links after CI |
| `release_candidate.yml` | Manual release-candidate builds |
| `release.yml` | On a published release: tag must equal `[crosspoint] version` or `<version>rc`; builds `crosspoint-<version>-<device>.bin` and requires 8 assets |
| `release-fonts.yml` | Manual font release |

Host tests live in `test/` (CMake and GoogleTest 1.17) and run with `pio run -t unit-tests`. Formatting is
`.clang-format` (Google style, 120 columns), applied by `bin/clang-format-fix`. There is no stack-budget check, no
CHANGELOG and no merged-image packaging.

CrossNext inherited the same workflows but gated them to the original repository, so they never ran there. CrossPlay
has a stack-budget checker, `scripts_local/stack_budget.py` (MIT, © 2026 Mario Ruiz), which reads
`-fstack-usage -fcallgraph-info=su` output and checks each FreeRTOS task's deepest call path against its stack.

## Options considered

1. **Keep upstream's workflows unchanged.** They build 8 environments we do not ship, and `release.yml` expects
   CrossPoint's version and asset names.
2. **Replace them with our own workflows** (chosen), reusing upstream's steps where they fit.
3. **No CI until later.** Too risky for a project that strangers will flash.

## Decision

GitHub Actions on `nandanito/crossmono`:

- clang-format 21 check (same `.clang-format` as upstream);
- cppcheck on our environment;
- build of our development and release environments;
- host tests (CMake/CTest), including the partition table test from [0005](0005-partitions.md);
- flash-size gate: warning at 85 %, failure at 95 % of the app slot;
- stack-budget check, adapted from CrossPlay's MIT script;
- semantic PR titles;
- release workflow on tag push, producing the assets in [0009](0009-install.md);
- deploy of the website (`crossmono/crossmono.github.io`) through GitHub Pages.

A hardware test checklist is run before every release
([docs/hardware-test-checklist.md](../hardware-test-checklist.md)).

## Consequences

- Our workflow files are edits to upstream files (`.github/workflows/*`) and are listed as seams. On each sync,
  upstream changes to these files are read and copied over by hand where useful.
- Until the 0.1.0 work replaces them, upstream's `ci.yml` runs on our pull requests and builds all 8 environments.
- The CrossPlay script keeps its copyright line, and is listed in THIRD-PARTY-NOTICES ([0011](0011-community-launch.md)).

## Sources

- `.github/workflows/*.yml`, `test/CMakeLists.txt`, `scripts/register_unit_tests_target.py`, `.clang-format`,
  `bin/clang-format-fix` at `60d3c8bb`
- CrossNext-PaperMono `scripts_local/stack_budget.py`, `host-tests/release/run.sh`

## Addendum 2026-11-06: the stack-budget check

The check is in CI from 0.1.0 (plan PR 10). `scripts/mono/stack_budget.py` keeps CrossPlay's method; the task table
is new, for the tasks this firmware creates. `scripts/mono/stack-budget.sh` builds `papermono-gh_release` with
`-fstack-usage -fcallgraph-info=su` into `.pio/stack-budget`, with a new, empty build cache (the cache does not
keep the `.ci` files), and runs the check. The CI job `stack-budget` runs the same script; `Test Status` needs it.

- **Measured**, each with its stack size read from the line that creates the task: the Arduino `loopTask`
  (24,576 B, `SET_LOOP_TASK_STACK_SIZE` in `src/main.cpp`; the activities' `loop()`, `onEnter()` and `onExit()`,
  the web server and the OTA download run here), `ActivityManagerRender` (16,384 B, `ActivityManager.cpp`; every
  activity's `render()`), `ble-start` (3,072 B, `lib/BlePageTurner`) and `ble-conn` (4,096 B, the SDK's
  `BleKeyboardHost`). The loop and render sizes are read from the `CROSSPOINT_VECTOR_FONTS` branch, and the check
  fails if the build did not compile that branch. A task that cannot be checked fails the check.
- **Not measured**, and printed on every run: `nimble_host` and `arduino_events` (their work runs through function
  pointers), `usbd` (prebuilt TinyUSB calls the USB drive callbacks), and the prebuilt ESP-IDF tasks. Not created
  in this firmware: the SDK's `fi_input` (nothing calls `InputManager::beginAsync()`) and `audio_play`
  (AudioManager is not linked).
- First result (2026-11-06, `main` at `4b73afb9`): loopTask 12,016 B, render 5,552 B, ble-start 768 B, ble-conn
  1,888 B; at least 1,024 B must be left. A run takes about 4 minutes, nearly all of it the build.
- **Known blind spot:** FreeType calls its rasteriser through function pointers. CrossPoint's comment in
  `ActivityManager.cpp` gives a measured peak of about 8 KB on the render task when a glyph is rasterised during
  layout; the graph sees 5.5 KB. The prebuilt functions that measured tasks call (libc, lwIP, mbedTLS, flash and
  OTA writes) count as 0 bytes too. Each measured number is a lower bound on such paths.

## Erratum 2026-11-06: CrossPlay attribution

The Context says the CrossPlay script is "MIT, © 2026 Mario Ruiz". That is right for its repository: CrossPlay's
`LICENSE` (branch `xteink`) has two lines, "Copyright (c) 2025 CrossPoint Reader organization" and "Copyright (c)
2026 Mario Ruiz (CrossPlay)", the second since 2026-08-07 (`aa1fc505`). The 0.1.0 plan (question 11) quoted only
the first line. What is wrong is the Consequences line "The CrossPlay script keeps its copyright line": the script has
no copyright line of its own. Our copy starts with a one-line provenance comment (repository, branch, commit
`7763b9ea`, MIT, both copyright holders), and `THIRD-PARTY-NOTICES` names the repository, the author's handle
(`ma-r-s`) and CrossPlay's `LICENSE` as published.

Sources: https://github.com/ma-r-s/crossplay/blob/xteink/LICENSE, `gh api repos/ma-r-s/crossplay/commits` for
`LICENSE` and `scripts_local/stack_budget.py`.
