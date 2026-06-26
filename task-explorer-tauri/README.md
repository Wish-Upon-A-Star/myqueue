# Taskory Tauri

This folder contains the editable Tauri source for the Taskory desktop app.

## Requirements

- Node.js
- Rust MSVC toolchain
- Microsoft C++ Build Tools
- Microsoft Edge WebView2

## Install

```powershell
npm.cmd ci
```

## Run

```powershell
npm.cmd run dev
```

## Build

```powershell
npm.cmd run build
```

The Windows bundle is generated under `src-tauri/target/release/bundle`.

## Project Layout

```text
src/index.html              App UI and browser-side logic
src-tauri/tauri.conf.json   Tauri app configuration
src-tauri/src/main.rs       Tauri entry point
```
