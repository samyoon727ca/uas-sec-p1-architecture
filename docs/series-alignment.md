# Series alignment: where P4–P7 depart from P1's allocation

**Status: Draft, awaiting owner decision (opened 2026-11-22).**

P1 allocates every verification event (VE) to one follow-on repo. The allocation is the `evidence_repo` column of [`data/verification.csv`](../data/verification.csv), summarised in the [README](../README.md#verification-evidence) table and in [`docs/08-verification-plan.md`](08-verification-plan.md). The standing decision of 2026-11-22 makes P1's series manifest and verification table the source of truth for the series. Several follow-on repos have grown on their own and no longer match that allocation. This memo records each departure and sets out options so the owner can decide. It changes no allocation: nothing in `data/` or `docs/08-verification-plan.md` moves until the owner records a decision below. The recommendations are labelled as such and are not decisions.

Proposal: [samyoon727ca/foreman#29](https://github.com/samyoon727ca/foreman/issues/29).

## Drift table

| P# | Repo | P1 scope and VEs | What the repo actually does | VEs left uncovered |
|---|---|---|---|---|
| P4 | [`uas-sec-p4-cc`](https://github.com/samyoon727ca/uas-sec-p4-cc) | Hardened CC image, MSS pipeline and supply chain. VE-09 (CC image hardening), VE-10 (CC command filter and logging), VE-11 (supply-chain pipeline and package integrity); 14 requirements | Mostly an inline MAVLink allowlist, rate-limit and logging proxy for VE-10 (approved idea #16). VE-09 and VE-11 have one task done each; VE-11 is also proposed in [foreman#15](https://github.com/samyoon727ca/foreman/issues/15) | VE-09, VE-11 (one task done each) |
| P5 | [`uas-sec-p5-fault-sim`](https://github.com/samyoon727ca/uas-sec-p5-fault-sim) | Hardware and firmware security assessment. VE-12 (tamper-evident seal inspection), VE-13 (FC debug port cannot be used); 2 requirements | Emulated fault injection on PX4's secure-boot bootloader (approved idea #18). No VE covers this work | VE-12, VE-13 |
| P6 | [`uas-sec-oscal`](https://github.com/samyoon727ca/uas-sec-oscal) | RMF-as-code (OSCAL): configuration and procedure evidence. VE-14 (FC parameter baseline), VE-15 (GCS configuration), VE-16 (MSS configuration and records); 12 requirements | Pilots OSCAL continuous-ATO evidence on P2's VE-07 / SR-005 (approved idea #7), which overlaps with [P2](https://github.com/samyoon727ca/uas-sec-p2-verified-boot) | VE-14, VE-15, VE-16 |
| P7 | None | No slot: the series ends at P6 | Work with no home in P2–P6, such as fault-injection research and the U-Boot FIT fuzz target (idea #20) | None (no VE allocated) |

**Context, not a departure.** 21 open or recent series tasks name no plan item: P2 3, P3 1, P4 4, P5 8, OSCAL 7. They are untraced work rather than a change of scope, and are listed here so the owner can see the size of the untraced backlog when deciding.

## P4: CC hardening and supply chain

**Departure.** P1 gives P4 three VEs covering 14 requirements. The repo's shipped work is concentrated on VE-10 (the inline MAVLink proxy). VE-09 (SR-006, SR-008, SR-009, SR-014, SR-016, SR-044) and VE-11 (SR-028, SR-031, SR-032, SR-033, SR-038) have one task done each.

**Options.**

- **(a) Re-scope P1.** Keep VE-10 in P4 and move VE-09 and/or VE-11 to another repo (for example VE-11 to the work proposed in foreman#15, or to a new P7).
  - *VE coverage:* VE-10 stays covered by the shipped proxy. VE-09 and VE-11 stay uncovered until the receiving repo produces evidence; the 11 requirements they verify move with them.
  - *Tables:* `evidence_repo` changes for the moved VEs; the README table's P4 row drops to VE-10 (3 requirements) and gains or changes the receiving row; the profile table's P4 description narrows to "CC command filter".
- **(b) Steer P4 back to its P1 scope.** Treat the proxy as complete for VE-10 and direct the next P4 tasks to VE-09 and VE-11.
  - *VE coverage:* All three VEs stay in P4; coverage of VE-09 and VE-11 depends on new P4 tasks. No requirement moves.
  - *Tables:* No change to `data/verification.csv`, the README table or the profile table.
- **(c) Split the repo.** Keep `uas-sec-p4-cc` for the CC (VE-09, VE-10) and create a separate supply-chain repo for VE-11.
  - *VE coverage:* VE-09 and VE-10 stay in P4; VE-11 moves to the new repo and is uncovered until it produces evidence.
  - *Tables:* `evidence_repo` for VE-11 changes; the README and profile tables gain a row for the new repo, and the P4 row drops to VE-09 and VE-10 (9 requirements).

*Recommendation (not a decision):* (b). The P1 scope still fits the repo's name, and the proxy already serves one of its VEs.

**Decision:** Pending owner decision

## P5: hardware and firmware assessment

**Departure.** P1 gives P5 VE-12 (SR-023, seal inspection) and VE-13 (SR-024, FC debug port). The repo does emulated fault injection on PX4's secure-boot bootloader, which no VE covers, so neither allocated VE has work and the repo's work traces to no VE.

**Options.**

- **(a) Re-scope P1.** Add a VE (and, if needed, a requirement traced to a threat) for fault-injection resistance of the FC bootloader, allocate it to P5, and move VE-12 and VE-13 to another repo or to a P7.
  - *VE coverage:* The new VE is covered by P5's work. VE-12 and VE-13 stay uncovered until the receiving repo produces evidence. A new VE also needs its row in `data/verification.csv`, a generated view in `docs/08-verification-plan.md` and the SysML model.
  - *Tables:* The README table's P5 row changes scope to "Fault injection on FC secure boot" with the new VE; VE-12/VE-13 move to the receiving row; the profile table's P5 description changes; the VE count in the README ("17 verification events") changes.
- **(b) Steer P5 back to its P1 scope.** Direct P5 to VE-12 and VE-13 and move the fault-injection work out (for example to a P7).
  - *VE coverage:* VE-12 and VE-13 get an owner with work planned. The fault-injection work stays outside any VE unless (a) or the P7 option adds one.
  - *Tables:* No change in P1; the repo's name (`fault-sim`) no longer fits its scope, so the profile table may need a rename note.
- **(c) Rename or split.** Keep `uas-sec-p5-fault-sim` as a fault-injection repo outside P2–P6 (as P7, or unnumbered research), and create a new P5 repo for VE-12 and VE-13.
  - *VE coverage:* VE-12 and VE-13 stay allocated to P5 and are uncovered until the new repo starts. The fault-injection work has no VE unless one is added.
  - *Tables:* `data/verification.csv` unchanged; the README table's P5 row points at the new repo; the profile table gains a row for the fault-injection repo.

*Recommendation (not a decision):* (c), combined with the P7 decision below. It keeps P1's hardware VEs intact and gives the fault-injection work an honest name.

**Decision:** Pending owner decision

## P6: RMF-as-code (OSCAL)

**Departure.** P1 gives P6 VE-14, VE-15 and VE-16 (configuration inspections of the FC, GCS and MSS, 12 requirements). The repo pilots OSCAL continuous-ATO evidence on P2's VE-07 / SR-005, which P1 allocates to P2. None of P6's own VEs have work.

**Options.**

- **(a) Re-scope P1.** Record the OSCAL pilot as a second evidence path for VE-07 (P2 stays the primary evidence repo), and move VE-14 to VE-16 to another repo or leave them in P6 for later.
  - *VE coverage:* VE-07 unchanged in coverage (P2 still owns its evidence). VE-14 to VE-16 stay uncovered. The validator allows one `evidence_repo` per VE, so a second path is documentation only unless the data model changes.
  - *Tables:* The README table's P6 row adds "OSCAL pilot on VE-07"; the profile table's P6 description changes; `data/verification.csv` changes only if VE-14 to VE-16 move.
- **(b) Steer P6 back to its P1 scope.** Treat the VE-07 pilot as the format proof and apply the same OSCAL evidence pipeline to VE-14, VE-15 and VE-16 next.
  - *VE coverage:* VE-14 to VE-16 stay in P6 and gain planned work; VE-07 stays with P2. No requirement moves.
  - *Tables:* No change to `data/verification.csv`, the README table or the profile table.
- **(c) Rename to match.** Accept that `uas-sec-oscal` is a series-wide evidence-packaging repo (not tied to P6's VEs) and give VE-14 to VE-16 a new P6 repo.
  - *VE coverage:* VE-14 to VE-16 are uncovered until the new repo starts; the OSCAL repo covers no VE of its own.
  - *Tables:* The README table's P6 row points at the new repo; the profile table gains a row for the OSCAL repo as cross-cutting tooling.

*Recommendation (not a decision):* (b). The pilot's tooling applies directly to P6's inspection VEs, so the overlap with P2 can end once it moves to them.

**Decision:** Pending owner decision

## P7: work outside P2–P6

**Departure.** The series has no slot after P6. Some approved or proposed work fits no repo's P1 scope: fault-injection research (see P5) and the U-Boot FIT fuzz target (idea #20).

**Options.**

- **(a) Re-scope P1: add P7.** Add a P7 row with a stated scope (for example "boot-chain robustness: fault injection and fuzzing") and, if the owner wants it traced, new VEs and requirements for it.
  - *VE coverage:* New VEs, if added, are uncovered until P7 produces evidence; existing VEs are unaffected unless the P5 decision moves VE-12/VE-13 there.
  - *Tables:* README intro ("five follow-on repos, P2–P6") and the evidence table gain P7; the profile table gains a P7 row; `data/verification.csv` gains rows only if new VEs are added, and `data/series.csv` must gain a P7 row, since `tools/validate_trace.py` accepts as evidence repos only the p_ids listed there.
- **(b) No P7: fold the work into existing repos.** Put boot-chain fuzzing under P2 (verified boot) and fault injection under P5, with VEs added to those repos if traced.
  - *VE coverage:* Existing allocations unchanged; any new VE is allocated to P2 or P5.
  - *Tables:* No new rows; the P2 and P5 scope descriptions in the README and profile tables widen.
- **(c) No P7: keep the work outside the series.** Treat it as research repos that are not part of P1's verification plan.
  - *VE coverage:* No change; the work contributes no evidence to any VE.
  - *Tables:* No change in P1; the profile table may list the repos separately from the series.

*Recommendation (not a decision):* (a) if the owner wants the fault-injection and fuzzing work to count as evidence; otherwise (c).

**Decision:** Pending owner decision

## Decision log

Record each decision here, then make the allocation change in its own PR. Besides the tables named under each option, any decision that moves a VE between repos also updates `data/series.csv` (the `ve_ids` of the giving and receiving rows, and a new row for any new repo) and the `evidence_repo` of every requirement the moved VE verifies in `data/requirements.csv`; `tools/validate_trace.py` checks both against the VE's `evidence_repo` in `data/verification.csv`.

| Date | Item | Decision | By |
|---|---|---|---|
