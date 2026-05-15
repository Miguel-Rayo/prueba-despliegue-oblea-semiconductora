# ============================================================
# MODELOS PYDANTIC — VALIDACIÓN ESTRICTA DE ENTRADAS/SALIDAS
# Pydantic v1 compatible con Python 3.14
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from app.config import ETAPAS_PROCESO, RANGOS_VARIABLES

class PrediccionRequest(BaseModel):
    """Datos crudos de entrada del usuario."""
    temperature_c:    float = Field(..., ge=380, le=520, description="Temperatura de la cámara (°C)")
    pressure_torr:    float = Field(..., ge=600, le=900, description="Presión del proceso (Torr)")
    gas_flow_sccm:    float = Field(..., ge=80,  le=160, description="Flujo de gas (sccm)")
    etch_rate_nm_min: float = Field(..., ge=60,  le=130, description="Tasa de grabado (nm/min)")
    voltage_v:        float = Field(..., ge=3.5, le=6.5,  description="Voltaje (V)")
    current_ma:       float = Field(..., ge=12,  le=28,  description="Corriente (mA)")
    process_step:     str   = Field(..., description="Etapa del proceso")

    @validator('process_step')
    def validate_process_step(cls, v):
        if v not in ETAPAS_PROCESO:
            raise ValueError(f"process_step debe ser uno de: {', '.join(ETAPAS_PROCESO)}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "temperature_c":    460.5,
                "pressure_torr":    690.0,
                "gas_flow_sccm":    115.0,
                "etch_rate_nm_min":  98.5,
                "voltage_v":          5.1,
                "current_ma":        20.3,
                "process_step":   "Etching"
            }
        }

class ZScoreBreakdown(BaseModel):
    temperature_c:    float
    pressure_torr:    float
    gas_flow_sccm:    float
    etch_rate_nm_min: float
    voltage_v:        float
    current_ma:       float
    potencia_w:       float
    anomaly_score:    float

class PrediccionResponse(BaseModel):
    """Respuesta completa del modelo con retroalimentación."""
    prediccion:       str
    es_defectuosa:    bool
    probabilidad:     float
    prob_defectuosa:  float
    prob_normal:      float
    z_scores:         Dict[str, float]
    retroalimentacion: str
    detalle_variables: List[Dict]

class HealthResponse(BaseModel):
    status:        str
    modelo_cargado: bool
    java_disponible: bool
    java_version:  Optional[str]
    mensaje:       str

class MetricasResponse(BaseModel):
    modelo:        str
    accuracy:      float
    precision:     float
    sensibilidad:  float
    f1_score:      float
    mae:           float
    auc:           float
    n_registros_train: int
    n_features:    int

class RangosResponse(BaseModel):
    variables: Dict
    etapas:    List[str]
