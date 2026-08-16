#!/usr/bin/env bash
# Fix Icons.command
#
# Double-click this to force macOS to redraw file icons — fixes the
# case where Lumen.app is correctly set as the default app for .lu
# files, but Finder is still showing the old cached icon.
#
# This will show a normal macOS password prompt (not typed into this
# window) because clearing the system icon cache needs admin access.

osascript -e 'do shell script "rm -rf /Library/Caches/com.apple.iconservices.store; find /private/var/folders/ -name com.apple.dock.iconcache -delete 2>/dev/null; find /private/var/folders/ -name com.apple.iconservices -exec rm -rf {} + 2>/dev/null; killall Dock; killall Finder" with administrator privileges with prompt "Lumen needs to refresh macOS'\''s icon cache."'

echo "Done — your Desktop and Finder windows should flash and reload."
echo "Your .lu file icons should now show up correctly."
echo ""
read -p "Press Return to close this window..."
