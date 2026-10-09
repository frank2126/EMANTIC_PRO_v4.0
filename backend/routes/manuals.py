"""
EMANTIC PRO - Manuals Router
Gestión de manuales técnicos con serialización correcta
Basado en código original que funcionaba correctamente
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db, ManualDB
import uuid
import os
from datetime import datetime, date

router = APIRouter(prefix="/api/manuals", tags=["manuals"])

# ═══════════════════════════════════════════════════════════
# CATEGORÍAS HARDCODEADAS (Como en el código original)
# ═══════════════════════════════════════════════════════════

MANUAL_CATEGORIES = [
    "Transmilenio",
    "Sistema de Frenos",
    "Sistema Eléctrico",
    "Suspensión",
    "Carrocería y Chasis",
    "Diagnóstico ECU",
    "General",
    "Motor y Transmisión"
]

# ═══════════════════════════════════════════════════════════
# Crear carpeta de uploads si no existe
# ═══════════════════════════════════════════════════════════

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# GET - Categorías (Hardcodeadas)
# ═══════════════════════════════════════════════════════════

@router.get("/categories")
async def get_categories():
    """
    Obtener todas las categorías de manuales disponibles
    Devuelve lista hardcodeada como en el código original
    """
    try:
        return MANUAL_CATEGORIES
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Todos los Manuales
# ═══════════════════════════════════════════════════════════

@router.get("/")
async def get_manuals(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Obtener lista de manuales con paginación
    Devuelve DICTS en lugar de objetos SQLAlchemy
    """
    try:
        # Filtrar solo manuales activos
        manuals = (
            db.query(ManualDB)
            .filter_by(active=True)
            .order_by(desc(ManualDB.uploaded_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Convertir a dicts para serialización correcta
        result = []
        for m in manuals:
            result.append({
                "id": m.id,
                "title": m.title or "",
                "description": m.description or "",
                "category": m.category or "General",
                "filename": m.filename or "",
                "url": m.url or "",
                "size_mb": m.size_mb or "0",
                "uploaded_by": m.uploaded_by or "",
                "uploaded_at": m.uploaded_at or str(date.today()),
                "active": m.active
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Manuales por Categoría
# ═══════════════════════════════════════════════════════════

@router.get("/categoria/{category}")
async def get_manuals_by_category(
    category: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Obtener manuales filtrados por categoría
    Devuelve DICTS para evitar problemas de serialización
    """
    try:
        manuals = (
            db.query(ManualDB)
            .filter_by(category=category, active=True)
            .order_by(desc(ManualDB.uploaded_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Convertir a dicts
        result = []
        for m in manuals:
            result.append({
                "id": m.id,
                "title": m.title or "",
                "description": m.description or "",
                "category": m.category or "General",
                "filename": m.filename or "",
                "url": m.url or "",
                "size_mb": m.size_mb or "0",
                "uploaded_by": m.uploaded_by or "",
                "uploaded_at": m.uploaded_at or str(date.today()),
                "active": m.active
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Manual por ID
# ═══════════════════════════════════════════════════════════

@router.get("/{manual_id}")
async def get_manual(manual_id: str, db: Session = Depends(get_db)):
    """Obtener un manual específico por ID"""
    try:
        m = db.query(ManualDB).filter_by(id=manual_id, active=True).first()
        
        if not m:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        return {
            "id": m.id,
            "title": m.title or "",
            "description": m.description or "",
            "category": m.category or "General",
            "filename": m.filename or "",
            "url": m.url or "",
            "size_mb": m.size_mb or "0",
            "uploaded_by": m.uploaded_by or "",
            "uploaded_at": m.uploaded_at or str(date.today()),
            "active": m.active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# POST - Subir Manual (Con Form como en el original)
# ═══════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_manual(
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    category: str = Form("General"),
    db: Session = Depends(get_db)
):
    """
    Subir un nuevo manual PDF
    Usa Form para los parámetros (como en el código original)
    Devuelve un DICT
    """
    try:
        # Validar que sea PDF
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
        
        # Generar ID único
        file_id = str(uuid.uuid4())
        
        # Crear nombre único del archivo
        filename = f"{file_id}_{file.filename}"
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Calcular tamaño en MB
        size_mb = round(len(content) / 1024 / 1024, 1)
        
        # Guardar archivo en disco
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Preparar título (usar nombre del archivo si no se proporciona)
        final_title = title or file.filename.replace(".pdf", "")
        
        # Crear registro en BD
        m = ManualDB(
            id=file_id,
            title=final_title,
            description=description,
            category=category,
            filename=filename,
            url=f"/uploads/{filename}",  # Ruta relativa como en original
            size_mb=str(size_mb),
            uploaded_by="admin",  # En producción: obtener del usuario autenticado
            uploaded_at=str(date.today()),
            active=True
        )
        
        db.add(m)
        db.commit()
        db.refresh(m)
        
        # Retornar DICT
        return {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "filename": m.filename,
            "url": m.url,
            "size_mb": m.size_mb,
            "uploaded_by": m.uploaded_by,
            "uploaded_at": m.uploaded_at,
            "message": "Manual subido correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Intentar eliminar archivo si falló
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Error al subir manual: {str(e)}")

# ═══════════════════════════════════════════════════════════
# DELETE - Eliminar Manual (Marca como inactivo)
# ═══════════════════════════════════════════════════════════

@router.delete("/{manual_id}")
async def delete_manual(manual_id: str, db: Session = Depends(get_db)):
    """
    Eliminar un manual (marca como inactivo en lugar de eliminar)
    Como en el código original
    """
    try:
        m = db.query(ManualDB).filter_by(id=manual_id).first()
        
        if not m:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        # Marcar como inactivo en lugar de eliminar
        m.active = False
        db.commit()
        
        return {"message": "Manual eliminado correctamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# PUT - Actualizar Manual
# ═══════════════════════════════════════════════════════════

@router.put("/{manual_id}")
async def update_manual(
    manual_id: str,
    title: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    db: Session = Depends(get_db)
):
    """Actualizar información de un manual"""
    try:
        m = db.query(ManualDB).filter_by(id=manual_id).first()
        
        if not m:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        # Actualizar solo los campos proporcionados
        if title:
            m.title = title
        if description:
            m.description = description
        if category:
            m.category = category
        
        db.commit()
        db.refresh(m)
        
        return {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "filename": m.filename,
            "url": m.url,
            "size_mb": m.size_mb,
            "uploaded_by": m.uploaded_by,
            "uploaded_at": m.uploaded_at,
            "message": "Manual actualizado"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Búsqueda de Manuales
# ═══════════════════════════════════════════════════════════

@router.get("/search/{query}")
async def search_manuals(query: str, db: Session = Depends(get_db)):
    """Buscar manuales por título o descripción"""
    try:
        manuals = (
            db.query(ManualDB)
            .filter(
                (ManualDB.title.ilike(f"%{query}%")) |
                (ManualDB.description.ilike(f"%{query}%"))
            )
            .filter_by(active=True)
            .order_by(desc(ManualDB.uploaded_at))
            .all()
        )
        
        result = []
        for m in manuals:
            result.append({
                "id": m.id,
                "title": m.title or "",
                "description": m.description or "",
                "category": m.category or "General",
                "filename": m.filename or "",
                "url": m.url or "",
                "size_mb": m.size_mb or "0",
                "uploaded_by": m.uploaded_by or "",
                "uploaded_at": m.uploaded_at or str(date.today()),
                "active": m.active
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))