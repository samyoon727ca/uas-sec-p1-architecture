# 7. Requirements

There are 44 derived "shall" requirements, each closing at least one threat in [§5](05-threat-model.md). They are allocated to four components: CC 15, MSS 13, FC 9 and GCS 7. Verification methods are Test 23, Inspection 13 and Demonstration 8. The evidence is spread across the follow-on repos, with most of it in P3, P4 and P6.

The data lives in [`data/requirements.csv`](../data/requirements.csv), with parent threats in [`data/trace.csv`](../data/trace.csv). Column rules are in [`data/README.md`](../data/README.md).

## 7.1 Conventions

- **One "shall" per requirement, allocated to one component.** The validator enforces both.
- **PX4 parameter values come from the v1.18.0-rc1 source:** `NAV_DLL_ACT`, `COM_DL_LOSS_T`, `EKF2_GPS_CHECK`, `NAV_TRAFF_AVOID` and `UXRCE_DDS_CFG`. They are re-checked when the baseline re-pins to v1.18.0 (DD-06).
- **Values not fixed in P1 are named and handed to the producing repo.** Examples are the allowlist contents (SR-011), the rate limits (SR-012) and the watchdog period (SR-016). P1 fixes what they must achieve.
- **Evidence repos:**
  - P2: verified boot
  - P3: keys, signing and the SITL harness
  - P4: CC image, MSS pipeline and GCS packages
  - P5: hardware assessment
  - P6: configuration and procedure evidence for the RMF package
- **The resiliency technique column** is a first mapping to NIST SP 800-160 Vol. 2 Rev. 1. [§6](06-cyber-resiliency.md) covers that mapping in full.

## 7.2 Requirements and parent threats

Generated from the CSVs by `tools/render_views.py`. CI fails if this view drifts from the data.

<!-- BEGIN GENERATED: requirements-table -->
44 requirements. Evidence: P2 3, P3 13, P4 14, P5 2, P6 12.

| ID | Requirement | Allocated to | Method | Evidence | Parent threats |
|---|---|---|---|---|---|
| SR-001 | The CC shall discard all traffic on its radio interface except WireGuard traffic from the provisioned GCS peer. | CMP-CC | T | P3 | THR-001, THR-006, THR-010, THR-014, THR-042, THR-043, THR-046, THR-048, THR-064, THR-065 |
| SR-002 | The GCS shall discard all traffic on its radio interface except WireGuard traffic from the provisioned CC peer. | CMP-GCS | T | P3 | THR-015, THR-043, THR-045, THR-046, THR-048 |
| SR-003 | The FC shall reject MAVLink messages that are unsigned or not signed with the provisioned key, except HEARTBEAT, RADIO_STATUS, ADSB_VEHICLE and COLLISION. | CMP-FC | D | P3 | THR-042, THR-049, THR-064 |
| SR-004 | The FC shall enter Return mode when no GCS heartbeat has been received for COM_DL_LOSS_T = 10 s (NAV_DLL_ACT = 2). | CMP-FC | T | P3 | THR-009, THR-044 |
| SR-005 | The CC shall boot only boot-chain components signed with the project boot key, verified from a hardware root of trust. | CMP-CC | T | P2 | THR-008, THR-010, THR-032 |
| SR-006 | The CC shall mount its root filesystem read-only with block-level integrity verification. | CMP-CC | T | P4 | THR-008, THR-032 |
| SR-007 | The CC shall install only update images that are signed with the MSS release key and newer than the installed version. | CMP-CC | T | P3 | THR-008, THR-041, THR-059 |
| SR-008 | The CC shall restrict read access to the MAVLink signing key to a single signing service. | CMP-CC | T | P4 | THR-010 |
| SR-009 | The CC shall run the MAVLink router, the command filter and the video pipeline as unprivileged processes confined by a mandatory access control policy. | CMP-CC | T | P4 | THR-010, THR-014, THR-053 |
| SR-010 | The CC shall seal its WireGuard private key and its copy of the signing key to its TPM, bound to the measured boot state. | CMP-CC | T | P2 | THR-007, THR-034, THR-035 |
| SR-011 | The CC shall forward from the GCS tunnel to the FC only messages and commands on the approved allowlist, which excludes SERIAL_CONTROL, FILE_TRANSFER_PROTOCOL, SETUP_SIGNING, RADIO_STATUS, ADSB_VEHICLE and COLLISION. | CMP-CC | T | P4 | THR-003, THR-029, THR-050, THR-051, THR-057 |
| SR-012 | The CC shall rate-limit MAVLink traffic forwarded to the FC to the approved per-message rates. | CMP-CC | T | P4 | THR-005 |
| SR-013 | The CC shall log each command it forwards to the FC with a timestamp and either the sending WireGuard peer or a CC-originated marker. | CMP-CC | T | P4 | THR-004 |
| SR-014 | The CC shall accept only the USB device classes and identifiers on the approved payload list. | CMP-CC | T | P4 | THR-011, THR-053 |
| SR-015 | The CC shall verify the signature of MAVLink frames received from the FC before using them for autonomy decisions. | CMP-CC | T | P3 | THR-052 |
| SR-016 | The CC shall restore C2 forwarding through a hardware watchdog when its C2 services stop responding. | CMP-CC | T | P4 | THR-009 |
| SR-017 | The CC shall encrypt stored mission imagery to a public key whose private key is held only on the MSS. | CMP-CC | D | P3 | THR-036 |
| SR-018 | The FC shall boot only firmware signed with the project firmware key, using PX4 Bootloader Secure Boot. | CMP-FC | T | P2 | THR-030, THR-041, THR-058 |
| SR-019 | The FC shall encrypt flight logs with PX4 log encryption, using a public key whose private key is held only on the MSS. | CMP-FC | D | P3 | THR-028 |
| SR-020 | The FC shall run with the GNSS spoofing and jamming checks enabled (EKF2_GPS_CHECK bits 9 and 11 set). | CMP-FC | I | P6 | THR-012, THR-024, THR-054 |
| SR-021 | The FC shall take no automatic flight action on ADS-B traffic reports (NAV_TRAFF_AVOID = 0 or 1). | CMP-FC | I | P6 | THR-050 |
| SR-022 | The FC shall have only the MAVLink instance for the CC link enabled besides USB, with the uXRCE-DDS client disabled (UXRCE_DDS_CFG = 0). | CMP-FC | I | P6 | THR-002 |
| SR-023 | The FC shall carry tamper-evident seals over its SD-card slot, debug connectors and sensor and actuator wiring that are inspected before each flight. | CMP-FC | I | P5 | THR-013, THR-026, THR-027, THR-049, THR-055, THR-056, THR-065 |
| SR-024 | The FC shall have its SWD/JTAG debug port disabled or physically sealed in the flight configuration. | CMP-FC | T | P5 | THR-030 |
| SR-025 | The GCS shall alert the operator when FC telemetry is unsigned or not signed with the provisioned key. | CMP-GCS | D | P3 | THR-027, THR-045, THR-057 |
| SR-026 | The GCS shall require individual operator authentication to unlock a session. | CMP-GCS | I | P6 | THR-016, THR-018 |
| SR-027 | The GCS shall use full-disk encryption. | CMP-GCS | I | P6 | THR-016, THR-037, THR-038 |
| SR-028 | The GCS shall install only software packages whose signatures verify against the MSS release key. | CMP-GCS | T | P4 | THR-017, THR-019 |
| SR-029 | The GCS shall have no network interface enabled other than the ground-radio link during operations. | CMP-GCS | I | P6 | THR-019 |
| SR-030 | The GCS shall record each sortie's sent and received MAVLink traffic with the operator account that ran it. | CMP-GCS | I | P6 | THR-004, THR-018 |
| SR-031 | The MSS shall build release artifacts only from dependencies pinned by cryptographic hash to approved sources. | CMP-MSS | T | P4 | THR-021, THR-025, THR-063 |
| SR-032 | The MSS shall produce an SBOM and a vulnerability scan for every release artifact, including PX4 firmware. | CMP-MSS | T | P4 | THR-006, THR-063 |
| SR-033 | The MSS shall record build provenance for every release artifact and verify it before loading. | CMP-MSS | T | P4 | THR-021, THR-041, THR-063 |
| SR-034 | The MSS shall hold software signing private keys in a hardware security module that does not export them. | CMP-MSS | D | P3 | THR-020, THR-023, THR-039 |
| SR-035 | The MSS shall keep an encrypted offline backup of each software signing key. | CMP-MSS | D | P3 | THR-040 |
| SR-036 | The MSS shall provision a new MAVLink signing key to the FC, CC and GCS after any loss of physical custody of a key holder. | CMP-MSS | D | P3 | THR-007, THR-016, THR-026, THR-034, THR-037 |
| SR-037 | The MSS shall provision the first signing key on the FC over USB at first power-up, before any other link is connected. | CMP-MSS | D | P3 | THR-057 |
| SR-038 | The MSS shall process offloaded vehicle data in an account that has no access to key material. | CMP-MSS | T | P4 | THR-061, THR-062 |
| SR-039 | The MSS shall log each software load and key-provisioning action with the maintainer's identity. | CMP-MSS | I | P6 | THR-022 |
| SR-040 | The MSS shall require individual maintainer authentication. | CMP-MSS | I | P6 | THR-020, THR-022 |
| SR-041 | The MSS shall record the firmware versions of the GNSS module, ESCs, radios and payload at each maintenance action and compare them with the approved baseline. | CMP-MSS | I | P6 | THR-011, THR-012, THR-013 |
| SR-042 | The MSS shall provision GCS keys over a direct wired connection and never through removable media. | CMP-MSS | I | P6 | THR-060 |
| SR-043 | The MSS shall generate and provision keys only while disconnected from external networks. | CMP-MSS | I | P6 | THR-023, THR-039 |
| SR-044 | The CC shall accept maintenance connections only when authenticated with the MSS maintenance key. | CMP-CC | T | P4 | THR-059 |
<!-- END GENERATED: requirements-table -->
