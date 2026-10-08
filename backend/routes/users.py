
# Rutas de Gestión de Usuarios
#  CRUD de usuarios (solo admin)


from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

from database import UserDB, SessionLocal
from security import hash_password, validate_username, validate_password_strength, get_password_error_message
from deps import get_db, get_current_admin_user
from utils.rate_limit import rate_limit_sync, RATE_LIMIT_CREATE_USER, get_client_ip
from schemas.auth import CreateUserRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


# ── LISTAR USUARIOS ────────────────────────────────────
@router.get("")
def list_users(db: Session = Depends(get_db), admin=Depends(get_current_admin_user)):
    """
    Listar todos los usuarios.
    Solo acceso admin.
    
    Returns:
        Lista de usuarios
    """
    users = db.query(UserDB).order_by(UserDB.created_at).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "active": u.active,
            "created_at": str(u.created_at)
        }
        for u in users
    ]


# ── CREAR USUARIO ──────────────────────────────────────
@router.post("")
@rate_limit_sync(
    max_attempts=RATE_LIMIT_CREATE_USER['max_attempts'],
    window_seconds=RATE_LIMIT_CREATE_USER['window_seconds'],
    key_func=lambda req, db=None, request=None, admin=None, **kw: f"{admin.get('username')}:create_user" if admin else "create_user"
)
def create_user(
    req: CreateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    """
    Crear nuevo usuario.
    Solo acceso admin.
    
    Validaciones:
    - Username único
    - Contraseña segura
    - Email válido (si se proporciona)
    - Rol válido (admin o tecnico)
    
    Args:
        req: Datos del nuevo usuario
        
    Returns:
        Confirmación de creación
        
    Raises:
        HTTPException 400: Si validación falla
        HTTPException 409: Si username ya existe
    """
    from utils.audit import log_role_change
    
    # Verificar username único
    if db.query(UserDB).filter_by(username=req.username.lower()).first():
        logger.warning(f"Intento de crear usuario con username duplicado: {req.username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{req.username}' ya existe."
        )
    
    # Crear usuario
    user_id = str(uuid.uuid4())
    new_user = UserDB(
        id=user_id,
        username=req.username.lower(),
        password=hash_password(req.password),
        name=req.name,
        email=req.email or "",
        role=req.role,
        active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Registrar en auditoría
    log_role_change(
        db=db,
        admin_id=admin.get("sub"),
        admin_username=admin.get("username"),
        user_id=user_id,
        user_username=req.username.lower(),
        old_role=None,  # Es creación
        new_role=req.role,
        action="CREATE",
        reason=f"Creación de nuevo usuario: {req.name}"
    )
    
    logger.info(f"Usuario creado: {req.username} con rol {req.role} por {admin.get('username')}")
    
    return {
        "message": f"Usuario '{req.username}' creado exitosamente con rol '{req.role}'",
        "user_id": new_user.id
    }


# ── CAMBIAR ROL DE USUARIO ─────────────────────────────
@router.patch("/{username}/role")
def change_user_role(
    username: str,
    new_role: str = Query(..., regex="^(admin|tecnico)$"),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    """
    Cambiar rol de usuario.
    Solo acceso admin.
    
    No permite cambiar rol del admin principal.
    
    Args:
        username: Username del usuario
        new_role: Nuevo rol ("admin" o "tecnico")
        
    Returns:
        Confirmación del cambio
    """
    from utils.audit import log_role_change
    
    username = username.lower()
    
    # Proteger admin principal
    if username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar el rol del admin principal."
        )
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(username=username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    old_role = user.role
    
    # No permitir cambio innecesario
    if old_role == new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario ya tiene rol '{new_role}'"
        )
    
    # Cambiar rol
    user.role = new_role
    db.commit()
    
    # Registrar en auditoría
    log_role_change(
        db=db,
        admin_id=admin.get("sub"),
        admin_username=admin.get("username"),
        user_id=user.id,
        user_username=username,
        old_role=old_role,
        new_role=new_role,
        action="UPDATE",
        reason=f"Cambio de rol de {old_role} a {new_role}"
    )
    
    logger.info(f"Rol cambió para {username}: {old_role} → {new_role} por {admin.get('username')}")
    
    return {
        "message": f"Rol de '{username}' cambió de '{old_role}' a '{new_role}'",
        "old_role": old_role,
        "new_role": new_role
    }


# ── ACTIVAR/BLOQUEAR USUARIO ───────────────────────────
@router.patch("/{username}/toggle")
def toggle_user_status(
    username: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    """
    Activar o bloquear un usuario.
    Solo acceso admin.
    
    No permite bloquear al admin principal.
    
    Args:
        username: Username del usuario a modificar
        
    Returns:
        Confirmación del cambio
    """
    from utils.audit import log_role_change
    
    username = username.lower()
    
    # Proteger admin principal
    if username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes modificar al admin principal."
        )
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(username=username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    old_active = user.active
    
    # Toggle
    user.active = not user.active
    db.commit()
    
    status_msg = "activado" if user.active else "bloqueado"
    
    # Registrar en auditoría
    log_role_change(
        db=db,
        admin_id=admin.get("sub"),
        admin_username=admin.get("username"),
        user_id=user.id,
        user_username=username,
        old_role=user.role,
        new_role=user.role,
        action="UPDATE",
        reason=f"Usuario {status_msg}"
    )
    
    logger.info(f"Usuario {username} {status_msg} por {admin.get('username')}")
    
    return {
        "message": f"Usuario '{username}' {status_msg}",
        "active": user.active
    }


# ── ELIMINAR USUARIO ───────────────────────────────────
@router.delete("/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    """
    Eliminar un usuario.
    Solo acceso admin.
    
    No permite eliminar al admin principal.
    
    Args:
        username: Username del usuario a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    from utils.audit import log_role_change
    
    username = username.lower()
    
    # Proteger admin principal
    if username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar al admin principal."
        )
    
    # Buscar usuario
    user = db.query(UserDB).filter_by(username=username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    # Registrar en auditoría ANTES de eliminar
    log_role_change(
        db=db,
        admin_id=admin.get("sub"),
        admin_username=admin.get("username"),
        user_id=user.id,
        user_username=username,
        old_role=user.role,
        new_role=None,  # Se eliminó
        action="DELETE",
        reason=f"Usuario eliminado"
    )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Usuario eliminado: {username} por {admin.get('username')}")
    
    return {"message": f"Usuario '{username}' eliminado"}


# ── VER AUDITORÍA DE CAMBIOS ───────────────────────────
@router.get("/audit/log")
def get_audit_log(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
    user_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Ver log de auditoría de cambios de roles.
    Solo acceso admin.
    
    Query Parameters:
    - user_id: Filtrar por usuario afectado (opcional)
    - days: Últimos N días (default 30)
    - limit: Máximo de registros (default 100)
    
    Returns:
        Lista de cambios de roles registrados
    """
    from utils.audit import get_role_audit_log, format_audit_log
    
    audits = get_role_audit_log(
        db=db,
        user_id=user_id,
        admin_id=None,
        days=days,
        limit=limit
    )
    
    return {
        "total": len(audits),
        "audits": [format_audit_log(audit) for audit in audits]
    }
