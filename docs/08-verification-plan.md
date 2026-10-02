# 8. Verification plan

Every one of the 44 requirements is covered by at least one of 16 verification events. Each event uses the same method and evidence repo as the requirements it verifies, and the validator enforces that. All events are planned. Their results arrive as P2–P6 produce evidence.

The events live in [`data/verification.csv`](../data/verification.csv), with their procedures and pass criteria. Each requirement in [`data/requirements.csv`](../data/requirements.csv) names a verification method and the repo that produces the evidence:

- **I**, Inspection
- **A**, Analysis
- **D**, Demonstration
- **T**, Test

**SITL harness.** VE-01 and VE-02 run in a PX4 software-in-the-loop (SITL) harness hosted in **P3**. P3 owns MAVLink key provisioning, so the signed-C2 demo belongs there, and the heartbeat test reuses the same setup. P5 covers hardware testing on owned devices and does not need SITL.

*Assumption: SITL builds support signing. PX4 stores the key under the board's root path (`CONFIG_BOARD_ROOT_PATH` in `mavlink_sign_control.h`), which suggests they do. Confirming this is P3's first step.*

## 8.1 Verification events

Generated from the CSVs by `tools/render_views.py`. CI fails if this view drifts from the data. The requirements table in [§7](07-requirements.md) shows the reverse mapping, in its "Verified by" column.

<!-- BEGIN GENERATED: verification-events -->
16 verification events: 16 planned.

| ID | Event | Method | Evidence | Verifies | Pass criteria |
|---|---|---|---|---|---|
| VE-01 | Spoofed GCS heartbeats do not suppress the data-link-loss failsafe | T | P3 | SR-001, SR-002, SR-004 | FC enters Return within COM_DL_LOSS_T plus a stated tolerance; CC and GCS counters show injected packets dropped; control run shows the failsafe suppressed. |
| VE-02 | Signed C2 works with the pinned versions | D | P3 | SR-003, SR-025 | Signed commands execute; unsigned and wrongly signed commands have no effect; the GCS alerts on unsigned telemetry. Closes OI-01. |
| VE-03 | CC accepts only signed, newer update images | T | P3 | SR-007 | Only the valid newer image installs; each rejection is logged. |
| VE-04 | CC autonomy ignores unsigned or altered FC telemetry | T | P3 | SR-015 | Autonomy decisions use only frames with valid signatures; injected frames are logged and discarded. |
| VE-05 | Imagery and flight logs are unreadable without the MSS key | D | P3 | SR-017, SR-019 | Copies from the vehicle are unreadable; the MSS decrypts both. |
| VE-06 | Key management on the MSS | D | P3 | SR-034, SR-035, SR-036, SR-037 | Export fails; the restored key signs an artifact that verifies; after rotation the old key is rejected by FC, CC and GCS; first-key provisioning follows the defined order. |
| VE-07 | CC verified boot and key sealing | T | P2 | SR-005, SR-010 | Only the signed chain boots; the keys unseal only in the measured, unmodified boot state. |
| VE-08 | FC boots only signed firmware | T | P2 | SR-018 | Only the signed image starts PX4; the others stay in the bootloader. |
| VE-09 | CC image hardening | T | P4 | SR-006, SR-008, SR-009, SR-014, SR-016, SR-044 | Modified blocks fail to read; only the signing service reads the key; confined services cannot reach credentials; the device is refused; the watchdog restores C2 forwarding; the login is refused. |
| VE-10 | CC command filter and logging | T | P4 | SR-011, SR-012, SR-013 | Excluded messages never reach the FC; the approved command does; the flood is limited to the approved rate; each forwarded command is logged with time and WireGuard peer. |
| VE-11 | Supply-chain pipeline and package integrity | T | P4 | SR-028, SR-031, SR-032, SR-033, SR-038 | Both bad builds fail; the release has an SBOM, a vulnerability scan and provenance; the tampered artifact and unsigned package are rejected; the offload account cannot read key material. |
| VE-12 | Tamper-evident seal inspection | I | P5 | SR-023 | Seals cover every listed access point, and the SD-card access is visibly evident. |
| VE-13 | FC debug port cannot be used | T | P5 | SR-024 | No debug session can be established, or the port is sealed so that any attempt is evident. |
| VE-14 | FC parameter baseline | I | P6 | SR-020, SR-021, SR-022 | Bits 9 and 11 are set; NAV_TRAFF_AVOID is 0 or 1; uXRCE-DDS is disabled; only the CC-link MAVLink instance is enabled besides USB. |
| VE-15 | GCS configuration | I | P6 | SR-026, SR-027, SR-029, SR-030 | Individual logins and screen lock are enforced; the disk is encrypted; only the ground-radio interface is enabled; each sortie record names its operator. |
| VE-16 | MSS configuration and records | I | P6 | SR-039, SR-040, SR-041, SR-042, SR-043 | Individual logins; every load and provisioning action is logged with a maintainer; peripheral versions are recorded against the baseline; GCS keys are provisioned wired; key operations happen offline. |
<!-- END GENERATED: verification-events -->

VE-01 and VE-02 are written out in full below, because they close the architecture's open items (OI-01) and its priority threats (THR-001, THR-027, THR-057).

## 8.2 VE-01: spoofed GCS heartbeats do not suppress the data-link-loss failsafe

**Setup:**
- PX4 v1.18 (DD-06) running in SITL, with a signing key provisioned and `NAV_DLL_ACT` = 2 (DD-05).
- A CC stand-in running WireGuard, mavlink-router and the SR-001 interface rules, connected to the FC over a serial-equivalent link.
- QGroundControl v5.1.5 as the GCS, connected through the tunnel.
- An injector on the CC's radio-side network.

**Procedure:**
1. Start a mission with the GCS connected through the tunnel.
2. Cut the GCS tunnel.
3. From the radio-side network, inject unsigned `HEARTBEAT` messages with `MAV_TYPE_GCS` at the normal GCS rate.
4. Record the FC flight mode, the failsafe events and the CC packet counters.
5. **GCS side (SR-002).** Repeat the injection at the GCS's radio-side network, aimed at the GCS host.
6. **Control run.** Repeat steps 1–4, but inject the same heartbeats directly on an FC MAVLink link that bypasses the CC.

**Pass criteria:**
- **Main run:** the FC enters the GCS-loss failsafe and starts Return within `COM_DL_LOSS_T` of the cut, plus a stated tolerance. The CC counters show the injected packets dropped at the radio interface.
- **GCS side:** the GCS counters show the injected packets dropped at its radio interface.
- **Control run:** the failsafe is suppressed. This shows the threat is real and that the test can detect it.

**Residual risk not covered:** heartbeats from a compromised CC or GCS (THR-001 residual).

## 8.3 VE-02: signed C2 works with the pinned versions

**Setup:**
- PX4 v1.18 in SITL at the pinned tag.
- QGroundControl v5.1.5.
- A second MAVLink client with no key.
- A third client holding a different key.

**Procedure:**
1. While disarmed, provision the key with `SETUP_SIGNING` from an MSS stand-in.
2. Load the same key into QGroundControl.
3. Upload a mission, change a parameter, arm, and fly.
4. Send the same command from the keyless client.
5. Send the same command from the wrong-key client.
6. Disarm, delete the key file from the SITL storage, and reboot the FC. This simulates removal from the SD card (THR-027).
7. **Replay characterization (THR-065).** Restore the key and record a signed command. Stop the FC without a graceful shutdown, restart it, and replay the recorded frame.

**Pass criteria:**
- Commands signed by QGroundControl are accepted and executed.
- Telemetry from the FC is signed.
- Unsigned and wrongly signed commands are rejected and have no effect.
- After step 6, QGroundControl alerts the operator that FC telemetry is unsigned (SR-025).
- Step 7 is a measurement, not a pass/fail check. Its result updates THR-065: if the replayed frame is rejected, the assumption is retired; if it is accepted, the threat stands and a requirement is added.

**Until this passes,** documents describe GCS-to-FC signing as design intent only, not as working (OI-01).
