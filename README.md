# P1: Security architecture and requirements for a notional small UAS

[![validate](https://github.com/samyoon727ca/uas-sec-p1-architecture/actions/workflows/validate.yml/badge.svg)](https://github.com/samyoon727ca/uas-sec-p1-architecture/actions/workflows/validate.yml)

This repo is the security architecture, threat model and derived requirements for a notional, unclassified small UAS. The UAS is built from open-source parts: a PX4 flight controller, a Linux companion computer, a ground control station, and a MAVLink telemetry/C2 link. P1 is the anchor for five follow-on repos, P2–P6. Each one implements and verifies requirements allocated here.

> **Notional and unclassified.** Built only from public sources: PX4 and MAVLink documentation, NIST, MITRE. It is not based on any real program or system. Assumptions are labeled as assumptions.

## Threat

_Status: planned._ Threats will be analyzed STRIDE per element, with MITRE EMB3D and ATT&CK for ICS. Each threat gets a mission-impact rating. See [`docs/05-threat-model.md`](docs/05-threat-model.md).

## Requirements

_Status: planned._ Each "shall" requirement will trace to a parent threat, be allocated to one component, and name a verification method and evidence repo. See [`data/requirements.csv`](data/requirements.csv).

## Design

_Status: drafting._ See [`docs/04-architecture.md`](docs/04-architecture.md).

## Verification evidence

Traceability is checked automatically on every push. [`tools/validate_trace.py`](tools/validate_trace.py) fails the build if any of these hold:

- a threat is neither mitigated nor explicitly accepted;
- a requirement has no parent threat, has no allocated component, or can't be verified;
- an ID is orphaned;
- an architecture element has no threat analysis.

The column rules are in [`data/README.md`](data/README.md).

Evidence for each requirement will come from the follow-on repos:

| Repo | Scope | Status |
|---|---|---|
| P2 | Verified boot chain | Planned |
| P3 | PKI, key management and signed updates | Planned |
| P4 | Hardened embedded Linux and supply-chain pipeline | Planned |
| P5 | Hardware and firmware security assessment | Planned |
| P6 | RMF-as-code (OSCAL) | Planned |

## Repository map

| Path | Contents | Status |
|---|---|---|
| [`docs/01-system-description.md`](docs/01-system-description.md) | Purpose, scope, components, interfaces | Drafting |
| [`docs/02-conops.md`](docs/02-conops.md) | Mission phases, actors, lost-link behavior | Drafting |
| [`docs/03-assumptions.md`](docs/03-assumptions.md) | Labeled assumptions `A-##` | Drafting |
| [`docs/04-architecture.md`](docs/04-architecture.md) | Trust boundaries, data flows, design decisions | Drafting |
| [`docs/05-threat-model.md`](docs/05-threat-model.md) | STRIDE per element, EMB3D, ATT&CK for ICS | Planned |
| [`docs/06-cyber-resiliency.md`](docs/06-cyber-resiliency.md) | NIST SP 800-160 Vol. 2 techniques mapped to the design | Planned |
| [`docs/07-requirements.md`](docs/07-requirements.md) | Requirement conventions | Planned |
| [`docs/08-verification-plan.md`](docs/08-verification-plan.md) | I/A/D/T methods and the evidence map | Planned |
| [`docs/references.md`](docs/references.md) | Sources, with pinned versions | Drafting |
| [`data/`](data/) | Elements, threats, requirements, trace (CSV) | Schema only |
| `model/sysml/` | SysML v2 textual model | Planned |
| `brief/` | ~10-slide PDR-style brief (Marp) | Planned |

## Run the checks locally

```sh
python -m unittest discover -s tests
python tools/validate_trace.py
```

Python 3.11+. Standard library only.

## License

[Apache-2.0](LICENSE)
