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

# Check if we need to re-exec with sudo for /dev/mem access
if [[ "$(id -u)" -ne 0 ]]; then
  echo "LED hardware requires sudo access to /dev/mem"
  echo "Restarting with sudo (preserving user environment for audio/display)..."
  
  # Get the real user info before becoming root
  REAL_USER="${SUDO_USER:-$(id -un)}"
  REAL_UID="${SUDO_UID:-$(id -u)}"
  
  # Re-execute this script with sudo, preserving environment
  exec sudo -E \
    REAL_USER="$REAL_USER" \
    REAL_UID="$REAL_UID" \
    "$0" "$@"
fi

# Now we're running as root, but we need to preserve user's audio/display environment
REAL_USER="${REAL_USER:-root}"
REAL_UID="${REAL_UID:-0}"

echo "Running as: $(id -un)  UID: $(id -u)"
echo "Real user: $REAL_USER  UID: $REAL_UID"

# Zet user runtime dir (nodig voor PipeWire/Pulse compat sockets)
export XDG_RUNTIME_DIR="/run/user/${REAL_UID}"

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
echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
echo "DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-"(not set)"}"

# Running as root now, so we have direct /dev/mem access for LED hardware
echo "✓ Running with sudo - /dev/mem access available"

exec "$PYTHON" "$PY_FILE"
