#!/usr/bin/env python3

import requests
import json

GRAFANA_URL = "https://dashboard.satnogs.org/api/ds/query?ds_type=influxdb"

def descubrir_variables(nombre, norad):
    print(f"\n🔍 Escaneando todas las variables disponibles para {nombre} ({norad})...")
    
    payload = {
        "queries": [
            {
                "datasource": {"type": "influxdb", "uid": "000000001"},
                # Enviamos una consulta SQL cruda a InfluxDB para pedir las 'llaves'
                "query": f'SHOW FIELD KEYS FROM "{norad}"',
                "rawQuery": True,
                "refId": "A"
            }
        ]
    }

    headers = {
        "Content-Type": "application/json", 
        "Accept": "application/json"
    }

    try:
        r = requests.post(GRAFANA_URL, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        
        try:
            # Grafana envuelve la respuesta de SHOW FIELD KEYS en esta estructura
            frames = data['results']['A']['frames'][0]
            variables = frames['data']['values'][0]
            
            print(f"✅ ¡Éxito! Se encontraron {len(variables)} variables distintas.")
            print("\n📋 Lista alfabética para analizar:")
            
            for var in sorted(variables):
                print(f"  - {var}")
                
        except (KeyError, IndexError):
            print("⚠️ No se pudo extraer la lista. InfluxDB no devolvió campos para este NORAD.")
            
    except Exception as e:
        print(f"⚠️ Error HTTP: {e}")

# Misiones a explorar
descubrir_variables("CatSat", 60246)
descubrir_variables("LASARsat", 62391)
descubrir_variables("RamSat", 48850)