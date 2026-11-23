"""Unit tests for tools/render_views.py: marker handling, the status cell and the series table."""
from __future__ import annotations

import json
import sys
import tempfile
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


SHA = "0" * 40
URL = f"https://github.com/samyoon727ca/uas-sec-p2-verified-boot/blob/{SHA}/evidence/ve07.md"
P2 = {"p_id": "P2", "repo": "uas-sec-p2-verified-boot", "ve_ids": "VE-07; VE-08",
      "alignment": "aligned", "note": ""}
P4 = {"p_id": "P4", "repo": "uas-sec-p4-cc", "ve_ids": "VE-09; VE-10; VE-11",
      "alignment": "pending decision", "note": "Repo is the proxy"}
EVENTS = {ve: {"status": "planned", "evidence": "", "req_ids": reqs} for ve, reqs in {
    "VE-07": "SR-005; SR-006", "VE-08": "SR-006; SR-007", "VE-09": "SR-010",
    "VE-10": "SR-011", "VE-11": "SR-012"}.items()}


class SeriesTableTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.alignment = self.dir / "series-alignment.md"

    def status(self, row, events=EVENTS):
        return rv.series_status(row, events, self.dir, self.alignment)

    def test_formats_ranges(self):
        self.assertEqual(rv.format_ves(["VE-07", "VE-08"]), "VE-07, VE-08")
        self.assertEqual(rv.format_ves(["VE-01", "VE-02", "VE-03", "VE-04", "VE-05", "VE-06", "VE-17"]),
                         "VE-01 to VE-06, VE-17")
        self.assertEqual(rv.format_ves(["VE-01", "VE-02", "VE-03", "VE-04"], {"VE-02": ["u"]}),
                         "VE-01, [VE-02](u), VE-03, VE-04")
        self.assertEqual(rv.format_ves(["VE-09"], {"VE-09": ["u1", "u2"]}), "VE-09 ([1](u1), [2](u2))")

    def test_counts_distinct_requirements(self):
        self.assertEqual(rv.requirement_count(["VE-07", "VE-08"], EVENTS), 3)

    def test_series_table_matches_committed_counts(self):
        rows = {line.split(" | ")[0]: line.split(" | ")[2] for line in rv.series_table().splitlines()[2:]}
        self.assertEqual([v for k, v in sorted(rows.items())], ["3", "14", "14", "2", "12"])
        self.assertFalse(any("[P1]" in k for k in rows))

    def test_falls_back_to_verification_csv_without_snapshot(self):
        events = dict(EVENTS, **{"VE-08": {"status": "passed", "evidence": "u8", "req_ids": "SR-006"}})
        self.assertEqual(self.status(P2, events),
                         "planned: VE-07; passed: [VE-08](u8) "
                         "([emulation-only evidence](overview/p2-snapshot/evidence/))")

    def test_uses_snapshot_status_and_links(self):
        doc = {"p_id": "P2", "repo": "uas-sec-p2-verified-boot", "p1_commit": SHA, "ves": [
            {"ve_id": "VE-07", "status": "partly evidenced", "evidence": [URL]},
            {"ve_id": "VE-08", "status": "planned", "evidence": []}]}
        (self.dir / "uas-sec-p2-verified-boot.json").write_text(json.dumps(doc), encoding="utf-8")
        self.assertEqual(self.status(P2), f"partly evidenced: [VE-07]({URL}); planned: VE-08")

    def test_invalid_snapshot_fails(self):
        doc = {"p_id": "P2", "repo": "uas-sec-p2-verified-boot", "p1_commit": SHA, "ves": [
            {"ve_id": "VE-07", "status": "done", "evidence": ["https://example.com/x"]}]}
        (self.dir / "uas-sec-p2-verified-boot.json").write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.status(P2)

    def test_pending_decision_note_links_alignment(self):
        note = "planned: VE-09 to VE-11<br>Allocation pending decision: Repo is the proxy ([series alignment]({}))"
        self.assertEqual(self.status(P4), note.format("docs/series-alignment.md"))
        self.alignment.write_text("# Memo\n\n## P4: CC hardening and supply chain\n", encoding="utf-8")
        self.assertEqual(self.status(P4), note.format("docs/series-alignment.md#p4-cc-hardening-and-supply-chain"))
        self.assertNotIn("pending", self.status(P2))


if __name__ == "__main__":
    unittest.main()
