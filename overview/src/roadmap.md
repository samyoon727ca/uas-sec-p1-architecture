# Roadmap: P3 to P6 {#roadmap}

P3 to P6 are planned; none has produced evidence yet. Each section below says what the project is for, lists the P1 requirements and verification events it owns (generated from P1's `data/requirements.csv` and `data/verification.csv`, with parent threats from `data/trace.csv`), and what it inherits from P2, citing the P2 document that hands it over. P1 also names a P7, which fuzzes the CC's command filter (P1 `docs/04-architecture.md` DD-04); it owns no P1 requirement and has no section here.

Each project has one source file, `overview/src/pN.md`. While its front matter says `kind: stub`, the file is a section of this chapter and the tables are added automatically. When the project has its own results, its file becomes `kind: chapter`, is written as a full chapter like P1's and P2's, and leaves this chapter; when no stub is left, the chapter disappears (`overview/README.md`).

<!-- gen: roadmap-stubs -->
