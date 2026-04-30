#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatizador GMAT v2 - Nanosatelite 3U - Dataset para modelo probabilistico
Genera escenarios con modos de operacion reales y extrae metricas de Markov.

Uso:
    python3 ejecutar_simulaciones.py

Requiere:
    - GmatConsole instalado (modo headless)
    - SAT1_Template.script en CARPETA_SCRIPTS
    - Python 3.8+, sin dependencias externas
"""

import subprocess
import os
import csv
import json
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURACION - AJUSTAR SEGUN TU SISTEMA
# ============================================================

GMAT_CONSOLE   = "/home/danilo/Escritorio/GMAT/R2026a/bin/GmatConsole"
CARPETA_SCRIPTS = "/home/danilo/Documentos/MisMisionesGMAT"
CARPETA_OUTPUT  = "/home/danilo/Escritorio/GMAT/R2026a/output"
CARPETA_RESULTS = "/home/danilo/Documentos/MisMisionesGMAT/resultados"
TEMPLATE        = os.path.join(CARPETA_SCRIPTS, "SAT1_Template.script")

DURACION_SECS   = 691200.0   # 8 dias

# Constantes del panel solar (fijas para todos los escenarios)
P_SOLAR_BASE    = 1361.0     # W/m2
AREA_PANEL      = 0.03       # m2
EFF_CELULA      = 0.18       # eficiencia base de celulas fotovoltaicas
PASO_SECS       = 60.0       # paso de integracion en segundos

# Limite critico de bateria para el modelo de Markov
BATERIA_CRITICA = 4.0        # Wh - limite de BateriaMin en el script

# ============================================================
# DEFINICION DE ESCENARIOS
#
# consumo_base_w  : consumo constante del modo (W)
# consumo_tx_w    : consumo durante transmision sobre UNDAV (W)
#                   Si es None, no se inyecta logica de transmision
# eficiencia      : factor de eficiencia de paneles (0.0 a 1.0)
# ============================================================

ESCENARIOS = [

    # --- GRUPO 1: MODO IDLE (3W base) ---
    {
        "nombre":        "E1_Idle_3W_Ef100",
        "grupo":         "Idle",
        "consumo_base_w": 3.0,
        "consumo_tx_w":  None,
        "eficiencia":    1.00,
        "descripcion":   "Reposo 3W, paneles 100% - linea base supervivencia"
    },
    {
        "nombre":        "E1_Idle_3W_Ef90",
        "grupo":         "Idle",
        "consumo_base_w": 3.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.90,
        "descripcion":   "Reposo 3W, paneles 90% - degradacion leve"
    },
    {
        "nombre":        "E1_Idle_3W_Ef85",
        "grupo":         "Idle",
        "consumo_base_w": 3.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.85,
        "descripcion":   "Reposo 3W, paneles 85% - degradacion moderada"
    },
    {
        "nombre":        "E1_Idle_3W_Ef50",
        "grupo":         "Fallo",
        "consumo_base_w": 3.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.50,
        "descripcion":   "Reposo 3W, paneles 50% - fallo de actitud critico"
    },

    # --- GRUPO 2: MODO NOMINAL IoT (5W base) ---
    {
        "nombre":        "E2_Nominal_5W_Ef100",
        "grupo":         "Nominal",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  None,
        "eficiencia":    1.00,
        "descripcion":   "Nominal 5W, paneles 100%"
    },
    {
        "nombre":        "E2_Nominal_5W_Ef90",
        "grupo":         "Nominal",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.90,
        "descripcion":   "Nominal 5W, paneles 90%"
    },
    {
        "nombre":        "E2_Nominal_5W_Ef85",
        "grupo":         "Nominal",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.85,
        "descripcion":   "Nominal 5W, paneles 85%"
    },
    {
        "nombre":        "E2_Nominal_5W_Ef50",
        "grupo":         "Fallo",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  None,
        "eficiencia":    0.50,
        "descripcion":   "Nominal 5W, paneles 50% - fallo actitud con carga nominal"
    },

    # --- GRUPO 3: TRANSMISION DINAMICA (15W en pase UNDAV, 5W base) ---
    # El consumo de 15W se inyecta SOLO cuando el satelite ve la estacion.
    # Fuera del pase el satelite opera en modo nominal (5W).
    {
        "nombre":        "E3_Tx15W_Base5W_Ef100",
        "grupo":         "Transmision",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  15.0,
        "eficiencia":    1.00,
        "descripcion":   "Transmision 15W en pase, nominal 5W, paneles 100%"
    },
    {
        "nombre":        "E3_Tx15W_Base5W_Ef90",
        "grupo":         "Transmision",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  15.0,
        "eficiencia":    0.90,
        "descripcion":   "Transmision 15W en pase, nominal 5W, paneles 90%"
    },
    {
        "nombre":        "E3_Tx15W_Base5W_Ef85",
        "grupo":         "Transmision",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  15.0,
        "eficiencia":    0.85,
        "descripcion":   "Transmision 15W en pase, nominal 5W, paneles 85%"
    },
    {
        "nombre":        "E3_Tx20W_Base5W_Ef100",
        "grupo":         "Transmision",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  20.0,
        "eficiencia":    1.00,
        "descripcion":   "Transmision 20W pico en pase, nominal 5W, paneles 100%"
    },
    {
        "nombre":        "E3_Tx20W_Base5W_Ef85",
        "grupo":         "Transmision",
        "consumo_base_w": 5.0,
        "consumo_tx_w":  20.0,
        "eficiencia":    0.85,
        "descripcion":   "Transmision 20W pico en pase, nominal 5W, paneles 85%"
    },
]


# ============================================================
# CALCULO DE DELTAS
# ============================================================

def calcular_deltas(consumo_w, eficiencia, paso=PASO_SECS):
    """
    Calcula DeltaE_Sol y DeltaE_Eclipse para un paso dado.
    P_panel = P_SOLAR_BASE * AREA * EFF_CELULA * eficiencia
    DeltaE_Sol     = (P_panel - consumo) * paso / 3600
    DeltaE_Eclipse = -consumo * paso / 3600
    """
    p_panel = P_SOLAR_BASE * AREA_PANEL * EFF_CELULA * eficiencia
    delta_sol     = round((p_panel - consumo_w) * paso / 3600.0, 7)
    delta_eclipse = round(-consumo_w * paso / 3600.0, 7)
    return delta_sol, delta_eclipse


# ============================================================
# GENERACION DEL BLOQUE DE MISION SEQUENCE
# Aqui se inyecta la logica dinamica de transmision si aplica.
# ============================================================

def generar_mission_sequence(escenario, delta_sol_base, delta_eclipse_base):
    """
    Genera el bloque BeginMissionSequence completo.
    Si el escenario tiene consumo_tx_w, agrega la deteccion de elevacion
    sobre UNDAV para cambiar el delta de energia durante el pase.
    """
    consumo_tx = escenario.get("consumo_tx_w")
    eficiencia  = escenario["eficiencia"]

    # Bloques de inicio comunes
    bloque = f"""
BeginMissionSequence;

BateriaWh        = 38.0;
BateriaMax       = 40.0;
BateriaMin       = {BATERIA_CRITICA};
PasoSeg          = {PASO_SECS};
ProximoPaso      = {PASO_SECS};
DeltaE_Sol       = {delta_sol_base};
DeltaE_Eclipse   = {delta_eclipse_base};
DoD_Limite_Wh    = 12.0;
DoD_Actual       = 0.0;
DoD_Acum_Eclipse = 0.0;
EstadoAnterior   = 1.0;
EarthRad         = 6378.137;
"""

    # Si hay transmision dinamica, precalcular los deltas de TX
    if consumo_tx is not None:
        delta_sol_tx, delta_eclipse_tx = calcular_deltas(consumo_tx, eficiencia)
        bloque += f"""
% Deltas modo base (guardados para restaurar fuera del pase)
DeltaE_Sol_Base   = {delta_sol_base};
DeltaE_Eclipse_Base = {delta_eclipse_base};
% Deltas para modo transmision (consumo {consumo_tx}W durante pase UNDAV)
DeltaE_Sol_TX    = {delta_sol_tx};
DeltaE_Eclipse_TX = {delta_eclipse_tx};
"""

    bloque += f"""
While Sat1.ElapsedSecs < {DURACION_SECS}

   Propagate EarthPointProp(Sat1) {{Sat1.ElapsedSecs = ProximoPaso}};
   ProximoPaso = ProximoPaso + PasoSeg;

   % Deteccion geometrica de eclipse (modelo cilindro de sombra)
   SatX = Sat1.X;
   SatY = Sat1.Y;
   SatZ = Sat1.Z;
   SunX = Sun.X;
   SunY = Sun.Y;
   SunZ = Sun.Z;

   DotSatSun = SatX*SunX + SatY*SunY + SatZ*SunZ;
   SunMag = sqrt(SunX*SunX + SunY*SunY + SunZ*SunZ);
   PerpDist = sqrt(SatX*SatX + SatY*SatY + SatZ*SatZ - (DotSatSun/SunMag)^2);
"""

    # Logica de transmision dinamica: detectar visibilidad con UNDAV
    # Se usa la elevacion del satelite sobre la estacion UNDAV.
    # Sat1.UNDAV_Station.Elevation > 7 grados = pase valido
    if consumo_tx is not None:
        bloque += f"""
   % Deteccion geometrica de pase sobre UNDAV
   % UNDAV: Lat=-34.66 deg, Lon=301.61 deg Este, alt=0.01 km
   % La posicion inercial de UNDAV se actualiza con la rotacion terrestre
   % GAST_0 = angulo sidereo de Greenwich al epoch '22 Apr 2026 14:30:00 UTC'
   LonInercial_deg = 301.61 + 124.5442 + 0.004178079 * Sat1.ElapsedSecs;
   LonInercial_rad = LonInercial_deg * 0.017453293;

   UNDAV_X = 5246.289 * cos(LonInercial_rad);
   UNDAV_Y = 5246.289 * sin(LonInercial_rad);
   UNDAV_Z = -3627.287;

   % Vector del centro de la Tierra al satelite, relativo a UNDAV
   dX = SatX - UNDAV_X;
   dY = SatY - UNDAV_Y;
   dZ = SatZ - UNDAV_Z;

   % Zenith de UNDAV = posicion UNDAV normalizada (vector hacia el cielo)
   NormD    = sqrt(dX^2 + dY^2 + dZ^2);
   DotZenD  = dX*(UNDAV_X/6378.147) + dY*(UNDAV_Y/6378.147) + dZ*(UNDAV_Z/6378.147);

   % Elevacion = asin(componente_radial / distancia_total) en radianes
   % Convertir a grados con RadToDeg = 57.29578
   ElevacionDeg = asin(DotZenD / NormD) * 57.29578;

   % Si elevacion > 7 grados -> pase valido -> consumo TX
   If ElevacionDeg > 7.0
      DeltaE_Sol     = DeltaE_Sol_TX;
      DeltaE_Eclipse = DeltaE_Eclipse_TX;
   Else
      DeltaE_Sol     = {delta_sol_base};
      DeltaE_Eclipse = {delta_eclipse_base};
   EndIf;
"""

    # Logica principal de eclipse/sol con DoD
    bloque += """
   If DotSatSun < 0
      If PerpDist < EarthRad

         % --- EN ECLIPSE ---
         If EstadoAnterior == 1
            DoD_Acum_Eclipse = 0.0;
         EndIf;

         EstadoAnterior   = 0;
         BateriaWh        = BateriaWh + DeltaE_Eclipse;
         DoD_Acum_Eclipse = DoD_Acum_Eclipse + 0.08333;

         If BateriaWh < BateriaMin
            BateriaWh = BateriaMin;
         EndIf;

      Else

         % --- EN SOL (fuera del cilindro de sombra) ---
         If EstadoAnterior == 0
            DoD_Actual       = DoD_Acum_Eclipse;
            DoD_Acum_Eclipse = 0.0;
         EndIf;

         EstadoAnterior = 1;
         BateriaWh = BateriaWh + DeltaE_Sol;

         If BateriaWh > BateriaMax
            BateriaWh = BateriaMax;
         EndIf;

      EndIf;

   Else

      % --- EN SOL (lado iluminado) ---
      If EstadoAnterior == 0
         DoD_Actual       = DoD_Acum_Eclipse;
         DoD_Acum_Eclipse = 0.0;
      EndIf;

      EstadoAnterior = 1;
      BateriaWh = BateriaWh + DeltaE_Sol;

      If BateriaWh > BateriaMax
         BateriaWh = BateriaMax;
      EndIf;

   EndIf;

EndWhile;
"""
    return bloque


# ============================================================
# GENERACION DEL SCRIPT GMAT COMPLETO
# ============================================================

def generar_script(escenario):
    """
    Lee el template y genera el script completo para un escenario.
    Devuelve (ruta_script, delta_sol, delta_eclipse).
    """
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        contenido = f.read()

    nombre      = escenario["nombre"]
    eficiencia  = escenario["eficiencia"]
    consumo_base = escenario["consumo_base_w"]
    consumo_tx   = escenario.get("consumo_tx_w")

    delta_sol, delta_eclipse = calcular_deltas(consumo_base, eficiencia)

    # Reemplazar marcadores estaticos
    contenido = contenido.replace("@@NOMBRE_ESCENARIO@@", nombre)
    contenido = contenido.replace("@@CONSUMO_W@@",        str(consumo_base))
    contenido = contenido.replace("@@CONSUMO_TX@@",       str(consumo_tx) if consumo_tx else "N/A")
    contenido = contenido.replace("@@EFICIENCIA@@",       str(eficiencia))
    contenido = contenido.replace("@@DURACION_SECS@@",    str(DURACION_SECS))

    # Agregar variable de TX si aplica
    vars_extra = ""
    if consumo_tx is not None:
        vars_extra = ("Create Variable DeltaE_Sol_TX DeltaE_Eclipse_TX\n"
                     "Create Variable DeltaE_Sol_Base DeltaE_Eclipse_Base\n"
                     "Create Variable LonInercial_deg LonInercial_rad\n"
                     "Create Variable UNDAV_X UNDAV_Y UNDAV_Z\n"
                     "Create Variable dX dY dZ NormD DotZenD ElevacionDeg;")

    contenido = contenido.replace("@@VARS_EXTRA@@", vars_extra)

    # Reemplazar el bloque de mission sequence completo
    mission_seq = generar_mission_sequence(escenario, delta_sol, delta_eclipse)
    contenido = contenido.replace("@@MISSION_SEQUENCE@@", mission_seq)

    nombre_archivo = nombre + ".script"
    ruta_script = os.path.join(CARPETA_SCRIPTS, nombre_archivo)

    with open(ruta_script, 'w', encoding='utf-8') as f:
        f.write(contenido)

    return ruta_script, delta_sol, delta_eclipse


# ============================================================
# EJECUCION DE GMAT
# ============================================================

def ejecutar_gmat(ruta_script):
    """
    Ejecuta GMAT en modo headless. Devuelve (exito, stdout, stderr).
    """
    if not os.path.isfile(GMAT_CONSOLE):
        return False, "", f"No se encontro GmatConsole en: {GMAT_CONSOLE}"

    cmd = [GMAT_CONSOLE, "--run", ruta_script, "--exit"]

    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200   # 2 horas max por simulacion de 8 dias
        )
        exito = resultado.returncode == 0
        return exito, resultado.stdout, resultado.stderr

    except subprocess.TimeoutExpired:
        return False, "", "Timeout: simulacion supero 2 horas"
    except FileNotFoundError:
        return False, "", f"No se pudo ejecutar: {GMAT_CONSOLE}"


# ============================================================
# EXTRACCION DE METRICAS DEL CSV (para modelo de Markov)
# ============================================================

def extraer_metricas(nombre_escenario):
    """
    Lee el CSV de telemetria y extrae:
      - bateria_min     : valor minimo de BateriaWh
      - dod_max         : valor maximo de DoD_Actual
      - tiempo_colapso  : ElapsedSecs cuando BateriaWh toco BateriaMin
      - total_filas     : numero de filas de datos
      - colapso         : True si la bateria llego al limite critico
    """
    csv_nombre = nombre_escenario + "_Telemetria.csv"
    csv_ruta = os.path.join(CARPETA_OUTPUT, csv_nombre)

    metricas = {
        "bateria_min":    None,
        "dod_max":        None,
        "tiempo_colapso": None,
        "total_filas":    0,
        "colapso":        False,
        "csv_encontrado": False
    }

    if not os.path.isfile(csv_ruta):
        return metricas

    metricas["csv_encontrado"] = True

    bateria_min = float('inf')
    dod_max     = 0.0
    elapsed     = 0.0
    fila_num    = 0

    try:
        with open(csv_ruta, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        # La primera linea es cabecera
        # Formato: UTCGregorian  Lat  Lon  Alt  BateriaWh  DoD_Actual
        # Los campos estan separados por espacios multiples (fixed width)
        for linea in lineas[1:]:
            partes = linea.split()
            if len(partes) < 8:
                continue

            fila_num += 1

            try:
                # El timestamp UTCGregorian ocupa los primeros 4 tokens
                # (ej: "22 Apr 2026 14:30:00.000")
                # Luego: Lat Lon Alt BateriaWh DoD_Actual
                bateria_wh = float(partes[-2])
                dod_actual  = float(partes[-1])
            except (ValueError, IndexError):
                continue

            elapsed += PASO_SECS   # aproximacion del tiempo transcurrido

            if bateria_wh < bateria_min:
                bateria_min = bateria_wh

            if dod_actual > dod_max:
                dod_max = dod_actual

            # Detectar primer colapso (toca el limite critico)
            if bateria_wh <= BATERIA_CRITICA and not metricas["colapso"]:
                metricas["colapso"]        = True
                metricas["tiempo_colapso"] = elapsed

        metricas["total_filas"] = fila_num
        metricas["bateria_min"] = round(bateria_min, 5) if bateria_min != float('inf') else None
        metricas["dod_max"]     = round(dod_max, 5)

    except Exception as e:
        print(f"    [WARN] Error leyendo CSV: {e}")

    return metricas


# ============================================================
# RENOMBRADO DE OUTPUTS (evita sobreescritura entre escenarios)
# ============================================================

def renombrar_outputs(nombre_escenario):
    """
    GMAT guarda los archivos con el nombre definido en el script.
    Como ya estan nombrados con el nombre del escenario en el template,
    esta funcion verifica que existen y los mueve a CARPETA_RESULTS.
    """
    os.makedirs(CARPETA_RESULTS, exist_ok=True)

    archivos = [
        nombre_escenario + "_Telemetria.csv",
        nombre_escenario + "_Eclipses.txt",
        nombre_escenario + "_Contactos.txt",
    ]

    movidos = []
    for archivo in archivos:
        origen  = os.path.join(CARPETA_OUTPUT, archivo)
        destino = os.path.join(CARPETA_RESULTS, archivo)
        if os.path.isfile(origen):
            os.replace(origen, destino)
            movidos.append(archivo)

    return movidos


# ============================================================
# EXPORTAR RESUMEN A JSON (para el modelo probabilistico)
# ============================================================

def exportar_json(resumen_total):
    """
    Exporta todas las metricas en formato JSON para uso externo.
    """
    os.makedirs(CARPETA_RESULTS, exist_ok=True)
    ruta = os.path.join(CARPETA_RESULTS, "metricas_markov.json")

    datos = []
    for r in resumen_total:
        datos.append({
            "escenario":       r["escenario"],
            "grupo":           r["grupo"],
            "descripcion":     r["descripcion"],
            "consumo_base_w":  r["consumo_base_w"],
            "consumo_tx_w":    r["consumo_tx_w"],
            "eficiencia":      r["eficiencia"],
            "delta_sol":       r["delta_sol"],
            "delta_eclipse":   r["delta_eclipse"],
            "estado":          r["estado"],
            "bateria_min_wh":  r["metricas"]["bateria_min"],
            "dod_max_wh":      r["metricas"]["dod_max"],
            "colapso":         r["metricas"]["colapso"],
            "tiempo_colapso_s": r["metricas"]["tiempo_colapso"],
            "tiempo_colapso_h": round(r["metricas"]["tiempo_colapso"] / 3600, 2)
                                 if r["metricas"]["tiempo_colapso"] else None,
            "filas_csv":       r["metricas"]["total_filas"],
        })

    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    return ruta


# ============================================================
# EJECUCION PRINCIPAL
# ============================================================

def main():
    inicio = datetime.now()
    print("=" * 65)
    print("  AUTOMATIZADOR GMAT v2 - NANOSATELITE 3U - MODELO MARKOV")
    print(f"  Inicio    : {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duracion  : {DURACION_SECS/3600:.0f}h ({DURACION_SECS/86400:.1f} dias) por sim.")
    print(f"  Escenarios: {len(ESCENARIOS)}")
    print(f"  Outputs   : {CARPETA_RESULTS}")
    print("=" * 65)

    # Verificar GmatConsole antes de empezar
    if not os.path.isfile(GMAT_CONSOLE):
        print(f"\n[ERROR FATAL] GmatConsole no encontrado en:")
        print(f"  {GMAT_CONSOLE}")
        print(f"  Verificar la variable GMAT_CONSOLE en este script.")
        print(f"  Buscar con: find /home/danilo -name 'GmatConsole*' 2>/dev/null")
        return

    # Verificar que GmatConsole es ejecutable
    if not os.access(GMAT_CONSOLE, os.X_OK):
        print(f"\n[ERROR FATAL] GmatConsole existe pero no tiene permisos de ejecucion:")
        print(f"  {GMAT_CONSOLE}")
        print(f"  Corregir con: chmod +x {GMAT_CONSOLE}")
        return

    print(f"  GmatConsole : {GMAT_CONSOLE} [OK]")

    if not os.path.isfile(TEMPLATE):
        print(f"\n[ERROR FATAL] Template no encontrado:")
        print(f"  {TEMPLATE}")
        print(f"  Copiar SAT1_Template_v2.script a esa carpeta.")
        return

    os.makedirs(CARPETA_RESULTS, exist_ok=True)
    resumen_total = []

    for i, escenario in enumerate(ESCENARIOS, 1):
        nombre     = escenario["nombre"]
        consumo_tx = escenario.get("consumo_tx_w")

        print(f"\n[{i:02d}/{len(ESCENARIOS)}] {nombre}")
        print(f"  {escenario['descripcion']}")
        print(f"  Consumo base : {escenario['consumo_base_w']}W"
              + (f"  |  TX pase: {consumo_tx}W" if consumo_tx else ""))
        print(f"  Eficiencia   : {int(escenario['eficiencia']*100)}%")

        # Generar script
        ruta_script, delta_sol, delta_eclipse = generar_script(escenario)
        print(f"  DeltaE Sol   : {delta_sol:+.7f} Wh/paso")
        print(f"  DeltaE Ecl   : {delta_eclipse:+.7f} Wh/paso")

        # Ejecutar GMAT
        print(f"  Ejecutando...", end="", flush=True)
        t0 = datetime.now()
        exito, stdout, stderr = ejecutar_gmat(ruta_script)
        t1 = datetime.now()
        dur = (t1 - t0).total_seconds()

        if exito:
            print(f" OK ({dur:.0f}s)")
            metricas = extraer_metricas(nombre)
            movidos  = renombrar_outputs(nombre)

            print(f"  Bateria min  : {metricas['bateria_min']} Wh")
            print(f"  DoD max      : {metricas['dod_max']} Wh")
            if metricas["colapso"]:
                h = metricas["tiempo_colapso"] / 3600
                print(f"  COLAPSO en   : {h:.1f}h ({metricas['tiempo_colapso']:.0f}s)")
            else:
                print(f"  Sin colapso en {DURACION_SECS/3600:.0f}h")

            estado = "OK"
        else:
            print(f" FALLO ({dur:.0f}s)")
            output_completo = stdout + "\n" + stderr
            errores = [
                l.strip() for l in output_completo.splitlines()
                if "ERROR" in l and l.strip()
            ]
            if errores:
                print(f"    Errores GMAT ({len(errores)} total, mostrando primeros 5):")
                for e in errores[:5]:
                    print(f"      {e}")
            else:
                ultimas = [l for l in stdout.splitlines() if l.strip()][-6:]
                print(f"    Output GMAT (ultimas lineas):")
                for l in ultimas:
                    print(f"      {l}")
            metricas = extraer_metricas(nombre)
            estado   = "FALLO"

        resumen_total.append({
            "escenario":     nombre,
            "grupo":         escenario["grupo"],
            "descripcion":   escenario["descripcion"],
            "consumo_base_w": escenario["consumo_base_w"],
            "consumo_tx_w":  consumo_tx,
            "eficiencia":    escenario["eficiencia"],
            "delta_sol":     delta_sol,
            "delta_eclipse": delta_eclipse,
            "estado":        estado,
            "duracion_s":    dur,
            "metricas":      metricas,
        })

    # --- Resumen final en consola ---
    fin = datetime.now()
    tiempo_total = (fin - inicio).total_seconds()

    print("\n" + "=" * 65)
    print("  RESUMEN - METRICAS PARA MODELO DE MARKOV")
    print("=" * 65)
    print(f"  {'Escenario':<35} {'Est':5} {'BatMin':8} {'DoDMax':8} {'Colapso'}")
    print(f"  {'-'*35} {'-'*5} {'-'*8} {'-'*8} {'-'*15}")

    exitosos = 0
    for r in resumen_total:
        m = r["metricas"]
        bat  = f"{m['bateria_min']:.2f}" if m["bateria_min"] else "---"
        dod  = f"{m['dod_max']:.3f}"     if m["dod_max"] is not None else "---"
        col  = f"{m['tiempo_colapso']/3600:.1f}h" if m["colapso"] else "No"
        est  = "OK" if r["estado"] == "OK" else "FAIL"
        print(f"  {r['escenario']:<35} {est:5} {bat:8} {dod:8} {col}")
        if r["estado"] == "OK":
            exitosos += 1

    print(f"\n  Exitosos    : {exitosos}/{len(ESCENARIOS)}")
    print(f"  Tiempo total: {tiempo_total/60:.1f} minutos")

    # --- Exportar JSON para el modelo probabilistico ---
    ruta_json = exportar_json(resumen_total)
    print(f"\n  JSON Markov : {ruta_json}")

    # --- Log de texto ---
    log_ruta = os.path.join(CARPETA_RESULTS, "log_simulaciones.txt")
    with open(log_ruta, 'w', encoding='utf-8') as f:
        f.write(f"Log simulaciones GMAT v2\n")
        f.write(f"Fecha inicio : {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duracion sim : {DURACION_SECS}s ({DURACION_SECS/86400:.1f} dias)\n")
        f.write(f"Total tiempo : {tiempo_total/60:.1f} min\n\n")
        for r in resumen_total:
            m = r["metricas"]
            f.write(f"{'='*50}\n")
            f.write(f"Escenario : {r['escenario']}\n")
            f.write(f"Estado    : {r['estado']}\n")
            f.write(f"Descripcion: {r['descripcion']}\n")
            f.write(f"Consumo   : {r['consumo_base_w']}W base")
            if r["consumo_tx_w"]:
                f.write(f" / {r['consumo_tx_w']}W en pase TX")
            f.write(f"\nEficiencia: {int(r['eficiencia']*100)}%\n")
            f.write(f"DeltaSol  : {r['delta_sol']:+.7f} Wh/paso\n")
            f.write(f"DeltaEcl  : {r['delta_eclipse']:+.7f} Wh/paso\n")
            f.write(f"BatMin    : {m['bateria_min']} Wh\n")
            f.write(f"DoDMax    : {m['dod_max']} Wh\n")
            if m["colapso"]:
                f.write(f"COLAPSO   : {m['tiempo_colapso']}s "
                        f"({m['tiempo_colapso']/3600:.2f}h)\n")
            else:
                f.write(f"Colapso   : No ocurrio\n")
            f.write(f"Filas CSV : {m['total_filas']}\n\n")

    print(f"  Log texto   : {log_ruta}")
    print("=" * 65)


if __name__ == "__main__":
    main()
