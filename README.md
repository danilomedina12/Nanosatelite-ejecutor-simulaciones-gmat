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