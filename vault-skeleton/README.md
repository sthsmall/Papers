# Vault 骨架（vault-skeleton）

本目录是 ResearchVault 的**最小可用骨架**：把这里的目录/文件复制到 `{{VAULT_ROOT}}`，即可让 `.opencode/skills/` 下的 Zotero 工作流跑起来。

## 复制方式

```powershell
# 1. 复制骨架（保留已有文件，不覆盖）
robocopy vault-skeleton "{{VAULT_ROOT}}" /E /XC /XN /XO
# 2. 复制写作模板（skill 依赖 <VAULT_ROOT>\模板\）
xcopy templates "{{VAULT_ROOT}}\模板\" /E /I
```

> `{{VAULT_ROOT}}` 请替换为你的实际路径（见根目录 `AGENTS.example.md`）。

## 骨架包含

| 路径 | 作用 |
| --- | --- |
| `01knowledge/index.md` | Knowledge Wiki 导航索引（知识页入口） |
| `01knowledge/log.md` | append-only 处理日志（入库 / 知识库更新事件） |
| `01knowledge/.meta/claims/` | claim sidecar（JSON），格式见 `research-vault-knowledge-maintainer/references/knowledge-schema.md` |
| `01knowledge/.meta/gaps/` | 证据缺口 sidecar |
| `02vault/_index/文献索引.md` | Analytical Notes 总索引（ingest 时维护） |
| `03fulltext/` | MinerU 全文归档（按 `<collection>/<zotero_key>.md`） |
| `10_Daily/` | evil-read-arxiv 每日/年度推荐笔记 |
| `20_Research/Papers/` | evil-read-arxiv 在线分析笔记 |
| `99_System/Config/research_interests.yaml` | 在线发现层的研究兴趣配置（从 `evil-read-arxiv/config.example.yaml` 生成） |
| `tools/` | 可选工具脚本目录（如 `run_mineru_production.py`，需自备） |

## 与仓库其他部分的关系

- 写作模板在仓库根目录 `templates/`（本骨架不重复存放，避免版本漂移）。
- 索引格式由对应 skill 维护，本骨架只提供初版空模板。

## 可选维护索引

`research-vault-literature-retrieval` 会按顺序读取 `02vault/_index/` 下**已存在**的以下页面（缺失则跳过）：

1. `文献索引.md`（骨架已提供）
2. `研究主题索引.md`（可选，自行创建）
3. `研究方法索引.md`（可选，自行创建）
4. `字段补全检查.md`（可选，自行创建）
