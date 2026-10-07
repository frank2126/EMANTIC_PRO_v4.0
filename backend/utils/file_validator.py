# ═══════════════════════════════════════════════════════════════════════════════
#  EMANTIX PRO — FASE 5 — Utilidades de Validación de Archivos
#  Funciones para validar Excel, PDF y otros archivos de forma segura
# ═══════════════════════════════════════════════════════════════════════════════

import os
import hashlib
import logging
from typing import Tuple, Dict, Any
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

# ── CONSTANTES ──────────────────────────────────────────────────────────────

ALLOWED_EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
ALLOWED_EXCEL_MIMES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
    'application/vnd.ms-excel',  # xls
    'text/csv',  # csv
}

ALLOWED_PDF_EXTENSIONS = {'.pdf'}
ALLOWED_PDF_MIMES = {'application/pdf'}

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_EXCEL_ROWS = 1000000  # 1M rows
MAX_EXCEL_COLUMNS = 100
MAX_COLUMNS_TO_DISPLAY = 50

# ── VALIDACIÓN DE EXCEL ────────────────────────────────────────────────────

def validate_excel_file(filename: str, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validar archivo Excel de forma segura.
    
    Validaciones:
    1. Extensión permitida
    2. MIME type correcto
    3. Tamaño dentro de límite
    4. Estructura de archivo válida
    
    Args:
        filename: Nombre del archivo
        file_bytes: Contenido del archivo
        
    Returns:
        (válido, mensaje_error)
    """
    
    # 1. Validar extensión
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXCEL_EXTENSIONS:
        return False, f"Extensión no permitida: {file_ext}. Permitidas: {ALLOWED_EXCEL_EXTENSIONS}"
    
    # 2. Validar tamaño
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return False, f"Archivo demasiado grande: {size_mb:.1f}MB. Máximo: 100MB"
    
    # 3. Validar MIME type
    # Detectar MIME type real (no confiar solo en extensión)
    mime_type = detect_mime_type(file_bytes, filename)
    if mime_type not in ALLOWED_EXCEL_MIMES:
        return False, f"Tipo MIME no permitido: {mime_type}. Se esperaba Excel/CSV"
    
    # 4. Validar estructura (si es XLSX)
    if file_ext == '.xlsx':
        valid, msg = validate_xlsx_structure(file_bytes)
        if not valid:
            return False, msg
    
    # 5. Validar nombre de archivo (sin path traversal)
    if not is_safe_filename(filename):
        return False, "Nombre de archivo contiene caracteres inválidos"
    
    return True, ""


def validate_pdf_file(filename: str, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validar archivo PDF de forma segura.
    
    Validaciones:
    1. Extensión permitida
    2. MIME type correcto
    3. Tamaño dentro de límite
    4. Estructura de PDF válida
    
    Args:
        filename: Nombre del archivo
        file_bytes: Contenido del archivo
        
    Returns:
        (válido, mensaje_error)
    """
    
    # 1. Validar extensión
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_PDF_EXTENSIONS:
        return False, f"Extensión no permitida: {file_ext}. Debe ser .pdf"
    
    # 2. Validar tamaño
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return False, f"Archivo demasiado grande: {size_mb:.1f}MB. Máximo: 100MB"
    
    # 3. Validar MIME type
    mime_type = detect_mime_type(file_bytes, filename)
    if mime_type not in ALLOWED_PDF_MIMES:
        return False, f"Tipo MIME no permitido: {mime_type}. Se esperaba PDF"
    
    # 4. Validar estructura de PDF
    valid, msg = validate_pdf_structure(file_bytes)
    if not valid:
        return False, msg
    
    # 5. Validar nombre de archivo
    if not is_safe_filename(filename):
        return False, "Nombre de archivo contiene caracteres inválidos"
    
    return True, ""


def detect_mime_type(file_bytes: bytes, filename: str) -> str:
    """
    Detectar MIME type real del archivo (magic bytes).
    
    No confía solo en la extensión, valida los primeros bytes.
    
    Returns:
        MIME type detectado
    """
    
    # Verificar magic bytes (primeros bytes del archivo)
    magic_bytes = file_bytes[:4]
    
    # Excel (ZIP magic bytes)
    if magic_bytes.startswith(b'PK\x03\x04'):
        # Podría ser XLSX o Zip bomb
        # Verificar que sea XLSX válido
        if filename.lower().endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            return 'application/zip'  # Potencialmente peligroso
    
    # XLS (Microsoft magic bytes)
    if magic_bytes.startswith(b'\xd0\xcf\x11\xe0'):
        return 'application/vnd.ms-excel'
    
    # PDF
    if file_bytes.startswith(b'%PDF'):
        return 'application/pdf'
    
    # CSV (solo puede ser si la extensión es .csv)
    if filename.lower().endswith('.csv'):
        return 'text/csv'
    
    # Si no detectamos nada, usar mimetypes como fallback
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def validate_xlsx_structure(file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validar estructura interna de archivo XLSX.
    
    Busca detectar:
    - Archivos ZIP corrupto
    - Zip bombs
    - Estructura XLSX inválida
    """
    
    try:
        from openpyxl import load_workbook
        from io import BytesIO
        
        # Intentar cargar el archivo
        workbook = load_workbook(BytesIO(file_bytes), data_only=True)
        
        if not workbook.sheetnames:
            return False, "XLSX no tiene hojas de trabajo"
        
        return True, ""
    
    except Exception as e:
        logger.error(f"Error validando XLSX: {str(e)}")
        return False, f"XLSX corrupto o inválido: {type(e).__name__}"


def validate_pdf_structure(file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validar estructura de PDF.
    
    Verifica:
    - PDF válido
    - No corrupto
    """
    
    try:
        # Verificar que empieza con %PDF
        if not file_bytes.startswith(b'%PDF'):
            return False, "No es un PDF válido (no contiene magic bytes)"
        
        # Verificar que contiene EOF
        if b'%%EOF' not in file_bytes:
            return False, "PDF no está completo (falta %%EOF)"
        
        # Intentar leer con librería PDF si disponible
        try:
            import PyPDF2
            from io import BytesIO
            reader = PyPDF2.PdfReader(BytesIO(file_bytes))
            # Solo verificar que se puede leer
            _ = len(reader.pages)
        except ImportError:
            # PyPDF2 no disponible, solo hacemos validación básica
            pass
        except Exception as e:
            logger.error(f"Error validando PDF: {str(e)}")
            return False, f"PDF corrupto o inválido: {type(e).__name__}"
        
        return True, ""
    
    except Exception as e:
        logger.error(f"Error en validación de PDF: {str(e)}")
        return False, f"Error al validar PDF: {type(e).__name__}"


def is_safe_filename(filename: str) -> bool:
    """
    Verificar que el nombre de archivo no contiene path traversal.
    
    Detecta:
    - ../
    - ..\\
    - Caracteres inválidos
    - Nombres reservados (CON, PRN, AUX, etc en Windows)
    """
    
    # Caracteres peligrosos
    dangerous_chars = {'..', '/', '\\', '\0', '\n', '\r', '\t'}
    
    # Verificar path traversal
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Verificar nombres reservados de Windows
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                     'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                     'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False
    
    # Máximo 255 caracteres
    if len(filename) > 255:
        return False
    
    return True


def generate_safe_filename(original_filename: str) -> str:
    """
    Generar nombre de archivo seguro a partir del original.
    
    - Usa UUID para evitar colisiones
    - Preserva extensión
    - Sanitiza caracteres
    """
    
    import uuid
    from pathlib import Path
    
    # Obtener extensión
    ext = Path(original_filename).suffix.lower()
    
    # Generar nombre aleatorio
    safe_name = f"{uuid.uuid4()}{ext}"
    
    return safe_name


def calculate_file_hash(file_bytes: bytes) -> str:
    """
    Calcular hash SHA256 del archivo para detectar duplicados.
    
    Returns:
        Hash SHA256 en formato hex
    """
    return hashlib.sha256(file_bytes).hexdigest()


def validate_excel_structure(headers: list, rows_count: int) -> Tuple[bool, str]:
    """
    Validar estructura de datos de Excel.
    
    Args:
        headers: Lista de encabezados
        rows_count: Cantidad de filas
        
    Returns:
        (válido, mensaje_error)
    """
    
    # Validar cantidad de columnas
    if len(headers) > MAX_EXCEL_COLUMNS:
        return False, f"Demasiadas columnas: {len(headers)}. Máximo: {MAX_EXCEL_COLUMNS}"
    
    # Validar cantidad de filas
    if rows_count > MAX_EXCEL_ROWS:
        return False, f"Demasiadas filas: {rows_count}. Máximo: {MAX_EXCEL_ROWS}"
    
    # Validar que hay al menos 1 columna
    if len(headers) == 0:
        return False, "Excel no tiene columnas"
    
    # Validar que no hay encabezados duplicados
    if len(headers) != len(set(headers)):
        return False, "Excel tiene encabezados duplicados"
    
    return True, ""


def validate_required_columns(headers: list, required_columns: list) -> Tuple[bool, list]:
    """
    Validar que las columnas obligatorias están presentes.
    
    Args:
        headers: Lista de encabezados del Excel
        required_columns: Lista de columnas requeridas
        
    Returns:
        (válido, columnas_faltantes)
    """
    
    headers_lower = [h.lower().strip() if h else '' for h in headers]
    required_lower = [c.lower().strip() for c in required_columns]
    
    missing = [col for col in required_lower if col not in headers_lower]
    
    return len(missing) == 0, missing


# ── DETECCIÓN DE DUPLICADOS ────────────────────────────────────────────────

def find_duplicate_rows(rows: list, key_fields: list) -> Tuple[list, list]:
    """
    Encontrar filas duplicadas dentro del archivo.
    
    Args:
        rows: Lista de diccionarios (filas)
        key_fields: Campos que definen la unicidad
        
    Returns:
        (filas_únicas, índices_duplicados)
    """
    
    seen = {}
    unique_rows = []
    duplicate_indices = []
    
    for idx, row in enumerate(rows):
        # Crear clave compuesta
        key = tuple(row.get(field, '') for field in key_fields)
        
        if key in seen:
            duplicate_indices.append(idx)
        else:
            seen[key] = idx
            unique_rows.append(row)
    
    return unique_rows, duplicate_indices


# ── LOGGING Y AUDITORÍA ────────────────────────────────────────────────────

def log_file_upload(username: str, filename: str, file_size: int, file_type: str, status: str):
    """
    Registrar auditoría de upload de archivo.
    
    Args:
        username: Usuario que subió el archivo
        filename: Nombre original del archivo
        file_size: Tamaño en bytes
        file_type: Tipo (excel, pdf, etc)
        status: Resultado (success, failed, rejected)
    """
    
    size_mb = file_size / (1024 * 1024)
    logger.info(
        f"FILE_UPLOAD | user={username} | type={file_type} | "
        f"size={size_mb:.1f}MB | status={status} | filename={filename}"
    )
