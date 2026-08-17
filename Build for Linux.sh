#!/usr/bin/env bash
# Build for Linux.sh
#
# Builds the Lumen desktop app for Linux: a windowed code editor with a
# Run button, no Python needed to run it afterward. Run it from a
# terminal with:
#   ./"Build for Linux.sh"
# (or double-click it if your file manager is set to run executable
# text files — not all are, by default, hence the terminal instructions)
#
# After building, run "Install Linux Desktop Entry.sh" to add Lumen to
# your application menu and associate it with .lu files.

set -e
cd "$(dirname "$0")"

trap 'echo ""; echo "!! Build failed — see the error above. !!"; exit 1' ERR

echo "=================================================="
echo " Building Lumen for Linux..."
echo "=================================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found."
    echo "Install it with your distro's package manager, e.g.:"
    echo "  sudo apt install python3 python3-pip python3-tk   # Debian/Ubuntu"
    echo "  sudo dnf install python3 python3-pip python3-tkinter   # Fedora"
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "Python's tkinter module isn't installed (needed for the GUI)."
    echo "Install it with your distro's package manager, e.g.:"
    echo "  sudo apt install python3-tk       # Debian/Ubuntu"
    echo "  sudo dnf install python3-tkinter  # Fedora"
    echo "  sudo pacman -S tk                 # Arch"
    exit 1
fi

echo "Using: $(python3 --version)"
echo ""

if ! python3 -m pip install --upgrade pyinstaller 2>/tmp/lumen_pip_err.$$; then
    if grep -qi "externally-managed-environment" /tmp/lumen_pip_err.$$; then
        echo "Detected an externally-managed Python (common on Debian/Ubuntu) — retrying with --break-system-packages..."
        python3 -m pip install --upgrade pyinstaller --break-system-packages
    else
        cat /tmp/lumen_pip_err.$$ >&2
        rm -f /tmp/lumen_pip_err.$$
        exit 1
    fi
fi
rm -f /tmp/lumen_pip_err.$$

echo ""
echo "Running PyInstaller (this is the part that can take a minute)..."
echo ""
python3 -m PyInstaller --noconfirm Lumen.spec

echo ""
echo "=================================================="
echo " Done!"
echo ""
echo " Your Linux app is ready at:"
echo "   $(pwd)/dist/Lumen/Lumen"
echo ""
echo " Run it directly with: ./dist/Lumen/Lumen"
echo ""
echo " Next, run \"Install Linux Desktop Entry.sh\" to add Lumen to your"
echo " application menu with its icon, and set it as the default app for"
echo " .lu files."
echo "=================================================="
echo ""
