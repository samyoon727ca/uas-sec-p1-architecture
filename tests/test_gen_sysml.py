"""Unit tests for tools/gen_sysml.py helpers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import gen_sysml as gs  # noqa: E402


class GenSysmlTest(unittest.TestCase):
    def test_feature_path_uses_dot_notation_below_the_context(self):
        self.assertEqual(gs.feature_path("uasSystem::airVehicle::missionComputing::cc"),
                         "UAS_Architecture::uasSystem.airVehicle.missionComputing.cc")

    def test_doc_text_cannot_close_the_comment(self):
        self.assertNotIn("*/", gs.doc("a */ b"))

    def test_string_literal_escapes_quotes(self):
        self.assertEqual(gs.string('say "hi"'), '"say \\"hi\\""')

    def test_every_element_has_an_alias_in_the_architecture_model(self):
        _, _, problems = gs.aliases()
        self.assertEqual(problems, [])

    def test_generated_model_is_current(self):
        index, _, _ = gs.aliases()
        self.assertEqual(gs.OUT.read_text(encoding="utf-8"), gs.generate(index))


if __name__ == "__main__":
    unittest.main()
