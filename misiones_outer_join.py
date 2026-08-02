#!/usr/bin/env python3

import requests
import pandas as pd
from datetime import datetime
import os
import json
from functools import reduce

GRAFANA_URL = "https://dashboard.satnogs.org/api/ds/query?ds_type=influxdb"
CONFIG_FILE = "sats.json"

def cargar_configuracion(path_json):
    """Carga la especificación de misiones desde un archivo JSON externo"""
    if not os.path.exists(path_json):
        print(f"Error Fatal: No se encontró el archivo de configuración '{path_json}'.")
        exit(1)
        
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parseando '{path_json}': {e}")
        exit(1)

def extraer_metrica(norad, field, time_from, time_to, col_name, divisor):
    """Extrae una sola métrica de InfluxDB y devuelve un DataFrame con el Timestamp como índice"""
    payload = {
        "queries": [{
            "datasource": {"type": "influxdb", "uid": "000000001"},
            "measurement": f"/^{norad}$/",
            "refId": "A",
            "select": [[
                {"params": [field], "type": "field"},
                {"params": [], "type": "last"}
            ]],
            "groupBy": [
                {"params": ["$__interval"], "type": "time"},
                {"params": ["none"], "type": "fill"}
            ],
            "intervalMs": 600000, # 10 minutos
            "maxDataPoints": 5000,
            "tags": []
        }],
        "from": time_from, "to": time_to
    }

    try:
        r = requests.post(GRAFANA_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        
        frames = data['results']['A']['frames'][0]
        timestamps = frames['data']['values'][0]
        valores = frames['data']['values'][1]
        
        df = pd.DataFrame({
            "timestamp": [datetime.fromtimestamp(ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
            col_name: [v / divisor for v in valores]
        })
        
        df.set_index("timestamp", inplace=True)
        return df.dropna()
    except Exception as e:
        print(f"Error extrayendo {field}: {e}")
        return None

def procesar_satelite(nombre, info):
    print(f"\nConstruyendo matriz de telemetría para {nombre}...")
    
    time_from = str(info["from"])
    time_to = str(info["to"])
    
    if time_from.startswith("now-") and time_from.endswith("d"):
        rango_str = time_from.replace("now-", "")
    elif time_from.isdigit() and time_to.isdigit():
        delta_ms = int(time_to) - int(time_from)
        dias = delta_ms // (1000 * 60 * 60 * 24)
        rango_str = f"{dias}d"
    else:
        rango_str = "custom"
        
    dataframes = []
    
    for col_name, metric_info in info["metrics"].items():
        print(f"Descargando {metric_info['field']}...")
        df_metric = extraer_metrica(
            info["norad"], 
            metric_info["field"], 
            info["from"], 
            info["to"], 
            col_name, 
            metric_info["divisor"]
        )
        if df_metric is not None and not df_metric.empty:
            dataframes.append(df_metric)
            
    if not dataframes:
        print("No se obtuvieron datos.")
        return
        
    df_final = reduce(lambda left, right: pd.merge(left, right, on='timestamp', how='outer'), dataframes)
    df_final.sort_index(inplace=True)
    df_final.reset_index(inplace=True)
    
    filename = f"telemetria_extendida_{nombre.lower()}_{rango_str}.csv"
    df_final.to_csv(filename, index=False, sep=',')
    print(f"¡Éxito! CSV unificado generado con {len(df_final)} registros y {len(df_final.columns)} columnas.")
    print(f"Guardado en: {os.path.abspath(filename)}")

def main():
    sats_config = cargar_configuracion(CONFIG_FILE)
    for sat_name, sat_info in sats_config.items():
        procesar_satelite(sat_name, sat_info)

if __name__ == "__main__":
    main()