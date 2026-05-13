# Nanosatelite-ejecutor-simulaciones-gmat

Herramienta para la automatización de simulaciones energéticas en GMAT (General Mission Analysis Tool) mediante Python. Este proyecto permite ejecutar matrices de escenarios paramétricos para caracterizar el comportamiento de un nanosatélite 3U.


Propósito

Esta herramienta nace con el objetivo de realizar múltiples simulaciones secuenciales en GMAT variando variables críticas (como el consumo en Watts o la eficiencia de los paneles) de forma automática, eliminando el error humano en la configuración manual de scripts.

Componentes
- Python (Automatizador)

Script de automatización por lotes que actúa como puente entre la lógica de usuario y el motor de GMAT.

    Generación Dinámica: Crea archivos .script a partir de un template base usando marcadores de posición (@@).

    Matriz de Escenarios: Parametriza modos de operación (Reposo, Nominal, Transmisión) y degradación de paneles solares (1.0 a 0.5 de eficiencia).

    Extracción de Métricas: Procesa la telemetría CSV para calcular la batería mínima, profundidad de descarga (DoD) real por eclipse y tiempo de colapso.

    Salida: Produce un resumen consolidado en formato JSON diseñado para alimentar modelos probabilísticos de recompensas de Markov.

- GMAT (Modelo de Misión)

Script de misión configurado para un CubeSat 3U en órbita heliosíncrona (SSO) a 600 km.

    Propagación: 8 días de misión (691,200 s) incluyendo arrastre atmosférico (Jacchia-Roberts) y presión de radiación solar (SRP).

    Balance de Energía: Implementación paso a paso con detección geométrica de eclipses (umbra y penumbra).

    Lógica Dinámica: Conmutación de cargas (picos de 15W/20W) durante ventanas de contacto con la estación terrestre (UNDAV).

- Script Analizador universal de Telemetría

    Este componente ha evolucionado de un script específico para GMAT a un motor de análisis multifuente. Su función es realizar una correlación cruzada entre telemetría heterogénea (datos reales de SatNOGS) y escenarios determinísticos (GMAT) para identificar estados críticos de la misión.

    El analizador utiliza una arquitectura modular basada en el Patrón Estrategia (Strategy), lo que permite procesar distintas misiones sin modificar el código núcleo, cumpliendo con el principio Abierto/Cerrado (SOLID).
    Lógica de Identificación de "Hits"

    Un "hit" se define matemáticamente como la intersección temporal de dos condiciones que estresan el subsistema de potencia (EPS): la falta de generación y la alta demanda operativa.

    ![alt text](image.png)

    Indicadores e Inferencias

    Dado que la telemetría real no siempre etiqueta los eventos, el framework aplica reglas específicas según la fuente:
    - Modo GMAT: Intersección directa entre intervalos de archivos de eventos y telemetría.
    - Modo Empírico (SatNOGS): Inferencia mediante indicadores indirectos:
        - Eclipse: Corriente de carga ≈ 0, voltaje de paneles nulo o caída térmica en arreglos solares.
        - Carga Crítica: Incremento en contadores de paquetes, picos de corriente en el bus o aumento de temperatura en el amplificador de radio (PA).
    
    Componentes del Framework
    - test_api_satnogs.py: Script de descubrimiento inicial que consulta la API de SatNOGS para localizar identificadores NORAD y verificar el estado operativo (alive/re-entered) de las misiones.
    - test_api_dashboard.py: Herramienta de inspección que consulta el esquema de InfluxDB (SHOW FIELD KEYS) para listar exhaustivamente todas las variables de telemetría disponibles para un NORAD ID específico.
    - analizador_universal.py: El motor principal "ciego" que orquesta el análisis, detecta automáticamente el tipo de satélite y genera los reportes.
    - reglas_misiones.py: El cerebro modular que contiene las estrategias específicas (umbrales, divisores y heurísticas) para cada misión (CatSat, LASARsat, RamSat, GMAT).
    - misiones_outer_join.py: Script de pre-procesamiento que unifica métricas fragmentadas de la API de SatNOGS mediante uniones externas (Outer Join).

    Características Principales
    - Agnóstico a la fuente: Procesa archivos CSV tanto de GMAT como de telemetría extendida real.
    - Escalabilidad: Permite integrar nuevas misiones en minutos mediante la creación de una nueva clase de estrategia.
    - Normalización Dinámica: Aplica factores de escala (divisores 10, 100, 1000) detectados por ingeniería inversa en los esquemas de InfluxDB.
    - Stress-Testing: Identifica patrones de "deuda energética" acumulativa tanto en modelos teóricos como en datos de vuelo.

    Productos de Salida
    Los resultados se consolidan en la carpeta resultados_analizador_universal/:
    - reporte_fvs_*.txt: Resumen ejecutivo que detalla puntos críticos, niveles de batería y validación de márgenes de seguridad.
    - detalle_hits_*.txt: Registro tipo "bisturí" con la traza temporal minuto a minuto de cada hit, facilitando la visualización de la pendiente de descarga real.

