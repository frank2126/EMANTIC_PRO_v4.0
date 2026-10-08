#  Arquitectura modular y segura

from fastapi import FastAPI, HTTPException, status

from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.trustedhost import TrustedHostMiddleware

from fastapi.responses import JSONResponse

import logging

import sys

from datetime import datetime
 
# Configuración

from config import settings

from database import init_db
 
# Rutas (routes)

from routes.auth import router as auth_router

from routes.users import router as users_router

from routes.maintenance import router as maintenance_router

from routes.reportes import router as reportes_router

from routes.excel import router as excel_router

from routes.manuals import router as manuals_router

from routes.health import router as health_router

from routes.datos import router as datos_router
 
# Error handling

from utils.error_handler import setup_exception_handlers
 
# Configurar logging

logging.basicConfig(

    level=settings.log_level,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

    handlers=[

        logging.StreamHandler(sys.stdout),

    ]

)

logger = logging.getLogger(__name__)
 
# ── CREAR APP ──────────────────────────────────────────

app = FastAPI(

    title="EMANTIX PRO API",

    description="Sistema de Gestión Técnica Centralizado",

    version=settings.app_version,

    docs_url="/docs" if settings.debug else None,

    redoc_url="/redoc" if settings.debug else None,

    openapi_url="/openapi.json" if settings.debug else None,

)
 
 
# ── MIDDLEWARES DE SEGURIDAD ───────────────────────────
 
cors_origins = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]
 
app.add_middleware(

    CORSMiddleware,

    allow_origins=cors_origins,

    allow_credentials=True,

    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],

    allow_headers=["Content-Type", "Authorization"],

    max_age=3600,

)
 
if not settings.debug:

    app.add_middleware(

        TrustedHostMiddleware,

        allowed_hosts=cors_origins + ["localhost", "127.0.0.1"]

    )
 
logger.info("✅ Middlewares de seguridad configurados")
 
 
# ── MANEJO GLOBAL DE ERRORES ───────────────────────────

# Los manejadores se registran al final, después de incluir todos los routers

# Ver setup_exception_handlers() al final del archivo
 
 
# ── EVENTOS ────────────────────────────────────────────
 
@app.on_event("startup")

async def startup_event():

    """Inicializaciones al iniciar"""

    logger.info("=" * 60)

    logger.info(" EMANTIX PRO API - Iniciando")

    logger.info("=" * 60)

    try:

        settings.validate_settings()

    except Exception as e:

        logger.error(f"❌ Error de configuración: {str(e)}")

        raise

    try:

        init_db()

        logger.info("✅ Base de datos inicializada")

    except Exception as e:

        logger.error(f"❌ Error BD: {str(e)}")

        raise

    logger.info(f" Versión: {settings.app_version}")

    logger.info(f" Debug: {settings.debug}")

    logger.info("✅ Aplicación lista")

    logger.info("=" * 60)
 
 
@app.on_event("shutdown")

async def shutdown_event():

    """Apagar limpiamente"""

    logger.info("🛑 EMANTIX PRO API - Apagando")
 
 
# ── RUTAS ──────────────────────────────────────────────
 
@app.get("/health")

def health_check():

    """Health check endpoint"""

    return {

        "status": "healthy",

        "timestamp": datetime.utcnow().isoformat(),

        "version": settings.app_version

    }
 
@app.get("/")

def root():

    """Información de la API"""

    return {

        "name": "EMANTIX PRO API",

        "version": settings.app_version,

        "status": "running",

        "docs": "/docs" if settings.debug else "N/A"

    }
 
app.include_router(auth_router)

app.include_router(users_router)

app.include_router(maintenance_router)

app.include_router(reportes_router)

app.include_router(excel_router)

app.include_router(manuals_router)

app.include_router(health_router)

app.include_router(datos_router)  # /api/dpv, /api/ico, /api/disponibilidad, /api/dpv-mensual, /api/cargas
 
logger.info("✅ Rutas registradas: auth, users, maintenance, reportes, excel, manuals, health, datos")
 
# ── REGISTRAR MANEJADORES DE EXCEPCIONES ────────────────

# Debe ser después de incluir todos los routers

setup_exception_handlers(app)

logger.info("✅ Manejadores de excepciones registrados")
 
 
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "main:app",

        host="127.0.0.1",

        port=8000,

        reload=settings.debug,

        log_level=settings.log_level.lower(),

    )
 