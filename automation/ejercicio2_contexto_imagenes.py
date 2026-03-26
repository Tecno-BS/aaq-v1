# ============================================================
# Ejercicio 2 — AAQ-BS: Llenar contexto Q0-Q10 y subir slides
# Autor: Automatización AAQ-BS
# ============================================================
# Este script automatiza:
#   1. Abrir el primer proyecto disponible
#   2. Llenar las preguntas de contexto Q0 a Q9 (textareas)
#   3. Responder Q10 (toggle "No aplica")
#   4. Generar imágenes de prueba y subirlas como slides
#   5. Verificar que el botón "Analizar" queda habilitado
# Nota: No se ejecuta el análisis para no consumir créditos de OpenAI.
# ============================================================

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import struct
import zlib
import os
import time


def encontrar_chrome():
    """Detecta la ruta de Chrome en Windows si no está en la ubicación estándar."""
    rutas_candidatas = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Chromium\Application\chrome.exe",
    ]
    for ruta in rutas_candidatas:
        if os.path.exists(ruta):
            return ruta
    return None

# ── Configuración ────────────────────────────────────────────
APP_URL      = "http://localhost:5173"
ASSETS_DIR   = os.path.join(os.path.dirname(__file__), "assets")
NUM_SLIDES   = 3   # cantidad de imágenes de prueba a generar y subir

# ── Respuestas de contexto (Q0 – Q9) ────────────────────────
RESPUESTAS = {
    "q0": "Analista senior de investigación cuantitativa para el sector de consumo masivo.",
    "q1": "Estudio de salud de marca para el cliente Empresa X en la categoría de bebidas. "
          "El problema de investigación es medir la evolución de indicadores de marca.",
    "q2": "¿Cómo ha evolucionado el top of mind y la intención de compra de la marca X "
          "tras la campaña de relanzamiento del Q1 2026?",
    "q3": "Salud de Marca — seguimiento trimestral de indicadores de marca Brandstrat.",
    "q4": "Ajustar la estrategia de comunicación y definir los focos de inversión para Q3 2026 "
          "con base en los resultados de este seguimiento.",
    "q5": "Segmentos por edad (18-35 y 36-50), género (M/F) y frecuencia de consumo "
          "(ocasional, regular, intensivo).",
    "q6": "800 casos online, margen de error ±3,5% al 95% de confianza.",
    "q7": "Diferencias mayores a 5 puntos porcentuales se consideran estadísticamente significativas.",
    "q8": "Diferencias de proporciones con prueba Z, análisis de tendencias en el tiempo "
          "y descomposición por segmentos.",
    "q9": "Seguimiento trimestral — esta es la ola 4 de 4 mediciones anuales (Q2 2025 – Q1 2026).",
}


# ── Generador de PNG de prueba (sin dependencias externas) ───
def generar_png(ruta, ancho=200, alto=150, color=(255, 140, 0)):
    """Crea un PNG sólido con el color indicado sin librerías de imagen."""
    raw = b"".join(b"\x00" + bytes(color) * ancho for _ in range(alto))
    compressed = zlib.compress(raw)

    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")

    with open(ruta, "wb") as f:
        f.write(signature + ihdr + idat + iend)


def preparar_imagenes():
    """Genera las imágenes de prueba en la carpeta assets/."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    rutas = []
    colores = [(255, 80, 0), (0, 120, 200), (60, 180, 75)]
    for i in range(NUM_SLIDES):
        ruta = os.path.join(ASSETS_DIR, f"slide_prueba_{i + 1}.png")
        generar_png(ruta, color=colores[i % len(colores)])
        rutas.append(os.path.abspath(ruta))
        print(f"Imagen generada: {ruta}")
    return rutas


def main():
    # ── Preparar imágenes de prueba ──────────────────────────
    rutas_imagenes = preparar_imagenes()
    time.sleep(1)

    # ── Configuración del navegador ──────────────────────────
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")

    chrome_path = encontrar_chrome()
    if chrome_path:
        options.binary_location = chrome_path
        print(f"Chrome encontrado en: {chrome_path}")
    else:
        print("Advertencia: Chrome no encontrado en rutas estándar.")

    driver = Chrome(service=service, options=options)
    wait   = WebDriverWait(driver, 10)

    # ── Abrir la aplicación ──────────────────────────────────
    driver.get(APP_URL)
    print("\nAplicación abierta:", APP_URL)
    time.sleep(2)

    # ── Abrir el primer proyecto disponible ──────────────────
    primera_tarjeta = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='project-card']"))
    )
    nombre_proyecto = primera_tarjeta.get_attribute("data-project-name")
    primera_tarjeta.click()
    print(f"Proyecto abierto: {nombre_proyecto}")
    time.sleep(2)

    # ── Llenar Q0 a Q9 ──────────────────────────────────────
    for qid, respuesta in RESPUESTAS.items():
        # Abrir la pregunta haciendo clic en su encabezado
        encabezado = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"[data-testid='question-header-{qid}']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'})", encabezado)
        encabezado.click()
        time.sleep(0.4)

        # Escribir la respuesta en el textarea
        textarea = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"[data-testid='textarea-{qid}']")
            )
        )
        textarea.clear()
        textarea.send_keys(respuesta)
        print(f"  {qid.upper()} completada.")
        time.sleep(0.3)

    # ── Responder Q10 (toggle "No aplica") ───────────────────
    encabezado_q10 = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='question-header-q10']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", encabezado_q10)
    encabezado_q10.click()
    time.sleep(0.4)

    btn_no = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='q10-no']"))
    )
    btn_no.click()
    print("  Q10 respondida: No aplica.")
    time.sleep(1)

    # ── Subir slides de prueba ───────────────────────────────
    input_slides = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-slides']"))
    )
    # Enviar las rutas separadas por nueva línea (Selenium acepta múltiples archivos así)
    input_slides.send_keys("\n".join(rutas_imagenes))
    print(f"  {NUM_SLIDES} slide(s) de prueba cargados.")
    time.sleep(2)

    # ── Verificar botón "Analizar" habilitado ────────────────
    btn_analizar = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-analizar']")
    if btn_analizar.is_enabled():
        print("\n✓ ÉXITO: Formulario completo. Botón 'Analizar' habilitado.")
        print("  (Script finalizado sin ejecutar el análisis para preservar créditos de OpenAI.)")
    else:
        print("\n✗ FALLO: Botón 'Analizar' sigue deshabilitado. Revisar campos incompletos.")

    time.sleep(4)
    driver.quit()
    print("Navegador cerrado.")


if __name__ == "__main__":
    main()
