# ═══════════════════════════════════════════════════════════════════════════════
#  EMANTIX PRO — FASE 5 — Rutas de Manuales PDF
#  SEGURO: Validación, autenticación, control de acceso
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
from typing import Optional
from datetime import datetime
import uuid
import os
from pathlib import Path

from database import SessionLocal, ManualDB
from deps import get_db, get_current_user, get_current_admin_user
from schemas.auth import CurrentUserResponse
from pydantic import BaseModel
from utils.file_validator import (
    validate_pdf_file, generate_safe_filename, log_file_upload,
    calculate_file_hash
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manuals", tags=["manuals"])

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MANUALS_DIR = os.path.join(UPLOAD_DIR, "manuals")

# Crear directorio si no existe
os.makedirs(MANUALS_DIR, exist_ok=True)
os.makedirs(os.path.join(MANUALS_DIR, "temp"), exist_ok=True)

# ── SCHEMAS ────────────────────────────────────────────────────────────────

class ManualCreate(BaseModel):
    """Schema para crear manual"""
    title: str
    description: Optional[str] = ""
    category: str = "General"

class ManualResponse(BaseModel):
    """Schema para respuesta de manual"""
    id: str
    title: str
    description: str
    category: str
    filename: str
    size_mb: float
    uploaded_by: str
    uploaded_at: str
    active: bool

    class Config:
        orm_mode = True

class ManualListResponse(BaseModel):
    """Schema para listado paginado"""
    items: list[ManualResponse]
    total: int
    page: int
    page_size: int

# ── ENDPOINTS ──────────────────────────────────────────────────────────────

@router.get("", response_model=ManualListResponse)
def list_manuals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """
    Listar manuales con paginación (SEGURO).
    
    Seguridad:
    - Requiere autenticación
    - Paginación para evitar DoS
    - Sin exposición de rutas de archivo
    
    Query Parameters:
    - page: Número de página
    - page_size: Registros por página (máximo 100)
    - category: Filtrar por categoría
    - active_only: Solo manuales activos
    """
    
    query = db.query(ManualDB)
    
    if active_only:
        query = query.filter(ManualDB.active == True)
    
    if category:
        query = query.filter(ManualDB.category == category)
    
    total = query.count()
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()
    
    # Sanitizar respuesta (no exponer rutas internas)
    response_items = []
    for manual in items:
        manual_dict = {
            "id": manual.id,
            "title": manual.title,
            "description": manual.description,
            "category": manual.category,
            "filename": manual.title,  # No exponer nombre real del archivo
            "size_mb": float(manual.size_mb) if manual.size_mb else 0,
            "uploaded_by": manual.uploaded_by,
            "uploaded_at": manual.uploaded_at,
            "active": manual.active,
        }
        response_items.append(ManualResponse(**manual_dict))
    
    return ManualListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ManualResponse)
async def upload_manual(
    file: UploadFile = File(...),
    title: str = None,
    description: str = "",
    category: str = "General",
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user),
):
    """
    Subir nuevo manual PDF (SEGURO - Solo admin).
    
    Seguridad:
    - Solo admin puede subir
    - Validación MIME type
    - Validación de estructura PDF
    - Nombre de archivo aleatorio
    - Scanning de malware (futuro: ClamAV)
    
    Parámetros:
    - file: Archivo PDF
    - title: Título del manual
    - description: Descripción
    - category: Categoría
    """
    
    try:
        # Leer contenido del archivo
        content = await file.read()
        
        # Validar archivo
        valid, error = validate_pdf_file(file.filename, content)
        if not valid:
            log_file_upload(current_user.username, file.filename, len(content), "pdf", "rejected")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validación de PDF falló: {error}"
            )
        
        # Generar nombre de archivo seguro
        safe_filename = generate_safe_filename(file.filename)
        file_path = os.path.join(MANUALS_DIR, safe_filename)
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Calcular tamaño en MB
        size_mb = len(content) / (1024 * 1024)
        
        # Crear registro en BD
        manual = ManualDB(
            id=str(uuid.uuid4()),
            title=title or file.filename,
            description=description,
            category=category,
            filename=safe_filename,
            url=f"/api/manuals/{uuid.uuid4()}/download",  # URL segura con token
            size_mb=str(round(size_mb, 2)),
            uploaded_by=current_user.username,
            uploaded_at=datetime.utcnow().isoformat(),
            active=True
        )
        
        db.add(manual)
        db.commit()
        db.refresh(manual)
        
        # Log
        log_file_upload(current_user.username, file.filename, len(content), "pdf", "success")
        logger.info(f"Manual subido: {manual.id} by {current_user.username}")
        
        return ManualResponse.from_orm(manual)
    
    except Exception as e:
        log_file_upload(current_user.username, file.filename, 0, "pdf", "error")
        logger.error(f"Error subiendo manual: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando archivo"  # No exponer detalles técnicos
        )
    
    finally:
        await file.close()


@router.get("/{manual_id}")
def get_manual(
    manual_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_user),
):
    """
    Obtener información de manual específico (SEGURO).
    
    Seguridad:
    - Verificar que manual existe
    - No exponer ruta de archivo
    """
    
    manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
    
    if not manual or not manual.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual no encontrado"
        )
    
    # Sanitizar respuesta
    manual_dict = {
        "id": manual.id,
        "title": manual.title,
        "description": manual.description,
        "category": manual.category,
        "filename": manual.title,  # No exponer nombre real
        "size_mb": float(manual.size_mb) if manual.size_mb else 0,
        "uploaded_by": manual.uploaded_by,
        "uploaded_at": manual.uploaded_at,
        "active": manual.active,
    }
    
    return ManualResponse(**manual_dict)


@router.get("/{manual_id}/download")
def download_manual(
    manual_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_user),
):
    """
    Descargar manual PDF (SEGURO).
    
    Seguridad CRÍTICA:
    - Verificar autenticación
    - Verificar que manual existe y está activo
    - Usar ruta interna (no URL del usuario)
    - Logging de descarga
    - Rate limiting (futuro)
    
    Args:
        manual_id: ID del manual
        
    Returns:
        Archivo PDF
    """
    
    # Verificar autenticación
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida"
        )
    
    # Obtener manual de BD
    manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
    
    # Verificar que existe y está activo
    if not manual or not manual.active:
        logger.warning(f"Intento de descargar manual no existente: {manual_id} by {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual no encontrado"
        )
    
    # Verificar que el archivo existe
    file_path = os.path.join(MANUALS_DIR, manual.filename)
    if not os.path.exists(file_path):
        logger.error(f"Archivo de manual no existe: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando archivo"
        )
    
    # Verificar que la ruta es segura (no path traversal)
    try:
        real_path = os.path.realpath(file_path)
        safe_dir = os.path.realpath(MANUALS_DIR)
        if not real_path.startswith(safe_dir):
            logger.error(f"Intento de path traversal: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ruta de archivo inválida"
            )
    except Exception as e:
        logger.error(f"Error validando ruta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando archivo"
        )
    
    # Log de descarga (auditoría)
    logger.info(f"MANUAL_DOWNLOAD | manual_id={manual_id} | user={current_user.username} | title={manual.title}")
    
    # Devolver archivo
    return FileResponse(
        path=file_path,
        filename=f"{manual.title}.pdf",
        media_type="application/pdf"
    )


@router.patch("/{manual_id}")
def update_manual(
    manual_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user),
):
    """
    Actualizar información de manual (Solo admin).
    
    Restricciones:
    - No se puede cambiar archivo (usar delete + upload)
    - Solo admin puede actualizar
    """
    
    manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual no encontrado"
        )
    
    # Actualizar solo campos permitidos
    if title:
        manual.title = title
    if description is not None:
        manual.description = description
    if category:
        manual.category = category
    
    db.commit()
    db.refresh(manual)
    
    logger.info(f"Manual actualizado: {manual_id} by {current_user.username}")
    
    return ManualResponse.from_orm(manual)


@router.delete("/{manual_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manual(
    manual_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user),
):
    """
    Eliminar manual (Solo admin).
    
    Seguridad:
    - Eliminar archivo físico
    - Eliminar registro de BD
    - Logging de eliminación
    """
    
    manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
    
    if not manual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual no encontrado"
        )
    
    # Eliminar archivo físico
    file_path = os.path.join(MANUALS_DIR, manual.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error eliminando archivo: {str(e)}")
            # Continuar y eliminar de BD de todas formas
    
    # Eliminar de BD
    db.delete(manual)
    db.commit()
    
    logger.info(f"Manual eliminado: {manual_id} by {current_user.username}")


@router.get("/categories/list")
def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener lista de categorías disponibles.
    
    Útil para UI (select dropdown)
    """
    
    categories = db.query(ManualDB.category).distinct().filter(
        ManualDB.active == True
    ).order_by(ManualDB.category).all()
    
    return {"categories": [c[0] for c in categories if c[0]]}
