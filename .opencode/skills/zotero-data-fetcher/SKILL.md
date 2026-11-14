---
name: zotero-data-fetcher
description: "根据本地 PDF/paper_id（默认）或 Zotero Item Key（可选 legacy）提取元数据、PDF 路径、批注和 Fulltext，并为归档或分析写作提供可追踪的原始数据。此技能不翻译、不总结、不替代全文证据。"
---

# Zotero Data Fetcher

## 职责

只负责找到论文元数据、PDF 和 Fulltext；不负责 MinerU 转换、中文分析笔记或用户检索。默认使用本地 PDF + `paper_id`，Zotero 只作为可选 legacy。

## 统一输出字段

尽可能输出以下字段，并保持同名：

`paper_id`、`pdf_path`、`title`、`authors`、`year`、`venue`、`doi`、`arxiv_id`、`collection`、`note_path`、`fulltext_path`、`annotations`、`zotero_key`（legacy）。

`paper_id` 是默认主键；`zotero_key`/`pdf_key` 只用于旧数据兼容。

## 模式 0：本地 PDF（默认）

1. 先查 `{{PAPER_REGISTRY}}` 的 `paper_id`/`pdf_path`；没有记录时用 `paper-registry resolve` 生成。
2. 元数据优先级：registry → PDF 内嵌 Title/Author → arXiv/DOI 查询 → 用户显式提供；不要用标题猜 DOI/arXiv。
3. 返回 `paper_id`、`pdf_path`、`title`、`authors`、`year`、`venue`、`doi`、`arxiv_id`、`collection`。
4. 批注可选：存在 `02vault/<collection>/annotations/<paper_id>.md` 时读取；不存在不视为失败。

## 模式 A：首次论文处理（Zotero legacy）

1. 读取 Zotero `prefs.js`，确认生效的数据目录；按当前可用的 Zotero connector/API 或现有提取脚本查询父条目。
2. 获取标题、作者、年份、DOI、所属 Collection、父条目 Key。
3. 在子附件中锁定 PDF，记录附件 Key 和真实本地路径；不存在 PDF 时明确失败原因。
4. 提取批注、Notes 和 `.zotero-ft-cache`（若存在），但保持原始语言和原始内容。
5. 将 `PDF path + metadata` 交给 `zotero-fulltext-archiver`；将原始语料交给 `zotero-analytical-writer`。

## 模式 B：已有论文证据查询

- 若分析笔记存在 `fulltext_path`，先返回并使用该全文路径。
- 精确正文证据优先级为：**MinerU Fulltext → Original PDF verification → `.zotero-ft-cache` fallback**。
- 批注可用于理解阅读重点，但不能替代正文原文。
- 缓存或批注缺失不等于 PDF 缺失；分别记录 `cache_found`、`pdf_found` 和 `annotations_found`。

## 约束

- 不根据标题猜 `paper_id`/Item Key；同名或多条候选必须报告冲突。
- 不修改 Zotero 数据库，不移动原 PDF，不覆盖无关文件。
- 默认不要求 Zotero；只有用户明确需要旧库、批注或 BibTeX 时才进入 Zotero 模式。
- 不在 Fetcher 阶段翻译、总结或套用中文模板。
