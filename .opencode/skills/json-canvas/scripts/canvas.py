#!/usr/bin/env python3
"""Minimal JSON Canvas (Obsidian .canvas) validator and creator."""

from __future__ import annotations

import argparse
import json
import os
import sys

NODE_TYPES = {"text", "file", "link", "group"}
SIDES = {"top", "right", "bottom", "left"}
ENDS = {"none", "arrow"}


def new_canvas() -> dict:
    return {"nodes": [], "edges": []}


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list):
        errors.append("nodes must be an array")
        nodes = []
    if not isinstance(edges, list):
        errors.append("edges must be an array")
        edges = []

    node_ids = set()
    for i, node in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(node, dict):
            errors.append(f"{where}: must be an object")
            continue
        nid = node.get("id")
        if not isinstance(nid, str) or not nid:
            errors.append(f"{where}: missing string id")
        elif nid in node_ids:
            errors.append(f"{where}: duplicate id {nid!r}")
        else:
            node_ids.add(nid)
        ntype = node.get("type")
        if ntype not in NODE_TYPES:
            errors.append(f"{where}: invalid type {ntype!r}")
        for field in ("x", "y", "width", "height"):
            if not isinstance(node.get(field), (int, float)):
                errors.append(f"{where}: {field} must be a number")
        if isinstance(node.get("width"), (int, float)) and node["width"] <= 0:
            errors.append(f"{where}: width must be > 0")
        if isinstance(node.get("height"), (int, float)) and node["height"] <= 0:
            errors.append(f"{where}: height must be > 0")
        if ntype == "text" and not isinstance(node.get("text"), str):
            errors.append(f"{where}: text node needs string text")
        if ntype == "file" and not isinstance(node.get("file"), str):
            errors.append(f"{where}: file node needs string file")
        if ntype == "link" and not isinstance(node.get("url"), str):
            errors.append(f"{where}: link node needs string url")
        if ntype == "group" and not isinstance(node.get("label"), str):
            errors.append(f"{where}: group node needs string label")
        color = node.get("color")
        if color is not None and not (isinstance(color, str) and (color in {str(i) for i in range(1, 7)} or color.startswith("#"))):
            errors.append(f"{where}: color must be '1'..'6' or #RRGGBB")

    edge_ids = set()
    for i, edge in enumerate(edges):
        where = f"edges[{i}]"
        if not isinstance(edge, dict):
            errors.append(f"{where}: must be an object")
            continue
        eid = edge.get("id")
        if not isinstance(eid, str) or not eid:
            errors.append(f"{where}: missing string id")
        elif eid in edge_ids:
            errors.append(f"{where}: duplicate id {eid!r}")
        else:
            edge_ids.add(eid)
        for endpoint in ("fromNode", "toNode"):
            value = edge.get(endpoint)
            if value not in node_ids:
                errors.append(f"{where}: {endpoint} {value!r} does not reference a node")
        for side in ("fromSide", "toSide"):
            if side in edge and edge[side] not in SIDES:
                errors.append(f"{where}: invalid {side} {edge[side]!r}")
        for end in ("fromEnd", "toEnd"):
            if end in edge and edge[end] not in ENDS:
                errors.append(f"{where}: invalid {end} {edge[end]!r}")
        color = edge.get("color")
        if color is not None and not (isinstance(color, str) and (color in {str(i) for i in range(1, 7)} or color.startswith("#"))):
            errors.append(f"{where}: color must be '1'..'6' or #RRGGBB")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new")
    p.add_argument("--out", required=True)

    p = sub.add_parser("validate")
    p.add_argument("file")

    args = ap.parse_args()
    if args.cmd == "new":
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(new_canvas(), f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("wrote", args.out)
        return 0

    data = json.load(open(args.file, encoding="utf-8"))
    errors = validate(data)
    if errors:
        print(f"INVALID {args.file}: {len(errors)} error(s)")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK {args.file}: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
