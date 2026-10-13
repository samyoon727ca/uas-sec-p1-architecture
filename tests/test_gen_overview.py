"""Unit tests for tools/gen_overview.py and tools/check_p2_snapshot.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_p2_snapshot as snap  # noqa: E402
import gen_overview as go  # noqa: E402

DATA = go.Data()


def write(folder: Path, name: str, text: str) -> None:
    (folder / name).write_bytes(text.encode("utf-8"))


def source_tree(folder: Path, projects: dict[str, str]) -> Path:
    write(folder, "front.md", "# Contents {-}\n")
    write(folder, "roadmap.md", "# Roadmap {#roadmap}\n\nIntro.\n\n<!-- gen: roadmap-stubs -->\n")
    write(folder, "limitations.md", "# Limitations {#limitations}\n")
    write(folder, "appendix.md", "# Appendix {-}\n")
    for name, text in projects.items():
        write(folder, name, text)
    return folder


CHAPTER = "---\nproject: P1\nkind: chapter\n---\n\n# P1 {#p1}\n\n{{p1.reqs}} requirements.\n"
STUB = "---\nproject: P3\nkind: stub\ntitle: Keys\n---\n\nP3 owns {{p1.repo_reqs:P3}} requirements.\n"


class FrontMatterTest(unittest.TestCase):
    def test_parses_fields_and_body(self):
        meta, body = go.front_matter("---\nproject: P3  # note\nkind: stub\n---\nBody\n")
        self.assertEqual(meta, {"project": "P3", "kind": "stub"})
        self.assertEqual(body, "Body\n")

    def test_no_front_matter(self):
        self.assertEqual(go.front_matter("# Title\n"), ({}, "# Title\n"))

    def test_line_without_colon_fails(self):
        with self.assertRaises(go.GenError):
            go.front_matter("---\nproject P3\n---\n")


class AssembleTest(unittest.TestCase):
    def test_stub_goes_to_roadmap_with_generated_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = source_tree(Path(tmp), {"p1.md": CHAPTER, "p3.md": STUB})
            text = go.assemble(src, DATA)
        self.assertIn(f"{len(DATA.reqs)} requirements.", text)
        self.assertIn("## P3: Keys {#p3}", text)
        self.assertIn(f"P3 owns {len(DATA.repo_reqs('P3'))} requirements.", text)
        self.assertIn("| SR-001 |", text)            # P3's requirement table
        self.assertIn("| VE-01 |", text)             # P3's verification events
        self.assertLess(text.index("# P1 {#p1}"), text.index("# Roadmap"))
        self.assertLess(text.index("# Roadmap"), text.index("# Limitations"))

    def test_roadmap_dropped_when_no_stub_is_left(self):
        chapter3 = "---\nproject: P3\nkind: chapter\n---\n\n# P3 {#p3}\n"
        with tempfile.TemporaryDirectory() as tmp:
            src = source_tree(Path(tmp), {"p1.md": CHAPTER, "p3.md": chapter3})
            text = go.assemble(src, DATA)
        self.assertNotIn("# Roadmap", text)
        self.assertIn("# P3 {#p3}", text)

    def test_chapter_must_start_with_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = source_tree(Path(tmp), {"p1.md": "---\nproject: P1\nkind: chapter\n---\n\nText first.\n"})
            with self.assertRaises(go.GenError):
                go.assemble(src, DATA)

    def test_front_matter_must_match_file_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = source_tree(Path(tmp), {"p4.md": STUB})
            with self.assertRaises(go.GenError):
                go.assemble(src, DATA)

    def test_stub_needs_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = source_tree(Path(tmp), {"p3.md": "---\nproject: P3\nkind: stub\n---\n\nText.\n"})
            with self.assertRaises(go.GenError):
                go.assemble(src, DATA)

    def test_real_sources_expand_completely(self):
        text = go.assemble(go.SRC, DATA)
        self.assertNotRegex(text, r"\{\{|<!-- gen:")


class GeneratedValuesTest(unittest.TestCase):
    def setUp(self):
        self.values = go.inline_values(DATA)

    def test_unknown_inline_value_fails(self):
        with self.assertRaises(go.GenError):
            go.expand_inline("{{p1.no_such_value}}", self.values)

    def test_unknown_block_fails(self):
        with self.assertRaises(go.GenError):
            go.expand_blocks("<!-- gen: no-such-block -->\n", DATA)

    def test_counts_come_from_the_data(self):
        self.assertEqual(go.expand_inline("{{p1.threats}}", self.values), str(len(DATA.threats)))
        self.assertEqual(go.expand_inline("{{p2.tcs}}", self.values), str(len(DATA.cases)))

    def test_evidence_path(self):
        run_id = go.expand_inline("{{ev:VE-07:environment/run_id}}", self.values)
        self.assertRegex(run_id, r"^\d+$")
        with self.assertRaises(go.GenError):
            go.expand_inline("{{ev:VE-07:environment/no_such_field}}", self.values)

    def test_table_escapes_pipes_and_newlines(self):
        self.assertEqual(go.table(["a"], [["x|y\nz"]]).splitlines()[-1], "| x\\|y z |")


class RollupTest(unittest.TestCase):
    """The roll-up must match P2's own rule (P2 tools/render_views.py)."""

    def rollup(self, *pairs):
        d = go.Data()
        d.cases = [{"tc_id": f"TC-{i}", "ve_id": "VE-07", "ci_status": ci, "hw_status": hw}
                   for i, (ci, hw) in enumerate(pairs)]
        return d.rollup("VE-07")

    def test_ci_only_pass_is_in_progress(self):
        r = self.rollup(("passed", "planned"), ("n/a", "planned"))
        self.assertEqual((r["status"], r["ci"][:2], r["hw"][:2]), ("in progress", (1, 1), (0, 2)))

    def test_all_passed(self):
        self.assertEqual(self.rollup(("passed", "passed"), ("n/a", "passed"))["status"], "passed")

    def test_any_failure_fails(self):
        self.assertEqual(self.rollup(("passed", "failed"))["status"], "failed")

    def test_nothing_run_is_planned(self):
        self.assertEqual(self.rollup(("planned", "planned"))["status"], "planned")


class DiagramTest(unittest.TestCase):
    def test_blocks_are_numbered_and_replaced(self):
        text = "a\n```mermaid\nflowchart LR\n  A --> B\n```\nb\n```mermaid\nflowchart TB\n  C\n```\n"
        with tempfile.TemporaryDirectory() as tmp:
            out, n = go.extract_diagrams(text, Path(tmp))
            self.assertEqual(n, 2)
            self.assertEqual((Path(tmp) / "diagrams/d01.mmd").read_text(), "flowchart LR\n  A --> B\n")
        self.assertIn('<img src="diagrams/d02.svg"', out)
        self.assertNotIn("```mermaid", out)

    def test_mermaid_from_a_p1_document(self):
        block = go.block_mermaid_from(DATA, ["docs/04-architecture.md", "0"])
        self.assertTrue(block.startswith("```mermaid\nflowchart LR"))
        with self.assertRaises(go.GenError):
            go.block_mermaid_from(DATA, ["docs/04-architecture.md", "99"])

    def test_mermaid_from_with_a_direction_changes_only_the_direction(self):
        original = go.block_mermaid_from(DATA, ["docs/04-architecture.md", "0"])
        turned = go.block_mermaid_from(DATA, ["docs/04-architecture.md", "0", "TB"])
        self.assertTrue(turned.startswith("```mermaid\nflowchart TB\n"))
        self.assertEqual(turned.split("\n", 2)[2], original.split("\n", 2)[2])
        with self.assertRaises(go.GenError):
            go.block_mermaid_from(DATA, ["docs/04-architecture.md", "0", "XY"])
        with self.assertRaises(go.GenError):   # block 3 is a sequence diagram
            go.block_mermaid_from(DATA, ["docs/04-architecture.md", "3", "TB"])


class ProvenanceTest(unittest.TestCase):
    def test_the_rebuilt_pdf_is_not_an_uncommitted_change(self):
        self.assertIn(":(exclude)overview/overview.pdf", go.DIRTY_PATHS)
        for path in ("data", "docs", "overview", "tools"):
            self.assertIn(path, go.DIRTY_PATHS)

    def test_provenance_names_both_commits(self):
        text = go.block_provenance(DATA, [])
        self.assertIn(DATA.p2_pin["commit"], text)
        self.assertIn(DATA.p1["data"], text)


class AuditTest(unittest.TestCase):
    def test_every_finding_is_in_the_index_and_in_full(self):
        index = go.block_audit_index(DATA, [])
        full = go.block_audit_findings(DATA, [])
        for f in DATA.audit["findings"]:
            self.assertIn(f"[{f['id']}](#{f['id'].lower()})", index)
            self.assertIn(f"{{#{f['id'].lower()}}}", full)
            for key in ("claim", "observation", "evidence", "fix"):
                self.assertIn(go.cell(go.md_text(f[key])), full)   # the text itself, not a summary

    def test_most_severe_first(self):
        order = [f["severity"] for f in go.audit_findings(DATA)]
        self.assertEqual(order, sorted(order, key=go.SEVERITIES.index))

    def test_finding_text_cannot_start_markup(self):
        self.assertEqual(go.md_text("a_b <c> *d* [e] `f` \\g &"),
                         "a\\_b &lt;c&gt; \\*d\\* \\[e\\] \\`f\\` \\\\g &amp;")

    def test_a_bad_finding_fails(self):
        d = go.Data.__new__(go.Data)
        d.audit = {"findings": [{"id": "A-01", "severity": "severe", "title": "t", "repo": "P2", "claim": "c",
                                 "observation": "o", "evidence": "e", "fix": "f"}]}
        with self.assertRaises(go.GenError):
            go.block_audit_index(d, [])
        d.audit["findings"][0].update(severity="high", fix="")
        with self.assertRaises(go.GenError):
            go.block_audit_index(d, [])

    def test_no_audit_file_fails_only_if_asked_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = go.Data(audit=Path(tmp))
            self.assertIsNone(d.audit)
            with self.assertRaises(go.GenError):
                go.block_audit_summary(d, [])


class SnapshotTest(unittest.TestCase):
    def test_pin_is_a_full_commit(self):
        repo, commit = snap.read_pin(snap.SNAPSHOT / "pin.txt")
        self.assertEqual(repo, "samyoon727ca/uas-sec-p2-verified-boot")
        self.assertRegex(commit, r"^[0-9a-f]{40}$")

    def test_snapshot_lists_copies_but_not_its_own_pin(self):
        files = snap.snapshot_files()
        self.assertIn("data/p1/pin.txt", files)       # P2's own pin is a copied file
        self.assertNotIn("pin.txt", files)

    def test_snapshot_holds_every_cited_evidence_summary(self):
        files = snap.snapshot_files()
        for c in DATA.cases:
            for env in ("ci", "hw"):
                if c[f"{env}_evidence"]:
                    folder = Path(c[f"{env}_evidence"]).parent.as_posix()
                    self.assertIn(f"{folder}/summary.json", files)

    def test_bad_pin_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            pin = Path(tmp) / "pin.txt"
            pin.write_text("repo: a/b\ncommit: db31c14\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                snap.read_pin(pin)


if __name__ == "__main__":
    unittest.main()
