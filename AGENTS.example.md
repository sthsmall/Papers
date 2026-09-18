# AGENTS.md（示例 / 模板）

> 把本文件复制为 `AGENTS.md` 后，按下表把占位符替换为你的实际路径。本文件是可提交的脱敏版本，不包含任何个人绝对路径。

## 占位符 → 实际路径映射

本项目 skill（`.opencode/skills/`、`evil-read-arxiv/skills/`）使用可配置占位符。执行相关任务时，请按下表把占位符替换为实际路径。

| 占位符 | 实际路径（请填写） |
| --- | --- |
| `{{VAULT_ROOT}}` | 你的 Obsidian 研究库根目录（含 `01knowledge/`、`02vault/`、`03fulltext/`、`模板/`） |
| `{{ARCHIVE_ROOT}}` | 历史 MinerU / 全文归档目录（可为空） |
| `{{RESEARCH_DIR}}` | 研究工具与论文 PDF 目录（如 `<RESEARCH_DIR>\papers\` 存放论文 PDF） |
| `{{MINERU_EXE}}` | MinerU 可执行文件路径 |

## 使用注意

- 上述目录可能尚未创建。执行 skill 流程前先 `Test-Path` 确认；缺失时向用户确认，不要自动批量创建。
- **MinerU 调用**：绿色便携版需先设置环境变量 `PYTHONPATH=<MinerU根>\src`、`HF_HOME=<MinerU根>\models`、`HF_HUB_OFFLINE=1`、`MINERU_MODEL_SOURCE=modelscope`、`PYTHONUTF8=1`，再执行 `<python> -m mineru.cli.client -p <pdf> -o <out> -b pipeline`。
- **未检测到 MinerU 时的硬性约定**：先搜索既有 MinerU（可执行文件 / CLI / Python 模块 / 历史输出），**不要重复安装**。若确认确实没有可用 MinerU，**必须停下并询问用户"是否安装 MinerU"**，并指向 `README.md` 的「MinerU 安装与模型下载」。**未获用户明确同意前，不得执行任何安装或下载**（不得 `pip install`、不得下载模型/便携版）。用户拒绝或环境不满足时，转 `FULLTEXT_DEFERRED`（Note-only 降级），**不得静默跳过或伪造全文**。
  - **只问一次**：该询问**仅在首次确认缺失时发生一次**；一旦 MinerU 已确认可用（或用户已授权/已安装），后续任务直接使用，不再重复询问。每次任务开始时只做一次轻量存在性探测即可。
- **MinerU 精度选择**：有 NVIDIA GPU 时优先 `-b hybrid-engine --effort high`（需另设 `CUDA_PATH=<MinerU根>\cuda`）；文本型 PDF 若字符/连字符识别不佳（字体编码问题），改用 `-m ocr` 强制 OCR。归档 fulltext 的 frontmatter `source_type` 记录实际后端（如 `mineru`、`mineru-hybrid`、`mineru-ocr`）。
- **Vault 模板**：`templates/` 下的模板首次使用需复制到 `{{VAULT_ROOT}}\模板\`（含 `论文精读模板.md` 和 `知识库模板\`）。skill 依赖此路径。
- 涉及文献检索/精读/知识库任务时，优先加载对应的 `research-vault-*` 与 `zotero-*` skill（位于 `.opencode/skills/`），遵循其流程与证据规则。
- **Zotero 数据读写**：走 Zotero Desktop 本地 API（默认端口 `23119`，只读）+ Connector（写入走 `import-bibtex` / `import-ris`）；不依赖 MCP。若本地 API 被锁，可用 SQLite 以只读模式（`?immutable=1`）直读。备用 Web API 需要你自己的 API Key，请通过环境变量提供，**不要写进仓库**。
  - 可选 helper：`.opencode/skills/zotero/scripts/zotero.py`（仅 Python 标准库依赖）。`zotero-*` skill 本身只要求能访问上述本地 API + Connector，可自行替换实现。
- **Vault 初始化**：把 `vault-skeleton/` 复制到 `{{VAULT_ROOT}}`（提供 `01knowledge/index.md`、`log.md`、`.meta/`、`02vault/_index/文献索引.md` 等初版），再把 `templates/` 复制到 `{{VAULT_ROOT}}\模板\`。
- **Zotero 云存储（可选）**：如不使用云存储，论文 PDF 本地存放于 `{{RESEARCH_DIR}}\papers\`，只把 MinerU 全文归档到 Vault 即可；Zotero 条目以元数据为主，PDF 附件缺失属正常。
- **arXiv/顶会在线发现**：`start-my-day`、`conf-papers`、`extract-paper-images`、`paper-search`、`paper-analyze`（位于 `evil-read-arxiv/skills/`）。依赖 Python 环境（见 `evil-read-arxiv/requirements.txt`），研究兴趣配置位于 `{{VAULT_ROOT}}/99_System/Config/research_interests.yaml`（可复制 `evil-read-arxiv/config.example.yaml` 生成）。
- 两个 skill 目录（`.opencode/skills/` 与 `evil-read-arxiv/skills/`）通过 `opencode.json` 的 `skills.paths` 注册。
