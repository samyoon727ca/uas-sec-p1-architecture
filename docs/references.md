# References

Every external source used in P1, with the version pinned and the date it was accessed. Framework IDs (EMB3D, ATT&CK for ICS) are valid only against the versions listed here. All sources were accessed 2026-10-02.

## PX4 version note

PX4's own docs say: "The signing protocol was audited when it was drafted, but PX4's implementation of it has not been." [PX4-HARD]. P1 treats PX4 signing as an unaudited control.

The **MAVLink signing implementation is absent from PX4 tag `v1.17.0`**. A search of all 135 files of `src/modules/mavlink` at that tag finds no signing code, and the docs at that tag have no message-signing or hardening page. Both are present in the v1.18 pre-releases (`mavlink_sign_control.cpp` at tag `v1.18.0-rc1`). The v1.18 release notes describe signing as "now spec-compliant (breaking change)" [PX4-1.18]. The hardening page on `docs.px4.io/main` carries a "PX4 v1.17" badge, but the code behind it ships from v1.18. The baseline decision is DD-06.

## Sources

| Tag | Source | Version pinned | Used for |
|---|---|---|---|
| [PX4-SIGN] | [PX4 Guide: MAVLink Message Signing](https://docs.px4.io/main/en/mavlink/message_signing) | `main` docs; matches the doc at tag `v1.18.0-rc1` | Key storage, provisioning, unsigned allowlist, armed guard (§4.2) |
| [PX4-HARD] | [PX4 Guide: MAVLink Security Hardening](https://docs.px4.io/main/en/mavlink/security_hardening) | Same | Shared key on all GCS and CC nodes, enforcement on all links, capabilities at risk, audit status |
| [PX4-1.18] | [PX4 v1.18 release notes](https://docs.px4.io/main/en/releases/1.18) | Beta at time of access | Signing made spec-compliant; SBOM generation |
| [PX4-SRC] | PX4-Autopilot source at tags `v1.17.0` and `v1.18.0-rc1`: [`mavlink_sign_control.cpp`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/mavlink/mavlink_sign_control.cpp), [`mavlink_receiver.cpp`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/mavlink/mavlink_receiver.cpp), [`commander_params.yaml`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/src/modules/commander/commander_params.yaml), [`fmu-v6x rc.board_defaults`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/boards/px4/fmu-v6x/init/rc.board_defaults), [`generate_config.py`](https://github.com/PX4/PX4-Autopilot/blob/v1.18.0-rc1/Tools/serial/generate_config.py) | `v1.17.0`, `v1.18.0-rc1` | Signing absent in v1.17.0; GCS liveness from `MAV_TYPE_GCS` heartbeats; `NAV_DLL_ACT` default 0 (Disabled) and `COM_DL_LOSS_T` default 10 s; FMUv6X default MAVLink-over-Ethernet instance; serial config value 0 = disabled |
| [PX4-PR26894] | [PX4-Autopilot PR #26894](https://github.com/PX4/PX4-Autopilot/pull/26894) | Merged to `main` | Earlier behavior (non-standard `MAV_SIGN_CFG`, USB-only provisioning) and the spec-compliant change |
| [MAV-SIGN] | [MAVLink Developer Guide: Message Signing](https://mavlink.io/en/guide/message_signing.html) | Current | 32-byte key; 48-bit SHA-256-based signature; timestamps and link IDs; no encryption |
| [QGC] | [QGroundControl `src/MAVLink/Signing`](https://github.com/mavlink/qgroundcontrol/tree/v5.1.5/src/MAVLink/Signing) | `v5.1.5` | GCS-side signing implementation exists |
| [MAVROUTER] | [mavlink-router sample configuration](https://github.com/mavlink-router/mavlink-router/blob/master/examples/config.sample) | `master` at access; version pinned in P4 | Filters available per endpoint: `AllowMsgIdIn/Out`, `BlockMsgIdIn/Out`, `AllowSrcSysIn/Out`, `AllowSrcCompIn/Out` (and their `Block*` forms). No command-ID filter |
| [WG] | [WireGuard protocol](https://www.wireguard.com/protocol/) | Current | Curve25519, ChaCha20-Poly1305, BLAKE2s, HKDF; no cipher agility |
| [EMB3D] | [MITRE EMB3D](https://emb3d.mitre.org/) | v2.0.2 | Device-level threat IDs (`TID-###`) in the threat model |
| [ATTACK-ICS] | [MITRE ATT&CK for ICS](https://attack.mitre.org/matrices/ics/) | ATT&CK content v19.2 | C2 and control technique IDs. Some ICS techniques appear to have been renumbered (for example, Unauthorized Message now shows as T1692). Every ID will be re-checked against v19.2 when used |
| [SP800-160v2] | [NIST SP 800-160 Vol. 2 Rev. 1, *Developing Cyber-Resilient Systems*](https://doi.org/10.6028/NIST.SP.800-160v2r1) ([CSRC page](https://csrc.nist.gov/pubs/sp/800/160/v2/r1/final)) | Rev. 1, December 2021 | The 14 cyber resiliency techniques (Table D-2), enforced by the validator |
| [SYSML-PILOT] | [OMG SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation) | Release pinned in the SysML session | Model validation |

## Bookmarked for later repos

| Repo | Source | Notes |
|---|---|---|
| P2 | [PX4 Bootloader Secure Boot](https://docs.px4.io/main/en/advanced_config/bootloader_secure_boot) [PX4-SECBOOT] | The PX4 bootloader verifies an Ed25519 signature (via monocypher) before starting the firmware. Absent from tag `v1.17.0`; present at `v1.18.0-rc1` |
| A-09 (data at rest) | [PX4 Log Encryption](https://docs.px4.io/main/en/dev_log/log_encryption) ([v1.17 page](https://docs.px4.io/v1.17/en/dev_log/log_encryption)) | ULog encryption with XChaCha20 and an RSA2048-OAEP key wrap. Not enabled in default builds. Present in v1.17 and v1.18 |
| P4 | [PX4 SBOM](https://docs.px4.io/main/en/contribute/sbom) | An SPDX 2.3 JSON SBOM is generated for every firmware build. New in v1.18 |
