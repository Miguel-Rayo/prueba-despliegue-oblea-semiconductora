# ============================================================
# SERVICIO DE TRANSFORMACIÓN
# Pipeline idéntico al script R:
#   1. Z-score con parámetros del dataset original
#   2. One-hot encoding de process_step
#   3. Variables derivadas (sobre valores z-scoreados)
# ============================================================

import math
from typing import Dict, List
from app.config import get_params_normalizacion, VARS_NUMERICAS, ETAPAS_PROCESO
from app.core.logging import get_logger

logger = get_logger(__name__)

def aplicar_z_score(datos: Dict[str, float]) -> Dict[str, float]:
    """
    Aplica normalización z-score usando los parámetros del entrenamiento.
    Fórmula: z = (x - media) / sd
    """
    params = get_params_normalizacion()
    z_scores = {}
    logger.debug(f"Iniciando z-score para datos: {datos}")
    
    for var in VARS_NUMERICAS:
        media_key = f"{var}_media"
        sd_key = f"{var}_sd"
        media = params.get(media_key)
        sd = params.get(sd_key)
        
        if media is None or sd is None:
            logger.error(f"Parámetro de normalización faltante para {var}")
            raise ValueError(f"Parámetro de normalización faltante para {var}")
        
        if sd == 0:
            logger.warning(f"Desviación estándar cero para {var}, asignando z=0")
            z_scores[var] = 0.0
        else:
            z_scores[var] = (datos[var] - media) / sd
            logger.debug(f"  {var}: raw={datos[var]:.4f}, media={media:.4f}, sd={sd:.4f}, z={z_scores[var]:.4f}")
    
    return z_scores

def aplicar_one_hot(process_step: str) -> Dict[str, int]:
    """
    One-hot encoding de la etapa del proceso.
    Genera step_CMP, step_Deposition, etc.
    """
    if process_step not in ETAPAS_PROCESO:
        logger.error(f"Etapa inválida recibida: {process_step}")
        raise ValueError(f"Etapa inválida: {process_step}. Debe ser uno de {ETAPAS_PROCESO}")
    
    one_hot = {}
    for etapa in ETAPAS_PROCESO:
        one_hot[f"step_{etapa}"] = 1 if process_step == etapa else 0
    
    logger.debug(f"One-hot para '{process_step}': {one_hot}")
    return one_hot

def calcular_variables_derivadas(z_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Calcula variables derivadas SOBRE los valores z-scoreados.
    
    potencia_w = voltage_v_z * (current_ma_z / 1000)
    anomaly_score = abs(temp_z) + abs(pressure_z) + abs(etch_z)
    """
    potencia_w = z_scores["voltage_v"] * (z_scores["current_ma"] / 1000.0)
    anomaly_score = (
        abs(z_scores["temperature_c"]) +
        abs(z_scores["pressure_torr"]) +
        abs(z_scores["etch_rate_nm_min"])
    )
    
    derivadas = {
        "potencia_w": potencia_w,
        "anomaly_score": anomaly_score
    }
    
    logger.debug(f"Variables derivadas: potencia_w={potencia_w:.6f}, anomaly_score={anomaly_score:.4f}")
    return derivadas

def transformar_entrada(datos: Dict) -> Dict:
    """
    Pipeline completo de transformación.
    Recibe datos crudos del usuario.
    Devuelve diccionario con TODAS las features que espera el PMML.
    """
    logger.info(f"Iniciando transformación para oblea en etapa {datos.get('process_step')}")
    
    # 1. Extraer variables numéricas
    raw_numeric = {var: datos[var] for var in VARS_NUMERICAS}
    
    # 2. Z-score
    z_scores = aplicar_z_score(raw_numeric)
    
    # 3. One-hot encoding
    step_features = aplicar_one_hot(datos["process_step"])
    
    # 4. Variables derivadas (sobre z-scores)
    derivadas = calcular_variables_derivadas(z_scores)
    
    # 5. Combinar todo en el formato exacto que espera el PMML
    features = {}
    features.update(z_scores)           # temperature_c, pressure_torr, etc. (z-scoreados)
    features.update(derivadas)          # potencia_w, anomaly_score
    features.update(step_features)      # step_CMP, step_Deposition, etc.
    
    # Log de resumen de features
    logger.info(f"Transformación completada. Features generadas: {list(features.keys())}")
    logger.debug(f"Valores finales de features: {features}")
    
    return features

def generar_retroalimentacion(z_scores: Dict[str, float], prediccion: str,
                               prob_defectuosa: float) -> tuple:
    """
    Genera texto explicativo dinámico basado en los z-scores más extremos.
    Devuelve (texto_principal, lista_detalles).
    """
    logger.info(f"Generando retroalimentación para predicción={prediccion}, prob_def={prob_defectuosa:.4f}")
    
    detalles = []
    mensajes = []
    
    # Analizar cada variable numérica z-scoreada
    vars_a_analizar = [
        ("pressure_torr", "Presión del proceso", 2.0),
        ("temperature_c", "Temperatura de la cámara", 2.0),
        ("etch_rate_nm_min", "Tasa de grabado", 2.0),
        ("gas_flow_sccm", "Flujo de gas", 2.0),
        ("voltage_v", "Voltaje", 2.0),
        ("current_ma", "Corriente eléctrica", 2.0),
    ]
    
    for var_name, var_label, umbral in vars_a_analizar:
        z = z_scores.get(var_name, 0)
        abs_z = abs(z)
        
        detalles.append({
            "variable": var_name,
            "label": var_label,
            "z_score": round(z, 4),
            "desviacion_significativa": abs_z >= umbral
        })
        
        if abs_z >= umbral:
            direccion = "superior" if z > 0 else "inferior"
            mensajes.append(
                f"• **{var_label}** presenta una desviación crítica de {abs_z:.2f} desviaciones estándar "
                f"por encima del rango nominal (z={z:+.2f})."
            )
            logger.debug(f"Variable crítica detectada: {var_name} (z={z:.2f})")
    
    # Analizar anomaly_score
    anomaly = abs(z_scores.get("anomaly_score", 0))
    if anomaly >= 4.0:
        mensajes.append(
            f"• **Score de anomalía combinado** es elevado ({anomaly:.2f}), indicando múltiples "
            f"parámetros simultáneamente fuera del perfil de operación normal aprendido."
        )
    
    # Texto principal según predicción
    if prediccion == "Defectuosa":
        if mensajes:
            texto = (
                f"### Alerta de defecto detectada (confianza: {prob_defectuosa*100:.1f}%)\n\n"
                f"El modelo ha identificado que los parámetros de esta oblea exceden los límites "
                f"del comportamiento normal aprendido durante el entrenamiento con ~7,500 registros.\n\n"
                f"**Factores determinantes:**\n" + "\n".join(mensajes)
            )
        else:
            texto = (
                f"### Alerta de defecto detectada (confianza: {prob_defectuosa*100:.1f}%)\n\n"
                f"El modelo clasifica esta oblea como defectuosa basándose en la combinación "
                f"subtle de variables en el espacio multivariante, aunque ninguna variable individual "
                f"presenta una desviación extrema aislada. La frontera de decisión del Random Forest "
                f"ha detectado un patrón anómalo en la interacción entre parámetros."
            )
    else:
        texto = (
            f"### Oblea dentro de parámetros normales (confianza: {(1-prob_defectuosa)*100:.1f}%)\n\n"
            f"Todos los parámetros se encuentran dentro de los rangos de operación aprendidos por el modelo "
            f" durante el entrenamiento. La oblea no presenta señales estadísticamente significativas de falla."
        )
        if mensajes:
            texto += "\n\n**Nota:** Aunque algunas variables muestran desviaciones moderadas, no alcanzan el umbral crítico."
    
    logger.info("Retroalimentación generada exitosamente")
    return texto, detalles
