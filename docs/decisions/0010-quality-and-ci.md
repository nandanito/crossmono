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
