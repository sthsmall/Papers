# MinerU 4.1.5 全量重跑计划

> 状态：**运行完成（93/93）；68 篇 ready 已归档 4.1.5；25 篇 key_pending 待补 key**  
> 日期：2026-11-11  
> 范围：ResearchVault 现有 103 篇 Fulltext 对应的 PDF；不覆盖旧全文，先 staging、验收、再替换。  
> 清单：`mineru_415_rerun_manifest.tsv`（103 行，逐篇 batch / key / pages / action / status）  
> 范围边界：本轮以 **103 篇 Vault Fulltext** 为准；`research/papers` 的 65 个 PDF 只作为 28 篇缺失篇目的来源，不额外重跑未入库 PDF。若要把未入库 PDF 也跑，需要另列清单。

## 1. 盘点

| 项目 | 数量 | 说明 |
|---|---:|---|
| Vault Fulltext | 103 | MOT 48 / SAM 29 / VOS 13 / RS 12 / VIS 1 |
| 已用 4.1.5 跑过 | 9 | 8 篇 A/B + GOOSE；不重跑 |
| 可直接重跑 | 65 | Zotero key + PDF 都在 |
| 需先补 Zotero key | 16 | 本地 `research/papers` 已有 PDF |
| 需先补 PDF 附件 | 12 | 9 篇 arXiv key + 3 篇 Zotero 条目无 PDF；本地已有 PDF |
| 暂缓 | 1 | `Detect Anything in Real Time...`，本地/Zotero 都没有 PDF |
| 本轮重跑合计 | **93** | 65 + 16 + 12 |
| 重跑页数 | **1,431 页** | 不含 9 篇已完成 |
| 预估 GPU 时间 | **约 108 分钟** | 按 0.39 页/s + 每篇 0.5 min 启动；不含人工验收 |

已完成的 9 篇：`ZGJM7L7M`、`7V2T9NDK`、`MHHV6S74`、`2Q48RTFR`、`4NQ97YDP`、`CXJQ2RCU`、`CTAXE5TV`、`6PLWQPZW`、`BIGYNNLX`。

## 2. 前置依赖（先做，不占 GPU）

| 依赖 | 数量 | 处理 |
|---|---:|---|
| 无 `zotero_key` | 16 | 先建 Zotero 父条目并回填 key；本地 PDF 已在 `research/papers`，不重新下载 |
| 有 key、无 PDF 附件 | 3 | 把本地 PDF 作为附件挂到 Zotero 条目（不上传云存储） |
| arXiv key | 9 | 本地 PDF 已有；建 Zotero 条目后回填正式 key |
| 完全缺 PDF | 1 | 暂停该篇，标记 `FULLTEXT_DEFERRED`，不阻塞其他批次 |

> 依赖未解决的篇目在批次中**先跳过**，不阻塞同批其他论文；解决后补跑。所有依赖完成后，再统一补跑。

## 3. 批次表

批次按 Collection 分组，每批最多 10 篇；每批结束**停下报告**，不自动续跑下一批。

| 批次 | Collection | 篇数 | 页数 | 预估 GPU | 依赖 | 状态 |
|---|---|---:|---:|---:|---|---|
| B01 | MOT | 10 | 153 | 11.5 min | 0 | 进行中 3/10 |
| B02 | MOT | 10 | 156 | 11.7 min | 0 | 未开始 |
| B03 | MOT | 10 | 145 | 11.4 min | key×2 | 未开始 |
| B04 | MOT | 10 | 160 | 11.9 min | key×3 | 未开始 |
| B05 | MOT | 6 | 89 | 6.8 min | pdf×2 | 未开始 |
| B06 | SAM | 10 | 153 | 11.6 min | key×1 + pdf×2 | 未开始 |
| B07 | SAM | 10 | 193 | 13.2 min | key×2 + pdf×1 | 未开始 |
| B08 | SAM | 4 | 83 | 5.5 min | key×1 + pdf×1 | 未开始 |
| B09 | VOS | 10 | 120 | 10.2 min | key×2 + pdf×1 | 未开始 |
| B10 | VOS | 2 | 20 | 1.9 min | pdf×2 | 未开始 |
| B11 | RS | 10 | 145 | 11.2 min | key×5 + pdf×3 | 未开始 |
| B12 | VIS | 1 | 14 | 1.1 min | 0 | 未开始 |

## 4. 单篇执行

```powershell
& .opencode\skills\zotero-fulltext-archiver\scripts\mineru_parse.ps1 `
  -Pdf "<pdf>" -Out "<staging>\<batch>\<key>" -Tier standard
```

- 默认 4.1.5 `--tier standard --format zip`
- 启动前检查 `nvidia-smi` free；**< 12 GB 直接 exit 75**，该批次暂停，不循环重试
- 只有 4.1.5 失败，或该篇明确需要图内文字/附录定性图时，才加 `-Fallback340`
- 输出保留 zip；解压后的 `markdown.md` / `structured_content.json` / `images/` 进入验收
- 每篇结束检查 `mineru.cli` / `fast_api` / `multiprocessing.spawn` 是否退出；有残留只清理本次 MinerU 进程树

路径约定：

```text
staging:  E:\program\MinerU\MinerU-4.1.5\rerun_2026-11\<batch>\<key>\
backup:   {{ARCHIVE_ROOT}}\2026-11-11_mineru340_fulltext\<collection>\<key>.md
fulltext: {{VAULT_ROOT}}\03fulltext\<collection>\<key>.md
page map: {{VAULT_ROOT}}\03fulltext\<collection>\page_maps\<key>.json
```

## 5. 验收门（逐篇）

**硬失败（不替换）**

- exit code ≠ 0，或 zip 缺失
- Markdown < 500 字符
- 图片引用有缺失
- page map 页数 ≠ PDF 页数，或 bbox 覆盖 < 100%

**自动通过（可替换）**

- 字符数 ≥ 旧全文的 85%
- 公式数量 ≥ 旧全文（或差异有明确原因）
- 表格内容不缺失；图片引用全部解析
- 与旧全文相似度 ≥ 0.85
- 抽 2 条 quote 能在 page map 中对到正确 PDF 页

**人工复核（不自动替换）**

- 相似度 0.70–0.85，或字符数 70%–85%
- 表格/公式数量下降
- 附录章节缺失，或图内文字是这篇的关键内容

**保留旧版 / 回退 3.4.0**

- 相似度 < 0.70 且无法解释
- 主方法/实验章节缺失
- 必须依赖图内文字（饼图、词云、定性图标签）或附录逐例图

## 6. 替换与回滚

1. 旧全文先复制到 `{{ARCHIVE_ROOT}}\2026-11-11_mineru340_fulltext\<collection>\<key>.md`。
2. 只有验收通过才替换 `03fulltext`；不通过保留旧版并记录原因。
3. 新全文沿用原 `zotero_key`、`pdf_key`、`note_path`；`source_type` 写 `mineru-4.1.5`。
4. 用 `build_page_map.py` 生成 `page_maps/<key>.json`，回填 `page_mapping`。
5. 不自动重写分析笔记；只更新 fulltext 与 page map。笔记里的页码在人工核验后再改。
6. 回滚：用 backup 覆盖回 `03fulltext`，删除新 page map，恢复原 `page_mapping`。

## 7. 风险

| 风险 | 影响 | 处理 |
|---|---|---|
| 4.1.5 不 OCR 图内文字 | 图表内数据/标签丢失 | 关键篇回退 3.4.0，或补一次图内 OCR |
| 附录定性图减少 | 附录逐例图不完整 | 人工复核；需要时 3.4.0 |
| GPU 与实验冲突 | 解析被 OOM/卡顿 | 12 GB 守卫；每批前检查；不后台常驻 |
| 后台脚本/进程残留 | 占 GPU、干扰实验 | 每篇/每批检查 `client`/`fast_api`/`spawn`；批次结束确认无残留；不把整批挂在一个后台 shell |
| 老旧 PDF 字体编码 | 乱码/连字符异常 | 3.4.0 `-m ocr` 或人工复核 |
| 旧全文是证据档案 | 直接替换会破坏引用 | 先备份、逐篇验收、不批量覆盖 |
| 依赖篇目阻塞 | 批次卡住 | 依赖项跳过，解决后补跑 |

## 8. 运行结果（2026-11-12）

- 90/90 成功，0 失败，0 次 GPU 守卫暂停；21:35:14 → 22:35:04，约 60 分钟。
- 加上此前 3 篇试点，共验收 93 篇。
- 验收结果：**53 自动通过、16 备注通过（仅少 1 个 display formula）、24 待复核、0 硬失败**。
- 复核结论：24 篇待复核中，16 篇 ready 已确认可归档（`2IZL6P3F` 的 2 个窄表头已手工修复）；8 篇 key_pending 保留复核记录，等补 key 后再定。
- 归档结果：**68 篇 ready 已替换为 4.1.5**，旧全文备份到 `{{ARCHIVE_ROOT}}\2026-11-11_mineru340_fulltext\`；**25 篇 key_pending 仍保留旧版**。
- 明细：`rerun_2026-11/verification_clean.tsv`；报告：`rerun_2026-11/verification_report.md`；替换日志：`rerun_2026-11/replacement_log.tsv`。

## 9. 确认清单

- [ ] 确认范围：只跑 103 篇 Vault Fulltext 对应的 PDF（93 篇重跑，9 篇跳过，1 篇暂缓）
- [ ] 确认是否要把 `research/papers` 中未入库的额外 PDF 也纳入（若纳入，另加批次与清单）
- [ ] 确认 16 篇先建 Zotero 条目、12 篇先补 PDF 附件
- [ ] 确认 `Detect Anything in Real Time` 暂缓
- [ ] 确认每批 10 篇、每批结束停下报告
- [ ] 确认 12 GB 显存守卫与不自动重试
- [ ] 确认旧全文备份路径与替换/回滚规则
- [ ] 确认 3.4.0 fallback 只用于图内文字/附录定性图/4.1.5 失败
- [ ] 确认替换范围：只换 39 篇 ready 自动通过，还是连同 13 篇备注通过一起换
- [ ] 确认 16 篇 ready 待复核逐篇看，还是先保留旧版
- [ ] 确认 25 篇 key_pending 先建 Zotero 条目，再归档

确认后再从 B01 开始；在确认前不启动任何 GPU 任务。
