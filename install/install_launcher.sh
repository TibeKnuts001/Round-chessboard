#!/bin/bash
# Installeer application launcher en desktop icon voor Chess spel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Chess Project - Launcher & Desktop Icon Setup"
echo "=============================================="
echo ""

# Maak applications directory als die niet bestaat
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

# Maak Desktop directory als die niet bestaat (normaal bestaat deze al)
DESKTOP_DIR="$HOME/Desktop"
mkdir -p "$DESKTOP_DIR"

# Kopieer en installeer app icon
ICON_SOURCE="$SCRIPT_DIR/assets/appicon/appicon.png"
ICON_DEST="/usr/share/pixmaps/roundchess.png"

if [ -f "$ICON_SOURCE" ]; then
    echo "Installing app icon..."
    sudo cp "$ICON_SOURCE" "$ICON_DEST"
    ICON_PATH="$ICON_DEST"
    echo "   ✓ Icon installed: $ICON_DEST"
else
    echo "Warning: App icon not found, using default Debian logo"
    ICON_PATH="/usr/share/pixmaps/debian-logo.png"
fi

# Maak application launcher in .local/share/applications
LAUNCHER_FILE="$APPS_DIR/Roundchess.desktop"

echo ""
echo "Creating application launcher..."
cat > "$LAUNCHER_FILE" << EOF
[Desktop Entry]
Name=Round chessboard
Comment=Round chessboard game
Exec=$SCRIPT_DIR/run.sh
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Game;
EOF

chmod +x "$LAUNCHER_FILE"
echo "   ✓ Launcher created: $LAUNCHER_FILE"

# Maak desktop icon (link naar launcher)
DESKTOP_ICON="$DESKTOP_DIR/Roundchess.desktop"

echo ""
echo "Creating desktop icon..."
cat > "$DESKTOP_ICON" << EOF
[Desktop Entry]
Type=Link
Name=Round chessboard
Icon=$ICON_PATH
URL=$LAUNCHER_FILE
EOF

chmod +x "$DESKTOP_ICON"
echo "   ✓ Desktop icon created: $DESKTOP_ICON"

# Configureer libfm voor quick_exec (zodat .desktop files direct starten)
LIBFM_CONF="$HOME/.config/libfm/libfm.conf"
mkdir -p "$HOME/.config/libfm"

if [ -f "$LIBFM_CONF" ]; then
    # File bestaat - check of [config] sectie bestaat
    if grep -q "^\[config\]" "$LIBFM_CONF"; then
        # [config] bestaat - check of quick_exec al bestaat
        if grep -q "^quick_exec" "$LIBFM_CONF"; then
            # Update bestaande quick_exec
            sed -i 's/^quick_exec=.*/quick_exec=1/' "$LIBFM_CONF"
        else
            # Voeg quick_exec toe onder [config]
            sed -i '/^\[config\]/a quick_exec=1' "$LIBFM_CONF"
        fi
    else
        # [config] bestaat niet - voeg toe aan einde
        echo "" >> "$LIBFM_CONF"
        echo "[config]" >> "$LIBFM_CONF"
        echo "quick_exec=1" >> "$LIBFM_CONF"
    fi
else
    # File bestaat niet - maak nieuwe
    cat > "$LIBFM_CONF" << EOF
[config]
quick_exec=1
EOF
fi

echo "   ✓ libfm configured for quick_exec"

# Reconfigure pcmanfm file manager
echo ""
echo "Reconfiguring file manager..."
pcmanfm --reconfigure 2>/dev/null || true
echo "   ✓ File manager reconfigured"

# Set wallpaper
echo ""
echo "Setting desktop wallpaper..."
WALLPAPER_PATH="$SCRIPT_DIR/assets/splashscreen/splash_1024x614.png"
if [ -f "$WALLPAPER_PATH" ]; then
    pcmanfm --set-wallpaper="$WALLPAPER_PATH" --wallpaper-mode=fit 2>/dev/null || true
    echo "   ✓ Wallpaper set to splash screen"
else
    echo "   ⚠ Wallpaper file not found: $WALLPAPER_PATH"
fi

# Hide desktop trash icon
echo ""
echo "Hiding desktop trash icon..."
PCMANFM_CONF_DIR="$HOME/.config/pcmanfm/LXDE-pi"
if [ -d "$PCMANFM_CONF_DIR" ]; then
    for conf_file in "$PCMANFM_CONF_DIR"/*.conf; do
        if [ -f "$conf_file" ]; then
            if grep -q "show_trash=1" "$conf_file"; then
                sed -i 's/show_trash=1/show_trash=0/' "$conf_file"
                echo "   ✓ Updated: $conf_file"
            fi
        fi
    done
    pcmanfm --reconfigure 2>/dev/null || true
    echo "   ✓ Desktop trash icon hidden"
else
    echo "   ⚠ PCManFM config directory not found"
fi

echo ""
echo "=============================================="
echo "✅ Launcher & Desktop icon setup compleet!"
echo "=============================================="
echo ""
echo "Je kunt het chess spel nu starten via:"
echo "  - Application menu (Games -> Round chessboard)"
echo "  - Desktop icon (Round chessboard)"
echo "  - Command line: ./run.sh"
echo ""
