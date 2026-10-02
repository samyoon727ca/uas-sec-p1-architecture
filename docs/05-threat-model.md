# 5. Threat model

The threat model covers every STRIDE element of the architecture: 65 threats on 40 elements. 62 threats are mitigated by derived requirements and 3 are accepted. 41 are rated MI-1, and most of those end the same way: an adversary holds the shared MAVLink signing key, or runs code on a node that holds it. That is the architecture's central weakness (§4.2). It is why the requirements concentrate on the CC (15 of 44) and on keeping code and keys trustworthy (P2, P3, P4).

The data lives in [`data/threats.csv`](../data/threats.csv). Mitigating requirements are in [`data/requirements.csv`](../data/requirements.csv), and the links between them are in [`data/trace.csv`](../data/trace.csv).

## 5.1 Method

**STRIDE per element** over [`data/elements.csv`](../data/elements.csv). Which categories apply to which element type follows Microsoft's STRIDE-per-element chart [STRIDE-MS], and the validator enforces it:

| Element type | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| Process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| External entity | ✓ | | ✓ | | | |
| Data store | | ✓ | | ✓ | ✓ | |
| Data flow | | ✓ | | ✓ | ✓ | |

**Conventions:**
- **Trust boundaries** are not STRIDE elements. Their threats are recorded on the data flows that cross them.
- **Host-to-store access** is implicit (§4.1), so those threats are recorded on the data store.
- **One row per distinct attack.** An element can carry several threats under one category; DF-04 has four tampering threats.
- **No threat recorded.** An element with no meaningful threat carries a written `no_threat_rationale` instead. There are four: EE-OP, EE-MNT, DF-10 and DF-17. Each points to where the related threat is analyzed.

**Adversaries** are the three tiers in A-08: RF-proximate, physical access, and supply chain.

**Mission impact** uses the project scale MI-1 to MI-4 ([`data/README.md`](../data/README.md)). Two points matter when reading the ratings:
- **Consequence only.** The rating is the effect on the mission if the threat is realized. It has no likelihood term.
- **Before mitigation.** It is scored before mitigations are applied.

So a threat that ends with full C2 rates MI-1 however hard it is to carry out. Priority (§5.3) combines the rating with how exposed the path is.

**Framework mapping.** IDs are taken from, and validated against, pinned catalogs ([`data/catalogs/`](../data/catalogs/)):
- **MITRE EMB3D v2.0.2** [EMB3D] for threats to embedded devices and their storage: FC, CC, radios and peripherals. 43 threats carry an EMB3D ID. The GCS and MSS are general-purpose hosts, so EMB3D is not applied to threats against them. Where a device attacks the MSS or must verify its output (THR-041, THR-061, THR-062), the device-side EMB3D threat is cited.
- **MITRE ATT&CK for ICS v19.2** [ATTACK-ICS] where command, control, reporting or the engineering workflow applies. 52 threats carry a technique ID. Revoked IDs are not used: T0855 and T0856 are now T1692.001 and T1692.002, and T0839 and T0857 are now T1693.002 and T1693.001.
- **No mapping:** 8 threats have no good fit in either framework. They are:
  - the attribution threats THR-004, THR-018 and THR-022;
  - GNSS spoofing and jamming (THR-024, THR-054); neither framework covers attacks on satellite navigation signals;
  - unauthorized MSS use (THR-020), signing-key loss (THR-040) and keys left on removable media (THR-060).

  Their fields are left blank rather than forced.

**Disposition.** `mitigate` means at least one requirement traces to the threat. `accept` needs a written rationale. Residual risk after mitigation is stated in the threat description where it matters.

## 5.2 STRIDE coverage

Generated from the CSVs by `tools/render_views.py`. CI fails if this view drifts from the data.

<!-- BEGIN GENERATED: threat-matrix -->
65 threats on 40 STRIDE elements: 41 MI-1, 16 MI-2, 6 MI-3, 2 MI-4; 62 mitigated, 3 accepted.

Blank: applicable, no threat recorded. –: category does not apply to the element type.

| Element | Type | S | T | R | I | D | E |
|---|---|---|---|---|---|---|---|
| CMP-FC Flight controller | Process | THR-002, THR-064 | THR-003 | THR-004 |  | THR-005 | THR-006 |
| CMP-CC Companion computer | Process | THR-007 | THR-008 |  |  | THR-009 | THR-010 |
| CMP-PL EO payload | Process |  | THR-011 |  |  |  |  |
| CMP-NAV GNSS and compass module | Process |  | THR-012 |  |  |  |  |
| CMP-ACT ESCs and motors | Process |  | THR-013 |  |  |  |  |
| CMP-RAD-A Air data-link radio | Process |  |  |  |  |  | THR-014 |
| CMP-RAD-G Ground data-link radio | Process |  |  |  |  |  | THR-015 |
| CMP-GCS Ground control station | Process | THR-001, THR-016 | THR-017 | THR-018 |  |  | THR-019 |
| CMP-MSS Maintenance and support station | Process | THR-020 | THR-021 | THR-022 |  |  | THR-023 |
| EE-OP Operator (rationale) | External entity |  | – |  | – | – | – |
| EE-MNT Maintainer (rationale) | External entity |  | – |  | – | – | – |
| EE-GNSS GNSS signals | External entity | THR-024 | – |  | – | – | – |
| EE-UPSTREAM Upstream software sources | External entity | THR-025 | – |  | – | – | – |
| DS-FC-KEY FC MAVLink signing key file | Data store | – | THR-027 | – | THR-026 |  | – |
| DS-FC-LOG FC flight logs | Data store | – | THR-029 | – | THR-028 |  | – |
| DS-FC-FW FC firmware and parameters | Data store | – | THR-030 | – | THR-031 |  | – |
| DS-CC-SYS CC system image and configuration | Data store | – | THR-032 | – | THR-033 |  | – |
| DS-CC-CRED CC credentials | Data store | – | THR-035 | – | THR-034 |  | – |
| DS-CC-DATA CC mission data | Data store | – |  | – | THR-036 |  | – |
| DS-GCS-CRED GCS credentials | Data store | – |  | – | THR-037 |  | – |
| DS-GCS-DATA GCS mission data | Data store | – |  | – | THR-038 |  | – |
| DS-MSS-KEYS MSS key material | Data store | – |  | – | THR-039 | THR-040 | – |
| DS-MSS-ART MSS release artifacts | Data store | – | THR-041 | – |  |  | – |
| DF-01 C2 uplink | Data flow | – | THR-042 | – | THR-043 | THR-044 | – |
| DF-02 Telemetry downlink | Data flow | – | THR-045 | – | THR-046, THR-047 |  | – |
| DF-03 Video downlink | Data flow | – |  | – | THR-048 |  | – |
| DF-04 CC to FC commands | Data flow | – | THR-049, THR-050, THR-051, THR-065 | – |  |  | – |
| DF-05 FC to CC telemetry | Data flow | – | THR-052 | – |  |  | – |
| DF-06 Payload imagery | Data flow | – | THR-053 | – |  |  | – |
| DF-07 GNSS signals | Data flow | – |  | – |  | THR-054 | – |
| DF-08 Navigation data | Data flow | – | THR-055 | – |  |  | – |
| DF-09 Actuator commands | Data flow | – | THR-056 | – |  |  | – |
| DF-10 Operator input (rationale) | Data flow | – |  | – |  |  | – |
| DF-11 FC maintenance load | Data flow | – | THR-057, THR-058 | – |  |  | – |
| DF-12 CC maintenance load | Data flow | – | THR-059 | – |  |  | – |
| DF-13 GCS provisioning | Data flow | – |  | – | THR-060 |  | – |
| DF-14 CC data offload | Data flow | – | THR-061 | – |  |  | – |
| DF-15 FC log offload | Data flow | – | THR-062 | – |  |  | – |
| DF-16 Upstream software intake | Data flow | – | THR-063 | – |  |  | – |
| DF-17 Maintainer actions (rationale) | Data flow | – |  | – |  |  | – |
<!-- END GENERATED: threat-matrix -->

## 5.3 Priority threats

These are ranked by mission impact and by how reachable the path is for the A-08 adversary tiers.

| Threat | Impact | Mitigated by | Evidence | Residual |
|---|---|---|---|---|
| **THR-010** Code execution on the CC yields full vehicle C2 | MI-1 | SR-001 (only WireGuard on the radio side), SR-005 (verified boot), SR-008 (one service holds the key), SR-009 (confined parsers) | P2, P3, P4 | A full CC compromise still yields C2. PX4 signing has no per-node keys |
| **THR-001** Spoofed GCS heartbeats suppress the data-link-loss failsafe | MI-1 | SR-001 | P3 (VE-01) | A compromised CC or GCS |
| **THR-026, THR-027** Signing key read, replaced or deleted on the FC's SD card | MI-1 | SR-023 (seals, pre-flight inspection), SR-036 (rotate after loss of custody), SR-025 (GCS alarm on signing state) | P5, P3 | Seals detect access; they don't prevent it |
| **THR-057** Unauthorized peer installs the first signing key | MI-2 | SR-037 (first key over USB at first power-up), SR-011 (CC drops `SETUP_SIGNING` from the tunnel), SR-025 | P3, P4 | A window remains if procedure SR-037 is skipped |
| **THR-021, THR-063** Malicious code enters signed artifacts through the build or upstream | MI-1 | SR-031 (hash-pinned deps), SR-032 (SBOM and scan), SR-033 (provenance) | P4 | Malicious changes that pass review upstream |
| **THR-016, THR-019** GCS stolen, or compromised through unrelated use | MI-1 | SR-026, SR-027, SR-028, SR-029 | P4, P6 | A key holder lives on a laptop |
| **THR-002** Commands reach the FC outside the C2 path (uXRCE-DDS, spare MAVLink instance) | MI-1 | SR-022 | P6 | None identified while the configuration holds |
| **THR-024** GNSS spoofing diverts the vehicle | MI-1 | SR-020 (spoofing and jamming checks on) | P6 | Spoofing the receiver does not report |

## 5.4 Accepted risks

| Threat | Impact | Rationale |
|---|---|---|
| THR-031 Firmware and parameters extracted from a captured FC | MI-4 | PX4 is open source and the parameter baseline is published in P1. The only secret on the FC is the signing key (THR-026) |
| THR-033 CC system image read from a captured vehicle | MI-4 | The image holds open-source software and documented configuration. Credentials are kept separately (THR-034) |
| THR-047 RF emissions reveal vehicle and GCS locations | MI-2 | WireGuard hides content, not the existence or direction of transmissions. Emission control belongs to the waveform and EW (A-12) |

## 5.5 System-level residual risk

- **Shared signing key.** Mitigations make a key-holder compromise less likely and more evident (SR-013, SR-025). They don't change its consequence, because MAVLink signing in PX4 has one key for all nodes. A design that authenticates each node to the FC would need a change outside PX4's current signing. That is recorded as an open question for P3.
- **RF jamming** cannot be prevented within scope. SR-004 bounds its effect to a Return.
- **GNSS spoofing that the receiver does not report** is not detected.
- **PX4's signing implementation is unaudited** (THR-064). Post-reboot replay (THR-065) rests on an assumption that VE-02 will confirm or retire.
- **Physical tampering** is detected (SR-023), not prevented. This follows the generic anti-tamper scope.
- **Hardware supply-chain insertion before receipt** that leaves reported firmware versions unchanged (THR-012, THR-013).
