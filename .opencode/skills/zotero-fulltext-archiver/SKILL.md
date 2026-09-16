---
name: zotero-fulltext-archiver
description: "将已有 Zotero PDF 或历史 MinerU 输出归档为可追踪的 ResearchVault Fulltext Markdown：先复用已成功的 MinerU 链路，再写入统一 frontmatter、整理安全图片路径、保留页面映射并执行只读校验。此技能不做中文总结、不改写论文正文、不负责用户检索。"
---

# Zotero Fulltext Archiver

## Batch 6D production safeguards (Windows CPU / MinerU 3.x)

When a validated Zotero PDF must be run through MinerU on the current Windows
CPU environment, use an ASCII-only *working copy* in a scoped temporary run
directory. The Zotero attachment remains read-only. Record the source and
working-copy SHA-256 values and do not invoke MinerU until they match.

Use the explicitly validated `pipeline` backend for this environment. This is
an environment-specific fallback, not a general claim that the hybrid backend
is unsuitable. Give a complete article a hard limit of at least 60 minutes.
A no-progress stop may be used only after 10--15 minutes during which stdout,
stderr, output files, and process CPU time have all remained inactive. Abort
for persistently available RAM below 2 GB only after a sustained observation,
and record the resource samples.

Every invocation must stream timestamped stdout and stderr to the run
directory, record stage transitions, and clean only the MinerU CLI tree and
new `mineru.cli.fast_api` descendants created by that invocation. Recheck for
those exact processes after cleanup; never terminate unrelated Python work.

Archive only after the raw Markdown gate passes: non-empty full-document
front/middle/end samples, source identity, image-file/reference checks, and
no missing image targets. Formal archiving may add schema frontmatter and
rewrite image paths, but must otherwise preserve the extracted body verbatim.

Before invoking MinerU, inspect the formal `03fulltext` path by `zotero_key`.
If a formal Fulltext already has matching `zotero_key`/`pdf_key`, valid
frontmatter, resolved images, and a non-empty article body, reuse it and run
targeted validation. A Note-template repair is not a reason to rerun MinerU.
If `page_mapping` is `unknown`, retain that value; the Analytical Writer may
still verify quotation pages directly against the read-only Original PDF.

## 职责边界

执行：`Zotero PDF → MinerU → Fulltext Markdown → 图片整理 → metadata → Note 关联 → validation`。

不执行中文翻译、分析笔记写作、批量检索或 Zotero 数据库改写。

## 1. 先确认实际 MinerU 环境

**不要重复安装 MinerU**。先搜索 `{{VAULT_ROOT}}`、`{{RESEARCH_DIR}}` 和相关项目中的 `MinerU`、`mineru`、`magic-pdf`、批处理脚本、配置和历史输出。先检查是否已有可用的 MinerU（可执行文件 / CLI / Python 模块 / 历史输出），只有确认不存在时才进入 1.1。

### 1.1 确认未安装时：必须先询问用户是否安装（硬性要求）

若穷尽搜索后确认环境中**没有可用的 MinerU**（`Test-Path`、命令探测、模块探测均失败）：

1. **必须立即停下来，明确询问用户"是否安装 MinerU"**，并给出获取方式（指向仓库 `README.md` 的「MinerU 安装与模型下载」）。
2. **在用户明确同意之前，绝对不得执行任何安装动作**——不得 `pip install` / `uv pip install`、不得运行 `mineru-models-download`、不得下载便携版、不得改动 `mineru.json` 或模型缓存。
3. 用户同意后 → 按 README 指引安装；安装完成后回到本流程第 1 节重新确认环境，再继续归档。
4. 用户拒绝、或环境无法满足（无网络 / 无 GPU / 磁盘不足 / 无权限）→ **不得伪造、不得静默跳过该步**；转为 `FULLTEXT_DEFERRED` 状态并如实记录原因，交由 `research-vault-ingest-orchestrator` 走 Note-only 降级路径（此时任何结论都不得标记为 `fulltext_verified`）。

> **禁止行为**：未经询问就安装；未经用户同意就下载模型；静默跳过后声称已归档；用模型生成的"全文"冒充 MinerU 输出；在 `03fulltext` 无产物的情况下报告 `COMPLETE`。
>
> **不适用场景**：若用户在本次会话中已明确授权安装，或已有可用 MinerU（含历史输出可直接复用），则无需再次询问，直接按第 2、3 节处理。

当前已发现的可复用调用链是（**可选：批量脚本需自备，本仓库不附带**；若脚本缺失，改为直接按 `AGENTS.md` 调用 MinerU CLI）：

`{{RESEARCH_DIR}}\mineru_batch_runner.py` → `{{MINERU_EXE}}` → 系统临时输出目录 → `{{ARCHIVE_ROOT}}\mineru-staging\`。批量输出只能作为外部暂存；逐篇补齐 frontmatter、图片路径和 Note 关联并验证后，才复制到 `{{VAULT_ROOT}}\03fulltext\<collection>\`。

历史 `MinerU_test` 的页码辅助文件已归档到 `{{ARCHIVE_ROOT}}\2026-08-10\MinerU_test\`；如需核验历史页码映射可定向读取，但不足以证明所有论文都可可靠映射。

## 2. 归档路径

正式全文：

```text
{{VAULT_ROOT}}\03fulltext\<collection>\<zotero_key>.md
{{VAULT_ROOT}}\03fulltext\<collection>\images\<zotero_key>\<image-file>
```

旧的 `MinerU_batch` 已归档到 `{{ARCHIVE_ROOT}}\2026-08-10\MinerU_batch\`，不作为运行时输入或正式全文检索目录。当前 Vault 的分析笔记仍位于 `论文库/` 时，不移动它们；仅在全文 frontmatter 中写准确的 `note_path`。

## 3. 优先迁移旧结果

若 `MinerU_batch` 已有与 `zotero_key` 唯一对应的 Markdown 和图片：

1. 确认 Zotero 主键、PDF 键、标题和 Collection。
2. 将旧 Markdown 复制到正式 `03fulltext/<collection>/<zotero_key>.md`；分析笔记中的 Obsidian 链接仍使用 `fulltext/<collection>/<zotero_key>`。
3. 将图片复制到 `images/<zotero_key>/`，不得使用完整论文标题作为目录名。
4. 将原有图片引用改为相对于 Fulltext Markdown 的安全路径，例如 `![](<images/Q22PFLNV/image.jpg>)`。
5. 逐一检查每个本地图片引用真实存在；有缺失时不能报告成功。

若没有可复用结果，才调用已确认的 MinerU 可执行文件处理单篇 PDF；不得批量重跑整个库。

## 4. Fulltext Frontmatter

每个正式全文顶部至少包含：

```yaml
---
type: literature-fulltext
title: "..."
zotero_key: "Q22PFLNV"
pdf_key: "4RMSR7ZR"
doi: "..."
collection: "创新经济地理"
note_path: "论文库/创新经济地理/论文标题.md"
fulltext_path: "03fulltext/创新经济地理/Q22PFLNV.md"
zotero_item: "zotero://select/library/items/Q22PFLNV"
zotero_pdf: "zotero://open-pdf/library/items/4RMSR7ZR"
source_type: mineru
page_mapping: unknown
---
```

Vault 内部路径统一使用 `/`。缺失的 DOI 可留空，但不得伪造。

## 5. 原文与页码规则

- MinerU Markdown 是证据档案：不翻译、总结、润色、重写、删减或插入模型生成内容。
- 允许的后处理仅包括 frontmatter、机器定位标记和安全图片路径修复。
- 只有当 `content_list.json`/`middle.json` 等信息与真实 PDF 通过单篇测试可靠对应时，才写 `page_mapping: reliable` 或 `<!-- pdf_page: N -->`。
- 0-based/1-based 转换必须记录并用真实 PDF 验证；无法可靠映射时写 `page_mapping: unknown`，不要猜 page。

## 6. 关联与校验

归档完成后：

1. 分析笔记补 `fulltext_path`，并可增加 `[[fulltext/<collection>/<zotero_key>]]` 入口；不因全文归档重写整篇笔记，模板化重排由 `zotero-analytical-writer` 单独负责。
2. Fulltext 补 `note_path`，确认双方 `zotero_key`、`pdf_key` 一致。
3. 运行链接校验脚本（**可选，需自备**）：`{{RESEARCH_DIR}}\zotero_batch\validate_research_vault_literature_links.py`；脚本缺失时改为逐项核对下一条的双向链接要求，只报告，不自动删除。
4. 只有 PDF、Fulltext、图片、Note、链接均有效时，才向 Collection Manager 报告 COMPLETE。
