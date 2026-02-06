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

# Check of een script is opgegeven, anders start chessgame
if [ -z "$1" ]; then
    SCRIPT="chessgame.py"
    echo "Starting chess game..."
else
    SCRIPT="$1"
    # Check of bestand bestaat
    if [ ! -f "$SCRIPT" ]; then
        echo "❌ Bestand niet gevonden: $SCRIPT"
        exit 1
    fi
    echo "Running $SCRIPT in venv..."
fi

echo ""
sudo venv/bin/python3 "$SCRIPT" "${@:2}"
