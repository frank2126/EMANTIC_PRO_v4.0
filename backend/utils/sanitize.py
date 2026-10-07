# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Sanitización de Entrada (Prevención XSS)
#  Limpia strings de contenido peligroso
# ═══════════════════════════════════════════════════════════

import re
import html
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_string(
    value: Optional[str],
    max_length: int = 500,
    allow_newlines: bool = False
) -> str:
    """
    Sanitizar string de entrada.
    
    Elimina:
    - Scripts y HTML tags peligrosos
    - Caracteres de control
    - Null bytes
    
    Mantiene:
    - Espacios normales
    - Caracteres Unicode válidos
    - Puntuación normal
    
    Args:
        value: String a sanitizar
        max_length: Longitud máxima permitida
        allow_newlines: Permitir saltos de línea
        
    Returns:
        String sanitizado y limpio
    """
    if not value:
        return ""
    
    # Convertir a string si es necesario
    if not isinstance(value, str):
        value = str(value)
    
    # 1. Remover null bytes (potencial inyección)
    value = value.replace('\x00', '')
    
    # 2. Remover caracteres de control peligrosos
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # 3. Remover tags HTML y scripts
    # Elimina cualquier cosa que se vea como tag HTML
    value = re.sub(r'<[^>]*>', '', value)
    
    # 4. Remover event handlers en atributos (por si acaso)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    
    # 5. Remover javascript: protocol
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'data:text/html', '', value, flags=re.IGNORECASE)
    value = re.sub(r'vbscript:', '', value, flags=re.IGNORECASE)
    
    # 6. Escapar HTML entities para que aparezcan literales si las hay
    # Esto es importante para mostrar "&lt;" como "&lt;" en lugar de "<"
    value = html.escape(value, quote=True)
    
    # 7. Limpiar espacios extras (múltiples espacios)
    value = re.sub(r' +', ' ', value)
    
    # 8. Remover newlines si no están permitidos
    if not allow_newlines:
        value = value.replace('\n', ' ').replace('\r', ' ')
    else:
        # Si se permiten, limpiarlos de caracteres peligrosos
        lines = value.split('\n')
        value = '\n'.join(line.strip() for line in lines if line.strip())
    
    # 9. Limitar longitud
    if len(value) > max_length:
        logger.warning(f"String truncado: {len(value)} > {max_length}")
        value = value[:max_length].rstrip()
    
    # 10. Stripear espacios al inicio y final
    value = value.strip()
    
    return value


def sanitize_username(username: str) -> str:
    """
    Sanitizar username (más restrictivo).
    
    Solo permite:
    - Letras (a-z, A-Z)
    - Números (0-9)
    - Punto (.)
    - Subguión (_)
    
    Args:
        username: Username a sanitizar
        
    Returns:
        Username limpio
    """
    if not username:
        return ""
    
    # Remover caracteres no alfanuméricos (excepto . y _)
    username = re.sub(r'[^a-zA-Z0-9._]', '', username)
    
    # Limitar longitud
    username = username[:100]
    
    return username.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitizar email.
    
    Valida que tenga formato básico de email.
    
    Args:
        email: Email a sanitizar
        
    Returns:
        Email limpio
    """
    if not email:
        return ""
    
    email = email.strip().lower()
    
    # Validar formato básico
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError(f"Email inválido: {email}")
    
    return email


def sanitize_html_safe(value: Optional[str], max_length: int = 1000) -> str:
    """
    Sanitizar para campos que PODRÍAN tener HTML básico.
    
    Permite:
    - Saltos de línea
    - Espacios múltiples
    - Puntuación
    
    Pero NO permite:
    - Scripts
    - Tags HTML peligrosos
    - Event handlers
    
    Args:
        value: Contenido a sanitizar
        max_length: Longitud máxima
        
    Returns:
        Contenido sanitizado
    """
    if not value:
        return ""
    
    # Usar sanitización básica con newlines permitidos
    return sanitize_string(value, max_length=max_length, allow_newlines=True)


def is_safe_string(value: str) -> bool:
    """
    Verificar si un string es seguro (sin XSS).
    
    Retorna False si detecta:
    - Scripts
    - HTML tags
    - Caracteres de control
    - Null bytes
    
    Args:
        value: String a verificar
        
    Returns:
        True si es seguro, False si es sospechoso
    """
    if not isinstance(value, str):
        return False
    
    # Patrones sospechosos
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<embed',
        r'<object',
        r'data:text/html',
        r'vbscript:',
        r'\x00',  # Null byte
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control chars
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return False
    
    return True


def log_xss_attempt(value: str, field: str, username: str = "unknown") -> None:
    """
    Registrar intento de XSS sospechoso.
    
    Args:
        value: Valor sospechoso
        field: Campo donde se intentó
        username: Usuario que lo intentó
    """
    if not is_safe_string(value):
        logger.warning(
            f"SECURITY: Posible intento de XSS detectado | "
            f"Usuario: {username} | Campo: {field} | "
            f"Valor: {value[:100]}..."
        )


# ═══════════════════════════════════════════════════════════
# EJEMPLOS DE USO
# ═══════════════════════════════════════════════════════════

"""
# En schemas o rutas:

from utils.sanitize import sanitize_string, sanitize_username, is_safe_string

# Sanitizar entrada de usuario
@router.post("/users")
def create_user(req: CreateUserRequest, ...):
    # Sanitizar campos
    req.name = sanitize_string(req.name)
    req.email = req.email.lower()  # Ya validado por Pydantic
    
    # Verificar seguridad
    if not is_safe_string(req.name):
        raise HTTPException(400, "Nombre contiene caracteres sospechosos")
    
    # Guardar en BD
    user = UserDB(
        name=req.name,  # Ya sanitizado
        ...
    )

# Antes de retornar (doble protección)
response_data = {
    "name": sanitize_string(user.name),
    "email": user.email,
    ...
}
"""
