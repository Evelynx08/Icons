#!/usr/bin/env bash
# Installs the BookOS icon themes (Dark / Light / Tinted-Dark / Tinted-Light).
#
#   ./install.sh            → install for current user  (~/.local/share/icons)
#   sudo ./install.sh -s    → install system-wide       (/usr/share/icons)
#   ./install.sh -u         → uninstall (same scope flags apply)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
SYSTEM=0; UNINSTALL=0
for a in "$@"; do
    case "$a" in
        -s|--system)    SYSTEM=1 ;;
        -u|--uninstall) UNINSTALL=1 ;;
        *) echo "uso: $0 [-s|--system] [-u|--uninstall]"; exit 1 ;;
    esac
done

if [ "$SYSTEM" = 1 ]; then
    [ "$(id -u)" = 0 ] || { echo "instalación system-wide necesita sudo"; exit 1; }
    DEST="/usr/share/icons"
else
    DEST="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
fi
mkdir -p "$DEST"

# Each pack = a dir with an index.theme. Theme id = the Name= inside it.
shopt -s nullglob
installed=()
for pack in "$SRC"/BookOS-Icon-Pack-*/; do
    [ -f "$pack/index.theme" ] || { echo "  ⚠ omito $(basename "$pack") (sin index.theme)"; continue; }
    name="$(grep -m1 '^Name=' "$pack/index.theme" | cut -d= -f2 | tr -d '\r')"
    name="${name:-$(basename "$pack")}"
    target="$DEST/$name"

    if [ "$UNINSTALL" = 1 ]; then
        rm -rf "$target" && echo "  ✗ eliminado $name"
        continue
    fi

    rm -rf "$target"
    cp -r "$pack" "$target"
    rm -f "$target/generador.py"          # no empaquetar el generador
    echo "  ✓ instalado $name → $target"
    installed+=("$name")
done

[ "$UNINSTALL" = 1 ] && { echo "Listo."; exit 0; }

# Refrescar caché de iconos de cada tema instalado
for n in "${installed[@]}"; do
    gtk-update-icon-cache -qf "$DEST/$n" 2>/dev/null || true
done
kbuildsycoca6 --noincremental 2>/dev/null || true

echo
echo "Instalados: ${installed[*]}"
echo "Aplica uno con:  kwriteconfig6 --file kdeglobals --group Icons --key Theme BookOS-Dark"
echo "o desde Ajustes del sistema → Apariencia → Iconos."
