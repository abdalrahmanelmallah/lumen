#!/usr/bin/env bash
# Build for Mac.command
#
# Double-click this file in Finder to build the macOS Lumen app.
# (First time only: right-click it -> Open, to get past Gatekeeper,
# since this file isn't signed by Apple.)
#
# It does everything build.sh does, but you never have to open
# Terminal or type a command yourself.

cd "$(dirname "$0")"

# If anything below fails, print the error and PAUSE instead of letting
# the window close instantly, so you can actually read what happened.
trap 'echo ""; echo "!! Build failed — see the error above. !!"; echo ""; read -p "Press Return to close this window..."; exit 1' ERR

echo "=================================================="
echo " Building Lumen for macOS..."
echo "=================================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found on this Mac."
    echo "Install it from https://www.python.org/downloads/ and then double-click this file again."
    echo ""
    read -p "Press Return to close this window..."
    exit 1
fi

echo "Using: $(python3 --version)"
echo ""

python3 -m pip install --upgrade pyinstaller
echo ""
echo "Running PyInstaller (this is the part that can take a minute)..."
echo ""
python3 -m PyInstaller --noconfirm Lumen.spec

echo ""
echo "Registering .lu file icon with macOS..."
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
"$LSREGISTER" -f "$(pwd)/dist/Lumen.app" || true
touch "$(pwd)/dist/Lumen.app"

echo ""
echo "=================================================="
echo " Done!"
echo ""
echo " Your Mac app is ready at:"
echo "   $(pwd)/dist/Lumen.app"
echo ""
echo " Double-click Lumen.app to open the editor. Drag it to"
echo " /Applications, or zip it up to share with others."
echo ""
echo " Your .lu files should now show the Lumen icon. If they"
echo " still show the old generic icon, open Lumen.app once, then"
echo " right-click any .lu file -> Get Info -> Open with -> Lumen"
echo " -> Change All... (that forces Finder to refresh)."
echo "=================================================="
echo ""
read -p "Press Return to close this window..."
