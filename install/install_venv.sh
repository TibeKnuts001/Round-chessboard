#!/bin/bash
# Installeer Python virtual environment en dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "Chess Project - Virtual Environment Setup"
echo "=========================================="
echo ""

# Installeer system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y liblgpio-dev mpg123 libopenblas0
echo ""

# Check of venv al bestaat
if [ -d "venv" ]; then
    echo "⚠️  venv bestaat al. Activeer en update dependencies..."
    source venv/bin/activate
    echo "Upgrading pip..."
    pip install --upgrade pip
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
else
    # Maak venv
    echo "Creating virtual environment..."
    python3 -m venv venv

    # Activeer venv
    echo "Activating venv..."
    source venv/bin/activate

    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Installeer dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Virtual environment setup compleet!"
echo ""
echo "Gebruik ./run.sh om het chess spel te starten"
echo "Of activeer handmatig met: source venv/bin/activate"
