# JSON Canvas Spec (working reference)

Source format: Obsidian `.canvas`, JSON with two top-level arrays: `nodes`, `edges`.

## Top level

```json
{ "nodes": [], "edges": [] }
```

Both arrays may be empty. Preserve unknown fields when editing.

## Nodes

Common:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | unique within file |
| `type` | `text` / `file` / `link` / `group` | yes | |
| `x` | number | yes | pixels |
| `y` | number | yes | pixels |
| `width` | number | yes | pixels |
| `height` | number | yes | pixels |
| `color` | string | no | `1`–`6` or `#RRGGBB` |

### text

`text` (string, Markdown). Example:

```json
{"id":"t1","type":"text","text":"**Claim**\n- evidence","x":0,"y":0,"width":240,"height":120}
```

### file

`file` is a vault-relative path. Example:

```json
{"id":"f1","type":"file","file":"02vault/SAM/SAM 3 Segment Anything with Concepts.md","x":300,"y":0,"width":300,"height":200}
```

### link

`url` (string). Example:

```json
{"id":"l1","type":"link","url":"https://arxiv.org/abs/2409.18839","x":0,"y":200,"width":300,"height":120}
```

### group

`label` (string); optional `background` (path) and `backgroundStyle` (`cover` / `ratio` / `repeat`). Group has no parent field: membership is geometric, so the box must cover its children.

```json
{"id":"g1","type":"group","label":"Method","x":-40,"y":-40,"width":720,"height":520,"background":"","backgroundStyle":"cover"}
```

## Edges

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | unique within file |
| `fromNode` | string | yes | existing node id |
| `toNode` | string | yes | existing node id |
| `fromSide` | `top` / `right` / `bottom` / `left` | no | default auto |
| `toSide` | same | no | default auto |
| `fromEnd` | `none` / `arrow` | no | default arrow |
| `toEnd` | `none` / `arrow` | no | default arrow |
| `label` | string | no | edge label |
| `color` | string | no | `1`–`6` or hex |

```json
{"id":"e1","fromNode":"t1","toNode":"f1","fromSide":"right","toSide":"left","label":"supports"}
```

## Practical rules

- IDs are stable; do not reuse an ID for a different node.
- Edges must reference existing node IDs; validate before opening.
- Groups render behind nodes; put group objects first and size them to contain children.
- Coordinates are pixels; keep a 40–80 px gap between cards.
- Do not use `.canvas` for prose; keep the note in Markdown and use Canvas for relations.
- Validate with `scripts/canvas.py validate <file>`.
