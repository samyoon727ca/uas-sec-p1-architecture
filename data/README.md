# Traceability data

These six CSVs are the single source of truth for P1's elements, threats, requirements, trace links, verification events and the series of repos that produce the evidence. The `catalogs/` folder pins the framework IDs they may use. GitHub renders each file as a searchable table. `tools/validate_trace.py` enforces every rule below on each push.

Multi-value cells are semicolon-separated (`TID-201; TID-215`).

## `elements.csv`: DFD elements

One row per element of the [architecture](../docs/04-architecture.md).

| Column | Rule |
|---|---|
| `element_id` | Unique. Pattern depends on `type`: `CMP-*` process, `EE-*` external entity, `DS-*` data store, `DF-##` data flow, `TB-##` trust boundary |
| `name`, `description` | Required |
| `type` | `process`, `external_entity`, `data_store`, `data_flow`, `trust_boundary` |
| `host` | Data stores only: the `CMP-*` that holds it |
| `source`, `destination` | Data flows only: a process, external entity or data store |
| `crosses` | Data flows only: the `TB-##` boundaries the flow crosses |
| `interface` | Physical/logical interface and protocol (e.g. `UART; MAVLink 2 signed`) |
| `no_threat_rationale` | Required when a STRIDE element has no threat rows; must be empty otherwise |

**STRIDE-per-element completeness.** Every process, external entity, data store and data flow has at least one row in `threats.csv` or an explicit `no_threat_rationale`. Trust boundaries are not STRIDE elements: threats against a boundary are recorded on the flows that cross it.

## `threats.csv`

| Column | Rule |
|---|---|
| `threat_id` | Unique, `THR-###` |
| `title`, `description` | Required |
| `element_id` | The one STRIDE element the threat applies to |
| `stride` | One of `S`, `T`, `R`, `I`, `D`, `E`, and applicable to the element's type: processes all six, external entities `S` and `R`, data stores and data flows `T`, `I` and `D` (Microsoft's STRIDE-per-element chart) |
| `emb3d` | Optional. MITRE EMB3D threat IDs, `TID-###`, present in `catalogs/emb3d-v2.0.2.csv` |
| `attack_ics` | Optional. MITRE ATT&CK for ICS technique IDs, `T####` or `T####.###`, present in `catalogs/attack-ics-v19.2.csv` |
| `mission_impact` | `MI-1` to `MI-4` (scale below) |
| `disposition` | `mitigate` (at least one requirement traces to it) or `accept` |
| `acceptance_rationale` | Required for `accept`; empty for `mitigate` |

The validator checks every EMB3D and ATT&CK ID against the pinned catalogs in [`catalogs/`](catalogs/), so a revoked or mistyped ID fails the build.

**Mission-impact scale.** This scale is project-defined (assumption A-13), not taken from a standard.

| Rating | Meaning |
|---|---|
| MI-1 | Loss of vehicle control or vehicle, or a safety hazard to people or property |
| MI-2 | Mission failure, or loss of confidentiality of mission data (flight plans, imagery) |
| MI-3 | Mission degraded but completed |
| MI-4 | Negligible mission effect |

## `requirements.csv`

| Column | Rule |
|---|---|
| `req_id` | Unique, `SR-###` |
| `statement` | Exactly one "shall" |
| `rationale` | Required |
| `allocated_to` | One `CMP-*` component |
| `verification` | `I` Inspection, `A` Analysis, `D` Demonstration, `T` Test |
| `evidence_repo` | `P2` to `P6`: the repo that will produce the verification evidence |
| `resiliency_approach` | Optional. One or more NIST SP 800-160 Vol. 2 Rev. 1 `Technique: Approach` pairs, present in `catalogs/sp800-160v2r1-approaches.csv` |

Parent threats are not stored here. They live only in `trace.csv`, so the two can't drift apart.

## `trace.csv`

| Column | Rule |
|---|---|
| `threat_id` | A known threat |
| `req_id` | A known requirement |

Every requirement needs at least one parent threat. Duplicate pairs are rejected.

## `verification.csv`

| Column | Rule |
|---|---|
| `ve_id` | Unique, `VE-##` |
| `title`, `procedure`, `pass_criteria` | Required |
| `method` | `I`, `A`, `D` or `T` |
| `evidence_repo` | `P2` to `P6` |
| `req_ids` | One or more known requirements. Each must have the same method and evidence repo as the event |
| `status` | `planned`, `partly evidenced`, `passed` or `failed` |
| `evidence` | Required when `status` is `partly evidenced`, `passed` or `failed`; optional while `planned`. One or more links, separated by `;`, each a GitHub URL pinned to a full commit SHA: `https://github.com/<owner>/<repo>/blob/<sha>/<path>` (or `tree/`) |

Every requirement must be covered by at least one event whose method and evidence repo match its own.

The evidence repo (P2 to P6) records the result here with a pull request. Pinning each link to a commit means the evidence it shows cannot change after P1 records the result.

## `series.csv`: series manifest

One row per repo in the UAS series. This file is the source of truth for which repo each `P#` names and which verification events it owns.

| Column | Rule |
|---|---|
| `p_id` | Unique, `P` followed by digits (`P1`) |
| `repo` | Unique GitHub repo name: letters, digits, `_`, `.` and `-` only |
| `scope` | Required. The repo's scope, as in the [README](../README.md) table |
| `ve_ids` | Known verification events allocated to the repo; empty for P1 |
| `alignment` | `aligned`, or `pending decision` when the repo's actual work differs from its P1 allocation |
| `note` | Optional. For `pending decision`, one line on what the repo actually does |

Every event in `verification.csv` appears in exactly one row, the row whose `p_id` equals the event's `evidence_repo`. Every `evidence_repo` in `verification.csv` and `requirements.csv` must be a `p_id` here. Changing an allocation therefore means changing both files in the same pull request.

Each series repo reports its status in a `series-status.json` file that may claim only the VEs listed in its row here. The format is in [`docs/series-status.md`](../docs/series-status.md), and `tools/check_series_status.py` checks it.

## Counts in the README and brief

`README.md` and `brief/pdr-brief.md` state counts taken from these files: elements (all, STRIDE and trust boundaries), threats (total, by mission impact, mitigated and accepted, with an EMB3D or ATT&CK for ICS ID), requirements (total, by `allocated_to`, by `verification` and by `evidence_repo`), SP 800-160 techniques and approaches (used by requirements, and in the catalog), and verification events (total and `planned`). The validator computes each count and checks it at every place the two files state it. Those places are listed in `COUNT_CLAIMS` in `tools/validate_trace.py`, one `(file, regex, fact)` entry each. A pattern that matches nothing is an error, so a reworded sentence fails instead of going unchecked: update its pattern in the same pull request. The validator reads the two files under `--root`, which defaults to the parent of `--data-dir`; pass `--skip-counts` to validate a data folder that has no README or brief beside it.

## Priority-threat tables in `docs/05-threat-model.md` and the README

The hand-written priority-threat tables in [`docs/05-threat-model.md`](../docs/05-threat-model.md) (§5.3) and [`README.md`](../README.md) are checked against `trace.csv` and `requirements.csv` (`PRIORITY_THREAT_TABLES` in `tools/validate_trace.py`). For each row, the set of `SR-###` IDs in "Mitigated by" must equal the requirements that `trace.csv` links to the row's `THR-###` IDs. In `docs/05-threat-model.md`, the set of plain `P#` repo IDs in "Evidence" (ignoring parentheticals such as `(VE-01)`) must equal the `evidence_repo` values of those requirements in `requirements.csv`. A missing heading, table or column is an error. Like the count check, this reads under `--root` and is skipped by `--skip-counts`.

## Tools that read this folder

- `tools/validate_trace.py` checks every rule above.
- `tools/render_views.py` generates the doc views and the README series table from the CSVs and `series-status/`.
- `tools/gen_sysml.py` generates `model/sysml/uas_security.sysml` from the CSVs.
- `tools/check_series_status.py` checks series status files against `series.csv` and `verification.csv`.
- `tools/fetch_series_status.py` reads `series.csv` and writes each series repo's status file into `series-status/`.
- `tools/gen_overview.py` generates the project overview's tables and statuses from the CSVs.

## Running locally

```sh
python -m unittest discover -s tests   # validator self-tests
python tools/validate_trace.py         # validate data/
python tools/render_views.py           # regenerate doc views (--check in CI)
python tools/gen_sysml.py              # regenerate model/sysml/uas_security.sysml (--check in CI)
```
