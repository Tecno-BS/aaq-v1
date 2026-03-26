# ============================================================
# Ejercicio 3 — AAQ-BS: Consultar historial y exportar a CSV
# Autor: Automatización AAQ-BS
# ============================================================
# Este script automatiza:
#   1. Consultar todos los proyectos desde la API
#   2. Por cada proyecto, obtener su historial de análisis
#   3. Consolidar los datos en un DataFrame con pandas
#   4. Guardar el resultado en historial_aaq.csv
#   5. Mostrar el precio promedio de slides por análisis
# ============================================================

import requests
import pandas as pd
import time

# ── Configuración ────────────────────────────────────────────
API_BASE   = "http://localhost:8000"
ARCHIVO_CSV = "historial_aaq.csv"


def obtener_proyectos():
    """Obtiene la lista de proyectos desde la API."""
    respuesta = requests.get(f"{API_BASE}/projects")
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_analisis(project_id):
    """Obtiene el historial de análisis de un proyecto."""
    respuesta = requests.get(f"{API_BASE}/projects/{project_id}/analyses")
    respuesta.raise_for_status()
    return respuesta.json()


def main():
    # ── Obtener proyectos ────────────────────────────────────
    print("Conectando con la API de AAQ-BS...")
    time.sleep(1)

    proyectos = obtener_proyectos()
    print(f"Proyectos encontrados: {len(proyectos)}")

    if not proyectos:
        print("No hay proyectos en la base de datos. Crea uno primero con el Ejercicio 1.")
        return

    # ── Recorrer proyectos y extraer análisis ────────────────
    registros = []

    for proyecto in proyectos:
        pid   = proyecto.get("id") or proyecto.get("_id")
        nombre = proyecto.get("name", "Sin nombre")
        codigo = proyecto.get("code", "")

        print(f"\n  Proyecto: {nombre} ({codigo})")

        analisis_lista = obtener_analisis(pid)
        print(f"  Análisis encontrados: {len(analisis_lista)}")
        time.sleep(0.3)

        for i, analisis in enumerate(analisis_lista):
            registros.append({
                "proyecto_nombre": nombre,
                "proyecto_codigo":  codigo,
                "proyecto_id":      pid,
                "version":          len(analisis_lista) - i,
                "fecha_creacion":   analisis.get("createdAt", ""),
                "num_slides":       analisis.get("slideCount", 0),
                "num_contexto":     analisis.get("contextImageCount", 0),
                "tiene_pdf":        analisis.get("hasPdf", False),
                "analisis_id":      analisis.get("id") or analisis.get("_id", ""),
            })

    # ── Crear DataFrame y guardar CSV ────────────────────────
    df = pd.DataFrame(registros)

    if df.empty:
        print("\nNo se encontraron análisis en ningún proyecto.")
        return

    df.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8-sig")
    print(f"\nArchivo guardado: {ARCHIVO_CSV}")
    print("\n── Historial completo ──────────────────────────────────")
    print(df.to_string(index=False))

    # ── Estadísticas básicas ─────────────────────────────────
    print("\n── Estadísticas ────────────────────────────────────────")
    print(f"  Total de análisis:          {len(df)}")
    print(f"  Total de proyectos:         {df['proyecto_nombre'].nunique()}")
    print(f"  Promedio de slides/análisis:{df['num_slides'].mean():.1f}")
    print(f"  Máximo de slides en un análisis: {df['num_slides'].max()}")

    analisis_por_proyecto = df.groupby("proyecto_nombre")["analisis_id"].count()
    print("\n  Análisis por proyecto:")
    for nombre, cantidad in analisis_por_proyecto.items():
        print(f"    - {nombre}: {cantidad} análisis")


if __name__ == "__main__":
    main()
