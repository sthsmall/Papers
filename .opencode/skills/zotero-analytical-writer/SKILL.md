---
name: zotero-analytical-writer
description: "使用 Zotero metadata、批注和 MinerU Fulltext，严格按 {{VAULT_ROOT}}\\模板\\论文精读模板.md 创建或更新 ResearchVault 中文精读笔记，并确保 Zotero 链接、公式与原文引用真实可追溯。"
---

# Zotero Analytical Writer

## Canonical template

For every Note creation or content update, read `{{VAULT_ROOT}}\模板\论文精读模板.md` first and use it as the sole structural authority. Start a new Note by copying that template; for an existing Note, update it in place and normalize its body to the template rather than introducing a parallel structure.

Keep the visible section order exactly as follows:

`基本信息 → 一句话摘要 → 论文贡献 → 任务与问题 → 方法（方法 0 总体框架 + 方法 1/2/3… 分块） → 评测与数据 → 主要发现 → 关联精读笔记 → 我的判断 → 开源与复现（可选）`

Keep the template's table, field labels, heading levels, and frontmatter fields. Replace every retained placeholder with verified content; remove unused optional formula blocks, surplus finding/quote pairs, and placeholder related-note links. Do not add legacy headings such as `研究对象`, `研究方法`, `数据来源`, `研究结论`, `研究对象与问题`, `整体流程`, `数据与证据定位`, `局限与后续问题`, or `Zotero信息`. 方法的"局限"信息放进方法块内与`我的判断`，数据缺陷放进`评测与数据`与`我的判断`。

## 职责与语料顺序

Writer 只负责分析层：`metadata + annotations + MinerU Fulltext + 必要时 PDF → 中文 analytical note`。

- Fulltext 是原文证据，分析笔记是中文理解层；不得把二者混为一谈。
- 保留现有的 `task`、`paradigm`、`data_scale`、`method_summary`、`key_metric`、`key_result`、`relevance`、中文逻辑重构、学术垃圾过滤、公式防乱码、Zotero URI 和 Dataview 刷新逻辑。
- 不负责 PDF→MinerU；缺全文时交给 `zotero-fulltext-archiver`，不要自行伪造原文。
- 若已有正式 Fulltext，先复用并校验，不因 Note 模板修整而重新运行 MinerU。

## Knowledge handoff contract

The Analytical Note is the structural-library layer for later Knowledge synthesis; it is not a substitute for the Knowledge Page template. Preserve machine-readable fields and make the following handoff explicit whenever the Note will feed Knowledge:

- distinguish author-reported findings, methods, limitations, and the writer's interpretation;
- retain the exact `zotero_key`, `note_path`, `fulltext_path`, formulas, quotations, and PDF/Fulltext entry points;
- record which conclusions were checked against Fulltext and which remain Note-only;
- never mark a Knowledge claim as `fulltext_verified` merely because the Note contains a summary;
- if a field or conclusion cannot be located in the Note or Fulltext, write “未在当前材料中定位到可核验原文”，not a reconstructed quote or inferred page number.

When a later Knowledge task asks for “all papers”, the Knowledge Maintainer must read the Note's structured fields and the linked Fulltext independently; the Writer must not collapse the two layers into a single unsupported summary.

## Frontmatter 与稳定身份

Keep the template frontmatter (`title`、`aliases`、`tags`、`created`、`source`、`author`、`year`、`task`、`paradigm`、`data_scale`、`method_summary`、`key_metric`、`key_result`、`relevance`) and replace its placeholders with verified values. Add the following identity and navigation fields after the template fields when the values are known:

```yaml
type: literature-note
zotero_key: "Q22PFLNV"
pdf_key: "4RMSR7ZR"
doi: "..."
collection: "创新经济地理"
note_path: "论文库/创新经济地理/论文标题.md"
fulltext_path: "fulltext/创新经济地理/Q22PFLNV.md"
```

Do not batch-rewrite untouched historical Notes. When updating a specified Note, normalize that same file to the template and preserve verified content and stable identity; never create a duplicate Note. Add only confirmable fields and fulltext entry points. Treat `zotero_key` as the primary key and `pdf_key` as the attachment key. Prefer `note/<collection>/` for new Notes while continuing to support the Vault's current `论文库/` paths.

## 原文引用规则

- “主要发现 + 原文引用”中的原文必须真实出现在 MinerU Fulltext 或 Original PDF。
- 严禁根据中文摘要反向生成英文 quote；定位不到时写“未在当前全文中定位到可核验原句”。
- 引用要保留必要上下文，检查否定、条件、稳健性限定、假设和局限。
- PDF 页码只有在可靠映射或实际 PDF 验证后才写入 `zotero://open-pdf/...?...page=` 或写入“PDF 第 n 页”；否则保留 Fulltext 链接并写“PDF 页码未验证”。不能因为 Fulltext 的 `page_mapping: unknown` 就猜页码，也不能因为页码未知而阻止通过原 PDF 直接核验引文。
- 结论区每一条“主要发现”都要紧邻至少一条真实原文引用；先在 MinerU Fulltext 定位，再在 Original PDF 核对上下文、否定、条件、稳健性和页码。找不到原句时明确写“未在当前全文中定位到可核验原句”，不得反向生成 quote。

## 内容与格式约束

- `task` 概括研究任务（输入输出对象）；`paradigm` 定位范式；`data_scale`、`method_summary`、`key_metric`、`key_result`、`relevance` 必须来自真实材料，不复制大段摘要。
- `论文贡献` 每条对应论文自述贡献（反查 Abstract/引言），不要发明贡献条目。
- 方法区按论文实际方法数量组织成并列的"方法 1/方法 2/…"分块；纯单方法论文可退化为一段方法概述。每块至少含"解决的问题 + 关键设计 + 设计动机"，公式与消融证据按需取舍。
- 过滤作者地址、单位、邮编、邮箱、基金号和排版垃圾；数据与方法缺失时如实说明。
- 公式仅在原文可靠时保留；乱码或残片不强行解释，也不为占位符生成符号拆解。
- 写入前检查 YAML、美元符号配对、`zotero://select/...` 和 PDF/Fulltext 入口。
- 写入前检查标题层级、模板占位符是否清除、结论是否成对、公式是否闭合，以及 `fulltext_path` 与 Note↔Fulltext 双向入口是否存在。
- `关联精读笔记` 只保留与研究问题、方法或结论存在直接关系的真实 Note；没有可确认的关联时，保留章节说明但移除示例链接。

## 写入与索引

1. 先判定是新建还是更新指定 Note；两种情况都先读取当前模板。更新时允许重排正文以匹配模板，但不得改变稳定身份或制造重复 Note。
2. 在基本信息区的链接行加入 `全文 Markdown：[[fulltext/<collection>/<zotero_key>]]`（路径存在时），并保留可验证的 Zotero 入口。
3. 新建论文笔记时才刷新四个根 Dataview 索引；更新既有 Note 不触发全库批量重写，但若标题、路径或索引字段变化，定向刷新受影响索引。
