#!/bin/bash
# Chess Project - Main Installer
# Installeert alles behalve de virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "╔════════════════════════════════════════╗"
echo "║   Chess Project - Installation         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Maak alle scripts executable
echo "1. Making scripts executable..."
chmod +x run.sh
chmod +x install/install_venv.sh
chmod +x install/install_splash.sh
chmod +x install/install_autostart.sh
chmod +x install/install_launcher.sh
chmod +x install/install_stockfish.sh
echo "   ✓ Done"
echo ""

# Installeer splash screen
echo "2. Installing splash screen..."
./install/install_splash.sh
echo ""

# Installeer launcher en desktop icon
echo "3. Installing launcher & desktop icon..."
./install/install_launcher.sh
echo ""

# Installeer autostart
echo "4. Installing autostart..."
./install/install_autostart.sh
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
echo "  1. Install virtual environment: ./install/install_venv.sh"
echo "  2. Start the game: ./run.sh"
echo ""
echo "The chess game will now start automatically after reboot!"
echo ""
