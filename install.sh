#!/bin/bash
# Input Master Installer
# Run once as root: sudo ./install.sh
# After install, the app runs as your normal user (no root needed)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root: sudo ./install.sh${NC}"
    exit 1
fi

ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${RED}Run with sudo from your normal user, not as root directly.${NC}"
    echo "Example: sudo ./install.sh"
    exit 1
fi

INSTALL_DIR="/opt/input-master"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}=== Input Master Installer ===${NC}"
echo ""

# --- Detect package manager and install dependencies ---
echo -e "${YELLOW}[1/6] Installing system packages...${NC}"

if command -v pacman &>/dev/null; then
    # Arch / Manjaro
    pacman -S --needed --noconfirm \
        python python-pip python-virtualenv tk \
        python-pillow python-gobject gtk3 libappindicator-gtk3 \
        2>/dev/null
elif command -v apt-get &>/dev/null; then
    # Debian / Ubuntu
    apt-get update -qq
    apt-get install -y -qq \
        python3 python3-pip python3-venv python3-tk \
        python3-pil python3-pil.imagetk python3-gi \
        gir1.2-gtk-3.0 \
        2>/dev/null
    apt-get install -y -qq gir1.2-ayatanaappindicator3-0.1 2>/dev/null \
        || apt-get install -y -qq gir1.2-appindicator3-0.1 2>/dev/null \
        || echo -e "${YELLOW}  AppIndicator not found - tray icon may use fallback backend${NC}"
elif command -v dnf &>/dev/null; then
    # Fedora / RHEL
    dnf install -y \
        python3 python3-pip python3-tkinter \
        python3-pillow python3-gobject gtk3 libappindicator-gtk3 \
        2>/dev/null
else
    echo -e "${RED}Unsupported package manager. Install manually:${NC}"
    echo "  python3, pip, tk, pillow, pygobject, gtk3, libappindicator"
    exit 1
fi

# --- Create install directory ---
echo -e "${YELLOW}[2/6] Installing application...${NC}"
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/macro_gui.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/input-master.png" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/tray-icon-*.png "$INSTALL_DIR/" 2>/dev/null || true

# --- Create venv with system site packages (for gi/gtk) ---
echo -e "${YELLOW}[3/6] Setting up Python environment...${NC}"
python3 -m venv --system-site-packages "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install -q customtkinter evdev pystray pillow

# --- Set up permissions for evdev/uinput (the key part) ---
echo -e "${YELLOW}[4/6] Configuring input device permissions...${NC}"

# Add user to input group
usermod -aG input "$ACTUAL_USER"
echo "  Added $ACTUAL_USER to 'input' group"

# Create udev rule for /dev/uinput so input group can write to it
cat > /etc/udev/rules.d/99-input-master-uinput.rules << 'EOF'
# Allow input group to create virtual input devices
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF

# Also ensure /dev/input/* devices are accessible
cat > /etc/udev/rules.d/99-input-master-evdev.rules << 'EOF'
# Allow input group to read input devices
SUBSYSTEM=="input", GROUP="input", MODE="0660"
EOF

# Load uinput module and make it persistent
modprobe uinput 2>/dev/null || true
if ! grep -q "^uinput$" /etc/modules 2>/dev/null; then
    echo "uinput" >> /etc/modules
fi

udevadm control --reload-rules
udevadm trigger

echo "  Created udev rules for uinput and evdev"
echo "  Loaded uinput kernel module"

# --- Create launcher script ---
echo -e "${YELLOW}[5/6] Creating launcher...${NC}"
cat > "$INSTALL_DIR/input-master" << LAUNCHER
#!/bin/bash
exec "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/macro_gui.py" "\$@"
LAUNCHER
chmod +x "$INSTALL_DIR/input-master"
ln -sf "$INSTALL_DIR/input-master" /usr/local/bin/input-master

# --- Create desktop entries ---
echo -e "${YELLOW}[6/6] Creating desktop entries...${NC}"

ICON_PATH="$INSTALL_DIR/input-master.png"
if [ ! -f "$ICON_PATH" ]; then
    ICON_PATH="input-master"
fi

cat > /usr/share/applications/input-master.desktop << DESKTOP
[Desktop Entry]
Name=Input Master
Comment=Mouse macro and button remapping tool
Exec=$INSTALL_DIR/input-master
Icon=$ICON_PATH
Type=Application
Categories=Utility;
Terminal=false
StartupWMClass=Input Master Control
DESKTOP

# Autostart entry (starts in tray on login)
AUTOSTART_DIR="/home/$ACTUAL_USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cp /usr/share/applications/input-master.desktop "$AUTOSTART_DIR/"
chown "$ACTUAL_USER:$ACTUAL_USER" "$AUTOSTART_DIR/input-master.desktop"

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "  App installed to: $INSTALL_DIR"
echo "  Config stored at: ~/.config/input-master/config.json"
echo "  Launch command:   input-master"
echo ""
echo -e "${YELLOW}IMPORTANT: Log out and back in for the 'input' group to take effect.${NC}"
echo "After that, Input Master will run without root and autostart in your tray."
