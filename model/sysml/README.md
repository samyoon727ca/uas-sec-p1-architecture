# SysML v2 model

A SysML v2 textual model of P1, validated in CI against the OMG reference implementation:

- [`uas_architecture.sysml`](uas_architecture.sysml) is written by hand. It holds the structure, ports, data flows and trust boundaries of [§4](../../docs/04-architecture.md).
- [`uas_security.sysml`](uas_security.sysml) is **generated** from [`data/`](../../data/) by `tools/gen_sysml.py`. It holds the 65 threats, 44 requirements and 16 verification events of §5, §7 and §8.

Both files validate on the OMG SysML v2 Pilot Implementation with 0 errors and 0 warnings.

## Modeling conventions

| P1 concept | SysML v2 construct |
|---|---|
| Component, external entity | `part` usage inside `uasSystem`, with the element ID as its short name (`part <'CMP-FC'> fc`) |
| Data store | `item` usage inside its host part (`item <'DS-FC-KEY'> signingKeyFile`) |
| Data flow | `flow` between ports (`flow <'DF-04'> ccToFcCommands of MavlinkFrame from … to …`) |
| Trust boundary | `TrustBoundary` enumeration literal (`<'TB-02'>`). Flows carry `@Crosses` metadata listing the boundaries they cross |
| Element ID index | One `alias` per element ID (`alias 'CMP-CC' for …`). The generator fails if any ID in `elements.csv` lacks one |
| Threat | `concern` typed by `Threat`, with mission impact, STRIDE category and disposition. A `dependency` links it to its element |
| Requirement | `requirement` typed by `SecurityRequirement`. It `frame`s its parent threats and is `satisfy`-ed by its allocated component |
| Verification event | `verification` case whose objective `verify`s its requirements |

The CSVs remain the single source of truth. The security model is regenerated from them, and CI fails if the committed file is stale.

## Tooling: OMG Pilot Implementation, run headless

**Choice.** Validation uses the OMG SysML v2 Pilot Implementation [SYSML-PILOT]: release `2026-08`, distributed as the Jupyter SysML kernel 0.62.0 (EPL-2.0).
- **Download.** `tools/sysml/validate.sh` downloads the kernel zip from the Pilot Implementation's GitHub release and checks it against a pinned SHA-256. That is the same hash conda-forge's recipe pins.
- **Validation.** `tools/sysml/ValidateSysML.java` then loads the bundled standard library and runs each file through the implementation's own API (`SysMLInteractive.process`). It reports syntax errors, semantic errors and warnings with line and column, and exits non-zero on any error.
- **Requirements.** Java 21 only. No Eclipse, Jupyter or conda.

**Trade-off:**

| Option | For | Against |
|---|---|---|
| **OMG Pilot Implementation, chosen** | The reference implementation, so "validates on the OMG implementation" is a defensible claim. Free, and released monthly | No documented CLI, so P1 carries a roughly 50-line driver over its Java API. About 130 MB download (cached in CI). Plain PlantUML diagrams only |
| Syside (Sensmetry) | Polished editor; headless validation and diagram export | The CLI and automation tier is paid, so it doesn't suit a public repo's CI. The original open-source version is archived |
| Eclipse SysON | Open-source web editor with graphical views | Textual import goes through an embedded SysIDE CLI with a reported bug for current syntax (SysON issue #2543). Not a CI validator |
| Community ANTLR parsers | Light and fast | Syntax checks only, and their conformance is unverified |

**Caveats found while building this:**
- `frame`, `analysis` and `accept` are SysML v2 keywords. Generated enumeration literals are therefore always quoted.
- A `satisfy` target must be reached with dot notation from the context. The generator derives that path from the alias index.

## Run locally

```sh
python tools/gen_sysml.py      # regenerate uas_security.sysml after editing data/
tools/sysml/validate.sh        # downloads the pinned kernel once into .cache/sysml
```
