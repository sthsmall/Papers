---
name: paper-registry
description: "本地论文身份与元数据登记：为 PDF 生成稳定 paper_id，维护 Vault 的 02vault/_index/papers.tsv，校验 PDF/Fulltext/Note 路径；不依赖 Zotero。Use when adding a paper without Zotero, resolving a local PDF's identity, or validating the paper registry."
---

# Paper Registry

本地优先的论文身份层。身份只由 `paper_id` + 本地 `pdf_path` 决定，不使用 Zotero。

## 职责

- 给本地 PDF 分配稳定 `paper_id`
- 维护 `{{VAULT_ROOT}}\02vault\_index\papers.tsv`
- 校验 PDF / Fulltext / Note 路径与 ID 唯一性
- 给 Fetcher、Fulltext Archiver、Writer、Orchestrator 提供身份

不负责：MinerU 转换、全文写作、知识整理、文献检索。

## paper_id 规则

优先级：

1. 已有 8 位 key（如 `2Q48RTFR`）→ 直接沿用
2. arXiv → `arxiv_2409.18839`
3. DOI → `doi_10.1109_tgrs.2026.3675693`（非法字符替换为 `_`）
4. 其余 → `pdf_<PDF SHA-256 前 12 位>`

> 不重命名已有 `03fulltext/<collection>/<file>.md`；`paper_id` 是逻辑主键，路径可以不同。

## 命令

```powershell
$py = "python"   # 可用项目 Python
$reg = "{{VAULT_ROOT}}\02vault\_index\papers.tsv"

# 1) 解析本地 PDF（不写 registry）
& $py .opencode\skills\paper-registry\scripts\paper_registry.py resolve `
  --pdf "{{RESEARCH_DIR}}\papers\paper.pdf" --collection MOT

# 2) 登记/更新（按 paper_id 幂等）
& $py .opencode\skills\paper-registry\scripts\paper_registry.py register `
  --registry $reg `
  --pdf "{{RESEARCH_DIR}}\papers\paper.pdf" `
  --collection MOT --title "..." --authors "..." --year 2026 --venue "..."

# 3) 校验
& $py .opencode\skills\paper-registry\scripts\paper_registry.py validate `
  --registry $reg --vault "{{VAULT_ROOT}}"

# 4) 列表
& $py .opencode\skills\paper-registry\scripts\paper_registry.py list `
  --registry $reg --collection MOT
```

`resolve` 会读取 PDF 内嵌 Title/Author（若 `pypdf` 可用），否则留空；标题、作者、年份、venue 可由用户显式传入。**不要根据标题猜 DOI/arXiv ID。**

## papers.tsv

列：

```text
paper_id  title  authors  year  venue  doi  arxiv_id  collection
pdf_path  fulltext_path  note_path  status  page_mapping
```

- `status`：`PDF_ONLY` / `FULLTEXT_OK` / `NOTE_OK` / `COMPLETE` / `DEFERRED`
- `page_mapping`：`page_maps/<paper_id>.json` 或 `unknown`

## 与其他 skill 的衔接

- `zotero-data-fetcher`：优先读 registry；无 registry 记录时用 `resolve` 生成。
- `zotero-fulltext-archiver`：用 `paper_id` + `pdf_path`。
- `zotero-analytical-writer`：从 registry/fulltext frontmatter 取元数据；批注可选（本地）。
- `research-vault-ingest-orchestrator`：身份门改为 `paper_id` + PDF 存在。

## 约束

- 不移动、不重命名已有论文 PDF/Fulltext/Note。
- 不把标题当唯一主键；冲突时报告，不覆盖。
- 不写入任何外部文献管理器；身份与元数据只存在 papers.tsv。
- `papers.tsv` 是本地状态文件；批量改动前先 `validate`，改后复验。
