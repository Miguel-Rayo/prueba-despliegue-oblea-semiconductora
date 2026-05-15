# ============================================================
# ENDPOINTS API
# Todos con logging frecuente para trazabilidad
# ============================================================

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    PrediccionRequest, PrediccionResponse, HealthResponse,
    MetricasResponse, RangosResponse
)
from app.services.transform import transformar_entrada, generar_retroalimentacion
from app.services.model_service import predecir, get_modelo_estado, cargar_modelo
from app.config import (
    RANGOS_VARIABLES, ETAPAS_PROCESO, get_metricas,
    IMPORTANCIA_VARIABLES
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=dict)
def root():
    logger.info("GET / - Solicitud de bienvenida")
    return {
        "mensaje": "API Predicción Obleas Semiconductoras — activa",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": ["/health", "/rangos", "/metricas", "/predecir"]
    }

@router.get("/health", response_model=HealthResponse)
def health_check():
    logger.info("GET /health - Verificando estado del sistema...")
    estado = get_modelo_estado()
    
    java_ok = estado["java_path"] is not None
    modelo_ok = estado["cargado"]
    
    if modelo_ok and java_ok:
        status = "ok"
        mensaje = "Sistema operativo. Modelo PMML cargado y Java disponible."
    elif not modelo_ok and java_ok:
        status = "degraded"
        mensaje = "Java disponible pero modelo no cargado."
    else:
        status = "error"
        mensaje = "Java no detectado. El servicio de predicción no está disponible."
    
    logger.info(f"Health status: {status} | modelo={modelo_ok} | java={java_ok}")
    return HealthResponse(
        status=status,
        modelo_cargado=modelo_ok,
        java_disponible=java_ok,
        java_version=estado.get("java_version"),
        mensaje=mensaje
    )

@router.get("/rangos", response_model=RangosResponse)
def rangos():
    logger.info("GET /rangos - Devolviendo rangos de variables")
    return RangosResponse(
        variables=RANGOS_VARIABLES,
        etapas=ETAPAS_PROCESO
    )

@router.get("/metricas", response_model=MetricasResponse)
def metricas():
    logger.info("GET /metricas - Devolviendo métricas del modelo")
    m = get_metricas()
    return MetricasResponse(
        modelo=m.get("modelo", "Random Forest"),
        accuracy=m.get("accuracy", 0.0),
        precision=m.get("precision", 0.0),
        sensibilidad=m.get("sensibilidad", 0.0),
        f1_score=m.get("f1_score", 0.0),
        mae=m.get("mae", 0.0),
        auc=m.get("auc", 0.0),
        n_registros_train=7500,
        n_features=13
    )

@router.get("/importancia", response_model=list)
def importancia():
    logger.info("GET /importancia - Devolviendo ranking de variables")
    return IMPORTANCIA_VARIABLES

@router.post("/predecir", response_model=PrediccionResponse)
def predecir_endpoint(oblea: PrediccionRequest):
    logger.info("=" * 60)
    logger.info("POST /predecir - Nueva solicitud de predicción")
    logger.info(f"Datos recibidos: temp={oblea.temperature_c}, pressure={oblea.pressure_torr}, step={oblea.process_step}")
    
    # Verificar que el modelo está cargado
    estado = get_modelo_estado()
    if not estado["cargado"]:
        logger.error("Predicción rechazada: modelo no cargado")
        raise HTTPException(status_code=503, detail="El modelo no está disponible. Verifique /health.")
    
    try:
        # 1. Transformar datos
        datos_crudos = oblea.dict()
        features = transformar_entrada(datos_crudos)
        
        # 2. Predecir
        resultado_modelo = predecir(features)
        
        prediccion = resultado_modelo["prediccion"]
        prob_def = resultado_modelo["prob_defectuosa"]
        prob_norm = resultado_modelo["prob_normal"]
        es_defectuosa = prediccion == "Defectuosa"
        
        logger.info(f"Resultado modelo: {prediccion} (defectuosa={es_defectuosa})")
        
        # 3. Preparar z-scores para respuesta
        z_scores_respuesta = {
            "temperature_c":    round(features["temperature_c"], 4),
            "pressure_torr":    round(features["pressure_torr"], 4),
            "gas_flow_sccm":    round(features["gas_flow_sccm"], 4),
            "etch_rate_nm_min": round(features["etch_rate_nm_min"], 4),
            "voltage_v":        round(features["voltage_v"], 4),
            "current_ma":       round(features["current_ma"], 4),
            "potencia_w":       round(features["potencia_w"], 6),
            "anomaly_score":    round(features["anomaly_score"], 4),
        }
        
        # 4. Generar retroalimentación
        retro, detalles = generar_retroalimentacion(
            z_scores_respuesta, prediccion, prob_def
        )
        
        response = PrediccionResponse(
            prediccion=prediccion,
            es_defectuosa=es_defectuosa,
            probabilidad=round(float(prob_def if es_defectuosa else prob_norm), 4),
            prob_defectuosa=round(float(prob_def), 4),
            prob_normal=round(float(prob_norm), 4),
            z_scores=z_scores_respuesta,
            retroalimentacion=retro,
            detalle_variables=detalles
        )
        
        logger.info("POST /predecir completado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en /predecir: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno en predicción: {str(e)}")
