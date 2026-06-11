# Taskory

Taskory (태스토리) is a desktop task queue app for breaking large work into smaller tasks and notes.

The current app is built with Python and customtkinter. It does not use Electron.

## Downloads

Use the package for your operating system:

- Windows: `Taskory-windows.zip`
- macOS Intel: `Taskory-macos-intel.zip`
- macOS Apple Silicon: `Taskory-macos-arm64.zip`

Check your Mac type:

```bash
uname -m
```

- `x86_64`: Intel Mac
- `arm64`: Apple Silicon Mac

## Windows launch

1. Unzip `Taskory-windows.zip`.
2. Run `Taskory/Taskory.exe`.

Windows data files are stored next to the executable:

```text
Taskory/task-explorer-state.json
Taskory/activity-log.db
```

## macOS launch

The macOS zip contains a folder like this:

```text
Taskory-macos-arm64/
  Taskory.app
  run.command
  README-mac.txt
```

For the first launch, use `run.command` instead of double-clicking the app directly.

1. Unzip the package.
2. Double-click `run.command`.
3. If macOS blocks it, right-click `run.command` and choose `Open`.
4. If it launches successfully, you can move `Taskory.app` to Applications later.

Terminal launch:

```bash
cd ~/Downloads/Taskory-macos-arm64
chmod +x run.command
./run.command
```

For Intel Mac, use the Intel folder name:

```bash
cd ~/Downloads/Taskory-macos-intel
chmod +x run.command
./run.command
```

`run.command` performs these checks automatically:

- fixes executable permissions when possible
- removes macOS quarantine attributes when possible
- runs `Taskory.app/Contents/MacOS/Taskory --smoke-test`
- opens `Taskory.app`
- writes logs for debugging

macOS logs:

```text
~/Library/Application Support/Taskory/Taskory-run-command.log
~/Library/Application Support/Taskory/Taskory-launcher.log
~/Library/Application Support/Taskory/Taskory-boot.log
~/Library/Application Support/Taskory/Taskory-startup-error.log
```

macOS data files:

```text
~/Library/Application Support/Taskory/task-explorer-state.json
~/Library/Application Support/Taskory/activity-log.db
```

## Main features

- Tree-based task breakdown
- Add, edit, delete, copy tasks
- Task and memo separation
- Memo blocks and image memo blocks
- Today, important, completed, priority views
- Eisenhower matrix view
- Current subtree view
- TXT export/import
- Saved lists and project folders
- Created/completed date views
- Activity logging by app, title, time, and group
- Mini memo mode
- AI task breakdown from pasted text using an OpenAI API key
- Audio transcription into task-ready text, including large-file splitting when `ffmpeg.exe` is available
- AI preview before adding generated tasks and memos to the current folder
- AI Board friendly JSONL export for RAG or Notion/GitHub automation handoff

## Paste tree example

```text
Socket object
??? State
??? Address info
??? Buffer
??? Options
```

Indented text also works:

```text
Parent task
  Child task 1
  Child task 2
    Smaller task
```

## OpenAI task breakdown and audio transcription

Taskory can turn rough pasted text into an import preview before anything is added to the current folder.

1. Set `OPENAI_API_KEY`, or enter the key when Taskory asks for it.
2. Open `도구`.
3. Click `구조 붙여넣기`.
4. Paste rough notes into the paste box.
5. Click `AI 분해 미리보기`.
6. Review or edit the generated tree.
7. Click `붙여넣기 추가` only when the preview looks right.

Optional model settings:

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:TASKORY_OPENAI_MODEL="gpt-4o-mini"
$env:TASKORY_TRANSCRIBE_MODEL="whisper-1"
```

Audio transcription:

1. Click `도구` → `음성 전사`.
2. Pick an audio file.
3. Taskory sends the file to OpenAI transcription and places the transcript in the paste box.
4. Click `AI 분해 미리보기` if you want the transcript converted into a task tree.

Large audio files over 24MB require `ffmpeg` in `PATH`. When `ffmpeg` is available, Taskory splits the audio into smaller MP3 chunks and transcribes them in order.

## AI Board export

Taskory can export its local task tree into JSONL that is easy for AI Board to ingest as RAG knowledge or automation input.

```bash
python scripts/export_taskory_for_ai_board.py task-explorer-state.json -o taskory-ai-board.jsonl
```

Pretty JSON output is also available:

```bash
python scripts/export_taskory_for_ai_board.py task-explorer-state.json --pretty-json -o taskory-ai-board.json
```

Each exported record contains:

- `title`
- `path`
- `kind`
- `memo`
- `flags`
- `priority`
- `createdAt`
- `completedAt`
- `text`

The `text` field is a compact Korean summary designed for search, RAG, and Notion/GitHub report generation.

### AI Board sync

You can also upload the current Taskory state directly to AI Board. The sync script logs in, exports JSONL, replaces the previous Taskory knowledge source with the same title, uploads the new file to `/api/knowledge/upload`, and skips repeated uploads when the state file has not changed.

Dry-run without uploading:

```bash
python scripts/sync_taskory_to_ai_board.py --state task-explorer-state.json --dry-run
```

One-time upload:

```bash
python scripts/sync_taskory_to_ai_board.py ^
  --state task-explorer-state.json ^
  --base-url http://127.0.0.1:8000 ^
  --email user@example.com ^
  --password your-password ^
  --title "Taskory 작업 동기화"
```

Watch mode:

```bash
python scripts/sync_taskory_to_ai_board.py --state task-explorer-state.json --watch --interval 300 --email user@example.com --password your-password
```

By default, the script replaces existing AI Board `taskory` knowledge with the same title so a long-running watcher does not create duplicate RAG sources. Add `--append` only when you intentionally want to keep historical snapshots.

For automation runners, prefer environment variables instead of putting credentials in command history:

```powershell
$env:AI_BOARD_BASE_URL="http://127.0.0.1:8000"
$env:AI_BOARD_EMAIL="user@example.com"
$env:AI_BOARD_PASSWORD="your-password"
python scripts/sync_taskory_to_ai_board.py --state task-explorer-state.json --watch
```

## Development launch

Python 3.12 is recommended.

```bash
python task_explorer_native.py
```

Windows build:

```powershell
.\build_windows.ps1
```

macOS build, on macOS only:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

## Build outputs

```text
release/Taskory-windows.zip

dist/Taskory-macos-intel.zip
dist/Taskory-macos-arm64.zip
```

Personal task data and activity logs should not be included in release zips.
