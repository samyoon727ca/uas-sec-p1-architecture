# uas-sec-p1-architecture: guide

This repo is P1, the security architecture, threat model and derived security requirements for a notional, unclassified small drone built from open-source parts (a PX4 flight controller, a Linux companion computer, a ground control station and a MAVLink radio link). It is the anchor of a series of follow-on repos, P2 to P6, each of which implements and verifies some of the requirements allocated here. Its readers are the owner, reviewers of the series, and the follow-on repos, which copy and trace to its data.

## How it fits

- **What depends on it.** The five follow-on repos listed in `data/series.csv`: P2 `uas-sec-p2-verified-boot`, P3 `uas-sec-p3-pki`, P4 `uas-sec-p4-cc`, P5 `uas-sec-p5-fault-sim` and P6 `uas-sec-oscal`. Each owns the verification events (VEs, the planned tests and inspections that prove requirements) listed in its row. P2 keeps a byte-for-byte copy of P1's data at a pinned commit (`overview/p2-snapshot/data/p1/pin.txt` is that copy's pin, as seen from P2).
- **What it reads from them.** Each follow-on repo publishes a `series-status.json` (format in `docs/series-status.md`). A daily workflow fetches these into `data/series-status/` (`.github/workflows/series-status.yml`). The overview PDF also reads a pinned snapshot of P2 in `overview/p2-snapshot/`, pinned to a commit in `overview/p2-snapshot/pin.txt`.
- **Program items it carries.** All 17 VEs and 45 requirements are allocated here; the allocation for P4, P5 and P6 is marked "pending decision" in `data/series.csv` and discussed in `docs/series-alignment.md`.
- **Pinned external references.** PX4 `v1.18.0-rc1` (decision DD-06, `docs/04-architecture.md:217`), QGroundControl `v5.1.5`, and the other sources in `docs/references.md`. Framework catalogs are pinned as CSVs: MITRE EMB3D v2.0.2, ATT&CK for ICS v19.2 and NIST SP 800-160 Vol. 2 Rev. 1 approaches (`data/catalogs/`).
- **Pinned tools.** Python 3.11+ standard library only for every tool in `tools/` (README, "Run the checks locally"); CI uses Python 3.12 (`.github/workflows/validate.yml`). The SysML v2 Pilot Implementation release `2026-08` (Jupyter SysML kernel 0.62.0) with a pinned SHA-256 (`tools/sysml/validate.sh:10-12`), run on Java 21. Node 22 with `@marp-team/marp-cli` 4.5.1, `@mermaid-js/mermaid-cli` 12.0.0 and `puppeteer` 25.12.0 for the brief (`brief/package.json`), plus `markdown-it` 14.3.2 for the overview (`overview/package.json`). GitHub Actions are pinned to full commit SHAs in both workflows.

## How it works

The six CSVs in `data/` are the single source of truth (`data/README.md`). The prose docs in `docs/` are written by hand, except for tables between `<!-- BEGIN GENERATED -->` markers, which are rendered from the CSVs. Everything else is generated from or checked against the CSVs.

```text
data/*.csv + data/catalogs/*.csv
   ├─ tools/validate_trace.py ──> pass/fail (trace rules)
   ├─ tools/render_views.py ───> generated tables in docs/05–08 and README series table
   │      ▲ data/series-status/*.json  <── tools/fetch_series_status.py <── P2–P6 repos
   │      └─ checked by tools/check_series_status.py
   ├─ tools/gen_sysml.py ──────> model/sysml/uas_security.sysml ──> tools/sysml/validate.sh
   └─ tools/gen_overview.py ───> overview/build/ ──> overview/overview.pdf
          ▲ overview/src/*.md, overview/p2-snapshot/, overview/audit/findings.json
docs/04-architecture.md + README.md (Mermaid) ──> brief/build.sh ──> brief/pdr-brief.pdf
```

1. **Data.** `data/elements.csv` lists the 46 data-flow-diagram elements (40 STRIDE elements plus 6 trust boundaries). `data/threats.csv` holds 66 threats, `data/requirements.csv` 45 requirements, `data/trace.csv` the threat-to-requirement links, `data/verification.csv` the 17 VEs with status and evidence, and `data/series.csv` which repo owns which VEs.
2. **Validation.** `tools/validate_trace.py` checks schemas, ID formats, references, STRIDE applicability per element type (`tools/validate_trace.py:56`), coverage of every element by threats, every mitigated threat by a requirement and every requirement by a VE of the same method and repo, catalog IDs, and that a VE marked `partly evidenced`, `passed` or `failed` links evidence, every link pinned to a full commit SHA (`tools/validate_trace.py:322-326`). The allowed evidence repos are the `series.csv` p_ids other than P1 (`tools/validate_trace.py:254`).
3. **Doc views.** `tools/render_views.py` rewrites five generated blocks: the threat matrix, requirements table, resiliency approaches, verification events and the README series table (`tools/render_views.py:266`). The series table uses a repo's status snapshot when one exists and falls back to `data/verification.csv` per VE otherwise (`data/series-status/README.md`).
4. **Series status.** `tools/fetch_series_status.py` downloads each repo's `series-status.json`, capped at 1 MiB (`tools/fetch_series_status.py:31`), and removes snapshots of repos no longer in `series.csv` only after every fetch succeeds. `tools/check_series_status.py` then rejects files that claim VEs not allocated to their repo, use unknown IDs or statuses, or link unpinned evidence.
5. **SysML v2 model.** `model/sysml/uas_architecture.sysml` is hand-written; `tools/gen_sysml.py` generates `model/sysml/uas_security.sysml` from the CSVs. `tools/sysml/validate.sh` downloads the pinned Pilot Implementation and runs `tools/sysml/ValidateSysML.java` over both files. Conventions are in `model/sysml/README.md`.
6. **Brief.** `brief/build.sh` extracts Mermaid diagrams from `docs/04-architecture.md` and `README.md` into `brief/assets/*.mmd`, renders them, and builds `brief/pdr-brief.pdf` from `brief/pdr-brief.md` with Marp.
7. **Overview.** `overview/build.sh` runs `tools/gen_overview.py`, which expands `overview/src/*.md` with tables and numbers generated from `data/`, the P2 snapshot and the audit findings file, then renders diagrams and prints to PDF via `overview/render.mjs`. Its source conventions are in `overview/README.md`.

## Code map

| Path | What's there |
|---|---|
| `README.md` | Summary of threats, requirements and design; generated series table; local check commands |
| `docs/01-…08-*.md` | The baselined analysis: system, CONOPS, assumptions, architecture and decisions DD-01 to DD-06, threat model, resiliency, requirements, verification plan |
| `docs/references.md` | Sources with pinned versions |
| `docs/series-alignment.md` | Draft memo on where P4–P7 depart from P1's VE allocation; decisions pending |
| `docs/series-status.md` | Format of the `series-status.json` each follow-on repo publishes |
| `data/` | The six source-of-truth CSVs; column rules in `data/README.md` |
| `data/catalogs/` | Pinned EMB3D, ATT&CK for ICS and SP 800-160 catalogs |
| `data/series-status/` | Fetched status snapshots (currently only a README; no snapshot is committed) |
| `tools/validate_trace.py` | The traceability validator |
| `tools/render_views.py` | Generated tables in the docs and README |
| `tools/fetch_series_status.py`, `tools/check_series_status.py` | Fetch and check follow-on repos' status files |
| `tools/gen_sysml.py`, `tools/sysml/` | SysML generator and the Pilot Implementation validator |
| `tools/gen_overview.py`, `tools/check_p2_snapshot.py` | Overview generator; check that the P2 snapshot matches P2 |
| `model/sysml/` | SysML v2 model (one hand-written, one generated file) |
| `brief/` | 11-slide PDR-style brief: Marp source, built PDF, pinned Node toolchain |
| `overview/` | Overview PDF sources, P2 snapshot, audit findings copy and closures, build |
| `tests/` | `unittest` tests for every Python tool; fixtures in `tests/fixtures/series-status/` |
| `.github/workflows/` | `validate.yml` (every push and PR), `series-status.yml` (daily) |

## Run it and test it

From the README ("Run the checks locally"):

```sh
python -m unittest discover -s tests
python tools/validate_trace.py
python tools/render_views.py --check
python tools/gen_sysml.py --check
tools/sysml/validate.sh   # Java 21+; downloads the pinned SysML v2 Pilot Implementation once
CHROME_PATH=/path/to/chrome brief/build.sh   # Node 22+; rebuilds brief/pdr-brief.pdf
python tools/check_p2_snapshot.py            # needs network; overview/p2-snapshot matches P2
CHROME_PATH=/path/to/chrome overview/build.sh   # Node 22+, git; rebuilds overview/overview.pdf
python tools/fetch_series_status.py          # needs network; refreshes data/series-status/ from P2–P6
python tools/check_series_status.py data/series-status/*.json   # if any snapshots exist
```

To regenerate rather than check, run `python tools/render_views.py` or `python tools/gen_sysml.py` without `--check`. No virtual environment or install is needed for the Python tools.

What needs something special, and how CI handles it (`.github/workflows/validate.yml`):

- **`traceability` job:** Python 3.12; runs the unit tests (`-v`), `validate_trace.py`, `check_series_status.py` on any snapshots (skipped when there are none), `render_views.py --check` and `gen_sysml.py --check`. No network.
- **`sysml` job:** Java 21 (Temurin); needs network for the first download, cached in `.cache/sysml` keyed on the hash of `tools/sysml/validate.sh`.
- **`brief` job:** Node 22 and the runner's Chrome; builds the brief, fails if the regenerated `brief/assets/*.mmd` differ from the committed ones, and uploads the PDF as an artifact.
- **`overview` job:** full git history (the document names the last commit that changed `data/`), network for `check_p2_snapshot.py`, Node 22 and Chrome; uploads the PDF as an artifact.
- **`series-status.yml`:** daily at 06:23 UTC or on demand; fetches, checks, regenerates views, runs `validate_trace.py`, and on `main` only opens or updates a PR on `bot/series-status` using `GITHUB_TOKEN`. The unit tests are network-free: `tests/test_fetch_series_status.py` serves files from a local `http.server`.

## What's verified

All 120 unit tests pass with `python -m unittest discover -s tests`, and `validate_trace.py`, `render_views.py --check` and `gen_sysml.py --check` pass on the current data (run locally on Python 3.12.1 while writing this guide).

- **Trace rules** (every rule listed in the README's "Verification evidence" section): `tests/test_validate_trace.py` builds small datasets that break each rule (STRIDE applicability, missing parents, method and repo mismatch, unpinned evidence, catalog IDs, series manifest rules) and checks the real baseline passes (`test_baseline_is_valid`).
- **Generated views:** `tests/test_render_views.py` covers marker splicing, status cells, snapshot fallback per VE and rejection of an invalid snapshot; CI's `render_views.py --check` catches drift in the committed docs.
- **Series status:** `tests/test_check_series_status.py` (one fixture per error in `tests/fixtures/series-status/`) and `tests/test_fetch_series_status.py` (404 keeps a snapshot, other errors fail, size cap at and over 1 MiB, stale snapshot removed only when every fetch succeeds, `file://` base URL).
- **SysML:** `tests/test_gen_sysml.py` checks escaping, that every element has an alias, and that the committed model is current; the `sysml` CI job validates both model files on the OMG Pilot Implementation.
- **Overview generator:** `tests/test_gen_overview.py` covers front matter, stubs and chapters, unknown generator names failing, counts coming from data, audit findings rendering, and the P2 pin format. The `overview` CI job checks the snapshot against P2 over the network.
- **Brief:** CI checks only that the diagram sources match the docs and that the PDF builds.

Not tested or only documented:

- The committed PDFs (`brief/pdr-brief.pdf`, `overview/overview.pdf`) are not compared with the CI build; CI uploads fresh PDFs as artifacts, so a stale committed PDF would pass.
- The analysis itself (whether threats are complete, whether requirements are right) is reviewed by people, not by tests; the validator checks structure and coverage only.
- No requirement is verified yet: 16 VEs are `planned` and VE-02 is `partly evidenced` in `data/verification.csv`. P2's evidence is from emulation, not hardware (`overview/audit/closures.md`).
- `tools/check_p2_snapshot.py` and `tools/fetch_series_status.py` against the real GitHub hosts run only in CI, not in the unit tests.
- On the bot's series-status PR, `validate.yml` does not run, so the unit tests, `render_views.py --check` and `gen_sysml.py --check` are skipped for it (`.github/workflows/series-status.yml`, PR body text).

## Decisions and constraints

- **CSVs are the single source of truth;** tables, the SysML security model and overview numbers are generated, and CI fails on drift (`data/README.md`, `model/sysml/README.md`, `overview/README.md`). Parent threats live only in `trace.csv` so they can't drift from requirements.
- **Standard library only** for all Python tools, so the checks need no install (each tool's docstring; README).
- **Design decisions DD-01 to DD-06** are in `docs/04-architecture.md:212-217`: radio to CC to FC; WireGuard GCS-to-CC (with the note that its suite is not FIPS-approved); UART-only MAVLink with uXRCE-DDS disabled because signing doesn't cover DDS; a CC allowlist as defense in depth; Return on link loss; PX4 v1.18 because no v1.17 release has MAVLink signing.
- **Shared signing key.** PX4 uses one MAVLink signing key on all nodes, so FC, CC, GCS and maintenance station are all in the C2 trust base (`docs/04-architecture.md:3`).
- **Pinned everything:** catalog versions, PX4 tag, SysML kernel with SHA-256, Node toolchain lockfiles, Actions by commit SHA, evidence URLs pinned to full commit SHAs.
- **Mission-impact scale is project-defined** (assumption A-13), not from a standard (`data/README.md`).
- **OMG Pilot Implementation chosen** for SysML validation over paid or syntax-only alternatives; trade study in `model/sysml/README.md`.
- **Series status is pulled, not pushed:** P1 fetches status files and only accepts VEs that `series.csv` allocates to the repo (`docs/series-status.md`). The bot workflow uses only `GITHUB_TOKEN` and opens PRs only from `main`.
- **Snapshots and audit findings are byte-for-byte copies,** with line-ending conversion disabled (`.gitattributes`) so the hashes and the snapshot check hold. The audit's full report is held by the owner outside this repo (`overview/audit/README.md`).

## Open edges

- **OI-01:** QGroundControl and PX4 signing interoperability is not demonstrated; to be closed by VE-02 in P3, whose QGroundControl steps wait on uas-sec-p3-pki#6 (README "Status").
- **OI-02:** per-node authentication to the FC; trade study in P3. **OI-03:** no independent C2 path (the Path Diversity gap in `docs/06-cyber-resiliency.md`); deferred to a later P1 revision.
- **DD-06 re-pin** from PX4 `v1.18.0-rc1` to `v1.18.0` once released (`docs/references.md:7`).
- **Series alignment:** P4, P5 and P6 are "pending decision" in `data/series.csv`; every decision in `docs/series-alignment.md` is "Pending owner decision".
- **Audit findings open:** the 2026-10-13 audit's findings are rendered in the overview's limitations chapter; `overview/audit/closures.md` records one closure, and says the other items it lists are still open.
- **Closure note out of date:** `overview/audit/closures.md` says the README's P2 row reads `In progress (emulation only)`, but the generated row now reads `planned: VE-07, VE-08` with an emulation-only evidence link, because the series table is generated from `data/verification.csv` (where VE-07 and VE-08 are `planned`).
- **No series status snapshots yet:** `data/series-status/` holds only its README, so the series table currently comes entirely from `data/verification.csv`.
- **Overview covers only P2's data:** the generator reads only P2's snapshot; P3 to P6 are roadmap stubs (`overview/README.md`, "Chapters and stubs").
- **Stale committed PDFs** would not be caught by CI (see "What's verified").
