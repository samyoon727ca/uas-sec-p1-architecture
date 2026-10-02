# 8. Verification plan

> Status: started. Two verification events are defined. The rest follow the requirements.

Each requirement in [`data/requirements.csv`](../data/requirements.csv) names a verification method and the repo that produces the evidence:

- **I**, Inspection
- **A**, Analysis
- **D**, Demonstration
- **T**, Test

The verification events below define how that evidence is produced.

**SITL harness.** VE-01 and VE-02 run in a PX4 software-in-the-loop (SITL) harness hosted in **P3**. P3 owns MAVLink key provisioning, so the signed-C2 demo belongs there, and the heartbeat test reuses the same setup. P5 covers hardware testing on owned devices and does not need SITL.

*Assumption: SITL builds support signing. PX4 stores the key under the board's root path (`CONFIG_BOARD_ROOT_PATH` in `mavlink_sign_control.h`), which suggests they do. Confirming this is P3's first step.*

## Verification events

| ID | Verifies | Method | Evidence repo | Status |
|---|---|---|---|---|
| VE-01 | SR-001 (THR-001) | T | P3 | Planned |
| VE-02 | OI-01: signed C2 with the pinned versions. Later, the signing requirements | D | P3 | Planned |

### VE-01: spoofed GCS heartbeats do not suppress the data-link-loss failsafe

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
5. **Control run.** Repeat steps 1–4, but inject the same heartbeats directly on an FC MAVLink link that bypasses the CC.

**Pass criteria:**
- **Main run:** the FC enters the GCS-loss failsafe and starts Return within `COM_DL_LOSS_T` of the cut, plus a stated tolerance. The CC counters show the injected packets dropped at the radio interface.
- **Control run:** the failsafe is suppressed. This shows the threat is real and that the test can detect it.

**Residual risk not covered:** heartbeats from a compromised CC or GCS (THR-001 residual).

### VE-02: signed C2 works with the pinned versions

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

**Pass criteria:**
- Commands signed by QGroundControl are accepted and executed.
- Telemetry from the FC is signed.
- Unsigned and wrongly signed commands are rejected and have no effect.

**Until this passes,** documents describe GCS-to-FC signing as design intent only, not as working (OI-01).
