# ============================================================
# Ejercicio 1 — AAQ-BS: Crear un nuevo proyecto
# Autor: Automatización AAQ-BS
# ============================================================
# Este script automatiza:
#   1. Abrir la aplicación AAQ-BS en el navegador
#   2. Abrir el modal de "Nuevo proyecto"
#   3. Llenar el nombre y código del proyecto
#   4. Confirmar la creación
#   5. Verificar que la app navegó al panel de análisis del proyecto
# ============================================================

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# ── Configuración ────────────────────────────────────────────
APP_URL         = "http://localhost:5173"
NOMBRE_PROYECTO = "Estudio Prueba Automatizada"
CODIGO_PROYECTO = "AUTO-2026-001"


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


def main():
    # ── Configuración del navegador ──────────────────────────
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")

    chrome_path = encontrar_chrome()
    if chrome_path:
        options.binary_location = chrome_path
        print(f"Chrome encontrado en: {chrome_path}")
    else:
        print("Advertencia: Chrome no encontrado en rutas estándar. Intentando con la ruta por defecto.")

    driver = Chrome(service=service, options=options)
    wait   = WebDriverWait(driver, 10)

    # ── Abrir la aplicación ──────────────────────────────────
    driver.get(APP_URL)
    print("Aplicación abierta:", APP_URL)
    time.sleep(2)

    # ── Hacer clic en "Nuevo proyecto" ───────────────────────
    btn_nuevo = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-nuevo-proyecto']"))
    )
    btn_nuevo.click()
    print("Modal de nuevo proyecto abierto.")
    time.sleep(1)

    # ── Llenar nombre del proyecto ───────────────────────────
    input_nombre = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-nombre-proyecto']"))
    )
    input_nombre.send_keys(NOMBRE_PROYECTO)
    print(f"Nombre ingresado: {NOMBRE_PROYECTO}")
    time.sleep(0.5)

    # ── Llenar código del proyecto ───────────────────────────
    input_codigo = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-codigo-proyecto']")
    input_codigo.send_keys(CODIGO_PROYECTO)
    print(f"Código ingresado: {CODIGO_PROYECTO}")
    time.sleep(0.5)

    # ── Confirmar creación ───────────────────────────────────
    btn_crear = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-crear-proyecto']")
    btn_crear.click()
    print("Botón 'Crear proyecto' presionado.")

    # ── Verificar navegación al panel de análisis ────────────
    # Al crear un proyecto la app navega automáticamente al AnalysisView.
    # El topbar muestra el nombre del proyecto activo como confirmación.
    try:
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".topbar-project"),
                NOMBRE_PROYECTO
            )
        )
        print(f"\n✓ ÉXITO: Proyecto '{NOMBRE_PROYECTO}' creado.")
        print("  La app navegó automáticamente al panel de análisis.")
    except Exception:
        elementos = driver.find_elements(By.CSS_SELECTOR, ".topbar-project")
        contenido = elementos[0].text if elementos else "(vacío)"
        print(f"\n✗ FALLO: No se detectó el proyecto en el topbar. Contenido actual: '{contenido}'")

    time.sleep(3)
    driver.quit()
    print("Navegador cerrado.")


if __name__ == "__main__":
    main()
