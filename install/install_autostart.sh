#!/bin/bash
# Installeer autostart voor Chess of Checkers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Chess & Checkers - Autostart Setup"
echo "===================================="
echo ""

# Check welk spel autostart moet worden
if [ -z "$1" ]; then
    echo "Usage: $0 <game>"
    echo "  where <game> is: chess, checkers, none"
    echo ""
    echo "Examples:"
    echo "  $0 chess     - Autostart chess game"
    echo "  $0 checkers  - Autostart checkers game"
    echo "  $0 none      - Disable autostart"
    exit 1
fi

# Maak autostart directory als die niet bestaat
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Bepaal desktop file
DESKTOP_FILE="$AUTOSTART_DIR/roundchess.desktop"

case "$1" in
    chess)
        echo "Setting up autostart for Chess..."
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Chess
Exec=$SCRIPT_DIR/chess.sh
X-GNOME-Autostart-enabled=true
EOF
        echo ""
        echo "✅ Autostart setup compleet!"
        echo "Chess spel start nu automatisch na reboot"
        ;;
    checkers)
        echo "Setting up autostart for Checkers..."
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Checkers
Exec=$SCRIPT_DIR/checkers.sh
X-GNOME-Autostart-enabled=true
EOF
        echo ""
        echo "✅ Autostart setup compleet!"
        echo "Checkers spel start nu automatisch na reboot"
        ;;
    none)
        echo "Disabling autostart..."
        if [ -f "$DESKTOP_FILE" ]; then
            rm "$DESKTOP_FILE"
            echo "✅ Autostart disabled"
        else
            echo "⚠ Autostart was not enabled"
        fi
        ;;
    *)
        echo "❌ Unknown game: $1"
        echo "Valid options: chess, checkers, none"
        exit 1
        ;;
esac

echo "Desktop file: $DESKTOP_FILE"
echo ""
