#!/usr/bin/env python
"""Verify Taskory AI helpers without calling external APIs."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import task_explorer_native as taskory


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def fake_urlopen(request, timeout=0):
    url = getattr(request, "full_url", "")
    if url.endswith("/chat/completions"):
        return FakeResponse({"choices": [{"message": {"content": "프로젝트 준비 {today}\n  요구사항 정리\n  [memo] 참고\n  > 회의록 확인"}}]})
    if url.endswith("/audio/transcriptions"):
        return FakeResponse({"text": "회의에서 로그인 화면과 배포 확인을 논의했습니다."})
    raise AssertionError(f"Unexpected URL: {url}")


def main() -> int:
    original_urlopen = taskory.urllib.request.urlopen
    taskory.urllib.request.urlopen = fake_urlopen
    try:
        preview = taskory.openai_breakdown_text("test-key", "프로젝트 준비를 작업으로 나눠줘")
        parsed = taskory.parse_tree_text_detailed(preview)
        assert not parsed["errors"], parsed["errors"]
        assert len(parsed["rows"]) == 3, parsed["rows"]
        assert parsed["rows"][0]["title"] == "프로젝트 준비"
        assert parsed["rows"][0]["isToday"] is True
        assert parsed["rows"][2]["kind"] == "memo"

        with tempfile.TemporaryDirectory(prefix="taskory-ai-verify-") as tmp:
            audio = Path(tmp) / "sample.wav"
            audio.write_bytes(b"RIFF0000WAVE")
            body, content_type = taskory.multipart_form({"model": "whisper-1"}, "file", audio)
            assert b'name="file"; filename="sample.wav"' in body
            assert content_type.startswith("multipart/form-data; boundary=")
            transcript = taskory.openai_transcribe_file("test-key", audio)
            assert "로그인 화면" in transcript
            parts, temp_dir = taskory.split_audio_for_transcription(audio)
            assert parts == [audio]
            assert temp_dir is None
    finally:
        taskory.urllib.request.urlopen = original_urlopen

    print(json.dumps({"ok": True, "checked": ["openai_breakdown_text", "openai_transcribe_file", "multipart_form", "split_audio_for_transcription"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
