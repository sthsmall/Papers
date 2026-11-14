# Zotero Analytical Workflow Skills + evil-read-arxiv

本项目集成了两套文献工作流，作为 opencode 项目级 skill：

1. **Zotero 分析工作流**（`zotero-*` / `research-vault-*`）：Zotero 本地文献库 + MinerU 全文的简读/精读与知识页管理。
2. **evil-read-arxiv 在线发现**（`start-my-day` 等）：arXiv / Semantic Scholar / DBLP 在线论文推荐与检索，作为互补补上"发现新论文"环节。

覆盖：

- 论文分类批处理与断点续跑
- 论文元数据、批注、全文缓存提取
- PDF/MinerU 全文归档与可追踪链接维护
- 中文简读笔记生成、旧笔记方法段原位重写与配图
- 知识主题页维护、证据地图与跨论文综合
- ResearchVault 内的 Note-first 文献检索与原文核验
- Zotero、Fulltext、精读笔记和 Knowledge 的端到端编排
- arXiv 每日推荐、顶会检索、在线来源深度分析

## 目录结构

```text
Papers/
├── README.md
├── LICENSE                  # MIT（本仓库自研部分）
├── NOTICE                   # 第三方组件署名（evil-read-arxiv 等）
├── AGENTS.example.md        # 脱敏版项目说明；复制为 AGENTS.md 并填写占位符路径
├── opencode.json            # skills.paths 注册两个 skill 目录
├── .opencode/
│   └── skills/              # 本项目统一维护的 skill（12 个）
│       ├── paper-registry/              # paper_id / papers.tsv
│       ├── zotero-collection-manager/
│       ├── zotero-data-fetcher/
│       ├── zotero-fulltext-archiver/
│       ├── zotero-analytical-writer/
│       ├── research-vault-ingest-orchestrator/
│       ├── research-vault-knowledge-maintainer/
│       ├── research-vault-literature-retrieval/
│       ├── zotero/          # 可选 legacy helper（BibTeX/引用）
│       ├── obsidian-bases/  # .base 文件
│       ├── obsidian-cli/    # Obsidian CLI
│       └── obsidian-markdown/  # Obsidian 语法
├── vault-skeleton/          # 最小可用 Vault 骨架（01knowledge/02vault/03fulltext/99_System）
├── templates/
│   └── 论文简读模板.md        # 唯一笔记模板；知识页模板在 knowledge-maintainer/references/
└── evil-read-arxiv/         # juliye2025 的在线发现（按作者独立，vendor 整合）
    ├── skills/              # 5 个 skill，跟随上游仓库
    │   ├── start-my-day/
    │   ├── conf-papers/
    │   ├── paper-analyze/
    │   ├── extract-paper-images/
    │   └── paper-search/
    ├── web/                 # Next.js 论文推荐网页端（暂不配置）
    ├── tests/
    ├── config.example.yaml  # 研究兴趣配置模板（复制到 {{VAULT_ROOT}}/99_System/Config/research_interests.yaml）
    └── requirements.txt     # Python 依赖
```

- `.opencode/skills/` 与 `evil-read-arxiv/skills/` 都是 opencode skill 目录，通过 `opencode.json` 的 `skills.paths` 注册，启动时自动加载。
- 两个作者的工作流按仓库分离，便于各自独立更新维护。
- `templates/` 是 Vault 写作模板，`vault-skeleton/` 是 Vault 目录骨架；两者都需复制到 `{{VAULT_ROOT}}`（见下）。
- `config.yaml` 未入库（个人研究兴趣配置），请从 `config.example.yaml` 生成，详见下文。

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/sthsmall/Papers
cd Papers
# 2. 配置占位符（复制后填写 {{VAULT_ROOT}} 等实际路径）
copy AGENTS.example.md AGENTS.md
# 3. 初始化你的 Vault（目录骨架 + 写作模板）
robocopy vault-skeleton "<你的Vault根>" /E /XC /XN /XO
xcopy templates "<你的Vault根>\模板\" /E /I
# 4. 生成研究兴趣配置（或直接编辑 vault-skeleton 提供的初版）
copy evil-read-arxiv\config.example.yaml "<你的Vault根>\99_System\Config\research_interests.yaml"
# 5. 安装 Python 依赖
pip install -r evil-read-arxiv/requirements.txt
```

**环境前置**：opencode（加载 skill）、本地论文 PDF 目录（`research/papers/`）、paper registry（`{{VAULT_ROOT}}/02vault/_index/papers.tsv`）、MinerU（PDF→Markdown）、Python 3.10+。Zotero 是**可选 legacy**，默认流程不再要求。

## MinerU 安装与模型下载

MinerU 是全文归档层（`zotero-fulltext-archiver`）的唯一硬依赖。**本仓库不自动安装它**：skill 会先搜索既有安装，若确认缺失，**会停下来询问你是否安装**，得到同意后才按本节指引执行。

> **只询问一次**：该询问仅在**首次确认缺失**时发生；一旦 MinerU 已可用（或你已授权/已安装），后续任务直接使用，不再重复询问。

### 方式 A：pip 安装（通用）

```bash
pip install --upgrade pip
pip install -U "mineru[full]"                # 或：uv pip install -U "mineru[full]"

# 国内网络：优先 HF 镜像；ModelScope 也可用但实测更慢
export HF_ENDPOINT=https://hf-mirror.com     # PowerShell: $env:HF_ENDPOINT="https://hf-mirror.com"

# 下载 standard 档所需的小模型 + VLM（mineru-kit 随 mineru 包安装）
mineru-kit models download --tier standard --small-backend torch --vlm-engine lmdeploy --source huggingface
mineru-kit models verify --tier standard --small-backend torch --vlm-engine lmdeploy
```

### 方式 B：MinerU 4.1.5（推荐，GPU）+ 3.4.0 便携版（fallback）

4.1.5 用独立 venv，不覆盖旧版；模型默认放在 `MINERU_HOME\models`：

```powershell
$env:MINERU_HOME = "<MinerU415根>\home"
$env:MINERU_MODEL_SOURCE = "local"
& "<MinerU415根>\venv\Scripts\mineru-kit.exe" parse `
    "<论文.pdf>" -o "<输出目录>" --tier standard --format zip
```

或直接用带显存检查的包装脚本（free < 12 GB 时 exit 75，不抢 GPU）：

```powershell
& ".opencode\skills\zotero-fulltext-archiver\scripts\mineru_parse.ps1" `
    -Pdf "<论文.pdf>" -Out "<输出目录>" -Tier standard
```

输出 zip 包含 `markdown.md`、`middle_json.json`、`structured_content.json`、`images/`。`structured_content.json` 每个 block 带 `page_idx` 与归一化 bbox，可用 `.opencode\skills\zotero-fulltext-archiver\scripts\build_page_map.py` 生成 `page_map.json`。

3.4.0 便携版保留作 fallback（仅当 4.1.5 失败，或需要图内文字/附录定性图时）：

```powershell
$env:PYTHONPATH      = "<MinerU340根>\src"
$env:HF_HOME         = "<MinerU340根>\models"
$env:HF_HUB_OFFLINE  = "1"
$env:MINERU_MODEL_SOURCE = "modelscope"
$env:PYTHONUTF8      = "1"
$env:CUDA_PATH       = "<MinerU340根>\cuda"

& "<MinerU340根>\WPy64-312101\python\python.exe" -m mineru.cli.client `
    -p "<论文.pdf>" -o "<输出目录>" -b hybrid-engine --effort high
```

重下 4.1.5 模型时优先 HF 镜像（实测约 3.8 MB/s，ModelScope 约 1.6 MB/s）：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
& "<MinerU415根>\venv\Scripts\mineru-kit.exe" models download `
    --tier standard --small-backend torch --vlm-engine lmdeploy --source huggingface
```

### 校验安装

```bash
mineru-kit --version
mineru-kit models verify --tier standard --small-backend torch --vlm-engine lmdeploy
```

### 后端选择建议

| 场景 | 推荐 |
| --- | --- |
| 默认（有 NVIDIA GPU） | 4.1.5 `--tier standard` |
| 更高精度、可接受更慢 | 4.1.5 `--tier advanced`（同一套权重，增加推理投入） |
| 需要图内文字 / 附录定性图 | 3.4.0 `-b hybrid-engine --effort high` |
| 文本型 PDF 字符/连字符识别差（字体编码问题） | 3.4.0 `-m ocr` 强制 OCR |
| 无 GPU / 低显存 | 4.1.5 `--tier basic`（仅小模型），或 3.4.0 `-b pipeline` |

### 没有 MinerU 时会发生什么

- `zotero-fulltext-archiver` 停止 → 记录 `FULLTEXT_DEFERRED`，**不会伪造全文、不会写坏 `03fulltext/`**。
- 其余环节可降级运行（Note-only）：本地 PDF/registry 元数据、基于**原始 PDF** 核验引文的中文简读/精读笔记、知识页维护，以及在线发现（evil-read-arxiv）均不受影响。
- 约束：无 Fulltext 时，任何结论**不得标记 `fulltext_verified`**。

## 论文身份（paper-registry）

默认不依赖 Zotero；每篇论文用一个稳定 `paper_id`：

- 已有 8 位 key → 直接沿用（如 `2Q48RTFR`）
- arXiv → `arxiv_2409.18839`
- DOI → `doi_...`
- 其余 → `pdf_<PDF SHA-256 前 12 位>`

登记文件：`{{VAULT_ROOT}}\02vault\_index\papers.tsv`，记录 `paper_id / title / authors / year / venue / doi / arxiv_id / collection / pdf_path / fulltext_path / note_path / status / page_mapping / legacy_zotero_key`。

```powershell
python .opencode\skills\paper-registry\scripts\paper_registry.py resolve `
  --pdf "{{RESEARCH_DIR}}\papers\paper.pdf" --collection MOT
python .opencode\skills\paper-registry\scripts\paper_registry.py register `
  --registry "{{VAULT_ROOT}}\02vault\_index\papers.tsv" `
  --pdf "{{RESEARCH_DIR}}\papers\paper.pdf" --collection MOT --title "..."
python .opencode\skills\paper-registry\scripts\paper_registry.py validate `
  --registry "{{VAULT_ROOT}}\02vault\_index\papers.tsv" --vault "{{VAULT_ROOT}}"
```

`zotero_key` 仅作为 `legacy_zotero_key` 保留；`zotero` skill 只在需要 BibTeX/引用导出时使用。

## 工作流关系

推荐按下面顺序使用：

1. `paper-registry`：解析本地 PDF、分配 `paper_id`、登记 `papers.tsv`。
2. `zotero-data-fetcher`：优先读 registry + 本地 PDF；Zotero 模式仅 legacy。
3. `zotero-fulltext-archiver`：用 `paper_id` + `pdf_path` 归档 MinerU 全文，整理图片/page map，维护 Note 与 Fulltext 关联。
4. `zotero-analytical-writer`：新笔记按简读模板创建；旧笔记只做 `## 三、方法详解` 原位重写（方法段质量门、配图、引文核验）。
5. `research-vault-ingest-orchestrator`：按单篇论文编排 `paper_id` 身份、Fulltext、笔记、Knowledge 决策和校验。
6. `research-vault-knowledge-maintainer`：维护 `knowledge-theme` 主题页、证据地图、条件性与研究空白，执行跨论文覆盖与证据审查。
7. `research-vault-literature-retrieval`：处理 ResearchVault 文献问题时，先从 Analytical Notes 定位论文，再按需进入对应 Fulltext 或原始 PDF 核验。

## 在线发现（evil-read-arxiv）

补上"发现新论文"环节，与本地 Zotero 管线互补：

- `start-my-day`：arXiv + Semantic Scholar 每日推荐（四维评分），生成 `10_Daily/YYYY-MM-DD论文推荐.md`，前 3 篇自动深度分析 + 提图。
- `conf-papers`：DBLP + S2 顶会检索（CVPR/ICLR/NeurIPS/ICML 等），生成 `10_Daily/{年份}_顶会论文推荐.md`。
- `paper-analyze`：深度分析 arXiv ID / 公开 PDF / 项目页 / 博客 / 本地 PDF，生成带证据与图片的 Obsidian 笔记。
- `extract-paper-images`：优先从 arXiv 源码包提取论文图片。
- `paper-search`：在已有笔记中按标题/作者/关键词/领域搜索。

**配置**：研究兴趣位于 `{{VAULT_ROOT}}/99_System/Config/research_interests.yaml`（`vault-skeleton/` 已提供初版，也可复制 `evil-read-arxiv/config.example.yaml` 生成）。依赖 `pip install -r evil-read-arxiv/requirements.txt`。

> 注：`evil-read-arxiv/config.yaml` 为个人配置，**未入库**。`paper-search` 在找不到 `config.yaml` 时会自动回退读取 `config.example.yaml`。

> 与本地管线的分工：`paper-analyze` / `paper-search` 与 `zotero-analytical-writer` / `research-vault-literature-retrieval` 功能重叠；在线发现类（start-my-day / conf-papers / extract-paper-images）是本项目的互补核心。

## 统一合并工作流

两套 skill 分工原则：**evil-read-arxiv 负责"找"（在线发现），本地 PDF + registry 工作流负责"精读和沉淀"（本地证据链）**。

```text
        【发现层 · evil-read-arxiv】
start-my-day / conf-papers 推荐出论文
   ↓ 筛选值得精读的
paper-analyze 快速预览（可选）
   ↓
paper-registry register 本地 PDF（arXiv/DOI → paper_id）   ← Zotero 可选
   ↓
        【精读层 · 本地 PDF 工作流】
ingest-orchestrator / collection-manager 接手
paper-registry → fetcher → fulltext-archiver → analytical-writer → knowledge-maintainer
   ↓
        【检索层】
本地问题：research-vault-literature-retrieval（精读笔记，权威）
在线记忆：paper-search（在线分析笔记，辅助）
```

**衔接要点**：

1. **入口衔接（唯一交接点）**：`start-my-day` / `conf-papers` 发现的论文，先把本地 PDF 下载到 `{{RESEARCH_DIR}}\papers\`，用 `paper-registry register` 按 arXiv ID / DOI 分配 `paper_id`，再触发本地 PDF 管线做严谨精读。在线推荐笔记不直接成为精读笔记的证据。
2. **两套笔记并存**：在线分析笔记（`20_Research/Papers/`，快、带图、可含项目页/博客）与精读笔记（`02vault/`，严谨、原文核验）并存；精读笔记是权威层，在线笔记作为快速预览与溯源补充。
3. **检索分层**：日常文献问题走 `research-vault-literature-retrieval`（Note-first，原文核验）；`paper-search` 仅用于回忆在线分析笔记中的内容。
4. **功能重叠避免**：`paper-analyze` 不替代 `zotero-analytical-writer`——前者做在线来源（arXiv/PDF/博客）快速分析，后者做本地 PDF 已归档论文的中文精读。
5. **配置前置**：使用发现层前先完成 `research_interests.yaml` 配置与 Python 依赖安装（见上文"配置"）；使用精读层前先确认 `papers.tsv` 可读、模板已复制到 `{{VAULT_ROOT}}\模板\`。Zotero 不再是前置条件。

## 可配置占位符

本仓库不包含任何个人绝对路径。首次使用请先 **`copy AGENTS.example.md AGENTS.md`**，再按下表把占位符替换为你的实际路径（可配置在 `AGENTS.md` 或项目 `opencode.json` 的 `instructions` 中）。

| 占位符 | 说明 |
| --- | --- |
| `{{VAULT_ROOT}}` | ResearchVault 根目录（含 `01knowledge`、`02vault`、`03fulltext`、`模板\`、`tools\`） |
| `{{ARCHIVE_ROOT}}` | 历史 MinerU 归档目录（可为空） |
| `{{RESEARCH_DIR}}` | 研究工具与论文 PDF 目录（如 `<RESEARCH_DIR>\papers\`） |
| `{{MINERU_EXE}}` | MinerU 3.4.0 legacy 可执行文件路径（fallback） |
| `{{MINERU340_ROOT}}` | MinerU 3.4.0 绿色便携版根目录（fallback） |
| `{{MINERU415_HOME}}` | MinerU 4.1.5 的 `MINERU_HOME`（含 `config.yaml`、`models/`） |
| `{{MINERU415_VENV}}` | MinerU 4.1.5 venv |
| `{{MINERU415_KIT}}` | `{{MINERU415_VENV}}\Scripts\mineru-kit.exe` |
| `{{MINERU_PARSE_PS1}}` | `.opencode/skills/zotero-fulltext-archiver/scripts/mineru_parse.ps1` |
| `{{PAPER_REGISTRY}}` | `{{VAULT_ROOT}}\02vault\_index\papers.tsv` |

### 推荐的 Vault 布局（对应占位符）

```text
{{VAULT_ROOT}}/
├── 01knowledge/
│   └── .meta/
├── 02vault/
│   └── _index/
├── 03fulltext/
│   └── <collection>/
│       └── page_maps/        # 4.1.5 page_idx + bbox（可选）
├── 10_Daily/                # evil-read-arxiv 每日/年度推荐笔记
├── 20_Research/
│   └── Papers/              # evil-read-arxiv 在线分析笔记
├── 99_System/
│   └── Config/
│       └── research_interests.yaml   # 研究兴趣配置
├── 模板/
│   └── 论文简读模板.md
├── tools/
└── note/
```

其中 `templates/` 目录下的模板文件即为 `{{VAULT_ROOT}}\模板\` 的来源。

> 注意：若使用 opencode 且占位符路径与默认不同，建议在项目 `opencode.json` 的 `instructions` 或 AGENTS.md 中给出占位符到实际路径的映射，agent 会在执行时解析。

## 路径占位符说明

- Zotero 工作流 skill 原使用 `D:\ResearchVault` 等硬编码路径，已替换为占位符。
- evil-read-arxiv skill 原使用 `$OBSIDIAN_VAULT_PATH` 环境变量，已统一替换为 `{{VAULT_ROOT}}` 占位符；脚本仍保留 `--vault` / `--config` 参数与 `OBSIDIAN_VAULT_PATH` 环境变量兜底。
- `evil-read-arxiv/web/` 的 `python-bridge.ts` 与 `tests/` 已更新为指向 `evil-read-arxiv/skills/` 新位置。

## 使用建议

- 这些 skill 由 opencode 从 `.opencode/skills/` 与 `evil-read-arxiv/skills/` 两个目录加载（见 `opencode.json` 的 `skills.paths`）。
- `zotero-analytical-writer` 使用 `{{VAULT_ROOT}}\模板\论文简读模板.md`；知识页维护 skill 使用 `.opencode/skills/research-vault-knowledge-maintainer/references/` 下的模板与 schema。
- 批量笔记迁移按 `zotero-analytical-writer/references/note-migration-playbook.md` 执行；验收用 `zotero-analytical-writer/scripts/scan_note_quality.py`，并同步 `02vault/_index` 的方法段列与状态页。
- 先启动发现层（`start-my-day` / `conf-papers`）看每日/顶会论文，再对值得精读的走统一合并工作流。

## 后续可继续补充

- 增加示例输入与输出
- 增加安装说明或依赖说明
- 为每个 skill 单独补充测试样例或演示数据

## 已知依赖与缺口

本仓库的 skill 文档与模板是完整的，但以下环节需要使用者自备（skill 内已标注为"可选/需自备"）：

| 环节 | 状态 | 说明 |
| --- | --- | --- |
| MinerU 本体 | **需自行安装** | 见上文「MinerU 安装与模型下载」。skill 检测到缺失时会**先询问用户是否安装**，未获明确同意前不执行任何安装/下载；拒绝则转 `FULLTEXT_DEFERRED` |
| Zotero 访问层 | 已附带 | `.opencode/skills/zotero/scripts/zotero.py`（仅 Python 标准库依赖）；`zotero-*` skill 本身只要求能访问 Zotero 本地 API + Connector，可自行替换实现 |
| Vault 目录骨架 | 已附带 | `vault-skeleton/`（含 `01knowledge/index.md`、`log.md`、`.meta/`、`02vault/_index/文献索引.md` 等初版） |
| 写作模板 | 已附带 | `templates/`（`论文简读模板.md`）；知识页模板在 `knowledge-maintainer/references/` |
| MinerU 批量脚本 | **需自备** | 如 `{{RESEARCH_DIR}}\mineru_batch_runner.py`、`{{VAULT_ROOT}}\tools\run_mineru_production.py`；缺失时直接按 `AGENTS.md` 调用 MinerU CLI |
| 链接一致性校验脚本 | **需自备** | 如 `{{RESEARCH_DIR}}\zotero_batch\validate_research_vault_literature_links.py`；缺失时按 skill 内检查项人工核对 |
| Knowledge 校验器 | **需自备** | `research-vault-knowledge-maintainer/scripts/validate_research_vault_knowledge.py` 未随仓库发布；缺失时按 `validation-contract.md` 检查项人工核对 |
| 可选维护索引 | 可选 | `02vault/_index/` 下 `研究主题索引.md`、`研究方法索引.md`、`字段补全检查.md`；检索 skill 会"缺失则跳过" |

> 上述"需自备"项是本工作流在原作者环境中使用的外部脚本，仓库未包含（也不影响 skill 逻辑本身）。如果你实现了等价脚本，欢迎自行补充。

## 许可证与署名

- 本仓库自研部分（`.opencode/skills/` 中 7 个 `zotero-*`/`research-vault-*`、`templates/`、`vault-skeleton/` 等）：**MIT License**，见 [LICENSE](LICENSE)。
- `evil-read-arxiv/`：版权归 [juliye2025](https://github.com/juliye2025/evil-read-arxiv)，**MIT License**，以 vendor 方式整合。
- `.opencode/skills/zotero/`：第三方 helper skill，**上游许可证未声明**，公开再分发前请先确认授权（详见 [NOTICE](NOTICE)）。
- 完整第三方署名见 [NOTICE](NOTICE)。

## 仓库不包含的内容

为避免体积、版权与隐私问题，以下内容**不入库**（见 `.gitignore`）：

- `research/`：论文 PDF 与 MinerU 运行产物。
- `evil-read-arxiv/data/`：个人 API 设置、收藏、反馈与偏好。
- `evil-read-arxiv/config.yaml`：个人研究兴趣配置（请用 `config.example.yaml` 生成）。
- `AGENTS.md`：本机专属路径映射（请用 `AGENTS.example.md` 复制生成）。
