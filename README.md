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

- Script analizador de datos

    El script realiza una correlación cruzada entre múltiples fuentes de datos independientes para identificar estados críticos de la misión donde la generación solar es nula y la demanda energética es máxima. Su objetivo es extraer patrones de comportamiento que validen la resiliencia del nanosatélite ante fallos de actitud o degradación de paneles.

    El analizador utiliza una lógica de conjuntos para identificar "Hits" (puntos críticos de muestreo). Un hit se define matemáticamente como la intersección temporal de dos condiciones estresantes para el subsistema de potencia (EPS). 
    
    ![alt text](image.png)

    Factores Determinantes:
    - Falta de entrada: Corriente de paneles solares en 0 (Umbra/Penumbra).  
    - Alta demanda: Picos de consumo (15W/20W) por transmisión activa hacia la estación terrestre (UNDAV).

    Características Principales
    - Discretización de Tiempo: Convierte intervalos de eventos de GMAT y telemetría de estado en objetos datetime de alta precisión para su cruce lógico.  
    - Análisis de 13 Escenarios: Procesa de forma masiva los datos de la matriz de sensibilidad (variaciones de eficiencia del 50% al 100% y modos de 3W a 20W).  
    - Agnóstico al Volumen: Diseñado para escalar a cientos de simulaciones, permitiendo realizar stress-testing del modelo probabilístico.  
    - Detección de Degradación: Identifica patrones de "deuda energética" acumulativa u "efecto memoria" entre jornadas de simulación.

    Devuelve dos archivos en su salida: 
    - reporte_fvs.txt: Un resumen ejecutivo por escenario que detalla puntos críticos, niveles de batería inicial/final y estado de seguridad del umbral (32 Wh). 
    - detalle_hits_fvs.txt: Un registro tipo "bisturí" con la traza temporal minuto a minuto de cada hit, facilitando la visualización de la pendiente de descarga y la identificación de clústeres de pases nocturnos.


