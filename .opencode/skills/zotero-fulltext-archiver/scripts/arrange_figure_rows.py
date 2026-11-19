"""Lay out side-by-side figure panels of MinerU 4.1.5 fulltexts as one grid row.

MinerU emits every figure panel as an independent image block, so a 2x2 figure
arrives as four stacked markdown images in column-major order. This pass merges
only runs that are unambiguously side by side on the same PDF page.

Rule: a run of >=2 consecutive image lines is merged when all images
  - come from the same page (page_N_*),
  - share one vertical band (overlap >= 60% of the median height),
  - do not overlap horizontally.
Merged rows are ordered left to right, column widths follow the PDF bbox widths,
and images narrower than 500 px get a max-width so they are never upscaled.

Usage:
    python arrange_figure_rows.py --dry-run
    python arrange_figure_rows.py --apply
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import zipfile

from PIL import Image

DEFAULT_VAULT = r"D:\remoteRepository\obsidian-git-repository\researchVault"
DEFAULT_STAGE = r"E:\program\MinerU\MinerU-4.1.5"
DEFAULT_LOG = r"D:\projects\general\Papers\fulltext_image_layout_log.tsv"

IMG_RE = re.compile(r"^\s*!\[([^\]]*)\]\((images/[^)]+)\)\s*$")


def index_structured(stage: str) -> dict[str, str]:
    """paper_id -> zip that contains structured_content.json."""
    idx: dict[str, str] = {}
    for z in glob.glob(os.path.join(stage, "**", "*.zip"), recursive=True):
        idx.setdefault(os.path.basename(os.path.dirname(z)), z)
    return idx


def load_bbox_map(zip_path: str) -> dict[str, list[float]]:
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith("structured_content.json")]
        if not names:
            return {}
        data = json.loads(z.read(names[0]).decode("utf-8"))
    return {
        os.path.basename(b["image_source"]): b["bbox"]
        for page in data.get("pages", [])
        for b in page.get("blocks", [])
        if b.get("image_source") and b.get("bbox")
    }


def find_runs(lines: list[str]) -> list[list[dict]]:
    """Runs of consecutive image lines (blank lines between them are allowed)."""
    runs: list[list[dict]] = []
    cur: list[dict] = []
    for i, line in enumerate(lines):
        m = IMG_RE.match(line)
        if m:
            cur.append({"idx": i, "alt": m.group(1), "path": m.group(2)})
            continue
        if line.strip() == "":
            continue
        if len(cur) >= 2:
            runs.append(cur)
        cur = []
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def same_band(entries: list[dict], bboxes: dict[str, list[float]]) -> bool:
    pages = {os.path.basename(e["path"]).split("_")[1] for e in entries}
    if len(pages) != 1:
        return False
    bs = [bboxes.get(os.path.basename(e["path"])) for e in entries]
    if any(b is None for b in bs):
        return False
    y0 = max(b[1] for b in bs if b)
    y1 = min(b[3] for b in bs if b)
    if y1 - y0 <= 0:
        return False
    heights = sorted(b[3] - b[1] for b in bs if b)
    if (y1 - y0) < 0.6 * heights[len(heights) // 2]:
        return False
    xs = sorted((b[0], b[2]) for b in bs if b)
    return all(b[0] >= a[1] - 0.01 for a, b in zip(xs, xs[1:]))


def natural_width(path: str) -> int | None:
    try:
        with Image.open(path) as im:
            return im.width
    except Exception:  # noqa: BLE001
        return None


def render_row(entries: list[dict], bboxes: dict[str, list[float]], base_dir: str) -> list[str]:
    bs = [bboxes[os.path.basename(e["path"])] for e in entries]
    widths = [max(b[2] - b[0], 0.01) for b in bs]
    total = sum(widths)
    cols = " ".join(f"{w / total:.3f}fr" for w in widths)
    out = [f'<div style="display:grid;grid-template-columns:{cols};gap:6px;align-items:start;">']
    for e in entries:
        nw = natural_width(os.path.normpath(os.path.join(base_dir, e["path"])))
        cap = f";max-width:{nw}px" if nw and nw < 500 else ""
        alt = e["alt"].replace('"', "&quot;")
        out.append(f'<img src="{e["path"]}" alt="{alt}" style="width:100%{cap}">')
    out.append("</div>")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=DEFAULT_VAULT)
    ap.add_argument("--stage", default=DEFAULT_STAGE)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.apply and not args.dry_run:
        ap.error("choose --dry-run or --apply")

    fulltext_dir = os.path.join(args.vault, "03fulltext")
    idx = index_structured(args.stage)
    log_rows: list[tuple[str, int, str]] = []

    for path in sorted(glob.glob(os.path.join(fulltext_dir, "*", "*.md"))):
        key = os.path.splitext(os.path.basename(path))[0]
        text = open(path, encoding="utf-8").read()
        if f"images/{key}/page_" not in text:
            continue
        bboxes = load_bbox_map(idx[key]) if key in idx else {}

        lines = text.splitlines()
        todo = []
        for run in find_runs(lines):
            if same_band(run, bboxes):
                run.sort(key=lambda e: bboxes[os.path.basename(e["path"])][0])
                todo.append(run)
        if not todo:
            continue

        rel = os.path.relpath(path, args.vault).replace("\\", "/")
        print(f"{rel}: {len(todo)} row(s)")
        for run in todo:
            log_rows.append((rel, len(run), " | ".join(os.path.basename(e["path"]) for e in run)))
        if args.dry_run:
            continue

        new_lines = list(lines)
        for run in sorted(todo, key=lambda r: -min(e["idx"] for e in r)):
            start = min(e["idx"] for e in run)
            end = max(e["idx"] for e in run)
            new_lines[start:end + 1] = render_row(run, bboxes, os.path.dirname(path))

        new_text = "\n".join(new_lines)
        old_count = len(re.findall(r"!\[", text)) + text.count("<img ")
        new_count = len(re.findall(r"!\[", new_text)) + new_text.count("<img ")
        if old_count != new_count:
            print("SKIP ref-count mismatch", rel, old_count, new_count)
            log_rows = log_rows[:-len(todo)]
            continue
        if new_text.count("<div") != text.count("<div") + len(todo):
            print("SKIP div-count mismatch", rel)
            log_rows = log_rows[:-len(todo)]
            continue
        open(path, "w", encoding="utf-8", newline="\n").write(new_text + "\n")

    if args.apply and log_rows:
        existing: list[list[str]] = []
        if os.path.exists(args.log):
            existing = [l.split("\t") for l in open(args.log, encoding="utf-8").read().splitlines()[1:] if l.strip()]
        seen = {(r[0], r[2]) for r in existing}
        merged = [tuple(r) for r in existing]
        for r in log_rows:
            if (r[0], r[2]) not in seen:
                merged.append(r)
                seen.add((r[0], r[2]))
        with open(args.log, "w", encoding="utf-8", newline="") as f:
            f.write("file\timages\torder\n")
            for r in merged:
                f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
        print("log:", args.log)
    print("rows:", len(log_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
