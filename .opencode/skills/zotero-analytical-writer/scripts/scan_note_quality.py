#!/usr/bin/env python3
"""Scan ResearchVault Analytical Notes for method-migration quality.

Usage:
  python scan_note_quality.py --vault "D:\\path\\to\\researchVault"
  python scan_note_quality.py --vault ... --gaps          # list per-note method gaps
  python scan_note_quality.py --vault ... --strict        # gaps also fail the run
  python scan_note_quality.py --vault ... --json out.json

Exits 1 when a hard failure is found (broken image, YAML error, legacy method
heading, duplicate method heading, missing method section, etc.). With
--strict, method-completeness gaps are also counted as hard failures.
"""

import argparse
import collections
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

COLLECTIONS = ["MOT", "SAM", "VOS", "RS", "VIS"]
TRANSLATION_MARKERS = ("中文全译",)

# Method-completeness dimensions. A gap is reported when none of the keywords
# appears in the chosen scope. "论文未给" / "原文无公式" count as explicit
# waivers, not omissions.
COMPLETENESS_CHECKS = [
    ("task-io", "note", ("输入", "输出", "task", "input", "output", "token", "张量", "尺寸")),
    ("architecture", "method", ("架构", "总体", "共享", "冻结", "编码器", "backbone", "模块")),
    ("module-mechanism", "method", ("模块", "算子", "注意力", "attention", "门控", "匹配", "公式")),
    ("math-formula", "method", ("$$", "公式", "原文无公式", "无公式")),
    ("train-config", "note", ("优化器", "Adam", "学习率", "lr", "batch", "epoch", "迭代", "论文未给", "原文未给")),
    ("loss-detail", "note", ("损失", "loss", "权重", "BCE", "focal", "dice", "IoU", "论文未给")),
    ("inference-rule", "note", ("推理", "阈值", "门控", "后处理", "NMS", "top-", "延迟", "论文未给")),
    ("ablation-evidence", "note", ("消融", "ablation", "去掉", "Table", "表 ", "表")),
    ("boundary", "note", ("边界", "局限", "失效", "失败", "域差", "未报告", "SOT", "单来源")),
    ("compute-cost", "note", ("参数", "FLOPs", "FPS", "显存", "算力", "论文未给")),
]
HARD_PREFIXES = (
    "missing-method-section", "legacy-method-heading",
    "duplicate-method-heading", "broken-image", "empty-fulltext-path",
    "img<4-no-note", "formula<2-no-note", "no-quote-section",
)


def read(path):
    return open(path, encoding="utf-8", errors="ignore").read()


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    try:
        return yaml.safe_load(text.split("---", 2)[1]) or {} if yaml else {}
    except Exception:
        return {}


def method_section(text):
    m = re.search(r"^##\s*三、方法详解[^\n]*\n(.*?)(?=^##\s)", text, re.S | re.M)
    if m:
        return m.group(1)
    m = re.search(r"^##\s*(?:研究方法|方法)\s*\n(.*?)(?=^##\s)", text, re.S | re.M)
    return m.group(1) if m else ""


def method_gaps(text, body):
    """Return soft completeness gaps for a note's method section."""
    gaps = []
    for name, scope, keywords in COMPLETENESS_CHECKS:
        hay = body if scope == "method" else text
        if not any(k in hay for k in keywords):
            gaps.append(name)
    # Page verification is a separate, high-value check.
    n_unverified = text.count("PDF 页码未验证")
    if n_unverified:
        gaps.append(f"quote-page-unverified:{n_unverified}")
    return gaps


def scan(vault):
    root = os.path.join(vault, "02vault")
    rows = []
    for col in COLLECTIONS:
        d = os.path.join(root, col)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md") or any(x in name for x in TRANSLATION_MARKERS):
                continue
            path = os.path.join(d, name)
            text = read(path)
            fm = frontmatter(text)
            body = method_section(text)
            mlen = len(body)
            imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
            broken = [x for x in imgs if not os.path.exists(os.path.normpath(os.path.join(d, x)))]
            has_quote = "引文核验" in text
            formulas = text.count("$$") // 2
            no_formula_note = "原文无公式" in text or "无公式" in text
            single_formula_note = any(k in text for k in (
                "原文仅 1", "原文仅一", "原文只有 1", "原文只有一",
                "仅 1 个编号", "仅一个编号", "原文仅此一",
            ))
            no_img_note = any(k in text for k in ("原文仅", "原文图不足", "原文只有", "原文共", "原文可用图", "图注缺失", "未能嵌入"))
            legacy = bool(re.search(r"^##\s*(?:研究方法|方法)\s*$", text, re.M))
            dup = text.count("## 三、方法详解")
            flags = []
            if not body:
                flags.append("missing-method-section")
            if legacy:
                flags.append("legacy-method-heading")
            if dup > 1:
                flags.append(f"duplicate-method-heading:{dup}")
            if broken:
                flags.append(f"broken-image:{len(broken)}")
            if mlen >= 4500 and len(imgs) < 4 and not no_img_note:
                flags.append("img<4-no-note")
            if mlen >= 4500 and formulas < 2 and not (no_formula_note or single_formula_note):
                flags.append("formula<2-no-note")
            if mlen >= 4500 and not has_quote:
                flags.append("no-quote-section")
            if not fm.get("fulltext_path"):
                flags.append("empty-fulltext-path")
            status = "FULL" if mlen >= 4500 else ("BORDER" if mlen >= 4000 else "PENDING")
            rows.append(dict(collection=col, file=name, status=status,
                             method_chars=mlen, images=len(imgs),
                             formulas=formulas, flags=flags,
                             gaps=method_gaps(text, body)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="ResearchVault root")
    ap.add_argument("--json", help="write JSON result")
    ap.add_argument("--gaps", action="store_true", help="list method-completeness gaps per note")
    ap.add_argument("--strict", action="store_true", help="treat method gaps as hard failures")
    args = ap.parse_args()

    rows = scan(args.vault)
    hard = [r for r in rows if any(f.startswith(HARD_PREFIXES) for f in r["flags"])]
    with_gaps = [r for r in rows if r["gaps"]]
    strict_hard = [r for r in with_gaps] if args.strict else []

    print(f"{'col':4s} {'status':7s} {'chars':>6s} {'img':>4s} {'form':>4s}  note / flags")
    for r in sorted(rows, key=lambda x: (x["collection"], x["status"], x["method_chars"])):
        print(f"{r['collection']:4s} {r['status']:7s} {r['method_chars']:6d} "
              f"{r['images']:4d} {r['formulas']:4d}  {r['file'][:70]}  {r['flags']}")

    print("\nCOUNTS")
    for col in COLLECTIONS:
        sub = [r for r in rows if r["collection"] == col]
        print(col, "total", len(sub),
              "FULL", sum(r["status"] == "FULL" for r in sub),
              "BORDER", sum(r["status"] == "BORDER" for r in sub),
              "PENDING", sum(r["status"] == "PENDING" for r in sub))
    print("TOTAL", len(rows), "FULL", sum(r["status"] == "FULL" for r in rows),
          "HARD", len(hard))

    print("\nMETHOD COMPLETENESS (soft; use --strict to fail on these)")
    counter = collections.Counter()
    for r in with_gaps:
        for g in r["gaps"]:
            counter[g.split(":")[0]] += 1
    for key, n in counter.most_common():
        print(f"  {key:26s} {n}")
    print("notes-with-gaps", len(with_gaps), "strict-hard", len(strict_hard))

    if args.gaps:
        print("\nPER-NOTE GAPS")
        for r in sorted(with_gaps, key=lambda x: (-len(x["gaps"]), x["collection"], x["file"])):
            print(f"  {r['collection']:4s} {r['file'][:64]:64s} {','.join(r['gaps'])}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        print("wrote", args.json)

    return 1 if (hard or strict_hard) else 0


if __name__ == "__main__":
    sys.exit(main())
