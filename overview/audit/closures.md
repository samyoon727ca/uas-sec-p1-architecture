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

## 2026-11-28: P1-02 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-02: README.md:76-87 attributes drift and SysML checks to validate_trace.py."
- **What changed.** The "Verification evidence" section of the top-level [`README.md`](../../README.md) now names the tool that runs each check. The trace, count and priority-table rules stay under `tools/validate_trace.py`. A second list, "The other checks", names `tools/check_series_status.py`, `tools/render_views.py --check` (doc-view drift), `tools/gen_sysml.py --check` (SysML model drift), `tools/sysml/validate.sh` (SysML validation on the OMG Pilot Implementation), `tools/check_p2_snapshot.py`, `brief/build.sh` with the `brief/assets/*.mmd` diff step after it, `overview/build.sh` and the unit tests, each with the condition it fails on. `docs/GUIDE.md` ("What's verified") now says the trace-rule tests cover the `validate_trace.py` rules of that section.
- **Check.** `tests/test_docs_consistency.py` (`VerificationEvidenceTest`) collects every `python tools/*.py` command and every `.sh` script (`tools/sysml/validate.sh`, `brief/build.sh`, `overview/build.sh`) that a step of `.github/workflows/validate.yml` runs, and fails if one is not named in the README's "Verification evidence" section (the generated series table excluded). It also fails if a `tools/*.py` or `.sh` script named in that section is not run by the workflow, so a stale tool name cannot stay.
- **Change.** The pull request that closes issue #45 (samyoon727ca/uas-sec-p1-architecture#45).

## 2026-11-28: P1-13 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-13: data/README.md omits gen_sysml.py."
- **What changed.** [`data/README.md`](../../data/README.md) has a new section, "Tools that read this folder", naming the six tools that read `data/`: `validate_trace.py`, `render_views.py`, `gen_sysml.py`, `check_series_status.py`, `fetch_series_status.py` and `gen_overview.py`. Its "Running locally" block now includes `python tools/gen_sysml.py`.
- **Check.** `tests/test_docs_consistency.py` (`DataReadmeTest`) fails if a tool in its fixed list of data readers is not named in `data/README.md`, and if a `tools/*.py` that builds a path under `data/` (`/ "data"`) or holds a `"data"` or `"data/..."` string literal is missing from that list.
- **Change.** The pull request that closes issue #45 (samyoon727ca/uas-sec-p1-architecture#45).

## 2026-11-28: P1-14 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-14: model/sysml/README.md:30 'Java 21 only'."
- **What changed.** [`model/sysml/README.md`](../../model/sysml/README.md) ("Tooling: OMG Pilot Implementation, run headless") now reads "Java 21: CI runs Temurin 21 (`java-version` in `.github/workflows/validate.yml`), and other versions are untested." The README's "Run the checks locally" block, the same block in `docs/GUIDE.md` ("Run it and test it") and the header comment of `tools/sysml/validate.sh` said "Java 21+"; they now say Java 21, matching what CI runs. The workflow is unchanged; pinning a full Java version is P1-10.
- **Check.** `tests/test_docs_consistency.py` (`JavaVersionTest`) reads the major version from `java-version` in `validate.yml` and fails if any "Java N" in `model/sysml/README.md`, `README.md` or `docs/GUIDE.md` names another version or adds "+", "or later" or "only".
- **Change.** The pull request that closes issue #45 (samyoon727ca/uas-sec-p1-architecture#45).

## 2026-11-28: P1-15 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-15: README.md:15 'Closed by VE-02' under 'Still open'."
- **What changed.** In the top-level [`README.md`](../../README.md), OI-01 in the "Still open" list (at the top of the README, before "Threat") now reads "To be closed by VE-02 in P3 (partly evidenced; its QGroundControl steps wait on uas-sec-p3-pki#6)". The "Design" section said the same ("closed by VE-02") and now says "to be closed by VE-02, which is partly evidenced; its QGroundControl steps wait on uas-sec-p3-pki#6". The overview's P1 chapter ([`overview/src/p1.md`](../src/p1.md), item 3 of its list of command-protection layers) said "closed by verification event VE-02 in P3" and now says "to be closed by verification event VE-02 in P3, which is partly evidenced; its QGroundControl steps wait on uas-sec-p3-pki#6". This change does not rebuild the PDF, so the committed [`overview/overview.pdf`](../overview.pdf) still has the old wording until it is next rebuilt (`overview/build.sh`; the `overview` job of `validate.yml` builds it on every push). `data/verification.csv` is unchanged: VE-02 stays `partly evidenced`.
- **Check.** `tests/test_docs_consistency.py` (`StillOpenTest`) fails if any bullet of the README's "Still open" list contains "closed by" in any letter case (so "Closed by" and "closed by" both fail) other than as "to be closed by", or if the list is not found.
- **Change.** The pull request that closes issue #45 (samyoon727ca/uas-sec-p1-architecture#45).

## 2026-11-28: P1-12 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-12: docs/references.md:32-42 rows without versions."
- **What changed.** Every row of the Sources table in [`docs/references.md`](../../docs/references.md) now pins a version a reader can retrieve, taken as it stood on the access date, 2026-10-02. Each pin was looked up with `git ls-remote` and a treeless clone of the source repository, or from the Wayback Machine when the source has no repository:
  - PX4-SIGN, PX4-HARD (which said "Same"), PX4-1.18 ("Beta at time of access") and PX4-1.17 ("Stable"): PX4-Autopilot `main` at commit `b12d17f6`, the head of `main` at the end of 2026-10-02, where the docs live under `docs/en/`. Only the v1.18 release notes changed on `main` that day, in the serial-passthrough item, which P1 does not cite. PX4-SIGN said its `main` doc "matches the doc at tag `v1.18.0-rc1`". It does not: the `main` doc adds text on the shared key and on forwarding. The cell now says that the key storage, provisioning, allowlist and armed-guard text P1 uses is also in `v1.18.0-rc1`. The PX4-HARD cell notes that the audit-status line P1 quotes is not in `v1.18.0-rc1`.
  - MAV-SIGN ("Current"): mavlink-devguide commit `7412790c`, the head of `master` on 2026-10-02.
  - MAVROUTER ("`master` at access"): mavlink-router commit `2362c620`, the head of `master` on 2026-10-02. "Version pinned in P4" is kept.
  - WG ("Current"): the page has no version or repository, so the pin is the access date with the Wayback Machine snapshot `20260926112636`, whose text is the same as the page on 2026-11-28.
  - CMVP-140C ("Current list"): the page as updated 2026-08-21, whose latest change-log entry is 2026-06-22, with the Wayback Machine snapshot `20261001210954`. That snapshot, like the page on 2026-11-28, lists AES-GCM and SHA-2/SHA-3 and no ChaCha20, Poly1305 or BLAKE2.

  No "Used for" cell changed: the pinned version of each source agrees with it, so no conflict was added to [`owner-decisions.md`](owner-decisions.md). Which sources are cited, and their links, are unchanged.
- **Check.** `tests/test_docs_consistency.py` (`ReferencesPinTest`) parses the Sources table and fails if any "Version pinned" cell has no version-like token (a tag such as `v1.2.3`, a commit of 7 or more hex digits, a year, or "Rev."), consists only of words such as Current, Stable, Same, `master` or `main`, or starts with "Same". It is run by the `traceability` job of `validate.yml`.
- **Change.** The pull request that closes issue #46 (samyoon727ca/uas-sec-p1-architecture#46).

## 2026-11-28: P1-10 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-10: python, java and node float by major version in validate.yml."
- **What changed.** Every setup-* action in both workflows now runs an exact release. In [`.github/workflows/validate.yml`](../../.github/workflows/validate.yml), `python-version` is `"3.12.16"` (lines 23 and 101, was `"3.12"`), `java-version` is `"21.0.13"` (Temurin, line 52, was `"21"`) and `node-version` is `"22.23.5"` (lines 73 and 106, was `"22"`). [`.github/workflows/series-status.yml`](../../.github/workflows/series-status.yml) floated Python the same way and now also runs `"3.12.16"` (line 36). Each was the newest release in its line on 2026-11-28 that the action can install on `ubuntu-24.04`: the `actions/python-versions` and `actions/node-versions` manifests, and the Adoptium API for Temurin. A comment above each pin says where to find a newer patch release to bump to. The action SHA pins are unchanged.
- **Check.** `tests/test_docs_consistency.py` (`ToolchainPinTest`) reads every `*-version` input in both workflows and fails if one is not a full `X.Y.Z` version, so a bare major (`"21"`), a major.minor (`"3.12"`), a wildcard (`"3.12.x"`) or an alias (`lts/*`) fails the build. It also fails if `python-version`, `java-version` or `node-version` is no longer found. It is run by the `traceability` job of `validate.yml`.
- **Change.** The pull request that closes issue #47 (samyoon727ca/uas-sec-p1-architecture#47).

## 2026-11-28: P1-11 (cited by audit finding A-31)

- **Original finding.** A-31, observation: "P1-11: brief/package-lock.json:1256-1258 pins deprecated @xmldom/xmldom 0.9.10."
- **What changed.** `speech-rule-engine` 4.1.4 (through `mathjax-full` 3.2.2, `@marp-team/marp-core` 4.4.0 and `@marp-team/marp-cli` 4.5.1) requires exactly `@xmldom/xmldom` 0.9.10, so [`brief/package.json`](../../brief/package.json) now has an `overrides` entry that sets it to 0.9.12. On 2026-11-28, 0.9.12 was the `latest` release and the only 0.9.x release npm did not mark deprecated: 0.9.0 to 0.9.11 all carry "this version has critical issues, please update to the latest version". `npm install` in `brief/` regenerated [`brief/package-lock.json`](../../brief/package-lock.json); the only change is the `node_modules/@xmldom/xmldom` entry (line 1256), now 0.9.12 with no `deprecated` field. No other package moved. `npm ci` and `brief/build.sh` ran on the machine that made the change and built the PDF; the `brief` job of `validate.yml` is the proof on CI's toolchain. `overview/package-lock.json` does not contain `@xmldom/xmldom`, so it is unchanged. One deprecated package remains in `brief/package-lock.json`: `mathjax-full` 3.2.2 ("Version 4 replaces this package with the scoped package @mathjax/src"), which Marp requires; replacing it means moving Marp, which this change leaves out. For that reason the check is a unit test with a listed exception, not the `npm warn deprecated` step [`triage.md`](triage.md) proposed, which would fail on `mathjax-full`.
- **Check.** `tests/test_docs_consistency.py` (`LockfileDeprecationTest`) fails if any package in `brief/package-lock.json` or `overview/package-lock.json` is marked `deprecated`, other than those listed with a reason in `DEPRECATED_ALLOWED` (only `mathjax-full` in `brief/`), and if a listed exception is no longer in its lockfile. It also checks directly that the `@xmldom/xmldom` entry in `brief/package-lock.json` is not deprecated. It is run by the `traceability` job of `validate.yml`.
- **Change.** The pull request that closes issue #47 (samyoon727ca/uas-sec-p1-architecture#47).

## 2026-11-28: A-33

- **Original finding.** A-33, "P1 has no .gitattributes; Windows checkouts get CRLF", observation: "P1 has no .gitattributes. On this machine (core.autocrlf=true), git archive and checkouts write CRLF, and P1's own render_views.py writes CRLF on Windows. P2 fixed the same problem for itself (P2-12)." Fix: "Add '* text=auto eol=lf' as P2 did."
- **What changed.** [`.gitattributes`](../../.gitattributes), which already set `-text` for `overview/p2-snapshot/**` and `overview/audit/**` and `binary` for `*.pdf`, now starts with `* text=auto eol=lf`. Because it is the first rule, the later `-text` and `binary` rules still override it, so the P2 snapshot, the audit files and the PDFs keep their exact bytes. Checkouts and `git archive` now write LF for every text file, whatever `core.autocrlf` says. `git add --renormalize .` changed no file: every blob in the index was already LF (`git ls-files --eol` lists 95 `i/lf` and 4 `i/-text` files, none `i/crlf`). `tools/render_views.py` is unchanged and still writes the platform's line ending on Windows, but with this rule git converts those files to LF when they are added, and `render_views.py --check` reads them with universal newlines, so neither the committed files nor the check depend on the platform.
- **Check.** `tests/test_docs_consistency.py` (`GitattributesTest`) fails if the first rule of `.gitattributes` is not `* text=auto eol=lf` or if `*.pdf binary` is missing. It is run by the `traceability` job of `validate.yml`.
- **Change.** The pull request that closes issue #47 (samyoon727ca/uas-sec-p1-architecture#47).

The open status of every other P1 audit item is tracked in [`triage.md`](triage.md).
