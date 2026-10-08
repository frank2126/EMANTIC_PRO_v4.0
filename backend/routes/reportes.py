
# Rutas de Reportes
#  CRUD  BD y caché


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import hashlib

from database import SessionLocal, ReporteDB
from deps import get_db, get_current_user, get_current_admin_user
from schemas.auth import CurrentUserResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reportes", tags=["reportes"])

# ── SCHEMAS ────────────────────────────────────────────────

class ReporteCreate(BaseModel):
    """Schema para crear reporte"""
    fecha: str
    pir: str
    unidad_funcional: str
    tecnico: str
    supervisor: str
    protocolo: str
    bus: int
    novedad: str
    tipo_novedad: str = "OK"

    class Config:
        orm_mode = True

class ReporteResponse(BaseModel):
    """Schema para respuesta de reporte"""
    id: str
    fecha: str
    pir: str
    unidad_funcional: str
    tecnico: str
    supervisor: str
    protocolo: str
    bus: int
    novedad: str
    tipo_novedad: str
    created_at: datetime
    uploaded_by: str

    class Config:
        orm_mode = True

class PaginatedReporteResponse(BaseModel):
    """Schema para respuesta paginada"""
    items: List[ReporteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ReporteStatsResponse(BaseModel):
    """Schema para estadísticas de reportes"""
    fecha: str
    tipo_novedad: str
    count: int

class ReporteResumenResponse(BaseModel):
    """Schema para resumen agregado de reportes"""
    total_reportes: int
    reportes_por_tipo: Dict[str, int]
    reportes_por_unidad: Dict[str, int]
    reportes_por_dia: List[Dict[str, Any]]

# ── CACHÉ OPTIMIZADO ───────────────────────────────────────

class ReporteCache:
    """Cache para reportes con invalidación automática"""
    def __init__(self):
        self.cache = {}
        self.ttl_seconds = 120  # Cache por 2 minutos
    
    def get_key(self, prefix: str, filters: dict) -> str:
        """Generar clave de caché"""
        filter_str = str(sorted(filters.items()))
        cache_key = f"{prefix}:{hashlib.md5(filter_str.encode()).hexdigest()}"
        return cache_key
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if (datetime.utcnow().timestamp() - timestamp) > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any):
        """Guardar valor en caché"""
        self.cache[key] = (value, datetime.utcnow().timestamp())
    
    def invalidate(self, prefix: Optional[str] = None):
        """Invalidar caché específico o todo"""
        if prefix is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self.cache[k]

reporte_cache = ReporteCache()

# ── ENDPOINTS ──────────────────────────────────────────────

@router.get("", response_model=PaginatedReporteResponse)
def list_reportes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    tipo_novedad: Optional[str] = Query(None),
    unidad_funcional: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
):
    """
    Listar reportes con paginación (OPTIMIZADO).
    
    Optimizaciones:
    - Paginación automática
    - Filtros con índices
    - Caché de resultados
    
    Query Parameters:
    - tipo_novedad: Filtrar por tipo
    - unidad_funcional: Filtrar por unidad
    - fecha_desde, fecha_hasta: Rango de fechas
    """
    
    # Construir diccionario de filtros
    filters = {
        'tipo': tipo_novedad,
        'unidad': unidad_funcional,
        'desde': fecha_desde,
        'hasta': fecha_hasta
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    
    cache_key = reporte_cache.get_key("reportes:list", filters)
    cached_result = reporte_cache.get(cache_key)
    if cached_result:
        logger.debug(f"Cache hit para {cache_key}")
        return cached_result
    
    # Construir query
    query = db.query(ReporteDB)
    
    # Aplicar filtros
    if tipo_novedad:
        query = query.filter(ReporteDB.tipo_novedad == tipo_novedad)
    if unidad_funcional:
        query = query.filter(ReporteDB.unidad_funcional == unidad_funcional)
    if fecha_desde:
        query = query.filter(ReporteDB.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(ReporteDB.fecha <= fecha_hasta)
    
    # Contar total
    total = query.count()
    
    # Paginación
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    # Ejecutar query
    items = query.order_by(ReporteDB.created_at.desc()).offset(skip).limit(page_size).all()
    
    response = PaginatedReporteResponse(
        items=[ReporteResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    reporte_cache.set(cache_key, response)
    
    return response


@router.get("/resumen", response_model=ReporteResumenResponse)
def get_resumen_reportes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
):
    """
    Obtener resumen agregado de reportes (OPTIMIZADO).
    
    Optimizaciones:
    - Agregación en BD (no en Python)
    - Índices en columnas de agrupación
    - Caché de resultados (5 minutos)
    
    Returns:
    - Total de reportes
    - Reportes por tipo
    - Reportes por unidad
    - Reportes por día
    """
    
    filters = {
        'desde': fecha_desde,
        'hasta': fecha_hasta
    }
    cache_key = reporte_cache.get_key("reportes:resumen", filters)
    cached_result = reporte_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Query base
    query = db.query(ReporteDB)
    
    if fecha_desde:
        query = query.filter(ReporteDB.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(ReporteDB.fecha <= fecha_hasta)
    
    # Total
    total = query.count()
    
    # Agregación por tipo (en BD)
    por_tipo = db.query(
        ReporteDB.tipo_novedad,
        func.count(ReporteDB.id).label("count")
    ).filter(query.whereclause)
    por_tipo_dict = {row[0]: row[1] for row in por_tipo.group_by(ReporteDB.tipo_novedad).all()}
    
    # Agregación por unidad (en BD)
    por_unidad = db.query(
        ReporteDB.unidad_funcional,
        func.count(ReporteDB.id).label("count")
    ).filter(query.whereclause)
    por_unidad_dict = {row[0]: row[1] for row in por_unidad.group_by(ReporteDB.unidad_funcional).all()}
    
    # Agregación por día (en BD)
    por_dia = db.query(
        ReporteDB.fecha,
        func.count(ReporteDB.id).label("count")
    ).filter(query.whereclause).group_by(ReporteDB.fecha).all()
    por_dia_list = [{"fecha": row[0], "count": row[1]} for row in por_dia]
    
    response = ReporteResumenResponse(
        total_reportes=total,
        reportes_por_tipo=por_tipo_dict,
        reportes_por_unidad=por_unidad_dict,
        reportes_por_dia=por_dia_list
    )
    
    reporte_cache.set(cache_key, response)
    
    return response


@router.post("", response_model=ReporteResponse)
def create_reporte(
    req: ReporteCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    """
    Crear nuevo reporte (OPTIMIZADO).
    
    Restricciones:
    - Usuarios autenticados pueden crear
    - Validación con Pydantic
    - Invalidar caché tras creación
    """
    reporte_cache.invalidate("reportes")
    
    reporte = ReporteDB(
        id=str(uuid.uuid4()),
        fecha=req.fecha,
        pir=req.pir,
        unidad_funcional=req.unidad_funcional,
        tecnico=req.tecnico,
        supervisor=req.supervisor,
        protocolo=req.protocolo,
        bus=req.bus,
        novedad=req.novedad,
        tipo_novedad=req.tipo_novedad,
        uploaded_by=current_user.username
    )
    
    db.add(reporte)
    db.commit()
    db.refresh(reporte)
    
    logger.info(f"Reporte creado: {reporte.id}")
    
    return ReporteResponse.from_orm(reporte)


@router.delete("/{reporte_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reporte(
    reporte_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Eliminar reporte (OPTIMIZADO).
    
    Restricciones:
    - Solo admin puede eliminar
    - Invalidar caché tras eliminación
    """
    reporte = db.query(ReporteDB).filter(ReporteDB.id == reporte_id).first()
    
    if not reporte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado"
        )
    
    db.delete(reporte)
    db.commit()
    
    reporte_cache.invalidate("reportes")
    
    logger.info(f"Reporte eliminado: {reporte_id}")
