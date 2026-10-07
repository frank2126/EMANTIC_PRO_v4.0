# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Error Handling Global
#  Manejo centralizado de excepciones
# ═══════════════════════════════════════════════════════════

import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# MANEJADORES DE EXCEPCIONES ESPECÍFICAS
# ═══════════════════════════════════════════════════════════

async def handle_validation_error(request: Request, exc: RequestValidationError):
    """
    Manejar errores de validación de Pydantic.
    
    En producción: Mensaje genérico
    En desarrollo: Detalles de validación
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    # Detalles para desarrollo
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "type": error["type"],
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "type": "validation_error",
            "message": "Invalid input data",
            "details": errors
        }
    )


async def handle_database_error(request: Request, exc: SQLAlchemyError):
    """
    Manejar errores de base de datos.
    
    ⚠️ NUNCA exponer detalles de SQL o estructura de BD
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log detallado internamente
    logger.error(
        f"Database error (Request ID: {request_id})",
        exc_info=True,
        extra={"request_path": request.url.path}
    )
    
    # Tipos específicos de error de BD
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Data conflict",
                "type": "integrity_error",
                "message": "The operation violates database constraints",
                "request_id": request_id
            }
        )
    
    if isinstance(exc, NoResultFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not found",
                "type": "not_found",
                "message": "The requested resource was not found",
                "request_id": request_id
            }
        )
    
    # Error genérico de BD
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "type": "database_error",
            "message": "An unexpected database error occurred",
            "request_id": request_id
        }
    )


async def handle_generic_error(request: Request, exc: Exception):
    """
    Manejar cualquier otra excepción no capturada.
    
    Nunca exponer:
    - Stack traces
    - Código fuente
    - Estructura de la aplicación
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log completo internamente con stack trace
    logger.error(
        f"Unhandled exception (Request ID: {request_id}) on {request.url.path}",
        exc_info=True,
        extra={
            "request_path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Respuesta genérica al cliente
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "type": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )


# ═══════════════════════════════════════════════════════════
# MIDDLEWARE DE LOGGING DE REQUESTS
# ═══════════════════════════════════════════════════════════

async def logging_middleware(request: Request, call_next):
    """
    Middleware para loguear todos los requests.
    
    Registra:
    - Método y ruta
    - Status code
    - Tiempo de respuesta
    - Información de cliente
    """
    import time
    import uuid
    
    # Generar request ID único
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Registrar inicio
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    logger.debug(f"[{request_id}] → {request.method} {request.url.path}")
    
    try:
        # Ejecutar endpoint
        response = await call_next(request)
        
        # Registrar fin
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] ← {response.status_code} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
                "client_ip": client_ip
            }
        )
        
        # Agregar request ID a response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    except Exception as e:
        # Registrar excepción
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] ✗ {request.method} {request.url.path}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "process_time": f"{process_time:.3f}s",
                "client_ip": client_ip,
                "error_type": type(e).__name__
            }
        )
        
        raise


# ═══════════════════════════════════════════════════════════
# FUNCIÓN PARA REGISTRAR EN MAIN.PY
# ═══════════════════════════════════════════════════════════

def setup_exception_handlers(app: FastAPI):
    """
    Registrar todos los manejadores de excepciones en la aplicación.
    
    Debe llamarse en main.py DESPUÉS de incluir todos los routers.
    
    Ejemplo:
        app = FastAPI()
        # ... incluir routers ...
        setup_exception_handlers(app)
    """
    
    # Manejador de validación (Pydantic)
    app.add_exception_handler(
        RequestValidationError,
        handle_validation_error
    )
    
    # Manejador de errores de BD
    app.add_exception_handler(
        SQLAlchemyError,
        handle_database_error
    )
    
    # Manejador genérico (DEBE ser último)
    app.add_exception_handler(
        Exception,
        handle_generic_error
    )
    
    # Agregar middleware de logging
    app.middleware("http")(logging_middleware)
    
    logger.info("Exception handlers and logging middleware registered")


# ═══════════════════════════════════════════════════════════
# RESPUESTAS JSON CONSISTENTES
# ═══════════════════════════════════════════════════════════

"""
Formato de error consistente:

{
  "error": "Nombre del error",           # Nombre corto
  "type": "error_type",                  # Tipo para parsing
  "message": "Mensaje legible",          # Mensaje para usuario
  "request_id": "uuid",                  # Tracking
  "details": [...]                       # Solo si hay detalles
}

Ejemplos:

1. Validación:
{
  "error": "Validation error",
  "type": "validation_error",
  "message": "Invalid input data",
  "details": [
    {"field": "username", "type": "value_error", "message": "..."}
  ]
}

2. No encontrado:
{
  "error": "Not found",
  "type": "not_found",
  "message": "The requested resource was not found",
  "request_id": "uuid"
}

3. Error de BD:
{
  "error": "Data conflict",
  "type": "integrity_error",
  "message": "The operation violates database constraints",
  "request_id": "uuid"
}

4. Error interno:
{
  "error": "Internal server error",
  "type": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "uuid"
}
"""
