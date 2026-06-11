#!/usr/bin/env python3
"""Export Taskory state into AI Board friendly JSONL.

The output is intentionally simple: one JSON object per task/memo node with
path, flags, memo text, and a search-ready text field.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_ID = "root"


def load_state(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), dict):
        raise ValueError(f"Not a Taskory state file: {path}")
    return data


def node_path(nodes: dict, node_id: str) -> list[str]:
    parts: list[str] = []
    current = nodes.get(node_id)
    seen: set[str] = set()
    while current and current.get("id") != ROOT_ID:
        current_id = str(current.get("id") or "")
        if current_id in seen:
            break
        seen.add(current_id)
        parts.append(str(current.get("title") or "이름 없음"))
        current = nodes.get(current.get("parentId"))
    return list(reversed(parts))


def iter_records(state: dict) -> list[dict]:
    nodes = state.get("nodes", {})
    records: list[dict] = []
    for node_id, node in nodes.items():
        if node_id == ROOT_ID or not isinstance(node, dict):
            continue
        path = node_path(nodes, node_id)
        title = str(node.get("title") or "이름 없음").strip() or "이름 없음"
        memo = str(node.get("memo") or "").strip()
        flags = []
        if node.get("isToday"):
            flags.append("today")
        if node.get("isImportant"):
            flags.append("important")
        if node.get("completed"):
            flags.append("completed")
        if node.get("isCustomFolder"):
            flags.append("folder")
        kind = "memo" if node.get("kind") == "memo" else "task"
        text_parts = [
            f"제목: {title}",
            f"경로: {' > '.join(path)}",
            f"종류: {kind}",
            f"상태: {', '.join(flags) if flags else 'normal'}",
        ]
        if node.get("priority") is not None:
            text_parts.append(f"우선순위: {node.get('priority')}")
        if memo:
            text_parts.append(f"메모: {memo}")
        records.append(
            {
                "id": node.get("id") or node_id,
                "title": title,
                "path": path,
                "kind": kind,
                "memo": memo,
                "flags": flags,
                "priority": node.get("priority"),
                "createdAt": node.get("createdAt"),
                "completedAt": node.get("completedAt"),
                "parentId": node.get("parentId"),
                "children": node.get("children") or [],
                "text": "\n".join(text_parts),
            }
        )
    return sorted(records, key=lambda item: (item.get("path") or [], item.get("createdAt") or ""))


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Taskory state to AI Board JSONL")
    parser.add_argument("state", type=Path, help="Path to task-explorer-state.json")
    parser.add_argument("-o", "--output", type=Path, help="Output JSONL path. Defaults to stdout.")
    parser.add_argument("--pretty-json", action="store_true", help="Write a JSON array instead of JSONL.")
    args = parser.parse_args()

    records = iter_records(load_state(args.state))
    if args.pretty_json:
        payload = json.dumps(records, ensure_ascii=False, indent=2)
    else:
        payload = "\n".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in records)
        if payload:
            payload += "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
