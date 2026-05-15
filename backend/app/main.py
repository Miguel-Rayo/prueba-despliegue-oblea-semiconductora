# ============================================================
# MAIN FASTAPI APPLICATION
# Incluye middleware CORS, manejo de excepciones,
# montaje de archivos estáticos del frontend,
# y carga del modelo al inicio.
# ============================================================

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.exceptions import validation_exception_handler, generic_exception_handler
from app.core.logging import get_logger
from app.services.model_service import cargar_modelo
from app.config import verify_data_files

logger = get_logger(__name__)

# Ruta al frontend (hermano del backend)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

def create_app() -> FastAPI:
    logger.info("=" * 60)
    logger.info("INICIANDO APLICACIÓN FASTAPI")
    logger.info("=" * 60)
    
    # Verificar archivos de datos antes de arrancar
    missing = verify_data_files()
    if missing:
        logger.error(f"ARCHIVOS DE DATOS FALTANTES: {missing}")
    else:
        logger.info("Todos los archivos de datos están presentes")
    
    app = FastAPI(
        title="API Predicción Obleas Semiconductoras",
        description=(
            "Servicio de predicción de defectos en obleas semiconductoras "
            "basado en un modelo Random Forest entrenado con ~7,500 registros "
            "y exportado a PMML desde R."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Middleware CORS (permisivo para desarrollo local)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Manejadores de excepciones
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Incluir rutas API bajo /api
    app.include_router(router, prefix="/api")
    
    # Montar frontend estático si existe
    if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
        logger.info(f"Montando archivos estáticos desde: {FRONTEND_DIR}")
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    else:
        logger.warning(f"Frontend no encontrado en {FRONTEND_DIR}. Solo API disponible.")

    # Precarga síncrona del modelo ANTES de exponer la app al mundo.
    # Esto evita que Render reciba "modelo no cargado" durante healthchecks
    # tempranos o peticiones iniciales tras un cold start.
    logger.info("PRECARGA SINCRONA: Cargando modelo PMML...")
    ok, msg = cargar_modelo()
    if ok:
        logger.info(f"PRECARGA EXITOSA: {msg}")
    else:
        logger.error(f"PRECARGA FALLIDA: {msg}")
        logger.error("El endpoint /predecir NO estará disponible hasta que se resuelva el problema con Java/PMML.")

    return app

app = create_app()
