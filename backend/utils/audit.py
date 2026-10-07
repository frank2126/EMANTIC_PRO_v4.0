# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Auditoría de Cambios de Roles
#  Registro centralizado de cambios de autorización
# ═══════════════════════════════════════════════════════════

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from database import RoleAuditDB

logger = logging.getLogger(__name__)


def log_role_change(
    db: Session,
    admin_id: str,
    admin_username: str,
    user_id: str,
    user_username: str,
    old_role: Optional[str],
    new_role: str,
    action: str,
    reason: str = "",
    ip_address: str = ""
) -> RoleAuditDB:
    """
    Registrar cambio de rol en tabla de auditoría.
    
    Parámetros:
        db: Sesión de BD
        admin_id: ID del admin que hizo cambio
        admin_username: Username del admin
        user_id: ID del usuario afectado
        user_username: Username del usuario afectado
        old_role: Rol anterior (None si es creación)
        new_role: Rol nuevo
        action: "CREATE", "UPDATE", "DELETE"
        reason: Razón del cambio (opcional)
        ip_address: IP del admin (opcional)
        
    Returns:
        Registro de auditoría creado
    """
    audit = RoleAuditDB(
        id=str(uuid.uuid4()),
        admin_id=admin_id,
        admin_username=admin_username,
        user_id=user_id,
        user_username=user_username,
        old_role=old_role,
        new_role=new_role,
        action=action,
        reason=reason,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(audit)
    db.commit()
    
    # Log en sistema
    logger.info(
        f"ROLE AUDIT: {action} | Admin: {admin_username}({admin_id}) | "
        f"User: {user_username}({user_id}) | Old: {old_role} | New: {new_role} | "
        f"Reason: {reason}"
    )
    
    return audit


def get_role_audit_log(
    db: Session,
    user_id: Optional[str] = None,
    admin_id: Optional[str] = None,
    days: int = 30,
    limit: int = 100
) -> list:
    """
    Obtener log de auditoría de cambios de roles.
    
    Parámetros:
        db: Sesión de BD
        user_id: Filtrar por usuario afectado
        admin_id: Filtrar por admin que hizo cambio
        days: Últimos N días (default 30)
        limit: Máximo de registros a retornar
        
    Returns:
        Lista de registros de auditoría
    """
    query = db.query(RoleAuditDB)
    
    # Filtro por fecha
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = query.filter(RoleAuditDB.created_at >= since)
    
    # Filtros opcionales
    if user_id:
        query = query.filter(RoleAuditDB.user_id == user_id)
    if admin_id:
        query = query.filter(RoleAuditDB.admin_id == admin_id)
    
    # Ordenar por más reciente primero
    query = query.order_by(RoleAuditDB.created_at.desc())
    
    return query.limit(limit).all()


def format_audit_log(audit: RoleAuditDB) -> dict:
    """
    Formatear registro de auditoría para respuesta.
    
    Args:
        audit: Registro de auditoría
        
    Returns:
        Diccionario formateado
    """
    return {
        "id": audit.id,
        "admin": {
            "id": audit.admin_id,
            "username": audit.admin_username
        },
        "user": {
            "id": audit.user_id,
            "username": audit.user_username
        },
        "change": {
            "action": audit.action,
            "old_role": audit.old_role,
            "new_role": audit.new_role,
            "reason": audit.reason
        },
        "timestamp": audit.created_at.isoformat(),
        "ip_address": audit.ip_address
    }
