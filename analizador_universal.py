#!/usr/bin/env python3

import pandas as pd
from datetime import datetime
import os
import glob
import argparse

# Importamos la inteligencia inyectable del archivo de reglas
from reglas_misiones import ESTRATEGIAS_DISPONIBLES

# ============================================================
# 1. CONFIGURACIÓN DE DIRECTORIOS
# ============================================================
parser = argparse.ArgumentParser(description="Analizador Universal FVS (GMAT y SatNOGS)")
parser.add_argument("-d", "--dir", type=str, required=True, 
                    help="Ruta al directorio que contiene los CSV a analizar en esta tanda.")
args = parser.parse_args()

DIR_ENTRADA = args.dir # se toma el directorio que se escribió por terminal

DIR_RESULTADOS = "resultados_analizador_universal"
if not os.path.exists(DIR_RESULTADOS):
    os.makedirs(DIR_RESULTADOS)
    print(f"📁 Directorio '{DIR_RESULTADOS}' creado.")

# ============================================================
# 2. MOTOR DE ANÁLISIS GENÉRICO
# ============================================================

def procesar_archivo(path_csv):
    try:
        # Algunos CSV de GMAT pueden tener espacios en los nombres de columnas
        df = pd.read_csv(path_csv)
    except Exception as e:
        print(f"  ⚠️ Error leyendo {path_csv}: {e}")
        return [], "Error de Lectura"

    columnas = df.columns.tolist()
    estrategia_elegida = None

    # Polimorfismo: Preguntamos a cada clase si reconoce la estructura del CSV
    for estrategia in ESTRATEGIAS_DISPONIBLES:
        if estrategia.es_esta_mision(columnas):
            estrategia_elegida = estrategia
            break
            
    if not estrategia_elegida:
        return [], "Desconocido"

    # La estrategia elegida procesa el archivo según sus propias reglas
    hits = estrategia_elegida.extraer_eventos_criticos(df, path_csv)
    
    return hits, estrategia_elegida.nombre

# ============================================================
# 3. BÚSQUEDA Y PROCESAMIENTO
# ============================================================

# Buscamos patrones de SatNOGS y GMAT solo en el directorio indicado
archivos_a_analizar = glob.glob(os.path.join(DIR_ENTRADA, "*telemetria*.csv")) + \
                      glob.glob(os.path.join(DIR_ENTRADA, "*_Telemetria.csv"))

print(f"--- Iniciando Analizador. Escaneando directorio: '{DIR_ENTRADA}' ---")
lineas_reporte = ["=== INFORME UNIVERSAL FVS (MODULAR) ===\n", f"Fecha: {datetime.now()}\n\n"]
lineas_detalle = ["=== REGISTRO DETALLADO DE PUNTOS CRÍTICOS ===\n", f"Fecha: {datetime.now()}\n\n"]

print(f"--- Iniciando Analizador Universal. Archivos encontrados: {len(archivos_a_analizar)} ---")

for path_archivo in archivos_a_analizar:
    nombre_base = os.path.basename(path_archivo)
    print(f"\n[+] Evaluando: {nombre_base}")
    
    hits, tipo_mision = procesar_archivo(path_archivo)
    
    if tipo_mision in ["Desconocido", "Error de Lectura"]:
        print(f"  [!] Archivo ignorado. No coincide con ninguna estrategia conocida.")
        continue
        
    print(f"  [*] Motor asignado: {tipo_mision}")
    
    resumen = f"Archivo: {nombre_base} | Motor: {tipo_mision}\n"
    
    if hits:
        resumen += f"  - Puntos Críticos detectados: {len(hits)}\n"
        resumen += f"  - Energía en primer hit: {hits[0]['Bateria']}\n"
        resumen += f"  - Energía en último hit: {hits[-1]['Bateria']}\n"
        
        lineas_detalle.append(f"\nDETALLE: {nombre_base} ({tipo_mision})\n")
        lineas_detalle.append(f"{'Timestamp':<25} | {'Energía (V o Wh)':<15}\n")
        lineas_detalle.append("-" * 45 + "\n")
        for h in hits:
            lineas_detalle.append(f"{str(h['Tiempo']):<25} | {h['Bateria']:<15}\n")
        lineas_detalle.append("-" * 60 + "\n")
        
        print(f"  ✅ ÉXITO: {len(hits)} eventos críticos encontrados.")
    else:
        resumen += "  - Sin eventos críticos detectados.\n"
        print("  [i] Sin eventos críticos.")
        
    resumen += "-" * 50 + "\n"
    lineas_reporte.append(resumen)

# ============================================================
# 4. ESCRITURA DE REPORTES CON TIMING DEL SISTEMA
# ============================================================

# Generamos el timestamp para evitar la sobreescritura accidental
timestamp_ejecucion = datetime.now().strftime("%Y%m%d_%H%M%S")

path_resumen = os.path.join(DIR_RESULTADOS, f"reporte_fvs_universal_{timestamp_ejecucion}.txt")
path_detalle = os.path.join(DIR_RESULTADOS, f"detalle_hits_universal_{timestamp_ejecucion}.txt")

with open(path_resumen, "w") as f_res:
    f_res.writelines(lineas_reporte)

with open(path_detalle, "w") as f_det:
    f_det.writelines(lineas_detalle)

print(f"\n--- PROCESO COMPLETADO ---")
print(f"✅ Reporte consolidado guardado en: {path_resumen}")
print(f"✅ Detalle granular guardado en: {path_detalle}")