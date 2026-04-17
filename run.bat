@echo off
cd /d "%~dp0"
if not exist node_modules\electron (
  echo Electron dependency is missing.
  echo Run install.bat first.
  pause
  exit /b 1
)
npm start
pause
