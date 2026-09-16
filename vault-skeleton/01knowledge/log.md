# ResearchVault 知识库处理日志

本文件为 append-only 日志，记录每次入库与知识库更新事件。不重写历史条目。

## 条目格式

```markdown
---

## YYYY-MM-DD（可选：本次主题）

**论文**：<标题>（<作者/会议>）
**Zotero key**：<zotero_key>
**Fulltext 状态**：<已归档 / 复用既有 / 缺失原因>
**Analytical Note 状态**：<已创建 / 已更新 / 按模板修复>
**Knowledge 动作**：<NO_KNOWLEDGE_CHANGE / 创建或更新某知识页（evidence_count=N, 证据等级）>
**校验结果**：<通过项 / 未通过项>
```

---

<!-- 在此之下按时间追加事件，不要修改上方格式说明 -->
