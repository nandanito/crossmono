#!/bin/sh
# Stack budget (ADR 0010): an instrumented build of papermono-gh_release, then scripts/mono/stack_budget.py.
#
#   scripts/mono/stack-budget.sh [--verbose] [--summary <file>]
#
# The build goes to its own folder, .pio/stack-budget (or $STACK_BUDGET_DIR), and starts from an empty one:
# - The flags change PlatformIO's project checksum, and a checksum change deletes the whole build folder. In a
#   folder of its own that does not touch .pio/build.
# - The build cache stores objects but not the .ci and .su files beside them. An object restored from the cache
#   has no call graph, so this build uses a new, empty cache folder, deleted at the end.
# PIO names the pio command (default: pio).
set -eu
cd "$(dirname "$0")/../.."

env=papermono-gh_release
dir=${STACK_BUDGET_DIR:-.pio/stack-budget}
cache=$(mktemp -d)
trap 'rm -rf "$cache"' EXIT INT TERM

rm -rf "${dir:?}/$env"
PLATFORMIO_BUILD_DIR="$dir" \
PLATFORMIO_BUILD_CACHE_DIR="$cache" \
PLATFORMIO_BUILD_FLAGS="-fstack-usage -fcallgraph-info=su" \
  "${PIO:-pio}" run -e "$env"

python3 scripts/mono/stack_budget.py --build-dir "$dir/$env" "$@"
