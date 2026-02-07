#!/bin/bash
# Chess Project - Main Installer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "╔════════════════════════════════════════╗"
echo "║   Chess Project - Installation         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Maak alle scripts executable
echo "1. Making scripts executable..."
chmod +x run.sh
chmod +x chess.sh
chmod +x checkers.sh
chmod +x install/install_venv.sh
chmod +x install/install_splash.sh
chmod +x install/install_launcher.sh
chmod +x install/install_stockfish.sh
echo "   ✓ Done"
echo ""

# Vraag of venv geïnstalleerd moet worden
echo "2. Virtual Environment Setup"
echo "   Do you want to install Python virtual environment? (recommended)"
read -p "   Install venv? [Y/n]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "   Installing virtual environment..."
    ./install/install_venv.sh
    echo ""
else
    echo "   Skipping virtual environment installation"
    echo "   You can install it later with: ./install/install_venv.sh"
    echo ""
fi

# Installeer splash screen
echo "3. Installing splash screen..."
./install/install_splash.sh
echo ""

# Installeer launcher en desktop icon
echo "4. Installing launcher & desktop icon..."
./install/install_launcher.sh
echo ""

# Installeer Stockfish
echo "5. Installing Stockfish chess engine..."
./install/install_stockfish.sh
echo ""

echo "╔════════════════════════════════════════╗"
echo "║         Installation Complete!         ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  • Start the game: ./run.sh"
echo ""
echo "The chess game will now start automatically after reboot!"
echo ""
