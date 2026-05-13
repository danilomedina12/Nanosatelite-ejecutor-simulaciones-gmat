#!/usr/bin/env python3

import requests

BASE_URL = "https://db.satnogs.org/api"

SATS = [
    "RamSat",
    "CatSat",
    "LASARSAT"
]


def buscar_satelite(nombre):

    url = f"{BASE_URL}/satellites/"

    print(f"\n🔎 Buscando satélite: {nombre}")

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()

        sats = r.json()

        encontrados = []

        for sat in sats:

            sat_name = sat.get("name", "")

            if nombre.lower() in sat_name.lower():

                encontrados.append({
                    "name": sat_name,
                    "norad": sat.get("norad_cat_id"),
                    "status": sat.get("status"),
                    "image": sat.get("image")
                })

        if not encontrados:
            print("❌ No encontrado")
            return

        for e in encontrados:

            print("\n🛰️ Coincidencia encontrada")
            print(f"Nombre     : {e['name']}")
            print(f"NORAD ID   : {e['norad']}")
            print(f"Estado     : {e['status']}")
            print(f"Imagen     : {e['image']}")

    except requests.RequestException as e:
        print(f"⚠️ Error: {e}")


def main():

    print("=== Búsqueda NORAD en SatNOGS ===")

    for sat in SATS:
        buscar_satelite(sat)


if __name__ == "__main__":
    main()