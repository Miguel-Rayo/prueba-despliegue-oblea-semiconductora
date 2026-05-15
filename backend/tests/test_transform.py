# ============================================================
# TESTS UNITARIOS — PIPELINE DE TRANSFORMACIÓN
# Valida que la transformación numérica sea correcta.
# ============================================================

import sys
from pathlib import Path

# Agregar app al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.transform import aplicar_z_score, calcular_variables_derivadas, transformar_entrada
from config import get_params_normalizacion

def test_z_score():
    params = get_params_normalizacion()
    # Usar un valor típico: media exacta debería dar z=0
    datos = {
        "temperature_c": params["temperature_c_media"],
        "pressure_torr": params["pressure_torr_media"],
        "gas_flow_sccm": params["gas_flow_sccm_media"],
        "etch_rate_nm_min": params["etch_rate_nm_min_media"],
        "voltage_v": params["voltage_v_media"],
        "current_ma": params["current_ma_media"],
    }
    z = aplicar_z_score(datos)
    for var, val in z.items():
        assert abs(val) < 1e-6, f"Z-score de {var} debería ser ~0, got {val}"
    print("[PASS] test_z_score: medias dan z=0")

def test_z_score_una_sd():
    params = get_params_normalizacion()
    datos = {
        "temperature_c": params["temperature_c_media"] + params["temperature_c_sd"],
        "pressure_torr": params["pressure_torr_media"] + params["pressure_torr_sd"],
        "gas_flow_sccm": params["gas_flow_sccm_media"] + params["gas_flow_sccm_sd"],
        "etch_rate_nm_min": params["etch_rate_nm_min_media"] + params["etch_rate_nm_min_sd"],
        "voltage_v": params["voltage_v_media"] + params["voltage_v_sd"],
        "current_ma": params["current_ma_media"] + params["current_ma_sd"],
    }
    z = aplicar_z_score(datos)
    for var, val in z.items():
        assert abs(val - 1.0) < 1e-6, f"Z-score de {var} debería ser ~1, got {val}"
    print("[PASS] test_z_score_una_sd: media+sd dan z=1")

def test_transformar_entrada():
    datos = {
        "temperature_c": 450.4123,
        "pressure_torr": 758.3465,
        "gas_flow_sccm": 120.0585,
        "etch_rate_nm_min": 95.3956,
        "voltage_v": 4.9955,
        "current_ma": 19.9927,
        "process_step": "Etching"
    }
    features = transformar_entrada(datos)
    
    # Verificar que todas las claves esperadas están presentes
    expected_keys = [
        "temperature_c", "pressure_torr", "gas_flow_sccm", "etch_rate_nm_min",
        "voltage_v", "current_ma", "potencia_w", "anomaly_score",
        "step_CMP", "step_Deposition", "step_Etching", "step_Lithography", "step_Oxidation"
    ]
    for key in expected_keys:
        assert key in features, f"Falta feature: {key}"
    
    # Verificar one-hot
    assert features["step_Etching"] == 1
    assert features["step_CMP"] == 0
    assert features["step_Deposition"] == 0
    
    print("[PASS] test_transformar_entrada: features completas y one-hot correcto")

if __name__ == "__main__":
    print("Ejecutando tests de transformación...")
    test_z_score()
    test_z_score_una_sd()
    test_transformar_entrada()
    print("\n[TODOS LOS TESTS PASARON]")
