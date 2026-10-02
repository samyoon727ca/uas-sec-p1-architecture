# Traceability data

These four CSVs are the single source of truth for P1's elements, threats, requirements and trace links. GitHub renders each file as a searchable table. `tools/validate_trace.py` enforces every rule below on each push.

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
| `stride` | One of `S`, `T`, `R`, `I`, `D`, `E` |
| `emb3d` | Optional. MITRE EMB3D threat IDs, `TID-###` |
| `attack_ics` | Optional. MITRE ATT&CK for ICS technique IDs, `T####` |
| `mission_impact` | `MI-1` to `MI-4` (scale below) |
| `disposition` | `mitigate` (at least one requirement traces to it) or `accept` |
| `acceptance_rationale` | Required for `accept`; empty for `mitigate` |

The validator checks EMB3D and ATT&CK IDs for format only. Their existence is checked by hand against the pinned versions in [references](../docs/references.md).

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
| `resiliency_technique` | Optional. One or more of the 14 techniques in NIST SP 800-160 Vol. 2 Rev. 1, Table D-2 |

Parent threats are not stored here. They live only in `trace.csv`, so the two can't drift apart.

## `trace.csv`

| Column | Rule |
|---|---|
| `threat_id` | A known threat |
| `req_id` | A known requirement |

Every requirement needs at least one parent threat. Duplicate pairs are rejected.

## Running locally

```sh
python -m unittest discover -s tests   # validator self-tests
python tools/validate_trace.py         # validate data/
```
