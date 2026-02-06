#!/bin/bash
# Installeer application launchers en desktop icons voor Chess en Checkers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Chess & Checkers - Launcher & Desktop Icon Setup"
echo "=================================================="
echo ""

# Maak applications directory als die niet bestaat
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

# Maak Desktop directory als die niet bestaat (normaal bestaat deze al)
DESKTOP_DIR="$HOME/Desktop"
mkdir -p "$DESKTOP_DIR"

# Kopieer en installeer app icons
CHESS_ICON_SOURCE="$SCRIPT_DIR/assets/appicon/chess.png"
CHESS_ICON_DEST="/usr/share/pixmaps/chess.png"

CHECKERS_ICON_SOURCE="$SCRIPT_DIR/assets/appicon/checkers.png"
CHECKERS_ICON_DEST="/usr/share/pixmaps/roundcheckers.png"

echo "Installing app icons..."

# Chess icon
if [ -f "$CHESS_ICON_SOURCE" ]; then
    sudo cp "$CHESS_ICON_SOURCE" "$CHESS_ICON_DEST"
    CHESS_ICON_PATH="$CHESS_ICON_DEST"
    echo "   ✓ Chess icon installed: $CHESS_ICON_DEST"
else
    echo "   Warning: Chess icon not found, using default Debian logo"
    CHESS_ICON_PATH="/usr/share/pixmaps/debian-logo.png"
fi

# Checkers icon
if [ -f "$CHECKERS_ICON_SOURCE" ]; then
    sudo cp "$CHECKERS_ICON_SOURCE" "$CHECKERS_ICON_DEST"
    CHECKERS_ICON_PATH="$CHECKERS_ICON_DEST"
    echo "   ✓ Checkers icon installed: $CHECKERS_ICON_DEST"
else
    echo "   Warning: Checkers icon not found, using default Debian logo"
    CHECKERS_ICON_PATH="/usr/share/pixmaps/debian-logo.png"
fi

# ========================================
# CHESS LAUNCHER
# ========================================
CHESS_LAUNCHER_FILE="$APPS_DIR/Chess.desktop"

echo ""
echo "Creating Chess application launcher..."
cat > "$CHESS_LAUNCHER_FILE" << EOF
[Desktop Entry]
Name=Chess
Comment=Play Chess on round chessboard
Exec=$SCRIPT_DIR/chess.sh
Icon=$CHESS_ICON_PATH
Terminal=false
Type=Application
Categories=Game;
EOF

chmod +x "$CHESS_LAUNCHER_FILE"
echo "   ✓ Chess launcher created: $CHESS_LAUNCHER_FILE"

# Maak chess desktop icon
CHESS_DESKTOP_ICON="$DESKTOP_DIR/Chess.desktop"

echo ""
echo "Creating Chess desktop icon..."
cat > "$CHESS_DESKTOP_ICON" << EOF
[Desktop Entry]
Type=Link
Name=Chess
Icon=$CHESS_ICON_PATH
URL=$CHESS_LAUNCHER_FILE
EOF

chmod +x "$CHESS_DESKTOP_ICON"
echo "   ✓ Chess desktop icon created: $CHESS_DESKTOP_ICON"

# ========================================
# CHECKERS LAUNCHER
# ========================================
CHECKERS_LAUNCHER_FILE="$APPS_DIR/Checkers.desktop"

echo ""
echo "Creating Checkers application launcher..."
cat > "$CHECKERS_LAUNCHER_FILE" << EOF
[Desktop Entry]
Name=Checkers
Comment=Play Checkers on round chessboard
Exec=$SCRIPT_DIR/checkers.sh
Icon=$CHECKERS_ICON_PATH
Terminal=false
Type=Application
Categories=Game;
EOF

chmod +x "$CHECKERS_LAUNCHER_FILE"
echo "   ✓ Checkers launcher created: $CHECKERS_LAUNCHER_FILE"

# Maak checkers desktop icon
CHECKERS_DESKTOP_ICON="$DESKTOP_DIR/Checkers.desktop"

echo ""
echo "Creating Checkers desktop icon..."
cat > "$CHECKERS_DESKTOP_ICON" << EOF
[Desktop Entry]
Type=Link
Name=Checkers
Icon=$CHECKERS_ICON_PATH
URL=$CHECKERS_LAUNCHER_FILE
EOF

chmod +x "$CHECKERS_DESKTOP_ICON"
echo "   ✓ Checkers desktop icon created: $CHECKERS_DESKTOP_ICON"

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
echo "=================================================="
echo "✅ Launcher & Desktop icon setup compleet!"
echo "=================================================="
echo ""
echo "Je kunt de games nu starten via:"
echo "  - Application menu (Games):"
echo "      • Chess"
echo "      • Checkers"
echo "  - Desktop icons:"
echo "      • Chess"
echo "      • Checkers"
echo "  - Command line:"
echo "      • ./chess.sh     - Start chess"
echo "      • ./checkers.sh  - Start checkers"
echo ""
