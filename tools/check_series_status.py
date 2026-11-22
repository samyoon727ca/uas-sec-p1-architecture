#!/usr/bin/env python3
"""Check series-status.json files against P1's series manifest.

Each series repo publishes series-status.json at its root (format in
docs/series-status.md). This reads one or more local copies plus
data/series.csv and data/verification.csv and reports an error when a file
names an unknown p_id or repo, claims a VE that series.csv does not allocate
to that repo, uses an unknown ve_id or status, links evidence not pinned to a
full commit SHA, or has a malformed p1_commit. An allocated VE missing from
the file is a warning. Exits 1 if any error is found. Standard library only.

Usage:
    python tools/check_series_status.py [--data-dir data] PATH...
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_trace import EVIDENCE_URL, Report, load, split_multi  # noqa: E402

STATUSES = ("planned", "in progress", "partly evidenced", "evidenced")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
FIELDS = {"p_id": str, "repo": str, "p1_commit": str, "ves": list}


def check_file(path: Path, series: dict[str, dict], events: set[str], report: Report) -> None:
    where = str(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report.error(where, f"cannot read JSON: {exc}")
        return
    if not isinstance(doc, dict):
        report.error(where, "top level must be a JSON object")
        return
    bad = [name for name, kind in FIELDS.items() if not isinstance(doc.get(name), kind)]
    for name in bad:
        report.error(where, f"'{name}' is required and must be a {FIELDS[name].__name__}")
    if bad:
        return

    if not COMMIT.match(doc["p1_commit"]):
        report.error(where, f"p1_commit '{doc['p1_commit']}' must be a full 40-character lowercase hex SHA")

    row = series.get(doc["p_id"])
    if row is None:
        report.error(where, f"p_id '{doc['p_id']}' is not a row in series.csv")
        allocated = None
    else:
        if doc["repo"] != row["repo"]:
            report.error(where, f"repo '{doc['repo']}' does not match series.csv, which names "
                                f"'{row['repo']}' for {doc['p_id']}")
        allocated = split_multi(row["ve_ids"])

    seen: set[str] = set()
    for i, ve in enumerate(doc["ves"]):
        at = f"{where}: ves[{i}]"
        if not isinstance(ve, dict):
            report.error(at, "must be an object with ve_id, status and evidence")
            continue
        ve_id, status, evidence = ve.get("ve_id"), ve.get("status"), ve.get("evidence")
        if not isinstance(ve_id, str) or ve_id not in events:
            report.error(at, f"ve_id {ve_id!r} is not a known verification event")
        elif ve_id in seen:
            report.error(at, f"{ve_id} is listed more than once")
        else:
            seen.add(ve_id)
            if allocated is not None and ve_id not in allocated:
                owner = next((p for p, r in series.items() if ve_id in split_multi(r["ve_ids"])), "no repo")
                report.error(at, f"{doc['p_id']} claims {ve_id}, but series.csv allocates it to {owner}")
        if status not in STATUSES:
            report.error(at, f"status {status!r} must be one of {', '.join(STATUSES)}")
        if not isinstance(evidence, list):
            report.error(at, "'evidence' is required and must be a list of URLs")
            continue
        for link in evidence:
            if not isinstance(link, str) or not EVIDENCE_URL.match(link):
                report.error(at, f"evidence {link!r} must be a GitHub URL pinned to a full commit SHA")

    for ve_id in allocated or []:
        if ve_id not in seen:
            report.warn(where, f"{ve_id} is allocated to {doc['p_id']} but missing from the file")


def check(paths: list[Path], data_dir: Path) -> Report:
    report = Report()
    series_rows = load(data_dir / "series.csv", report)
    event_rows = load(data_dir / "verification.csv", report)
    if series_rows is None or event_rows is None:
        return report
    series = {row["p_id"]: row for row in series_rows}
    events = {row["ve_id"] for row in event_rows}
    for path in paths:
        check_file(path, series, events, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument("paths", metavar="PATH", type=Path, nargs="+", help="series-status.json file")
    args = parser.parse_args(argv)

    report = check(args.paths, args.data_dir)
    for w in report.warnings:
        print(f"WARNING {w}")
    for e in report.errors:
        print(f"ERROR   {e}")
    status = "FAIL" if report.errors else "PASS"
    print(f"{status}: {len(args.paths)} file(s), {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
