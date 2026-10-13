#!/usr/bin/env python3
"""Expand the overview sources into one Markdown document for the PDF build.

    python3 tools/gen_overview.py --out overview/build

Reads the chapter sources in overview/src/, P1's data/*.csv and the pinned P2
snapshot in overview/p2-snapshot/, and writes to --out:

    overview.md        the document: chapters in order, every table and number filled in
    diagrams/dNN.mmd   each Mermaid block, for mermaid-cli to render as diagrams/dNN.svg
    provenance.json    the P1 and P2 commits the document states its numbers as of

Source conventions (overview/README.md has the full rules):

    <!-- gen: NAME ARGS -->   on a line of its own: replaced by a generated block
    {{NAME}}, {{NAME:ARG}}    inline: replaced by a generated value
    ```mermaid ... ```        a diagram

Project files overview/src/pN.md start with front matter naming the project
and its kind: "chapter" (a full chapter of its own) or "stub" (a section of
the roadmap chapter, with its P1 requirements and verification events added
automatically). Unknown generator names fail the build, so no status or count
is ever typed by hand. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_trace import split_multi  # noqa: E402

SRC = ROOT / "overview" / "src"
DATA = ROOT / "data"
SNAPSHOT = ROOT / "overview" / "p2-snapshot"

METHOD = {"T": "Test", "I": "Inspection", "D": "Demonstration", "A": "Analysis"}
COMPONENT = {"CMP-CC": "CC", "CMP-FC": "FC", "CMP-GCS": "GCS", "CMP-MSS": "MSS"}
STATUS_LABEL = {"passed": "passed", "failed": "**failed**", "planned": "planned", "n/a": "–"}

GEN = re.compile(r"^<!-- gen: ([a-z0-9-]+)((?: \S+)*) -->$", re.M)
INLINE = re.compile(r"\{\{\s*([a-z0-9_.]+)(?::([^{}]*?))?\s*\}\}")
MERMAID = re.compile(r"^```mermaid\n(.*?)^```$", re.M | re.S)
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
PROJECT_FILE = re.compile(r"^p(\d+)\.md$")
# Uncommitted changes here make the build say "+changes". The PDF itself is the
# build's output, so rebuilding it in the same tree does not count.
DIRTY_PATHS = ("data", "docs", "overview", "tools", ":(exclude)overview/overview.pdf")


class GenError(Exception):
    """A source asks for something the data cannot give."""


# --- small helpers --------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def counted(counter: Counter, labels: dict[str, str] | None = None, order: list[str] | None = None) -> str:
    keys = order or sorted(counter, key=lambda k: (-counter[k], k))
    return ", ".join(f"{(labels or {}).get(k, k)} {counter[k]}" for k in keys if counter[k])


def front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split 'key: value' front matter from the body. No front matter gives an empty dict."""
    m = FRONT_MATTER.match(text)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            key, sep, value = line.partition(":")
            if not sep:
                raise GenError(f"front matter line without ':': {line!r}")
            fields[key.strip()] = value.strip()
    return fields, text[m.end():]


def read_pin(path: Path) -> dict[str, str]:
    fields = {}
    for line in read_text(path).splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def git(*args: str, cwd: Path = ROOT) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def json_path(obj, path: str):
    """obj['a']['b'] for the path 'a/b'; list items by index."""
    for part in path.split("/"):
        if isinstance(obj, list):
            obj = obj[int(part)]
        elif isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            raise GenError(f"no '{part}' in evidence path '{path}'")
    return obj


# --- the data ---------------------------------------------------------------------

class Data:
    """P1's CSVs, the P2 snapshot and its evidence summaries, and the commits they come from."""

    def __init__(self, data: Path = DATA, snapshot: Path = SNAPSHOT, root: Path = ROOT) -> None:
        self.elements = {e["element_id"]: e for e in read_csv(data / "elements.csv")}
        self.threats = read_csv(data / "threats.csv")
        self.threat = {t["threat_id"]: t for t in self.threats}
        self.reqs = read_csv(data / "requirements.csv")
        self.req = {r["req_id"]: r for r in self.reqs}
        self.trace = read_csv(data / "trace.csv")
        self.ves = read_csv(data / "verification.csv")
        self.ve = {v["ve_id"]: v for v in self.ves}
        self.parents: dict[str, list[str]] = {}
        for link in self.trace:
            self.parents.setdefault(link["req_id"], []).append(link["threat_id"])
        self.verified_by: dict[str, list[str]] = {}
        for v in self.ves:
            for rid in split_multi(v["req_ids"]):
                self.verified_by.setdefault(rid, []).append(v["ve_id"])

        self.p2_pin = read_pin(snapshot / "pin.txt")
        self.p2_p1_pin = read_pin(snapshot / "data/p1/pin.txt")
        self.children = read_csv(snapshot / "data/requirements.csv")
        self.child_trace = read_csv(snapshot / "data/trace.csv")
        self.cases = read_csv(snapshot / "data/testcases.csv")
        self.case = {c["tc_id"]: c for c in self.cases}
        self.evidence: dict[str, dict] = {}
        for c in self.cases:
            for env in ("ci", "hw"):
                path = c[f"{env}_evidence"]
                if path and path not in self.evidence:
                    summary = snapshot / Path(path).parent / "summary.json"
                    if not summary.exists():
                        raise GenError(f"{c['tc_id']}: no summary.json in the P2 snapshot for {path}")
                    self.evidence[path] = json.loads(read_text(summary))

        head = git("rev-parse", "HEAD", cwd=root)
        self.p1 = {
            "head": head or "unknown",
            "data": git("log", "-1", "--first-parent", "--format=%H", "--", "data", cwd=root) or "unknown",
            "dirty": bool(git("status", "--porcelain", "--", *DIRTY_PATHS, cwd=root)) if head else False,
        }

    # P1 views ------------------------------------------------------------------

    def repo_reqs(self, repo: str) -> list[dict]:
        return [r for r in self.reqs if r["evidence_repo"] == repo]

    def repo_ves(self, repo: str) -> list[dict]:
        return [v for v in self.ves if v["evidence_repo"] == repo]

    def repo_threats(self, repo: str) -> list[str]:
        ids = {t for r in self.repo_reqs(repo) for t in self.parents.get(r["req_id"], [])}
        return sorted(ids)

    # P2 views ------------------------------------------------------------------

    def ve_cases(self, ve: str) -> list[dict]:
        cases = [c for c in self.cases if c["ve_id"] == ve]
        if not cases:
            raise GenError(f"no P2 test case for {ve}")
        return cases

    def rollup(self, ve: str) -> dict:
        """One status per event, by the rule P2's tools/render_views.py uses."""
        cases = self.ve_cases(ve)
        counts = {}
        for env in ("ci", "hw"):
            runs = [c[f"{env}_status"] for c in cases if c[f"{env}_status"] != "n/a"]
            counts[env] = (sum(s == "passed" for s in runs), len(runs), sum(s == "failed" for s in runs))
        passed = sum(c[0] for c in counts.values())
        total = sum(c[1] for c in counts.values())
        failed = sum(c[2] for c in counts.values())
        if failed:
            status = "failed"
        elif total and passed == total:
            status = "passed"
        elif passed:
            status = "in progress"
        else:
            status = "planned"
        return {"status": status, **counts}

    def ve_evidence(self, ve: str) -> tuple[str, dict]:
        """The one CI evidence folder an event's test cases cite, and its summary.json."""
        paths = sorted({c["ci_evidence"] for c in self.ve_cases(ve) if c["ci_evidence"]})
        if len(paths) != 1:
            raise GenError(f"{ve}: expected one CI evidence folder, found {paths}")
        return str(Path(paths[0]).parent.as_posix()), self.evidence[paths[0]]


# --- generated values ---------------------------------------------------------------

def short(sha: str) -> str:
    return sha[:7] if re.fullmatch(r"[0-9a-f]{40}", sha) else sha


def inline_values(d: Data) -> dict:
    """Inline generators: name -> function(arg) -> str."""
    impact = Counter(t["mission_impact"] for t in d.threats)
    accepted = sum(t["disposition"] == "accept" for t in d.threats)
    stride_elements = [e for e in d.elements.values()
                       if e["type"] in ("process", "external_entity", "data_store", "data_flow")]
    ve_status = Counter(v["status"] for v in d.ves)

    def need(arg: str | None, what: str) -> str:
        if not arg:
            raise GenError(f"{what} needs an argument")
        return arg

    def threat(arg):
        t = d.threat.get(need(arg, "p1.threat"))
        if not t:
            raise GenError(f"unknown threat {arg}")
        return t

    def req(arg):
        r = d.req.get(need(arg, "p1.req")) or next((c for c in d.children if c["req_id"] == arg), None)
        if not r:
            raise GenError(f"unknown requirement {arg}")
        return r

    def ve(arg):
        v = d.ve.get(need(arg, "p1.ve"))
        if not v:
            raise GenError(f"unknown verification event {arg}")
        return v

    def case(arg):
        c = d.case.get(need(arg, "p2.tc"))
        if not c:
            raise GenError(f"unknown test case {arg}")
        return c

    def ev(arg):
        ve_id, _, path = need(arg, "ev").partition(":")
        _, summary = d.ve_evidence(ve_id)
        value = json_path(summary, path)
        if isinstance(value, (dict, list)):
            raise GenError(f"evidence path {arg} is not a single value")
        return str(value)

    def ev_folder(arg):
        return d.ve_evidence(need(arg, "ev.folder"))[0]

    def ev_runs(arg):
        _, s = d.ve_evidence(need(arg, "ev.runs"))
        runs = s["runs"]
        controls = sum(r.get("role") == "control" for r in runs)
        of_them = "1 of them a control run" if controls == 1 else f"{controls} of them control runs"
        return f"{sum(bool(r['ok']) for r in runs)} of {len(runs)} runs passed, {of_them}"

    def ev_run_count(arg):
        return str(len(d.ve_evidence(need(arg, "ev.run_count"))[1]["runs"]))

    def ev_static_count(arg):
        return str(len(d.ve_evidence(need(arg, "ev.static_count"))[1].get("static") or []))

    def ev_tc_runs(arg):
        ve_id, _, tc = need(arg, "ev.tc_runs").partition(":")
        runs = [r for r in d.ve_evidence(ve_id)[1]["runs"] if r["tc"] == tc]
        if not runs:
            raise GenError(f"no run of {tc} in the {ve_id} evidence")
        roles = Counter(r["role"] for r in runs)
        words = {"positive": "positive run", "test": "test run", "control": "control run"}
        return " and ".join(f"{roles[k]} {words[k]}{'s' if roles[k] != 1 else ''}"
                            for k in ("positive", "test", "control") if roles[k])

    def tcs_where(pred) -> list[str]:
        return [c["tc_id"] for c in d.cases if pred(c)]

    def id_list(ids: list[str]) -> str:
        return ", ".join(ids) if ids else "none"

    values = {
        # commits
        "p1.commit": lambda a: short(d.p1["head"]),
        "p1.commit_full": lambda a: d.p1["head"],
        "p1.data_commit": lambda a: short(d.p1["data"]),
        "p1.data_commit_full": lambda a: d.p1["data"],
        "p2.commit": lambda a: short(d.p2_pin["commit"]),
        "p2.commit_full": lambda a: d.p2_pin["commit"],
        "p2.repo": lambda a: d.p2_pin["repo"],
        "p2.p1_pin": lambda a: short(d.p2_p1_pin["commit"]),
        "p2.p1_pin_full": lambda a: d.p2_p1_pin["commit"],
        # P1 counts
        "p1.threats": lambda a: str(len(d.threats)),
        "p1.threat_impacts": lambda a: ", ".join(f"{impact[k]} {k}" for k in sorted(impact)),
        "p1.threats_mitigated": lambda a: str(len(d.threats) - accepted),
        "p1.threats_accepted": lambda a: str(accepted),
        "p1.stride_elements": lambda a: str(len(stride_elements)),
        "p1.elements": lambda a: str(len(d.elements)),
        "p1.reqs": lambda a: str(len(d.reqs)),
        "p1.reqs_by_component": lambda a: counted(Counter(r["allocated_to"] for r in d.reqs), COMPONENT),
        "p1.reqs_by_method": lambda a: counted(Counter(r["verification"] for r in d.reqs), METHOD),
        "p1.reqs_by_repo": lambda a: counted(Counter(r["evidence_repo"] for r in d.reqs),
                                             order=sorted({r["evidence_repo"] for r in d.reqs})),
        "p1.trace_links": lambda a: str(len(d.trace)),
        "p1.ves": lambda a: str(len(d.ves)),
        "p1.ve_statuses": lambda a: ", ".join(f"{ve_status[k]} {k}" for k in sorted(ve_status)),
        "p1.repo_reqs": lambda a: str(len(d.repo_reqs(need(a, "p1.repo_reqs")))),
        "p1.repo_req_ids": lambda a: id_list([r["req_id"] for r in d.repo_reqs(need(a, "p1.repo_req_ids"))]),
        "p1.repo_ves": lambda a: id_list([v["ve_id"] for v in d.repo_ves(need(a, "p1.repo_ves"))]),
        "p1.repo_threats": lambda a: str(len(d.repo_threats(need(a, "p1.repo_threats")))),
        "p1.repo_threats_mi1": lambda a: str(sum(d.threat[t]["mission_impact"] == "MI-1"
                                                  for t in d.repo_threats(need(a, "p1.repo_threats_mi1")))),
        # single P1 items
        "p1.threat_title": lambda a: threat(a)["title"],
        "p1.threat_mi": lambda a: threat(a)["mission_impact"],
        "p1.req_statement": lambda a: req(a)["statement"],
        "p1.req_repo": lambda a: req(a)["evidence_repo"],
        "p1.ve_title": lambda a: ve(a)["title"],
        "p1.ve_status": lambda a: ve(a)["status"],
        "p1.ve_reqs": lambda a: ", ".join(split_multi(ve(a)["req_ids"])),
        # P2 counts and statuses
        "p2.children": lambda a: str(len(d.children)),
        "p2.tcs": lambda a: str(len(d.cases)),
        "p2.ve_ci": lambda a: "{} of {}".format(*d.rollup(need(a, "p2.ve_ci"))["ci"][:2]),
        "p2.ve_hw": lambda a: "{} of {}".format(*d.rollup(need(a, "p2.ve_hw"))["hw"][:2]),
        "p2.ve_status": lambda a: d.rollup(need(a, "p2.ve_status"))["status"],
        "p2.tc_title": lambda a: case(a)["title"],
        "p2.tc_ci": lambda a: STATUS_LABEL.get(case(a)["ci_status"], case(a)["ci_status"]),
        "p2.tc_hw": lambda a: STATUS_LABEL.get(case(a)["hw_status"], case(a)["hw_status"]),
        "p2.tc_ci_raw": lambda a: case(a)["ci_status"],
        "p2.tc_hw_raw": lambda a: case(a)["hw_status"],
        "p2.tcs_ci": lambda a: str(len(tcs_where(lambda c: c["ci_status"] != "n/a"))),
        "p2.tcs_hw": lambda a: str(len(tcs_where(lambda c: c["hw_status"] != "n/a"))),
        "p2.tcs_ci_passed": lambda a: str(len(tcs_where(lambda c: c["ci_status"] == "passed"))),
        "p2.tcs_hw_passed": lambda a: str(len(tcs_where(lambda c: c["hw_status"] == "passed"))),
        "p2.tcs_hw_planned": lambda a: str(len(tcs_where(lambda c: c["hw_status"] == "planned"))),
        "p2.tc_ids_ci_only": lambda a: id_list(tcs_where(lambda c: c["hw_status"] == "n/a")),
        "p2.tc_ids_hw_only": lambda a: id_list(tcs_where(lambda c: c["ci_status"] == "n/a")),
        "p2.tc_ids_ci_passed": lambda a: id_list(tcs_where(lambda c: c["ci_status"] == "passed")),
        # evidence (P2 snapshot)
        "ev": ev,
        "ev.folder": ev_folder,
        "ev.runs": ev_runs,
        "ev.run_count": ev_run_count,
        "ev.static_count": ev_static_count,
        "ev.tc_runs": ev_tc_runs,
        "p2.trace_links": lambda a: str(len(d.child_trace)),
    }
    return values


def expand_inline(text: str, values: dict) -> str:
    def sub(m: re.Match) -> str:
        name, arg = m.group(1), m.group(2)
        if name not in values:
            raise GenError(f"unknown inline value {{{{{name}}}}}")
        return values[name](arg.strip() if arg else None)
    return INLINE.sub(sub, text)


# --- generated blocks ---------------------------------------------------------------

def threat_cell(d: Data, ids: list[str]) -> str:
    return ", ".join(sorted(ids))


def block_p1_repos(d: Data, args: list[str]) -> str:
    repos = sorted({r["evidence_repo"] for r in d.reqs} | {v["evidence_repo"] for v in d.ves})
    rows = []
    for repo in repos:
        ves = d.repo_ves(repo)
        status = Counter(v["status"] for v in ves)
        rows.append([repo, str(len(d.repo_reqs(repo))), ", ".join(v["ve_id"] for v in ves),
                     ", ".join(f"{status[k]} {k}" for k in sorted(status))])
    return table(["Evidence repo", "Requirements", "Verification events", "Event status in P1"], rows)


def block_p1_reqs_of(d: Data, args: list[str]) -> str:
    (repo,) = args
    rows = [[r["req_id"], r["statement"], COMPONENT.get(r["allocated_to"], r["allocated_to"]),
             METHOD[r["verification"]], ", ".join(d.verified_by.get(r["req_id"], [])),
             threat_cell(d, d.parents.get(r["req_id"], []))] for r in d.repo_reqs(repo)]
    if not rows:
        raise GenError(f"no P1 requirement has evidence repo {repo}")
    return table(["ID", "Requirement", "On", "Method", "Verified by", "Parent threats"], rows)


def block_p1_threats_of(d: Data, args: list[str]) -> str:
    (repo,) = args
    rows = []
    for tid in d.repo_threats(repo):
        t = d.threat[tid]
        el = d.elements.get(t["element_id"], {})
        reqs = sorted(r["req_id"] for r in d.repo_reqs(repo) if tid in d.parents.get(r["req_id"], []))
        rows.append([tid, t["title"], f"{t['element_id']} {el.get('name', '')}".strip(), t["stride"],
                     t["mission_impact"], ", ".join(reqs)])
    return table(["Threat", "Title", "Element", "STRIDE", "Impact", f"{repo} requirement"], rows)


def block_p1_ves_of(d: Data, args: list[str]) -> str:
    (repo,) = args
    rows = [[v["ve_id"], v["title"], METHOD[v["method"]], ", ".join(split_multi(v["req_ids"])), v["status"],
             v["pass_criteria"]] for v in d.repo_ves(repo)]
    return table(["Event", "Title", "Method", "Verifies", "P1 status", "Pass criteria"], rows)


def block_p1_ve_procedure(d: Data, args: list[str]) -> str:
    rows = [[v, d.ve[v]["procedure"]] for v in args]
    return table(["Event", "Procedure in P1's data/verification.csv"], rows)


def block_p2_children(d: Data, args: list[str]) -> str:
    threats: dict[str, list[str]] = {}
    for t in d.child_trace:
        threats.setdefault(t["req_id"], []).append(t["threat_id"])
    cases: dict[str, list[str]] = {}
    for c in d.cases:
        for rid in split_multi(c["verifies"]):
            cases.setdefault(rid, []).append(c["tc_id"])
    rows = [[r["req_id"], r["statement"], r["parent_req"], ", ".join(threats.get(r["req_id"], [])),
             ", ".join(cases.get(r["req_id"], []))] for r in d.children]
    return table(["ID", "Requirement", "Parent", "Parent threats", "Verified by"], rows)


def block_p2_ve_status(d: Data, args: list[str]) -> str:
    rows = []
    for v in d.repo_ves("P2"):
        r = d.rollup(v["ve_id"])
        rows.append([f"{v['ve_id']} {v['title']}", ", ".join(split_multi(v["req_ids"])),
                     "{} of {}".format(*r["ci"][:2]), "{} of {}".format(*r["hw"][:2]), r["status"], v["status"]])
    return table(["Event", "Verifies (P1)", "CI runs passed", "Hardware runs passed", "P2 status", "P1 status"], rows)


def block_p2_testcases(d: Data, args: list[str]) -> str:
    rows = [[c["tc_id"], c["ve_id"], c["title"], ", ".join(split_multi(c["verifies"])),
             STATUS_LABEL.get(c["ci_status"], c["ci_status"]), STATUS_LABEL.get(c["hw_status"], c["hw_status"])]
            for c in d.cases]
    return table(["ID", "Event", "Test case", "Verifies", "CI", "Hardware"], rows)


def block_p2_tc(d: Data, args: list[str]) -> str:
    (tc,) = args
    c = d.case.get(tc)
    if not c:
        raise GenError(f"unknown test case {tc}")

    def status(env: str) -> str:
        s = c[f"{env}_status"]
        label = {"n/a": "does not run there"}.get(s, s)
        return f"{label} (evidence: `{Path(c[f'{env}_evidence']).parent.as_posix()}/`)" if c[f"{env}_evidence"] else label

    return "\n".join([
        '<div class="tc-card">',
        "",
        table([c["tc_id"], c["title"]], [
            ["Event", f"{c['ve_id']} {d.ve[c['ve_id']]['title']}"],
            ["Verifies", ", ".join(split_multi(c["verifies"]))],
            ["CI", status("ci")],
            ["Hardware", status("hw")],
            ["Procedure", c["procedure"]],
            ["Pass criteria", c["pass_criteria"]],
        ]),
        "",
        "</div>",
    ])


def block_p2_runs(d: Data, args: list[str]) -> str:
    (ve,) = args
    _, s = d.ve_evidence(ve)
    rows = []
    for r in s["runs"]:
        role = r["role"] + (f" for {r['control_for']}" if r.get("control_for") else "")
        rows.append([r["id"], role, r["title"], "pass" if r["ok"] else "**FAIL**"])
    return table(["Run", "Role", "What it boots or checks", "Result"], rows)


def block_p2_static(d: Data, args: list[str]) -> str:
    (ve,) = args
    _, s = d.ve_evidence(ve)
    checks = s.get("static") or []
    if not checks:
        raise GenError(f"{ve}: the evidence has no static checks")
    return table(["Static check", "Result"], [[c["pattern"], "pass" if c["ok"] else "**FAIL**"] for c in checks])


def block_p2_unseal(d: Data, args: list[str]) -> str:
    _, s = d.ve_evidence("VE-07")
    rows = []
    for r in s["runs"]:
        if not (r.get("data") or r.get("tpm", "blank") != "blank"):
            continue
        said = "; ".join(sorted({re.sub(r"^\S+ ", "", u) for u in r.get("unseal", [])
                                 if not u.startswith("control build")})) or "–"
        if any(u.startswith("control build") for u in r.get("unseal", [])):
            said += " (control build: response in the clear)"
        rows.append([r["id"], r["uboot"], r["slot"], r["tpm"], r["data"] or "–", said])
    return table(["Run", "U-Boot", "FIT", "TPM", "CC data", "What p2-unseal printed"], rows)


def block_p2_pcrs(d: Data, args: list[str]) -> str:
    _, s = d.ve_evidence("VE-07")
    pred = s["pcr_prediction"]
    rows = [[str(e["pcr"]), e["type"], e["event"], f"`{e['sha256'][:16]}…`"] for e in pred["events"]
            if e["type"] != "EV_SEPARATOR"]
    sep = [e for e in pred["events"] if e["type"] == "EV_SEPARATOR"]
    if sep:
        rows.append([f"{sep[0]['pcr']}–{sep[-1]['pcr']}", "EV_SEPARATOR", sep[0]["event"], f"`{sep[0]['sha256'][:16]}…`"])
    out = table(["PCR", "Event type", "Event data", "SHA-256 of what was measured"], rows)
    finals = [[i, f"`{pred['pcrs_sha256'][str(i)]}`"] for i in pred["policy_pcrs"]]
    return out + "\n\n" + table(["Policy PCR", "Predicted SHA-256 value (equal to measured and replayed in TC-10)"], finals)


def block_p2_host(d: Data, args: list[str]) -> str:
    (ve,) = args
    _, s = d.ve_evidence(ve)
    rows = [[k, v] for k, v in s.get("host", {}).items()]
    return table(["Tool", "Version the run recorded"], rows)


def block_p2_artifacts(d: Data, args: list[str]) -> str:
    _, s = d.ve_evidence("VE-07")
    names = args or ["u-boot-hardened.bin", "Image.gz", "initramfs.cpio.gz"]
    rows = []
    for n in names:
        if n not in s["artifacts_sha256"]:
            raise GenError(f"no artifact {n} in the VE-07 evidence")
        rows.append([f"`{n}`", f"`{s['artifacts_sha256'][n]}`"])
    return table(["Built file", "SHA-256 in the CI evidence"], rows)


def block_provenance(d: Data, args: list[str]) -> str:
    dirty = " (with uncommitted changes in data/, docs/, overview/ or tools/)" if d.p1["dirty"] else ""
    same = d.p2_p1_pin["commit"] == d.p1["data"]
    rows = [
        ["P1 tree the document was built from", f"`{d.p1['head']}`{dirty}"],
        ["P1 data (`data/*.csv`): last commit that changed it", f"`{d.p1['data']}`"],
        ["P2 snapshot (`overview/p2-snapshot/pin.txt`)", f"`{d.p2_pin['commit']}` ({d.p2_pin['repo']})"],
        ["P1 commit that P2's own snapshot pins (`data/p1/pin.txt` in P2)",
         f"`{d.p2_p1_pin['commit']}`" + (" (the same P1 data as this document)" if same else
                                         " (**differs** from the P1 data this document uses)")],
    ]
    for path, s in sorted(d.evidence.items()):
        env = s.get("environment", {})
        rows.append([f"P2 evidence `{Path(path).parent.as_posix()}/`",
                     f"{s.get('event', '')}: GitHub Actions run {env.get('run_id', '?')}, code commit "
                     f"`{short(s.get('git', {}).get('commit', '') or env.get('sha', ''))}`, {s.get('date_utc', '')}"])
    return table(["What", "Commit or run"], rows)


def block_mermaid_from(d: Data, args: list[str], root: Path = ROOT) -> str:
    """A Mermaid block copied from a P1 document: PATH INDEX [DIRECTION].

    DIRECTION (TB, BT, LR or RL) re-lays out a flowchart to fit the page; the
    nodes, edges and labels stay exactly as in the document.
    """
    path, index, *direction = args
    blocks = MERMAID.findall(read_text(root / path))
    try:
        body = blocks[int(index)]
    except (IndexError, ValueError):
        raise GenError(f"{path} has no Mermaid block {index}") from None
    if direction:
        if len(direction) > 1 or direction[0] not in ("TB", "BT", "LR", "RL"):
            raise GenError(f"direction must be one of TB, BT, LR, RL, not {' '.join(direction)}")
        body, n = re.subn(r"\A(flowchart|graph) (TB|TD|BT|LR|RL)\b", rf"\1 {direction[0]}", body)
        if not n:
            raise GenError(f"{path} Mermaid block {index} is not a flowchart with a direction")
    return f"```mermaid\n{body}```"


BLOCKS = {
    "p1-repos": block_p1_repos,
    "p1-reqs-of": block_p1_reqs_of,
    "p1-threats-of": block_p1_threats_of,
    "p1-ves-of": block_p1_ves_of,
    "p1-ve-procedure": block_p1_ve_procedure,
    "p2-children": block_p2_children,
    "p2-ve-status": block_p2_ve_status,
    "p2-testcases": block_p2_testcases,
    "p2-tc": block_p2_tc,
    "p2-runs": block_p2_runs,
    "p2-static": block_p2_static,
    "p2-unseal": block_p2_unseal,
    "p2-pcrs": block_p2_pcrs,
    "p2-host": block_p2_host,
    "p2-artifacts": block_p2_artifacts,
    "provenance": block_provenance,
    "mermaid-from": block_mermaid_from,
}


def expand_blocks(text: str, d: Data, extra: dict | None = None) -> str:
    blocks = {**BLOCKS, **(extra or {})}

    def sub(m: re.Match) -> str:
        name, args = m.group(1), m.group(2).split()
        if name not in blocks:
            raise GenError(f"unknown block <!-- gen: {name} -->")
        try:
            return blocks[name](d, args)
        except (ValueError, KeyError) as exc:
            raise GenError(f"<!-- gen: {name} {' '.join(args)} -->: {exc}") from exc
    return GEN.sub(sub, text)


# --- assembly -------------------------------------------------------------------------

def projects(src: Path) -> list[tuple[int, dict, str]]:
    """Project files in project order: (number, front matter, body)."""
    out = []
    for path in src.iterdir():
        m = PROJECT_FILE.match(path.name)
        if not m:
            continue
        meta, body = front_matter(read_text(path))
        if meta.get("project") != f"P{m.group(1)}":
            raise GenError(f"{path.name}: front matter must say 'project: P{m.group(1)}'")
        if meta.get("kind") not in ("chapter", "stub"):
            raise GenError(f"{path.name}: 'kind' must be chapter or stub")
        if meta["kind"] == "stub" and not meta.get("title"):
            raise GenError(f"{path.name}: a stub needs a 'title'")
        if meta["kind"] == "chapter" and not re.match(r"\A\s*# ", body):
            raise GenError(f"{path.name}: a chapter must start with a level-1 heading")
        out.append((int(m.group(1)), meta, body.strip() + "\n"))
    return sorted(out, key=lambda p: p[0])


def roadmap_sections(stubs: list[tuple[int, dict, str]]) -> str:
    parts = []
    for n, meta, body in stubs:
        parts.append(f"## P{n}: {meta['title']} {{#p{n}}}\n\n{body}\n"
                     f"<!-- gen: p1-reqs-of P{n} -->\n\n"
                     f"*The P1 requirements whose evidence repo is P{n} (P1 `data/requirements.csv`, "
                     f"`data/trace.csv`).*\n\n"
                     f"<!-- gen: p1-ves-of P{n} -->\n\n"
                     f"*The P1 verification events P{n} runs (P1 `data/verification.csv`).*\n")
    return "\n".join(parts)


def assemble(src: Path, d: Data) -> str:
    """Front matter, full chapters, the roadmap of stubs, the limitations slot and the appendix."""
    for name in ("front.md", "roadmap.md", "limitations.md", "appendix.md"):
        if not (src / name).exists():
            raise GenError(f"overview/src/{name} is missing")
    projs = projects(src)
    chapters = [body for _, meta, body in projs if meta["kind"] == "chapter"]
    stubs = [p for p in projs if p[1]["kind"] == "stub"]
    parts = [read_text(src / "front.md"), *chapters]
    if stubs:
        roadmap = read_text(src / "roadmap.md")
        if "<!-- gen: roadmap-stubs -->" not in roadmap:
            raise GenError("roadmap.md needs a '<!-- gen: roadmap-stubs -->' line")
        parts.append(roadmap.replace("<!-- gen: roadmap-stubs -->", roadmap_sections(stubs)))
    parts += [read_text(src / "limitations.md"), read_text(src / "appendix.md")]
    text = "\n\n".join(p.strip() + "\n" for p in parts)
    text = expand_blocks(text, d)
    return expand_inline(text, inline_values(d))


def extract_diagrams(text: str, out: Path) -> tuple[str, int]:
    """Write each Mermaid block to out/diagrams/dNN.mmd; put an image of it in its place."""
    (out / "diagrams").mkdir(parents=True, exist_ok=True)
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        n += 1
        name = f"d{n:02d}"
        (out / "diagrams" / f"{name}.mmd").write_bytes(m.group(1).encode("utf-8"))
        return f'<figure class="diagram" id="fig-{name}"><img src="diagrams/{name}.svg" alt="Diagram {n}"></figure>'
    return MERMAID.sub(sub, text), n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "overview" / "build", help="output folder")
    args = parser.parse_args(argv)
    try:
        d = Data()
        text = assemble(SRC, d)
        args.out.mkdir(parents=True, exist_ok=True)
        for old in (args.out / "diagrams").glob("*") if (args.out / "diagrams").exists() else []:
            old.unlink()
        text, diagrams = extract_diagrams(text, args.out)
    except GenError as exc:
        print(f"gen_overview: {exc}", file=sys.stderr)
        return 1
    leftover = re.findall(r"\{\{[^}]*\}\}|<!-- gen:[^>]*-->", text)
    if leftover:
        print(f"gen_overview: unexpanded {leftover[:3]}", file=sys.stderr)
        return 1
    (args.out / "overview.md").write_bytes(text.encode("utf-8"))
    provenance = {"p1_head": d.p1["head"], "p1_data": d.p1["data"], "p1_dirty": d.p1["dirty"],
                  "p2": d.p2_pin["commit"], "p2_p1_pin": d.p2_p1_pin["commit"]}
    (args.out / "provenance.json").write_bytes((json.dumps(provenance, indent=2) + "\n").encode("utf-8"))
    print(f"overview.md: {len(text.splitlines())} lines, {diagrams} diagram(s); "
          f"P1 data {short(d.p1['data'])}, P2 {short(d.p2_pin['commit'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
