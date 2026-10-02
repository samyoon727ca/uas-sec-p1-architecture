# 6. Cyber resiliency

The design uses 11 of the 14 cyber resiliency techniques in NIST SP 800-160 Vol. 2 Rev. 1, through 16 of its 50 implementation approaches [SP800-160v2]. The weight sits on Substantiated Integrity, Privilege Restriction, Segmentation and Realignment. Together they keep the holders of the shared signing key trustworthy and shrink what can reach them (§5). The most consequential gap is Path Diversity: every C2 path runs through the CC (DD-01), so a CC failure ends C2 and only the failsafe remains (THR-009, OI-03).

## 6.1 Method

- **Names are pinned.** Technique and approach names come from Tables D-2 and D-4 of the publication and are pinned in [`data/catalogs/sp800-160v2r1-approaches.csv`](../data/catalogs/sp800-160v2r1-approaches.csv). The publication states the totals as 14 techniques and 50 approaches, which matches the catalog.
- **Each requirement names its approaches.** The `resiliency_approach` column of [`data/requirements.csv`](../data/requirements.csv) holds one or more `Technique: Approach` pairs, and the validator rejects any pair not in the catalog.
- **The mapping is a project judgment.** It follows the approach definitions and examples in Table D-4. For example, Table D-4 lists "Encrypt data at rest" and "Encrypt transmitted data (e.g., using a Virtual Private Network [VPN])" under Deception: Obfuscation. That is why the tunnel and the at-rest encryption map there.

## 6.2 How the design uses each technique

| Technique | Where it appears in the design | Key requirements |
|---|---|---|
| Substantiated Integrity | Verified boot on the FC (PX4 Bootloader Secure Boot) and the CC; signed, non-rollback updates; MAVLink signing at the FC; build provenance and pinned dependencies | SR-003, SR-005, SR-007, SR-018, SR-031, SR-033 |
| Privilege Restriction | One CC service holds the signing key; parsers run confined; CC keys sealed to the TPM; software signing keys in an HSM; individual operator and maintainer logins | SR-008, SR-009, SR-010, SR-026, SR-034, SR-040 |
| Segmentation | TB-02 separates flight-critical from mission computing (DD-03); the radio interfaces accept only WireGuard (DD-01, DD-02); offloaded data is handled in an account without key access | SR-001, SR-002, SR-009, SR-022, SR-038 |
| Realignment | The allowlist removes shell, file and key-management services from the link (DD-04); uXRCE-DDS and spare MAVLink instances are disabled (DD-03); the debug port is closed; traffic reports trigger no automatic action | SR-011, SR-014, SR-021, SR-022, SR-024 |
| Coordinated Protection | Three complementary C2 layers: WireGuard, the CC allowlist and MAVLink signing (§4.3) | SR-001, SR-002, SR-011 |
| Deception | Obfuscation only: encryption in transit (WireGuard) and at rest (full-disk encryption, log and imagery encryption). Nothing is designed to mislead an adversary | SR-001, SR-017, SR-019, SR-027 |
| Analytic Monitoring | GCS alarm on signing state; GNSS spoofing and jamming alerts; per-peer command log and sortie records | SR-013, SR-020, SR-025, SR-030 |
| Non-Persistence | Read-only root filesystem, and watchdog restarts from a known-good image; key rotation after loss of custody; keys handled offline and never left on removable media | SR-006, SR-016, SR-036, SR-042, SR-043 |
| Adaptive Response | The GCS-loss failsafe switches the vehicle to Return (DD-05) | SR-004 |
| Redundancy | Encrypted offline backup of software signing keys | SR-035 |
| Contextual Awareness | SBOM and vulnerability scan for every release, including PX4 firmware | SR-032 |

## 6.3 Approach coverage

Generated from the CSVs by `tools/render_views.py`. CI fails if this view drifts from the data.

<!-- BEGIN GENERATED: resiliency-approaches -->
11 of 14 techniques and 16 of 50 approaches are used by at least one requirement. Not used: Diversity, Dynamic Positioning, Unpredictability.

| Technique | Approach | Requirements |
|---|---|---|
| Adaptive Response | Dynamic Reconfiguration | SR-004 |
| Analytic Monitoring | Monitoring and Damage Assessment | SR-020, SR-025 |
| Analytic Monitoring | Forensic and Behavioral Analysis | SR-013, SR-030, SR-039 |
| Contextual Awareness | Dynamic Resource Awareness | SR-032 |
| Coordinated Protection | Calibrated Defense-in-Depth | SR-001, SR-002, SR-011 |
| Deception | Obfuscation | SR-001, SR-002, SR-017, SR-019, SR-027 |
| Non-Persistence | Non-Persistent Information | SR-036, SR-042 |
| Non-Persistence | Non-Persistent Services | SR-006, SR-016 |
| Non-Persistence | Non-Persistent Connectivity | SR-043 |
| Privilege Restriction | Trust-Based Privilege Management | SR-008, SR-009, SR-026, SR-037, SR-040, SR-044 |
| Privilege Restriction | Attribute-Based Usage Restriction | SR-010, SR-012, SR-034 |
| Realignment | Restriction | SR-011, SR-014, SR-021, SR-022, SR-024, SR-029 |
| Redundancy | Protected Backup and Restore | SR-035 |
| Segmentation | Predefined Segmentation | SR-001, SR-002, SR-009, SR-022, SR-029, SR-038 |
| Substantiated Integrity | Integrity Checks | SR-003, SR-005, SR-006, SR-007, SR-010, SR-015, SR-018, SR-020, SR-023, SR-041 |
| Substantiated Integrity | Provenance Tracking | SR-007, SR-018, SR-028, SR-031, SR-033 |
<!-- END GENERATED: resiliency-approaches -->

## 6.4 Techniques not used

| Technique | Why it is not used | Consequence |
|---|---|---|
| Diversity | **Path Diversity** ("multiple independent paths for command, control, and communications") is absent. DD-01 routes all C2 through the CC, and A-07 excludes a separate RC link. Design and Supply Chain Diversity would mean duplicate or multi-source FC and CC hardware, which is out of scope for one notional vehicle (A-02) | A CC failure ends all C2 (THR-009). The vehicle relies on the Return failsafe (SR-004). Recorded as OI-03 |
| Dynamic Positioning | Functions are fixed to their hardware on a single vehicle (A-02). There is nothing to relocate or distribute | None identified for this scope |
| Unpredictability | No randomized behavior is specified. Variation in frequency or timing belongs to the radio waveform, which is out of scope (A-12) | Transmissions remain observable (THR-047, accepted) |
