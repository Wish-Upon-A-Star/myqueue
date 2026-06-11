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
- Audio transcription into task-ready text, including large-file splitting when `ffmpeg.exe` is bundled
- AI preview before adding generated tasks and memos to the current folder

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

## Development launch

Python 3.12 is recommended.

```bash
python task_explorer_native.py
```

Windows build:

```powershell
.uild_windows.ps1
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
