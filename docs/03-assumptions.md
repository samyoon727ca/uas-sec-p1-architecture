# 3. Assumptions

Everything on this page is an **assumption**: a premise that hasn't been verified for this system and is accepted for analysis. Requirements and threats cite assumptions by ID. If one is invalidated, everything that cites it is re-examined. Verified facts are kept elsewhere: [§4.2](04-architecture.md#42-c2-trust-base) and [references](references.md).

| ID | Assumption | Why it matters |
|---|---|---|
| A-01 | The system is notional and unclassified. It is built only from public documentation and is not based on any real program or system | Keeps the work clean-room |
| A-02 | There is one air vehicle, one GCS and one MSS. No swarm, fleet management or cloud services | Bounds the element set |
| A-03 | The FC runs PX4 on a Pixhawk-standard FMU. The PX4 version is set by DD-06 | Fixes which PX4 security features exist |
| A-04 | The CC is a generic ARM64 Linux single-board computer that has, or can be fitted with, a hardware root of trust such as TPM 2.0. P2 demonstrates this on a dev board | Makes verified boot (P2) feasible |
| A-05 | The data link is an untrusted IP transport. No security credit is taken for the radios' own encryption or authentication | Confidentiality and peer authentication across TB-01 must come from DD-02 |
| A-06 | MAVLink 2 is used on every link, and signing is active in every operational configuration | Without it, any device that reaches a link has full C2 [PX4-HARD] |
| A-07 | There is no separate RC link. Manual control goes through the GCS over MAVLink | RC-link threats and the RC-loss failsafe are out of scope |
| A-08 | Adversaries fall into three tiers: (1) RF-proximate with an SDR, able to jam, eavesdrop and inject; (2) physical access to a lost or captured vehicle, or to unattended ground equipment; (3) able to insert code through an upstream source or a build host. Silicon-level implants and malicious insiders are out of scope. Operators and maintainers are trusted but may make mistakes | Defines what the threat model must cover |
| A-09 | Flight plans, telemetry and imagery are sensitive, so their confidentiality matters. All data is notional | Motivates the tunnel (DD-02) and data-at-rest protection |
| A-10 | Only civil GNSS is used | GNSS spoofing and jamming are in scope |
| A-11 | Security controls must not defeat PX4 failsafes. A security fault must lead to a safe flight state | Constrains every requirement |
| A-12 | Out of scope: airworthiness certification, the radio waveform, EW countermeasures beyond detection and resilience, Remote ID, UTM | Bounds the analysis |
| A-13 | The mission-impact scale MI-1 to MI-4 is project-defined, not taken from a standard | See [`data/README.md`](../data/README.md) |
| A-14 | Software loads and key provisioning happen only on the ground, disarmed, over wired connections, in an area under the maintainer's physical control | Narrows the signing-key provisioning window. That window is still a threat (§4.2, item 5) |
