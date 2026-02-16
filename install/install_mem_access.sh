#!/bin/bash
# Setup /dev/mem access voor rpi_ws281x library

echo "╔════════════════════════════════════════╗"
echo "║   Setup /dev/mem Access for LEDs       ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if running as sudo
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run with sudo"
   echo "Usage: sudo ./install/install_mem_access.sh"
   exit 1
fi

# Get the real user (not root)
REAL_USER="${SUDO_USER:-$USER}"

echo "Setting up /dev/mem access for user: $REAL_USER"
echo ""

# Methode 1: Voeg user toe aan kmem group (als die bestaat)
echo "1. Adding user to kmem group..."
if getent group kmem > /dev/null 2>&1; then
    usermod -aG kmem "$REAL_USER"
    echo "   ✓ User added to kmem group"
else
    echo "   ⚠ kmem group doesn't exist, skipping"
fi

# Methode 2: Voeg user toe aan gpio group (voor SPI/GPIO toegang)
echo ""
echo "2. Adding user to gpio group..."
if getent group gpio > /dev/null 2>&1; then
    usermod -aG gpio "$REAL_USER"
    echo "   ✓ User added to gpio group"
else
    echo "   ⚠ gpio group doesn't exist, skipping"
fi

# Methode 3: Maak udev rule voor /dev/mem
echo ""
echo "3. Creating udev rule for /dev/mem..."
cat > /etc/udev/rules.d/99-mem.rules << 'EOF'
# Allow /dev/mem access for LED hardware (rpi_ws281x)
KERNEL=="mem", MODE="0660", GROUP="kmem"
KERNEL=="gpiomem", MODE="0660", GROUP="gpio"
EOF

echo "   ✓ Created /etc/udev/rules.d/99-mem.rules"

# Herlaad udev rules
echo ""
echo "4. Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger
echo "   ✓ udev rules reloaded"

# Zet permissions direct (voor huidige sessie)
echo ""
echo "5. Setting current permissions..."
chmod 660 /dev/mem 2>/dev/null || echo "   ⚠ Could not change /dev/mem permissions (may need reboot)"
chmod 660 /dev/gpiomem 2>/dev/null && echo "   ✓ /dev/gpiomem permissions set"

# Methode 4: Gebruik capabilities voor Python (werkt zonder root tijdens runtime)
echo ""
echo "6. Setting capabilities on Python binary..."
# Find the real python3 binary (not symlink)
PYTHON_BIN=$(readlink -f /usr/bin/python3)
if [[ -f "$PYTHON_BIN" ]]; then
    echo "   Found Python binary: $PYTHON_BIN"
    # Geef CAP_SYS_RAWIO capability (toegang tot /dev/mem)
    setcap cap_sys_rawio=ep "$PYTHON_BIN" 2>/dev/null && echo "   ✓ Capabilities set on $PYTHON_BIN" || echo "   ⚠ Could not set capabilities"
    
    # Check of het gelukt is
    getcap "$PYTHON_BIN" 2>/dev/null
else
    echo "   ⚠ Could not find Python binary"
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║            Setup Complete!              ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "IMPORTANT: Logout and login again for group changes to take effect"
echo "           or reboot the system."
echo ""
echo "User $REAL_USER can now access /dev/mem for LED hardware"
echo ""
echo "Python binary has CAP_SYS_RAWIO capability for direct hardware access"
