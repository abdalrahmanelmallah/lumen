# install.ps1 — installs Lumen so the `lumen` command works from any
# directory on this machine. Needs only python (or py) already on PATH.
#
# Usage (in a plain PowerShell window, no Git Bash/WSL needed):
#   irm https://raw.githubusercontent.com/abdalrahmanelmallah/lumen/main/lumen/install.ps1 | iex
#
# Or, after cloning the repo:
#   .\install.ps1

$ErrorActionPreference = "Stop"

$Repo   = "abdalrahmanelmallah/lumen"
$Branch = "main"
$Raw    = "https://raw.githubusercontent.com/$Repo/$Branch/lumen"

$InstallDir = if ($env:LUMEN_HOME) { $env:LUMEN_HOME } else { Join-Path $env:USERPROFILE ".lumen" }
$BinDir     = Join-Path $env:USERPROFILE ".lumen\bin"
$BundledLibs = @("mathlib", "strings", "lists", "os")   # subgame.lu is fetched too, see below

Write-Host "Installing Lumen to $InstallDir ..."
New-Item -ItemType Directory -Force -Path (Join-Path $InstallDir "libs") | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

function Fetch($Url, $Dest) {
    Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
}

Fetch "$Raw/lumen.py" (Join-Path $InstallDir "lumen.py")

foreach ($lib in $BundledLibs + @("subgame")) {
    try {
        Fetch "$Raw/libs/$lib.lu" (Join-Path $InstallDir "libs\$lib.lu")
    } catch {
        Write-Host "  (skipping $lib.lu — not found)"
    }
}

function Get-Python {
    foreach ($cmd in @("python", "py")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            return $cmd
        }
    }
    Write-Host "Python was not found on this machine."
    Write-Host "Install it from https://www.python.org/downloads/ (check ""Add python.exe to PATH"" during setup) and run this installer again."
    exit 1
}
$python = Get-Python

# A tiny wrapper .cmd so `lumen` works from cmd.exe AND PowerShell,
# the same way the bash script's wrapper works from any shell.
@"
@echo off
$python "$InstallDir\lumen.py" %* "$InstallDir\libs"
"@ | Set-Content -Path (Join-Path $BinDir "lumen.cmd") -Encoding ASCII

Write-Host ""
Write-Host "Installed! lumen.py -> $InstallDir"
Write-Host "Command    -> $BinDir\lumen.cmd"
Write-Host ""

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    Write-Host "Added $BinDir to your PATH."
    Write-Host "Open a new terminal window for this to take effect."
} else {
    Write-Host "$BinDir is already on your PATH."
}

Write-Host ""
Write-Host "Try it (in a new terminal):"
Write-Host "  lumen get lists strings        # fetch any extra .lu libraries you want"
Write-Host "  'run(""hello from lumen"")' | Out-File hello.lu -Encoding ascii; lumen hello.lu"
Write-Host ""
Write-Host "Note: file, mathx, sys, and random are native libraries built into"
Write-Host "lumen.py itself — nothing to download, just import ""file"" etc."
