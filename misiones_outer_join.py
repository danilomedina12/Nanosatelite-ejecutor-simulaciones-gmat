#!/usr/bin/env python3

import requests
import pandas as pd
from datetime import datetime
import os
from functools import reduce

GRAFANA_URL = "https://dashboard.satnogs.org/api/ds/query?ds_type=influxdb"

# Diccionario Avanzado: Solo modificás acá el rango y el script se encarga del resto
SATS = {
    "CatSat": {
        "norad": 60246, "from": "now-60d", "to": "now",
        "metrics": {
            "voltaje_bateria_V": {"field": "batt_vbatt", "divisor": 1000},
            "corriente_carga_A": {"field": "p60_batt_chrg", "divisor": 1000},
            "temp_panel_C": {"field": "suns_temp_xpos", "divisor": 1},
            "temp_radio_C": {"field": "ax100_temp_pa", "divisor": 10}
        }
    },
    "LASARsat": {
        "norad": 62391, "from": "now-60d", "to": "now",
        "metrics": {
            "voltaje_bateria_V": {"field": "psu_battery", "divisor": 1000},
            "corriente_paneles_A": {"field": "psu_cur_in", "divisor": 1000},
            "temp_panel_C": {"field": "sol_temp_xp", "divisor": 100},
            "paquetes_tx": {"field": "uhf_tx_cnt", "divisor": 1}
        }
    },
    "RamSat": {
        "norad": 48850, "from": "1623715200000", "to": "1628899200000",
        "metrics": {
            "voltaje_bateria_V": {"field": "battery_voltage", "divisor": 100},
            "voltaje_panel_V": {"field": "voltage_feeding_bcr1_x", "divisor": 100},
            "temp_panel_C": {"field": "temperature_pos_x_array", "divisor": 10},
            "corriente_bus_A": {"field": "battery_bus_current", "divisor": 100}
        }
    }
}

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
        print(f"  ⚠️ Error extrayendo {field}: {e}")
        return None

def procesar_satelite(nombre, info):
    print(f"\n🛰️ Construyendo matriz de telemetría para {nombre}...")
    
    # --- LÓGICA DE FORMATEO AUTOMÁTICO DE NOMBRE ---
    time_from = str(info["from"])
    time_to = str(info["to"])
    
    if time_from.startswith("now-") and time_from.endswith("d"):
        # Extrae directamente el "60d", "15d", etc.
        rango_str = time_from.replace("now-", "")
    elif time_from.isdigit() and time_to.isdigit():
        # Si son timestamps (RamSat), calcula la diferencia en días
        delta_ms = int(time_to) - int(time_from)
        dias = delta_ms // (1000 * 60 * 60 * 24)
        rango_str = f"{dias}d"
    else:
        rango_str = "custom"
    # ------------------------------------------------
    
    dataframes = []
    
    for col_name, metric_info in info["metrics"].items():
        print(f"  ⬇️ Descargando {metric_info['field']}...")
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
        print("  ❌ No se obtuvieron datos.")
        return
        
    df_final = reduce(lambda left, right: pd.merge(left, right, on='timestamp', how='outer'), dataframes)
    df_final.sort_index(inplace=True)
    df_final.reset_index(inplace=True)
    
    # El nombre se formatea solo usando la variable dinámica rango_str
    filename = f"telemetria_extendida_{nombre.lower()}_{rango_str}.csv"
    df_final.to_csv(filename, index=False, sep=',')
    print(f"✅ ¡Éxito! CSV unificado generado con {len(df_final)} registros y {len(df_final.columns)} columnas.")
    print(f"💾 Guardado en: {os.path.abspath(filename)}")

# Ejecución
for sat_name, sat_info in SATS.items():
    procesar_satelite(sat_name, sat_info)