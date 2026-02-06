#!/bin/bash
# Install custom splash screen for Raspberry Pi
# Kopieert splash.png naar Plymouth theme folder

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "================================================"
echo "Chess Board - Splash Screen Installer"
echo "================================================"
echo ""

# Check of splash.png bestaat
SPLASH_FILE="assets/splashscreen/splash_1024x614.png"

if [ ! -f "$SPLASH_FILE" ]; then
    echo "ERROR: $SPLASH_FILE niet gevonden!"
    echo "Plaats je splash screen PNG in assets/splashscreen/"
    exit 1
fi

# Check of dit een Raspberry Pi is
if [ ! -d "/usr/share/plymouth/themes/pix" ]; then
    echo "WARNING: Plymouth pix theme folder niet gevonden"
    echo "Dit script is bedoeld voor Raspberry Pi OS"
    read -p "Toch doorgaan? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Splash screen wordt geïnstalleerd..."
echo "Source: $SPLASH_FILE"
echo "Destination: /usr/share/plymouth/themes/pix/splash.png"
echo ""

# Maak backup van originele splash screen
if [ -f "/usr/share/plymouth/themes/pix/splash.png" ]; then
    echo "Backup van originele splash screen maken..."
    sudo cp /usr/share/plymouth/themes/pix/splash.png /usr/share/plymouth/themes/pix/splash.png.backup
    echo "Backup opgeslagen als splash.png.backup"
fi

# Kopieer nieuwe splash screen (vraagt sudo wachtwoord)
echo ""
echo "Sudo rechten nodig om splash screen te installeren..."
sudo cp "$SPLASH_FILE" /usr/share/plymouth/themes/pix/splash.png

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✓ Splash screen succesvol geïnstalleerd!"
    echo "================================================"
    echo ""
    echo "De nieuwe splash screen wordt getoond bij:"
    echo "- Boot (opstarten)"
    echo "- Shutdown (afsluiten)"
    echo ""
    echo "Reboot om te testen:"
    echo "  sudo reboot"
    echo ""
    echo "Om originele splash screen te herstellen:"
    echo "  sudo cp /usr/share/plymouth/themes/pix/splash.png.backup /usr/share/plymouth/themes/pix/splash.png"
    echo ""
else
    echo ""
    echo "ERROR: Installatie mislukt!"
    exit 1
fi
