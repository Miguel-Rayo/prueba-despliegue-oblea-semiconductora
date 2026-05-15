# ============================================================
# CONFIGURACIÓN CENTRAL DEL BACKEND
# Minería de Datos — Web Service Obleas Semiconductoras
# ============================================================

import os
import json
from pathlib import Path

# Ruta base del proyecto (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Archivos de datos
PMML_PATH = DATA_DIR / "modelo_random_forest.pmml"
PARAMS_PATH = DATA_DIR / "params_normalizacion.json"
METRICAS_PATH = DATA_DIR / "metricas_rf.json"

# Verificación de existencia de archivos críticos
def verify_data_files():
    missing = []
    for name, path in [("PMML", PMML_PATH), ("Params", PARAMS_PATH), ("Metricas", METRICAS_PATH)]:
        if not path.exists():
            missing.append(name)
    return missing

# Rangos válidos para validación y frontend
RANGOS_VARIABLES = {
    "temperature_c":    {"min": 380.0, "max": 520.0, "unit": "°C",     "typical": 450.0},
    "pressure_torr":    {"min": 600.0, "max": 900.0, "unit": "Torr",   "typical": 760.0},
    "gas_flow_sccm":    {"min":  80.0, "max": 160.0, "unit": "sccm",   "typical": 115.0},
    "etch_rate_nm_min": {"min":  60.0, "max": 130.0, "unit": "nm/min", "typical":  95.0},
    "voltage_v":        {"min": 3.5,   "max": 6.5,   "unit": "V",      "typical": 5.0},
    "current_ma":       {"min":  12.0, "max":  28.0, "unit": "mA",     "typical": 20.0},
}

ETAPAS_PROCESO = ["CMP", "Deposition", "Etching", "Lithography", "Oxidation"]

VARS_NUMERICAS = ["temperature_c", "pressure_torr", "gas_flow_sccm",
                  "etch_rate_nm_min", "voltage_v", "current_ma"]

# Cargar parámetros de normalización en memoria
_params_norm = None

def get_params_normalizacion():
    global _params_norm
    if _params_norm is None:
        with open(PARAMS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # El JSON es una lista con un dict
            _params_norm = data[0] if isinstance(data, list) else data
    return _params_norm

# Cargar métricas en memoria
_metricas = None

def get_metricas():
    global _metricas
    if _metricas is None:
        with open(METRICAS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _metricas = data[0] if isinstance(data, list) else data
    return _metricas

# Importancia de variables (desde el conocimiento del modelo R)
# Los valores de importance son MeanDecreaseGini escalados del modelo entrenado en R.
IMPORTANCIA_VARIABLES = [
    {"variable": "pressure_torr",    "rank": 1,  "importance": 1227.0,
     "descripcion": "Presión del proceso",
     "explicacion": "Imagina que estás inflando un globo: si soplas muy fuerte o muy débil, la forma no queda uniforme. En la fabricación de chips, la presión dentro de la cámara controla cómo se depositan las capas. Es la variable más poderosa porque un pequeño cambio altera toda la estructura del circuito."},

    {"variable": "anomaly_score",    "rank": 2,  "importance": 680.0,
     "descripcion": "Score de anomalía combinado",
     "explicacion": "Este es como un 'termómetro grupal' que resume qué tan extraños se ven todos los parámetros juntos. Si varias mediciones se salen de lo normal al mismo tiempo, esta puntuación dispara la alerta de defecto."},

    {"variable": "etch_rate_nm_min", "rank": 3,  "importance": 205.0,
     "descripcion": "Tasa de grabado",
     "explicacion": "El grabado es como tallar madera con láser: la velocidad determina qué tan profundo y preciso queda el canal. Si va muy rápido, se come material de más; si va lento, deja residuos que estropean el chip."},

    {"variable": "temperature_c",    "rank": 4,  "importance": 166.0,
     "descripcion": "Temperatura de la cámara",
     "explicacion": "Piensa en hornear un pastel: la temperatura define si queda crudo o quemado. En semiconductores, cada material necesita una temperatura exacta para cristalizar correctamente. Unos pocos grados de diferencia pueden arruinar millones de transistores."},

    {"variable": "step_Deposition",  "rank": 5,  "importance": 53.0,
     "descripcion": "Etapa: Deposición",
     "explicacion": "La deposición es como pintar capas ultrafinas sobre la oblea. Es una de las etapas más delicadas porque cada capa debe tener el grosor exacto de unos pocos átomos para que el chip funcione."},

    {"variable": "current_ma",       "rank": 6,  "importance": 51.0,
     "descripcion": "Corriente eléctrica",
     "explicacion": "La corriente es la cantidad de electrones circulando por el equipo. Es como el caudal de agua en una tubería: si es muy alta, puede dañar componentes; si es muy baja, los procesos no se activan correctamente."},

    {"variable": "step_Lithography", "rank": 7,  "importance": 49.0,
     "descripcion": "Etapa: Litografía",
     "explicacion": "La litografía es como usar un proyector de luz para dibujar circuitos diminutos. Usa luz ultravioleta para transferir patrones. Si la temperatura o la luz varían, los dibujos salen borrosos y los chips fallan."},

    {"variable": "step_CMP",         "rank": 8,  "importance": 47.0,
     "descripcion": "Etapa: CMP",
     "explicacion": "CMP (Planarización Químico-Mecánica) es como lijar y pulir una mesa hasta dejarla perfectamente plana. En chips, la superficie debe ser tan lisa que no haya desniveles mayores que unos pocos nanómetros."},

    {"variable": "step_Oxidation",   "rank": 9,  "importance": 42.0,
     "descripcion": "Etapa: Oxidación",
     "explicacion": "La oxidación crea una capa protectora de 'cristal' sobre el silicio, similar a cómo el óxido protege el acero inoxidable. Esta capa aísla eléctricamente las partes del circuito para que no se interfieran entre sí."},

    {"variable": "voltage_v",        "rank": 10, "importance": 39.0,
     "descripcion": "Voltaje de operación",
     "explicacion": "El voltaje es la 'fuerza' que empuja a los electrones. Es como la presión del agua en una manguera: suficiente para que fluya, pero no tanta que reviente. En semiconductores, un voltaje inestable provoca cortocircuitos invisibles."},

    {"variable": "gas_flow_sccm",    "rank": 11, "importance": 34.0,
     "descripcion": "Flujo de gas",
     "explicacion": "Los gases especiales (como silano o cloro) se inyectan para depositar o grabar materiales. Es como regular el oxígeno de una soldadura: la cantidad exacta determina si la reacción es limpia o deja impurezas."},

    {"variable": "step_Etching",     "rank": 12, "importance": 32.0,
     "descripcion": "Etapa: Grabado",
     "explicacion": "El grabado elimina material con precisión atómica usando plasma o ácidos. Es como esculpir en piedra con un hilo de agua: la técnica es brutalmente precisa, y cualquier variación destruye el patrón del circuito."},

    {"variable": "potencia_w",       "rank": 13, "importance": 31.0,
     "descripcion": "Potencia eléctrica derivada",
     "explicacion": "La potencia (voltaje × corriente) indica cuánta energía total consume el proceso. Es como la potencia de una estufa: demasiada quema el material, muy poca no logra la reacción. Se calcula automáticamente del voltaje y la corriente."},
]
