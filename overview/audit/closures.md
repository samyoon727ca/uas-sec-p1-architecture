# Audit closures recorded in P1

Audit items that P1 closed after the audit of 2026-10-13. Each entry quotes the original finding, says what changed and where. The audit files are not edited: `findings.json` in this folder and the audit's `report.md` (held outside this repository) are unchanged, and their SHA-256 values in [`README.md`](README.md) still apply. A later audit will confirm or reopen these closures.

## 2026-11-19: P1-06 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-06 (README evidence-table 'Planned' column) also stands."
- **What changed.** In the evidence table of the top-level [`README.md`](../../README.md), the P2 row's Status now reads `In progress (emulation only)` instead of `Planned`, and links the status to the P2 CI evidence for VE-07 and VE-08 in [`overview/p2-snapshot/evidence/`](../p2-snapshot/evidence/) (pinned in [`overview/p2-snapshot/pin.txt`](../p2-snapshot/pin.txt)). That evidence comes from emulation, not hardware. The P3 to P6 rows are unchanged.
- **Change.** The pull request that closes issue #18 (samyoon727ca/uas-sec-p1-architecture#18).

The other items listed in A-31 (P1-01, P1-02 and P1-07 to P1-15) are still open.
