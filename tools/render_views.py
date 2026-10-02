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
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from validate_trace import STRIDE_APPLICABLE, STRIDE_ELEMENT_TYPES  # noqa: E402

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


def requirements_table() -> str:
    reqs = read("requirements.csv")
    parents: dict[str, list[str]] = {}
    for link in read("trace.csv"):
        parents.setdefault(link["req_id"], []).append(link["threat_id"])
    by_repo = Counter(r["evidence_repo"] for r in reqs)
    lines = [
        f"{len(reqs)} requirements. Evidence: "
        + ", ".join(f"{k} {by_repo[k]}" for k in sorted(by_repo)) + ".",
        "",
        "| ID | Requirement | Allocated to | Method | Evidence | Parent threats |",
        "|---|---|---|---|---|---|",
    ]
    for r in reqs:
        lines.append(
            f"| {r['req_id']} | {cell(r['statement'])} | {r['allocated_to']} | "
            f"{r['verification']} | {r['evidence_repo']} | {', '.join(sorted(parents.get(r['req_id'], [])))} |"
        )
    return "\n".join(lines)


VIEWS = {
    "threat-matrix": (ROOT / "docs/05-threat-model.md", threat_matrix),
    "requirements-table": (ROOT / "docs/07-requirements.md", requirements_table),
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
