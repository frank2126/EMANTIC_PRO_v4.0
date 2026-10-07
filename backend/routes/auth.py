# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Rutas de Autenticación
#  Login, sesiones, reset de contraseña
# ═══════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import random
import string
from datetime import datetime, timedelta
import logging

from database import SessionLocal, UserDB, PasswordResetDB
from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    validate_password_strength,
    get_password_error_message,
)
from deps import get_db, get_current_user
from utils.rate_limit import (
    rate_limit_sync,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_FORGOT_PASSWORD,
    RATE_LIMIT_RESET_PASSWORD,
    RATE_LIMIT_REFRESH_TOKEN,
    get_client_ip
)
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    VerifyCodeRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    CurrentUserResponse,
)
from services.email import send_password_reset_email
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Estado para bloqueo de intentos fallidos (OPTIMIZADO) ───────────
# Sistema con límite de memoria y limpieza automática
failed_login_attempts = {}
MAX_TRACKED_USERS = 1000  # Límite para evitar memory leak
CLEANUP_THRESHOLD = 500   # Ejecutar limpieza cuando se alcance este número

def cleanup_old_attempts(lockout_seconds: int = 300):
    """Limpiar intentos de login antiguos para evitar memory leak"""
    if len(failed_login_attempts) < CLEANUP_THRESHOLD:
        return
    
    now = time.time()
    users_to_delete = []
    
    for username, attempts in list(failed_login_attempts.items()):
        # Mantener solo intentos recientes
        recent = [t for t in attempts if now - t < lockout_seconds]
        
        if recent:
            failed_login_attempts[username] = recent
        else:
            users_to_delete.append(username)
    
    # Eliminar usuarios sin intentos recientes
    for username in users_to_delete:
        del failed_login_attempts[username]
    
    logger.debug(f"Limpieza de intentos: {len(users_to_delete)} usuarios removidos")


def is_account_locked(username: str, max_attempts: int = 5, lockout_seconds: int = 300) -> bool:
    """
    Verificar si una cuenta está bloqueada por intentos fallidos (OPTIMIZADO).
    
    Optimizaciones:
    - Limpieza automática de intentos antiguos
    - Límite de memoria
    - Operación O(n) reducida
    
    Args:
        username: Username a verificar
        max_attempts: Máximo de intentos permitidos
        lockout_seconds: Segundos de bloqueo
        
    Returns:
        True si está bloqueada, False si no
    """
    # Ejecutar limpieza si es necesario
    if len(failed_login_attempts) >= CLEANUP_THRESHOLD:
        cleanup_old_attempts(lockout_seconds)
    
    now = time.time()
    
    # Limpiar y contar solo intentos recientes
    if username in failed_login_attempts:
        recent_attempts = [
            t for t in failed_login_attempts[username]
            if now - t < lockout_seconds
        ]
        failed_login_attempts[username] = recent_attempts if recent_attempts else []
    
    # Retornar si está bloqueado
    return len(failed_login_attempts.get(username, [])) >= max_attempts


def record_failed_login(username: str):
    """
    Registrar un intento fallido de login (OPTIMIZADO).
    
    Optimizaciones:
    - Límite máximo de usuarios trackeados
    - Inicialización lazy
    """
    # Proteger contra ataques de diccionario
    if len(failed_login_attempts) >= MAX_TRACKED_USERS:
        cleanup_old_attempts()
    
    if username not in failed_login_attempts:
        failed_login_attempts[username] = []
    
    # Limitar intentos almacenados por usuario (máximo 10)
    if len(failed_login_attempts[username]) < 10:
        failed_login_attempts[username].append(time.time())


def clear_failed_logins(username: str):
    """
    Limpiar intentos fallidos tras login exitoso (OPTIMIZADO).
    
    Operación O(1) - eliminar entrada completa
    """
    failed_login_attempts.pop(username, None)  # Usar pop para evitar KeyError


# ── LOGIN ──────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse)
@rate_limit_sync(
    max_attempts=RATE_LIMIT_LOGIN['max_attempts'],
    window_seconds=RATE_LIMIT_LOGIN['window_seconds'],
    key_func=lambda req, request=None, **kw: f"{get_client_ip(request)}:login" if request else "login"
)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Autenticación de usuario.
    
    Validaciones:
    - Username/password requeridos
    - Cuenta no debe estar bloqueada
    - Usuario debe existir y estar activo
    - Contraseña debe coincidir
    
    Returns:
        JWT access token + información del usuario
        
    Raises:
        HTTPException 429: Si la cuenta está bloqueada
        HTTPException 401: Si credenciales son incorrectas
    """
    username = req.username.strip().lower()
    
    # Verificar si cuenta está bloqueada
    if is_account_locked(username):
        logger.warning(f"Intento de login bloqueado para {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intenta en 5 minutos."
        )
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(username=username).first()
    
    # Validar usuario existe y está activo
    if not user:
        record_failed_login(username)
        logger.warning(f"Intento de login con usuario inexistente: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas."
        )
    
    if not user.active:
        record_failed_login(username)
        logger.warning(f"Intento de login con usuario bloqueado: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas."
        )
    
    # Validar contraseña (bcrypt)
    if not verify_password(req.password, user.password):
        record_failed_login(username)
        remaining = 5 - len(failed_login_attempts.get(username, []))
        logger.warning(f"Contraseña incorrecta para {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciales incorrectas. Intentos restantes: {max(0, remaining)}"
        )
    
    # Login exitoso: crear tokens y limpiar intentos fallidos
    clear_failed_logins(username)
    
    # Datos para incluir en tokens
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "name": user.name
    }
    
    # Crear access token (corta duración)
    access_token = create_access_token(data=token_data)
    
    # Crear refresh token (larga duración)
    refresh_token = create_refresh_token(data=token_data)
    
    logger.info(f"Login exitoso para {username} (tokens generados)")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "email": user.email,
        }
    )


# ── OBTENER USUARIO ACTUAL ─────────────────────────────
@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado.
    
    Returns:
        Información del usuario actual
    """
    return CurrentUserResponse(
        id=current_user.get("sub"),
        username=current_user.get("username"),
        name=current_user.get("name"),
        role=current_user.get("role"),
        email=current_user.get("email"),
    )


# ── REFRESH TOKEN ──────────────────────────────────────
@router.post("/refresh", response_model=RefreshTokenResponse)
@rate_limit_sync(
    max_attempts=RATE_LIMIT_REFRESH_TOKEN['max_attempts'],
    window_seconds=RATE_LIMIT_REFRESH_TOKEN['window_seconds'],
    key_func=lambda req, request=None, **kw: f"{get_client_ip(request)}:refresh" if request else "refresh"
)
def refresh_access_token(req: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Refrescar access token usando refresh token.
    
    Validaciones:
    - Refresh token debe ser válido y no expirado
    - Refresh token debe ser específicamente de tipo "refresh"
    - Usuario debe existir y estar activo
    
    Args:
        req: Refresh token
        db: Sesión de BD
        
    Returns:
        Nuevo access token
        
    Raises:
        HTTPException 401: Si refresh token es inválido o expirado
        HTTPException 404: Si usuario no existe
    """
    # Validar refresh token
    payload = verify_refresh_token(req.refresh_token)
    
    user_id = payload.get("sub")
    username = payload.get("username")
    
    # Verificar que usuario sigue siendo válido
    user = db.query(UserDB).filter_by(id=user_id, username=username).first()
    
    if not user:
        logger.warning(f"Intento de refresh para usuario no encontrado: {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    if not user.active:
        logger.warning(f"Intento de refresh para usuario inactivo: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo."
        )
    
    # Crear nuevo access token
    new_access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "name": user.name
        }
    )
    
    logger.info(f"Token refrescado para {username}")
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


# ── LOGOUT ─────────────────────────────────────────────
@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout del usuario (limpia sesión en cliente).
    
    Nota: En aplicación stateless, el logout se realiza
    eliminando el token en el cliente. Este endpoint
    sirva como confirmación y para logging de auditoría.
    
    Args:
        current_user: Usuario autenticado (JWT)
        
    Returns:
        Confirmación de logout
    """
    username = current_user.get("username")
    logger.info(f"Logout para {username}")
    
    return {
        "message": "Sesión cerrada correctamente.",
        "logged_out": True
    }


# ── FORGOT PASSWORD ────────────────────────────────────
@router.post("/forgot-password")
@rate_limit_sync(
    max_attempts=RATE_LIMIT_FORGOT_PASSWORD['max_attempts'],
    window_seconds=RATE_LIMIT_FORGOT_PASSWORD['window_seconds'],
    key_func=lambda req, request=None, **kw: f"{get_client_ip(request)}:forgot-password" if request else "forgot-password"
)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Solicitar recuperación de contraseña.
    
    Genera código de 6 dígitos y lo envía por email.
    
    Args:
        req: Username del usuario
        
    Returns:
        Confirmación y email parcialmente enmascarado
    """
    username = req.username.strip().lower()
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(username=username, active=True).first()
    
    if not user:
        # No revelar si el usuario existe o no (seguridad)
        logger.warning(f"Intento de forgot password con usuario inexistente: {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    if not user.email or "@" not in user.email:
        logger.warning(f"Usuario sin email configurado: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuario no tiene email registrado."
        )
    
    # Generar código de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Invalidar códigos anteriores
    db.query(PasswordResetDB).filter_by(username=username, used=False).update({"used": True})
    db.commit()
    
    # Guardar nuevo código
    reset_record = PasswordResetDB(
        id=str(__import__('uuid').uuid4()),
        username=username,
        code=code,
        expires_at=expires_at,
        used=False
    )
    db.add(reset_record)
    db.commit()
    
    # Enviar email
    email_sent = send_password_reset_email(user.email, user.name, code)
    
    if not email_sent:
        logger.error(f"Error enviando email a {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar email. Intenta más tarde."
        )
    
    # Enmascarar email por seguridad
    parts = user.email.split("@")
    masked_email = parts[0][:2] + "***@" + parts[1]
    
    return {
        "message": f"Código enviado a {masked_email}",
        "masked_email": masked_email
    }


# ── VERIFY CODE ────────────────────────────────────────
@router.post("/verify-code")
def verify_code(req: VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    Verificar código de reset.
    
    Args:
        req: Username y código
        
    Returns:
        Confirmación de que el código es válido
        
    Raises:
        HTTPException 400: Si código es inválido o expirado
    """
    username = req.username.strip().lower()
    
    reset_record = db.query(PasswordResetDB).filter_by(
        username=username,
        code=req.code.strip(),
        used=False
    ).order_by(PasswordResetDB.created_at.desc()).first()
    
    if not reset_record:
        logger.warning(f"Código de reset inválido para {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código incorrecto."
        )
    
    if datetime.utcnow() > reset_record.expires_at:
        logger.warning(f"Código expirado para {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código expirado. Solicita uno nuevo."
        )
    
    return {"message": "Código válido", "valid": True}


# ── RESET PASSWORD ─────────────────────────────────────
@router.post("/reset-password")
@rate_limit_sync(
    max_attempts=RATE_LIMIT_RESET_PASSWORD['max_attempts'],
    window_seconds=RATE_LIMIT_RESET_PASSWORD['window_seconds'],
    key_func=lambda req, request=None, **kw: f"{get_client_ip(request)}:reset-password" if request else "reset-password"
)
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Cambiar contraseña con código de reset.
    
    Validaciones:
    - Código debe ser válido y no expirado
    - Contraseñas deben coincidir
    - Nueva contraseña debe cumplir requisitos de seguridad
    
    Args:
        req: Username, código y nueva contraseña
        
    Returns:
        Confirmación de cambio exitoso
    """
    username = req.username.strip().lower()
    
    # Validar código
    reset_record = db.query(PasswordResetDB).filter_by(
        username=username,
        code=req.code.strip(),
        used=False
    ).order_by(PasswordResetDB.created_at.desc()).first()
    
    if not reset_record:
        logger.warning(f"Intento de reset con código inválido: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o ya utilizado."
        )
    
    if datetime.utcnow() > reset_record.expires_at:
        logger.warning(f"Código expirado para reset: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código expirado. Solicita uno nuevo."
        )
    
    # Validar contraseña
    if req.new_password != req.confirm_password:
        logger.warning(f"Contraseñas no coinciden en reset: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden."
        )
    
    # Validar requisitos de seguridad
    validation = validate_password_strength(req.new_password)
    error_msg = get_password_error_message(validation)
    if error_msg:
        logger.warning(f"Contraseña débil en reset: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Actualizar contraseña
    user = db.query(UserDB).filter_by(username=username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    user.password = hash_password(req.new_password)
    reset_record.used = True
    
    db.commit()
    
    logger.info(f"Contraseña resetada para {username}")
    
    return {
        "message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."
    }


# ── CHANGE PASSWORD ────────────────────────────────
@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar contraseña para usuario autenticado.
    
    Validaciones:
    - Usuario debe estar autenticado
    - Contraseña actual debe ser correcta
    - Nueva contraseña debe cumplir requisitos
    - Contraseñas deben coincidir
    
    Args:
        req: Contraseña actual y nueva contraseña
        current_user: Usuario autenticado (desde JWT)
        db: Sesión de BD
        
    Returns:
        Confirmación de cambio exitoso
        
    Raises:
        HTTPException 401: Si contraseña actual es incorrecta
        HTTPException 400: Si validación falla
    """
    username = current_user.get("username")
    user_id = current_user.get("sub")
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(id=user_id, username=username).first()
    
    if not user:
        logger.warning(f"Intento de cambio de contraseña para usuario no encontrado: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado."
        )
    
    # Validar contraseña actual
    if not verify_password(req.current_password, user.password):
        logger.warning(f"Contraseña actual incorrecta en cambio: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta."
        )
    
    # Validar que nueva contraseña es diferente de la actual
    if verify_password(req.new_password, user.password):
        logger.warning(f"Nueva contraseña igual a la actual: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual."
        )
    
    # Actualizar contraseña
    user.password = hash_password(req.new_password)
    db.commit()
    
    logger.info(f"Contraseña cambiada exitosamente para {username}")
    
    return {
        "message": "Contraseña actualizada correctamente."
    }
