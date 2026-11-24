#!/usr/bin/env python3
"""Local paper registry: resolve, register, validate (no Zotero required)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys

COLUMNS = [
    "paper_id", "title", "authors", "year", "venue", "doi", "arxiv_id",
    "collection", "pdf_path", "fulltext_path", "note_path", "status",
    "page_mapping",
]


def sha1(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z.]+", "_", value).strip("_")


def pdf_metadata(path: str) -> dict:
    try:
        from pypdf import PdfReader
        meta = PdfReader(path).metadata or {}
        created = str(meta.get("/CreationDate") or "")
        year_match = re.search(r"(?:19|20)\d{2}", created)
        return {
            "title": str(meta.get("/Title") or "").strip(),
            "authors": str(meta.get("/Author") or "").strip(),
            "year": year_match.group(0) if year_match else "",
        }
    except Exception:
        return {}


def infer_arxiv(*values: str) -> str:
    for value in values:
        m = re.search(r"(\d{4}\.\d{4,5})", value or "")
        if m:
            return m.group(1)
    return ""


def paper_id_for(pdf: str, arxiv_id: str, doi: str) -> str:
    if arxiv_id:
        return "arxiv_" + sanitize(arxiv_id)
    if doi:
        return "doi_" + sanitize(doi.lower())
    if pdf and os.path.exists(pdf):
        return "pdf_" + sha1(pdf)[:12]
    raise SystemExit("cannot derive paper_id without PDF, arXiv ID, or DOI")


def load_rows(registry: str) -> list[dict]:
    if not os.path.exists(registry):
        return []
    with open(registry, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_rows(registry: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(registry)), exist_ok=True)
    with open(registry, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def cmd_resolve(args) -> int:
    meta = pdf_metadata(args.pdf) if args.pdf else {}
    arxiv_id = args.arxiv_id or infer_arxiv(args.title or "", os.path.basename(args.pdf or ""))
    doi = args.doi or ""
    pid = args.paper_id or paper_id_for(args.pdf, arxiv_id, doi)
    out = {
        "paper_id": pid,
        "title": args.title or meta.get("title", ""),
        "authors": args.authors or meta.get("authors", ""),
        "year": args.year or meta.get("year", ""),
        "venue": args.venue or "",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "collection": args.collection or "",
        "pdf_path": (args.pdf or "").replace("\\", "/"),
        "fulltext_path": "",
        "note_path": "",
        "status": "PDF_ONLY" if args.pdf else "DEFERRED",
        "page_mapping": "unknown",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_register(args) -> int:
    rows = load_rows(args.registry)
    meta = pdf_metadata(args.pdf) if args.pdf else {}
    arxiv_id = args.arxiv_id or infer_arxiv(args.title or "", os.path.basename(args.pdf or ""))
    pid = args.paper_id or paper_id_for(args.pdf, arxiv_id, args.doi or "")
    existing = next((r for r in rows if r["paper_id"] == pid), None)
    row = existing or {k: "" for k in COLUMNS}
    row["paper_id"] = pid
    for key, value in {
        "title": args.title or meta.get("title", ""),
        "authors": args.authors or meta.get("authors", ""),
        "year": args.year or meta.get("year", ""),
        "venue": args.venue or "",
        "doi": args.doi or "",
        "arxiv_id": arxiv_id,
        "collection": args.collection or row.get("collection", ""),
        "pdf_path": (args.pdf or row.get("pdf_path", "")).replace("\\", "/"),
    }.items():
        if value:
            row[key] = value
    if not row.get("status"):
        row["status"] = "PDF_ONLY"
    if not row.get("page_mapping"):
        row["page_mapping"] = "unknown"
    if existing is None:
        rows.append(row)
    write_rows(args.registry, rows)
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args) -> int:
    rows = load_rows(args.registry)
    errors = []
    seen = set()
    for r in rows:
        pid = r.get("paper_id", "")
        if not pid:
            errors.append("empty paper_id")
        if pid in seen:
            errors.append(f"duplicate paper_id: {pid}")
        seen.add(pid)
        if r.get("pdf_path") and not os.path.exists(r["pdf_path"]):
            errors.append(f"{pid}: missing PDF {r['pdf_path']}")
        if args.vault:
            for field in ("fulltext_path", "note_path"):
                rel = r.get(field, "")
                if rel and not os.path.exists(os.path.join(args.vault, rel)):
                    errors.append(f"{pid}: missing {field} {rel}")
    print(f"rows={len(rows)} unique={len(seen)} errors={len(errors)}")
    for e in errors:
        print(e)
    return 1 if errors else 0


def cmd_list(args) -> int:
    rows = load_rows(args.registry)
    for r in rows:
        if args.collection and r.get("collection") != args.collection:
            continue
        if args.status and r.get("status") != args.status:
            continue
        print(f"{r['paper_id']}\t{r.get('collection','')}\t{r.get('status','')}\t{r.get('title','')[:90]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("resolve")
    p.add_argument("--pdf")
    for k in ("title", "authors", "year", "venue", "doi", "arxiv-id", "collection", "paper-id"):
        p.add_argument("--" + k, dest=k.replace("-", "_"))
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("register")
    p.add_argument("--registry", required=True)
    p.add_argument("--pdf")
    for k in ("title", "authors", "year", "venue", "doi", "arxiv-id", "collection", "paper-id"):
        p.add_argument("--" + k, dest=k.replace("-", "_"))
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("validate")
    p.add_argument("--registry", required=True)
    p.add_argument("--vault")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("list")
    p.add_argument("--registry", required=True)
    p.add_argument("--collection")
    p.add_argument("--status")
    p.set_defaults(func=cmd_list)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
