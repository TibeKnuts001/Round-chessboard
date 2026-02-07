#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:-chess}"
PY_FILE="${2:-chessgame.py}"

echo "Starting ${APP_NAME} game..."
echo "User: $(id -un)  UID: $(id -u)"

# Ga naar de directory van deze run.sh (zodat assets/ paden kloppen)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Zorg dat we NIET als root draaien (root mist vaak user audio session)
if [[ "$(id -u)" -eq 0 ]]; then
  echo "ERROR: Do not run this script as root/sudo (PipeWire/BT audio will fail)."
  exit 1
fi

# Zet user runtime dir (nodig voor PipeWire/Pulse compat sockets)
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

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

# Optioneel: SDL audio driver niet forceren, laat SDL zelf kiezen (werkt vaak best)
# Als je ooit wél wil forceren naar pulse-compat:
# export SDL_AUDIODRIVER="pulseaudio"

# Fix /dev/mem permissions voor LED hardware (ws2811)
if [[ -e /dev/mem ]]; then
  CURRENT_PERMS=$(stat -c "%a" /dev/mem 2>/dev/null || stat -f "%Lp" /dev/mem 2>/dev/null)
  if [[ "$CURRENT_PERMS" != "777" ]]; then
    echo "Fixing /dev/mem permissions (current: $CURRENT_PERMS, need: 777)"
    sudo chmod 777 /dev/mem
  else
    echo "✓ /dev/mem permissions OK ($CURRENT_PERMS)"
  fi
fi

exec "$PYTHON" "$PY_FILE"
