"""Unit tests for tools/render_views.py: marker handling and the status cell."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import render_views as rv  # noqa: E402

B, E = "<!-- BEGIN GENERATED: v -->", "<!-- END GENERATED: v -->"


class SpliceTest(unittest.TestCase):
    def test_fills_empty_block(self):
        self.assertEqual(rv.splice(f"a\n{B}\n{E}\nz", "v", "body"), f"a\n{B}\nbody\n{E}\nz")

    def test_replaces_existing_block_and_is_idempotent(self):
        once = rv.splice(f"{B}\nold\nlines\n{E}", "v", "new")
        self.assertEqual(once, f"{B}\nnew\n{E}")
        self.assertEqual(rv.splice(once, "v", "new"), once)

    def test_missing_markers_fail(self):
        with self.assertRaises(SystemExit):
            rv.splice("no markers", "v", "body")


class StatusCellTest(unittest.TestCase):
    def test_links_status_to_evidence(self):
        self.assertEqual(rv.status_cell({"status": "planned", "evidence": ""}), "planned")
        self.assertEqual(rv.status_cell({"status": "passed", "evidence": "u1"}), "[passed](u1)")
        self.assertEqual(rv.status_cell({"status": "passed", "evidence": "u1; u2"}), "passed: [1](u1), [2](u2)")


if __name__ == "__main__":
    unittest.main()
