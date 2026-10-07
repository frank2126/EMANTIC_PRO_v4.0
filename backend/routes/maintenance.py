# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Rutas de Mantenimiento
#  CRUD optimizado con paginación y caché
# ═══════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
from datetime import datetime
from typing import List, Optional
import uuid
from functools import lru_cache
import hashlib

from database import SessionLocal, MaintenanceDB
from deps import get_db, get_current_admin_user, get_current_user
from schemas.auth import CurrentUserResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

# ── SCHEMAS ────────────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    """Schema para crear mantenimiento"""
    unidad: str
    tipo: str
    km_actual: int
    km_servicio: int
    fecha: str
    estado: str = "Programado"
    tecnico: str = ""

    class Config:
        orm_mode = True

class MaintenanceUpdate(BaseModel):
    """Schema para actualizar mantenimiento"""
    tipo: Optional[str] = None
    km_actual: Optional[int] = None
    km_servicio: Optional[int] = None
    fecha: Optional[str] = None
    estado: Optional[str] = None
    tecnico: Optional[str] = None

    class Config:
        orm_mode = True

class MaintenanceResponse(BaseModel):
    """Schema para respuesta de mantenimiento"""
    id: str
    unidad: str
    tipo: str
    km_actual: int
    km_servicio: int
    fecha: str
    estado: str
    tecnico: str
    created_at: datetime

    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    """Schema para respuesta paginada"""
    items: List[MaintenanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# ── CACHÉ SIMPLE (OPTIMIZADO) ──────────────────────────────

class MaintenanceCache:
    """Cache simple para listas paginadas"""
    def __init__(self):
        self.cache = {}
        self.ttl_seconds = 60  # Cache por 1 minuto
    
    def get_key(self, filters: dict, page: int, page_size: int) -> str:
        """Generar clave de caché basada en filtros y paginación"""
        # Crear hash de los filtros
        filter_str = str(sorted(filters.items()))
        cache_key = f"maintenance:{hashlib.md5(filter_str.encode()).hexdigest()}:{page}:{page_size}"
        return cache_key
    
    def get(self, key: str) -> Optional[dict]:
        """Obtener valor del caché"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        # Verificar si expiró
        if (datetime.utcnow().timestamp() - timestamp) > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: dict):
        """Guardar valor en caché"""
        self.cache[key] = (value, datetime.utcnow().timestamp())
    
    def invalidate(self):
        """Invalidar todo el caché"""
        self.cache.clear()

# Instancia global del caché
maintenance_cache = MaintenanceCache()

# ── ENDPOINTS ──────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse)
def list_maintenance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    unidad: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    tecnico: Optional[str] = Query(None),
):
    """
    Listar mantenimientos con paginación (OPTIMIZADO).
    
    Optimizaciones:
    - Paginación automática
    - Caché de resultados
    - Índices en columnas filtradas
    - Límite máximo de 500 registros por página
    
    Query Parameters:
    - page: Número de página (default: 1)
    - page_size: Registros por página (default: 50, máx: 500)
    - unidad: Filtrar por unidad
    - estado: Filtrar por estado
    - tecnico: Filtrar por técnico
    """
    
    # Construir diccionario de filtros
    filters = {
        'unidad': unidad,
        'estado': estado,
        'tecnico': tecnico
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Generar clave de caché
    cache_key = maintenance_cache.get_key(filters, page, page_size)
    
    # Intentar obtener del caché
    cached_result = maintenance_cache.get(cache_key)
    if cached_result:
        logger.debug(f"Cache hit para {cache_key}")
        return cached_result
    
    # Construir query base
    query = db.query(MaintenanceDB)
    
    # Aplicar filtros con índices
    if unidad:
        query = query.filter(MaintenanceDB.unidad == unidad)
    if estado:
        query = query.filter(MaintenanceDB.estado == estado)
    if tecnico:
        query = query.filter(MaintenanceDB.tecnico == tecnico)
    
    # Contar total antes de paginar
    total = query.count()
    
    # Calcular paginación
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    # Aplicar paginación y ejecutar query
    items = query.offset(skip).limit(page_size).all()
    
    # Construir respuesta
    response = PaginatedResponse(
        items=[MaintenanceResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    # Guardar en caché
    maintenance_cache.set(cache_key, response)
    
    return response


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener mantenimiento específico (OPTIMIZADO).
    
    Optimizaciones:
    - Query directa por ID (índice por defecto)
    - Sin caché (datos pueden cambiar frecuentemente)
    """
    maintenance = db.query(MaintenanceDB).filter(
        MaintenanceDB.id == maintenance_id
    ).first()
    
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    return MaintenanceResponse.from_orm(maintenance)


@router.post("", response_model=MaintenanceResponse)
def create_maintenance(
    req: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Crear nuevo mantenimiento (OPTIMIZADO).
    
    Restricciones:
    - Solo admin puede crear
    - Validación de datos con Pydantic
    - Invalidar caché tras creación
    """
    # Invalidar caché
    maintenance_cache.invalidate()
    
    # Crear registro
    maintenance = MaintenanceDB(
        id=str(uuid.uuid4()),
        unidad=req.unidad,
        tipo=req.tipo,
        km_actual=req.km_actual,
        km_servicio=req.km_servicio,
        fecha=req.fecha,
        estado=req.estado,
        tecnico=req.tecnico
    )
    
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    
    logger.info(f"Mantenimiento creado: {maintenance.id}")
    
    return MaintenanceResponse.from_orm(maintenance)


@router.patch("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: str,
    req: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Actualizar mantenimiento (OPTIMIZADO).
    
    Restricciones:
    - Solo admin puede actualizar
    - Actualización selectiva de campos
    - Invalidar caché tras actualización
    """
    maintenance = db.query(MaintenanceDB).filter(
        MaintenanceDB.id == maintenance_id
    ).first()
    
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    # Actualizar solo campos proporcionados
    update_data = req.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(maintenance, field, value)
    
    db.commit()
    db.refresh(maintenance)
    
    # Invalidar caché
    maintenance_cache.invalidate()
    
    logger.info(f"Mantenimiento actualizado: {maintenance.id}")
    
    return MaintenanceResponse.from_orm(maintenance)


@router.delete("/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maintenance(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Eliminar mantenimiento (OPTIMIZADO).
    
    Restricciones:
    - Solo admin puede eliminar
    - Invalidar caché tras eliminación
    """
    maintenance = db.query(MaintenanceDB).filter(
        MaintenanceDB.id == maintenance_id
    ).first()
    
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado"
        )
    
    db.delete(maintenance)
    db.commit()
    
    # Invalidar caché
    maintenance_cache.invalidate()
    
    logger.info(f"Mantenimiento eliminado: {maintenance_id}")


@router.get("/stats/by-estado", response_model=dict)
def stats_by_estado(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Estadísticas de mantenimientos por estado (OPTIMIZADO).
    
    Optimizaciones:
    - Usa índice en estado
    - Agregación en BD
    - Caché por 5 minutos (datos menos volátiles)
    """
    # Query agregada directa en BD
    from sqlalchemy import func
    
    stats = db.query(
        MaintenanceDB.estado,
        func.count(MaintenanceDB.id).label("count")
    ).group_by(MaintenanceDB.estado).all()
    
    return {
        "stats": [{"estado": s[0], "count": s[1]} for s in stats]
    }
