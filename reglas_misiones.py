import pandas as pd
from datetime import datetime
import os

# ============================================================
# ESTRATEGIAS SATNOGS (Telemetría Empírica)
# ============================================================

class CatSatEstrategia:
    nombre = "CatSat (Empírico)"
    
    @staticmethod
    def es_esta_mision(columnas):
        return 'corriente_carga_A' in columnas

    @staticmethod
    def extraer_eventos_criticos(df, path_archivo):
        df_critico = df[df['corriente_carga_A'] <= 0.05]
        eventos = []
        for _, fila in df_critico.iterrows():
            if pd.notna(fila['voltaje_bateria_V']):
                eventos.append({"Tiempo": fila['timestamp'], "Bateria": round(fila['voltaje_bateria_V'], 3)})
        return eventos


class LASARsatEstrategia:
    nombre = "LASARsat (Empírico)"
    
    @staticmethod
    def es_esta_mision(columnas):
        return 'corriente_paneles_A' in columnas

    @staticmethod
    def extraer_eventos_criticos(df, path_archivo):
        df_critico = df[df['corriente_paneles_A'] <= 0.05]
        eventos = []
        for _, fila in df_critico.iterrows():
            if pd.notna(fila['voltaje_bateria_V']):
                eventos.append({"Tiempo": fila['timestamp'], "Bateria": round(fila['voltaje_bateria_V'], 3)})
        return eventos


class RamSatEstrategia:
    nombre = "RamSat (Empírico)"
    
    @staticmethod
    def es_esta_mision(columnas):
        return 'voltaje_panel_V' in columnas

    @staticmethod
    def extraer_eventos_criticos(df, path_archivo):
        df_critico = df[df['voltaje_panel_V'] <= 1.0]
        eventos = []
        for _, fila in df_critico.iterrows():
            if pd.notna(fila['voltaje_bateria_V']):
                eventos.append({"Tiempo": fila['timestamp'], "Bateria": round(fila['voltaje_bateria_V'], 3)})
        return eventos

# ============================================================
# ESTRATEGIA GMAT (Simulación Teórica)
# ============================================================

class GMAT_SimulacionEstrategia:
    nombre = "Simulación GMAT"
    
    @staticmethod
    def es_esta_mision(columnas):
        # GMAT siempre genera esta columna específica
        return 'Sat1.UTCGregorian' in columnas

    @staticmethod
    def parse_gmat_time(time_str):
        try:
            return datetime.strptime(str(time_str).strip(), "%d %b %Y %H:%M:%S.%f")
        except Exception:
            return None

    @staticmethod
    def cargar_intervalos(path_csv):
        try:
            df = pd.read_csv(path_csv)
            intervalos = []
            for _, row in df.iterrows():
                start_str = str(row['Start Time (UTC)']).strip()
                if start_str and start_str[0].isdigit():
                    start = GMAT_SimulacionEstrategia.parse_gmat_time(start_str)
                    stop = GMAT_SimulacionEstrategia.parse_gmat_time(row['Stop Time (UTC)'])
                    if start and stop:
                        intervalos.append((start, stop))
            return intervalos
        except Exception:
            return []

    @staticmethod
    def extraer_eventos_criticos(df, path_archivo):
        # 1. Inferir las rutas de los archivos hermanos
        prefijo = path_archivo.replace("_Telemetria.csv", "")
        p_eclip = prefijo + "_Eclipses.csv"
        p_cont = prefijo + "_Contactos.csv"
        
        # 2. Cargar intervalos
        int_eclip = GMAT_SimulacionEstrategia.cargar_intervalos(p_eclip)
        int_cont = GMAT_SimulacionEstrategia.cargar_intervalos(p_cont)
        
        eventos = []
        
        # 3. Cruzar tiempos
        for _, fila in df.iterrows():
            t_actual = GMAT_SimulacionEstrategia.parse_gmat_time(fila['Sat1.UTCGregorian'])
            if not t_actual: continue

            en_eclipse = any(s <= t_actual <= e for s, e in int_eclip)
            en_contacto = any(s <= t_actual <= e for s, e in int_cont)

            if en_eclipse and en_contacto:
                eventos.append({
                    "Tiempo": t_actual, 
                    "Bateria": round(fila['BateriaWh'], 3)
                })
                
        return eventos


# ============================================================
# REGISTRO MAESTRO
# ============================================================
ESTRATEGIAS_DISPONIBLES = [CatSatEstrategia, LASARsatEstrategia, RamSatEstrategia, GMAT_SimulacionEstrategia]