#!/usr/bin/env python3
"""Validate the P1 traceability data in data/*.csv.

Checks schema, ID format and uniqueness, referential integrity, threat
dispositions, requirement quality, STRIDE-per-element applicability and
coverage, verification coverage, the series manifest, that EMB3D, ATT&CK
for ICS and NIST SP 800-160 Vol. 2 entries exist in the pinned catalogs
under data/catalogs/, and that the counts and priority-threat tables in
README.md, brief/pdr-brief.md and docs/05-threat-model.md match data/.
Exits 1 if any error is found. Standard library only.

Usage:
    python tools/validate_trace.py [--data-dir data] [--root DIR]
                                   [--skip-counts] [--allow-unanalyzed]

The doc checks (counts and priority-threat tables) read under --root, which
defaults to the parent of --data-dir; --skip-counts skips them.
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
        "evidence_repo", "resiliency_approach",
    ],
    "trace.csv": ["threat_id", "req_id"],
    "verification.csv": [
        "ve_id", "title", "method", "evidence_repo", "req_ids", "procedure",
        "pass_criteria", "status", "evidence",
    ],
    "series.csv": ["p_id", "repo", "scope", "ve_ids", "alignment", "note"],
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
# Which STRIDE categories apply to each element type: Microsoft's
# STRIDE-per-element chart (MSDN Magazine, November 2006, Figure 5).
STRIDE_APPLICABLE = {
    "process": set("STRIDE"),
    "external_entity": {"S", "R"},
    "data_store": {"T", "I", "D"},
    "data_flow": {"T", "I", "D"},
}

# Pinned framework catalogs (see data/catalogs/README.md).
CATALOGS = {
    "emb3d": "catalogs/emb3d-v2.0.2.csv",
    "attack_ics": "catalogs/attack-ics-v19.2.csv",
    # NIST SP 800-160 Vol. 2 Rev. 1, Table D-4: "Technique: Approach".
    "resiliency": "catalogs/sp800-160v2r1-approaches.csv",
}

THREAT_ID = re.compile(r"^THR-\d{3}$")
REQ_ID = re.compile(r"^SR-\d{3}$")
VE_ID = re.compile(r"^VE-\d{2}$")
P_ID = re.compile(r"^P\d+$")
REPO_NAME = re.compile(r"^[\w.-]+$")
EMB3D_ID = re.compile(r"^TID-\d{3}$")
ATTACK_ICS_ID = re.compile(r"^T\d{4}(\.\d{3})?$")
SHALL = re.compile(r"\bshall\b", re.IGNORECASE)
# Evidence links are pinned to a full commit SHA, so what they show cannot
# change after P1 records the result.
EVIDENCE_URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/(blob|tree)/[0-9a-f]{40}/\S+$")

STRIDE = {"S", "T", "R", "I", "D", "E"}
MISSION_IMPACT = {"MI-1", "MI-2", "MI-3", "MI-4"}
DISPOSITIONS = {"mitigate", "accept"}
VERIFICATION = {"I", "A", "D", "T"}  # Inspection, Analysis, Demonstration, Test
VE_STATUS = {"planned", "partly evidenced", "passed", "failed"}
ALIGNMENT = {"aligned", "pending decision"}


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


def load_catalogs(data_dir: Path, report: Report) -> dict[str, set[str]] | None:
    """Load the pinned framework ID catalogs. None if any is unusable."""
    catalogs: dict[str, set[str]] = {}
    for key, rel in CATALOGS.items():
        path = data_dir / rel
        if not path.is_file():
            report.error(rel, "catalog file not found")
            return None
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "id" not in reader.fieldnames:
                report.error(rel, "catalog must have an 'id' column")
                return None
            catalogs[key] = {row["id"].strip() for row in reader if row["id"]}
    return catalogs


def check_threats(rows: list[dict], elements: dict, catalogs: dict, report: Report) -> dict[str, dict]:
    index = index_unique(rows, "threat_id", THREAT_ID, report)
    for row in index.values():
        where = row["_where"]
        require(row, ["title", "description"], report)
        eid, stride = row["element_id"], row["stride"]
        if stride not in STRIDE:
            report.error(where, f"stride '{stride}' must be one of S,T,R,I,D,E")
        if eid not in elements:
            report.error(where, f"element_id '{eid}' is not a known element")
        elif elements[eid]["type"] not in STRIDE_ELEMENT_TYPES:
            report.error(where, f"element_id '{eid}' is a trust boundary; record the threat on a crossing data flow")
        elif stride in STRIDE and stride not in STRIDE_APPLICABLE[elements[eid]["type"]]:
            etype = elements[eid]["type"]
            allowed = ",".join(c for c in "STRIDE" if c in STRIDE_APPLICABLE[etype])
            report.error(where, f"stride '{stride}' does not apply to {etype} elements (allowed: {allowed})")
        for tid in split_multi(row["emb3d"]):
            if not EMB3D_ID.match(tid):
                report.error(where, f"malformed EMB3D ID '{tid}' (expected TID-###)")
            elif tid not in catalogs["emb3d"]:
                report.error(where, f"EMB3D ID '{tid}' is not in the pinned catalog ({CATALOGS['emb3d']})")
        for tid in split_multi(row["attack_ics"]):
            if not ATTACK_ICS_ID.match(tid):
                report.error(where, f"malformed ATT&CK for ICS ID '{tid}' (expected T#### or T####.###)")
            elif tid not in catalogs["attack_ics"]:
                report.error(where, f"ATT&CK for ICS ID '{tid}' is not in the pinned catalog ({CATALOGS['attack_ics']})")
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


def series_evidence_repos(rows: list[dict]) -> set[str]:
    """The evidence_repo values allowed in requirements and verification
    events: the series.csv p_ids other than P1, which holds this
    architecture rather than evidence. series.csv is the single source."""
    return {row["p_id"] for row in rows if P_ID.match(row["p_id"])} - {"P1"}


def check_requirements(rows: list[dict], elements: dict, catalogs: dict, evidence_repos: set[str],
                       report: Report) -> dict[str, dict]:
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
        if row["evidence_repo"] not in evidence_repos:
            report.error(where, f"evidence_repo '{row['evidence_repo']}' must be a p_id in series.csv "
                                f"other than P1 (one of {sorted(evidence_repos)})")
        for approach in split_multi(row["resiliency_approach"]):
            if approach not in catalogs["resiliency"]:
                report.error(where, f"'{approach}' is not an SP 800-160 Vol. 2 Rev. 1 'Technique: Approach' "
                                    f"({CATALOGS['resiliency']})")
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


def check_verification(rows: list[dict], reqs: dict, evidence_repos: set[str], report: Report) -> dict[str, dict]:
    """Every requirement must be covered by at least one verification event
    whose method and evidence repo match the requirement's. A passed or
    failed event, or one partly evidenced, must link its evidence."""
    index = index_unique(rows, "ve_id", VE_ID, report)
    covered: set[str] = set()
    for row in index.values():
        where = row["_where"]
        require(row, ["title", "procedure", "pass_criteria"], report)
        if row["method"] not in VERIFICATION:
            report.error(where, f"method '{row['method']}' must be one of I,A,D,T")
        if row["evidence_repo"] not in evidence_repos:
            report.error(where, f"evidence_repo '{row['evidence_repo']}' must be a p_id in series.csv "
                                f"other than P1 (one of {sorted(evidence_repos)})")
        if row["status"] not in VE_STATUS:
            report.error(where, f"status '{row['status']}' must be one of {sorted(VE_STATUS)}")
        links = split_multi(row["evidence"])
        if row["status"] in {"partly evidenced", "passed", "failed"} and not links:
            report.error(where, f"status '{row['status']}' requires 'evidence'")
        for link in links:
            if not EVIDENCE_URL.match(link):
                report.error(where, f"evidence '{link}' must be a GitHub URL pinned to a full commit SHA")
        rids = split_multi(row["req_ids"])
        if not rids:
            report.error(where, "'req_ids' is required")
        for rid in rids:
            req = reqs.get(rid)
            if req is None:
                report.error(where, f"req_id '{rid}' is not a known requirement")
                continue
            if req["verification"] != row["method"] or req["evidence_repo"] != row["evidence_repo"]:
                report.error(where, f"{rid} is {req['verification']}/{req['evidence_repo']} but "
                                    f"{row['ve_id']} is {row['method']}/{row['evidence_repo']}")
                continue
            covered.add(rid)
    for rid, req in reqs.items():
        if rid not in covered:
            report.error(req["_where"], f"{rid} is not covered by a verification event with matching method and evidence repo")
    return index


def check_series(rows: list[dict], events: dict, report: Report) -> dict[str, dict]:
    """series.csv is the manifest of series repos. Every verification event
    is listed in exactly one row, the row of its evidence repo. That every
    evidence repo is a p_id here is checked against series_evidence_repos()."""
    index = index_unique(rows, "p_id", P_ID, report)
    repos: dict[str, str] = {}
    listed: dict[str, dict] = {}
    for row in index.values():
        where, repo = row["_where"], row["repo"]
        require(row, ["scope"], report)
        if not REPO_NAME.match(repo):
            report.error(where, f"malformed repo '{repo}'")
        elif repo in repos:
            report.error(where, f"duplicate repo '{repo}' (first at {repos[repo]})")
        else:
            repos[repo] = where
        if row["alignment"] not in ALIGNMENT:
            report.error(where, f"alignment '{row['alignment']}' must be one of {sorted(ALIGNMENT)}")
        for ve in split_multi(row["ve_ids"]):
            event = events.get(ve)
            if event is None:
                report.error(where, f"ve_id '{ve}' is not a known verification event")
            elif ve in listed:
                report.error(where, f"{ve} is listed more than once (first at {listed[ve]['_where']})")
            else:
                listed[ve] = row
                if event["evidence_repo"] != row["p_id"]:
                    report.error(where, f"{ve} is listed under {row['p_id']} but its evidence_repo "
                                        f"is '{event['evidence_repo']}' in verification.csv")
    for ve, event in events.items():
        if ve not in listed:
            report.error(event["_where"], f"{ve} is not listed in series.csv")
    return index


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


def count_facts(elements, threats, reqs, events, catalogs) -> dict[str, int]:
    """The counts that README.md and brief/pdr-brief.md state, from data/."""
    approaches = {a for r in reqs.values() for a in split_multi(r["resiliency_approach"])}
    facts = {
        "elements": len(elements),
        "STRIDE elements": sum(e["type"] in STRIDE_ELEMENT_TYPES for e in elements.values()),
        "trust boundaries": sum(e["type"] == "trust_boundary" for e in elements.values()),
        "threats": len(threats),
        "mitigated threats": sum(t["disposition"] == "mitigate" for t in threats.values()),
        "accepted threats": sum(t["disposition"] == "accept" for t in threats.values()),
        "threats with an EMB3D ID": sum(bool(split_multi(t["emb3d"])) for t in threats.values()),
        "threats with an ATT&CK for ICS ID": sum(bool(split_multi(t["attack_ics"])) for t in threats.values()),
        "requirements": len(reqs),
        "verification events": len(events),
        "planned verification events": sum(e["status"] == "planned" for e in events.values()),
        "resiliency techniques used": len({a.split(":")[0] for a in approaches}),
        "resiliency approaches used": len(approaches),
        "resiliency techniques": len({a.split(":")[0] for a in catalogs["resiliency"]}),
        "resiliency approaches": len(catalogs["resiliency"]),
    }
    for mi in sorted(MISSION_IMPACT):
        facts[f"{mi} threats"] = sum(t["mission_impact"] == mi for t in threats.values())
    for eid, row in elements.items():
        if row["type"] == "process":
            facts[f"requirements allocated to {eid}"] = sum(r["allocated_to"] == eid for r in reqs.values())
    for method in sorted(VERIFICATION):
        facts[f"requirements verified by {method}"] = sum(r["verification"] == method for r in reqs.values())
    for repo in sorted({r["evidence_repo"] for r in reqs.values()}):
        facts[f"requirements with evidence repo {repo}"] = sum(r["evidence_repo"] == repo for r in reqs.values())
    return facts


# Every place README.md and brief/pdr-brief.md state a count taken from data/:
# (file relative to the repo root, regex with exactly one group capturing the
# number, fact from count_facts). Each pattern must match at least once, so a
# reworded sentence fails here instead of going unchecked; update its pattern
# in the same change. Every match must equal the fact.
COUNT_CLAIMS = [
    ("README.md", r"\b(\d+) of \d+ verification events are planned", "planned verification events"),
    ("README.md", r"\b\d+ of (\d+) verification events are planned", "verification events"),
    ("README.md", r"^(\d+) threats, analyzed STRIDE per element", "threats"),
    ("README.md", r"\bacross all (\d+) STRIDE elements", "STRIDE elements"),
    ("README.md", r"\((\d+) data-flow-diagram elements", "elements"),
    ("README.md", r"\bless (\d+) trust boundaries\)", "trust boundaries"),
    ("README.md", r"\b(\d+) MI-1\b", "MI-1 threats"),
    ("README.md", r"\b(\d+) MI-2\b", "MI-2 threats"),
    ("README.md", r"\b(\d+) MI-3\b", "MI-3 threats"),
    ("README.md", r"\b(\d+) MI-4\b", "MI-4 threats"),
    ("README.md", r"\b(\d+) are mitigated\b", "mitigated threats"),
    ("README.md", r"\b(\d+) accepted with rationale", "accepted threats"),
    ("README.md", r"^(\d+) derived \"shall\" requirements", "requirements"),
    ("README.md", r"\bCC (\d+)\b", "requirements allocated to CMP-CC"),
    ("README.md", r"\bMSS (\d+)\b", "requirements allocated to CMP-MSS"),
    ("README.md", r"\bFC (\d+)\b", "requirements allocated to CMP-FC"),
    ("README.md", r"\bGCS (\d+)\b", "requirements allocated to CMP-GCS"),
    ("README.md", r"\bTest (\d+)\b", "requirements verified by T"),
    ("README.md", r"\bInspection (\d+)\b", "requirements verified by I"),
    ("README.md", r"\bDemonstration (\d+)\b", "requirements verified by D"),
    ("README.md", r"\buses (\d+) of the \d+ NIST SP 800-160", "resiliency techniques used"),
    ("README.md", r"\buses \d+ of the (\d+) NIST SP 800-160", "resiliency techniques"),
    ("README.md", r"^(\d+) verification events cover all \d+ requirements", "verification events"),
    ("README.md", r"^\d+ verification events cover all (\d+) requirements", "requirements"),
    ("README.md", r"\| (\d+) verification events covering all requirements", "verification events"),
    ("brief/pdr-brief.md", r"\b(\d+) elements in all\b", "elements"),
    ("brief/pdr-brief.md", r"^## 4\. Threat model: (\d+) threats", "threats"),
    ("brief/pdr-brief.md", r"\*\*Coverage:\*\* all (\d+) STRIDE elements", "STRIDE elements"),
    ("brief/pdr-brief.md", r"\bEMB3D v2\.0\.2 \((\d+) threats\)", "threats with an EMB3D ID"),
    ("brief/pdr-brief.md", r"\bATT&CK for ICS v19\.2 \((\d+)\)", "threats with an ATT&CK for ICS ID"),
    ("brief/pdr-brief.md", r"\b(\d+) MI-1\b", "MI-1 threats"),
    ("brief/pdr-brief.md", r"\b(\d+) MI-2\b", "MI-2 threats"),
    ("brief/pdr-brief.md", r"\b(\d+) MI-3\b", "MI-3 threats"),
    ("brief/pdr-brief.md", r"\b(\d+) MI-4\b", "MI-4 threats"),
    ("brief/pdr-brief.md", r"\b(\d+) mitigated, ", "mitigated threats"),
    ("brief/pdr-brief.md", r"\b(\d+) accepted with rationale", "accepted threats"),
    ("brief/pdr-brief.md", r"^## 6\. Requirements: (\d+) derived", "requirements"),
    ("brief/pdr-brief.md", r"\bCC (\d+)\b", "requirements allocated to CMP-CC"),
    ("brief/pdr-brief.md", r"\bMSS (\d+)\b", "requirements allocated to CMP-MSS"),
    ("brief/pdr-brief.md", r"\bFC (\d+)\b", "requirements allocated to CMP-FC"),
    ("brief/pdr-brief.md", r"\bGCS (\d+)\b", "requirements allocated to CMP-GCS"),
    ("brief/pdr-brief.md", r"\bTest (\d+)\b", "requirements verified by T"),
    ("brief/pdr-brief.md", r"\bInspection (\d+)\b", "requirements verified by I"),
    ("brief/pdr-brief.md", r"\bDemonstration (\d+)\b", "requirements verified by D"),
    ("brief/pdr-brief.md", r"\b(\d+) of \d+ techniques, through", "resiliency techniques used"),
    ("brief/pdr-brief.md", r"\b\d+ of (\d+) techniques, through", "resiliency techniques"),
    ("brief/pdr-brief.md", r"\bthrough (\d+) of \d+ approaches", "resiliency approaches used"),
    ("brief/pdr-brief.md", r"\bthrough \d+ of (\d+) approaches", "resiliency approaches"),
    ("brief/pdr-brief.md", r"^(\d+) verification events cover all \d+ requirements", "verification events"),
    ("brief/pdr-brief.md", r"^\d+ verification events cover all (\d+) requirements", "requirements"),
    ("brief/pdr-brief.md", r"^\| P2 \| [^|\n]+ \| (\d+) \|", "requirements with evidence repo P2"),
    ("brief/pdr-brief.md", r"^\| P3 \| [^|\n]+ \| (\d+) \|", "requirements with evidence repo P3"),
    ("brief/pdr-brief.md", r"^\| P4 \| [^|\n]+ \| (\d+) \|", "requirements with evidence repo P4"),
    ("brief/pdr-brief.md", r"^\| P5 \| [^|\n]+ \| (\d+) \|", "requirements with evidence repo P5"),
    ("brief/pdr-brief.md", r"^\| P6 \| [^|\n]+ \| (\d+) \|", "requirements with evidence repo P6"),
]


def check_counts(root: Path, facts: dict[str, int], report: Report, claims=COUNT_CLAIMS) -> None:
    """Each count that a claim's pattern captures in its file must equal the
    fact computed from data/. A pattern that matches nothing is an error."""
    texts: dict[str, str | None] = {}
    for rel, pattern, fact in claims:
        if rel not in texts:
            path = root / rel
            texts[rel] = path.read_text(encoding="utf-8") if path.is_file() else None
            if texts[rel] is None:
                report.error(rel, "file not found (count check)")
        text = texts[rel]
        if text is None:
            continue
        regex = re.compile(pattern, re.MULTILINE)
        if regex.groups != 1:
            report.error(rel, f"count pattern '{pattern}' must have exactly one group")
            continue
        if fact not in facts:
            report.error(rel, f"count pattern '{pattern}' names unknown fact '{fact}'")
            continue
        matches = list(regex.finditer(text))
        if not matches:
            report.error(rel, f"count pattern '{pattern}' ({fact}) matches nothing; "
                              f"update it in COUNT_CLAIMS if the sentence was reworded")
        for m in matches:
            stated = int(m.group(1))
            if stated != facts[fact]:
                line = text.count("\n", 0, m.start(1)) + 1
                report.error(f"{rel}:{line}", f"states {stated} {fact}, but data/ has {facts[fact]}")


# Hand-written priority-threat summary tables checked against trace.csv and
# (when check_evidence is True) requirements.csv:
# (file relative to the repo root, heading/marker line above the table, check_evidence).
PRIORITY_THREAT_TABLES = [
    ("docs/05-threat-model.md", "## 5.3 Priority threats", True),
    ("README.md", "**Priority threats:**", False),
]

MD_TABLE_SEP = re.compile(r"^:?-+:?$")
THREAT_TOKEN = re.compile(r"\bTHR-\d+\b")
REQ_TOKEN = re.compile(r"\bSR-\d+\b")


def _split_md_row(line: str) -> list[str]:
    """Split a pipe-delimited Markdown table row into stripped cells."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def parse_markdown_table(text: str, rel: str, heading: str,
                         report: Report) -> tuple[int, list[str], list[tuple[int, list[str]]]] | None:
    """Find and parse the Markdown table immediately following heading.
    Returns (header line number, header cells, [(line number, cells), ...])."""
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line.strip() == heading]
    if not matches:
        report.error(rel, f"priority-threat table heading '{heading}' not found")
        return None
    if len(matches) > 1:
        report.error(rel, f"priority-threat table heading '{heading}' appears more than once")
        return None

    idx = matches[0] + 1
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("|"):
            break
        if re.match(r"^#{1,6}\s", stripped):
            report.error(rel, f"no markdown table found after '{heading}'")
            return None
        idx += 1
    if idx >= len(lines):
        report.error(rel, f"no markdown table found after '{heading}'")
        return None

    header_line = lines[idx].strip()
    header_lineno = idx + 1
    if len(header_line) < 2 or not header_line.endswith("|"):
        report.error(f"{rel}:{header_lineno}", "malformed markdown table header row")
        return None
    header = _split_md_row(header_line)

    sep_idx = idx + 1
    if sep_idx >= len(lines):
        report.error(f"{rel}:{header_lineno}", "markdown table missing separator row")
        return None
    sep_line = lines[sep_idx].strip()
    if len(sep_line) < 2 or not (sep_line.startswith("|") and sep_line.endswith("|")):
        report.error(f"{rel}:{sep_idx + 1}", "markdown table missing separator row")
        return None
    sep_cells = _split_md_row(sep_line)
    if len(sep_cells) != len(header) or not all(MD_TABLE_SEP.match(c) for c in sep_cells):
        report.error(f"{rel}:{sep_idx + 1}", "malformed markdown table separator row")
        return None

    rows: list[tuple[int, list[str]]] = []
    row_idx = sep_idx + 1
    while row_idx < len(lines) and lines[row_idx].strip().startswith("|"):
        raw = lines[row_idx].strip()
        lineno = row_idx + 1
        if len(raw) < 2 or not raw.endswith("|"):
            report.error(f"{rel}:{lineno}", "malformed markdown table row")
            row_idx += 1
            continue
        cells = _split_md_row(raw)
        if len(cells) != len(header):
            report.error(f"{rel}:{lineno}", f"table row has {len(cells)} cells, expected {len(header)}")
            row_idx += 1
            continue
        rows.append((lineno, cells))
        row_idx += 1

    if not rows:
        report.error(f"{rel}:{header_lineno}", f"priority-threat table after '{heading}' has no data rows")
        return None
    return header_lineno, header, rows


def _strip_parentheticals(text: str) -> str:
    """Remove parenthesised text, innermost first, so nested groups such as
    '(VE-01 (see P2))' go entirely. Unbalanced parentheses are left in place."""
    while True:
        stripped = re.sub(r"\([^()]*\)", "", text)
        if stripped == text:
            return text
        text = stripped


def check_priority_threats(root: Path, threats: dict, reqs: dict,
                           links: list[tuple[str, str]], report: Report,
                           tables=PRIORITY_THREAT_TABLES) -> None:
    """Each row of a priority-threat summary table must list exactly the SRs
    that trace.csv links to the row's threats, and (when check_evidence is
    True) the Evidence cell's plain repo IDs must match those SRs'
    evidence_repo values in requirements.csv."""
    traced_reqs: dict[str, set[str]] = {}
    for tid, rid in links:
        traced_reqs.setdefault(tid, set()).add(rid)

    for rel, heading, check_evidence in tables:
        path = root / rel
        if not path.is_file():
            report.error(rel, "file not found (priority threats check)")
            continue
        parsed = parse_markdown_table(path.read_text(encoding="utf-8"), rel, heading, report)
        if parsed is None:
            continue
        header_lineno, header, rows = parsed
        header_where = f"{rel}:{header_lineno}"
        if "Mitigated by" not in header:
            report.error(header_where, "priority-threat table missing required column 'Mitigated by'")
            continue
        mitigated_col = header.index("Mitigated by")
        evidence_col = None
        if check_evidence:
            if "Evidence" not in header:
                report.error(header_where, "priority-threat table missing required column 'Evidence'")
                continue
            evidence_col = header.index("Evidence")

        for lineno, cells in rows:
            where = f"{rel}:{lineno}"
            row_threats = THREAT_TOKEN.findall(cells[0])
            if not row_threats:
                report.error(where, "priority-threat row has no threat ID in first cell")
                continue
            unknown = [t for t in row_threats if t not in threats]
            for tid in unknown:
                report.error(where, f"unknown threat '{tid}' in priority-threat table")
            if unknown:
                continue

            thr_label = ", ".join(dict.fromkeys(row_threats))
            listed_srs = set(REQ_TOKEN.findall(cells[mitigated_col]))
            expected_srs = set().union(*(traced_reqs.get(t, set()) for t in row_threats))
            missing = expected_srs - listed_srs
            extra = listed_srs - expected_srs
            if missing:
                report.error(where, f"{thr_label}: missing traced requirement(s) "
                                    f"{', '.join(sorted(missing))} from trace.csv")
            if extra:
                report.error(where, f"{thr_label}: listed requirement(s) "
                                    f"{', '.join(sorted(extra))} do not trace to {thr_label} in trace.csv")

            if evidence_col is not None:
                ev_plain = _strip_parentheticals(cells[evidence_col])
                tokens = [tok.strip() for tok in ev_plain.split(",")] if ev_plain.strip() else []
                listed_repos: set[str] = set()
                bad_repo = False
                for tok in tokens:
                    if not P_ID.match(tok):
                        report.error(where, f"{thr_label}: malformed evidence repo '{tok}' in Evidence cell")
                        bad_repo = True
                    else:
                        listed_repos.add(tok)
                expected_repos = {reqs[sr]["evidence_repo"] for sr in expected_srs if sr in reqs}
                if not bad_repo and listed_repos != expected_repos:
                    got = ", ".join(sorted(listed_repos)) or "(none)"
                    want = ", ".join(sorted(expected_repos)) or "(none)"
                    report.error(where, f"{thr_label}: evidence repos '{got}' do not match "
                                        f"requirements.csv '{want}'")


def validate(data_dir: Path, allow_unanalyzed: bool = False, root: Path | None = None) -> Report:
    """Validate data_dir. If root is given, also check the counts and
    priority-threat tables in README.md, brief/pdr-brief.md and
    docs/05-threat-model.md against the data."""
    report = Report()
    loaded = {name: load(data_dir / name, report) for name in SCHEMAS}
    catalogs = load_catalogs(data_dir, report)
    if catalogs is None or any(rows is None for rows in loaded.values()):
        return report

    elements = check_elements(loaded["elements.csv"], report)
    threats = check_threats(loaded["threats.csv"], elements, catalogs, report)
    evidence_repos = series_evidence_repos(loaded["series.csv"])
    reqs = check_requirements(loaded["requirements.csv"], elements, catalogs, evidence_repos, report)
    links = check_trace(loaded["trace.csv"], threats, reqs, report)
    events = check_verification(loaded["verification.csv"], reqs, evidence_repos, report)
    series = check_series(loaded["series.csv"], events, report)
    check_closure(elements, threats, reqs, links, report, allow_unanalyzed)
    if root is not None:
        check_counts(root, count_facts(elements, threats, reqs, events, catalogs), report)
        check_priority_threats(root, threats, reqs, links, report)

    report.summary = (
        f"{len(elements)} elements, {len(threats)} threats "
        f"({sum(t['disposition'] == 'accept' for t in threats.values())} accepted), "
        f"{len(reqs)} requirements, {len(links)} trace links, {len(events)} verification events, "
        f"{len(series)} series repos"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data",
        help="folder holding the CSVs and catalogs/ (default: the repo's data/)",
    )
    parser.add_argument(
        "--root", type=Path, default=None,
        help="folder holding README.md, brief/pdr-brief.md and docs/05-threat-model.md "
             "for the doc checks (default: the parent of --data-dir)",
    )
    parser.add_argument(
        "--skip-counts", action="store_true",
        help="don't check the counts or priority-threat tables in README.md, "
             "brief/pdr-brief.md and docs/05-threat-model.md",
    )
    parser.add_argument(
        "--allow-unanalyzed", action="store_true",
        help="report STRIDE elements with no threat rows as warnings, not errors",
    )
    args = parser.parse_args(argv)

    if args.skip_counts and args.root is not None:
        parser.error("--root and --skip-counts can't be used together")
    if args.skip_counts:
        root = None
    else:
        root = args.root if args.root is not None else args.data_dir.resolve().parent
    report = validate(args.data_dir, args.allow_unanalyzed, root=root)
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
