# AGENTS.md（示例 / 模板）

> 把本文件复制为 `AGENTS.md` 后，按下表把占位符替换为你的实际路径。本文件是可提交的脱敏版本，不包含任何个人绝对路径。

## 占位符 → 实际路径映射

本项目 skill（`.opencode/skills/`、`evil-read-arxiv/skills/`）使用可配置占位符。执行相关任务时，请按下表把占位符替换为实际路径。

| 占位符 | 实际路径（请填写） |
| --- | --- |
| `{{VAULT_ROOT}}` | 你的 Obsidian 研究库根目录（含 `01knowledge/`、`02vault/`、`03fulltext/`、`模板/`） |
| `{{ARCHIVE_ROOT}}` | 历史 MinerU / 全文归档目录（可为空） |
| `{{RESEARCH_DIR}}` | 研究工具与论文 PDF 目录（如 `<RESEARCH_DIR>\papers\` 存放论文 PDF） |
| `{{MINERU_EXE}}` | MinerU 3.4.0 legacy 可执行文件路径（可选 fallback） |
| `{{MINERU340_ROOT}}` | MinerU 3.4.0 绿色便携版根目录（可选 fallback） |
| `{{MINERU415_HOME}}` | MinerU 4.1.5 的 `MINERU_HOME`（含 `config.yaml` 与 `models/`） |
| `{{MINERU415_VENV}}` | MinerU 4.1.5 的 Python venv |
| `{{MINERU415_KIT}}` | `{{MINERU415_VENV}}\Scripts\mineru-kit.exe` |
| `{{MINERU_PARSE_PS1}}` | `.opencode/skills/zotero-fulltext-archiver/scripts/mineru_parse.ps1` |

## 使用注意

- 上述目录可能尚未创建。执行 skill 流程前先 `Test-Path` 确认；缺失时向用户确认，不要自动批量创建。
- **MinerU 默认 4.1.5（GPU）**：单篇优先调用 `{{MINERU_PARSE_PS1}} -Pdf <pdf> -Out <out> -Tier standard`。脚本先查 `nvidia-smi` 的 free，低于 12 GB 直接退出（exit 75），避免和用户实验抢显存。4.1.5 需要 `MINERU_HOME={{MINERU415_HOME}}`、`MINERU_MODEL_SOURCE=local`；VLM 仍是 `MinerU2.5-Pro-2605-1.2B`，小模型是 `MinerU-4_models_torch`。
- 4.1.5 输出 zip：`markdown.md` / `middle_json.json` / `structured_content.json` / `images/`。`structured_content.json` 每个 block 带 `page_idx` 和归一化 bbox；用 `.opencode/skills/zotero-fulltext-archiver/scripts/build_page_map.py` 生成 `page_map.json`，可回填 fulltext 的 `page_mapping`。
- **3.4.0 fallback**：仅当 4.1.5 失败，或需要图内文字/附录定性图时使用 `-Fallback340`，或手动执行 `{{MINERU340_ROOT}}\WPy64-312101\python\python.exe -m mineru.cli.client -p <pdf> -o <out> -b hybrid-engine --effort high`（需 `PYTHONPATH={{MINERU340_ROOT}}\src`、`HF_HOME={{MINERU340_ROOT}}\models`、`CUDA_PATH={{MINERU340_ROOT}}\cuda`）。文本型 PDF 字体编码异常时加 `-m ocr`。`source_type` 记录实际后端（`mineru-4.1.5` / `mineru-3.4.0-hybrid` / `mineru-3.4.0-ocr`）。
- 4.1.5 已知行为：默认不 OCR 图内文字（饼图/词云/定性图标签），只输出图片+图注；需要这些文字时回退 3.4.0。`Warm-up for 8320 tokens failed with status 6` 是 lmdeploy 的非致命告警，解析仍成功。
- **模型下载**：当前模型放在 `{{MINERU415_HOME}}\models`，默认 `MINERU_MODEL_SOURCE=local`，不要重复下载。若需重下：HF 镜像（`HF_ENDPOINT=https://hf-mirror.com`）快于 ModelScope；命令为 `{{MINERU415_KIT}} models download --tier standard --small-backend torch --vlm-engine lmdeploy --source huggingface`。
- **未检测到 MinerU 时的硬性约定**：先搜索既有 MinerU（可执行文件 / CLI / Python 模块 / 历史输出），**不要重复安装**。若确认确实没有可用 MinerU，**必须停下并询问用户"是否安装 MinerU"**，并指向 `README.md` 的「MinerU 安装与模型下载」。**未获用户明确同意前，不得执行任何安装或下载**（不得 `pip install`、不得下载模型/便携版）。用户拒绝或环境不满足时，转 `FULLTEXT_DEFERRED`（Note-only 降级），**不得静默跳过或伪造全文**。
  - **只问一次**：该询问**仅在首次确认缺失时发生一次**；一旦 MinerU 已确认可用（或用户已授权/已安装），后续任务直接使用，不再重复询问。每次任务开始时只做一次轻量存在性探测即可。
- **MinerU 精度选择**：默认 4.1.5 `standard`；`advanced` 只增加推理投入，不换权重。需要 3.4.0 的图内文字/强制 OCR 时按上一条 fallback。
- **Vault 模板**：`templates/` 下的 `论文简读模板.md` 首次使用需复制到 `{{VAULT_ROOT}}\模板\`。知识页模板与 schema 位于 `.opencode/skills/research-vault-knowledge-maintainer/references/`，不再放到 Vault 模板目录。
- **简读笔记质量门**：新笔记按 `论文简读模板.md` 创建；旧笔记只做 `## 三、方法详解` 原位重写，保留贡献/结果/判断章节。方法段 ≥4,500 字符（短论文 ≥4,000）；有公式的论文 ≥2 个原文公式，无公式则注明；训练细节、结果/消融/边界齐全；≥4 图或注明原文不足；引文用 Fulltext grep 命中并标注页码状态。
- **笔记迁移习惯**：批量迁移按 `.opencode/skills/zotero-analytical-writer/references/note-migration-playbook.md` 执行；验收用 `.opencode/skills/zotero-analytical-writer/scripts/scan_note_quality.py`，并同步 `02vault/_index/文献索引.md` 的 `方法段` 列与 `02vault/_index/笔记重写状态.md`。批次报告不能替代独立扫描。
- 涉及文献检索/精读/知识库任务时，优先加载对应的 `research-vault-*` 与 `zotero-*` skill（位于 `.opencode/skills/`），遵循其流程与证据规则。
- **Zotero 数据读写**：走 Zotero Desktop 本地 API（默认端口 `23119`，只读）+ Connector（写入走 `import-bibtex` / `import-ris`）；不依赖 MCP。若本地 API 被锁，可用 SQLite 以只读模式（`?immutable=1`）直读。备用 Web API 需要你自己的 API Key，请通过环境变量提供，**不要写进仓库**。
  - 可选 helper：`.opencode/skills/zotero/scripts/zotero.py`（仅 Python 标准库依赖）。`zotero-*` skill 本身只要求能访问上述本地 API + Connector，可自行替换实现。
- **Vault 初始化**：把 `vault-skeleton/` 复制到 `{{VAULT_ROOT}}`（提供 `01knowledge/index.md`、`log.md`、`.meta/`、`02vault/_index/文献索引.md` 等初版），再把 `templates/` 复制到 `{{VAULT_ROOT}}\模板\`。
- **Zotero 云存储（可选）**：如不使用云存储，论文 PDF 本地存放于 `{{RESEARCH_DIR}}\papers\`，只把 MinerU 全文归档到 Vault 即可；Zotero 条目以元数据为主，PDF 附件缺失属正常。
- **arXiv/顶会在线发现**：`start-my-day`、`conf-papers`、`extract-paper-images`、`paper-search`、`paper-analyze`（位于 `evil-read-arxiv/skills/`）。依赖 Python 环境（见 `evil-read-arxiv/requirements.txt`），研究兴趣配置位于 `{{VAULT_ROOT}}/99_System/Config/research_interests.yaml`（可复制 `evil-read-arxiv/config.example.yaml` 生成）。
- 两个 skill 目录（`.opencode/skills/` 与 `evil-read-arxiv/skills/`）通过 `opencode.json` 的 `skills.paths` 注册。
