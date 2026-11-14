# 去 Zotero 化：ResearchVault 论文身份与本地 PDF 工作流

> 状态：**P0/P1/P2 已实施（2026-11-15）；24 篇 key_pending 待归档；Zotero 已降为可选 legacy**
> 日期：2026-11-15  
> 目标：停止把 Zotero 作为必选依赖，用「本地 PDF + paper_id + 本地 registry」完成入库、全文、笔记和检索。

## 0. 实施状态

- 已建 `{{VAULT_ROOT}}\02vault\_index\papers.tsv`：103 行，103 个唯一 `paper_id`，102 个本地 PDF，1 个 `DEFERRED`。
- 已给 103 篇 Fulltext + 102 篇 Note 增加 `paper_id` / `pdf_path`；旧 `zotero_key` 保留为 legacy。
- 已新增 `paper-registry` skill 与 `paper_registry.py`（resolve/register/validate/list）。
- 已把 fetcher / archiver / writer / collection-manager / orchestrator 改为本地 PDF 默认；`zotero` 标为 optional legacy。
- `papers.tsv` 校验：103 行、103 唯一、0 错误。
- 剩余：24 篇 key_pending 已有 `paper_id` + 本地 PDF，可直接用 4.1.5 归档；1 篇无 PDF 保持 `DEFERRED`。

## 1. 现状审计

| Skill | Zotero 用途 | 依赖强度 | 处理建议 |
|---|---|---|---|
| `zotero` | 本地 API、搜索、BibTeX、Connector | 独立 | **保留为可选 legacy**，默认流程不再调用 |
| `zotero-data-fetcher` | 由 Item Key 取元数据、PDF、批注、Notes | 高 | **替换**为 `paper-data-fetcher`（本地 PDF/DOI/arXiv + registry） |
| `zotero-fulltext-archiver` | `zotero_key`/`pdf_key` 作为全文主键 | 高 | **解耦**：`paper_id` + 本地 `pdf_path`；旧字段保留兼容 |
| `zotero-collection-manager` | 按 Zotero Collection 调度 | 高 | **替换**为 `vault-ingest-manager`（目录 + registry 状态） |
| `zotero-analytical-writer` | 元数据、批注、Zotero 链接 | 中 | **解耦**：Fulltext + PDF + 可选 `annotations.md`；不再要求 Zotero |
| `research-vault-ingest-orchestrator` | 身份门 `zotero_key`/`pdf_key` | 高 | 身份门改为 `paper_id` + `pdf_path`；移除 Zotero gate |
| `research-vault-literature-retrieval` | 只引用 Fulltext/PDF 路径 | 低 | 改字段名与链接说明即可 |
| `research-vault-knowledge-maintainer` | 只引用 Fulltext/PDF 路径 | 低 | 支持 `paper_id` 即可 |
| `start-my-day` / `conf-papers` / `paper-search` | 无 | 无 | 不变 |

结论：**Zotero 不是检索/知识层的硬依赖，主要卡在身份、PDF 获取、元数据和 Collection 调度四处。**

## 2. 目标架构

```text
本地 PDF (research/papers 或 Zotero storage 旧文件)
  → paper_id 解析/登记 (paper-registry)
  → MinerU 4.1.5 (fulltext + page map)
  → Analytical Note
  → Knowledge / Retrieval
```

### 2.1 paper_id

优先级从高到低：

1. **沿用现有 8 位 key**（如 `2Q48RTFR`）作为 `paper_id`，保证 103 篇已有路径不变。
2. arXiv：`arxiv_2409.18839`。
3. DOI：`doi_10.1109_tgrs.2026.3675693`（非法字符替换为 `_`）。
4. 都没有：`pdf_<PDF SHA-256 前 12 位>`。

> 现有 `zotero_key` 不删除，作为 `legacy_zotero_key` 保留；新流程只读 `paper_id`。

### 2.2 本地 registry

建议位置：`{{VAULT_ROOT}}\02vault\_index\papers.tsv`（人可读、机器可解析）。

| 字段 | 说明 |
|---|---|
| `paper_id` | 主键 |
| `title` | 标题 |
| `authors` | 作者，分号分隔 |
| `year` | 年份 |
| `venue` | 期刊/会议 |
| `doi` | DOI，可空 |
| `arxiv_id` | arXiv ID，可空 |
| `collection` | 对应 `02vault/<collection>`、`03fulltext/<collection>` |
| `pdf_path` | 本地 PDF 路径（相对 `{{RESEARCH_DIR}}\papers\` 或绝对） |
| `fulltext_path` | 正式全文路径 |
| `note_path` | 分析笔记路径 |
| `status` | `PDF_ONLY` / `FULLTEXT_OK` / `NOTE_OK` / `COMPLETE` / `DEFERRED` |
| `page_mapping` | `page_maps/<paper_id>.json` 或 `unknown` |
| `legacy_zotero_key` | 旧 key，可空 |

### 2.3 Collection

- 不再依赖 Zotero Collection。
- 以 `02vault/<collection>/` 与 `03fulltext/<collection>/` 目录为准；registry 的 `collection` 字段只做索引。
- 新论文由用户指定 collection；未指定时放 `MOT`/`SAM` 等现有分类或 `Unsorted`。

## 3. Skill 改造方案

### 方案 A：渐进式（推荐）

保留现有目录名，增加本地模式，避免一次重命名所有引用：

1. `zotero-data-fetcher` 增加 **Local PDF 模式**：输入 PDF 路径/标题/DOI/arXiv，输出 registry 字段；Zotero 模式保留但默认不调用。
2. `zotero-fulltext-archiver` 增加 `paper_id` + `pdf_path` 输入；`zotero_key` 变可选 legacy。
3. `zotero-analytical-writer` 去掉“必须有 Zotero 元数据/批注”的前置条件；批注改为可选 sidecar。
4. `zotero-collection-manager` 增加 registry 调度模式；Zotero Collection 模式保留为 legacy。
5. `research-vault-ingest-orchestrator` 身份门改为 `paper_id` + `pdf_path`。
6. `zotero` skill 标记 optional，不删除。

### 方案 B：彻底重命名

新建 `paper-registry`、`paper-data-fetcher`、`fulltext-archiver`、`analytical-writer`、`vault-ingest-manager`，旧 `zotero-*` 作为 deprecated wrapper。

优点：命名清晰；缺点：所有 AGENTS/README/交叉引用要改，迁移成本高。建议先做 A，稳定后再重命名。

## 4. 数据迁移

### 4.1 现有 103 篇

- 有 8 位 key 的：`paper_id = zotero_key`，路径不变。
- 9 篇 arXiv key：`paper_id = arxiv_<id>`；全文/笔记路径保持不变，frontmatter 增加 `paper_id`。
- 17 篇无 key：按本地 PDF 文件名/SHA-256 生成 `paper_id`，补 `pdf_path`。
- 不移动、不重命名现有 `03fulltext` 文件；只加字段。

### 4.2 25 篇 key_pending

- 24 篇本地 PDF 已在 `research/papers`；1 篇 `Detect Anything in Real Time` 仍缺 PDF。
- 这 24 篇不再等 Zotero key：分配 `paper_id`，用 4.1.5 归档，生成 page map，再写笔记。
- 1 篇缺 PDF 的保持 `DEFERRED`。

### 4.3 批注

- Zotero 批注不再作为必需输入。
- 如需保留阅读重点，存 `{{VAULT_ROOT}}\02vault\<collection>\annotations\<paper_id>.md`，由 writer 可选读取。
- 旧 Zotero 批注可一次性导出为 Markdown，不阻塞主流程。

## 5. 分阶段执行

| 阶段 | 工作 | 影响 |
|---|---|---|
| P0 | 写 `papers.tsv` schema + `paper_registry.py`（resolve/register/validate） | 新增，不改旧数据 |
| P1 | 给 103 篇 frontmatter 增加 `paper_id`、`pdf_path`；旧 `zotero_key` 保留 | 只加字段，路径不变 |
| P2 | Fetcher 增加 Local PDF 模式；Orchestrator 身份门切换 | 新流程可用 |
| P3 | Fulltext Archiver 接受 `paper_id`/`pdf_path`；跑 24 篇 key_pending | 清掉 key 债务 |
| P4 | Collection Manager 增加 registry 调度；Writer 去掉 Zotero 前置 | 批量流程去 Zotero |
| P5 | 更新 AGENTS/README；`zotero` 标 optional；旧 skill 保留 | 文档收口 |

## 6. 风险与边界

| 风险 | 处理 |
|---|---|
| PDF 元数据质量差（标题/作者缺失） | arXiv/DOI/Crossref 查询 + 用户确认；不猜 |
| 本地 PDF 重名/重复 | SHA-256 去重；registry 唯一约束 |
| 旧 `zotero_key` 与新 `paper_id` 混用 | 明确 `paper_id` 为主键，`legacy_zotero_key` 只读 |
| 现有笔记/全文路径断裂 | 不重命名已有文件；只加字段 |
| 失去 Zotero 批注/Collection | 批注可选 sidecar；Collection 用目录 |
| 引用管理 | 保留 `zotero` skill 可选导出 BibTeX；或改用 DOI/Crossref |

## 7. 需要确认

- [ ] `paper_id` 是否沿用现有 8 位 key（推荐），还是全部重新生成？
- [ ] 是否采用方案 A（保留 skill 名、加本地模式），还是方案 B（彻底重命名）？
- [ ] 是否保留 `zotero_key` 作为 `legacy_zotero_key` 只读字段？
- [ ] `papers.tsv` 放 `02vault/_index/` 还是 `{{RESEARCH_DIR}}`？
- [ ] 24 篇 key_pending 是否立即用 `paper_id` 归档？
- [ ] 是否还需要 BibTeX/引用导出（决定 `zotero` skill 是否保留）？
