# 5. Threat model

> Status: planned.

STRIDE per element over [`data/elements.csv`](../data/elements.csv), with MITRE EMB3D for device-level threats and MITRE ATT&CK for ICS where control or C2 applies. Every threat has an ID, a mission-impact rating and a disposition. The data lives in [`data/threats.csv`](../data/threats.csv).

Seeded from the architecture review: **THR-001**, spoofed GCS heartbeats suppress the data-link-loss failsafe (MI-1). See [§4.2](04-architecture.md#42-c2-trust-base), item 6.
