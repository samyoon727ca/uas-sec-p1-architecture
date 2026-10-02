# Pinned framework catalogs

`tools/validate_trace.py` checks every EMB3D and ATT&CK for ICS ID in `threats.csv`, and every resiliency approach in `requirements.csv`, against these files. An entry that is well-formed but missing from the pinned version fails the build.

| File | Source | Pinned at | Extraction |
|---|---|---|---|
| `emb3d-v2.0.2.csv` | [mitre/emb3d](https://github.com/mitre/emb3d) `_data/threats.json` | Commit `0d7c25bb4e2928c516fb5811aaab9ff8bab2896c` (site version 2.0.2, June 1, 2026) | All 81 threats: `id`, `text` as name, `category` |
| `sp800-160v2r1-approaches.csv` | [NIST SP 800-160 Vol. 2 Rev. 1](https://doi.org/10.6028/NIST.SP.800-160v2r1), Table D-4 (December 2021) | Rev. 1 | All 14 techniques and 50 implementation approaches; the publication states both totals. `id` is `Technique: Approach` |
| `attack-ics-v19.2.csv` | [mitre-attack/attack-stix-data](https://github.com/mitre-attack/attack-stix-data) `ics-attack/ics-attack-19.2.json` | Tag `v19.2` (commit `6cda5ad8462c79e14fbb872f4e09059b18e0cfc4`) | All 97 `attack-pattern` objects that are neither revoked nor deprecated: ATT&CK ID, name, tactics |

Revoked ATT&CK for ICS IDs are excluded on purpose. For example, T0855 and T0856 were revoked in favor of T1692.001 and T1692.002, and using them fails validation.

To update a catalog, regenerate it from the new source version, change the version in its file name and in [`docs/references.md`](../../docs/references.md), and re-check every mapped ID.
