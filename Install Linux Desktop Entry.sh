#!/usr/bin/env bash
# Install Linux Desktop Entry.sh
#
# Adds Lumen to your application menu (with its icon) and registers it
# as the default app for .lu files — the Linux counterpart to what
# Lumen.spec's Info.plist does automatically on macOS. Run this after
# "Build for Linux.sh" has produced dist/Lumen/Lumen.
#
# This only touches your user's own files (~/.local/share/...) — no sudo
# needed, and nothing is installed system-wide.

set -e
cd "$(dirname "$0")"

APP_BIN="$(pwd)/dist/Lumen/Lumen"
ICON_SRC="$(pwd)/assets/lumen-logo.png"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
MIME_DIR="$HOME/.local/share/mime/packages"

if [ ! -x "$APP_BIN" ]; then
    echo "Couldn't find $APP_BIN"
    echo "Run \"Build for Linux.sh\" first to build the app, then run this again."
    exit 1
fi

mkdir -p "$APPS_DIR" "$ICONS_DIR" "$MIME_DIR"

echo "Installing icon..."
cp "$ICON_SRC" "$ICONS_DIR/lumen.png"

echo "Registering the .lu MIME type..."
cat > "$MIME_DIR/lumen.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/x-lumen">
    <comment>Lumen Source File</comment>
    <glob pattern="*.lu"/>
    <icon name="lumen"/>
  </mime-type>
</mime-info>
EOF

echo "Creating the application menu entry..."
cat > "$APPS_DIR/lumen.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Lumen
Comment=A tiny programming language editor
Exec="$APP_BIN" %f
Icon=lumen
Terminal=false
Categories=Development;IDE;
MimeType=text/x-lumen;
EOF

echo "Refreshing caches..."
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
command -v update-mime-database >/dev/null 2>&1 && update-mime-database "$HOME/.local/share/mime" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
command -v xdg-mime >/dev/null 2>&1 && xdg-mime default lumen.desktop text/x-lumen || true

echo ""
echo "Done! Lumen should now:"
echo " - show up in your application menu/launcher with its icon"
echo " - appear as an option when you right-click a .lu file -> Open With"
echo ""
echo "If your desktop doesn't pick it up right away, log out and back in"
echo "(some launchers cache the applications list)."
