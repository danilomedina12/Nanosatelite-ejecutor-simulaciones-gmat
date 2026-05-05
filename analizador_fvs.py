import pandas as pd
from datetime import datetime
import os
import glob

# ============================================================
# 1. FUNCIONES DE APOYO
# ============================================================

def parse_gmat_time(time_str):
    """Parsea el tiempo de GMAT. Soporta el formato con milisegundos."""
    try:
        return datetime.strptime(str(time_str).strip(), "%d %b %Y %H:%M:%S.%f")
    except Exception:
        return None

def cargar_intervalos(path_csv):
    """Carga los bloques de tiempo y cuenta eventos únicos."""
    try:
        df = pd.read_csv(path_csv)
        intervalos = []
        eventos_unicos = set() 

        for _, row in df.iterrows():
            start_str = str(row['Start Time (UTC)']).strip()
            if start_str and start_str[0].isdigit():
                start = parse_gmat_time(start_str)
                stop = parse_gmat_time(row['Stop Time (UTC)'])
                
                if start and stop:
                    intervalos.append((start, stop))
                    token = row.get('Event Number', start_str)
                    eventos_unicos.add(token)
            
        return intervalos, len(eventos_unicos)
    except Exception as e:
        print(f"Error en {path_csv}: {e}")
        return [], 0

def analizar_escenario(path_tele, path_eclip, path_cont):
    df_tele = pd.read_csv(path_tele)
    int_eclip, cant_eclip = cargar_intervalos(path_eclip)
    int_cont, cant_cont = cargar_intervalos(path_cont)

    print(f"      [DATOS] Eclipses Reales: {cant_eclip} | Contactos: {cant_cont}")

    eventos = []
    for _, fila in df_tele.iterrows():
        t_actual = parse_gmat_time(fila['Sat1.UTCGregorian'])
        if not t_actual: continue

        en_eclipse = any(s <= t_actual <= e for s, e in int_eclip)
        en_contacto = any(s <= t_actual <= e for s, e in int_cont)

        if en_eclipse and en_contacto:
            eventos.append({"Tiempo": t_actual, "Bateria": fila['BateriaWh']})
    return eventos

# ============================================================
# 2. PROCESAMIENTO UNIFICADO Y GENERACIÓN DE REPORTES
# ============================================================

RUTA_RESULTADOS = "resultados/convertidos"
archivos_telemetria = glob.glob(os.path.join(RUTA_RESULTADOS, "*_Telemetria.csv"))

# Listas para almacenar las líneas de los dos reportes
lineas_reporte = ["=== INFORME RESUMEN DE PATRONES FVS ===\n", f"Fecha: {datetime.now()}\n\n"]
lineas_detalle = ["=== REGISTRO DETALLADO DE PUNTOS CRÍTICOS (BISTURÍ) ===\n", f"Fecha: {datetime.now()}\n\n"]

print(f"--- Iniciando análisis de {len(archivos_telemetria)} escenarios ---")

for path_tele in archivos_telemetria:
    prefijo = path_tele.replace("_Telemetria.csv", "")
    nombre_base = os.path.basename(prefijo)
    
    p_eclip = prefijo + "_Eclipses.csv"
    p_cont = prefijo + "_Contactos.csv"
    
    if os.path.exists(p_eclip) and os.path.exists(p_cont):
        print(f"\n[+] Procesando: {nombre_base}")
        hits = analizar_escenario(path_tele, p_eclip, p_cont)
        
        # --- 2a. Lógica para el REPORTE RESUMEN ---
        resumen = f"Escenario: {nombre_base}\n"
        if hits:
            resumen += f"  - Puntos Críticos (TX en Eclipse): {len(hits)}\n"
            resumen += f"  - Batería en primer hit: {hits[0]['Bateria']} Wh\n"
            resumen += f"  - Batería en último hit: {hits[-1]['Bateria']} Wh\n"
            
            # --- 2b. Lógica para el REPORTE DETALLADO (El Bisturí) ---
            lineas_detalle.append(f"\nDETALLE ESCENARIO: {nombre_base}\n")
            lineas_detalle.append(f"{'Timestamp':<25} | {'Bateria (Wh)':<15}\n")
            lineas_detalle.append("-" * 45 + "\n")
            for h in hits:
                lineas_detalle.append(f"{str(h['Tiempo']):<25} | {h['Bateria']:<15}\n")
            lineas_detalle.append("-" * 60 + "\n")
            
            print(f"    ✅ HIT: Se detectaron {len(hits)} puntos críticos.")
        else:
            resumen += "  - Sin pases nocturnos detectados.\n"
            print("    [i] Sin pases nocturnos detectados.")
            
        resumen += "-" * 40 + "\n"
        lineas_reporte.append(resumen)
    else:
        print(f"\n[!] Faltan archivos hermanos para: {nombre_base}")

# ============================================================
# 3. ESCRITURA DE ARCHIVOS FINALES
# ============================================================

# Escribir reporte resumen
with open("reporte_fvs.txt", "w") as f_res:
    f_res.writelines(lineas_reporte)

# Escribir reporte detallado (el bisturí)
with open("detalle_hits_fvs.txt", "w") as f_det:
    f_det.writelines(lineas_detalle)

print("\n--- PROCESO COMPLETADO ---")
print(f"✅ Resumen generado en: reporte_fvs.txt")
print(f"✅ Detalle (bisturí) generado en: detalle_hits_fvs.txt")