# Validation contract

Run only the checks applicable to the observed state; never convert an omitted stage into a pass.

## Identity and artifact checks

- Parent `zotero_key` is resolved and unique.
- `pdf_key` is resolved when a PDF/Fulltext is required.
- Note exists when the workflow claims a Note result.
- Note uses the canonical structure from `{{VAULT_ROOT}}\模板\论文简读模板.md` when the request requires strict template compliance; no stale template placeholders or forbidden legacy headings (`研究对象`, `研究方法`, `数据来源`, `研究结论`, `整体流程`, `数据与证据定位`, `局限与后续问题`, `Zotero信息`) remain.
- New Notes follow the 简读 visible order (30-second core → contributions → motivation → method → results → summary → our judgment → quote verification). Existing legacy Notes may keep their contribution/results/judgment sections, but the method section must be `## 三、方法详解`.
- Method-section quality: at least 4,500 characters (4,000 for a genuinely short paper); at least two original formulas when the paper has formulas, or an explicit “原文无公式”; training configuration (optimizer, lr, batch, epochs, input size, loss weights, freeze/trainable modules); results, ablation, and boundaries. A module-name list or abstract paraphrase fails.
- Images: at least four (architecture / data / main result / qualitative or ablation), or all available figures with an explicit shortage note (“原文仅 n 图” / “原文共 n 图” / “MinerU 图注缺失，未能嵌入”); every image path resolves.
- Note frontmatter preserves the stable identity and required source fields, including `zotero_key`, `pdf_key`, `fulltext_path`, and `note_path` when available.
- Formal Fulltext exists when the workflow claims a Fulltext result.
- Note → Fulltext and Fulltext → Note paths resolve when both artifacts exist.
- `zotero_key` and `pdf_key` agree across Note and Fulltext.
- All Fulltext image links resolve; no missing image target is accepted.
- Every conclusion that claims a finding has a directly located source quotation; PDF page numbers are present only when verified against the Original PDF or a reliable page mapping.
- Key quotations are verbatim-greppable in the linked Fulltext; OCR/formula transcription is explicitly marked; unverified page numbers are marked “PDF 页码未验证”.
- Batch legacy-Note migration: run `.opencode/skills/zotero-analytical-writer/scripts/scan_note_quality.py --vault "{{VAULT_ROOT}}"`; exit code 1 (hard failure) blocks completion. After it passes, update `02vault/_index/文献索引.md` (`方法段` column) and `02vault/_index/笔记重写状态.md`; do not accept a batch on the basis of subagent/batch reports alone.

## Knowledge checks

When Knowledge is updated or re-evaluated, run the Knowledge validator `research-vault-knowledge-maintainer/scripts/validate_research_vault_knowledge.py --vault {{VAULT_ROOT}}` **if it is available**, and require exit code 0. This validator is **not bundled with this repository** (it is an optional, user-provided tool); when it is absent, perform the checks below manually. Inspect the resulting checks for:

- Knowledge source links, claim/gap sidecars and statement drift;
- source mismatch, embedded machine metadata, raw key leakage and template/schema compliance;
- evidence counts, identity resolution, duplicate/alias conflicts and relation calibration.

`fulltext_verified` remains invalid unless the particular claim has the chain Note → declared `fulltext_path` → targeted Fulltext verification. A failed contract yields `VALIDATION_FAILED`, not success.
