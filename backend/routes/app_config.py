"""
Guarda la URL de inserción de Power BI en la base de datos para que quede fija
para todos los usuarios: cualquiera con sesión iniciada puede leerla y solo un
administrador puede cambiarla

"""

import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import AppConfigDB
from deps import get_db, get_current_user, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

KEY_URL = "powerbi_url"
KEY_REFRESH = "powerbi_refresh"
REFRESH_VALIDOS = {"none", "30", "60", "300"}
MAX_URL_LEN = 2000

# --- HELPERS START ---------------------------------------------------------


def url_powerbi_valida(url: str) -> bool:
    """Solo https y solo dominios de Power BI (evita que se inserte otra página o un javascript:)."""
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
    except ValueError:
        return False
    if p.scheme != "https" or not host:
        return False
    return (
        host == "powerbi.com"
        or host.endswith(".powerbi.com")
        or host.endswith(".powerbigov.us")
    )


def _username(user) -> str:
    # En algunas rutas el usuario llega como dict y en otras como objeto
    if isinstance(user, dict):
        return str(user.get("username") or user.get("sub") or "")
    return str(getattr(user, "username", "") or "")

# --- HELPERS END -----------------------------------------------------------


class PowerBIConfigIn(BaseModel):
    url: str = ""
    refresh: str = "none"


def _leer(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfigDB).filter(AppConfigDB.key == key).first()
    return row.value if row and row.value is not None else default


def _escribir(db: Session, key: str, value: str, quien: str) -> None:
    row = db.query(AppConfigDB).filter(AppConfigDB.key == key).first()
    if row:
        row.value = value
        row.updated_by = quien
    else:
        db.add(AppConfigDB(key=key, value=value, updated_by=quien))


@router.get("/powerbi")
def obtener_powerbi(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {
        "url": _leer(db, KEY_URL),
        "refresh": _leer(db, KEY_REFRESH, "none"),
    }


@router.put("/powerbi")
def guardar_powerbi(
    datos: PowerBIConfigIn,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """Guarda la URL (o la borra si llega vacía) y el modo de recarga automática."""
    url = (datos.url or "").strip()
    refresh = (datos.refresh or "none").strip()

    if url:
        if len(url) > MAX_URL_LEN:
            raise HTTPException(status_code=400, detail="La URL es demasiado larga")
        if not url_powerbi_valida(url):
            raise HTTPException(
                status_code=400,
                detail="La URL debe ser https y de powerbi.com (la que se copia en Archivo → Insertar informe → Sitio web o portal)",
            )
    if refresh not in REFRESH_VALIDOS:
        raise HTTPException(status_code=400, detail="Modo de recarga no válido")

    quien = _username(admin)
    try:
        _escribir(db, KEY_URL, url, quien)
        _escribir(db, KEY_REFRESH, refresh, quien)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error guardando la configuración de Power BI")
        raise HTTPException(status_code=500, detail="No se pudo guardar la configuración")

    logger.info("Configuración de Power BI actualizada por %s", quien)
    return {"url": url, "refresh": refresh}