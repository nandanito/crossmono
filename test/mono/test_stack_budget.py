"""Check the stack-budget script on synthetic call graphs (scripts/mono/stack_budget.py, ADR 0010).

Run with python3 test/mono/test_stack_budget.py.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "mono"))

import stack_budget  # noqa: E402
from stack_budget import Task  # noqa: E402


def node(title: str, name: str, frame: str | None = "32 bytes (static)", place: str = "src/x.cpp:1:1") -> str:
    """A node line as GCC's -fcallgraph-info=su writes it; frame None is a function defined elsewhere."""
    label = f"{name}\\n{place}" + (f"\\n{frame}" if frame else "")
    tail = "" if frame else " shape : ellipse"
    return f'node: {{ title: "{title}" label: "{label}"{tail} }}\n'


def edge(source: str, target: str) -> str:
    return f'edge: {{ sourcename: "{source}" targetname: "{target}" label: "src/x.cpp:2:3" }}\n'


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.build = self.root / "build"
        self.build.mkdir()
        self.objects = 0

    def tearDown(self):
        self.tmp.cleanup()

    def ci(self, *lines: str, path: str | None = None) -> None:
        self.objects += 1
        file = self.build / (path or f"obj{self.objects}.cpp.ci")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(f'graph: {{ title: "{file.stem}"\n' + "".join(lines) + "}\n")

    def source(self, path: str, text: str) -> None:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    def graph(self) -> stack_budget.Graph:
        return stack_budget.load(self.build)

    def task_graph(self):
        """entry -> a (100) -> b (200); entry -> c (50). The deepest path is entry, a, b."""
        self.ci(
            node("_Z5entryPv", "void entry(void*)", "16 bytes (static)"),
            node("_Z1av", "void a()", "100 bytes (static)"),
            node("_Z1bv", "void b()", "200 bytes (static)"),
            node("_Z1cv", "void c()", "50 bytes (static)"),
            edge("_Z5entryPv", "_Z1av"),
            edge("_Z1av", "_Z1bv"),
            edge("_Z5entryPv", "_Z1cv"),
        )
        self.source("src/task.cpp", 'xTaskCreate(entry, "worker", 2048, nullptr, 1, nullptr);\n')
        return Task("worker", "src/task.cpp", r'xTaskCreate\(entry, "worker", (\d+),', "void entry(void*)")


class Load(Case):
    def test_frames_names_places_and_calls(self):
        self.ci(
            node("_Z1fv", "void f()", "48 bytes (static)", "src/f.cpp:3:6"),
            node("_Z1gv", "void g()", None, "src/g.h:1:6"),
            node("_Z1hv", "void h()", "64 bytes (dynamic)"),
            node("_Z1kv", "void k()", "80 bytes (dynamic,bounded)"),
            edge("_Z1fv", "_Z1gv"),
        )
        graph = self.graph()
        self.assertEqual(graph.frames, {"_Z1fv": 48, "_Z1gv": 0, "_Z1hv": 64, "_Z1kv": 80})
        self.assertEqual(graph.names["_Z1fv"], "void f()")
        self.assertEqual(graph.places["_Z1fv"], "src/f.cpp:3:6")
        self.assertNotIn("_Z1gv", graph.places, "a function defined elsewhere has no frame and no place")
        self.assertEqual(graph.dynamic, {"_Z1hv", "_Z1kv"})
        self.assertEqual(graph.calls, {"_Z1fv": {"_Z1gv"}})
        self.assertEqual(graph.objects, 1)

    def test_worst_frame_of_a_function_in_several_objects(self):
        self.ci(node("_Z1iv", "inline void i()", "32 bytes (static)"))
        self.ci(node("_Z1iv", "inline void i()", "96 bytes (static)"), path="sub/b.cpp.ci")
        self.ci(node("_Z1iv", "inline void i()", "64 bytes (static)"))
        graph = self.graph()
        self.assertEqual(graph.frames["_Z1iv"], 96)
        self.assertEqual(graph.objects, 3)


class Deepest(Case):
    def test_heaviest_path(self):
        self.task_graph()
        used, path, cycle = stack_budget.deepest("_Z5entryPv", self.graph())
        self.assertEqual((used, path, cycle), (316, ["_Z5entryPv", "_Z1av", "_Z1bv"], False))

    def test_shared_callee_counts_on_each_path(self):
        # entry -> a -> d and entry -> b -> d: d is memoised but still adds to both.
        self.ci(
            node("e", "e", "8 bytes (static)"),
            node("a", "a", "10 bytes (static)"),
            node("b", "b", "30 bytes (static)"),
            node("d", "d", "100 bytes (static)"),
            edge("e", "a"),
            edge("e", "b"),
            edge("a", "d"),
            edge("b", "d"),
        )
        self.assertEqual(stack_budget.deepest("e", self.graph())[:2], (138, ["e", "b", "d"]))

    def test_recursion_is_cut_and_reported(self):
        self.ci(
            node("r", "r", "40 bytes (static)"),
            node("s", "s", "40 bytes (static)"),
            edge("r", "s"),
            edge("s", "r"),
        )
        used, path, cycle = stack_budget.deepest("r", self.graph())
        self.assertEqual((used, path, cycle), (80, ["r", "s"], True))


class Measure(Case):
    def test_within_budget(self):
        task = self.task_graph()
        result = stack_budget.measure(task, self.graph(), self.root)
        self.assertEqual((result.stack, result.used, result.headroom, result.ok), (2048, 316, 1732, True))

    def test_over_budget_fails(self):
        task = self.task_graph()
        self.source("src/task.cpp", 'xTaskCreate(entry, "worker", 1300, nullptr, 1, nullptr);\n')
        result = stack_budget.measure(task, self.graph(), self.root)
        self.assertEqual(result.headroom, 984)
        self.assertFalse(result.ok, "less than MIN_HEADROOM left")

    def test_stack_expression(self):
        task = self.task_graph()
        self.source("src/task.cpp", 'xTaskCreate(entry, "worker", 2 * 1024 + 512, nullptr, 1, nullptr);\n')
        task = Task(task.name, task.source, r'xTaskCreate\(entry, "worker", ([^,]+),', task.entry)
        self.assertEqual(stack_budget.measure(task, self.graph(), self.root).stack, 2560)

    def test_stack_pattern_must_match_once(self):
        task = self.task_graph()
        for text, count in (("", 0), ('xTaskCreate(entry, "worker", 2048,\nxTaskCreate(entry, "worker", 4096,\n', 2)):
            with self.subTest(count=count):
                self.source("src/task.cpp", text)
                with self.assertRaisesRegex(stack_budget.BudgetError, f"matches {count} times"):
                    stack_budget.measure(task, self.graph(), self.root)

    def test_stack_that_is_not_a_number(self):
        task = self.task_graph()
        self.source("src/task.cpp", 'xTaskCreate(entry, "worker", kStack, nullptr, 1, nullptr);\n')
        task = Task(task.name, task.source, r'xTaskCreate\(entry, "worker", ([^,]+),', task.entry)
        with self.assertRaisesRegex(stack_budget.BudgetError, "cannot read the stack size 'kStack'"):
            stack_budget.measure(task, self.graph(), self.root)

    def test_missing_entry_fails(self):
        task = self.task_graph()
        task = Task(task.name, task.source, task.stack, "void other(void*)")
        with self.assertRaisesRegex(stack_budget.BudgetError, "is not in the graph, so the task is not checked"):
            stack_budget.measure(task, self.graph(), self.root)

    def test_ambiguous_entry_fails(self):
        task = self.task_graph()
        self.ci(node("_ZZ5entryPvENKUlvE_clEv", "void entry(void*)::<lambda()>", "8 bytes (static)"))
        task = Task(task.name, task.source, task.stack, "entry(void*)")
        with self.assertRaisesRegex(stack_budget.BudgetError, "2 functions match the entry"):
            stack_budget.measure(task, self.graph(), self.root)

    def test_fanout_adds_the_worst_override(self):
        task = self.task_graph()
        self.ci(
            node("_ZN1A4drawEv", "virtual void A::draw()", "500 bytes (static)"),
            node("_ZN1B4drawEv", "virtual void B::draw()", "100 bytes (static)"),
            node("_Z4deepv", "void deep()", "1000 bytes (static)"),
            edge("_ZN1B4drawEv", "_Z4deepv"),
        )
        task = Task(task.name, task.source, task.stack, task.entry, ("::draw()",))
        result = stack_budget.measure(task, self.graph(), self.root)
        self.assertEqual(result.used, 316 + 1100)
        self.assertEqual(result.path[-3:], ["[virtual call: worst of 2 overrides]", "_ZN1B4drawEv", "_Z4deepv"])

    def test_branch_proof(self):
        task = self.task_graph()
        self.ci(node("_Z4sizev", "size_t size()", "32 bytes (static)", "src/main.cpp:64:1"))
        self.ci(node("lib/x.cpp:_Z4sizev", "size_t size()", "32 bytes (static)", "lib/x.cpp:9:1"))
        proved = Task(task.name, task.source, task.stack, task.entry, needs=("size_t size()", "src/main.cpp"))
        self.assertTrue(stack_budget.measure(proved, self.graph(), self.root).ok)
        unproved = Task(task.name, task.source, task.stack, task.entry, needs=("size_t size()", "src/other.cpp"))
        with self.assertRaisesRegex(stack_budget.BudgetError, "is not what is built"):
            stack_budget.measure(unproved, self.graph(), self.root)


class Main(Case):
    def run_main(self, tasks, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(stack_budget, "TASKS", tasks), mock.patch.object(stack_budget, "ROOT", self.root):
            with redirect_stdout(out), redirect_stderr(err):
                code = stack_budget.main(["--build-dir", str(self.build), *args])
        return code, out.getvalue(), err.getvalue()

    def test_pass_prints_the_margin_and_the_unmeasured_tasks(self):
        task = self.task_graph()
        summary = self.root / "summary.md"
        code, out, err = self.run_main((task,), "--summary", str(summary))
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"ok\s+worker\s+316 of 2048\s+headroom\s+1732")
        self.assertIn("Not measured:", out)
        self.assertIn("nimble_host", out)
        self.assertIn("All 1 measured tasks", out)
        self.assertIn("| worker | 2,048 | 316 | 1,732 | ok |", summary.read_text())

    def test_task_over_budget_fails_and_shows_its_path(self):
        task = self.task_graph()
        self.source("src/task.cpp", 'xTaskCreate(entry, "worker", 1024, nullptr, 1, nullptr);\n')
        code, out, _ = self.run_main((task,))
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL\s+worker\s+316 of 1024\s+headroom\s+708")
        self.assertIn("void b() (200)", out, "a failing task prints its path without --verbose")
        self.assertIn("FAIL: less than 1024 B left in worker", out)

    def test_unchecked_task_fails_but_the_others_are_reported(self):
        task = self.task_graph()
        missing = Task("gone", task.source, task.stack, "void gone(void*)")
        summary = self.root / "summary.md"
        code, out, _ = self.run_main((missing, task), "--summary", str(summary))
        self.assertEqual(code, 1)
        self.assertIn("FAIL gone: the entry 'void gone(void*)' is not in the graph", out)
        self.assertRegex(out, r"ok\s+worker\s+316 of 2048")
        self.assertIn("FAIL: 1 of 2 tasks not checked", out)
        self.assertIn("**Not checked:** gone:", summary.read_text())

    def test_no_call_graph(self):
        code, _, err = self.run_main(())
        self.assertEqual(code, 1)
        self.assertIn("no .ci files", err)


class RealTasks(unittest.TestCase):
    """The patterns in TASKS still find exactly one stack size in this repository (checked again at each sync)."""

    def test_each_stack_size_is_found_once(self):
        for task in stack_budget.TASKS:
            with self.subTest(task=task.name):
                self.assertGreater(stack_budget.stack_size(task, ROOT), stack_budget.MIN_HEADROOM)

    def test_vector_font_branch(self):
        # The loop and render task sizes come from the CROSSPOINT_VECTOR_FONTS branch, not from #else.
        sizes = {task.name: stack_budget.stack_size(task, ROOT) for task in stack_budget.TASKS}
        main = (ROOT / "src" / "main.cpp").read_text()
        self.assertIn(f"SET_LOOP_TASK_STACK_SIZE({sizes['loopTask'] // 1024} * 1024)", main)
        manager = (ROOT / "src" / "activities" / "ActivityManager.cpp").read_text()
        block = manager.split("\n#if CROSSPOINT_VECTOR_FONTS\n", 1)[1].split("#endif", 1)[0]
        vector, other = block.split("#else", 1)
        line = f"renderTaskStackBytes = {sizes['ActivityManagerRender']};"
        self.assertIn(line, vector)
        self.assertNotIn(line, other)


if __name__ == "__main__":
    unittest.main()
