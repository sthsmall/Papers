#!/usr/bin/env python3
"""Build a page-level map from MinerU 4.1.5 structured_content.json.

The map is deliberately small: page_idx, page_number, block type, bbox and a
short content preview. It is meant for locating a quote/page in the original
PDF, not for replacing the fulltext Markdown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys


def block_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("content")
                if value is not None:
                    parts.append(str(value))
            elif item is not None:
                parts.append(str(item))
        return " ".join(parts)
    return "" if content is None else str(content)


def build_map(data: dict, include_content: bool = False) -> dict:
    pages = data.get("pages")
    if pages is None:
        pages = data.get("pdf_info")
    if not isinstance(pages, list):
        raise ValueError("structured_content.json has no 'pages' list")

    out_pages = []
    for fallback_idx, page in enumerate(pages):
        page_idx = page.get("page_idx", page.get("page_index", fallback_idx))
        blocks = page.get("blocks") or page.get("para_blocks") or []
        out_blocks = []
        for block in blocks:
            text = block_text(block).strip()
            item = {
                "type": block.get("type"),
                "bbox": block.get("bbox"),
                "content_preview": text[:300],
                "content_sha1": hashlib.sha1(text.encode("utf-8")).hexdigest() if text else None,
            }
            if include_content:
                item["content"] = text
            out_blocks.append(item)
        out_pages.append(
            {
                "page_idx": int(page_idx),
                "page_number": int(page_idx) + 1,
                "block_count": len(out_blocks),
                "blocks": out_blocks,
            }
        )

    return {
        "schema_version": 1,
        "source": "mineru-4.1.5:structured_content",
        "page_index_base": 0,
        "page_count": len(out_pages),
        "pages": out_pages,
    }


def update_frontmatter(fulltext: str, mapping_path: str) -> bool:
    text = open(fulltext, encoding="utf-8", errors="ignore").read()
    if not text.startswith("---"):
        raise ValueError(f"no YAML frontmatter: {fulltext}")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError(f"unterminated YAML frontmatter: {fulltext}")
    head, body = text[: end + 4], text[end + 4 :]
    rel = os.path.relpath(mapping_path, os.path.dirname(fulltext)).replace("\\", "/")
    line = f'page_mapping: "{rel}"'
    if re.search(r"(?m)^page_mapping:\s*.*$", head):
        head = re.sub(r"(?m)^page_mapping:\s*.*$", line, head, count=1)
    elif re.search(r"(?m)^fulltext_path:\s*.*$", head):
        head = re.sub(r"(?m)^(fulltext_path:\s*.*)$", r"\1\n" + line, head, count=1)
    else:
        head = head[: end] + "\n" + line + head[end:]
    if head == text[: end + 4]:
        return False
    open(fulltext, "w", encoding="utf-8", newline="\n").write(head + body)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structured", required=True, help="MinerU 4.1.5 structured_content.json")
    ap.add_argument("--out", required=True, help="page map JSON to write")
    ap.add_argument("--fulltext", help="optional fulltext Markdown whose page_mapping should be updated")
    ap.add_argument("--update-frontmatter", action="store_true")
    ap.add_argument("--include-content", action="store_true", help="store full block text (larger)")
    args = ap.parse_args()

    data = json.load(open(args.structured, encoding="utf-8"))
    page_map = build_map(data, include_content=args.include_content)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(page_map, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {args.out}: {page_map['page_count']} pages, "
          f"{sum(p['block_count'] for p in page_map['pages'])} blocks")

    if args.update_frontmatter:
        if not args.fulltext:
            raise SystemExit("--update-frontmatter requires --fulltext")
        changed = update_frontmatter(args.fulltext, args.out)
        print(("updated " if changed else "unchanged ") + args.fulltext)
    return 0


if __name__ == "__main__":
    sys.exit(main())
