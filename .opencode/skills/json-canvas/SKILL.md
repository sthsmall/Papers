---
name: json-canvas
description: "Create and edit Obsidian JSON Canvas (.canvas) files with text, file, link, and group nodes plus labeled edges. Use when building visual maps, mind maps, flowcharts, paper relationship graphs, or method diagrams in Obsidian, or when the user mentions Canvas, .canvas, nodes, edges, or groups."
---

# JSON Canvas

Obsidian Canvas 是一个 JSON 文件（`.canvas`），用节点和边描述视觉布局。它不是 Markdown，也不是 `.base`。

## 文件结构

```json
{
  "nodes": [
    {
      "id": "n1",
      "type": "text",
      "text": "**Paper**\nKey claim",
      "x": 0,
      "y": 0,
      "width": 260,
      "height": 100,
      "color": "1"
    },
    {
      "id": "g1",
      "type": "group",
      "label": "Method",
      "x": -40,
      "y": -40,
      "width": 700,
      "height": 500
    }
  ],
  "edges": [
    {
      "id": "e1",
      "fromNode": "n1",
      "fromSide": "right",
      "toNode": "n2",
      "toSide": "left",
      "label": "uses",
      "color": "4"
    }
  ]
}
```

节点类型：

| type | 必填字段 | 用途 |
|---|---|---|
| `text` | `text` | Markdown 文本卡片 |
| `file` | `file` | 指向 Vault 内文件（相对路径） |
| `link` | `url` | 外部链接 |
| `group` | `label` | 背景分组框 |

通用字段：`id`、`type`、`x`、`y`、`width`、`height`、`color`（`1`–`6` 或 hex）。`group` 还可用 `background`、`backgroundStyle`（`cover`/`ratio`/`repeat`）。

边字段：`id`、`fromNode`、`toNode`，可选 `fromSide`/`toSide`（`top`/`right`/`bottom`/`left`）、`fromEnd`/`toEnd`（`none`/`arrow`）、`label`、`color`。

完整规范见 [references/CANVAS_SPEC.md](references/CANVAS_SPEC.md)。

## 工作流程

1. 先读现有 `.canvas`（若有），保留已有节点/边与未知字段。
2. 先规划分组和相对位置，再写节点；`group` 建议放在 `nodes` 数组前面，保证在底层。
3. 节点 `id` 用稳定短 ID（如 `paper-sam3`、`method-memory`），不要用标题当 ID。
4. 边只连接真实存在的节点；跨组边用 `label` 说明关系。
5. 写完后运行校验：

```bash
python .opencode/skills/json-canvas/scripts/canvas.py validate "<file>.canvas"
```

6. 在 Obsidian 中打开检查布局；必要时只调 `x/y/width/height`，不改内容。

## 新建空画布

```bash
python .opencode/skills/json-canvas/scripts/canvas.py new --out "<file>.canvas"
```

## 约束

- 坐标是像素，不是百分比；组框要覆盖其成员节点。
- 同一文件内 `id` 必须唯一；边必须引用存在的节点。
- 不要用 `.canvas` 代替 Markdown 笔记；Canvas 是导航/关系视图。
- 不要删除用户已有的节点/边；编辑前先读取并保留未知字段。
- 颜色优先用 `1`–`6` 的主题色，hex 只用于特殊语义。
