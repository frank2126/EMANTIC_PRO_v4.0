# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Dependencias Compartidas
#  Inyección de dependencias para FastAPI
# ═══════════════════════════════════════════════════════════

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Optional

from database import SessionLocal
from security import verify_token

security = HTTPBearer()


def get_db() -> Session:
    """
    Dependencia para obtener sesión de BD.
    Se cierra automáticamente al terminar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependencia para obtener usuario actual desde token JWT.
    
    Args:
        credentials: Credenciales HTTP Bearer
        
    Returns:
        Payload del token (incluye user_id, username, role, etc)
        
    Raises:
        HTTPException 401: Si no hay token o es inválido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales no proporcionadas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    return payload


def get_current_admin_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Dependencia para obtener usuario actual y verificar que sea admin.
    
    Args:
        current_user: Usuario actual (desde get_current_user)
        
    Returns:
        Payload del usuario si es admin
        
    Raises:
        HTTPException 403: Si no es admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de administrador"
        )
    return current_user


def get_current_tecnico_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Dependencia para obtener usuario actual y verificar que sea técnico o admin.
    
    Args:
        current_user: Usuario actual (desde get_current_user)
        
    Returns:
        Payload del usuario si es técnico o admin
        
    Raises:
        HTTPException 403: Si no tiene permisos
    """
    if current_user.get("role") not in ["admin", "tecnico"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de técnico o superior"
        )
    return current_user
