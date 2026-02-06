#!/bin/bash
# Run Python script in virtual environment

# Bepaal de directory waar dit script staat (altijd /home/tibe/chess)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Export display voor pygame via SSH
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# Geef toegang tot X11 display (nodig voor pygame via SSH)
# Check alleen als xhost beschikbaar is en display actief is
if command -v xhost >/dev/null 2>&1; then
    xhost +local: >/dev/null 2>&1 || true
fi

# Check of venv bestaat
if [ ! -d "venv" ]; then
    echo "❌ venv niet gevonden. Run eerst: $SCRIPT_DIR/install_venv.sh"
    exit 1
fi

# Check of game parameter is opgegeven
if [ -z "$1" ]; then
    echo "❌ Game parameter required!"
    echo "Usage: $0 <game>"
    echo "  where <game> is: chess, checkers"
    echo ""
    echo "Or use:"
    echo "  ./chess.sh    - Start chess game"
    echo "  ./checkers.sh - Start checkers game"
    exit 1
fi

# Bepaal script op basis van game parameter
case "$1" in
    chess)
        SCRIPT="chessgame.py"
        echo "Starting chess game..."
        ;;
    checkers)
        SCRIPT="checkersgame.py"
        echo "Starting checkers game..."
        ;;
    *)
        echo "❌ Unknown game: $1"
        echo "Valid options: chess, checkers"
        exit 1
        ;;
esac

# Check of script bestaat
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Game script not found: $SCRIPT"
    exit 1
fi

echo ""
sudo venv/bin/python3 "$SCRIPT" "${@:2}"
