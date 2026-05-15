# ============================================================
# SERVICIO DE MODELO PMML
# Carga del modelo Random Forest y predicción.
# Incluye detección de Java y manejo de errores robusto.
# ============================================================

import os
import subprocess
from typing import Dict, Optional, Tuple
from app.config import PMML_PATH
from app.core.logging import get_logger

logger = get_logger(__name__)

_modelo = None
_java_path = None
_java_version = None

def _detectar_java() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Intenta detectar Java en el sistema.
    Prueba JDK 21 primero, luego JDK 26, luego JAVA_HOME genérico.
    Retorna: (encontrado, ruta_java, version_string)
    """
    candidatos = [
        r"C:\Program Files\Java\jdk-21.0.11\bin\java.exe",
        r"C:\Program Files\Java\jdk-26.0.1\bin\java.exe",
    ]
    
    # También probar con JAVA_HOME si está seteado
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidatos.insert(0, os.path.join(java_home, "bin", "java.exe"))
    
    for java_exe in candidatos:
        if os.path.exists(java_exe):
            try:
                result = subprocess.run(
                    [java_exe, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # java -version escribe en stderr
                version_line = result.stderr.strip().split("\n")[0] if result.stderr else ""
                logger.info(f"Java detectado: {java_exe} -> {version_line}")
                return True, java_exe, version_line
            except Exception as e:
                logger.warning(f"Java encontrado en {java_exe} pero no responde: {e}")
                continue
    
    logger.error("No se detectó Java en ninguna ubicación conocida")
    return False, None, None

def _configurar_java_para_pypmml(java_exe: str):
    """
    Configura las variables de entorno necesarias para que pypmml encuentre Java.
    """
    java_bin = os.path.dirname(java_exe)
    java_home = os.path.dirname(java_bin)
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = java_bin + os.pathsep + os.environ.get("PATH", "")
    logger.info(f"JAVA_HOME configurado a: {java_home}")

def cargar_modelo() -> Tuple[bool, str]:
    """
    Carga el modelo PMML usando pypmml.
    Retorna: (exitoso, mensaje)
    """
    global _modelo, _java_path, _java_version
    
    logger.info("=" * 60)
    logger.info("INICIANDO CARGA DEL MODELO PMML")
    logger.info("=" * 60)
    
    # 1. Verificar que el archivo PMML existe
    if not PMML_PATH.exists():
        logger.error(f"Archivo PMML no encontrado: {PMML_PATH}")
        return False, f"Archivo PMML no encontrado: {PMML_PATH}"
    
    logger.info(f"Archivo PMML encontrado: {PMML_PATH} ({PMML_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 2. Detectar Java
    java_ok, java_exe, version = _detectar_java()
    if not java_ok:
        logger.error("Java no está disponible. El modelo PMML no puede cargarse.")
        return False, "Java no detectado. Instale JDK 21 o 26."
    
    _java_path = java_exe
    _java_version = version
    _configurar_java_para_pypmml(java_exe)
    
    # 3. Intentar cargar pypmml
    try:
        logger.info("Importando pypmml...")
        from pypmml import Model
        logger.info("pypmml importado exitosamente")
        
        logger.info(f"Cargando modelo desde {PMML_PATH}...")
        _modelo = Model.fromFile(str(PMML_PATH))
        logger.info("MODELO PMML CARGADO EXITOSAMENTE")
        logger.info(f"Java usado: {version}")
        return True, "Modelo cargado correctamente"
        
    except ImportError as e:
        logger.error(f"No se pudo importar pypmml: {e}")
        return False, f"Librería pypmml no disponible: {e}"
    except Exception as e:
        logger.error(f"Error al cargar el modelo PMML: {e}", exc_info=True)
        return False, f"Error cargando PMML: {str(e)}"

def predecir(features: Dict[str, float]) -> Dict:
    """
    Ejecuta una predicción con el modelo PMML.
    Recibe el diccionario de features transformadas.
    Devuelve dict con predicción y probabilidades.
    """
    global _modelo
    
    if _modelo is None:
        logger.error("Intento de predicción sin modelo cargado")
        raise RuntimeError("El modelo no está cargado. Llame a cargar_modelo() primero.")
    
    logger.info("Ejecutando predicción PMML...")
    logger.debug(f"Features de entrada: {features}")
    
    try:
        resultado = _modelo.predict(features)
        logger.info(f"Resultado crudo del modelo: {resultado}")
        
        # Extraer probabilidades
        prob_normal = float(resultado.get("probability(Normal)", 0.0))
        prob_defectuosa = float(resultado.get("probability(Defectuosa)", 0.0))
        
        # Inferir predicción por mayor probabilidad (majority vote del Random Forest)
        if prob_defectuosa > prob_normal:
            prediccion = "Defectuosa"
        else:
            prediccion = "Normal"
        
        # Fallback: si existe _target en el resultado, usarlo
        if "_target" in resultado and resultado["_target"] in ("Normal", "Defectuosa"):
            prediccion = resultado["_target"]
        
        logger.info(f"Predicción: {prediccion} | Prob Normal: {prob_normal:.4f} | Prob Defectuosa: {prob_defectuosa:.4f}")
        
        return {
            "prediccion": prediccion,
            "prob_normal": prob_normal,
            "prob_defectuosa": prob_defectuosa,
        }
        
    except Exception as e:
        logger.error(f"Error durante la predicción: {e}", exc_info=True)
        raise RuntimeError(f"Error en predicción PMML: {str(e)}")

def get_modelo_estado() -> Dict:
    """Devuelve el estado actual del modelo."""
    return {
        "cargado": _modelo is not None,
        "java_path": _java_path,
        "java_version": _java_version,
    }
