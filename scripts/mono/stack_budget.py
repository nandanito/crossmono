# From ma-r-s/crossplay scripts_local/stack_budget.py (7763b9ea); MIT, (c) 2025 CrossPoint Reader org., 2026 Mario Ruiz
"""Stack budget (ADR 0010): each task's deepest call path against the stack it is created with.

    scripts/mono/stack-budget.sh [--verbose]          # instrumented build, then this check
    python3 scripts/mono/stack_budget.py --build-dir <dir> [--verbose] [--summary <file>]

GCC writes the data during the build of papermono-gh_release with these flags:

  -fstack-usage          one .su file per object: each function's own frame
  -fcallgraph-info=su    one .ci file per object: the same frames, and which function calls which

Together they are a call graph with a weight on each function. A task's need is the heaviest path from its
entry function. An inlined function has no frame of its own; its locals are counted in its caller.

Each task's stack size is read from the line that creates it, so the check cannot use an old number. A task
fails when less than MIN_HEADROOM bytes are left, and the whole check fails when an entry function is not in
the graph (an incremental build has .ci files only for the objects it recompiled).

What it cannot see:

  * calls through a function pointer: the path stops there. A virtual call has the same problem; a task
    names its virtual calls (fanout), and the worst override is added to its path.
  * code built without the flags: the prebuilt ESP-IDF libraries, including TinyUSB and the Wi-Fi stack, and the
    prebuilt libc, lwIP, mbedTLS and flash/OTA functions that the measured tasks call (their frames count as 0).
  * recursion: a cycle has no finite depth. It is reported, not summed.

So a pass means that no path the compiler can see is too deep; it does not mean that no path is.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# A task with less than this left is one change away from an overflow, and interrupts use its stack too.
MIN_HEADROOM = 1024


@dataclass(frozen=True)
class Task:
    name: str  # the name it is created with
    source: str  # the file that sets its stack size
    stack: str  # regex; group 1 is the size in bytes (digits, "*" and "+")
    entry: str  # part of the entry function's readable name; must match one function
    fanout: tuple[str, ...] = ()  # virtual calls the task makes; every override whose name contains one counts
    needs: tuple[str, str] | None = None  # (function, source path) that exists only if the size's branch is built


# The PaperMono builds define BOARD_HAS_PSRAM, so CROSSPOINT_VECTOR_FONTS is 1 (lib/EpdFont/VectorFontSupport.h).
# The first two sizes are read from that branch. SET_LOOP_TASK_STACK_SIZE in the same branch defines a strong
# getArduinoLoopTaskStackSize() in src/main.cpp; finding it in the graph shows that the branch was compiled.
VECTOR_FONTS_BRANCH = r"^#if CROSSPOINT_VECTOR_FONTS\n(?:(?!#e).*\n)*?"
VECTOR_FONTS_BUILT = ("getArduinoLoopTaskStackSize()", "src/main.cpp")

TASKS = (
    Task(
        "loopTask",  # Arduino's loop task: setup(), loop(), the activities, the web server, the OTA download
        "src/main.cpp",
        VECTOR_FONTS_BRANCH + r"SET_LOOP_TASK_STACK_SIZE\(([^)]+)\)",
        "void loopTask(void*)",
        ("Activity::loop()", "Activity::onEnter()", "Activity::onExit()"),
        VECTOR_FONTS_BUILT,
    ),
    Task(
        "ActivityManagerRender",
        "src/activities/ActivityManager.cpp",
        VECTOR_FONTS_BRANCH + r"\s*constexpr uint32_t renderTaskStackBytes = (\d+);",
        "ActivityManager::renderTaskLoop()",
        ("Activity::render(RenderLock&&)",),
        VECTOR_FONTS_BUILT,
    ),
    Task(
        "ble-start",  # starts the Bluetooth page turner
        "lib/BlePageTurner/src/SdkRadio.cpp",
        r'xTaskCreate\(startTaskEntry, "ble-start", (\d+),',
        "startTaskEntry(void*)",
    ),
    Task(
        "ble-conn",  # the SDK's BLE keyboard host: connects and subscribes
        "freeink-sdk/libs/network/BleKeyboardHost/src/BleKeyboardHost.cpp",
        r'xTaskCreate\(connTaskFn, "ble-conn", (\d+),',
        "connTaskFn(void*)",
    ),
)

# Tasks that run in this firmware but that the graph cannot measure; printed on every run. Not listed because
# they are never created here: the SDK's fi_input (nothing calls InputManager::beginAsync()) and audio_play
# (AudioManager is not linked).
NOT_MEASURED = (
    ("nimble_host", "NimBLE runs its events and callbacks through function pointers"),
    ("arduino_events", "network event callbacks are called through function pointers"),
    ("usbd", "the USB drive callbacks are called from the prebuilt TinyUSB library"),
    ("ESP-IDF tasks", "Wi-Fi, TCP/IP, event loop, timers, IPC and the Bluetooth controller are prebuilt"),
    ("prebuilt calls", "frames of libc, lwIP, mbedTLS and flash/OTA functions called from measured tasks count as 0"),
)

NODE = re.compile(r'node:\s*\{\s*title:\s*"([^"]+)"\s+label:\s*"([^"]*)"', re.S)
EDGE = re.compile(r'edge:\s*\{\s*sourcename:\s*"([^"]+)"\s+targetname:\s*"([^"]+)"')
FRAME = re.compile(r"(\d+)\s+bytes(?:\s+\((\w+)[^)]*\))?")


class BudgetError(Exception):
    """The check cannot run; the message says why."""


@dataclass
class Graph:
    frames: dict[str, int]  # symbol -> own frame in bytes (the worst, if it is in several objects)
    calls: dict[str, set[str]]  # symbol -> callees
    names: dict[str, str]  # symbol -> readable name
    places: dict[str, str]  # symbol -> "file:line:column"
    dynamic: set[str]  # symbols whose frame size is only a minimum (alloca, variable-length arrays)
    objects: int


def load(build_dir: Path) -> Graph:
    """Read every .ci file. Edges use the mangled node titles; the labels hold the readable names."""
    graph = Graph({}, {}, {}, {}, set(), 0)
    for ci in sorted(build_dir.rglob("*.ci")):
        graph.objects += 1
        text = ci.read_text(errors="replace")
        for title, label in NODE.findall(text):
            parts = label.split("\\n")
            frame = FRAME.search(parts[-1]) if len(parts) > 1 else None
            size = int(frame.group(1)) if frame else 0
            if size > graph.frames.get(title, -1):
                graph.frames[title] = size
            if frame and frame.group(2) == "dynamic":
                graph.dynamic.add(title)
            graph.names.setdefault(title, parts[0])
            if len(parts) > 2:
                graph.places.setdefault(title, parts[1])
        for source, target in EDGE.findall(text):
            graph.calls.setdefault(source, set()).add(target)
    return graph


def deepest(root: str, graph: Graph) -> tuple[int, list[str], bool]:
    """Heaviest path from root: (bytes, path, a cycle was cut)."""
    best: dict[str, tuple[int, list[str], bool]] = {}

    def walk(fn: str, on_path: frozenset[str]) -> tuple[int, list[str], bool]:
        if fn in on_path:
            return 0, [], True
        if fn in best:
            return best[fn]
        depth, path, cycle = 0, [], False
        for callee in graph.calls.get(fn, ()):
            d, p, c = walk(callee, on_path | {fn})
            cycle = cycle or c
            if d > depth:
                depth, path = d, p
        result = (graph.frames.get(fn, 0) + depth, [fn] + path, cycle)
        if not cycle:  # a path through a cycle depends on where it was entered
            best[fn] = result
        return result

    return walk(root, frozenset())


def matching(needle: str, graph: Graph) -> list[str]:
    return [symbol for symbol, name in graph.names.items() if needle in name]


def stack_size(task: Task, root: Path) -> int:
    source = root / task.source
    found = re.findall(task.stack, source.read_text(errors="replace"), re.M)
    if len(found) != 1:
        raise BudgetError(f"{task.name}: the stack size pattern matches {len(found)} times in {task.source}, not once")
    expression = found[0].strip()
    if not re.fullmatch(r"\d+(\s*[*+]\s*\d+)*", expression):
        raise BudgetError(f"{task.name}: cannot read the stack size {expression!r} in {task.source}")
    return sum(eval_product(term) for term in expression.split("+"))


def eval_product(term: str) -> int:
    result = 1
    for factor in term.split("*"):
        result *= int(factor)
    return result


@dataclass
class Result:
    task: str
    stack: int
    used: int
    path: list[str]
    cycle: bool

    @property
    def headroom(self) -> int:
        return self.stack - self.used

    @property
    def ok(self) -> bool:
        return self.headroom >= MIN_HEADROOM


def measure(task: Task, graph: Graph, root: Path) -> Result:
    stack = stack_size(task, root)
    if task.needs:
        name, place = task.needs
        if not any(graph.places.get(s, "").startswith(place) for s in matching(name, graph)):
            raise BudgetError(f"{task.name}: {name} from {place} is not in the graph, so {stack} is not what is built")
    entries = matching(task.entry, graph)
    if not entries:
        raise BudgetError(
            f"{task.name}: the entry {task.entry!r} is not in the graph, so the task is not checked "
            "(an incremental build has .ci files only for the objects it recompiled)"
        )
    if len(entries) > 1:
        found = "; ".join(graph.names[s] for s in entries[:5])
        raise BudgetError(f"{task.name}: {len(entries)} functions match the entry {task.entry!r} ({found})")
    used, path, cycle = deepest(entries[0], graph)
    overrides = sorted({s for needle in task.fanout for s in matching(needle, graph)})
    if overrides:
        worst, worst_path = 0, []
        for symbol in overrides:
            d, p, c = deepest(symbol, graph)
            cycle = cycle or c
            if d > worst:
                worst, worst_path = d, p
        used += worst
        path = path + [f"[virtual call: worst of {len(overrides)} overrides]"] + worst_path
    return Result(task.name, stack, used, path, cycle)


def describe(symbol: str, graph: Graph) -> str:
    if symbol.startswith("["):
        return symbol
    name = graph.names.get(symbol, symbol)
    name = name if len(name) <= 70 else name[:67] + "..."
    size = f"{graph.frames.get(symbol, 0)}{'+' if symbol in graph.dynamic else ''}"
    return f"{name} ({size})"


def report(results: list[Result], errors: list[str], graph: Graph, verbose: bool) -> list[str]:
    lines = []
    for r in results:
        mark = "ok" if r.ok else "FAIL"
        cycle = "  (recursion cut)" if r.cycle else ""
        lines.append(f"  {mark:<4} {r.task:<22} {r.used:>6} of {r.stack:<6} headroom {r.headroom:>6}{cycle}")
        if verbose or not r.ok:
            lines += [f"         {describe(step, graph)}" for step in r.path[:16]]
            if len(r.path) > 16:
                lines.append(f"         ... {len(r.path) - 16} more")
    lines += [f"  FAIL {error}" for error in errors]
    lines.append("")
    lines.append("  Not measured:")
    lines += [f"    {name:<16} {why}" for name, why in NOT_MEASURED]
    return lines


def summary(results: list[Result], errors: list[str]) -> str:
    rows = "".join(
        f"| {r.task} | {r.stack:,} | {r.used:,} | {r.headroom:,} | {'ok' if r.ok else '**FAIL**'} |\n" for r in results
    )
    failures = "".join(f"- **Not checked:** {error}\n" for error in errors)
    unmeasured = ", ".join(name for name, _ in NOT_MEASURED)
    return (
        "## Stack budget\n\n| Task | Stack (B) | Deepest path (B) | Headroom (B) | Result |\n|---|--:|--:|--:|---|\n"
        f"{rows}\n{failures}At least {MIN_HEADROOM} B must be left. Not measured: {unmeasured}.\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--build-dir", type=Path, required=True, help="the instrumented build: .pio/stack-budget/papermono-gh_release"
    )
    parser.add_argument("--verbose", action="store_true", help="print each task's deepest path")
    parser.add_argument("--summary", type=Path, help="file to append a Markdown table to")
    args = parser.parse_args(argv)

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))  # walk() recurses once per call on a path
    graph = load(args.build_dir)
    if not graph.frames:
        print(f"stack_budget.py: no .ci files in {args.build_dir}; run scripts/mono/stack-budget.sh", file=sys.stderr)
        return 1
    print(f"{len(graph.frames)} functions, {sum(map(len, graph.calls.values()))} calls, {graph.objects} objects\n")
    results, errors = [], []
    for task in TASKS:
        try:
            results.append(measure(task, graph, ROOT))
        except (BudgetError, OSError) as error:
            errors.append(str(error))
    print("\n".join(report(results, errors, graph, args.verbose)))
    if args.summary:
        with args.summary.open("a") as out:
            out.write(summary(results, errors))
    failed = [r.task for r in results if not r.ok]
    if failed:
        print(f"\nFAIL: less than {MIN_HEADROOM} B left in {', '.join(failed)}.")
        print("Make the frames on that path smaller, or raise the stack where the task is created.")
    if errors:
        print(f"\nFAIL: {len(errors)} of {len(TASKS)} tasks not checked (above).")
    if failed or errors:
        return 1
    print(f"\nAll {len(results)} measured tasks have at least {MIN_HEADROOM} B left on each path the compiler sees.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
