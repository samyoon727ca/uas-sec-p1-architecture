# Audit closures recorded in P1

Audit items that P1 closed after the audit of 2026-10-13. Each entry quotes the original finding, says what changed and where. The audit files are not edited: `findings.json` in this folder and the audit's `report.md` (held outside this repository) are unchanged, and their SHA-256 values in [`README.md`](README.md) still apply. A later audit will confirm or reopen these closures.

## 2026-11-19: P1-06 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-06 (README evidence-table 'Planned' column) also stands."
- **What changed.** In the evidence table of the top-level [`README.md`](../../README.md), the P2 row's Status now reads `In progress (emulation only)` instead of `Planned`, and links the status to the P2 CI evidence for VE-07 and VE-08 in [`overview/p2-snapshot/evidence/`](../p2-snapshot/evidence/) (pinned in [`overview/p2-snapshot/pin.txt`](../p2-snapshot/pin.txt)). That evidence comes from emulation, not hardware. The P3 to P6 rows are unchanged.
- **Change.** The pull request that closes issue #18 (samyoon727ca/uas-sec-p1-architecture#18).

## 2026-11-27: P1-01 and P1-08 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-01: brief/pdr-brief.md:29 'every number here is generated' (numbers are typed)." and "P1-08: README.md:24 'all 40 data-flow-diagram elements' (46 elements, 40 STRIDE elements)."
- **What changed.** The footer of [`brief/pdr-brief.md`](../../brief/pdr-brief.md) (line 29) now reads "every count taken from the repo's data is checked against it in CI". The Threat section of the top-level [`README.md`](../../README.md) (line 28) now reads "all 40 STRIDE elements (46 data-flow-diagram elements, less 6 trust boundaries)". The new check found two more wrong counts in the brief, which are corrected: 44 threats carry an EMB3D ID (it said 43) and 53 an ATT&CK for ICS ID (it said 52). Slide 4 now says "all 40 STRIDE elements" instead of "40 elements", and slide 8 no longer counts the source CSVs ("Five", though `data/` has six). The brief's PDF, [`brief/pdr-brief.pdf`](../../brief/pdr-brief.pdf), is not rebuilt in this change. `brief/build.sh` runs on the machine that made the change, but there it embeds macOS system fonts where the committed Ubuntu build uses Liberation fonts, so that PDF was not committed. Until the PDF is rebuilt with CI's toolchain, it still shows the old footer and EMB3D and ATT&CK counts; the `brief` job of `validate.yml` builds the corrected PDF as an artifact on every push. That gap is P1-09.
- **Check.** A rule in [`tools/validate_trace.py`](../../tools/validate_trace.py), run by the `traceability` job of `validate.yml`, computes the counts from `data/` and compares them with every place `README.md` and `brief/pdr-brief.md` state them, listed in `COUNT_CLAIMS`. A changed count or a reworded sentence that a pattern no longer matches fails the build. Tests are in `tests/test_validate_trace.py` (`CountClaimsTest`).
- **Change.** The pull request that closes issue #43 (samyoon727ca/uas-sec-p1-architecture#43).

## 2026-11-27: P1-07 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-07: docs/05-threat-model.md:108 THR-016/019 row omits SR-036 and P3."
- **What changed.** In the priority-threat table of [`docs/05-threat-model.md`](../../docs/05-threat-model.md) (§5.3, line 108), the `THR-016, THR-019` row now lists `SR-036 (rotate after loss of custody)` alongside `SR-026` to `SR-029`, and its Evidence cell now lists `P3, P4, P6`. Every other row of §5.3 and the `README.md` priority-threat table already matched `data/trace.csv` and `data/requirements.csv`. No data CSV under `data/` changed.
- **Check.** A rule in [`tools/validate_trace.py`](../../tools/validate_trace.py) (`PRIORITY_THREAT_TABLES`), run by the `traceability` job of `validate.yml`, parses both priority-threat tables and verifies that every row's listed requirements equal the set `data/trace.csv` links to that row's threats, and (for `docs/05-threat-model.md`) that the plain repo IDs in Evidence equal those requirements' `evidence_repo` values in `data/requirements.csv`. Tests are in `tests/test_validate_trace.py` (`PriorityThreatTablesTest`).
- **Change.** The pull request that closes issue #44 (samyoon727ca/uas-sec-p1-architecture#44).

The open status of every other P1 audit item is tracked in [`triage.md`](triage.md).
