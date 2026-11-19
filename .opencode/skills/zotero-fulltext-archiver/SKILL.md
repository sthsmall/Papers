---
name: zotero-fulltext-archiver
description: "将本地 PDF（默认，paper_id + pdf_path）或历史 MinerU 输出归档为可追踪的 ResearchVault Fulltext Markdown：先复用已成功的 MinerU 链路，再写入统一 frontmatter、整理安全图片路径、保留页面映射并执行只读校验。Zotero 为可选 legacy。此技能不做中文总结、不改写论文正文、不负责用户检索。"
---

# Zotero Fulltext Archiver

## MinerU 4.1.5 primary / 3.4.0 fallback (Windows GPU)

Default: run the wrapper
`.opencode/skills/zotero-fulltext-archiver/scripts/mineru_parse.ps1`
with `-Tier standard`. It uses MinerU 4.1.5 (`mineru-kit parse --format zip`)
and checks `nvidia-smi` free VRAM first: below **12 GB** it exits with code
**75** without touching the GPU. Do not bypass the guard unless the user
explicitly asks; the GPU is shared with the user's experiments.

Use an ASCII-only *working copy* in a scoped temporary run directory. The
Zotero attachment remains read-only. Record the source and working-copy
SHA-256 values and do not invoke MinerU until they match. Give a complete
article a hard limit of at least 30 minutes (4.1.5 is usually much faster);
a no-progress stop may be used only after 10--15 minutes during which stdout,
stderr, output files, and process CPU time have all remained inactive.

4.1.5 writes a zip containing `markdown.md`, `middle_json.json`,
`structured_content.json`, and `images/`. Archive the Markdown body verbatim;
only frontmatter, safe image paths, and page-map references may be changed.

Use the 3.4.0 fallback (`-Fallback340`, or the old `mineru.cli.client
-b hybrid-engine --effort high` command) only when 4.1.5 fails, or when
figure-internal text / appendix qualitative images are required. The old
`mineru.cli.fast_api` cleanup rule applies only to that fallback: stream
timestamped stdout/stderr, record stage transitions, and stop only the exact
MinerU CLI tree created by that invocation; never terminate unrelated Python
work.

Archive only after the raw Markdown gate passes: non-empty full-document
front/middle/end samples, source identity, image-file/reference checks, and
no missing image targets. Formal archiving may add schema frontmatter and
rewrite image paths, but must otherwise preserve the extracted body verbatim.

Before invoking MinerU, inspect the formal `03fulltext` path by `paper_id`.
If a formal Fulltext already has matching `paper_id`/`pdf_path`, valid
frontmatter, resolved images, and a non-empty article body, reuse it and run
targeted validation. A Note-template repair is not a reason to rerun MinerU.
If `page_mapping` is `unknown` and a 4.1.5 `structured_content.json` exists,
build `page_maps/<paper_id>.json` and verify 2--3 quotes; otherwise retain
`unknown`. The Analytical Writer may still verify quotation pages directly
against the read-only Original PDF.

## 职责边界

执行：`本地 PDF → MinerU → Fulltext Markdown → 图片整理 → metadata → Note 关联 → validation`（Zotero 可选 legacy）。

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
> **询问只在首次确认缺失时发生一次**：一旦环境中 MinerU 已被确认可用（或用户已明确授权安装、已完成安装），后续所有调用**直接使用，不再重复询问**。每次任务开始时只需一次轻量探测（`Test-Path` / 命令探测）；探测成功即直接进入后续步骤。
>
> **不适用场景**：若用户已授权安装、或已有可用 MinerU（含历史输出可直接复用），则无需询问，直接按第 2、3 节处理。

当前默认调用链：

`scripts/mineru_parse.ps1`（MinerU 4.1.5，`--tier standard --format zip`）→ 系统临时输出目录 → 解压/整理 → `{{VAULT_ROOT}}\03fulltext\<collection>\`。批量输出只能作为外部暂存；逐篇补齐 frontmatter、图片路径和 Note 关联并验证后，才复制。

3.4.0 fallback 仍可用 `{{MINERU340_ROOT}}\WPy64-312101\python\python.exe -m mineru.cli.client -b hybrid-engine --effort high`，但只用于 4.1.5 失败或需要图内文字/附录定性图的场景。

历史 `MinerU_test` 的页码辅助文件已归档到 `{{ARCHIVE_ROOT}}\2026-08-10\MinerU_test\`；如需核验历史页码映射可定向读取，但不足以证明所有论文都可可靠映射。

## 2. 归档路径

正式全文：

```text
{{VAULT_ROOT}}\03fulltext\<collection>\<paper_id>.md
{{VAULT_ROOT}}\03fulltext\<collection>\images\<paper_id>\<image-file>
```

旧的 `MinerU_batch` 已归档到 `{{ARCHIVE_ROOT}}\2026-08-10\MinerU_batch\`，不作为运行时输入或正式全文检索目录。当前 Vault 的分析笔记仍位于 `论文库/` 时，不移动它们；仅在全文 frontmatter 中写准确的 `note_path`。

## 3. 优先迁移旧结果

若历史 `MinerU_batch` 已有与 `paper_id` 唯一对应的 Markdown 和图片：

1. 确认 `paper_id`、本地 `pdf_path`、标题和 Collection。
2. 将旧 Markdown 复制到正式 `03fulltext/<collection>/<paper_id>.md`；分析笔记中的 Obsidian 链接仍使用 `fulltext/<collection>/<paper_id>`。
3. 将图片复制到 `images/<paper_id>/`，不得使用完整论文标题作为目录名。
4. 将原有图片引用改为相对于 Fulltext Markdown 的安全路径，例如 `![](<images/Q22PFLNV/image.jpg>)`。
5. 逐一检查每个本地图片引用真实存在；有缺失时不能报告成功。

若没有可复用结果，才用 `scripts/mineru_parse.ps1`（4.1.5）处理单篇 PDF；不得批量重跑整个库。仅当 4.1.5 失败、或确需图内文字/附录定性图时，才加 `-Fallback340` 调 3.4.0。

## 4. Fulltext Frontmatter

每个正式全文顶部至少包含：

```yaml
---
type: literature-fulltext
title: "..."
paper_id: "Q22PFLNV"
pdf_path: "D:/papers/Q22PFLNV.pdf"
zotero_key: "Q22PFLNV"   # 可选，legacy only
doi: "..."
collection: "创新经济地理"
note_path: "02vault/创新经济地理/论文标题.md"
fulltext_path: "03fulltext/创新经济地理/Q22PFLNV.md"
source_type: mineru-4.1.5
page_mapping: "page_maps/Q22PFLNV.json"
---
```

`paper_id` 是默认主键；`zotero_key`（legacy）、`zotero_item`、`zotero_pdf` 只在旧数据中保留。新论文不需要 Zotero。

Vault 内部路径统一使用 `/`。缺失的 DOI 可留空，但不得伪造。

## 5. 原文与页码规则

- MinerU Markdown 是证据档案：不翻译、总结、润色、重写、删减或插入模型生成内容。
- 允许的后处理仅包括 frontmatter、机器定位标记和安全图片路径修复。
- **4.1.5**：`structured_content.json` 的 `pages[].page_idx` 是 0-based，`page_number = page_idx + 1`，block bbox 为归一化坐标。用 `scripts/build_page_map.py` 生成 `page_maps/<paper_id>.json`，再写 `page_mapping: "page_maps/<paper_id>.json"`；先用 2--3 个 quote 对照真实 PDF 验证。
- **3.4.0 fallback**：只有当 `content_list.json`/`middle.json` 与真实 PDF 通过单篇测试可靠对应时，才写 `page_mapping: reliable` 或 `<!-- pdf_page: N -->`。
- 0-based/1-based 转换必须记录并用真实 PDF 验证；无法可靠映射时写 `page_mapping: unknown`，不要猜 page。

生成 4.1.5 页图并回填 frontmatter：

```powershell
python ".opencode\skills\zotero-fulltext-archiver\scripts\build_page_map.py" `
  --structured "<MinerU输出>\structured_content.json" `
  --out "{{VAULT_ROOT}}\03fulltext\<collection>\page_maps\<paper_id>.json" `
  --fulltext "{{VAULT_ROOT}}\03fulltext\<collection>\<paper_id>.md" `
  --update-frontmatter
```

## 5.1 多面板图排版

MinerU 把一张多面板图拆成多个独立图片块，并按块顺序输出；直接落盘会得到 4 张竖排小图（且常是列优先顺序）。归档后跑一次排版：

```powershell
python ".opencode\skills\zotero-fulltext-archiver\scripts\arrange_figure_rows.py" --dry-run
python ".opencode\skills\zotero-fulltext-archiver\scripts\arrange_figure_rows.py" --apply
```

合并条件（保守，只处理无歧义的情况）：

- 连续 ≥2 个图片行，且都来自同一页 `page_N_*`；
- 纵向共享同一带（重叠 ≥ 中位高度 60%），横向互不重叠；
- 合并为一行 CSS grid，顺序按 bbox 的 x 从左到右，列宽按 bbox 宽度比例；自然宽度 <500 px 的图加 `max-width` 防止放大发虚。

跨页连排、混合尺寸（如整页拼图）、纵向堆叠的两张不同图一律保持原样。记录写入 `fulltext_image_layout_log.tsv`。图片正文内容、图片文件与图注文字都不改，只改引用方式，因此仍满足“正文逐字保留”。

## 6. 关联与校验

归档完成后：

1. 分析笔记补 `fulltext_path`，并可增加 `[[fulltext/<collection>/<paper_id>]]` 入口；不因全文归档重写整篇笔记，模板化重排由 `zotero-analytical-writer` 单独负责。
2. Fulltext 补 `note_path`，确认双方 `paper_id` 一致；`zotero_key`/`pdf_key` 只作旧数据兼容。
3. 运行链接校验脚本（**可选，需自备**）：`{{RESEARCH_DIR}}\zotero_batch\validate_research_vault_literature_links.py`；脚本缺失时改为逐项核对下一条的双向链接要求，只报告，不自动删除。
4. 只有 PDF、Fulltext、图片、Note、链接均有效时，才向 Collection Manager 报告 COMPLETE。
