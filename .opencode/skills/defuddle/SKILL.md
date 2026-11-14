---
name: defuddle
description: "Extract clean article content from web pages with the Defuddle CLI, stripping navigation, ads, and boilerplate. Use instead of a raw webfetch when the user provides a blog, documentation, news, or project URL and wants the readable body as Markdown. Not for URLs ending in .md (already Markdown)."
---

# Defuddle

把网页正文转成干净 Markdown，减少导航/广告/侧栏噪声和 token 消耗。

## 命令

```bash
# 正文 → Markdown（最常用）
defuddle parse "<url>" --md

# 带 YAML frontmatter（title/author/source 等）
defuddle parse "<url>" --md --frontmatter

# 输出到文件
defuddle parse "<url>" --md -o "<out.md>"

# 读取元数据
defuddle parse "<url>" --json
defuddle parse "<url>" --property title
defuddle parse "<url>" --property description
```

`source` 也可以是本地 HTML 文件，或 `-` 从 stdin 读取。

## 使用流程

1. 确认 URL 不是 `.md`；`.md` 直接读取，不用 Defuddle。
2. 优先 `defuddle parse <url> --md --frontmatter`，输出到临时目录后再读。
3. 需要标题/作者/站点时用 `--json` 或 `--property`。
4. 只引用正文内容；导航、推荐、评论区不作为证据。
5. 页面需要登录、验证码、付费墙或返回 403 时，停止并让用户处理，不绕过。

## 边界

- 不做批量爬取；一次任务只抓用户明确给出的页面。
- 不把网页正文当论文原文证据；论文证据仍以 Fulltext/PDF 为准。
- 遇到 SPA/JS 渲染页，Defuddle 可能拿不到正文，退回 `webfetch` 或让用户提供 PDF/HTML。
- 输出中的链接可能是相对路径；需要绝对链接时自行补全。
