#!/bin/bash
# Start Chess Game

# Bepaal de directory waar dit script staat
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start chess via run.sh
"$SCRIPT_DIR/run.sh" chess "$@"
