# Rutas de solicitudes al Centro de Gestión
#  POST  /api/solicitudes              crear una solicitud (cualquier usuario con sesión)
#  GET   /api/solicitudes/mias         mis solicitudes con sus respuestas
#  GET   /api/solicitudes/resumen      contadores para la insignia del footer
#  POST  /api/solicitudes/mias/vistas  marcar mis respuestas como leídas
#  GET   /api/solicitudes/bandeja      admin: todas las solicitudes (filtro por estado)
#  PATCH /api/solicitudes/{id}         admin: responder / cambiar estado

import datetime
import logging
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import SolicitudDB, UserDB
from deps import get_current_admin_user, get_current_user, get_db
from services import newsletter as nl
from services import solicitudes as sv
from utils.rate_limit import rate_limit_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])


class NuevaSolicitud(BaseModel):
    tipo: str
    mensaje: str
    movil: Optional[str] = ""
    prioridad: Optional[str] = "normal"


class Gestion(BaseModel):
    estado: Optional[str] = None
    respuesta: Optional[str] = None


def _422(e: sv.ErrorValidacion):
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


# ── Avisos por correo (segundo plano; si no hay SMTP simplemente no se envían) ─

def _avisar_centro(sol_id: int, quien: str, tipo_label: str, movil: str, urgente: bool, mensaje: str):
    destino = os.getenv("CENTRO_GESTION_EMAIL", "").strip()
    if not destino:
        return
    cuerpo = (f"Solicitud #{sol_id} de {quien}\nTipo: {tipo_label}\nMóvil: {movil or '—'}\n"
              f"Prioridad: {'URGENTE' if urgente else 'normal'}\n\n{mensaje}\n\nResponde desde el pie de página de EMANTIC → «Panel de respuestas».")
    nl.enviar_aviso(destino, f"{'[URGENTE] ' if urgente else ''}Nueva solicitud #{sol_id} — {tipo_label}", "Nueva solicitud al Centro de Gestión", cuerpo)


def _avisar_respuesta(correo: str, sol_id: int, tipo_label: str, estado: str, respuesta: str):
    nl.enviar_aviso(correo, f"Respuesta a tu solicitud #{sol_id}", "El Centro de Gestión respondió tu solicitud",
                    f"{tipo_label} · estado: {estado.replace('_', ' ')}\n\n{respuesta}\n\nTambién la ves en EMANTIC → pie de página → «Panel de respuestas».")


# ── Crear ─────────────────────────────────────────────────────────────────────

@router.post("")
@rate_limit_sync(max_attempts=10, window_seconds=3600,
                 key_func=lambda req, bg=None, db=None, user=None, request=None, **kw: f"{(user or {}).get('sub', 'anon')}:solicitud")
def crear(req: NuevaSolicitud, request: Request, bg: BackgroundTasks,
          db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        datos = sv.validar_nueva(req.tipo, req.mensaje, req.movil, req.prioridad)
    except sv.ErrorValidacion as e:
        raise _422(e)
    u = db.query(UserDB).filter_by(id=user.get("sub")).first()
    ahora = datetime.datetime.utcnow()
    s = SolicitudDB(user_id=user.get("sub"), username=user.get("username", ""), solicitante=(u.name if u else user.get("name", "")),
                    email=(u.email if u else "") or "", estado="pendiente", respuesta="", visto_solicitante=True,
                    created_at=ahora, updated_at=ahora, **datos)
    db.add(s)
    db.commit()
    db.refresh(s)
    bg.add_task(_avisar_centro, s.id, s.solicitante or s.username, sv.TIPOS[s.tipo], s.movil, s.prioridad == "urgente", s.mensaje)
    return {"ok": True, "message": f"Solicitud #{s.id} enviada. El Centro de Gestión la atenderá lo antes posible.", "item": sv.serializar(s)}


# ── Del solicitante ───────────────────────────────────────────────────────────

@router.get("/mias")
def mias(db: Session = Depends(get_db), user=Depends(get_current_user)):
    filas = (db.query(SolicitudDB).filter_by(user_id=user.get("sub"))
             .order_by(SolicitudDB.created_at.desc()).limit(50).all())
    return {"items": [sv.serializar(s) for s in filas], "sin_leer": sum(1 for s in filas if s.respuesta and not s.visto_solicitante)}


@router.get("/resumen")
def resumen(db: Session = Depends(get_db), user=Depends(get_current_user)):
    sin_leer = (db.query(func.count(SolicitudDB.id))
                .filter(SolicitudDB.user_id == user.get("sub"), SolicitudDB.visto_solicitante == False, SolicitudDB.respuesta != "")  # noqa: E712
                .scalar() or 0)
    pendientes = None
    if user.get("role") == "admin":
        pendientes = db.query(func.count(SolicitudDB.id)).filter(SolicitudDB.estado == "pendiente").scalar() or 0
    return {"sin_leer": sin_leer, "pendientes": pendientes}


@router.post("/mias/vistas")
def marcar_vistas(db: Session = Depends(get_db), user=Depends(get_current_user)):
    n = (db.query(SolicitudDB)
         .filter(SolicitudDB.user_id == user.get("sub"), SolicitudDB.visto_solicitante == False, SolicitudDB.respuesta != "")  # noqa: E712
         .update({SolicitudDB.visto_solicitante: True}, synchronize_session=False))
    db.commit()
    return {"ok": True, "marcadas": n}


# ── Centro de Gestión (admin) ─────────────────────────────────────────────────

@router.get("/bandeja")
def bandeja(estado: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    if estado and estado not in sv.ESTADOS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Estado inválido")
    q = db.query(SolicitudDB)
    if estado:
        q = q.filter(SolicitudDB.estado == estado)
    # urgentes y pendientes primero, luego las más recientes
    filas = q.order_by(SolicitudDB.created_at.desc()).limit(200).all()
    filas.sort(key=lambda s: (s.estado not in ("pendiente", "en_proceso"), s.prioridad != "urgente"))
    cuentas = dict(db.query(SolicitudDB.estado, func.count(SolicitudDB.id)).group_by(SolicitudDB.estado).all())
    return {"items": [sv.serializar(s, incluir_solicitante=True) for s in filas],
            "conteo": {e: int(cuentas.get(e, 0)) for e in sv.ESTADOS}}


@router.patch("/{sol_id}")
def gestionar(sol_id: int, req: Gestion, bg: BackgroundTasks,
              db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    s = db.query(SolicitudDB).filter_by(id=sol_id).first()
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitud no encontrada")
    try:
        r = sv.aplicar_gestion(s, req.estado, req.respuesta, gestor=admin.get("name") or admin.get("username", ""))
    except sv.ErrorValidacion as e:
        raise _422(e)
    s.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(s)
    if r["cambio_respuesta"] and nl.email_valido(s.email):
        bg.add_task(_avisar_respuesta, s.email, s.id, sv.TIPOS.get(s.tipo, s.tipo), s.estado, s.respuesta)
    return {"ok": True, "item": sv.serializar(s, incluir_solicitante=True)}
