#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARY="$SCRIPT_DIR/EPADE"
ICON_SRC="$SCRIPT_DIR/epade.png"

if [ ! -f "$BINARY" ]; then
    echo "Erreur : binaire EPADE introuvable dans $SCRIPT_DIR" >&2
    exit 1
fi

chmod +x "$BINARY"

# Icône dans le thème hicolor de l'utilisateur
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
mkdir -p "$ICON_DIR"
cp "$ICON_SRC" "$ICON_DIR/epade.png"

# Lanceur .desktop
DESKTOP_FILE="$HOME/.local/share/applications/epade.desktop"
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=EPADE
Comment=Application de cotation psychogériatrique
Exec=$BINARY
Icon=epade
Terminal=false
Categories=Science;Education;X-Medical;
StartupWMClass=EPADE
EOF
chmod +x "$DESKTOP_FILE"

# Mise à jour des caches
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "Installation terminée."
echo "L'application ÉPADE est disponible dans vos applications."
echo "Vous pouvez aussi lancer directement : $BINARY"
