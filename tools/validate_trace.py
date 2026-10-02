#!/usr/bin/env python3
"""Validate the P1 traceability data in data/*.csv.

Checks schema, ID format and uniqueness, referential integrity, threat
dispositions, requirement quality, and STRIDE-per-element coverage.
Exits 1 if any error is found. Standard library only.

Usage:
    python tools/validate_trace.py [--data-dir data] [--allow-unanalyzed]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

SCHEMAS = {
    "elements.csv": [
        "element_id", "name", "type", "host", "source", "destination",
        "crosses", "interface", "description", "no_threat_rationale",
    ],
    "threats.csv": [
        "threat_id", "title", "element_id", "stride", "description", "emb3d",
        "attack_ics", "mission_impact", "disposition", "acceptance_rationale",
    ],
    "requirements.csv": [
        "req_id", "statement", "rationale", "allocated_to", "verification",
        "evidence_repo", "resiliency_technique",
    ],
    "trace.csv": ["threat_id", "req_id"],
}

# Element ID pattern by DFD element type.
ELEMENT_ID = {
    "process": re.compile(r"^CMP-[A-Z0-9]+(-[A-Z0-9]+)*$"),
    "external_entity": re.compile(r"^EE-[A-Z0-9]+(-[A-Z0-9]+)*$"),
    "data_store": re.compile(r"^DS-[A-Z0-9]+(-[A-Z0-9]+)*$"),
    "data_flow": re.compile(r"^DF-\d{2}$"),
    "trust_boundary": re.compile(r"^TB-\d{2}$"),
}
# Trust boundaries are not STRIDE elements; threats are recorded against the
# flows that cross them.
STRIDE_ELEMENT_TYPES = {"process", "external_entity", "data_store", "data_flow"}

THREAT_ID = re.compile(r"^THR-\d{3}$")
REQ_ID = re.compile(r"^SR-\d{3}$")
EMB3D_ID = re.compile(r"^TID-\d{3}$")
ATTACK_ICS_ID = re.compile(r"^T\d{4}(\.\d{3})?$")
SHALL = re.compile(r"\bshall\b", re.IGNORECASE)

STRIDE = {"S", "T", "R", "I", "D", "E"}
MISSION_IMPACT = {"MI-1", "MI-2", "MI-3", "MI-4"}
DISPOSITIONS = {"mitigate", "accept"}
VERIFICATION = {"I", "A", "D", "T"}  # Inspection, Analysis, Demonstration, Test
EVIDENCE_REPOS = {"P2", "P3", "P4", "P5", "P6"}

# NIST SP 800-160 Vol. 2 Rev. 1, Table D-2.
RESILIENCY_TECHNIQUES = {
    "Adaptive Response", "Analytic Monitoring", "Contextual Awareness",
    "Coordinated Protection", "Deception", "Diversity", "Dynamic Positioning",
    "Non-Persistence", "Privilege Restriction", "Realignment", "Redundancy",
    "Segmentation", "Substantiated Integrity", "Unpredictability",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.summary = ""

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def split_multi(value: str) -> list[str]:
    """Split a semicolon-separated cell into trimmed, non-empty values."""
    return [v.strip() for v in value.split(";") if v.strip()]


def load(path: Path, report: Report) -> list[dict] | None:
    """Load a CSV as dicts with a '_where' locator. None if unusable."""
    if not path.is_file():
        report.error(path.name, "file not found")
        return None
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        expected = SCHEMAS[path.name]
        if reader.fieldnames != expected:
            report.error(path.name, f"header must be exactly: {','.join(expected)}")
            return None
        rows = []
        for line, row in enumerate(reader, start=2):
            if None in row:
                report.error(f"{path.name}:{line}", "more cells than header columns")
                continue
            clean = {k: (v or "").strip() for k, v in row.items()}
            clean["_where"] = f"{path.name}:{line}"
            rows.append(clean)
        return rows


def index_unique(rows: list[dict], key: str, pattern, report: Report) -> dict[str, dict]:
    """Index rows by ID, reporting malformed and duplicate IDs."""
    index: dict[str, dict] = {}
    for row in rows:
        rid = row[key]
        if pattern is not None and not pattern.match(rid):
            report.error(row["_where"], f"malformed {key} '{rid}'")
            continue
        if rid in index:
            report.error(row["_where"], f"duplicate {key} '{rid}' (first at {index[rid]['_where']})")
            continue
        index[rid] = row
    return index


def require(row: dict, fields: list[str], report: Report) -> None:
    for name in fields:
        if not row[name]:
            report.error(row["_where"], f"'{name}' is required")


def check_elements(rows: list[dict], report: Report) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for row in rows:
        where, eid, etype = row["_where"], row["element_id"], row["type"]
        if etype not in ELEMENT_ID:
            report.error(where, f"type '{etype}' must be one of {sorted(ELEMENT_ID)}")
            continue
        if not ELEMENT_ID[etype].match(eid):
            report.error(where, f"element_id '{eid}' does not match the ID pattern for type '{etype}'")
            continue
        if eid in index:
            report.error(where, f"duplicate element_id '{eid}' (first at {index[eid]['_where']})")
            continue
        index[eid] = row
        require(row, ["name", "description"], report)

    for row in index.values():
        where, etype = row["_where"], row["type"]
        if etype == "data_flow":
            for end in ("source", "destination"):
                ref = row[end]
                if not ref:
                    report.error(where, f"data flow requires '{end}'")
                elif ref not in index:
                    report.error(where, f"{end} '{ref}' is not a known element")
                elif index[ref]["type"] in ("data_flow", "trust_boundary"):
                    report.error(where, f"{end} '{ref}' must be a process, external entity or data store")
            for tb in split_multi(row["crosses"]):
                if index.get(tb, {}).get("type") != "trust_boundary":
                    report.error(where, f"crosses '{tb}' is not a known trust boundary")
        else:
            for name in ("source", "destination", "crosses"):
                if row[name]:
                    report.error(where, f"'{name}' applies to data flows only")
        if etype == "data_store":
            host = row["host"]
            if not host:
                report.error(where, "data store requires 'host'")
            elif index.get(host, {}).get("type") != "process":
                report.error(where, f"host '{host}' is not a known process")
        elif row["host"]:
            report.error(where, "'host' applies to data stores only")
        if etype == "trust_boundary" and row["no_threat_rationale"]:
            report.error(where, "trust boundaries are not STRIDE elements; leave 'no_threat_rationale' empty")
    return index


def check_threats(rows: list[dict], elements: dict, report: Report) -> dict[str, dict]:
    index = index_unique(rows, "threat_id", THREAT_ID, report)
    for row in index.values():
        where = row["_where"]
        require(row, ["title", "description"], report)
        eid = row["element_id"]
        if eid not in elements:
            report.error(where, f"element_id '{eid}' is not a known element")
        elif elements[eid]["type"] not in STRIDE_ELEMENT_TYPES:
            report.error(where, f"element_id '{eid}' is a trust boundary; record the threat on a crossing data flow")
        if row["stride"] not in STRIDE:
            report.error(where, f"stride '{row['stride']}' must be one of S,T,R,I,D,E")
        for tid in split_multi(row["emb3d"]):
            if not EMB3D_ID.match(tid):
                report.error(where, f"malformed EMB3D ID '{tid}' (expected TID-###)")
        for tid in split_multi(row["attack_ics"]):
            if not ATTACK_ICS_ID.match(tid):
                report.error(where, f"malformed ATT&CK for ICS ID '{tid}' (expected T#### or T####.###)")
        if row["mission_impact"] not in MISSION_IMPACT:
            report.error(where, f"mission_impact '{row['mission_impact']}' must be one of {sorted(MISSION_IMPACT)}")
        disposition = row["disposition"]
        if disposition not in DISPOSITIONS:
            report.error(where, f"disposition '{disposition}' must be 'mitigate' or 'accept'")
        elif disposition == "accept" and not row["acceptance_rationale"]:
            report.error(where, "accepted threat requires 'acceptance_rationale'")
        elif disposition == "mitigate" and row["acceptance_rationale"]:
            report.error(where, "'acceptance_rationale' applies to accepted threats only")
    return index


def check_requirements(rows: list[dict], elements: dict, report: Report) -> dict[str, dict]:
    index = index_unique(rows, "req_id", REQ_ID, report)
    for row in index.values():
        where = row["_where"]
        require(row, ["statement", "rationale"], report)
        shall_count = len(SHALL.findall(row["statement"]))
        if row["statement"] and shall_count != 1:
            report.error(where, f"statement must contain exactly one 'shall' (found {shall_count})")
        alloc = row["allocated_to"]
        if not alloc:
            report.error(where, "'allocated_to' is required")
        elif elements.get(alloc, {}).get("type") != "process":
            report.error(where, f"allocated_to '{alloc}' is not a known component (process)")
        if row["verification"] not in VERIFICATION:
            report.error(where, f"verification '{row['verification']}' must be one of I,A,D,T")
        if row["evidence_repo"] not in EVIDENCE_REPOS:
            report.error(where, f"evidence_repo '{row['evidence_repo']}' must be one of {sorted(EVIDENCE_REPOS)}")
        for tech in split_multi(row["resiliency_technique"]):
            if tech not in RESILIENCY_TECHNIQUES:
                report.error(where, f"'{tech}' is not an SP 800-160 Vol. 2 Rev. 1 technique")
    return index


def check_trace(rows: list[dict], threats: dict, reqs: dict, report: Report) -> list[tuple[str, str]]:
    links: dict[tuple[str, str], str] = {}
    for row in rows:
        where, tid, rid = row["_where"], row["threat_id"], row["req_id"]
        ok = True
        if tid not in threats:
            report.error(where, f"threat_id '{tid}' is not a known threat")
            ok = False
        if rid not in reqs:
            report.error(where, f"req_id '{rid}' is not a known requirement")
            ok = False
        if (tid, rid) in links:
            report.error(where, f"duplicate link {tid} -> {rid} (first at {links[(tid, rid)]})")
        elif ok:
            links[(tid, rid)] = where
    return list(links)


def check_closure(elements, threats, reqs, links, report: Report, allow_unanalyzed: bool) -> None:
    linked_threats = {t for t, _ in links}
    linked_reqs = {r for _, r in links}

    for tid, row in threats.items():
        if row["disposition"] == "mitigate" and tid not in linked_threats:
            report.error(row["_where"], f"{tid} is dispositioned 'mitigate' but no requirement traces to it")

    for rid, row in reqs.items():
        if rid not in linked_reqs:
            report.error(row["_where"], f"{rid} has no parent threat in trace.csv")

    threatened = {row["element_id"] for row in threats.values()}
    for eid, row in elements.items():
        if row["type"] not in STRIDE_ELEMENT_TYPES:
            continue
        has_threats = eid in threatened
        rationale = row["no_threat_rationale"]
        if has_threats and rationale:
            report.error(row["_where"], f"{eid} has threat rows and a 'no_threat_rationale'; keep one")
        elif not has_threats and not rationale:
            msg = f"{eid} has no threat rows and no 'no_threat_rationale'"
            if allow_unanalyzed:
                report.warn(row["_where"], msg)
            else:
                report.error(row["_where"], msg)


def validate(data_dir: Path, allow_unanalyzed: bool = False) -> Report:
    report = Report()
    loaded = {name: load(data_dir / name, report) for name in SCHEMAS}
    if any(rows is None for rows in loaded.values()):
        return report

    elements = check_elements(loaded["elements.csv"], report)
    threats = check_threats(loaded["threats.csv"], elements, report)
    reqs = check_requirements(loaded["requirements.csv"], elements, report)
    links = check_trace(loaded["trace.csv"], threats, reqs, report)
    check_closure(elements, threats, reqs, links, report, allow_unanalyzed)

    report.summary = (
        f"{len(elements)} elements, {len(threats)} threats "
        f"({sum(t['disposition'] == 'accept' for t in threats.values())} accepted), "
        f"{len(reqs)} requirements, {len(links)} trace links"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument(
        "--allow-unanalyzed", action="store_true",
        help="report STRIDE elements with no threat rows as warnings, not errors",
    )
    args = parser.parse_args(argv)

    report = validate(args.data_dir, args.allow_unanalyzed)
    for w in report.warnings:
        print(f"WARNING {w}")
    for e in report.errors:
        print(f"ERROR   {e}")
    if report.summary:
        print(report.summary)
    status = "FAIL" if report.errors else "PASS"
    print(f"{status}: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
