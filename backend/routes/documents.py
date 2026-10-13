"""
EMANTIC PRO - Rutas de Documentación
Endpoints consumidos por Documentation.vue:
  GET    /api/docs            -> lista de documentos
  POST   /api/docs/upload     -> subir documento (title, category, file)
  DELETE /api/docs/{doc_id}   -> eliminar (solo admin)
"""

import os
import re
import uuid
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import DocumentDB
from deps import get_db, get_current_user, get_current_admin_user
from utils.sanitize import sanitize_string

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docs", tags=["documentos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_SIZE_MB = 100
ALLOWED_EXT = {
    "pdf", "doc", "docx", "xls", "xlsx", "csv", "ppt", "pptx",
    "txt", "mp4", "png", "jpg", "jpeg",
}


def _username(user) -> str:
    if isinstance(user, dict):
        return str(user.get("username") or user.get("sub") or "")
    return str(getattr(user, "username", "") or "")


def _doc_to_dict(d: DocumentDB) -> dict:
    return {
        "id": d.id,
        "title": d.title or "",
        "category": d.category or "General",
        "filename": d.filename or "",
        "url": d.url or "",
        "ext": d.ext or "FILE",
        "size_kb": d.size_kb or "0",
        "uploaded_by": d.uploaded_by or "",
        "uploaded_at": d.uploaded_at or "",
    }


@router.get("")
def list_docs(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(DocumentDB)
    if category:
        q = q.filter(DocumentDB.category == category)
    # SQL Server exige ORDER BY consistente; uploaded_at es texto, id desempata
    docs = q.order_by(desc(DocumentDB.uploaded_at), desc(DocumentDB.id)).all()
    return [_doc_to_dict(d) for d in docs]


@router.post("/upload")
async def upload_doc(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("General"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    original = os.path.basename(file.filename or "")
    ext = Path(original).suffix.lower().lstrip(".")

    if not original or ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(sorted(ALLOWED_EXT))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El archivo supera {MAX_SIZE_MB} MB")

    # Si es PDF, verificar firma real del archivo
    if ext == "pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido")

    doc_id = str(uuid.uuid4())
    # Nombre en disco: UUID + nombre limpio (sin caracteres peligrosos)
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original)[:150]
    stored_name = f"{doc_id}_{clean_name}"
    filepath = os.path.join(UPLOAD_DIR, stored_name)

    final_title = sanitize_string(title or Path(original).stem, max_length=300)
    final_category = sanitize_string(category or "General", max_length=100)

    try:
        with open(filepath, "wb") as f:
            f.write(content)

        doc = DocumentDB(
            id=doc_id,
            title=final_title,
            category=final_category,
            filename=stored_name,
            url=f"/uploads/{stored_name}",
            ext=ext.upper(),
            size_kb=str(round(len(content) / 1024)),
            uploaded_by=_username(user),
            uploaded_at=str(date.today()),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except Exception:
        db.rollback()
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        logger.exception("Error guardando documento")
        raise HTTPException(status_code=500, detail="No se pudo guardar el documento")

    logger.info("Documento subido por %s: %s", _username(user), stored_name)
    return {**_doc_to_dict(doc), "message": "Documento subido correctamente"}


@router.delete("/{doc_id}")
def delete_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    filepath = os.path.join(UPLOAD_DIR, os.path.basename(doc.filename or ""))
    try:
        db.delete(doc)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error eliminando documento")
        raise HTTPException(status_code=500, detail="No se pudo eliminar el documento")

    if doc.filename and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            logger.warning("No se pudo borrar el archivo %s", filepath)

    return {"message": "Documento eliminado correctamente"}