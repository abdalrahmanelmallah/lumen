#!/usr/bin/env bash
# install.sh — installs Lumen so the `lumen` command works from any
# directory on this machine. Needs only python3 and curl (or wget).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/abdalrahmanelmallah/lumen/main/install.sh | bash
#
# Or, after cloning the repo:
#   bash install.sh

set -euo pipefail

REPO="abdalrahmanelmallah/lumen"
BRANCH="main"
RAW="https://raw.githubusercontent.com/${REPO}/${BRANCH}/lumen"
INSTALL_DIR="${LUMEN_HOME:-$HOME/.lumen}"
BIN_DIR="$HOME/.local/bin"

BUNDLED_LIBS="mathlib strings lists os"   # subgame.lu is fetched too, see below

echo "Installing Lumen to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR/libs" "$BIN_DIR"

fetch() {
    # fetch <url> <dest>
    if command -v curl > /dev/null 2>&1; then
        curl -fsSL "$1" -o "$2"
    else
        wget -q "$1" -O "$2"
    fi
}

fetch "$RAW/lumen.py" "$INSTALL_DIR/lumen.py"

for lib in $BUNDLED_LIBS subgame; do
    fetch "$RAW/libs/$lib.lu" "$INSTALL_DIR/libs/$lib.lu" || \
        echo "  (skipping $lib.lu — not found)"
done

cat > "$BIN_DIR/lumen" << EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/lumen.py" "\$@" "$INSTALL_DIR/libs"
EOF
chmod +x "$BIN_DIR/lumen"

echo ""
echo "Installed! lumen.py -> $INSTALL_DIR"
echo "Command    -> $BIN_DIR/lumen"
echo ""
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, ...):"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    echo ""
fi
echo "Try it:"
echo "  lumen get lists strings        # fetch any extra .lu libraries you want"
echo "  echo 'run(\"hello from lumen\")' > hello.lu && lumen hello.lu"
echo ""
echo "Note: file, mathx, sys, and random are native libraries built into"
echo "lumen.py itself — nothing to download, just import \"file\" etc."
