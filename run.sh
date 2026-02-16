#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:-chess}"

# Kies automatisch het juiste Python bestand op basis van de parameter
case "$APP_NAME" in
  chess)
    PY_FILE="chessgame.py"
    ;;
  checkers)
    PY_FILE="checkersgame.py"
    ;;
  *)
    echo "ERROR: Unknown game '$APP_NAME'. Use 'chess' or 'checkers'."
    exit 1
    ;;
esac

echo "Starting ${APP_NAME} game..."

# Ga naar de directory van deze run.sh (zodat assets/ paden kloppen)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get current user info
CURRENT_USER="$(id -un)"
CURRENT_UID="$(id -u)"

echo "Running as: $CURRENT_USER  UID: $CURRENT_UID"

# Zet user runtime dir (nodig voor PipeWire/Pulse compat sockets)
export XDG_RUNTIME_DIR="/run/user/${CURRENT_UID}"

# Zet DISPLAY als het niet al ingesteld is (voor SSH sessies)
if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY not set, detecting..."
  # Probeer :0 (standaard voor lokaal scherm op Pi)
  if [[ -S "/tmp/.X11-unix/X0" ]]; then
    export DISPLAY=:0
    echo "DISPLAY set to :0"
  elif [[ -S "/tmp/.X11-unix/X1" ]]; then
    export DISPLAY=:1
    echo "DISPLAY set to :1"
  else
    echo "WARNING: No X11 socket found, trying :0 anyway"
    export DISPLAY=:0
  fi
else
  echo "DISPLAY already set: $DISPLAY"
fi

# Zorg dat DBus user bus klopt (veel desktop audio routing hangt hier indirect van af)
if [[ -S "${XDG_RUNTIME_DIR}/bus" ]]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
fi

# Handig om te zien of sockets bestaan (debug)
if [[ -S "${XDG_RUNTIME_DIR}/pipewire-0" ]]; then
  echo "PipeWire socket OK: ${XDG_RUNTIME_DIR}/pipewire-0"
else
  echo "WARNING: PipeWire socket not found yet: ${XDG_RUNTIME_DIR}/pipewire-0"
fi

if [[ -S "${XDG_RUNTIME_DIR}/pulse/native" ]]; then
  echo "Pulse compat socket OK: ${XDG_RUNTIME_DIR}/pulse/native"
else
  echo "Note: pulse/native not present (that's OK if you use pure PipeWire)."
fi

# Gebruik venv python als die bestaat
PYTHON="./venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

echo "Python: $PYTHON"
echo "PWD: $(pwd)"
echo "DISPLAY=$DISPLAY"
echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
echo "DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-"(not set)"}"

# Geef toegang tot X11 display (voor SSH sessies)
if command -v xhost >/dev/null 2>&1; then
  xhost +local: >/dev/null 2>&1 || true
fi

echo ""
echo "Starting game as user (requires /dev/mem access for LEDs)..."

exec "$PYTHON" "$PY_FILE"
