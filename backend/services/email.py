# Servicio de Email
#  Envío seguro de emails con variables de entorno

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, username: str, reset_code: str) -> bool:
    """
    Enviar email de reset de contraseña.
    
    Args:
        to_email: Email del usuario
        username: Username del usuario
        reset_code: Código de 6 dígitos
        
    Returns:
        True si se envió correctamente, False si no
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP no configurado. Email no enviado.")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 Código de recuperación - EMANTIX PRO"
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        
        # HTML email profesional
        html = f'''
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:32px;background:#f4f6f9;border-radius:12px;">
          <div style="background:linear-gradient(135deg,#0d5c45,#1a7fbf);padding:24px;border-radius:10px;text-align:center;margin-bottom:24px;">
            <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:2px;">EMANTIX PRO</h1>
            <p style="color:rgba(255,255,255,0.7);margin:6px 0 0;font-size:13px;">Sistema de Gestión Técnica</p>
          </div>
          <div style="background:#fff;padding:28px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <h2 style="color:#1a2332;font-size:18px;margin:0 0 8px;">Recuperación de contraseña</h2>
            <p style="color:#64748b;font-size:14px;margin:0 0 24px;">Hola <strong>{username}</strong>, recibimos una solicitud para restablecer tu contraseña.</p>
            <div style="background:#f0fdf4;border:2px dashed #10b981;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
              <p style="color:#64748b;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Tu código de verificación</p>
              <p style="color:#0d5c45;font-size:36px;font-weight:900;letter-spacing:8px;margin:0;font-family:monospace;">{reset_code}</p>
              <p style="color:#ef4444;font-size:12px;margin:10px 0 0;">⏰ Válido por 15 minutos</p>
            </div>
            <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">Si no solicitaste este código, ignora este mensaje.<br>Tu contraseña no será modificada.</p>
          </div>
          <p style="color:#94a3b8;font-size:11px;text-align:center;margin:16px 0 0;">© EMANTIX PRO - Todos los derechos reservados</p>
        </div>
        '''
        
        msg.attach(MIMEText(html, "html"))
        
        # Enviar con timeout
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        
        logger.info(f"Email de reset enviado a {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación SMTP. Verificar credenciales.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error al enviar email: {str(e)}")
        return False
