# Rutas de suscripción a correos técnicos
#  POST  /api/subscriptions                    footer: suscribirse (requiere sesión)
#  GET   /api/subscriptions/me                 ¿mi correo está suscrito?
#  PATCH /api/users/me/email-preferences       interruptor del perfil (activar / desactivar)
#  GET|POST /api/subscriptions/unsubscribe     baja con un clic desde el correo (sin sesión)
#  GET   /api/subscriptions                    admin: lista y totales
#  POST  /api/subscriptions/broadcast          admin: enviar un informe a los suscritos activos
#  POST  /api/subscriptions/send-test          admin: enviarse una prueba a sí mismo

import datetime
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import NewsletterSubscriptionDB, UserDB
from deps import get_current_admin_user, get_current_user, get_db
from services import newsletter as nl
from utils.rate_limit import rate_limit_sync

logger = logging.getLogger(__name__)
router = APIRouter(tags=["subscriptions"])


# ── Esquemas ──────────────────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    email: str
    accepted_terms: bool


class PreferencesRequest(BaseModel):
    enabled: bool


class BroadcastRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=150)
    body: str = Field(..., min_length=3, max_length=8000)


def _ahora():
    return datetime.datetime.utcnow()


def _upsert(db: Session, email: str, user_id, role_jwt, *, activo: bool, acepto: bool) -> NewsletterSubscriptionDB:
    """Crea o actualiza (reactiva / desactiva) la suscripción de ese correo."""
    s = db.query(NewsletterSubscriptionDB).filter(NewsletterSubscriptionDB.email == email).first()
    if s is None:
        s = NewsletterSubscriptionDB(email=email, created_at=_ahora())
        db.add(s)
    s.user_id = user_id or s.user_id
    s.role = nl.rol_suscripcion(role_jwt)
    s.accepted_terms = bool(acepto or s.accepted_terms)
    s.is_active = activo
    s.updated_at = _ahora()
    s.unsubscribed_at = None if activo else _ahora()
    db.commit()
    db.refresh(s)
    return s


def _bienvenida(sub_id: int, correo: str):
    """Correo de confirmación con el enlace de baja (tarea en segundo plano)."""
    nl.enviar_boletin(
        [(sub_id, correo)],
        "Te suscribiste a los informes técnicos de EMANTIC",
        "Listo: recibirás informes de gestión de móviles (DPV, ICO, inmovilizados), análisis de mantenimiento "
        "y novedades técnicas.\n\nSi no fuiste tú, usa el enlace de abajo para cancelar la suscripción.",
        titulo="Suscripción confirmada",
    )


# ── Footer: suscribirse ───────────────────────────────────────────────────────

@router.post("/api/subscriptions")
@rate_limit_sync(max_attempts=5, window_seconds=3600,
                 key_func=lambda req, db=None, bg=None, user=None, request=None, **kw: f"{(user or {}).get('sub', 'anon')}:subscribe")
def subscribe(req: SubscribeRequest, request: Request, bg: BackgroundTasks,
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    email = nl.normalizar_email(req.email)
    if not nl.email_valido(email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Correo electrónico inválido")
    if not req.accepted_terms:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Debes aceptar los Términos y la Política de Privacidad")

    previa = db.query(NewsletterSubscriptionDB).filter_by(email=email).first()
    ya_activa = bool(previa and previa.is_active)
    s = _upsert(db, email, user.get("sub"), user.get("role"), activo=True, acepto=True)
    if not ya_activa:
        bg.add_task(_bienvenida, s.id, s.email)
    return {"ok": True, "subscribed": True, "ya_estaba": ya_activa,
            "message": "Ya estabas suscrito." if ya_activa else "¡Listo! Te enviamos una confirmación."}


@router.get("/api/subscriptions/me")
def my_subscription(db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.query(UserDB).filter_by(id=user.get("sub")).first()
    correo = nl.normalizar_email(u.email) if u else ""
    s = db.query(NewsletterSubscriptionDB).filter_by(email=correo).first() if correo else None
    return {"email": correo, "tiene_correo": bool(correo), "subscribed": bool(s and s.is_active)}


# ── Perfil: interruptor ───────────────────────────────────────────────────────

@router.patch("/api/users/me/email-preferences")
def set_email_preferences(req: PreferencesRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "tecnico"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo técnicos y administradores")
    u = db.query(UserDB).filter_by(id=user.get("sub")).first()
    correo = nl.normalizar_email(u.email) if u else ""
    if not nl.email_valido(correo):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu usuario no tiene un correo válido. Pide a un administrador que lo registre.")
    s = _upsert(db, correo, u.id, u.role, activo=req.enabled, acepto=req.enabled)
    return {"ok": True, "email": correo, "subscribed": bool(s.is_active)}


# ── Baja con un clic (público: lo abre quien recibe el correo) ────────────────

def _baja(token: str, db: Session):
    def email_de(i):
        s = db.query(NewsletterSubscriptionDB).filter_by(id=i).first()
        return s.email if s else None
    sub_id = nl.leer_token_baja(settings.secret_key, token or "", email_de)
    if sub_id is None:
        return None
    s = db.query(NewsletterSubscriptionDB).filter_by(id=sub_id).first()
    s.is_active = False
    s.unsubscribed_at = s.updated_at = _ahora()
    db.commit()
    return s.email


@router.get("/api/subscriptions/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(token: str = "", db: Session = Depends(get_db)):
    correo = _baja(token, db)
    return HTMLResponse(nl.pagina_baja(correo is not None, correo or ""), status_code=200 if correo else 400)


@router.post("/api/subscriptions/unsubscribe")          # «One-Click» de Gmail/Outlook (RFC 8058)
def unsubscribe_one_click(token: str = "", db: Session = Depends(get_db)):
    if _baja(token, db) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enlace no válido")
    return {"ok": True}


# ── Administración ────────────────────────────────────────────────────────────

@router.get("/api/subscriptions")
def list_subscriptions(db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    filas = db.query(NewsletterSubscriptionDB).order_by(NewsletterSubscriptionDB.created_at.desc()).all()
    return {
        "total": len(filas),
        "activos": sum(1 for s in filas if s.is_active),
        "items": [{"id": s.id, "email": s.email, "role": s.role, "is_active": bool(s.is_active),
                   "created_at": str(s.created_at)} for s in filas],
    }


@router.post("/api/subscriptions/broadcast")
def broadcast(req: BroadcastRequest, bg: BackgroundTasks,
              db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    dest = [(s.id, s.email) for s in db.query(NewsletterSubscriptionDB).filter_by(is_active=True, accepted_terms=True).all()]
    if not dest:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay suscriptores activos")
    if not settings.smtp_user or not settings.smtp_password:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SMTP no configurado (SMTP_USER / SMTP_PASSWORD)")
    bg.add_task(nl.enviar_boletin, dest, req.subject.strip(), req.body.strip())
    logger.info("Boletín '%s' encolado por %s para %d suscriptores", req.subject, admin.get("username"), len(dest))
    return {"ok": True, "encolados": len(dest)}


@router.post("/api/subscriptions/send-test")
def send_test(req: BroadcastRequest, bg: BackgroundTasks,
              db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    u = db.query(UserDB).filter_by(id=admin.get("sub")).first()
    correo = nl.normalizar_email(u.email) if u else ""
    if not nl.email_valido(correo):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu usuario no tiene un correo válido")
    s = db.query(NewsletterSubscriptionDB).filter_by(email=correo).first()
    if s is None:                       # solo para tener un id con el que firmar el enlace de baja; queda DESACTIVADA
        s = _upsert(db, correo, u.id, u.role, activo=False, acepto=False)
    bg.add_task(nl.enviar_boletin, [(s.id, s.email)], "[PRUEBA] " + req.subject.strip(), req.body.strip())
    return {"ok": True, "enviado_a": correo}
