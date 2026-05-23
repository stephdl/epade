#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installation des dépendances Python..."
pip3 install --user fpdf2 tkcalendar

echo "Configuration du lanceur..."
chmod +x "$SCRIPT_DIR/main.py"

DESKTOP_FILE="$HOME/.local/share/applications/epade.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=EPADE
Comment=Application de cotation psychogériatrique
Exec=python3 $SCRIPT_DIR/main.py
Icon=$SCRIPT_DIR/assets/epade.png
Terminal=false
Categories=Medical;Science;
StartupWMClass=EPADE
EOF

chmod +x "$DESKTOP_FILE"

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo ""
echo "Installation terminée."
echo "L'application ÉPADE est disponible dans vos applications."
echo "Vous pouvez aussi lancer : python3 $SCRIPT_DIR/main.py"
