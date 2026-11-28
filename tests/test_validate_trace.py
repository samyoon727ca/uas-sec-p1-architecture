"""Unit tests for tools/validate_trace.py. Run: python -m unittest discover -s tests"""
from __future__ import annotations

import contextlib
import csv
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate_trace as vt  # noqa: E402


def element(eid, etype, **kw):
    row = {c: "" for c in vt.SCHEMAS["elements.csv"]}
    row.update(element_id=eid, name=eid, type=etype, description="d", **kw)
    return row


def threat(tid, eid, **kw):
    row = {c: "" for c in vt.SCHEMAS["threats.csv"]}
    row.update(threat_id=tid, title="t", element_id=eid, stride="T", description="d",
               mission_impact="MI-2", disposition="mitigate")
    row.update(kw)
    return row


def req(rid, alloc="CMP-FC", **kw):
    row = {c: "" for c in vt.SCHEMAS["requirements.csv"]}
    row.update(req_id=rid, statement="The FC shall verify X.", rationale="r",
               allocated_to=alloc, verification="T", evidence_repo="P2")
    row.update(kw)
    return row


def event(veid, req_ids, **kw):
    row = {c: "" for c in vt.SCHEMAS["verification.csv"]}
    row.update(ve_id=veid, title="t", req_ids=req_ids, procedure="p", pass_criteria="c", status="planned")
    row.update(kw)
    return row


def series(pid, ve_ids, **kw):
    row = {c: "" for c in vt.SCHEMAS["series.csv"]}
    row.update(p_id=pid, repo=f"uas-sec-{pid.lower()}", scope="s", ve_ids=ve_ids, alignment="aligned")
    row.update(kw)
    return row


SHA = "a1b2c3d4" * 5  # a full 40-character commit SHA
EVIDENCE = f"https://github.com/owner/repo/blob/{SHA}/evidence/ve07-ci/summary.md"


def baseline():
    """A small, fully valid data set."""
    return {
        "elements.csv": [
            element("CMP-FC", "process"),
            element("CMP-GCS", "process"),
            element("EE-OP", "external_entity", no_threat_rationale="Out of scope for test"),
            element("DS-FC-KEY", "data_store", host="CMP-FC"),
            element("TB-01", "trust_boundary"),
            element("DF-01", "data_flow", source="CMP-GCS", destination="CMP-FC", crosses="TB-01"),
        ],
        "threats.csv": [
            threat("THR-001", "DF-01"),
            threat("THR-002", "CMP-FC", stride="E", emb3d="TID-201; TID-202", attack_ics="T0836"),
            threat("THR-003", "CMP-GCS", stride="S"),
            threat("THR-004", "DS-FC-KEY", stride="I", disposition="accept",
                   acceptance_rationale="Physical access is mitigated operationally"),
        ],
        "requirements.csv": [
            req("SR-001", resiliency_approach="Substantiated Integrity: Integrity Checks"),
            req("SR-002", alloc="CMP-GCS", verification="I", evidence_repo="P6"),
        ],
        "trace.csv": [
            {"threat_id": "THR-001", "req_id": "SR-001"},
            {"threat_id": "THR-002", "req_id": "SR-001"},
            {"threat_id": "THR-003", "req_id": "SR-002"},
        ],
        "verification.csv": [
            event("VE-01", "SR-001", method="T", evidence_repo="P2"),
            event("VE-02", "SR-002", method="I", evidence_repo="P6"),
        ],
        "series.csv": [
            series("P1", ""),
            series("P2", "VE-01"),
            series("P6", "VE-02", alignment="pending decision", note="n"),
        ],
    }


# Small stand-ins for the pinned catalogs. T0855 is deliberately absent:
# it is revoked in ATT&CK for ICS v19.2.
TEST_CATALOGS = {
    "emb3d": ["TID-201", "TID-202"],
    "attack_ics": ["T0836", "T1692.001"],
    "resiliency": ["Substantiated Integrity: Integrity Checks"],
}


def write_catalogs(root: Path, catalogs=TEST_CATALOGS):
    for key, ids in catalogs.items():
        path = root / vt.CATALOGS[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("id,name\n" + "".join(f"{i},x\n" for i in ids))


class ValidatorTest(unittest.TestCase):
    def run_validator(self, data, allow_unanalyzed=False, catalogs=TEST_CATALOGS):
        with tempfile.TemporaryDirectory() as tmp:
            for name, rows in data.items():
                with open(Path(tmp) / name, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=vt.SCHEMAS[name])
                    writer.writeheader()
                    writer.writerows(rows)
            if catalogs is not None:
                write_catalogs(Path(tmp), catalogs)
            return vt.validate(Path(tmp), allow_unanalyzed)

    def assertError(self, data, fragment, **kw):
        report = self.run_validator(data, **kw)
        self.assertTrue(any(fragment in e for e in report.errors),
                        f"expected error containing {fragment!r}, got {report.errors}")

    # --- baseline -------------------------------------------------------
    def test_baseline_is_valid(self):
        report = self.run_validator(baseline())
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])

    def test_headers_only_is_valid(self):
        report = self.run_validator({name: [] for name in vt.SCHEMAS})
        self.assertEqual(report.errors, [])

    def test_wrong_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, cols in vt.SCHEMAS.items():
                (Path(tmp) / name).write_text(",".join(cols) + "\n")
            (Path(tmp) / "trace.csv").write_text("threat,requirement\n")
            write_catalogs(Path(tmp))
            report = vt.validate(Path(tmp))
        self.assertTrue(any("header must be exactly" in e for e in report.errors))

    # --- IDs ------------------------------------------------------------
    def test_duplicate_threat_id(self):
        data = baseline()
        data["threats.csv"].append(threat("THR-001", "CMP-FC"))
        self.assertError(data, "duplicate threat_id 'THR-001'")

    def test_malformed_requirement_id(self):
        data = baseline()
        data["requirements.csv"][0]["req_id"] = "REQ-1"
        self.assertError(data, "malformed req_id 'REQ-1'")

    def test_element_id_must_match_type(self):
        data = baseline()
        data["elements.csv"].append(element("DF-99", "process"))
        self.assertError(data, "does not match the ID pattern for type 'process'")

    # --- elements -------------------------------------------------------
    def test_flow_with_unknown_source(self):
        data = baseline()
        data["elements.csv"][5]["source"] = "CMP-NOPE"
        self.assertError(data, "source 'CMP-NOPE' is not a known element")

    def test_flow_crossing_unknown_boundary(self):
        data = baseline()
        data["elements.csv"][5]["crosses"] = "TB-01; TB-09"
        self.assertError(data, "crosses 'TB-09' is not a known trust boundary")

    def test_data_store_requires_process_host(self):
        data = baseline()
        data["elements.csv"][3]["host"] = "EE-OP"
        self.assertError(data, "host 'EE-OP' is not a known process")

    # --- threats --------------------------------------------------------
    def test_threat_on_unknown_element(self):
        data = baseline()
        data["threats.csv"][0]["element_id"] = "CMP-NOPE"
        self.assertError(data, "element_id 'CMP-NOPE' is not a known element")

    def test_threat_on_trust_boundary(self):
        data = baseline()
        data["threats.csv"][0]["element_id"] = "TB-01"
        self.assertError(data, "is a trust boundary")

    def test_invalid_stride_and_impact(self):
        data = baseline()
        data["threats.csv"][0].update(stride="X", mission_impact="High")
        self.assertError(data, "stride 'X'")
        self.assertError(data, "mission_impact 'High'")

    def test_malformed_framework_ids(self):
        data = baseline()
        data["threats.csv"][1].update(emb3d="TID-1", attack_ics="T836")
        self.assertError(data, "malformed EMB3D ID 'TID-1'")
        self.assertError(data, "malformed ATT&CK for ICS ID 'T836'")

    def test_framework_ids_must_exist_in_pinned_catalogs(self):
        data = baseline()
        data["threats.csv"][1].update(emb3d="TID-999", attack_ics="T0855")
        self.assertError(data, "EMB3D ID 'TID-999' is not in the pinned catalog")
        self.assertError(data, "ATT&CK for ICS ID 'T0855' is not in the pinned catalog")

    def test_missing_catalog_is_an_error(self):
        report = self.run_validator(baseline(), catalogs=None)
        self.assertTrue(any("catalog file not found" in e for e in report.errors))

    def test_stride_must_apply_to_element_type(self):
        data = baseline()
        data["threats.csv"][0]["stride"] = "S"          # DF-01 is a data flow
        self.assertError(data, "stride 'S' does not apply to data_flow elements (allowed: T,I,D)")
        data = baseline()
        data["threats.csv"][3]["stride"] = "R"          # DS-FC-KEY is a data store
        self.assertError(data, "stride 'R' does not apply to data_store elements")

    def test_external_entity_allows_spoofing_and_repudiation_only(self):
        data = baseline()
        data["elements.csv"][2]["no_threat_rationale"] = ""
        data["threats.csv"].append(threat("THR-005", "EE-OP", stride="T"))
        self.assertError(data, "stride 'T' does not apply to external_entity elements (allowed: S,R)")

    def test_mitigated_threat_without_requirement(self):
        data = baseline()
        data["trace.csv"] = [l for l in data["trace.csv"] if l["threat_id"] != "THR-003"]
        data["requirements.csv"] = [r for r in data["requirements.csv"] if r["req_id"] != "SR-002"]
        self.assertError(data, "THR-003 is dispositioned 'mitigate' but no requirement traces to it")

    def test_accepted_threat_requires_rationale(self):
        data = baseline()
        data["threats.csv"][3]["acceptance_rationale"] = ""
        self.assertError(data, "accepted threat requires 'acceptance_rationale'")

    def test_unknown_disposition(self):
        data = baseline()
        data["threats.csv"][0]["disposition"] = "transfer"
        self.assertError(data, "disposition 'transfer'")

    # --- requirements ---------------------------------------------------
    def test_requirement_without_parent_threat(self):
        data = baseline()
        data["requirements.csv"].append(req("SR-003"))
        self.assertError(data, "SR-003 has no parent threat")

    def test_requirement_must_be_allocated_to_component(self):
        data = baseline()
        data["requirements.csv"][0]["allocated_to"] = "DF-01"
        self.assertError(data, "allocated_to 'DF-01' is not a known component")

    def test_requirement_must_have_one_shall(self):
        data = baseline()
        data["requirements.csv"][0]["statement"] = "The FC shall sign and shall log."
        self.assertError(data, "exactly one 'shall' (found 2)")
        data["requirements.csv"][0]["statement"] = "The FC will sign."
        self.assertError(data, "exactly one 'shall' (found 0)")

    def test_verification_and_evidence_repo(self):
        data = baseline()
        data["requirements.csv"][0].update(verification="X", evidence_repo="P1")
        self.assertError(data, "verification 'X'")
        self.assertError(data, "evidence_repo 'P1'")

    def test_unknown_resiliency_approach(self):
        data = baseline()
        data["requirements.csv"][0]["resiliency_approach"] = "Substantiated Integrity: Hardening"
        self.assertError(data, "'Substantiated Integrity: Hardening' is not an SP 800-160 Vol. 2 Rev. 1 'Technique: Approach'")

    # --- verification coverage ------------------------------------------
    def test_requirement_without_verification_event(self):
        data = baseline()
        data["verification.csv"] = data["verification.csv"][:1]
        self.assertError(data, "SR-002 is not covered by a verification event")

    def test_verification_method_must_match_requirement(self):
        data = baseline()
        data["verification.csv"][1]["method"] = "T"
        self.assertError(data, "SR-002 is I/P6 but VE-02 is T/P6")

    def test_verification_repo_must_match_requirement(self):
        data = baseline()
        data["verification.csv"][0]["evidence_repo"] = "P3"
        self.assertError(data, "SR-001 is T/P2 but VE-01 is T/P3")

    def test_verification_event_references_unknown_requirement(self):
        data = baseline()
        data["verification.csv"][0]["req_ids"] = "SR-001; SR-099"
        self.assertError(data, "req_id 'SR-099' is not a known requirement")

    def test_verification_event_fields(self):
        data = baseline()
        data["verification.csv"][0].update(ve_id="VE-1", status="done")
        self.assertError(data, "malformed ve_id 'VE-1'")
        data = baseline()
        data["verification.csv"][0]["status"] = "done"
        self.assertError(data, "status 'done' must be one of")

    def test_result_requires_evidence(self):
        for status in ("partly evidenced", "passed", "failed"):
            data = baseline()
            data["verification.csv"][0]["status"] = status
            self.assertError(data, f"status '{status}' requires 'evidence'")

    def test_evidence_pinned_to_a_commit_is_valid(self):
        data = baseline()
        data["verification.csv"][0].update(status="passed", evidence=f"{EVIDENCE}; {EVIDENCE}#summary")
        data["verification.csv"][1]["evidence"] = EVIDENCE  # optional while planned
        report = self.run_validator(data)
        self.assertEqual(report.errors, [])

    def test_evidence_must_be_pinned_to_a_full_commit(self):
        unpinned = [
            EVIDENCE.replace(SHA, "main"),
            EVIDENCE.replace(SHA, SHA[:7]),
            EVIDENCE.replace("https://", "http://"),
            f"https://github.com/owner/repo/tree/{SHA}",
            "evidence/ve07-ci/summary.md",
        ]
        for link in unpinned:
            data = baseline()
            data["verification.csv"][0].update(status="passed", evidence=link)
            self.assertError(data, f"evidence '{link}' must be a GitHub URL pinned to a full commit SHA")

    # --- series manifest ----------------------------------------------
    def test_series_baseline_is_valid(self):
        report = self.run_validator(baseline())
        self.assertEqual(report.errors, [])
        self.assertIn("3 series repos", report.summary)

    def test_series_duplicate_ve(self):
        data = baseline()
        data["series.csv"][0]["ve_ids"] = "VE-01"
        self.assertError(data, "VE-01 is listed more than once")

    def test_series_ve_under_wrong_p_id(self):
        data = baseline()
        data["series.csv"][1]["ve_ids"] = ""
        data["series.csv"][2]["ve_ids"] = "VE-02; VE-01"
        self.assertError(data, "VE-01 is listed under P6 but its evidence_repo is 'P2'")

    def test_series_unknown_ve(self):
        data = baseline()
        data["series.csv"][1]["ve_ids"] = "VE-01; VE-99"
        self.assertError(data, "ve_id 'VE-99' is not a known verification event")

    def test_series_ve_not_listed(self):
        data = baseline()
        data["series.csv"][1]["ve_ids"] = ""
        self.assertError(data, "VE-01 is not listed in series.csv")

    def test_series_bad_alignment(self):
        data = baseline()
        data["series.csv"][1]["alignment"] = "done"
        self.assertError(data, "alignment 'done' must be one of")

    def test_series_missing_p_id(self):
        data = baseline()
        data["series.csv"] = data["series.csv"][:2]  # drop P6
        self.assertError(data, "evidence_repo 'P6' must be a p_id in series.csv other than P1")

    def test_series_new_p_id_is_an_evidence_repo(self):
        data = baseline()
        data["requirements.csv"][1]["evidence_repo"] = "P7"
        data["verification.csv"][1]["evidence_repo"] = "P7"
        data["series.csv"][2]["ve_ids"] = ""
        data["series.csv"].append(series("P7", "VE-02"))
        report = self.run_validator(data)
        self.assertEqual(report.errors, [])

    def test_series_ids_and_repos(self):
        data = baseline()
        data["series.csv"][0].update(p_id="Px")
        self.assertError(data, "malformed p_id 'Px'")
        data = baseline()
        data["series.csv"][0].update(p_id="")
        self.assertError(data, "malformed p_id ''")
        data = baseline()
        data["series.csv"].append(series("P2", ""))
        self.assertError(data, "duplicate p_id 'P2'")
        data = baseline()
        data["series.csv"][0]["repo"] = "bad/repo"
        self.assertError(data, "malformed repo 'bad/repo'")
        data = baseline()
        data["series.csv"][1]["repo"] = data["series.csv"][0]["repo"]
        self.assertError(data, "duplicate repo 'uas-sec-p1'")

    # --- trace ----------------------------------------------------------
    def test_trace_to_unknown_ids(self):
        data = baseline()
        data["trace.csv"].append({"threat_id": "THR-999", "req_id": "SR-999"})
        self.assertError(data, "threat_id 'THR-999' is not a known threat")
        self.assertError(data, "req_id 'SR-999' is not a known requirement")

    def test_duplicate_trace_link(self):
        data = baseline()
        data["trace.csv"].append({"threat_id": "THR-001", "req_id": "SR-001"})
        self.assertError(data, "duplicate link THR-001 -> SR-001")

    # --- STRIDE-per-element coverage ------------------------------------
    def test_element_without_threats_or_rationale(self):
        data = baseline()
        data["elements.csv"].append(element("CMP-CC", "process"))
        self.assertError(data, "CMP-CC has no threat rows and no 'no_threat_rationale'")

    def test_allow_unanalyzed_downgrades_to_warning(self):
        data = baseline()
        data["elements.csv"].append(element("CMP-CC", "process"))
        report = self.run_validator(data, allow_unanalyzed=True)
        self.assertEqual(report.errors, [])
        self.assertTrue(any("CMP-CC has no threat rows" in w for w in report.warnings))

    def test_element_with_threats_and_rationale(self):
        data = baseline()
        data["elements.csv"][0]["no_threat_rationale"] = "None apply"
        self.assertError(data, "CMP-FC has threat rows and a 'no_threat_rationale'")

    def test_trust_boundary_needs_no_coverage(self):
        data = baseline()
        data["elements.csv"].append(element("TB-02", "trust_boundary"))
        report = self.run_validator(data)
        self.assertEqual(report.errors, [])


class CountClaimsTest(unittest.TestCase):
    """README.md and brief/pdr-brief.md counts are checked against data/."""

    def run_on_copy(self, edit=None):
        """Validate the repo's data against copies of README.md, the brief and
        docs/05-threat-model.md, after edit(rel, text) -> text is applied."""
        with tempfile.TemporaryDirectory() as tmp:
            for rel in ("README.md", "brief/pdr-brief.md", "docs/05-threat-model.md"):
                dest = Path(tmp) / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                text = (ROOT / rel).read_text(encoding="utf-8")
                dest.write_text(edit(rel, text) if edit else text, encoding="utf-8")
            return vt.validate(ROOT / "data", root=Path(tmp))

    def test_repo_counts_match_data(self):
        report = vt.validate(ROOT / "data", root=ROOT)
        self.assertEqual(report.errors, [])

    def test_mutated_readme_count_fails(self):
        def edit(rel, text):
            return text.replace("42 MI-1, ", "41 MI-1, ") if rel == "README.md" else text
        report = self.run_on_copy(edit)
        self.assertTrue(any(e.startswith("README.md:") and "states 41 MI-1 threats, but data/ has 42" in e
                            for e in report.errors), report.errors)

    def test_mutated_brief_count_fails(self):
        def edit(rel, text):
            return text.replace("| P5 | Hardware and debug-port assessment | 2 |",
                                "| P5 | Hardware and debug-port assessment | 3 |") if rel != "README.md" else text
        report = self.run_on_copy(edit)
        self.assertTrue(any(e.startswith("brief/pdr-brief.md:") and
                            "states 3 requirements with evidence repo P5, but data/ has 2" in e
                            for e in report.errors), report.errors)

    def test_every_checked_number_fails_when_edited(self):
        for rel, pattern, fact in vt.COUNT_CLAIMS:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for m in re.finditer(pattern, text, re.MULTILINE):
                bumped = str(int(m.group(1)) + 1)
                edited = text[:m.start(1)] + bumped + text[m.end(1):]
                with self.subTest(rel=rel, pattern=pattern, at=m.start(1)):
                    report = self.run_on_copy(lambda r, t: edited if r == rel else t)
                    self.assertTrue(any(e.startswith(f"{rel}:") and f"states {bumped} {fact}," in e
                                        for e in report.errors), report.errors)

    def test_element_count_is_checked(self):
        def edit(rel, text):
            return text.replace("(46 data-flow-diagram elements", "(40 data-flow-diagram elements")
        report = self.run_on_copy(edit)
        self.assertTrue(any("states 40 elements, but data/ has 46" in e for e in report.errors), report.errors)

    def test_reworded_sentence_fails(self):
        def edit(rel, text):
            return text.replace("verification events are planned", "verification events are scheduled")
        report = self.run_on_copy(edit)
        self.assertTrue(any("verification events are planned" in e and "matches nothing" in e
                            for e in report.errors), report.errors)

    def test_pattern_matching_nothing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("There are 66 threats.\n", encoding="utf-8")
            report = vt.Report()
            vt.check_counts(Path(tmp), {"threats": 66}, report,
                            claims=[("README.md", r"There are (\d+) threats", "threats"),
                                    ("README.md", r"(\d+) requirements", "threats")])
        self.assertEqual(len(report.errors), 1, report.errors)
        self.assertIn("matches nothing", report.errors[0])

    def test_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = vt.Report()
            vt.check_counts(Path(tmp), {"threats": 66}, report,
                            claims=[("README.md", r"(\d+) threats", "threats")])
        self.assertTrue(any("file not found" in e for e in report.errors), report.errors)

    def test_cli_checks_counts_in_the_data_dirs_parent(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vt.main([]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "data", Path(tmp) / "data")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(vt.main(["--data-dir", str(Path(tmp) / "data")]), 1)
        self.assertIn("README.md: file not found", out.getvalue())

    def test_cli_root_option_points_the_count_check_elsewhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "data", Path(tmp) / "data")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(vt.main(["--data-dir", str(Path(tmp) / "data"), "--root", str(ROOT)]), 0)
            (Path(tmp) / "README.md").write_text(
                (ROOT / "README.md").read_text(encoding="utf-8").replace("42 MI-1, ", "41 MI-1, "),
                encoding="utf-8")
            (Path(tmp) / "brief").mkdir()
            shutil.copy(ROOT / "brief" / "pdr-brief.md", Path(tmp) / "brief" / "pdr-brief.md")
            (Path(tmp) / "docs").mkdir()
            shutil.copy(ROOT / "docs" / "05-threat-model.md", Path(tmp) / "docs" / "05-threat-model.md")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(vt.main(["--data-dir", str(ROOT / "data"), "--root", tmp]), 1)
        self.assertIn("states 41 MI-1 threats, but data/ has 42", out.getvalue())

    def test_cli_skip_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "data", Path(tmp) / "data")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(vt.main(["--data-dir", str(Path(tmp) / "data"), "--skip-counts"]), 0)
        self.assertNotIn("file not found", out.getvalue())


class PriorityThreatTablesTest(unittest.TestCase):
    """docs/05-threat-model.md §5.3 and README.md priority-threat tables match data/."""

    def run_on_copy(self, edit=None):
        """Validate the repo's data against copies of the checked docs after
        edit(rel, text) -> text is applied to each copy."""
        with tempfile.TemporaryDirectory() as tmp:
            for rel in ("README.md", "brief/pdr-brief.md", "docs/05-threat-model.md"):
                dest = Path(tmp) / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                text = (ROOT / rel).read_text(encoding="utf-8")
                dest.write_text(edit(rel, text) if edit else text, encoding="utf-8")
            return vt.validate(ROOT / "data", root=Path(tmp))

    def test_baseline_passes(self):
        report = vt.validate(ROOT / "data", root=ROOT)
        self.assertEqual(report.errors, [])

    def test_removed_sr_in_threat_model_fails(self):
        def edit(rel, text):
            if rel == "docs/05-threat-model.md":
                return text.replace(", SR-036 (rotate after loss of custody)", "")
            return text
        report = self.run_on_copy(edit)
        self.assertTrue(
            any(e.startswith("docs/05-threat-model.md:") and "missing traced requirement(s) SR-036" in e
                for e in report.errors),
            report.errors,
        )

    def test_removed_sr_in_readme_fails(self):
        def edit(rel, text):
            if rel == "README.md":
                return text.replace("SR-023, SR-025, SR-036", "SR-023, SR-025")
            return text
        report = self.run_on_copy(edit)
        self.assertTrue(
            any(e.startswith("README.md:") and "missing traced requirement(s) SR-036" in e
                for e in report.errors),
            report.errors,
        )

    def test_extra_untraced_sr_in_threat_model_fails(self):
        def edit(rel, text):
            if rel == "docs/05-threat-model.md":
                return text.replace("| SR-022 |", "| SR-022, SR-001 |")
            return text
        report = self.run_on_copy(edit)
        self.assertTrue(
            any(e.startswith("docs/05-threat-model.md:") and
                "listed requirement(s) SR-001 do not trace to THR-002" in e
                for e in report.errors),
            report.errors,
        )

    def test_extra_untraced_sr_in_readme_fails(self):
        def edit(rel, text):
            if rel == "README.md":
                return text.replace("SR-001 (tested by VE-01)", "SR-001, SR-002 (tested by VE-01)")
            return text
        report = self.run_on_copy(edit)
        self.assertTrue(
            any(e.startswith("README.md:") and
                "listed requirement(s) SR-002 do not trace to THR-001" in e
                for e in report.errors),
            report.errors,
        )

    def test_wrong_repo_in_threat_model_fails(self):
        cases = [
            # Replaced repo
            ("| P3, P4, P6 |", "| P2, P4, P6 |", "evidence repos 'P2, P4, P6' do not match requirements.csv 'P3, P4, P6'"),
            # Omitted repo (the original P1-07 defect)
            ("| P3, P4, P6 |", "| P4, P6 |", "evidence repos 'P4, P6' do not match requirements.csv 'P3, P4, P6'"),
            # Extra repo
            ("| P3 (VE-01) |", "| P3 (VE-01), P4 |", "evidence repos 'P3, P4' do not match requirements.csv 'P3'"),
            # Malformed repo token
            ("| P3 (VE-01) |", "| P3, bogus |", "malformed evidence repo 'bogus'"),
        ]
        for old, new, expected in cases:
            with self.subTest(old=old, new=new):
                report = self.run_on_copy(
                    lambda rel, text, o=old, n=new: text.replace(o, n) if rel == "docs/05-threat-model.md" else text
                )
                self.assertTrue(
                    any(e.startswith("docs/05-threat-model.md:") and expected in e for e in report.errors),
                    report.errors,
                )

    def test_parentheticals_in_evidence_cell_are_ignored(self):
        def edit(rel, text):
            if rel == "docs/05-threat-model.md":
                return text.replace("| P3 (VE-01) |", "| P3 (VE-01, see P2) |")
            return text
        report = self.run_on_copy(edit)
        self.assertEqual(report.errors, [])

    def test_nested_parentheticals_in_evidence_cell_are_ignored(self):
        def edit(rel, text):
            if rel == "docs/05-threat-model.md":
                return text.replace("| P3 (VE-01) |", "| P3 (VE-01 (see P2)) |")
            return text
        report = self.run_on_copy(edit)
        self.assertEqual(report.errors, [])

    def test_unbalanced_parenthesis_in_evidence_cell_fails(self):
        def edit(rel, text):
            if rel == "docs/05-threat-model.md":
                return text.replace("| P3 (VE-01) |", "| P3 (VE-01)) |")
            return text
        report = self.run_on_copy(edit)
        self.assertTrue(
            any(e.startswith("docs/05-threat-model.md:") and "malformed evidence repo 'P3 )'" in e
                for e in report.errors),
            report.errors,
        )

    def test_structural_errors_fail(self):
        threats = {"THR-001": {"_where": "threats.csv:2"}}
        reqs = {"SR-001": {"evidence_repo": "P3"}}
        links = [("THR-001", "SR-001")]

        def run_doc(content, check_evidence=True):
            with tempfile.TemporaryDirectory() as tmp:
                if content is not None:
                    (Path(tmp) / "doc.md").write_text(content, encoding="utf-8")
                report = vt.Report()
                vt.check_priority_threats(
                    Path(tmp), threats, reqs, links, report,
                    tables=[("doc.md", "## Priority", check_evidence)],
                )
                return report

        self.assertTrue(any("file not found" in e for e in run_doc(None).errors))
        self.assertTrue(any("heading '## Priority' not found" in e for e in run_doc("# Other\n").errors))
        self.assertTrue(any("no markdown table found" in e for e in run_doc("## Priority\n\n## Next\n").errors))
        self.assertIn("doc.md:3: priority-threat table missing required column 'Mitigated by'", run_doc(
            "## Priority\n\n| Threat | Evidence |\n|---|---|\n| THR-001 | P3 |\n"
        ).errors)
        self.assertIn("doc.md:3: priority-threat table missing required column 'Evidence'", run_doc(
            "## Priority\n\n| Threat | Mitigated by |\n|---|---|\n| THR-001 | SR-001 |\n",
            check_evidence=True,
        ).errors)
        self.assertTrue(any("heading '## Priority' appears more than once" in e for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by |\n|---|---|\n| THR-001 | SR-001 |\n\n"
            "## Priority\n\n| Threat | Mitigated by |\n|---|---|\n| THR-001 | SR-001 |\n",
            check_evidence=False,
        ).errors))
        self.assertTrue(any(e.startswith("doc.md:4:") and "malformed markdown table separator row" in e
                            for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by |\n| not a separator | --- |\n| THR-001 | SR-001 |\n",
            check_evidence=False,
        ).errors))
        self.assertTrue(any(e.startswith("doc.md:4:") and "malformed markdown table separator row" in e
                            for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by |\n|---|\n| THR-001 | SR-001 |\n",
            check_evidence=False,
        ).errors))
        self.assertTrue(any(e.startswith("doc.md:5:") and "table row has 3 cells, expected 2" in e
                            for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by |\n|---|---|\n| THR-001 | SR-001 | extra |\n",
            check_evidence=False,
        ).errors))
        self.assertTrue(any("has no data rows" in e for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by | Evidence |\n|---|---|---|\n"
        ).errors))
        self.assertTrue(any("unknown threat 'THR-999'" in e for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by | Evidence |\n|---|---|---|\n| THR-999 | SR-001 | P3 |\n"
        ).errors))
        self.assertTrue(any("no threat ID in first cell" in e for e in run_doc(
            "## Priority\n\n| Threat | Mitigated by | Evidence |\n|---|---|---|\n| No ID | SR-001 | P3 |\n"
        ).errors))


if __name__ == "__main__":
    unittest.main()
