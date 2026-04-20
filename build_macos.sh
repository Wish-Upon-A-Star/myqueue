#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This build script must be run on macOS."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_NAME="TaskExplorer"

"$PYTHON_BIN" -m venv .buildvenv-macos
source .buildvenv-macos/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

rm -rf build "dist/${APP_NAME}.app" "dist/${APP_NAME}-macos.zip"
pyinstaller --noconfirm --windowed --name "$APP_NAME" task_explorer_native.py
bash scripts/install_macos_launcher_wrapper.sh "dist/${APP_NAME}.app" "$APP_NAME"

if [[ ! -d "dist/${APP_NAME}.app" ]]; then
  echo "Build failed: dist/${APP_NAME}.app was not created."
  exit 1
fi

python - <<'PY'
from pathlib import Path
import zipfile
app = Path('dist/TaskExplorer.app')
out = Path('dist/TaskExplorer-macos.zip')
if out.exists():
    out.unlink()
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path in app.rglob('*'):
        z.write(path, path.relative_to(app.parent))
print(out)
PY

echo "Done: dist/${APP_NAME}.app"
echo "Archive: dist/${APP_NAME}-macos.zip"
