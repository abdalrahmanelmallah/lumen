#!/usr/bin/env bash
# Builds a standalone Lumen executable (no Python needed to run it
# afterward) using PyInstaller. Run this once on each OS you want a
# binary for — executables aren't cross-platform, so a binary built on
# Linux won't run on Windows/macOS and vice versa.
#
# Usage:
#   ./build.sh
#
# Output:
#   dist/lumen        (Linux/macOS)
#   dist/lumen.exe     (Windows, if run under build.ps1 instead)

set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found. Install it from https://www.python.org/downloads/"
    echo "(on Linux, use your distro's package manager, e.g. 'sudo apt install python3 python3-pip')"
    exit 1
fi

# Plain 'pip install' fails with an "externally-managed-environment" error
# on many recent Linux distros (Debian/Ubuntu 23.04+, PEP 668) unless you're
# in a virtualenv. Try the normal way first, and only fall back to
# --break-system-packages (safe here: pyinstaller is a build-time tool, not
# something that conflicts with system packages) if that's why it failed.
if ! python3 -m pip install --upgrade pyinstaller 2>/tmp/lumen_pip_err.$$; then
    if grep -qi "externally-managed-environment" /tmp/lumen_pip_err.$$; then
        echo "Detected an externally-managed Python (common on Linux) — retrying with --break-system-packages..."
        python3 -m pip install --upgrade pyinstaller --break-system-packages
    else
        cat /tmp/lumen_pip_err.$$ >&2
        rm -f /tmp/lumen_pip_err.$$
        exit 1
    fi
fi
rm -f /tmp/lumen_pip_err.$$

# ':' separates src:dest on Linux/macOS. Windows PyInstaller wants ';' —
# see build.ps1 for the Windows version of this command.
python3 -m PyInstaller --onefile --name lumen --add-data "libs:libs" lumen.py

echo
echo "Done. Standalone executable: dist/lumen"
echo "Copy it anywhere and run: ./lumen yourprogram.lu"
echo "(it has libs/ bundled inside it, so it works from any folder)"
