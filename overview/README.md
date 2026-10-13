# Project overview (PDF)

[`overview.pdf`](overview.pdf) explains the portfolio from first principles, for an engineer new to secure boot, measured boot and TPMs: the system and its threats (P1); every concept P2 relies on; P2's design, test cases and evidence; a step-by-step guide to rebuilding and rerunning the tests; and the roadmap for P3 to P6. A chapter is reserved for limitations and open findings, to be written later from an audit.

The PDF is generated. Every table of requirements, threats, verification events, test cases and evidence runs, and every count and status in its text, is filled in at build time from P1's `data/*.csv` and from a pinned snapshot of P2 (below). Nothing is retyped, so the document cannot drift from the data. It states the P1 and P2 commits it was built from on its "Built from" page and in every page footer.

## Layout

| Path | Contents |
|---|---|
| `src/front.md` | Title page, contents, conventions, "Built from" table |
| `src/p1.md` … `src/p6.md` | One file per project: a full chapter or a roadmap stub (below) |
| `src/roadmap.md` | Introduction of the roadmap chapter that collects the stubs |
| `src/limitations.md` | Placeholder for the limitations and open findings chapter |
| `src/appendix.md` | Glossary and sources |
| `p2-snapshot/` | Byte-for-byte copies of P2 files at the commit in `p2-snapshot/pin.txt` |
| `build.sh` | The build: generate, render diagrams, print to PDF |
| `render.mjs`, `style.css`, `mermaid.json` | Markdown to HTML to PDF in Chrome; print stylesheet; diagram theme |
| `package.json`, `package-lock.json`, `.npmrc` | The pinned Node toolchain |
| `overview.pdf` | The built PDF, committed |

The generator is [`../tools/gen_overview.py`](../tools/gen_overview.py) and the snapshot check is [`../tools/check_p2_snapshot.py`](../tools/check_p2_snapshot.py); both are standard-library Python, like P1's other tools, and `tests/test_gen_overview.py` tests the generator.

## Chapters and stubs

Each project has one source file, `src/pN.md`, that starts with front matter:

```
---
project: P3
kind: stub          # or: chapter
title: PKI, key management and signed updates; SITL harness   # stubs only
---
```

- **`kind: chapter`**: the file is a full chapter. It must start with a level-1 heading, written as `# Title {#pN}`. Chapters appear in project order after the front matter.
- **`kind: stub`**: the file is a section of the roadmap chapter, headed `P<N>: <title>`. Its body says what the project is for and what it inherits from earlier projects, citing their documents. The generator appends the project's P1 requirements (with parent threats) and verification events, generated from P1's data.

When no stub is left, the roadmap chapter is dropped. To add a project, add `src/pN.md`; the front matter must name the same number as the file.

**Turning a stub into a chapter** (when the project produces results):

1. In `src/pN.md`, set `kind: chapter`, drop `title`, and start the body with `# PN: <title> {#pN}`. The file leaves the roadmap and becomes a chapter in project order. Keep the `{#pN}` id: other chapters link to it.
2. Write it like `p2.md`: what the project must show (its P1 requirements, `<!-- gen: p1-reqs-of PN -->`), the concepts it needs, its design, every test case with what its pass does and does not show, how to read its evidence, and how to rebuild it.
3. If the chapter needs the project's own data (test cases, evidence), add a snapshot of that repo the way P2's is added: `overview/pN-snapshot/` with a `pin.txt`, a byte-for-byte check like `tools/check_p2_snapshot.py` run in CI, and generator blocks and values for it in `tools/gen_overview.py` with tests. The generator reads only P2's snapshot today; P2's code is the pattern.
4. Move anything the roadmap said the project inherits into the chapter, and update the "How to read it" paragraph in `src/front.md`.
5. Run the tests and rebuild the PDF.

The order is fixed by the generator: `front.md`, the chapters, the roadmap (if any stub is left), `limitations.md`, `appendix.md`.

## The limitations chapter

`src/limitations.md` is a separate file that the build always includes, after the chapters and the roadmap and before the appendix. Until it is written it holds only a marked placeholder (the `<div class="placeholder">` box), which says the chapter is reserved and points to the limitations already stated elsewhere. It is to be written from the audit of P1 and P2, at the step that reconciles the audit with this document; nothing in it may be written before then.

To fill it:

1. Replace everything below the heading with the chapter's text. Keep the heading line `# Limitations and open findings {#limitations}`: other chapters link to `#limitations`.
2. Cite each finding's source (the audit report, and the P1 or P2 file and line it concerns), and use generated values for any status, count or commit, as everywhere else.
3. Update the sentence that calls the chapter reserved in `src/front.md` ("How to read it"). Where a finding changes what a test case's pass shows, also correct that case's text in `src/p2.md`.
4. Rebuild the PDF.

## Writing the sources

- **Generated blocks.** A line `<!-- gen: NAME ARGS -->` is replaced by a generated table: for example `<!-- gen: p1-reqs-of P2 -->` (a repo's requirements), `<!-- gen: p2-testcases -->`, `<!-- gen: p2-tc TC-05 -->` (one test case's card), `<!-- gen: p2-runs VE-07 -->` (every run of an event's evidence), `<!-- gen: mermaid-from docs/04-architecture.md 0 TB -->` (a diagram taken from a P1 document, so it cannot drift; the optional last argument only changes a flowchart's direction to fit the page). The list is `BLOCKS` in `tools/gen_overview.py`.
- **Generated values.** `{{NAME}}` or `{{NAME:ARG}}` is replaced by a value: counts (`{{p1.threats}}`), statuses (`{{p2.ve_status:VE-07}}`, `{{p2.tc_ci:TC-05}}`), commits (`{{p2.commit}}`) and fields of an evidence `summary.json` (`{{ev:VE-07:environment/run_id}}`). The list is `inline_values()` in the generator. An unknown name fails the build.
- **Rule:** never type a status, a count from the data, or a commit into the sources; use a generated value. Numbers observed by running a command at a stated commit (a test count, for example) are written with that commit.
- **Diagrams.** Fenced ```` ```mermaid ```` blocks are rendered by mermaid-cli to SVG. Avoid `;` in labels; it ends a Mermaid statement.
- **Headings and references.** `{#id}` after a heading sets its anchor, `{-}` leaves it unnumbered. `[](#id)` becomes "chapter N" or "§N.M", or for an unnumbered heading its text and the section it sits in ("“Title” in §N.M"); an unknown id fails the build.
- **Citations** follow the convention on the document's Conventions page: "P1 `docs/04-architecture.md` §4.2", "P2 `tools/predict_pcrs.py`:225".

## The P2 snapshot

`p2-snapshot/` holds byte-for-byte copies of P2's `data/requirements.csv`, `data/trace.csv`, `data/testcases.csv`, `data/p1/pin.txt` and the `summary.json` of each evidence run its test cases cite, at the commit in `p2-snapshot/pin.txt`. This is the same arrangement P2 uses for its copy of P1 (`data/p1/` in P2). `.gitattributes` marks the folder `-text`, so a Windows checkout does not change line endings.

`tools/check_p2_snapshot.py` compares every file with P2 at the pinned commit and fails on any difference (it needs network access; CI runs it). The generator fails if a test case cites an evidence folder whose `summary.json` is not in the snapshot.

To move the pin: copy the files from the new P2 commit (`git show <commit>:<path>` keeps the bytes), add the `summary.json` of any newly cited evidence folder, delete ones no longer cited, update `pin.txt`, run the check, and rebuild the PDF, all in one change.

## Build

```sh
python tools/check_p2_snapshot.py                    # network; the snapshot matches P2
CHROME_PATH=/path/to/chrome overview/build.sh        # Node 22+, Python 3.11+, git
```

`build.sh` installs the pinned toolchain with `npm ci` on first use, runs the generator into `overview/build/` (git-ignored), renders each diagram with mermaid-cli and prints the HTML to `overview/overview.pdf` with puppeteer. Chrome cannot number the contents page by itself, so `render.mjs` prints twice or more: it reads the page of each heading from the PDF's named destinations, fills in the numbers, and prints again until no heading moves (it fails if they do not settle). The toolchain is the brief's: `package-lock.json` was derived from `brief/package-lock.json`, so every package both share is at the same version, and `markdown-it` is the version the brief already locks.

CI builds the PDF in the `overview` job of `.github/workflows/validate.yml` and uploads it as the `overview` artifact. The committed PDF is rebuilt and committed in its own change after the sources change, so its "Built from" page names a commit with no local changes. It is either the `overview` artifact of the CI run on a push of the source commit, downloaded unchanged (as `brief/pdr-brief.pdf` is), or built from a clean checkout of that commit with the pinned toolchain; the commit message says which, and the PDF's "Built from" page records the Node, Chrome and package versions that printed it. (A `pull_request` run builds GitHub's merge commit, which is on no branch, so use a push run's artifact.)
