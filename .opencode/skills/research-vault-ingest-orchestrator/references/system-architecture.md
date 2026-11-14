# ResearchVault production architecture

```text
Local PDF (pdf_path) + paper-registry row (paper_id)
  [legacy Zotero key optional]
        |
        v
03fulltext/<collection>/<paper_id>.md
  - original-language MinerU archive
  - image assets and reciprocal note link
        |
        v
02vault/<collection>/<paper>.md
  - Chinese structured single-paper Analytical Note
  - paper_id and fulltext_path
        |
        v
01knowledge/
  - Chinese human-facing derived synthesis
01knowledge/.meta/
  - claims, gaps, indexes and machine traceability
```

`01knowledge` is a navigation and synthesis layer, not primary scientific evidence. Evidence must remain traceable as Knowledge → Analytical Note → Fulltext → optional original PDF.

| Layer | Responsibility | Stable identity |
| --- | --- | --- |
| Local PDF + `papers.tsv` | Metadata and source PDF | `paper_id`, `pdf_path` |
| `03fulltext` | Verbatim source archive and images | `paper_id`, `pdf_path` |
| `02vault` | Structured single-paper interpretation | `paper_id` |
| `01knowledge` | Cross-paper Chinese synthesis and navigation | source Note links |
| `01knowledge/.meta` | Claims, gaps and machine-only traceability | claim/gap IDs plus Note-derived identity |
