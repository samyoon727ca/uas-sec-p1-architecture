<div class="title-page">
<div class="kicker">Notional and unclassified · built from public sources only</div>
<div class="title">Securing a small UAS, from threat model to boot evidence</div>
<div class="subtitle">An overview of the UAS security portfolio for engineers new to secure boot, measured boot and TPMs: the architecture (P1), verified boot, measured boot and key sealing (P2), and the roadmap for P3 to P6</div>
<div class="notice">Numbers and statuses in this document are generated at build time from P1's data at commit <code>{{p1.data_commit}}</code> and from a pinned snapshot of P2 at commit <code>{{p2.commit}}</code>. Nothing here is based on a real program or system. All keys mentioned are development or test keys; no private key appears in either repository.</div>
</div>

# Contents {-}

<!-- toc -->

# About this document {- #about}

This document explains the portfolio from first principles. It is written for an engineer who is new to secure boot, measured boot and Trusted Platform Modules (TPMs) and who must be able to understand the design, check the evidence, and rebuild and rerun the tests.

The portfolio is a set of repositories about one notional small unmanned aircraft system (UAS):

- **P1** defines the system, its threats, its security requirements and the plan for verifying them. It is the anchor for every other repository.
- **P2** produces the evidence for the P1 requirements on verified boot, measured boot and TPM key sealing on the companion computer, and signed firmware on the PX4 flight controller.
- **P3 to P6** are planned. Each owns other P1 requirements; the roadmap chapter lists them. P1 also names a P7, which fuzzes the companion computer's command filter (P1 `docs/04-architecture.md` DD-04); it owns no P1 requirement.

## How to read it {-}

The P1 chapter ([](#p1)) explains the system and why each P2 requirement exists. The P2 chapter ([](#p2)) first explains every concept P2 relies on, each before it is used, then the design, every test case, how to read the evidence, and how to rebuild everything. The roadmap ([](#roadmap)) covers P3 to P6. The next chapter ([](#limitations)) is reserved for limitations and open findings. The appendix ([](#appendix)) holds a glossary and the sources.

If you only want to rebuild and rerun the tests, go to [](#recreate) and look up concepts in [](#concepts) as you meet them.

## Conventions {-}

- **Generated, never retyped.** Every table of requirements, threats, verification events, test cases and evidence runs, and every count or status in the text, is generated when the PDF is built: from P1's `data/*.csv` and from the P2 snapshot in P1's `overview/p2-snapshot/`. That snapshot is a byte-for-byte copy of P2's `data/requirements.csv`, `data/trace.csv`, `data/testcases.csv`, `data/p1/pin.txt` and the `summary.json` of each evidence run the test cases cite, at the P2 commit in `overview/p2-snapshot/pin.txt`. P1's CI checks the copy against P2 with `tools/check_p2_snapshot.py`. A number that is not generated is quoted from a named file at the stated commit.
- **Citations.** "P1 `docs/04-architecture.md` §4.2" means that section of that file in the P1 repository at the commit in the table below; "P2 `tools/predict_pcrs.py`:225" means line 225 of that file in P2 at the snapshot commit. Facts about U-Boot, PX4, NXP and the TCG specifications are cited through the P2 document that checked them, with P2's source tags such as [UBOOT] or [PX4-BL] (P2 `docs/references.md`).
- **Labels.** *Assumption* marks something accepted for analysis but not shown. *Emulated* means a run on QEMU with a software TPM, not on the hardware; what each emulated run stands in for is stated where it appears. *Planned* means a test case has not run.
- **Status words.** A test case runs in CI, on hardware, or both; "–" means it does not run there. P2 rolls test cases up into a status per verification event: *failed* if any run has failed, otherwise *passed* only when every applicable CI and hardware run has passed, *in progress* when some have, *planned* when none have (P2 `tools/render_views.py`, `rollup()`). P1 records an event as passed only when a P1 pull request links the evidence (P2 `docs/06-verification.md` §6.5).
- **Identifiers.** `SR-###` is a P1 security requirement, `SR-###.#` a P2 child requirement, `THR-###` a P1 threat, `VE-##` a P1 verification event, `TC-##` a P2 test case, `DD-##` and `DD2-##` design decisions in P1 and P2, `A-##` and `A2-##` assumptions, `OI-##` and `OI2-##` open items.

## Built from {- #built-from}

<!-- gen: provenance -->

Toolchain that rendered this PDF: <!-- toolchain -->.
