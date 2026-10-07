# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Rate Limiting
#  Protección contra brute force y DoS
# ═══════════════════════════════════════════════════════════

import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Tuple
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter simple en memoria.
    
    Usa diccionario para rastrear intentos por IP/usuario.
    Limpia automáticamente entradas expiradas.
    """
    
    def __init__(self):
        # Estructura: {key: [(timestamp, count), ...]}
        self.attempts: Dict[str, list] = defaultdict(list)
        self.last_cleanup = time.time()
    
    def is_allowed(
        self,
        key: str,
        max_attempts: int = 5,
        window_seconds: int = 300
    ) -> Tuple[bool, dict]:
        """
        Verificar si una acción está permitida.
        
        Args:
            key: Identificador único (IP + endpoint o usuario + endpoint)
            max_attempts: Máximo de intentos permitidos
            window_seconds: Ventana de tiempo en segundos
            
        Returns:
            (permitido: bool, info: dict con detalles)
        """
        now = time.time()
        
        # Limpiar entradas expiradas ocasionalmente
        if now - self.last_cleanup > 60:
            self._cleanup(now, window_seconds)
            self.last_cleanup = now
        
        # Remover intentos fuera de la ventana
        self.attempts[key] = [
            (timestamp, count) for timestamp, count in self.attempts[key]
            if now - timestamp < window_seconds
        ]
        
        # Contar intentos actuales
        current_attempts = len(self.attempts[key])
        
        if current_attempts >= max_attempts:
            # Bloqueado
            next_reset = (self.attempts[key][0][0] + window_seconds) - now
            
            logger.warning(
                f"RATE LIMIT: {key} bloqueado | "
                f"Intentos: {current_attempts}/{max_attempts} | "
                f"Reset en {next_reset:.0f}s"
            )
            
            return False, {
                "blocked": True,
                "attempts": current_attempts,
                "max_attempts": max_attempts,
                "reset_seconds": max(int(next_reset), 1),
                "retry_after": max(int(next_reset), 1)
            }
        
        # Permitido - registrar intento
        self.attempts[key].append((now, 1))
        
        return True, {
            "blocked": False,
            "attempts": current_attempts + 1,
            "max_attempts": max_attempts,
            "remaining": max_attempts - (current_attempts + 1)
        }
    
    def _cleanup(self, now: float, window_seconds: int) -> None:
        """Limpiar entradas expiradas para liberar memoria"""
        keys_to_delete = []
        
        for key, attempts in self.attempts.items():
            # Filtrar intentos expirados
            valid_attempts = [
                (timestamp, count) for timestamp, count in attempts
                if now - timestamp < window_seconds
            ]
            
            if not valid_attempts:
                keys_to_delete.append(key)
            else:
                self.attempts[key] = valid_attempts
        
        # Eliminar claves vacías
        for key in keys_to_delete:
            del self.attempts[key]
        
        logger.debug(f"Rate limiter limpieza: {len(keys_to_delete)} claves removidas")


# Instancia global de rate limiter
_rate_limiter = RateLimiter()


def get_client_ip(request) -> str:
    """
    Obtener IP real del cliente.
    
    Considerar proxies:
    - X-Forwarded-For
    - X-Real-IP
    - client address
    
    Args:
        request: Objeto FastAPI Request
        
    Returns:
        IP del cliente
    """
    # Intentar obtener IP real de headers de proxy
    if request.headers.get('x-forwarded-for'):
        return request.headers['x-forwarded-for'].split(',')[0].strip()
    
    if request.headers.get('x-real-ip'):
        return request.headers['x-real-ip']
    
    # Fallback a IP directa
    return request.client.host if request.client else '0.0.0.0'


def rate_limit(
    max_attempts: int = 5,
    window_seconds: int = 300,
    key_func=None
):
    """
    Decorador de rate limiting para endpoints.
    
    Args:
        max_attempts: Máximo de intentos permitidos
        window_seconds: Ventana de tiempo (segundos)
        key_func: Función para generar clave (default: IP del cliente)
        
    Ejemplo:
        @router.post("/login")
        @rate_limit(max_attempts=5, window_seconds=300)
        def login(req: LoginRequest, request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request=None, **kwargs):
            # Obtener clave de rate limit
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                ip = get_client_ip(request) if request else '0.0.0.0'
                endpoint = request.url.path if request else 'unknown'
                key = f"{ip}:{endpoint}"
            
            # Verificar si está permitido
            allowed, info = _rate_limiter.is_allowed(
                key,
                max_attempts=max_attempts,
                window_seconds=window_seconds
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Demasiados intentos. Intenta de nuevo en {info['retry_after']} segundos",
                    headers={
                        "Retry-After": str(info['retry_after']),
                        "X-RateLimit-Limit": str(max_attempts),
                        "X-RateLimit-Remaining": str(0),
                        "X-RateLimit-Reset": str(int(time.time()) + info['retry_after'])
                    }
                )
            
            # Llamar función original
            result = await func(*args, request=request, **kwargs) if hasattr(func, '__await__') else func(*args, request=request, **kwargs)
            
            return result
        
        return wrapper
    return decorator


def rate_limit_sync(
    max_attempts: int = 5,
    window_seconds: int = 300,
    key_func=None
):
    """
    Decorador de rate limiting para funciones sincrónicas.
    
    Idéntico a rate_limit() pero para funciones sync.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, request=None, **kwargs):
            # Obtener clave de rate limit
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                ip = get_client_ip(request) if request else '0.0.0.0'
                endpoint = request.url.path if request else 'unknown'
                key = f"{ip}:{endpoint}"
            
            # Verificar si está permitido
            allowed, info = _rate_limiter.is_allowed(
                key,
                max_attempts=max_attempts,
                window_seconds=window_seconds
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Demasiados intentos. Intenta de nuevo en {info['retry_after']} segundos",
                    headers={
                        "Retry-After": str(info['retry_after']),
                        "X-RateLimit-Limit": str(max_attempts),
                        "X-RateLimit-Remaining": str(0),
                        "X-RateLimit-Reset": str(int(time.time()) + info['retry_after'])
                    }
                )
            
            # Llamar función original
            return func(*args, request=request, **kwargs)
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
# CONFIGURACIONES PREESTABLECIDAS
# ═══════════════════════════════════════════════════════════

# Rate limiting para LOGIN: 5 intentos en 5 minutos
RATE_LIMIT_LOGIN = {
    'max_attempts': 5,
    'window_seconds': 300  # 5 minutos
}

# Rate limiting para FORGOT PASSWORD: 3 intentos en 15 minutos
RATE_LIMIT_FORGOT_PASSWORD = {
    'max_attempts': 3,
    'window_seconds': 900  # 15 minutos
}

# Rate limiting para RESET PASSWORD: 5 intentos en 15 minutos
RATE_LIMIT_RESET_PASSWORD = {
    'max_attempts': 5,
    'window_seconds': 900  # 15 minutos
}

# Rate limiting para REFRESH TOKEN: 20 intentos en 1 minuto
RATE_LIMIT_REFRESH_TOKEN = {
    'max_attempts': 20,
    'window_seconds': 60  # 1 minuto
}

# Rate limiting para CREAR USUARIO: 10 intentos en 1 hora
RATE_LIMIT_CREATE_USER = {
    'max_attempts': 10,
    'window_seconds': 3600  # 1 hora
}


def reset_limit(key: str) -> None:
    """
    Resetear rate limit para una clave (usar con cuidado).
    
    Útil para testing o para liberar usuarios bloqueados.
    
    Args:
        key: Clave a resetear
    """
    if key in _rate_limiter.attempts:
        del _rate_limiter.attempts[key]
        logger.info(f"Rate limit reseteado para: {key}")
