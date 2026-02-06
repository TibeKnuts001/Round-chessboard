#!/bin/bash
# Installeer autostart voor Chess spel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Chess Project - Autostart Setup"
echo "================================"
echo ""

# Maak autostart directory als die niet bestaat
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Maak roundchess.desktop bestand
DESKTOP_FILE="$AUTOSTART_DIR/roundchess.desktop"

echo "Creating autostart entry..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Round chessboard
Exec=$SCRIPT_DIR/run.sh
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "✅ Autostart setup compleet!"
echo ""
echo "Chess spel start nu automatisch na reboot"
echo "Desktop file: $DESKTOP_FILE"
