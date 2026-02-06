#!/bin/bash
# Start Checkers Game

# Bepaal de directory waar dit script staat
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start checkers via run.sh
"$SCRIPT_DIR/run.sh" checkers "$@"
