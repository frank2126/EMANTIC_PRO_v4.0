# ═══════════════════════════════════════════════════════════════════════════════
#  EMANTIX PRO — FASE 9 — Logging Estructurado
#  Sistema de logs JSON con seguridad y sin datos sensibles
# ═══════════════════════════════════════════════════════════════════════════════

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from functools import wraps
from logging.handlers import RotatingFileHandler
import os

# ── CONFIGURACIÓN DE LOGGING ───────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Formateador que convierte logs a JSON estructurado"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Agregar excepción si existe
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Agregar datos contextuales si existen
        if hasattr(record, 'context'):
            log_obj['context'] = record.context
        
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """
    Configurar logging estructurado
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar logs (opcional)
    
    Returns:
        Logger configurado
    """
    
    logger = logging.getLogger('emantic')
    logger.setLevel(getattr(logging, log_level))
    
    # Limpiar handlers existentes
    logger.handlers = []
    
    # ── HANDLER: CONSOLE ───────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = JSONFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ── HANDLER: ARCHIVO (ROTATING) ────────────────────────────────────
    if log_file:
        # Crear directorio si no existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=100_000_000,  # 100MB
            backupCount=14,         # Guardar 14 archivos (2 semanas)
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# ── LOGGER GLOBAL ──────────────────────────────────────────────────────────

logger = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    log_file=os.getenv('LOG_FILE', '/var/log/emantic/backend.log')
)


# ── FUNCIONES DE LOGGING CON CONTEXTO ──────────────────────────────────────

def log_with_context(log_func, message: str, context: Dict[str, Any] = None, **kwargs):
    """Registrar log con contexto adicional (sin datos sensibles)"""
    record = logging.makeLogRecord({
        'msg': message,
        'level': logging.INFO,
        **kwargs
    })
    if context:
        record.context = context
    log_func(message, extra={'context': context} if context else {})


def log_user_action(action: str, user_id: int, resource: str, details: Dict = None):
    """Registrar acciones de usuario para auditoría"""
    context = {
        'action': action,
        'user_id': user_id,
        'resource': resource,
        'timestamp': datetime.utcnow().isoformat(),
    }
    if details:
        context['details'] = details
    
    logger.info(f"User action: {action} on {resource}", extra={'context': context})


def log_security_event(event_type: str, details: Dict, severity: str = 'WARNING'):
    """Registrar eventos de seguridad"""
    context = {
        'event_type': event_type,
        'severity': severity,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details
    }
    
    level = getattr(logging, severity, logging.WARNING)
    logger.log(level, f"Security event: {event_type}", extra={'context': context})


def log_performance(operation: str, duration_ms: float, success: bool, details: Dict = None):
    """Registrar métrica de performance"""
    context = {
        'operation': operation,
        'duration_ms': round(duration_ms, 2),
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
    }
    if details:
        context['details'] = details
    
    logger.info(f"Performance: {operation} ({duration_ms:.2f}ms)", extra={'context': context})


def log_database_operation(operation: str, table: str, rows_affected: int = None):
    """Registrar operación de base de datos"""
    context = {
        'operation': operation,
        'table': table,
        'rows_affected': rows_affected,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    logger.info(f"DB operation: {operation} on {table}", extra={'context': context})


# ── DECORADORES PARA LOGGING ───────────────────────────────────────────────

def log_endpoint_access(func):
    """Decorador para registrar acceso a endpoints"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import time
        from fastapi import Request
        
        # Extraer request si está disponible
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            if request:
                context = {
                    'method': request.method,
                    'path': request.url.path,
                    'status': 200,
                    'duration_ms': round(duration_ms, 2),
                }
                logger.info(f"Endpoint: {request.method} {request.url.path}", extra={'context': context})
            
            return result
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            if request:
                context = {
                    'method': request.method,
                    'path': request.url.path,
                    'error': str(e),
                    'duration_ms': round(duration_ms, 2),
                }
                logger.error(f"Endpoint error: {request.method} {request.url.path}", extra={'context': context})
            
            raise
    
    return wrapper


def log_performance_decorator(operation_name: str):
    """Decorador para medir performance de operaciones"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, True)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, False, {'error': str(e)})
                raise
        
        return wrapper
    return decorator


# ── EXPORTAR ───────────────────────────────────────────────────────────────

__all__ = [
    'logger',
    'setup_logging',
    'log_with_context',
    'log_user_action',
    'log_security_event',
    'log_performance',
    'log_database_operation',
    'log_endpoint_access',
    'log_performance_decorator',
]
