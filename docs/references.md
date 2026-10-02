# References

Every external source used in P1, with the version pinned and the date it was accessed. Framework IDs (EMB3D, ATT&CK for ICS) are valid only against the versions listed here. All sources were accessed 2026-10-02.

## PX4 signing version history

**Baseline: PX4 v1.18** (DD-06, approved). Analysis uses tag `v1.18.0-rc1`, to be re-pinned to `v1.18.0` when it is released.

PX4's own docs say: "The signing protocol was audited when it was drafted, but PX4's implementation of it has not been." [PX4-HARD]. P1 treats PX4 signing as an unaudited control.

| When | Where | Signing behavior |
|---|---|---|
| Tag `v1.17.0` (commit dated 2026-01-16) and `release/1.17` head (2026-08-06) | Stable v1.17 | **No signing code.** All 135 files under `src/modules/mavlink` were searched. There are no v1.17.x patch tags |
| 2026-03-09, PR #25284 | `main` only; never in a tagged release | First implementation. Enabled by the non-standard `MAV_SIGN_CFG` parameter (0 off, 1 all links except USB, 2 all links). `SETUP_SIGNING` accepted **only over USB** [PX4-PR25284] |
| 2026-04-12, PR #26894 | `main`; every v1.18 tag from `v1.18.0-alpha1` (2026-05-13) | Spec-compliant. Active whenever a key file exists. `MAV_SIGN_CFG` removed. `SETUP_SIGNING` accepted **on any link**, rejected while armed, with the first key accepted unsigned [PX4-PR26894], [PX4-1.18] |

The provisioning-window threat (§4.2, item 5) comes from the last row. Under the earlier implementation, installing a key required physical USB access. Under v1.18, any peer that reaches any FC link can install the first key.

**Inconsistent sources.** Three PX4 sources suggest signing is available in v1.17; the tagged source contradicts all three:
- PX4's v1.17 release announcement recommends enabling message signing and links to the `main` docs [PX4-BLOG-1.17].
- The v1.18 release notes say "If you used signing in v1.17, re-provision the key" [PX4-1.18].
- The hardening page carries a "PX4 v1.17" badge.

P1 relies on the tagged source.

## Sources

| Tag | Source | Version pinned | Used for |
|---|---|---|---|
| [PX4-SIGN] | [PX4 Guide: MAVLink Message Signing](https://docs.px4.io/main/en/mavlink/message_signing) | `main` docs; matches the doc at tag `v1.18.0-rc1` | Key storage, provisioning, unsigned allowlist, armed guard (§4.2) |
| [PX4-HARD] | [PX4 Guide: MAVLink Security Hardening](https://docs.px4.io/main/en/mavlink/security_hardening) | Same | Shared key on all GCS and CC nodes, enforcement on all links, capabilities at risk, audit status |
| [PX4-1.18] | [PX4 v1.18 release notes](https://docs.px4.io/main/en/releases/1.18) | Beta at time of access | Signing made spec-compliant; SBOM generation |
| [PX4-1.17] | [PX4 v1.17 release notes](https://docs.px4.io/main/en/releases/1.17) | Stable | MAVLink FTP path-traversal and session-validation hardening (THR-006) |
| [PX4-SRC] | PX4-Autopilot source at tags `v1.17.0` and `v1.18.0-rc1`: [`mavlink_sign_control.cpp`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/mavlink/mavlink_sign_control.cpp), [`mavlink_receiver.cpp`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/mavlink/mavlink_receiver.cpp), [`commander_params.yaml`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/commander/commander_params.yaml), [`fmu-v6x rc.board_defaults`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/boards/px4/fmu-v6x/init/rc.board_defaults), [`generate_config.py`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/Tools/serial/generate_config.py) | `v1.17.0`, `v1.18.0-rc1` | Signing absent in v1.17.0; GCS liveness from `MAV_TYPE_GCS` heartbeats; `NAV_DLL_ACT` default 0 (Disabled) and `COM_DL_LOSS_T` default 10 s; FMUv6X default MAVLink-over-Ethernet instance; serial config value 0 = disabled. Threat model, all checked in `v1.18.0-rc1`: `EKF2_GPS_CHECK` default 2047 (bit 9 spoofing on, bit 11 jamming off; `ekf2/params_gnss.yaml`); spoofing and jamming always raise alerts (`estimatorCheck.cpp`) and fail the GNSS checks only when their mask bits are set (`gnss_checks.cpp`); `COM_POS_LOW_ACT` default 3 (Return), mission and loiter modes only; `NAV_TRAFF_AVOID` default 1 (Warn only; `navigator_params.yaml`); `RADIO_STATUS` with a low TX buffer cuts the stream rate by 20% per message, to 1% (`Mavlink::update_radio_status`); no receive handler for `COLLISION` in `mavlink_receiver.cpp`; key path under `CONFIG_BOARD_ROOT_PATH` (`mavlink_sign_control.h`) |
| [PX4-PR25284] | [PX4-Autopilot PR #25284](https://github.com/PX4/PX4-Autopilot/pull/25284) and its [signing doc revision](https://github.com/PX4/PX4-Autopilot/blob/358574f9f6e006a7a18ecbd3015abddfa004788b/docs/en/mavlink/message_signing.md) | Commit `358574f9` | First implementation: `MAV_SIGN_CFG` modes, USB-only `SETUP_SIGNING` |
| [PX4-PR26894] | [PX4-Autopilot PR #26894](https://github.com/PX4/PX4-Autopilot/pull/26894) | Commit `62b3c9a0` | Spec-compliant change; `MAV_SIGN_CFG` removed |
| [PX4-BLOG-1.17] | [PX4 Autopilot Release v1.17: What You Need To Know](https://px4.io/px4-autopilot-release-v1-17-what-you-need-to-know/) | Posted 2026-05-18 | Recommends enabling signing; links to `main` docs |
| [MAV-SIGN] | [MAVLink Developer Guide: Message Signing](https://mavlink.io/en/guide/message_signing.html) | Current | 32-byte key; 48-bit SHA-256-based signature; timestamps and link IDs; no encryption |
| [QGC] | [QGroundControl `src/MAVLink/Signing`](https://github.com/mavlink/qgroundcontrol/tree/v5.1.5/src/MAVLink/Signing) | `v5.1.5` | GCS-side signing implementation exists |
| [MAVROUTER] | [mavlink-router sample configuration](https://github.com/mavlink-router/mavlink-router/blob/master/examples/config.sample) | `master` at access; version pinned in P4 | Filters available per endpoint: `AllowMsgIdIn/Out`, `BlockMsgIdIn/Out`, `AllowSrcSysIn/Out`, `AllowSrcCompIn/Out` (and their `Block*` forms). No command-ID filter |
| [WG] | [WireGuard protocol](https://www.wireguard.com/protocol/) | Current | Curve25519, ChaCha20-Poly1305, BLAKE2s, HKDF; no cipher agility |
| [CMVP-140C] | [CMVP-approved security functions (SP 800-140C supplemental list)](https://csrc.nist.gov/projects/cryptographic-module-validation-program/sp-800-140-series-supplemental-information/sp800-140c), per [NIST SP 800-140C Rev. 2](https://doi.org/10.6028/NIST.SP.800-140Cr2) | Current list | Lists AES (including GCM per SP 800-38D) and SHA-2/SHA-3. ChaCha20, Poly1305 and BLAKE2 do not appear (DD-02 trade note) |
| [EMB3D] | [MITRE EMB3D](https://emb3d.mitre.org/) | v2.0.2; catalog from [mitre/emb3d](https://github.com/mitre/emb3d) commit `0d7c25bb` | Device-level threat IDs (`TID-###`); 81 threats pinned in [`data/catalogs/emb3d-v2.0.2.csv`](../data/catalogs/emb3d-v2.0.2.csv) |
| [ATTACK-ICS] | [MITRE ATT&CK for ICS](https://attack.mitre.org/matrices/ics/) | ATT&CK content v19.2; catalog from [attack-stix-data](https://github.com/mitre-attack/attack-stix-data) tag `v19.2` | Technique IDs; 97 live techniques pinned in [`data/catalogs/attack-ics-v19.2.csv`](../data/catalogs/attack-ics-v19.2.csv). Revoked IDs checked through the STIX `revoked-by` relationships: T0855 → T1692.001, T0856 → T1692.002, T0857 → T1693.001, T0839 → T1693.002 |
| [SP800-160v2] | [NIST SP 800-160 Vol. 2 Rev. 1, *Developing Cyber-Resilient Systems*](https://doi.org/10.6028/NIST.SP.800-160v2r1) ([CSRC page](https://csrc.nist.gov/pubs/sp/800/160/v2/r1/final)) | Rev. 1, December 2021 | The 14 cyber resiliency techniques (Table D-2), enforced by the validator |
| [STRIDE-MS] | [Hernan, Lambert, Ostwald, Shostack, "Uncover Security Design Flaws Using The STRIDE Approach," MSDN Magazine](https://learn.microsoft.com/en-us/archive/msdn-magazine/2006/november/uncover-security-design-flaws-using-the-stride-approach) | November 2006 | STRIDE-per-element applicability chart (Figure 5), enforced by the validator |
| [SYSML-PILOT] | [OMG SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation) | Release pinned in the SysML session | Model validation |

## Bookmarked for later repos

| Repo | Source | Notes |
|---|---|---|
| P2 | [PX4 Bootloader Secure Boot](https://docs.px4.io/main/en/advanced_config/bootloader_secure_boot) [PX4-SECBOOT] | The PX4 bootloader verifies an Ed25519 signature (via monocypher) before starting the firmware. Absent from tag `v1.17.0`; present at `v1.18.0-rc1` |
| A-09 (data at rest) | [PX4 Log Encryption](https://docs.px4.io/main/en/dev_log/log_encryption) ([v1.17 page](https://docs.px4.io/v1.17/en/dev_log/log_encryption)) | ULog encryption with XChaCha20 and an RSA2048-OAEP key wrap. Not enabled in default builds. Present in v1.17 and v1.18 |
| P4 | [PX4 SBOM](https://docs.px4.io/main/en/contribute/sbom) | An SPDX 2.3 JSON SBOM is generated for every firmware build. New in v1.18 |
