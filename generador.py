#!/usr/bin/env python3
"""
Generador de packs de iconos BookOS (Light + Dark) — estilo Sonoma.

Toma los logos de Papirus y los monta sobre una base redondeada con un color
de fondo. Genera DOS variantes:
    - BookOS-Icon-Pack-Dark   (fondo oscuro)
    - BookOS-Icon-Pack-Light  (fondo claro)

El color de fondo de cada SVG queda como un `fill` simple y aislado, de modo
que un proceso posterior (el "tintado") pueda reemplazarlo con un simple
buscar/sustituir sin tocar el logo de la app.

Uso:
    python3 generador.py            # genera Light y Dark
    python3 generador.py dark       # solo Dark
    python3 generador.py light      # solo Light
"""
import os
import re
import sys

# ── Configuración ─────────────────────────────────────────────────────────
PAPIRUS_ORIGEN = "/usr/share/icons/Papirus/48x48/apps"
# Apps propias de BookOS (ya son cuadrados 512 con base propia): se les quita
# su rect de fondo y el glifo se monta a escala completa sobre la base del pack.
BOOKOS_ORIGEN = "/usr/share/icons/hicolor/scalable/apps"
BOOKOS_PREFIJO = "bookos-"
# Apps cuyo icono no está (aún) en hicolor: nombre de icono → SVG en su repo.
_BOOKOS_REPOS = os.path.expanduser("~/Descargas/BookOS")
BOOKOS_EXTRA = {
    "bookos-player":        f"{_BOOKOS_REPOS}/BookOS-Player/src-tauri/icons/icon.svg",
    "bookos-viewer":        f"{_BOOKOS_REPOS}/BookOS-Viewer/src-tauri/icons/icon.svg",
    "bookos-voicerecorder": f"{_BOOKOS_REPOS}/BookOS-VoiceRecorder/src-tauri/icons/icon.svg",
    "bookos-shell":         f"{_BOOKOS_REPOS}/bookos-shell/src-tauri/icons/icon.svg",
    "bookos-new":           f"{_BOOKOS_REPOS}/BookOS-New/src-tauri/icons/icon.svg",
}
# Diseños propios del pack: tienen prioridad sobre hicolor y BOOKOS_EXTRA.
BOOKOS_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookos-src")
FACTOR_OCUPACION = 0.78          # tamaño del logo dentro de la base (0-1)
LIENZO = 512                     # tamaño del lienzo de la base
RADIO = 80                       # radio de las esquinas

# Cada variante: (carpeta destino, color de fondo, nombre del tema, comentario)
VARIANTES = {
    "dark":  ("BookOS-Icon-Pack-Dark",  "#292930", "BookOS-Dark",  "Tema de iconos oscuro de BookOS"),
    "light": ("BookOS-Icon-Pack-Light", "#E9EBF7", "BookOS-Light", "Tema de iconos claro de BookOS"),
    # Bases para el tintado de bookos-settings (mismo arte; el logo se
    # recolorea después con el filtro #bookosTint que inyecta la app).
    "tinted-dark":  ("BookOS-Icon-Pack-Tinted-Dark",  "#292930", "BookOS-Tinted-Dark",  "Base oscura para iconos tintados de BookOS"),
    "tinted-light": ("BookOS-Icon-Pack-Tinted-Light", "#E9EBF7", "BookOS-Tinted-Light", "Base clara para iconos tintados de BookOS"),
}

# El color de fondo se escribe SIEMPRE así, en su propia línea, para que el
# tintado lo pueda localizar y reemplazar de forma fiable.
def base_svg(bg_color: str) -> str:
    return (
        f'<svg width="{LIENZO}" height="{LIENZO}" viewBox="0 0 {LIENZO} {LIENZO}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        f'<rect width="{LIENZO}" height="{LIENZO}" rx="{RADIO}" fill="{bg_color}"/>\n'
        f'</svg>\n'
    )

INDEX_THEME = """[Icon Theme]
Name={name}
Comment={comment}
DisplayDepth=32

Inherits={hereda}
Directories=apps/scalable,places/scalable,status/scalable

[apps/scalable]
Size=64
Context=Applications
Type=Scalable
MinSize=16
MaxSize=256

[places/scalable]
Size=64
Context=Places
Type=Scalable
MinSize=16
MaxSize=256

[status/scalable]
Size=24
Context=Status
Type=Scalable
MinSize=16
MaxSize=256
"""

FILTRO_SOMBRA = """
    <defs>
        <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="6" stdDeviation="5" flood-color="#000000" flood-opacity="0.4"/>
        </filter>
    </defs>
    """


def generar_variante(clave: str) -> None:
    carpeta, bg_color, nombre, comentario = VARIANTES[clave]
    out_dir = os.path.join(carpeta, "apps", "scalable")

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(carpeta, "places", "scalable"), exist_ok=True)
    os.makedirs(os.path.join(carpeta, "status", "scalable"), exist_ok=True)

    # index.theme + base-app.svg (modificables después)
    with open(os.path.join(carpeta, "index.theme"), "w", encoding="utf-8") as f:
        # Lo que el pack no tiene lo buscan GTK y Qt en estos. Los oscuros
        # heredan las variantes -Dark: los iconos monocromos de breeze llevan
        # el trazo casi negro dentro del SVG y sobre la base oscura no se ven.
        hereda = "Papirus-Dark,breeze-dark,hicolor" if "dark" in clave else "Papirus,breeze,hicolor"
        f.write(INDEX_THEME.format(name=nombre, comment=comentario, hereda=hereda))
    with open(os.path.join(carpeta, "base-app.svg"), "w", encoding="utf-8") as f:
        f.write(base_svg(bg_color))

    base = base_svg(bg_color)
    parte_superior = base[: base.rindex("</svg>")] + FILTRO_SOMBRA
    parte_inferior = "\n</svg>"
    w_base = float(LIENZO)

    # Sin Papirus se regeneran solo las apps de BookOS: los iconos de Papirus
    # ya generados están en el repo y no cambian.
    if os.path.isdir(PAPIRUS_ORIGEN):
        archivos = [f for f in os.listdir(PAPIRUS_ORIGEN) if f.endswith(".svg")]
    else:
        print(f"⚠ No encuentro Papirus en '{PAPIRUS_ORIGEN}'; solo regenero las apps de BookOS.")
        archivos = []
    print(f"🚀 [{nombre}] Procesando {len(archivos)} iconos de Papirus (fondo {bg_color})…")

    contador = 0
    for archivo in archivos:
        ruta_origen = os.path.join(PAPIRUS_ORIGEN, archivo)
        ruta_destino = os.path.join(out_dir, archivo)
        try:
            with open(ruta_origen, "r", encoding="utf-8") as f:
                contenido_origen = f.read()

            match_orig_vb = re.search(
                r'viewBox=[\'"]\s*0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*[\'"]',
                contenido_origen, re.IGNORECASE)
            w_orig = float(match_orig_vb.group(1)) if match_orig_vb else 48.0

            match_svg = re.search(r'<svg[^>]*>(.*)</svg>', contenido_origen, re.DOTALL | re.IGNORECASE)
            if not match_svg:
                continue
            contenido_interno = match_svg.group(1)

            w_target = w_base * FACTOR_OCUPACION
            escala = w_target / w_orig
            trans = (w_base - w_target) / 2

            nodo_grupo = (
                f'\n    \n    <g transform="translate({trans:.2f}, {trans:.2f}) scale({escala:.3f})" '
                f'filter="url(#logoShadow)" opacity="0.95">\n{contenido_interno}\n    </g>'
            )
            with open(ruta_destino, "w", encoding="utf-8") as f:
                f.write(parte_superior + nodo_grupo + parte_inferior)
            contador += 1
        except Exception:
            continue

    # ── Apps de BookOS ────────────────────────────────────────────────────
    fuentes = {}
    if os.path.isdir(BOOKOS_ORIGEN):
        for archivo in sorted(os.listdir(BOOKOS_ORIGEN)):
            if archivo.startswith(BOOKOS_PREFIJO) and archivo.endswith(".svg"):
                fuentes[archivo] = os.path.join(BOOKOS_ORIGEN, archivo)
    for nombre_icono, ruta in BOOKOS_EXTRA.items():
        if f"{nombre_icono}.svg" not in fuentes and os.path.isfile(ruta):
            fuentes[f"{nombre_icono}.svg"] = ruta
    if os.path.isdir(BOOKOS_LOCAL):
        for archivo in sorted(os.listdir(BOOKOS_LOCAL)):
            if archivo.endswith(".svg"):
                fuentes[archivo] = os.path.join(BOOKOS_LOCAL, archivo)
    # Glifos específicos de la variante (bookos-src/light | bookos-src/dark):
    # mismo arte con colores ajustados a la base clara u oscura del pack.
    sub_variante = os.path.join(BOOKOS_LOCAL, "dark" if "dark" in clave else "light")
    if os.path.isdir(sub_variante):
        for archivo in sorted(os.listdir(sub_variante)):
            if archivo.endswith(".svg"):
                fuentes[archivo] = os.path.join(sub_variante, archivo)

    bookos = 0
    if True:
        for archivo, ruta_src in sorted(fuentes.items()):
            try:
                with open(ruta_src, "r", encoding="utf-8") as f:
                    contenido_origen = f.read()
                match_svg = re.search(r'<svg[^>]*>(.*)</svg>', contenido_origen, re.DOTALL | re.IGNORECASE)
                if not match_svg:
                    continue
                interno = match_svg.group(1)
                # Quitar SU rect de fondo. En Dark/Light se conserva como base:
                # los diseños de BookOS son glifo blanco sobre color de marca, y
                # sobre la base neutra Reproductor y Grabadora quedaban como las
                # mismas barras blancas, invisibles además en el tema claro.
                # Las Tinted sí usan la base del pack porque el tintado recolorea
                # el logo y reemplaza ese color de fondo.
                fondo = re.search(r'<rect[^>]*/>', interno)
                interno = interno[:fondo.start()] + interno[fondo.end():] if fondo else interno
                superior = parte_superior
                if fondo and not clave.startswith("tinted"):
                    superior = (base[: base.index("<rect")] + fondo.group(0) + "\n"
                                + FILTRO_SOMBRA)
                match_vb = re.search(
                    r'viewBox=[\'"]\s*0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*[\'"]',
                    contenido_origen, re.IGNORECASE)
                w_orig = float(match_vb.group(1)) if match_vb else 512.0
                escala = w_base / w_orig          # glifo ya trae sus márgenes
                nodo = (
                    f'\n    \n    <g transform="translate(0.00, 0.00) scale({escala:.3f})" '
                    f'filter="url(#logoShadow)" opacity="0.95">\n{interno}\n    </g>'
                )
                with open(os.path.join(out_dir, archivo), "w", encoding="utf-8") as f:
                    f.write(superior + nodo + parte_inferior)
                bookos += 1
            except Exception:
                continue

    print(f"✅ [{nombre}] Generados {contador} iconos Papirus + {bookos} BookOS en {out_dir}\n")


def main() -> None:
    args = [a.lower() for a in sys.argv[1:]]
    objetivos = [a for a in args if a in VARIANTES] or list(VARIANTES.keys())
    for clave in objetivos:
        generar_variante(clave)
    print("🎉 Hecho. Para el tintado, copia el pack y reemplaza el color de fondo.")


if __name__ == "__main__":
    main()
