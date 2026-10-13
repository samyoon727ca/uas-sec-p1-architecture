# Limitations and open findings {#limitations}

This chapter reports an independent, adversarial audit of P1 and P2, made on 2026-10-13 at the commits below. It was made by a workstream separate from the one that wrote the rest of this document, and the two did not share drafts until this chapter was written. The findings are reproduced exactly as the audit wrote them. Every table here is generated from a byte-for-byte copy of the audit's `findings.json` (`overview/audit/`), so nothing in this chapter is reworded, shortened or summarized. None of the findings has been triaged or fixed: each stays open until the owner closes it in P1 or P2.

<!-- gen: audit-summary -->

*The audit's baselines and its findings by severity (`overview/audit/findings.json`).*

## What the audit did {#lim-method}

It read both repositories at the commits above. It went through P2 in depth, P1 at the level of scope, purpose and plan quality, and the seam between them. It then tested P2's test cases by mutation: in a WSL Ubuntu 24.04 distro with P2's pinned host packages, it broke one thing at a time and re-ran the harness. Some changes were made consistently in two places, where the question was whether shared constants hide a fault. The things broken were the U-Boot configuration or code, the unseal agent, the MSS policy tool, the provisioning and the harness. A test case that stays green when the property it claims is broken has a gap.

- **VE-07.** 18 experiments, plus a full baseline run of all 31 runs, which passed.
- **TC-11.** 5 experiments on the host checker, with synthetic images, because the PX4 build needs Docker.
- **Validator and evidence.** 4 experiments on P2's validator and secret scan.

The audit also checked the evidence against GitHub: it downloaded each run's artifact and compared it byte for byte with the committed folder, and it compared a local rebuild with CI. And it re-checked the findings of the earlier audit of 2026-10-09.

The audit's full report and its experiment scripts and results are held with the owner for triage, outside this repository. "Evidence" cells that name `experiments/...` refer to that folder. In those cells, **[verified]** means checked by reading code or data or by an experiment, and **[analysis]** means reasoned from a specification or source without a demonstration.

<!-- gen: audit-scale -->

*Severity scale (`overview/audit/findings.json`).*

**What this changes in the rest of this document.** Where a finding narrows what a test case's pass shows, the test case's section in chapter 2 now links to it:
- TC-04: A-06;
- TC-05 and TC-09: A-04, A-10;
- TC-06 and TC-10: A-03;
- TC-07: A-25;
- TC-08: A-01, A-05;
- TC-11: A-11;
- TC-14: A-24.

The concept sections on release policies, the epoch and key release link to A-01, A-02 and A-05. Statements that P2's documents make, and that this document quotes, are left as P2 states them; the findings say where they overstate.

## Index of findings {#lim-index}

<!-- gen: audit-index -->

## Findings {#lim-findings}

<!-- gen: audit-findings -->
