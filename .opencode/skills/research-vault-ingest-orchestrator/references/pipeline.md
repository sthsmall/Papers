# Production ingest pipeline

## Entry condition

Accept a paper only when the user identifies it by a local PDF path, `paper_id`, arXiv ID, DOI, collection plus an unambiguous item, or another resolvable explicit reference. This workflow does not discover papers. Zotero keys are optional legacy references.

## Stages

1. **State inspection** — inspect existing Note, Fulltext, Knowledge source coverage, sidecars, prior log entries, and Note conformance to `{{VAULT_ROOT}}\模板\论文简读模板.md` without writing.
2. **Identity resolution** — use `paper-registry` + `zotero-data-fetcher` to resolve `paper_id`, local `pdf_path`, and metadata. A conflict becomes `MANUAL_REVIEW_REQUIRED`.
3. **Fulltext gate** — reuse a valid formal Fulltext first; otherwise use `zotero-fulltext-archiver` and its production MinerU route.
4. **Analytical Note gate** — reuse a valid formal Note only if its identity, source links, structure, and method-section quality conform to the current contract; otherwise use `zotero-analytical-writer` in create mode (new Note) or same-path method-section-repair mode (legacy Note). The method section must be mechanism-level (≥4,500 chars; ≥2 formulas or explicit “原文无公式”; training details; results/ablation/boundaries), and images must reach four or document the original shortage.
5. **Pair validation** — require reciprocal Note/Fulltext paths and matching `paper_id`; `legacy_zotero_key`/`pdf_key` are optional. Validate image links and count where Fulltext exists; run the method-quality checks (length, formulas, training details, quotes) before accepting the Note.
6. **Knowledge decision** — call `research-vault-knowledge-maintainer` only with the completed Note and evidence state. It decides whether existing Knowledge is strengthened, conditioned, bounded, challenged, newly supported, or unchanged.
7. **Final validation and log** — validate Note-template conformance, quotation/page evidence, reciprocal links, and images; run the Knowledge validator when Knowledge is touched or re-evaluated, then append the human-readable log event only if the applicable contract passes.

## Delegation map

| Stage | Owner | Must not be duplicated here |
| --- | --- | --- |
| Paper identity/PDF lookup | `paper-registry` + `zotero-data-fetcher` | Local `paper_id`, `pdf_path`, metadata; Zotero optional legacy |
| PDF to formal Fulltext | `zotero-fulltext-archiver` | MinerU implementation and image migration |
| Structured paper understanding | `zotero-analytical-writer` | Note template and writing logic |
| Cross-paper synthesis | `research-vault-knowledge-maintainer` | Frozen schema, templates, claims and gaps |
| Later user questions | `research-vault-literature-retrieval` | Ingest execution |
