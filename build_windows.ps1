param(
    [string]$PythonBin = "",
    [switch]$SkipPackage
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$DefaultDistRoot = Join-Path $Root "dist"
$RebuiltDistRoot = Join-Path $Root "dist-rebuilt"
$DefaultAppDir = Join-Path $DefaultDistRoot "Taskory"
$BackupDir = Join-Path $Root ".build-data-backup"
$ReleaseDir = Join-Path $Root "release"
$PackageStage = Join-Path $Root ".build-data-backup\windows-package"
$DataFiles = @("task-explorer-state.json", "activity-log.db", "Taskory-boot.log", "Taskory-startup-error.log")
$BundledTools = @("ffmpeg.exe")

$running = Get-Process -Name "Taskory" -ErrorAction SilentlyContinue
if ($running) {
    Write-Warning "Taskory.exe is running. Building into dist-rebuilt\Taskory instead of replacing the running dist\Taskory."
    $DistRoot = $RebuiltDistRoot
    $AppDir = Join-Path $DistRoot "Taskory"
} else {
    $DistRoot = $DefaultDistRoot
    $AppDir = $DefaultAppDir
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

foreach ($name in $DataFiles) {
    $src = Join-Path $DefaultAppDir $name
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $BackupDir $name) -Force
    }
}

function Resolve-Python {
    param([string]$Requested)
    if ($Requested) {
        return $Requested
    }
    if (Test-Path ".venv-build\Scripts\python.exe") {
        return ".\.venv-build\Scripts\python.exe"
    }
    $py312 = (Get-Command py -ErrorAction SilentlyContinue)
    if ($py312) {
        try {
            & py -3.12 --version *> $null
            return "py -3.12"
        } catch {
        }
    }
    return "python"
}

$ResolvedPython = Resolve-Python $PythonBin

if ($ResolvedPython -eq "py -3.12") {
    & py -3.12 -m venv .venv-build
} elseif (!(Test-Path ".venv-build\Scripts\python.exe")) {
    & $ResolvedPython -m venv .venv-build
}

$BuildPython = ".\.venv-build\Scripts\python.exe"
try {
    & $BuildPython -m pip install -r requirements.txt
    & $BuildPython -m PyInstaller --noconfirm --clean --windowed --distpath $DistRoot --name Taskory task_explorer_native.py
} finally {
    New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
    foreach ($name in $BundledTools) {
        $tool = Join-Path $Root $name
        if (Test-Path -LiteralPath $tool) {
            Copy-Item -LiteralPath $tool -Destination (Join-Path $AppDir $name) -Force
        }
    }
    if ($AppDir -eq $DefaultAppDir) {
        foreach ($name in $DataFiles) {
            $backup = Join-Path $BackupDir $name
            if (Test-Path -LiteralPath $backup) {
                Copy-Item -LiteralPath $backup -Destination (Join-Path $AppDir $name) -Force
            }
        }
    }
}

& (Join-Path $AppDir "Taskory.exe") --smoke-test

if (-not $SkipPackage) {
    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    if (Test-Path -LiteralPath $PackageStage) {
        Remove-Item -LiteralPath $PackageStage -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $PackageStage | Out-Null
    $PackageAppDir = Join-Path $PackageStage "Taskory"
    Copy-Item -LiteralPath $AppDir -Destination $PackageAppDir -Recurse -Force
    foreach ($name in $DataFiles) {
        $target = Join-Path $PackageAppDir $name
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force
        }
    }
    $zip = Join-Path $ReleaseDir "Taskory-windows.zip"
    if (Test-Path -LiteralPath $zip) {
        Remove-Item -LiteralPath $zip -Force
    }
    Compress-Archive -Path $PackageAppDir -DestinationPath $zip -Force
    Write-Host "Package complete: $zip"
}

if ($AppDir -eq $DefaultAppDir) {
    Write-Host "Build complete. Data files were restored to dist\Taskory when present."
} else {
    Write-Host "Build complete. Running app was left untouched; new build is in dist-rebuilt\Taskory."
}
