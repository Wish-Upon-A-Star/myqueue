#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This build script must be run on macOS."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_NAME="Taskory"
ARCH_NAME="${TASK_EXPLORER_ARCH:-$(uname -m)}"
DIST_DIR="dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
PACKAGE_DIR="${DIST_DIR}/${APP_NAME}-macos-${ARCH_NAME}"
OUT_ZIP="${DIST_DIR}/${APP_NAME}-macos-${ARCH_NAME}.zip"

"$PYTHON_BIN" -m venv .buildvenv-macos
source .buildvenv-macos/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

rm -rf build "${APP_PATH}" "${PACKAGE_DIR}" "${OUT_ZIP}" "${DIST_DIR}/${APP_NAME}-macos.zip"
python -m PyInstaller --noconfirm --clean --windowed --name "$APP_NAME" task_explorer_native.py
bash scripts/install_macos_launcher_wrapper.sh "${APP_PATH}" "$APP_NAME"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "Build failed: ${APP_PATH} was not created."
  exit 1
fi

test -x "${APP_PATH}/Contents/MacOS/${APP_NAME}"
test -x "${APP_PATH}/Contents/MacOS/${APP_NAME}.bin"
file "${APP_PATH}/Contents/MacOS/${APP_NAME}"
file "${APP_PATH}/Contents/MacOS/${APP_NAME}.bin"
"${APP_PATH}/Contents/MacOS/${APP_NAME}" --smoke-test

if command -v xattr >/dev/null 2>&1; then
  xattr -cr "${APP_PATH}" || true
fi

if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "${APP_PATH}"
  codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
fi

mkdir -p "${PACKAGE_DIR}"
cp -R "${APP_PATH}" "${PACKAGE_DIR}/"
cat > "${PACKAGE_DIR}/run.command" <<'SH'
#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"
APP="Taskory.app"
LOG_DIR="$HOME/Library/Application Support/Taskory"
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG="$LOG_DIR/Taskory-run-command.log"

{
  echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] run.command start"
  echo "pwd: $(pwd)"
  echo "uname: $(uname -a)"
} >> "$LOG" 2>&1

if [[ ! -d "$APP" ]]; then
  echo "Taskory.app not found next to run.command" | tee -a "$LOG"
  echo "Keep run.command and Taskory.app in the same folder, then run this file again."
  read -r -p "Press Enter to close..." _
  exit 1
fi

chmod +x "$APP/Contents/MacOS/Taskory" "$APP/Contents/MacOS/Taskory.bin" 2>>"$LOG" || true
xattr -dr com.apple.quarantine "$APP" 2>>"$LOG" || true

"$APP/Contents/MacOS/Taskory" --smoke-test >> "$LOG" 2>&1
SMOKE=$?
if [[ $SMOKE -ne 0 ]]; then
  echo "Smoke test failed. Log: $LOG" | tee -a "$LOG"
  read -r -p "Press Enter to close..." _
  exit $SMOKE
fi

open "$APP" >> "$LOG" 2>&1
OPEN_STATUS=$?
if [[ $OPEN_STATUS -ne 0 ]]; then
  echo "open failed. Trying direct launch. Log: $LOG" | tee -a "$LOG"
  "$APP/Contents/MacOS/Taskory" >> "$LOG" 2>&1
fi
SH
chmod +x "${PACKAGE_DIR}/run.command"

cat > "${PACKAGE_DIR}/README-mac.txt" <<'TXT'
Taskory macOS launch guide

Recommended first launch:
1. Unzip this package.
2. Keep Taskory.app and run.command in the same folder.
3. Double-click run.command.
4. If macOS blocks it, right-click run.command and choose Open.

Terminal launch:
cd to this extracted folder, then run:

chmod +x run.command
./run.command

What run.command does:
- fixes executable permissions when possible
- removes the macOS quarantine attribute when possible
- runs Taskory.app/Contents/MacOS/Taskory --smoke-test
- opens Taskory.app
- writes logs for debugging

Logs:
~/Library/Application Support/Taskory/Taskory-run-command.log
~/Library/Application Support/Taskory/Taskory-launcher.log
~/Library/Application Support/Taskory/Taskory-boot.log
~/Library/Application Support/Taskory/Taskory-startup-error.log

After the app launches successfully, you may move Taskory.app to Applications.
TXT
if command -v xattr >/dev/null 2>&1; then
  xattr -cr "${PACKAGE_DIR}" || true
fi

rm -f "${OUT_ZIP}"
ditto -c -k --keepParent "${PACKAGE_DIR}" "${OUT_ZIP}"
unzip -t "${OUT_ZIP}" >/dev/null

# Verify the package zip really contains the user-facing launcher and app bundle.
unzip -Z1 "${OUT_ZIP}" | grep -qx "${APP_NAME}-macos-${ARCH_NAME}/run.command"
unzip -Z1 "${OUT_ZIP}" | grep -qx "${APP_NAME}-macos-${ARCH_NAME}/${APP_NAME}.app/Contents/MacOS/${APP_NAME}"
unzip -Z1 "${OUT_ZIP}" | grep -qx "${APP_NAME}-macos-${ARCH_NAME}/${APP_NAME}.app/Contents/MacOS/${APP_NAME}.bin"

echo "Done: ${APP_PATH}"
echo "Package: ${PACKAGE_DIR}"
echo "Archive: ${OUT_ZIP}"
