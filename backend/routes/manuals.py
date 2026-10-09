"""
EMANTIC PRO - Manuals Router
Endpoint para gestión de manuales técnicos y documentación
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db, ManualDB
import uuid
import os
from datetime import datetime

router = APIRouter(prefix="/api/manuals", tags=["manuals"])

# ═══════════════════════════════════════════════════════════
# GET - Obtener Manuales
# ═══════════════════════════════════════════════════════════

@router.get("/")
async def get_manuals(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Obtener lista de manuales con paginación
    SQL Server requiere ORDER BY cuando hay OFFSET/LIMIT
    """
    try:
        manuals = (
            db.query(ManualDB)
            .order_by(desc(ManualDB.id))  # ✅ IMPORTANTE: ORDER BY para SQL Server
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "data": manuals,
            "total": db.query(ManualDB).count(),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ═══════════════════════════════════════════════════════════
# GET - Obtener Manual por ID
# ═══════════════════════════════════════════════════════════

@router.get("/{manual_id}")
async def get_manual(manual_id: str, db: Session = Depends(get_db)):
    """Obtener un manual específico por ID"""
    try:
        manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
        
        if not manual:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        return {
            "success": True,
            "data": manual
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ═══════════════════════════════════════════════════════════
# POST - Subir Manual
# ═══════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_manual(
    file: UploadFile = File(...),
    title: str = None,
    category: str = "General",
    db: Session = Depends(get_db)
):
    """
    Subir un nuevo manual PDF
    ✅ ENDPOINT PARA SOLUCIONAR ERROR 405
    """
    try:
        # ✓ Validar que sea PDF
        if file.content_type not in ["application/pdf", "application/x-pdf"]:
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos PDF"
            )
        
        # ✓ Validar tamaño (máximo 100MB)
        max_size = 100 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail="Archivo demasiado grande (máximo 100MB)"
            )
        
        # ✓ Crear carpeta de uploads si no existe
        os.makedirs("uploads", exist_ok=True)
        
        # ✓ Generar nombre único para el archivo
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = f"uploads/{unique_filename}"
        
        # ✓ Guardar archivo en disco
        with open(filepath, "wb") as f:
            f.write(content)
        
        # ✓ Título por defecto si no se proporciona
        if not title:
            title = file.filename.replace(".pdf", "")
        
        # ✓ Calcular tamaño en MB
        size_mb = round(len(content) / 1024 / 1024, 2)
        
        # ✓ Crear registro en BD
        new_manual = ManualDB(
            id=str(uuid.uuid4()),
            title=title,
            description="",
            category=category,
            filename=unique_filename,
            url=filepath,
            size_mb=str(size_mb),
            uploaded_by="admin",  # En producción, obtener del usuario autenticado
            uploaded_at=datetime.utcnow().isoformat(),
            active=True
        )
        
        # ✓ Guardar en BD
        db.add(new_manual)
        db.commit()
        db.refresh(new_manual)
        
        return {
            "success": True,
            "message": "Manual subido correctamente",
            "data": {
                "id": new_manual.id,
                "title": new_manual.title,
                "filename": new_manual.filename,
                "size_mb": size_mb,
                "uploaded_at": new_manual.uploaded_at
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Intentar eliminar archivo si falló la BD
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        return {
            "success": False,
            "error": f"Error al subir manual: {str(e)}"
        }

# ═══════════════════════════════════════════════════════════
# PUT - Actualizar Manual
# ═══════════════════════════════════════════════════════════

@router.put("/{manual_id}")
async def update_manual(
    manual_id: str,
    title: str = None,
    description: str = None,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Actualizar información de un manual"""
    try:
        manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
        
        if not manual:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        # Actualizar solo los campos proporcionados
        if title:
            manual.title = title
        if description:
            manual.description = description
        if category:
            manual.category = category
        
        db.commit()
        db.refresh(manual)
        
        return {
            "success": True,
            "message": "Manual actualizado",
            "data": manual
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

# ═══════════════════════════════════════════════════════════
# DELETE - Eliminar Manual
# ═══════════════════════════════════════════════════════════

@router.delete("/{manual_id}")
async def delete_manual(manual_id: str, db: Session = Depends(get_db)):
    """Eliminar un manual y su archivo asociado"""
    try:
        manual = db.query(ManualDB).filter(ManualDB.id == manual_id).first()
        
        if not manual:
            raise HTTPException(status_code=404, detail="Manual no encontrado")
        
        # Guardar ruta para eliminar archivo
        filepath = manual.url
        
        # Eliminar registro de BD
        db.delete(manual)
        db.commit()
        
        # Intentar eliminar archivo del disco
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Advertencia: No se pudo eliminar archivo {filepath}: {e}")
        
        return {
            "success": True,
            "message": "Manual eliminado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

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
            .order_by(desc(ManualDB.id))
            .all()
        )
        
        return {
            "success": True,
            "data": manuals,
            "count": len(manuals)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }