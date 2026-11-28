# Owner decisions on P1's open audit items

One section per item that [`triage.md`](triage.md) classes as an owner decision. Each section quotes the fix the audit proposed ([`findings.json`](findings.json)), lists options with what each one touches, and ends with blank **Decision** and **Date** lines for the owner. No option is chosen here, and the order of the options is not a ranking.

When the owner fills in a decision, the change it calls for is made in its own pull request, and the item's row in [`triage.md`](triage.md) is updated when that change lands.

## P1-09: comparing the committed brief PDF with the CI build

**Finding.** A-31, observation: "P1-09: the committed brief PDF is never compared with CI's." A-31's fix: "As proposed on 2026-10-09; each item's fix is in _work/phase12/results/audit-p1.json." That file is not in this repository; the fix implied by the observation is a check that the committed `brief/pdr-brief.pdf` matches what CI builds from `brief/pdr-brief.md`.

**Options.**

- **(a) Compare extracted text.** The `brief` job of `.github/workflows/validate.yml` extracts the text of the committed PDF and of the PDF it builds (for example with `pdftotext`) and fails if they differ.
  - *Touches:* `validate.yml` (brief job), possibly `brief/build.sh`, and the open edge in `docs/GUIDE.md:101`. No requirement or VE.
  - *Consequence:* robust to timestamps and font subsetting; misses changes that are only visual (diagrams, layout).
- **(b) Make the build reproducible and compare bytes or page images.** Pin Chrome and Marp, set `SOURCE_DATE_EPOCH`, then compare the PDFs byte for byte, or compare rendered page images.
  - *Touches:* `validate.yml` (brief job), `brief/build.sh`, `brief/package.json` and `brief/package-lock.json`, and the open edge in `docs/GUIDE.md:101`. No requirement or VE.
  - *Consequence:* catches visual drift too; most effort and the most fragile when a pinned tool changes.
- **(c) Stop committing the PDF.** Remove `brief/pdr-brief.pdf` and link the CI artifact or a release asset instead.
  - *Touches:* `brief/pdr-brief.pdf` (deleted), `README.md:9`, `docs/GUIDE.md` (lines 27, 35, 71 and the open edge at 101), `README.md:138`, `validate.yml` if a release step is added. No requirement or VE.
  - *Consequence:* nothing to drift; the PDF is no longer readable straight from the repo tree.

**Decision:**

**Date:**

## A-02 (P1 part): SR-010's dependency on SR-006

**Finding.** A-02, fix: "After unsealing, extend a policy PCR (for example PCR 9) with a fixed separator, so a second unseal in the same boot fails, and add a test case that checks it. Record in P1 (SR-010 or SR-006 rationale) and in P2 docs/01 §1.5 that SR-010's binding extends past the initramfs only once SR-006 is in place with its root hash carried in the signed FIT or the measured command line."

Only the P1 part is in scope here: recording the dependency in P1. The PCR extend and its test case are P2's.

**Options.**

- **(a) Record the dependency in SR-010's rationale.** As P1 did for SR-018's dependency on SR-024: "SR-010's binding extends past the initramfs only once SR-006 is in place with its root hash carried in the signed FIT or the measured command line."
  - *Touches:* `data/requirements.csv` (SR-010 rationale), the generated views (`tools/render_views.py`) and SysML model (`tools/gen_sysml.py`). Requirements: SR-010. VEs: none change; VE-07 (P2) and VE-09 (P4) keep their criteria.
  - *Consequence:* smallest change; the root-hash condition is stated but not verified by any VE.
- **(b) Strengthen SR-006 and record the dependency in its rationale.** SR-006 requires the root hash to come from the signed FIT or the measured command line; its rationale names SR-010 as depending on it.
  - *Touches:* `data/requirements.csv` (SR-006 statement and rationale), `data/verification.csv` (VE-09 procedure and criteria: a root filesystem with a different root hash must not mount, or must change the measured state), generated views and SysML model. Requirements: SR-006. VEs: VE-09 (P4).
  - *Consequence:* the dependency becomes testable in P4; P4's VE-09 scope grows.
- **(c) Add a requirement for the seam.** A new requirement traced to THR-032: the root hash is carried in the signed or measured boot, verified by VE-07 or VE-09; SR-010's rationale cites it.
  - *Touches:* `data/requirements.csv` (new SR, SR-010 rationale), `data/trace.csv`, `data/verification.csv` (VE-07 or VE-09 `req_ids`, procedure and criteria), generated views and SysML model, the requirement count in `README.md` and the brief. VEs: VE-07 (P2) or VE-09 (P4).
  - *Consequence:* the seam has its own ID and owner; the requirement count changes.

**Decision:**

**Date:**

## A-09: VE-13 passes with a sealed but working debug port

**Finding.** A-09, fix: "Split VE-13's criteria: the pass requires that no debug session can be established in the flight configuration (for example, STM32H7 readout protection at the level that disables debug), and 'sealed' is recorded as a residual risk against SR-018 rather than as a pass."

**Options.**

- **(a) Split VE-13's criteria as the fix says.** Pass only if no debug session can be established in the flight configuration; a sealed but working port is recorded as a residual risk against SR-018.
  - *Touches:* `data/verification.csv` (VE-13 criteria), `data/requirements.csv` (SR-018 rationale for the residual risk), generated views and SysML model. Requirements: SR-018 (rationale). VEs: VE-13 (P5).
  - *Consequence:* VE-13 supports SR-018 as stated; P5 needs hardware with debug disabled (for example readout protection level 2).
- **(b) Also tighten SR-024.** As (a), and change SR-024 from "disabled or physically sealed" to "disabled", with sealing kept as an additional measure.
  - *Touches:* as (a), plus `data/requirements.csv` (SR-024 statement), and the threat rows that cite SR-024 in `docs/05-threat-model.md` if their wording relies on sealing. Requirements: SR-018, SR-024. VEs: VE-13 (P5).
  - *Consequence:* requirement and VE agree; disabling debug on the FC becomes mandatory and may limit field maintenance.
- **(c) Keep VE-13 and weaken SR-018's claim.** Leave VE-13's criteria as they are; SR-018's rationale states that against a captured vehicle (A-08 tier 2) a sealed port only makes a reflash evident.
  - *Touches:* `data/requirements.csv` (SR-018 rationale), possibly the threat rows of the tier-2 firmware threats in `data/threats.csv` and `docs/05-threat-model.md` (residual risk), generated views and SysML model. VEs: none.
  - *Consequence:* no new hardware demand; SR-018 is claimed as detection, not prevention, against tier 2.

**Decision:**

**Date:**

## A-12: A2-01 has no owner or control

**Finding.** A-12, fix: "Give A2-01 an owner (P3 or P4) and a control: the MSS step that HAB-signs u-boot.itb refuses a build whose .config lacks MEASURED_BOOT, verified by a test. Propose the matching P1 requirement or rationale change."

Only the P1 part is in scope here: the requirement or rationale change. A2-01 itself is in P2's `docs/01-scope-and-trace.md`.

**Options.**

- **(a) New MSS requirement, allocated to P3.** "The MSS shall refuse to sign a CC boot image whose build configuration does not enable measured boot", traced to a threat (existing or new) covering a signed U-Boot that does not measure, verified by an added step in VE-06 (or a new VE) in P3.
  - *Touches:* `data/requirements.csv`, `data/trace.csv`, `data/verification.csv` (VE-06 or a new VE), `data/series.csv` if a new VE is allocated, generated views and SysML model, the counts in `README.md` and the brief. VEs: VE-06 (P3) or new.
- **(b) New requirement on the build pipeline, allocated to P4.** The same control placed in the CC image build (P4's supply-chain pipeline), verified in VE-11.
  - *Touches:* as (a), with VE-11 (P4) in place of VE-06.
  - *Consequence:* the check sits where the image is built rather than where it is signed; a build made outside the pipeline is not covered.
- **(c) Rationale change only.** Add to SR-010's (or SR-005's) rationale that SR-010 holds only while every image signed with the CC boot key measures, and name P3 as owner of that condition, with no new requirement or VE.
  - *Touches:* `data/requirements.csv` (rationale), generated views and SysML model. VEs: none.
  - *Consequence:* the dependency is visible but nothing verifies it.

**Decision:**

**Date:**

## A-13: P2's hand-offs to P3 are not recorded in P1

**Finding.** A-13, fix: "Propose a P1 change, as P2 did for changes 1 to 5: record P2's key table in P1 docs/01 §1.3 and add OI2-04 and OI2-05 (and A-01's removal case) as P1 open items owned by P3."

**Options.**

- **(a) Do as the fix says.** Replace the "Software signing keys" row of the key table in `docs/01-system-description.md` §1.3 with P2's five keys (K-CC-ROOT, K-CC-OS, K-CC-POL, K-FC-FW, K-FC-REC) and their custody, drop "Candidate" for PX4 secure boot, and add OI2-04, OI2-05 and A-01's removal case to P1's open items, owned by P3.
  - *Touches:* `docs/01-system-description.md`, `README.md:17-22` (open items), `docs/GUIDE.md` if it lists open items, the brief if it lists them. Requirements: none directly, though OI2-04 bears on SR-034 for K-FC-FW. VEs: none.
- **(b) As (a), and add requirements for the hand-offs.** OI2-04 (PKCS#11 Ed25519 signer, so SR-034 holds for K-FC-FW) and OI2-05 (MSS-authorized epoch commit) become requirements on the MSS, verified by VE-06 or a new VE in P3.
  - *Touches:* as (a), plus `data/requirements.csv`, `data/trace.csv`, `data/verification.csv` (VE-06 or new), generated views and SysML model, counts in `README.md` and the brief. VEs: VE-06 (P3) or new.
- **(c) Reference P2 instead of copying.** The key-table row links to P2's key table at a pinned commit, and the open-items list links to OI2-04 and OI2-05 in P2 with P3 named as owner, without copying their text.
  - *Touches:* `docs/01-system-description.md`, `README.md:17-22`. No requirement or VE.
  - *Consequence:* no duplicated text to drift; P3 still has to follow the link into P2.

**Decision:**

**Date:**

## A-14: No path to put a new key into a fielded CC's TPM

**Finding.** A-14, fix: "Define the provisioning and re-key path, for example an MSS-side duplication of each key to the CC's parent public key followed by TPM2_Import on the CC, so no plaintext key exists on the CC. Assign it (P2 or P3), and add a test case for re-keying under SR-036."

**Options.**

- **(a) Wrapped import, owned by P3.** P1 adds a requirement that the MSS provisions CC keys only wrapped to the CC TPM's parent key (duplication, then TPM2_Import on the CC), traced to the key-exposure threats, and VE-06's procedure and criteria cover re-keying the CC under SR-036.
  - *Touches:* `data/requirements.csv` (new SR; SR-036 and SR-010 rationales), `data/trace.csv`, `data/verification.csv` (VE-06), `docs/01-system-description.md` §1.3 (WireGuard and signing-key provisioning), generated views and SysML model, counts in `README.md` and the brief. VEs: VE-06 (P3).
- **(b) Wrapped import, owned by P2.** The same requirement, verified by VE-07 in P2 (P2 owns the TPM sealing).
  - *Touches:* as (a), with VE-07 (P2) in place of VE-06.
  - *Consequence:* the TPM side is tested where sealing is built; the MSS side of SR-036 is still in P3's VE-06.
- **(c) Re-key by factory reprovisioning.** SR-036's rationale states that the CC is re-keyed by returning it to the factory sealing step, with no field path; the gap is recorded as a residual risk.
  - *Touches:* `data/requirements.csv` (SR-036 rationale), `docs/01-system-description.md` §1.3, possibly `docs/05-threat-model.md` (residual risk of the key-loss threats). No new VE.
  - *Consequence:* no new mechanism; rotation after loss of custody takes the vehicle out of service.

**Decision:**

**Date:**

## A-29: Assumptions have no owner or retiring test

**Finding.** A-29, fix: "Add owner and 'retired by' columns to both tables."

Only P1's table (`docs/03-assumptions.md`) is in scope here.

**Options.**

- **(a) Add both columns to P1's table.** Each of A-01 to A-14 gets an owner (a repo or the owner) and a "retired by" entry (a VE, an open item, or "not retired: accepted").
  - *Touches:* `docs/03-assumptions.md`. Requirements: none. VEs: any VE named as retiring an assumption may need a criterion for it in `data/verification.csv`.
- **(b) Move the assumptions into `data/` with the two columns, checked by `validate_trace.py`.** A new `data/assumptions.csv`, rendered into `docs/03-assumptions.md`; the validator checks that every owner is a known repo and every "retired by" ID exists.
  - *Touches:* new `data/assumptions.csv`, `docs/03-assumptions.md` (generated view), `tools/validate_trace.py`, `tools/render_views.py`, `data/README.md`, tests. VEs: as (a).
  - *Consequence:* the columns cannot drift; more tooling to maintain.
- **(c) Add an owner column only.** "Retired by" is left out; the page says that assumptions are re-examined at each audit.
  - *Touches:* `docs/03-assumptions.md`. No requirement or VE.
  - *Consequence:* someone answers for each assumption, but none has a check.

**Decision:**

**Date:**

## A-30 (with P1-03 and P1-04): P7 is assigned work but not defined

**Finding.** A-30, fix: "As proposed on 2026-10-09: name P7 in P1 with its scope and an owning requirement, or move the fuzzing commitment to P4." A-30 also notes that prior findings P1-03 and P1-04 are still open; their 2026-10-09 text is not in this repository, and A-30 is the record that covers them here.

The P7 question also appears in [`docs/series-alignment.md`](../../docs/series-alignment.md) (section "P7: work outside P2–P6"), which this list does not change.

**Options.**

- **(a) Name P7 in P1.** Add P7 to `data/series.csv` with its scope (fuzzing the CC command filter), add a requirement for the filter's robustness to malformed MAVLink (and, if wanted, the memory-safe-language commitment of DD-04), traced to the filter's threats and verified by a new VE allocated to P7.
  - *Touches:* `data/series.csv`, `data/requirements.csv`, `data/trace.csv`, `data/verification.csv` (new VE), `docs/04-architecture.md` (DD-04), `README.md:5` ("five follow-on repos, P2–P6"), generated views and SysML model, counts in `README.md` and the brief.
- **(b) Move the fuzzing commitment to P4.** DD-04 says "P4 builds and fuzzes it"; a requirement for the filter's robustness (and the memory-safe language, if wanted) is verified by an added fuzzing step in VE-10.
  - *Touches:* `docs/04-architecture.md` (DD-04), `data/requirements.csv`, `data/trace.csv`, `data/verification.csv` (VE-10), generated views and SysML model, counts in `README.md` and the brief. VEs: VE-10 (P4).
  - *Consequence:* the series stays P2–P6; P4's scope grows.
- **(c) Drop the fuzzing commitment.** DD-04 keeps the memory-safe filter and records the parser's attack surface as a residual risk, with no fuzzing owner.
  - *Touches:* `docs/04-architecture.md` (DD-04), possibly `docs/05-threat-model.md` (residual risk). No requirement or VE.
  - *Consequence:* no unowned commitment remains; the filter's parser has no verification beyond VE-10's functional tests.

**Decision:**

**Date:**

## A-32: Verification criteria that cannot fail

**Finding.** A-32, fix: "Give each criterion an observable outcome that can fail (for VE-05, a decryption with the wrong key that must fail; for VE-02, a stated replay result). Split VE-09 per requirement, or record per-requirement results inside it."

The finding also notes that SR-003 (signing) and SR-034 (HSM non-export) are verified by Demonstration only.

**Options.**

- **(a) Rewrite the criteria, keep VE-09 whole.** VE-02 states the post-reboot replay result; VE-05 requires a decryption with the wrong key to fail; VE-06 cites where the first-key order is defined; VE-08 names the firmware key and adds a wrong-key image to the procedure; VE-09 records one result per requirement and gives the watchdog a time bound. SR-003 and SR-034 keep method D.
  - *Touches:* `data/verification.csv` (VE-02, VE-05, VE-06, VE-08, VE-09), `docs/08-verification-plan.md` where its prose describes those VEs (its VE table is a generated view), generated views and SysML model. Requirements: none. VEs: VE-02, VE-05, VE-06 (P3), VE-08 (P2), VE-09 (P4).
  - *Consequence:* VE-02 is partly evidenced by P3 already; its new criterion may need P3 to rerun or add a step.
- **(b) As (a), and split VE-09 per requirement.** VE-09 becomes six VEs, one each for SR-006, SR-008, SR-009, SR-014, SR-016 and SR-044.
  - *Touches:* as (a), plus new VE IDs in `data/verification.csv` and `data/series.csv` (P4's `ve_ids`), the VE count in `README.md`, the brief and `docs/GUIDE.md`.
  - *Consequence:* each result stands alone; the VE count and the series table change.
- **(c) As (a) or (b), and change SR-003 and SR-034 to method T.** Their VEs become tests with failing outcomes (a wrongly signed message rejected; a key export attempt that must fail).
  - *Touches:* as (a) or (b), plus `data/requirements.csv` (verification method of SR-003 and SR-034) and `data/verification.csv`: `validate_trace.py` requires a covering VE with the same method, and VE-02 also covers SR-025 and VE-06 also covers SR-035 to SR-037 (method D), so SR-003 and SR-034 move to test VEs of their own or those VEs are split.
  - *Consequence:* the strongest evidence; VE-02's partial evidence was gathered as a demonstration and may need redoing as a test.

**Decision:**

**Date:**
