# Servicio de correos técnicos (boletines / informes)
#  - Enlace de baja firmado (HMAC) que funciona con un clic, sin iniciar sesión
#  - Plantilla HTML con la marca EMANTIC
#  - Envío en lote con UNA conexión SMTP (usa las mismas variables SMTP_* del correo de recuperación)

import base64
import hashlib
import hmac
import html
import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional, Tuple

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

ROLE_MAP = {"admin": "Administrador", "tecnico": "Tecnico"}


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def email_valido(email: str) -> bool:
    e = normalizar_email(email)
    return bool(e) and len(e) <= 255 and bool(EMAIL_RE.match(e)) and ".." not in e


def rol_suscripcion(role_jwt: Optional[str]) -> str:
    """Rol del JWT ('admin' | 'tecnico') → rol de la tabla ('Administrador' | 'Tecnico' | 'Externo')."""
    return ROLE_MAP.get((role_jwt or "").lower(), "Externo")


# ── Enlace de baja ───────────────────────────────────────────────────────────

def _firma(secret: str, sub_id: int, email: str) -> str:
    msg = f"unsub:{sub_id}:{normalizar_email(email)}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()[:32]


def crear_token_baja(secret: str, sub_id: int, email: str) -> str:
    """Token sin caducidad (un enlace de baja nunca debe dejar de funcionar). Cambia si cambia el correo."""
    raw = f"{sub_id}.{_firma(secret, sub_id, email)}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def leer_token_baja(secret: str, token: str, email_de_id) -> Optional[int]:
    """
    Devuelve el id de la suscripción si el token es válido, si no None.
    `email_de_id(id)` busca el correo de esa suscripción (None si no existe).
    """
    try:
        pad = "=" * (-len(token) % 4)
        sub_s, firma = base64.urlsafe_b64decode(token + pad).decode().split(".", 1)
        sub_id = int(sub_s)
    except Exception:
        return None
    email = email_de_id(sub_id)
    if not email:
        return None
    return sub_id if hmac.compare_digest(firma, _firma(secret, sub_id, email)) else None


def url_baja(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/api/subscriptions/unsubscribe?token={token}"


# ── Plantilla ────────────────────────────────────────────────────────────────

def _parrafos(texto: str) -> str:
    """Texto plano → párrafos HTML (todo escapado: lo que escriba un admin nunca inyecta HTML)."""
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto or "") if b.strip()]
    return "".join(
        f'<p style="color:#334155;font-size:14px;line-height:1.6;margin:0 0 14px;">{html.escape(b).replace(chr(10), "<br>")}</p>'
        for b in bloques
    )


def plantilla_html(titulo: str, cuerpo: str, enlace_baja: Optional[str] = None, base_url: str = "") -> str:
    if enlace_baja:
        pie = ('Recibes este correo porque te suscribiste a los informes técnicos de EMANTIC.<br>'
               f'<a href="{html.escape(enlace_baja)}" style="color:#0d5c45;font-weight:bold;">Cancelar suscripción</a>'
               '&nbsp;·&nbsp; © EMANTIC — Centralización técnica')
    else:
        pie = 'Mensaje automático de EMANTIC — Centro de Gestión. No respondas a este correo.'
    return f'''<!doctype html><html lang="es"><body style="margin:0;background:#f4f6f9;">
<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <div style="background:linear-gradient(135deg,#0d5c45,#1a7fbf);padding:22px 24px;border-radius:12px 12px 0 0;">
    <div style="color:#fff;font-size:22px;font-weight:800;letter-spacing:2px;">EMANTIC</div>
    <div style="color:rgba(255,255,255,.75);font-size:12px;letter-spacing:3px;margin-top:2px;">SISTEMA TÉCNICO</div>
  </div>
  <div style="background:#fff;padding:28px 24px;border-radius:0 0 12px 12px;box-shadow:0 2px 8px rgba(0,0,0,.06);">
    <h2 style="color:#0d3d2e;font-size:19px;margin:0 0 16px;">{html.escape(titulo)}</h2>
    {_parrafos(cuerpo)}
  </div>
  <p style="color:#94a3b8;font-size:11px;line-height:1.6;text-align:center;margin:18px 0 0;">
    {pie}
  </p>
</div></body></html>'''


def texto_plano(titulo: str, cuerpo: str, enlace_baja: str) -> str:
    return f"{titulo}\n\n{cuerpo}\n\n--\nCancelar suscripción: {enlace_baja}\n"


# ── Envío ────────────────────────────────────────────────────────────────────

def _mensaje(settings, to_email: str, asunto: str, titulo: str, cuerpo: str, enlace: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["List-Unsubscribe"] = f"<{enlace}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.attach(MIMEText(texto_plano(titulo, cuerpo, enlace), "plain", "utf-8"))
    msg.attach(MIMEText(plantilla_html(titulo, cuerpo, enlace), "html", "utf-8"))
    return msg


def enviar_boletin(
    destinatarios: Iterable[Tuple[int, str]],
    asunto: str,
    cuerpo: str,
    titulo: Optional[str] = None,
    *,
    settings=None,
    smtp_factory=smtplib.SMTP,
) -> dict:
    """
    Envía a [(id_suscripcion, correo), …] con UNA conexión SMTP. Un fallo en un correo no detiene el resto.
    Pensado para BackgroundTasks (es síncrono: FastAPI lo corre en un hilo, sin bloquear la API).
    Devuelve {'enviados': n, 'fallidos': n, 'sin_smtp': bool}.
    """
    if settings is None:
        from config import settings as _s
        settings = _s
    lista = list(destinatarios)
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP no configurado. Boletín no enviado (%d destinatarios).", len(lista))
        return {"enviados": 0, "fallidos": len(lista), "sin_smtp": True}

    base = os.getenv("APP_PUBLIC_URL", "http://localhost:8000")
    enviados = fallidos = 0
    try:
        with smtp_factory(settings.smtp_host, settings.smtp_port, timeout=20) as srv:
            srv.starttls()
            srv.login(settings.smtp_user, settings.smtp_password)
            for sub_id, correo in lista:
                try:
                    enlace = url_baja(base, crear_token_baja(settings.secret_key, sub_id, correo))
                    msg = _mensaje(settings, correo, asunto, titulo or asunto, cuerpo, enlace)
                    srv.sendmail(settings.smtp_user, correo, msg.as_string())
                    enviados += 1
                except Exception as e:                       # un correo malo no frena al resto
                    fallidos += 1
                    logger.error("No se pudo enviar a %s: %s", correo, e)
    except Exception as e:
        logger.error("Error SMTP en el boletín: %s", e)
        fallidos = len(lista) - enviados
    logger.info("Boletín '%s': %d enviados, %d fallidos", asunto, enviados, fallidos)
    return {"enviados": enviados, "fallidos": fallidos, "sin_smtp": False}


def enviar_aviso(to_email: str, asunto: str, titulo: str, cuerpo: str, *, settings=None, smtp_factory=smtplib.SMTP) -> bool:
    """Aviso transaccional de UN destinatario (sin enlace de baja): nueva solicitud / respuesta del Centro de Gestión."""
    if settings is None:
        from config import settings as _s
        settings = _s
    if not email_valido(to_email):
        return False
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP no configurado. Aviso no enviado a %s.", to_email)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(f"{titulo}\n\n{cuerpo}\n", "plain", "utf-8"))
        msg.attach(MIMEText(plantilla_html(titulo, cuerpo), "html", "utf-8"))
        with smtp_factory(settings.smtp_host, settings.smtp_port, timeout=15) as srv:
            srv.starttls()
            srv.login(settings.smtp_user, settings.smtp_password)
            srv.sendmail(settings.smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error("No se pudo enviar el aviso a %s: %s", to_email, e)
        return False


def pagina_baja(ok: bool, correo: str = "") -> str:
    """Página que ve la persona al pulsar «Cancelar suscripción»."""
    titulo = "Suscripción cancelada" if ok else "Enlace no válido"
    texto = (f"Dejarás de recibir los informes técnicos en <b>{html.escape(correo)}</b>. "
             "Puedes volver a activarlos cuando quieras desde el pie de página de EMANTIC."
             if ok else "Este enlace de cancelación no es válido o ya no existe.")
    return f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} · EMANTIC</title>
<body style="margin:0;background:#f4f6f9;font-family:Arial,Helvetica,sans-serif;display:grid;place-items:center;min-height:100vh;">
<div style="max-width:440px;margin:16px;background:#fff;border-radius:14px;box-shadow:0 4px 18px rgba(0,0,0,.08);overflow:hidden;text-align:center;">
<div style="background:linear-gradient(135deg,#0d5c45,#1a7fbf);padding:18px;color:#fff;font-weight:800;letter-spacing:2px;">EMANTIC<div style="font-size:11px;font-weight:400;letter-spacing:3px;opacity:.8;">SISTEMA TÉCNICO</div></div>
<div style="padding:28px;"><h2 style="color:#0d3d2e;margin:0 0 10px;">{titulo}</h2><p style="color:#475569;line-height:1.6;margin:0;">{texto}</p></div></div></body></html>'''
