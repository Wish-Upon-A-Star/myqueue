#!/usr/bin/env bash
set -euo pipefail

APP_PATH="${1:?Usage: install_macos_launcher_wrapper.sh path/to/TaskExplorer.app [ExecutableName]}"
APP_NAME="${2:-TaskExplorer}"
MACOS_DIR="${APP_PATH}/Contents/MacOS"
EXECUTABLE="${MACOS_DIR}/${APP_NAME}"
REAL_EXECUTABLE="${MACOS_DIR}/${APP_NAME}.bin"

if [[ ! -d "${MACOS_DIR}" ]]; then
  echo "Missing macOS bundle executable directory: ${MACOS_DIR}" >&2
  exit 1
fi

if [[ ! -f "${EXECUTABLE}" ]]; then
  echo "Missing app executable: ${EXECUTABLE}" >&2
  exit 1
fi

if [[ ! -f "${REAL_EXECUTABLE}" ]]; then
  mv "${EXECUTABLE}" "${REAL_EXECUTABLE}"
fi

cat > "${EXECUTABLE}" <<'SH'
#!/usr/bin/env bash
set -u

LOG_DIR="${HOME}/Library/Application Support/TaskExplorer"
LOG_FILE="${LOG_DIR}/TaskExplorer-launcher.log"
REAL_BIN="$(cd "$(dirname "$0")" && pwd)/TaskExplorer.bin"

mkdir -p "${LOG_DIR}" 2>/dev/null || true

{
  echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] launcher start"
  echo "argv: $*"
  echo "real_bin: ${REAL_BIN}"
  echo "pwd: $(pwd)"
  echo "uname: $(uname -a)"
} >> "${LOG_FILE}" 2>&1

if [[ ! -x "${REAL_BIN}" ]]; then
  {
    echo "real binary is missing or not executable"
    ls -la "$(dirname "${REAL_BIN}")" || true
  } >> "${LOG_FILE}" 2>&1
  exit 127
fi

exec "${REAL_BIN}" "$@" >> "${LOG_FILE}" 2>&1
SH

chmod +x "${EXECUTABLE}"
chmod +x "${REAL_EXECUTABLE}"

echo "Installed macOS launcher wrapper: ${EXECUTABLE} -> ${REAL_EXECUTABLE}"
