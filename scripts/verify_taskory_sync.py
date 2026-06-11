#!/usr/bin/env python
"""Verify Taskory -> AI Board sync replacement safety without network access."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import urllib.error
from pathlib import Path

import sync_taskory_to_ai_board as sync


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def write_state(path: Path, title: str = "Taskory Sync Verify") -> None:
    payload = {
        "nodes": {
            "root": {"title": "root", "children": ["project"]},
            "project": {"title": title, "memo": "AI Board RAG 동기화 검증", "children": ["child"]},
            "child": {"title": "업로드 후 교체", "memo": "성공 전에는 기존 자료를 삭제하지 않습니다."},
        }
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_args(state: Path, hash_file: Path, *, force: bool = False, append: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        state=state,
        hash_file=hash_file,
        base_url="http://ai-board.local",
        title="Taskory Sync Verify",
        instruction="Taskory 작업을 AI Board RAG로 사용합니다.",
        tags="taskory,verify",
        dry_run=False,
        force=force,
        append=append,
    )


def test_success_replaces_only_after_upload() -> None:
    calls: list[tuple[str, str]] = []

    def fake_urlopen(request, timeout=30):
        method = request.get_method()
        url = request.full_url
        calls.append((method, url))
        if method == "POST" and url.endswith("/api/knowledge/upload"):
            return FakeResponse({"source": {"id": 200, "title": "Taskory Sync Verify"}})
        if method == "GET" and url.endswith("/api/knowledge"):
            return FakeResponse(
                {
                    "sources": [
                        {"id": 100, "title": "Taskory Sync Verify", "sourceType": "taskory"},
                        {"id": 200, "title": "Taskory Sync Verify", "sourceType": "taskory"},
                        {"id": 300, "title": "Other", "sourceType": "taskory"},
                        {"id": 400, "title": "Taskory Sync Verify", "sourceType": "document"},
                    ]
                }
            )
        if method == "DELETE" and url.endswith("/api/knowledge/100"):
            return FakeResponse({"ok": True})
        raise AssertionError(f"Unexpected request: {method} {url}")

    original = sync.urllib.request.urlopen
    sync.urllib.request.urlopen = fake_urlopen
    try:
        with tempfile.TemporaryDirectory(prefix="taskory-sync-verify-") as tmp:
            root = Path(tmp)
            state = root / "state.json"
            hash_file = root / ".sync.sha256"
            write_state(state)
            result = sync.sync_once(make_args(state, hash_file), "token")
            assert result["status"] == "uploaded", result
            assert result["sourceId"] == 200, result
            assert result["replaced"] == 1, result
            assert hash_file.exists(), "hash must be written after a successful upload"
            upload_index = calls.index(("POST", "http://ai-board.local/api/knowledge/upload"))
            delete_index = calls.index(("DELETE", "http://ai-board.local/api/knowledge/100"))
            assert upload_index < delete_index, calls

            calls.clear()
            skipped = sync.sync_once(make_args(state, hash_file), "token")
            assert skipped["status"] == "skipped", skipped
            assert calls == [], calls
    finally:
        sync.urllib.request.urlopen = original


def test_failed_upload_does_not_delete_or_write_hash() -> None:
    calls: list[tuple[str, str]] = []

    def fake_urlopen(request, timeout=30):
        method = request.get_method()
        url = request.full_url
        calls.append((method, url))
        if method == "POST" and url.endswith("/api/knowledge/upload"):
            raise urllib.error.HTTPError(url, 500, "upload failed", {}, io.BytesIO(b'{"detail":"boom"}'))
        raise AssertionError(f"Unexpected request after failed upload: {method} {url}")

    original = sync.urllib.request.urlopen
    sync.urllib.request.urlopen = fake_urlopen
    try:
        with tempfile.TemporaryDirectory(prefix="taskory-sync-verify-") as tmp:
            root = Path(tmp)
            state = root / "state.json"
            hash_file = root / ".sync.sha256"
            write_state(state)
            try:
                sync.sync_once(make_args(state, hash_file), "token")
            except sync.SyncError as exc:
                assert "HTTP 500" in str(exc), exc
            else:
                raise AssertionError("failed upload should raise SyncError")
            assert not hash_file.exists(), "failed upload must not write the last-sync hash"
            assert all(method != "DELETE" for method, _ in calls), calls
    finally:
        sync.urllib.request.urlopen = original


def main() -> int:
    test_success_replaces_only_after_upload()
    test_failed_upload_does_not_delete_or_write_hash()
    print(json.dumps({"ok": True, "checked": ["upload_before_delete", "skip_unchanged", "failed_upload_preserves_existing_sources"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
