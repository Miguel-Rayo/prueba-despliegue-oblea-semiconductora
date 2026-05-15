# ============================================================
# MANEJO CENTRALIZADO DE EXCEPCIONES
# ============================================================

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error en {request.url.path}: {exc.errors()}")
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        errors.append({"field": loc, "message": err.get("msg", "Error de validación")})
    return JSONResponse(
        status_code=422,
        content={
            "error": "Datos de entrada inválidos",
            "details": errors
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "message": str(exc)
        }
    )
