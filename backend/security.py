# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Módulo de Seguridad
#  JWT, Hashing de contraseñas, validación
# ═══════════════════════════════════════════════════════════

import jwt
import bcrypt
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import HTTPException, status
from config import settings


# ── CONTRASEÑAS ────────────────────────────────────────
def hash_password(password: str) -> str:
    """
    Hashear contraseña con bcrypt.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash bcrypt (incluye salt)
    """
    if not password or len(password) < settings.password_min_length:
        raise ValueError(f"Contraseña debe tener mínimo {settings.password_min_length} caracteres")
    
    salt = bcrypt.gensalt(rounds=12)  # rounds=12 es seguro y razonablemente rápido
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verificar contraseña contra hash bcrypt.
    
    Args:
        password: Contraseña en texto plano
        hashed_password: Hash bcrypt almacenado
        
    Returns:
        True si coinciden, False si no
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def validate_password_strength(password: str) -> Dict[str, bool]:
    """
    Validar requisitos de seguridad de contraseña.
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Dict con resultados de validación
    """
    validation = {
        "length": len(password) >= settings.password_min_length,
        "uppercase": any(c.isupper() for c in password) if settings.password_require_uppercase else True,
        "number": any(c.isdigit() for c in password) if settings.password_require_number else True,
        "special": any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password) if settings.password_require_special else True,
    }
    
    return validation


def get_password_error_message(validation: Dict[str, bool]) -> Optional[str]:
    """
    Obtener mensaje de error específico de validación.
    
    Args:
        validation: Resultado de validate_password_strength
        
    Returns:
        Mensaje de error o None si es válida
    """
    if not validation["length"]:
        return f"La contraseña debe tener al menos {settings.password_min_length} caracteres"
    if not validation["uppercase"]:
        return "La contraseña debe tener al menos una letra mayúscula"
    if not validation["number"]:
        return "La contraseña debe tener al menos un número"
    if not validation["special"]:
        return "La contraseña debe tener al menos un carácter especial"
    return None


# ── JWT ────────────────────────────────────────────────
def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crear JWT access token.
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": user_id})
        expires_delta: Tiempo de expiración personalizado
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear token"
        )


def create_refresh_token(data: Dict) -> str:
    """
    Crear JWT refresh token (válido más tiempo).
    
    Args:
        data: Datos a incluir en el token
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear refresh token"
        )


def verify_token(token: str) -> Dict:
    """
    Verificar y decodificar JWT token (access o refresh).
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Payload del token decodificado
        
    Raises:
        HTTPException: Si token es inválido o expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Por favor, inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al validar token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> Dict:
    """
    Verificar y decodificar JWT refresh token.
    
    Valida que el token sea específicamente de tipo "refresh".
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Payload del token decodificado
        
    Raises:
        HTTPException: Si token es inválido, expirado o no es refresh token
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Verificar que es un refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido. Debe usar un refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado. Por favor, inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al validar refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── EMAIL ──────────────────────────────────────────────
def validate_email(email: str) -> bool:
    """
    Validar formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True si es válido, False si no
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ── USERNAME ───────────────────────────────────────────
def validate_username(username: str) -> bool:
    """
    Validar formato de username.
    Permitir: letras, números, puntos, guiones, guiones bajos
    
    Args:
        username: Username a validar
        
    Returns:
        True si es válido, False si no
    """
    if len(username) < 3 or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9._-]+$'
    return re.match(pattern, username) is not None
