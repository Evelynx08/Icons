import os
import re

# ==========================================
# CONFIGURACIÓN DE RUTAS (BookOS-Dark)
# ==========================================
# Apuntamos a la carpeta de APPS de Papirus (48x48 es la más limpia y optimizada)
PAPIRUS_ORIGEN = "/usr/share/icons/Papirus/48x48/apps"
BASE_SVG_PATH = "./base-app.svg"
OUTPUT_DIR = "./apps/scalable"

# Tamaño del logo dentro de la base (0.55 = 55% para mantener la elegancia de Sonoma)
FACTOR_OCUPACION = 0.65

def generar_tema_oscuro_sonoma():
    # Verificar que Papirus esté instalado en el sistema
    if not os.path.exists(PAPIRUS_ORIGEN):
        print(f"❌ Error: No encuentro el tema Papirus en '{PAPIRUS_ORIGEN}'.")
        print("👉 Instálalo en tu sistema usando tu gestor de paquetes (ej. pacman -S papirus-icon-theme).")
        return

    if not os.path.exists(BASE_SVG_PATH):
        print("❌ Error: No encuentro el archivo 'base-app.svg' en la raíz.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Leer la plantilla base
    with open(BASE_SVG_PATH, "r", encoding="utf-8") as f:
        base_svg_content = f.read()

    # Detectar el tamaño real del lienzo de tu base-app.svg
    w_base = 256.0
    match_base_vb = re.search(r'viewBox=[\'"]\s*0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*[\'"]', base_svg_content, re.IGNORECASE)
    if match_base_vb:
        w_base = float(match_base_vb.group(1))

    # 2. Cortar el archivo base justo antes del cierre del SVG
    match_svg_end = re.search(r'(</svg>)', base_svg_content, re.IGNORECASE)
    if not match_svg_end:
        print("❌ Error: base-app.svg no tiene etiqueta de cierre </svg>.")
        return

    parte_superior = base_svg_content[:match_svg_end.start()]
    parte_inferior = "\n</svg>"

    # Inyectar el filtro de sombreado premium para el logotipo de la app
    filtro_sombra = """
    <defs>
        <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="6" stdDeviation="5" flood-color="#000000" flood-opacity="0.4"/>
        </filter>
    </defs>
    """
    parte_superior += filtro_sombra

    # 3. Escanear TODO el arsenal de iconos de Papirus
    archivos = [f for f in os.listdir(PAPIRUS_ORIGEN) if f.endswith(".svg")]
    contador = 0

    print(f"🚀 Procesando la biblioteca de Papirus ({len(archivos)} iconos detectados)...")
    print("✨ Esto puede tardar unos segundos debido al volumen masivo de apps...")

    for archivo in archivos:
        ruta_origen = os.path.join(PAPIRUS_ORIGEN, archivo)
        ruta_destino = os.path.join(OUTPUT_DIR, archivo)

        try:
            with open(ruta_origen, "r", encoding="utf-8") as f:
                contenido_origen = f.read()

            # Detectar viewBox original del icono de Papirus (suele ser 48x48)
            match_orig_vb = re.search(r'viewBox=[\'"]\s*0\s+0\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*[\'"]', contenido_origen, re.IGNORECASE)
            w_orig = float(match_orig_vb.group(1)) if match_orig_vb else 48.0

            # Extraer los vectores limpios del interior del icono
            match_svg = re.search(r'<svg[^>]*>(.*)</svg>', contenido_origen, re.DOTALL | re.IGNORECASE)

            if match_svg:
                contenido_interno = match_svg.group(1)

                # Calcular proporciones exactas de centrado
                w_target = w_base * FACTOR_OCUPACION
                escala = w_target / w_orig
                trans_x = (w_base - w_target) / 2
                trans_y = (w_base - w_target) / 2

                # Ensamble con sombreado flotante independiente
                nodo_grupo = (
                    f'\n    \n'
                    f'    <g transform="translate({trans_x:.2f}, {trans_y:.2f}) scale({escala:.3f})" '
                    f'filter="url(#logoShadow)" opacity="0.95">\n'
                    f'{contenido_interno}\n'
                    f'    </g>'
                )

                nuevo_svg = parte_superior + nodo_grupo + parte_inferior

                with open(ruta_destino, "w", encoding="utf-8") as f:
                    f.write(nuevo_svg)
                contador += 1
        except Exception as e:
            # Si un SVG intermedio está corrupto, lo saltamos para no romper la ejecución masiva
            continue

    print(f"\n✅ ¡Éxito absoluto! Generados {contador} iconos de aplicaciones para BookOS-Dark.")

if __name__ == "__main__":
    generar_tema_oscuro_sonoma()
