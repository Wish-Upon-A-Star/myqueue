#!/usr/bin/env python
"""Sync Taskory state into AI Board knowledge.

This script logs in to AI Board, exports the local Taskory state, and uploads it
as a Taskory RAG knowledge source. It only uploads when the state file changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

from export_taskory_for_ai_board import iter_records, load_state


DEFAULT_TAGS = "taskory,ai-board,rag"


class SyncError(RuntimeError):
    pass


def state_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_json(url: str, *, method: str = "GET", token: str = "", data: bytes | None = None, content_type: str = "application/json") -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SyncError(f"AI Board request failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SyncError(f"AI Board is not reachable: {exc.reason}") from exc


def login(base_url: str, email: str, password: str) -> str:
    payload = json.dumps({"email": email, "password": password}, ensure_ascii=False).encode("utf-8")
    response = request_json(f"{base_url}/api/auth/login", method="POST", data=payload)
    token = response.get("token")
    if not token:
        raise SyncError("AI Board login did not return a token.")
    return str(token)


def export_jsonl(state_path: Path, output_path: Path) -> int:
    records = iter_records(load_state(state_path))
    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in records),
        encoding="utf-8",
    )
    return len(records)


def multipart_body(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----taskory-ai-board-{uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/x-ndjson"
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def upload_knowledge(base_url: str, token: str, export_path: Path, *, title: str, instruction: str, tags: str) -> dict:
    body, content_type = multipart_body(
        {
            "title": title,
            "source_type": "taskory",
            "instruction": instruction,
            "tags": tags,
        },
        "file",
        export_path,
    )
    return request_json(f"{base_url}/api/knowledge/upload", method="POST", token=token, data=body, content_type=content_type)


def delete_previous_taskory_sources(base_url: str, token: str, title: str, keep_source_id: int | str | None) -> int:
    if keep_source_id is None:
        return 0
    keep_id = str(keep_source_id)
    response = request_json(f"{base_url}/api/knowledge", token=token)
    sources = response.get("sources") or []
    deleted = 0
    for source in sources:
        if not isinstance(source, dict):
            continue
        if source.get("title") != title or source.get("sourceType") != "taskory":
            continue
        source_id = source.get("id")
        if source_id is None:
            continue
        if str(source_id) == keep_id:
            continue
        request_json(f"{base_url}/api/knowledge/{source_id}", method="DELETE", token=token)
        deleted += 1
    return deleted


def read_last_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_last_hash(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def sync_once(args: argparse.Namespace, token: str) -> dict:
    state_path = args.state.resolve()
    if not state_path.exists():
        raise SyncError(f"Taskory state file not found: {state_path}")

    current_hash = state_hash(state_path)
    hash_path = args.hash_file.resolve()
    previous_hash = read_last_hash(hash_path)
    if previous_hash == current_hash and not args.force:
        return {"status": "skipped", "reason": "state unchanged", "state": str(state_path)}

    with tempfile.TemporaryDirectory(prefix="taskory-ai-board-") as tmp:
        export_path = Path(tmp) / "taskory-ai-board.jsonl"
        count = export_jsonl(state_path, export_path)
        if args.dry_run:
            return {"status": "dry-run", "records": count, "export": str(export_path), "stateHash": current_hash}
        response = upload_knowledge(
            args.base_url.rstrip("/"),
            token,
            export_path,
            title=args.title,
            instruction=args.instruction,
            tags=args.tags,
        )

    write_last_hash(hash_path, current_hash)
    source = response.get("source", {})
    replaced = 0
    if not args.append:
        replaced = delete_previous_taskory_sources(args.base_url.rstrip("/"), token, args.title, source.get("id"))
    return {
        "status": "uploaded",
        "records": count,
        "sourceId": source.get("id"),
        "sourceTitle": source.get("title"),
        "replaced": replaced,
        "stateHash": current_hash,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Taskory state to AI Board RAG knowledge")
    parser.add_argument("--state", type=Path, default=Path("task-explorer-state.json"), help="Taskory state JSON path")
    parser.add_argument("--base-url", default=os.environ.get("AI_BOARD_BASE_URL", "http://127.0.0.1:8000"), help="AI Board API base URL")
    parser.add_argument("--email", default=os.environ.get("AI_BOARD_EMAIL", ""), help="AI Board login email")
    parser.add_argument("--password", default=os.environ.get("AI_BOARD_PASSWORD", ""), help="AI Board login password")
    parser.add_argument("--token", default=os.environ.get("AI_BOARD_TOKEN", ""), help="Existing AI Board bearer token")
    parser.add_argument("--title", default="Taskory 작업 동기화", help="Knowledge source title")
    parser.add_argument(
        "--instruction",
        default="Taskory 작업 목록을 GitHub, Notion, Figma, Calendar 자동화의 업무 맥락으로 참고하세요.",
        help="AI Board knowledge instruction",
    )
    parser.add_argument("--tags", default=DEFAULT_TAGS, help="Comma separated tags")
    parser.add_argument("--hash-file", type=Path, default=Path(".taskory-ai-board-sync.sha256"), help="Last synced hash file")
    parser.add_argument("--force", action="store_true", help="Upload even when the state hash is unchanged")
    parser.add_argument("--append", action="store_true", help="Keep previous Taskory knowledge sources instead of replacing the same title")
    parser.add_argument("--dry-run", action="store_true", help="Export and validate without uploading")
    parser.add_argument("--watch", action="store_true", help="Keep syncing in a loop")
    parser.add_argument("--interval", type=int, default=300, help="Watch interval seconds")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.interval < 10:
        raise SyncError("--interval must be at least 10 seconds")

    token = args.token
    if not token and not args.dry_run:
        if not args.email or not args.password:
            raise SyncError("Set --token or both --email and --password, or use --dry-run.")
        token = login(args.base_url.rstrip("/"), args.email, args.password)

    while True:
        result = sync_once(args, token)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if not args.watch:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
