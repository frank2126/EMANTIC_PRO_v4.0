"""
- Rutas de Repuestos
- Listado con búsqueda, filtros y paginación en el servidor
- Carga desde Excel (.xlsx), solo administradores
- Requiere sesión iniciada (igual que el resto de la API)
"""

import io
import logging
import unicodedata
from typing import Optional

import openpyxl
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from database import RepuestoDB
from deps import get_db, get_current_user, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repuestos", tags=["repuestos"])

# --- HELPERS START ---------------------------------------------------------

# Encabezado del Excel (sin tildes, minúsculas, con guiones bajos) -> campo del modelo
COLUMN_MAP = {
    "pieza": "pieza",
    "descripcion": "descripcion",
    "udm": "udm",
    "clase": "clase",
    "jerarquia_de_la_pieza": "jerarquia_pieza",
    "nivel_de_sistema": "nivel_sistema",
    "nivel_de_montaje": "nivel_montaje",
    "nivel_de_componente": "nivel_componente",
    "condicion": "condicion",
    "numero_de_pieza_del_fabricante_principal": "numero_pieza_fabricante",
    "suministrador_sugerido": "suministrador_sugerido",
    "seguimiento_de_piezas_reparables": "seguimiento_piezas_reparables",
    "seguimiento_por_activo": "seguimiento_por_activo",
    "dias_de_garantia": "dias_garantia",
    "evitar_nuevos_pedidos": "evitar_nuevos_pedidos",
}

# Largo máximo de cada columna de texto (evita errores de SQL Server por truncado)
MAX_LEN = {
    "pieza": 50,
    "descripcion": 500,
    "udm": 20,
    "clase": 50,
    "jerarquia_pieza": 100,
    "nivel_sistema": 50,
    "nivel_montaje": 100,
    "nivel_componente": 100,
    "condicion": 100,
    "numero_pieza_fabricante": 100,
    "suministrador_sugerido": 200,
    "seguimiento_piezas_reparables": 10,
    "seguimiento_por_activo": 10,
    "evitar_nuevos_pedidos": 10,
}


def _norm_header(value) -> str:
    """'Descripción' -> 'descripcion', 'Días de garantía' -> 'dias_de_garantia'."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower().strip()
    return "_".join(text.split())


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def _to_int(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def parse_repuestos(content: bytes):
    """
    Lee el Excel y devuelve (registros, omitidos).
    Cada registro es un dict con los campos del modelo. Si una pieza aparece
    repetida en el archivo, queda la última fila.
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)

    try:
        header_row = next(rows)
    except StopIteration:
        raise ValueError("El archivo Excel está vacío")

    columns = {}  # índice de columna -> campo del modelo
    for idx, name in enumerate(header_row):
        field = COLUMN_MAP.get(_norm_header(name))
        if field:
            columns[idx] = field

    if "pieza" not in columns.values():
        raise ValueError("No se encontró la columna 'Pieza' en el Excel")

    records = {}
    skipped = 0
    for row in rows:
        rec = {}
        for idx, field in columns.items():
            raw = row[idx] if idx < len(row) else None
            if field == "dias_garantia":
                rec[field] = _to_int(raw)
            else:
                rec[field] = _clean(raw)[: MAX_LEN[field]]

        if not rec.get("pieza"):
            skipped += 1
            continue
        records[rec["pieza"]] = rec

    return list(records.values()), skipped


def repuesto_to_dict(r: RepuestoDB) -> dict:
    return {
        "id": r.id,
        "pieza": r.pieza,
        "descripcion": r.descripcion or "",
        "udm": r.udm or "",
        "clase": r.clase or "",
        "jerarquia_pieza": r.jerarquia_pieza or "",
        "nivel_sistema": r.nivel_sistema or "",
        "nivel_montaje": r.nivel_montaje or "",
        "nivel_componente": r.nivel_componente or "",
        "condicion": r.condicion or "",
        "numero_pieza_fabricante": r.numero_pieza_fabricante or "",
        "suministrador_sugerido": r.suministrador_sugerido or "",
        "seguimiento_piezas_reparables": r.seguimiento_piezas_reparables or "",
        "seguimiento_por_activo": r.seguimiento_por_activo or "",
        "dias_garantia": r.dias_garantia or 0,
        "evitar_nuevos_pedidos": r.evitar_nuevos_pedidos or "",
    }

# --- HELPERS END -----------------------------------------------------------


# ── LISTADO + BÚSQUEDA ──────────────────────────────────────────────────────

@router.get("")
def list_repuestos(
    q: Optional[str] = Query(None, max_length=100),
    clase: Optional[str] = Query(None, max_length=50),
    nivel_sistema: Optional[str] = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Busca en código (pieza) y descripción.
    Varias palabras se combinan con AND: "filtro aceite" encuentra descripciones
    que contengan ambas. Los códigos que empiezan con la primera palabra salen primero.
    """
    query = db.query(RepuestoDB).filter(RepuestoDB.activo == True)  # noqa: E712

    if clase:
        query = query.filter(RepuestoDB.clase == clase)
    if nivel_sistema:
        query = query.filter(RepuestoDB.nivel_sistema == nivel_sistema)

    terms = (q or "").split()[:5]
    for term in terms:
        query = query.filter(
            or_(
                RepuestoDB.pieza.icontains(term, autoescape=True),
                RepuestoDB.descripcion.icontains(term, autoescape=True),
            )
        )

    total = query.count()

    order = []
    if terms:
        order.append(
            case((RepuestoDB.pieza.istartswith(terms[0], autoescape=True), 0), else_=1)
        )
    order.append(RepuestoDB.pieza.asc())  # SQL Server exige ORDER BY con OFFSET

    items = (
        query.order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [repuesto_to_dict(r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── VALORES PARA LOS FILTROS ────────────────────────────────────────────────

@router.get("/filtros")
def get_filtros(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    def distinct_values(column):
        rows = (
            db.query(column)
            .filter(RepuestoDB.activo == True)  # noqa: E712
            .filter(column.isnot(None), column != "")
            .distinct()
            .order_by(column.asc())
            .all()
        )
        return [r[0] for r in rows]

    return {
        "clases": distinct_values(RepuestoDB.clase),
        "niveles": distinct_values(RepuestoDB.nivel_sistema),
    }


# ── CARGA DESDE EXCEL (SOLO ADMIN) ──────────────────────────────────────────

@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Inserta repuestos nuevos y actualiza los existentes (se identifican por 'Pieza')."""
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Sube un archivo Excel en formato .xlsx")

    content = await file.read()

    try:
        records, skipped = parse_repuestos(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("No se pudo leer el Excel de repuestos")
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo Excel")

    if not records:
        raise HTTPException(status_code=400, detail="El Excel no tiene filas con código de pieza")

    inserted = 0
    updated = 0
    try:
        existing = {r.pieza: r for r in db.query(RepuestoDB).all()}
        for rec in records:
            row = existing.get(rec["pieza"])
            if row:
                for key, value in rec.items():
                    setattr(row, key, value)
                row.activo = True
                updated += 1
            else:
                db.add(RepuestoDB(**rec, activo=True))
                inserted += 1
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error guardando repuestos")
        raise HTTPException(status_code=500, detail="Error guardando los repuestos")

    logger.info(
        "Repuestos cargados por %s: %s nuevos, %s actualizados, %s omitidos",
        getattr(admin, "username", "admin"), inserted, updated, skipped,
    )
    return {
        "insertados": inserted,
        "actualizados": updated,
        "omitidos": skipped,
        "total": len(records),
    }