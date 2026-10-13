# Audit findings (source of the limitations chapter)

`findings.json` is a byte-for-byte copy of the findings file of the audit of P1 and P2 made on 2026-10-13. The audit's report, experiment scripts and results are held by the owner outside this repository (`_work/audits/2026-10-13/` on the owner's machine). In the findings, `experiments/...` paths are relative to that folder.

| File | SHA-256 |
|---|---|
| `findings.json` (this copy, and the audit's original) | `1d83a4b957b30a2dcf8d5f20358fe797dac54e011c9bec3be171349db53f5dde` |
| The audit's `report.md` (not copied here) | `9afdc98c5aa484469be4466392a1fd75e17148322326d5dbb834f4feb6dcbb04` |

`tools/gen_overview.py` renders the chapter's tables from this file (blocks `audit-summary`, `audit-scale`, `audit-index`, `audit-findings`). The text of each finding goes into the PDF unchanged, apart from whitespace, so the chapter cannot soften or drift from the audit.

When the owner triages a finding, record the outcome in the repo it concerns (P1 or P2) and in a later audit. Do not edit this copy: replace it with that audit's file and update the hashes above.
