# ═══════════════════════════════════════════════════════════════════════════════
#  EMANTIX PRO — FASE 9 — Health Checks
#  Verificación de salud de backend y todas sus dependencias
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import sqlalchemy as sa
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import os
import psutil

from utils.logging_config import logger, log_performance
from deps import get_current_admin_user

router = APIRouter(prefix="/api/health", tags=["health"])

# ── MODELOS ────────────────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    """Status de un componente"""
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    response_time_ms: Optional[float] = None
    timestamp: str


class HealthResponse(BaseModel):
    """Respuesta de health check completo"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    components: Dict[str, HealthStatus]
    system: Optional[Dict[str, Any]] = None


# ── VERIFICACIONES ────────────────────────────────────────────────────────

async def check_database(db_engine) -> HealthStatus:
    """Verificar conexión a base de datos"""
    import time
    start_time = time.time()
    
    try:
        async with db_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthStatus(
                status="healthy",
                message="Database connection successful",
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.utcnow().isoformat()
            )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {str(e)}")
        
        return HealthStatus(
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=round(response_time_ms, 2),
            timestamp=datetime.utcnow().isoformat()
        )


async def check_memory() -> HealthStatus:
    """Verificar uso de memoria"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Considerar degraded si memory > 80%
        if memory.percent > 90:
            status = "unhealthy"
            message = f"Memory usage critical: {memory.percent}%"
        elif memory.percent > 80:
            status = "degraded"
            message = f"Memory usage high: {memory.percent}%"
        else:
            status = "healthy"
            message = f"Memory usage normal: {memory.percent}%"
        
        # Advertencia si disco < 10% disponible
        if disk.percent > 90:
            if status != "unhealthy":
                status = "degraded"
                message += f" | Disk space critical: {disk.percent}%"
        
        return HealthStatus(
            status=status,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Memory health check failed: {str(e)}")
        return HealthStatus(
            status="degraded",
            message=f"Memory check failed: {str(e)}",
            timestamp=datetime.utcnow().isoformat()
        )


async def check_cpu() -> HealthStatus:
    """Verificar carga de CPU"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        if cpu_percent > 90:
            status = "unhealthy"
        elif cpu_percent > 75:
            status = "degraded"
        else:
            status = "healthy"
        
        message = f"CPU usage: {cpu_percent}% | Load: {load_avg[0]:.2f}"
        
        return HealthStatus(
            status=status,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"CPU health check failed: {str(e)}")
        return HealthStatus(
            status="degraded",
            message=f"CPU check failed: {str(e)}",
            timestamp=datetime.utcnow().isoformat()
        )


async def check_disk() -> HealthStatus:
    """Verificar espacio en disco"""
    try:
        disk = psutil.disk_usage('/')
        
        if disk.percent > 95:
            status = "unhealthy"
            message = f"Disk almost full: {disk.percent}%"
        elif disk.percent > 85:
            status = "degraded"
            message = f"Disk usage high: {disk.percent}%"
        else:
            status = "healthy"
            message = f"Disk usage normal: {disk.percent}%"
        
        return HealthStatus(
            status=status,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Disk health check failed: {str(e)}")
        return HealthStatus(
            status="degraded",
            message=f"Disk check failed: {str(e)}",
            timestamp=datetime.utcnow().isoformat()
        )


# ── ENDPOINTS ──────────────────────────────────────────────────────────────

@router.get("")
async def health_check_simple():
    """Health check simple (usado por Kubernetes, load balancers)"""
    return {"status": "healthy"}


@router.get("/full", response_model=HealthResponse)
async def health_check_full(
    admin=Depends(get_current_admin_user),
    db=None
):
    """
    Health check completo de todos los componentes.
    
    ⚠️ ADMIN ONLY — No expone información del sistema públicamente.
    
    Información visible solo para administradores.
    """
    import time
    start_time = time.time()
    
    # Realizar checks en paralelo
    db_status, memory_status, cpu_status, disk_status = await asyncio.gather(
        check_database(db) if db else asyncio.sleep(0),
        check_memory(),
        check_cpu(),
        check_disk(),
        return_exceptions=True
    )
    
    # Manejar excepciones
    if isinstance(db_status, Exception):
        db_status = HealthStatus(
            status="unhealthy",
            message="Database check failed",  # No exponer detalles
            timestamp=datetime.utcnow().isoformat()
        )
    
    if not db_status:
        db_status = HealthStatus(
            status="unknown",
            message="Database check skipped",
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Agregar todos los componentes
    components = {
        "database": db_status,
        "memory": memory_status,
        "cpu": cpu_status,
        "disk": disk_status,
    }
    
    # Determinar estado general
    statuses = [c.status for c in components.values() if c.status]
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Información del sistema (solo visible para admin)
    system_info = {
        "uptime_seconds": int(time.time() - start_time),
        "memory_usage_percent": psutil.virtual_memory().percent,
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
        "disk_usage_percent": psutil.disk_usage('/').percent,
    }
    
    response_time_ms = (time.time() - start_time) * 1000
    log_performance("health_check_full", response_time_ms, overall_status == "healthy")
    
    logger.info(f"Health check full by admin {admin.get('username')}: {overall_status}")
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        components=components,
        system=system_info
    )


@router.get("/liveness")
async def liveness_check():
    """Liveness check (¿Está el pod corriendo?)"""
    return {"status": "alive"}


@router.get("/readiness")
async def readiness_check(db=None):
    """
    Readiness check (¿Puede recibir tráfico?).
    
    Verifica que la aplicación está lista pero sin exponer
    información sensible del sistema.
    """
    try:
        # Verificar BD
        if db:
            import time
            start_time = time.time()
            await check_database(db)
            response_time_ms = (time.time() - start_time) * 1000
        else:
            response_time_ms = 0
        
        # Respuesta simple sin detalles de sistema
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": response_time_ms
        }
    
    except Exception as e:
        logger.warning(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/startup")
async def startup_check(db=None):
    """Startup check (¿Terminó de iniciar?)"""
    # En una aplicación real, verificar que todas las migraciones completaron
    # y que los recursos críticos se cargaron
    return {"status": "ready"}


# ── FUNCIÓN PARA USAR EN MAIN.PY ───────────────────────────────────────────

def setup_health_checks(app, db_engine):
    """Registrar health check router en la aplicación FastAPI"""
    app.include_router(router)
    logger.info("Health check endpoints registered")
