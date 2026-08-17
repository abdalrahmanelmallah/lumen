# build.ps1
# Builds a standalone lumen.exe (no Python needed to run it afterward)
# using PyInstaller. This is the Windows counterpart to build.sh — the
# only real differences are the ';' data separator PyInstaller wants on
# Windows (vs ':' on Linux/macOS) and the .exe extension.
#
# Usage (from PowerShell):
#   .\build.ps1
#
# If PowerShell refuses to run this because of its execution policy, run
# it like this instead (only affects this one process, nothing permanent):
#   powershell -ExecutionPolicy Bypass -File build.ps1
#
# Output:
#   dist\lumen.exe

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-Python {
    foreach ($cmd in @("python", "py")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            return $cmd
        }
    }
    Write-Host "Python was not found on this machine."
    Write-Host "Install it from https://www.python.org/downloads/ (check ""Add python.exe to PATH"" during setup) and run this script again."
    exit 1
}

$python = Get-Python
Write-Host "Using: $(& $python --version)"

& $python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed — see the error above."
    exit 1
}

# ';' separates src;dest on Windows PyInstaller (Linux/macOS use ':' — see build.sh).
& $python -m PyInstaller --onefile --name lumen --add-data "libs;libs" lumen.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed — see the error above."
    exit 1
}

Write-Host ""
Write-Host "Done. Standalone executable: dist\lumen.exe"
Write-Host "Copy it anywhere and run: .\lumen.exe yourprogram.lu"
Write-Host "(it has libs\ bundled inside it, so it works from any folder)"
