"""Unit tests for tools/check_series_status.py. Run: python -m unittest discover -s tests"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_series_status as css  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "series-status"
DATA = ROOT / "data"


def run(name: str):
    return css.check([FIXTURES / name], DATA)


class CheckSeriesStatusTest(unittest.TestCase):
    def assert_one_error(self, name: str, fragment: str) -> None:
        report = run(name)
        self.assertEqual(len(report.errors), 1, report.errors)
        self.assertIn(fragment, report.errors[0])

    def test_valid_file_passes(self):
        report = run("valid.json")
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])

    def test_p6_claiming_ve07_fails(self):
        self.assert_one_error("p6-claims-ve07.json", "P6 claims VE-07, but series.csv allocates it to P2")

    def test_unknown_p_id(self):
        self.assert_one_error("unknown-p-id.json", "p_id 'P9' is not a row in series.csv")

    def test_repo_mismatch(self):
        self.assert_one_error("repo-mismatch.json", "repo 'uas-sec-p3-pki' does not match series.csv")

    def test_unknown_ve(self):
        self.assert_one_error("unknown-ve.json", "ve_id 'VE-99' is not a known verification event")

    def test_unknown_status(self):
        self.assert_one_error("unknown-status.json", "status 'passed' must be one of")

    def test_unpinned_evidence(self):
        self.assert_one_error("unpinned-evidence.json", "must be a GitHub URL pinned to a full commit SHA")

    def test_short_p1_commit(self):
        self.assert_one_error("bad-p1-commit.json", "p1_commit 'a16601e' must be a full 40-character")

    def test_missing_allocated_ve_is_a_warning(self):
        report = run("missing-ve.json")
        self.assertEqual(report.errors, [])
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("VE-08 is allocated to P2 but missing from the file", report.warnings[0])

    def test_malformed_json_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text in ("{", "[]", '{"p_id": "P2"}'):
                path = Path(tmp) / "series-status.json"
                path.write_text(text, encoding="utf-8")
                self.assertTrue(css.check([path], DATA).errors, text)

    def test_exit_code(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(css.main([str(FIXTURES / "valid.json")]), 0)
            self.assertEqual(css.main([str(FIXTURES / "valid.json"), str(FIXTURES / "p6-claims-ve07.json")]), 1)


if __name__ == "__main__":
    unittest.main()
