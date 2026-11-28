"""Unit tests that the hand-written docs agree with the workflow and the tools.

Each test keeps one audit item closed (overview/audit/closures.md): P1-02
(README names the tool behind each check), P1-13 (data/README.md names every
tool that reads data/), P1-14 (the Java version matches CI) and P1-15 (no
"Still open" item says it is closed).
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

# The tools/*.py that read files under data/. test_data_readers_list_is_complete
# fails if a tool that builds a path under data/ is missing here.
DATA_READERS = (
    "validate_trace.py",
    "render_views.py",
    "gen_sysml.py",
    "check_series_status.py",
    "fetch_series_status.py",
    "gen_overview.py",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def readme_section(text: str, heading: str) -> str:
    """The body of a '## ' section, stopping at the next '## ' heading or a
    generated block, whose contents are not hand-written."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |^<!-- BEGIN GENERATED|\Z)", text, re.M | re.S)
    if match is None:
        raise AssertionError(f"README.md has no '## {heading}' section")
    return match.group(1)


def still_open_items(text: str) -> list[str]:
    """The bullets of the list introduced by the README's 'Still open' line."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if "Still open" in line), None)
    if start is None:
        raise AssertionError("README.md has no 'Still open' list")
    items = []
    for line in lines[start + 1:]:
        if line.startswith("- "):
            items.append(line)
        elif items or line.strip():
            break
    return items


def workflow_tools() -> set[str]:
    """The tools/ scripts validate.yml runs: each `python tools/<x>.py` and each
    `tools/....sh` given as a step's command (not, say, inside hashFiles)."""
    workflow = read(WORKFLOW)
    tools = set(re.findall(r"\bpython3? (tools/[\w./-]+\.py)\b", workflow))
    tools |= set(re.findall(r"^\s*(?:- )?(?:run: )?(tools/[\w./-]+\.sh)\b", workflow, re.M))
    return tools


class VerificationEvidenceTest(unittest.TestCase):
    """P1-02: each tool validate.yml runs is named in README's Verification
    evidence, and each tool named there is run by validate.yml."""

    def test_every_workflow_tool_is_named(self):
        tools = workflow_tools()
        self.assertIn("tools/sysml/validate.sh", tools)
        self.assertIn("tools/render_views.py", tools)
        section = readme_section(read(ROOT / "README.md"), "Verification evidence")
        missing = sorted(t for t in tools if t not in section)
        self.assertEqual(missing, [], "run by validate.yml but not named in README's Verification evidence")

    def test_every_named_tool_is_run_by_the_workflow(self):
        tools = workflow_tools()
        section = readme_section(read(ROOT / "README.md"), "Verification evidence")
        named = set(re.findall(r"(?<![\w/])(tools/[\w./-]+\.(?:py|sh))\b", section))
        self.assertIn("tools/validate_trace.py", named)
        stale = sorted(t for t in named if t not in tools)
        self.assertEqual(stale, [], "named in README's Verification evidence but not run by validate.yml")


class DataReadmeTest(unittest.TestCase):
    """P1-13: every tool that reads data/ is named in data/README.md."""

    def test_data_readers_list_is_complete(self):
        # A path joined onto "data", or a string literal "data" or "data/...".
        builds_data_path = re.compile(r'/ "data"|["\']data(?:/|["\'])')
        readers = sorted(p.name for p in (ROOT / "tools").glob("*.py") if builds_data_path.search(read(p)))
        self.assertTrue(readers)
        self.assertEqual(sorted(set(readers) - set(DATA_READERS)), [], "add these to DATA_READERS")

    def test_every_data_reader_is_named(self):
        text = read(ROOT / "data" / "README.md")
        missing = [name for name in DATA_READERS if f"tools/{name}" not in text]
        self.assertEqual(missing, [], "read data/ but are not named in data/README.md")


class JavaVersionTest(unittest.TestCase):
    """P1-14: the Java version the docs state is the one CI's setup-java runs."""

    def test_docs_state_ci_java_major(self):
        majors = set(re.findall(r'java-version:\s*"?(\d+)', read(WORKFLOW)))
        self.assertEqual(len(majors), 1, f"expected one java-version in validate.yml, found {majors}")
        (ci,) = majors
        sysml = read(ROOT / "model" / "sysml" / "README.md")
        self.assertRegex(sysml, r"\*\*Requirements\.\*\* Java \d+")
        for path in (ROOT / "model" / "sysml" / "README.md", ROOT / "README.md", ROOT / "docs" / "GUIDE.md"):
            for m in re.finditer(r"\bJava (\d+)(\+| or later| only)?", read(path)):
                with self.subTest(file=path.relative_to(ROOT).as_posix(), text=m.group(0)):
                    self.assertEqual(m.group(1), ci)
                    self.assertIsNone(m.group(2), "state the version CI runs, without \"+\", \"or later\" or \"only\"")


class StillOpenTest(unittest.TestCase):
    """P1-15: nothing listed under README's 'Still open' says it is closed."""

    def test_no_still_open_item_says_closed_by(self):
        items = still_open_items(read(ROOT / "README.md"))
        self.assertTrue(items, "the 'Still open' list is empty or not found")
        self.assertEqual([i for i in items if "Closed by" in i], [])


if __name__ == "__main__":
    unittest.main()
