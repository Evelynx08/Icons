#!/usr/bin/env bash
# Actualiza las agujas de bookos-clock.svg en los temas BookOS instalados
# con la hora actual y notifica a KDE para que refresque los iconos.
set -u
H=$(date +%-I); M=$(date +%-M)
hd=$(( (H % 12) * 30 + M / 2 ))
md=$(( M * 6 ))

changed=0
for f in "${XDG_DATA_HOME:-$HOME/.local/share}/icons"/BookOS-*/apps/scalable/bookos-clock.svg; do
    [ -w "$f" ] || continue
    sed -i -E \
        -e "s/(id=\"aguja-hora\" transform=\"rotate\()[0-9.]+/\1$hd/" \
        -e "s/(id=\"aguja-minuto\" transform=\"rotate\()[0-9.]+/\1$md/" \
        "$f" && changed=1
done

# Señal que KIconLoader escucha para invalidar su caché de iconos.
if [ "$changed" = 1 ]; then
    dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 2>/dev/null || true
fi
