import re

def convertir(ruta):
    salida = ruta + ".csv"

    with open(ruta, "r") as f_in, open(salida, "w") as f_out:
        for linea in f_in:
            linea = linea.strip()

            if not linea:
                continue

            # Evita romper encabezados tipo "Spacecraft: Sat1"
            if ":" in linea and not linea[0].isdigit():
                continue

            # Reemplaza múltiples espacios por ;
            linea = re.sub(r'\s{2,}', ';', linea)

            f_out.write(linea + "\n")

    print("Listo:", salida)


archivo = input("Archivo: ").strip().strip('"').strip("'")
convertir(archivo)
