#!/usr/bin/env python3
"""Render generated Markdown views from data/*.csv into the docs.

Views are written between marker comments:
    <!-- BEGIN GENERATED: <name> -->  ...  <!-- END GENERATED: <name> -->

    python tools/render_views.py           # rewrite the views in place
    python tools/render_views.py --check   # exit 1 if any view is out of date

Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from check_series_status import check  # noqa: E402
from validate_trace import CATALOGS, STRIDE_APPLICABLE, STRIDE_ELEMENT_TYPES, split_multi  # noqa: E402

TYPE_LABEL = {"process": "Process", "external_entity": "External entity",
              "data_store": "Data store", "data_flow": "Data flow"}


def read(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def threat_matrix() -> str:
    elements = [e for e in read("elements.csv") if e["type"] in STRIDE_ELEMENT_TYPES]
    threats = read("threats.csv")
    by_cell: dict[tuple[str, str], list[str]] = {}
    for t in threats:
        by_cell.setdefault((t["element_id"], t["stride"]), []).append(t["threat_id"])

    impact = Counter(t["mission_impact"] for t in threats)
    accepted = sum(t["disposition"] == "accept" for t in threats)
    lines = [
        f"{len(threats)} threats on {len(elements)} STRIDE elements: "
        + ", ".join(f"{impact[k]} {k}" for k in sorted(impact))
        + f"; {len(threats) - accepted} mitigated, {accepted} accepted.",
        "",
        "Blank: applicable, no threat recorded. –: category does not apply to the element type.",
        "",
        "| Element | Type | S | T | R | I | D | E |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in elements:
        eid, etype = e["element_id"], e["type"]
        cells = []
        for c in "STRIDE":
            if c not in STRIDE_APPLICABLE[etype]:
                cells.append("–")
            else:
                cells.append(", ".join(by_cell.get((eid, c), [])))
        name = f"{eid} {e['name']}"
        if e["no_threat_rationale"]:
            name += " (rationale)"
        lines.append(f"| {cell(name)} | {TYPE_LABEL[etype]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def verified_by() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for ve in read("verification.csv"):
        for rid in split_multi(ve["req_ids"]):
            out.setdefault(rid, []).append(ve["ve_id"])
    return out


def requirements_table() -> str:
    reqs = read("requirements.csv")
    parents: dict[str, list[str]] = {}
    for link in read("trace.csv"):
        parents.setdefault(link["req_id"], []).append(link["threat_id"])
    ves = verified_by()
    by_repo = Counter(r["evidence_repo"] for r in reqs)
    lines = [
        f"{len(reqs)} requirements. Evidence: "
        + ", ".join(f"{k} {by_repo[k]}" for k in sorted(by_repo)) + ".",
        "",
        "| ID | Requirement | Allocated to | Method | Evidence | Verified by | Parent threats |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in reqs:
        lines.append(
            f"| {r['req_id']} | {cell(r['statement'])} | {r['allocated_to']} | "
            f"{r['verification']} | {r['evidence_repo']} | {', '.join(ves.get(r['req_id'], []))} | "
            f"{', '.join(sorted(parents.get(r['req_id'], [])))} |"
        )
    return "\n".join(lines)


def resiliency_approaches() -> str:
    with (DATA / CATALOGS["resiliency"]).open(newline="", encoding="utf-8-sig") as f:
        catalog = list(csv.DictReader(f))
    users: dict[str, list[str]] = {}
    for r in read("requirements.csv"):
        for approach in split_multi(r["resiliency_approach"]):
            users.setdefault(approach, []).append(r["req_id"])
    techniques = list(dict.fromkeys(row["technique"] for row in catalog))
    used_tech = [t for t in techniques if any(row["id"] in users for row in catalog if row["technique"] == t)]
    unused = [t for t in techniques if t not in used_tech]
    lines = [
        f"{len(used_tech)} of {len(techniques)} techniques and {len(users)} of {len(catalog)} approaches "
        f"are used by at least one requirement. Not used: {', '.join(unused) or 'none'}.",
        "",
        "| Technique | Approach | Requirements |",
        "|---|---|---|",
    ]
    for row in catalog:
        if row["id"] in users:
            lines.append(f"| {row['technique']} | {row['approach']} | {', '.join(users[row['id']])} |")
    return "\n".join(lines)


def verification_events() -> str:
    events = read("verification.csv")
    status = Counter(e["status"] for e in events)
    lines = [
        f"{len(events)} verification events: " + ", ".join(f"{status[k]} {k}" for k in sorted(status)) + ".",
        "",
        "| ID | Event | Method | Evidence | Verifies | Status | Pass criteria |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in events:
        lines.append(
            f"| {e['ve_id']} | {cell(e['title'])} | {e['method']} | {e['evidence_repo']} | "
            f"{', '.join(split_multi(e['req_ids']))} | {status_cell(e)} | {cell(e['pass_criteria'])} |"
        )
    return "\n".join(lines)


def status_cell(event: dict) -> str:
    """The status, linked to its evidence: one link, or numbered links if several."""
    links = split_multi(event["evidence"])
    if len(links) == 1:
        return f"[{event['status']}]({links[0]})"
    if links:
        return f"{event['status']}: " + ", ".join(f"[{i}]({u})" for i, u in enumerate(links, 1))
    return event["status"]


SERIES_OWNER = "samyoon727ca"
SERIES_STATUS = DATA / "series-status"
ALIGNMENT = ROOT / "docs/series-alignment.md"
# Shown for a repo that has no status snapshot yet.
FALLBACK_LINKS = {"P2": ("emulation-only evidence", "overview/p2-snapshot/evidence/")}


def ve_number(ve_id: str) -> int:
    return int(ve_id.split("-")[1])


def format_ves(ve_ids: list[str], links: dict[str, list[str]] | None = None) -> str:
    """VE IDs in order; runs of three or more consecutive IDs become 'VE-01 to VE-06'.

    An ID with evidence links is linked (numbered if several) and is never folded into a run.
    """
    links = links or {}
    parts: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if len(run) >= 3:
            parts.append(f"{run[0]} to {run[-1]}")
        else:
            parts.extend(run)
        run.clear()

    for ve in ve_ids:
        urls = [cell(u) for u in links.get(ve, [])]
        if urls:
            flush()
            if len(urls) == 1:
                parts.append(f"[{ve}]({urls[0]})")
            else:
                parts.append(f"{ve} (" + ", ".join(f"[{i}]({u})" for i, u in enumerate(urls, 1)) + ")")
            continue
        if run and ve_number(ve) != ve_number(run[-1]) + 1:
            flush()
        run.append(ve)
    flush()
    return ", ".join(parts)


def requirement_count(ve_ids: list[str], events: dict[str, dict]) -> int:
    return len({rid for ve in ve_ids for rid in split_multi(events[ve]["req_ids"])})


def load_snapshot(row: dict, snapshot_dir: Path) -> dict[str, dict] | None:
    """The repo's VE entries from its status snapshot, checked first; None if there is no snapshot."""
    path = snapshot_dir / f"{row['repo']}.json"
    if not path.is_file():
        return None
    report = check([path], DATA)
    if report.errors:
        raise SystemExit("invalid series status snapshot:\n  " + "\n  ".join(report.errors))
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {ve["ve_id"]: ve for ve in doc["ves"]}


def alignment_link(p_id: str, alignment: Path) -> str:
    """docs/series-alignment.md, with the anchor of the '## P#: ...' heading if there is one."""
    target = "docs/series-alignment.md"
    if alignment.is_file():
        for line in alignment.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"## {p_id}:"):
                slug = re.sub(r"[^\w\- ]", "", line[3:].strip().lower()).replace(" ", "-")
                return f"{target}#{slug}"
    return target


def series_status(row: dict, events: dict[str, dict], snapshot_dir: Path, alignment: Path) -> str:
    ve_ids = split_multi(row["ve_ids"])
    snapshot = load_snapshot(row, snapshot_dir)
    by_status: dict[str, list[str]] = {}
    links: dict[str, list[str]] = {}
    for ve in ve_ids:
        entry = (snapshot or {}).get(ve)
        if entry is None:
            status, links[ve] = events[ve]["status"], split_multi(events[ve]["evidence"])
        else:
            status, links[ve] = entry["status"], entry["evidence"]
        by_status.setdefault(status, []).append(ve)
    text = "; ".join(f"{status}: {format_ves(ves, links)}" for status, ves in by_status.items())
    if snapshot is None and row["p_id"] in FALLBACK_LINKS:
        label, url = FALLBACK_LINKS[row["p_id"]]
        text += f" ([{label}]({url}))"
    if row["alignment"] == "pending decision":
        text += (f"<br>Allocation pending decision: {cell(row['note'])} "
                 f"([series alignment]({alignment_link(row['p_id'], alignment)}))")
    return text


def series_table(snapshot_dir: Path = SERIES_STATUS, alignment: Path = ALIGNMENT) -> str:
    events = {e["ve_id"]: e for e in read("verification.csv")}
    lines = [
        "| Repo | Scope | Requirements | Verification events | Status |",
        "|---|---|---|---|---|",
    ]
    for row in read("series.csv"):
        ve_ids = split_multi(row["ve_ids"])
        if not ve_ids:  # P1 itself
            continue
        lines.append(
            f"| [{row['p_id']}](https://github.com/{SERIES_OWNER}/{row['repo']}) | {cell(row['scope'])} | "
            f"{requirement_count(ve_ids, events)} | {format_ves(ve_ids)} | "
            f"{series_status(row, events, snapshot_dir, alignment)} |"
        )
    return "\n".join(lines)


VIEWS = {
    "threat-matrix": (ROOT / "docs/05-threat-model.md", threat_matrix),
    "requirements-table": (ROOT / "docs/07-requirements.md", requirements_table),
    "resiliency-approaches": (ROOT / "docs/06-cyber-resiliency.md", resiliency_approaches),
    "verification-events": (ROOT / "docs/08-verification-plan.md", verification_events),
    "series-table": (ROOT / "README.md", series_table),
}


def splice(text: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!-- BEGIN GENERATED: {re.escape(name)} -->\n)(?:.*?\n)?(<!-- END GENERATED: {re.escape(name)} -->)",
        re.S,
    )
    if not pattern.search(text):
        raise SystemExit(f"markers for view '{name}' not found")
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text, count=1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if any generated view is out of date")
    args = parser.parse_args(argv)

    stale = []
    for name, (path, render) in VIEWS.items():
        text = path.read_text(encoding="utf-8")
        new = splice(text, name, render())
        if new != text:
            stale.append(f"{path.relative_to(ROOT)} ({name})")
            if not args.check:
                path.write_text(new, encoding="utf-8")
    if args.check and stale:
        for s in stale:
            print(f"STALE   {s}: run python tools/render_views.py")
        return 1
    print("views up to date" if args.check else f"rendered {len(VIEWS)} view(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
