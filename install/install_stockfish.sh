#!/bin/bash
# Installeer Stockfish chess engine

echo "Chess Project - Stockfish Installation"
echo "======================================="
echo ""

# Check of stockfish al geïnstalleerd is
if command -v stockfish >/dev/null 2>&1; then
    CURRENT_VERSION=$(stockfish --version 2>&1 | head -n 1)
    echo "✓ Stockfish is already installed: $CURRENT_VERSION"
    echo ""
    exit 0
fi

echo "Installing Stockfish chess engine..."
echo ""

# Installeer via apt (Raspberry Pi OS)
if command -v apt-get >/dev/null 2>&1; then
    echo "Using apt-get to install stockfish..."
    sudo apt-get update
    sudo apt-get install -y stockfish
    
    if [ $? -eq 0 ]; then
        INSTALLED_VERSION=$(stockfish --version 2>&1 | head -n 1)
        echo ""
        echo "======================================="
        echo "✅ Stockfish successfully installed!"
        echo "======================================="
        echo "Version: $INSTALLED_VERSION"
        echo ""
    else
        echo ""
        echo "❌ Failed to install Stockfish"
        exit 1
    fi
else
    echo "⚠ apt-get not found - please install Stockfish manually"
    echo ""
    echo "On Debian/Ubuntu/Raspberry Pi OS:"
    echo "  sudo apt-get install stockfish"
    echo ""
    exit 1
fi
