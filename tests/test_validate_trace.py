"""Unit tests for tools/validate_trace.py. Run: python -m unittest discover -s tests"""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
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


if __name__ == "__main__":
    unittest.main()
