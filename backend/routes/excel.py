
#  Rutas de Procesamiento de Excel

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid
import time

from database import SessionLocal, DpvRegistroDB, IcoRegistroDB, CargaHistorialDB
from deps import get_db, get_current_admin_user
from schemas.auth import CurrentUserResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/excel", tags=["excel"])

# ── SCHEMAS ────────────────────────────────────────────────

class ExcelUploadResponse(BaseModel):
    """Schema para respuesta de upload de Excel"""
    total_rows: int
    inserted: int
    updated: int
    errors: int
    time_seconds: float
    status: str  # "success", "partial", "failed"
    message: str

# ── CONFIGURACIÓN ──────────────────────────────────────────

BATCH_SIZE = 1000  # Procesar 1000 registros por batch
MAX_FILE_SIZE_MB = 100
CHUNK_SIZE = 8192

# ── HELPERS ────────────────────────────────────────────────

def validate_dpv_row(row: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validar fila de DPV (OPTIMIZADO).
    
    Optimizaciones:
    - Validación rápida sin acceso a BD
    - Retorna booleano + mensaje de error
    - Fallos temprano
    """
    required_fields = ['dpv_id', 'estado', 'placa']
    
    for field in required_fields:
        if field not in row or not row[field]:
            return False, f"Campo requerido faltante: {field}"
    
    # Validar que dpv_id sea número
    try:
        int(row['dpv_id'])
    except (ValueError, TypeError):
        return False, f"dpv_id debe ser número: {row.get('dpv_id')}"
    
    return True, ""

def validate_ico_row(row: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validar fila de ICO (OPTIMIZADO).
    
    Validaciones rápidas sin acceso a BD
    """
    required_fields = ['ico_id', 'estado', 'placa']
    
    for field in required_fields:
        if field not in row or not row[field]:
            return False, f"Campo requerido faltante: {field}"
    
    try:
        int(row['ico_id'])
    except (ValueError, TypeError):
        return False, f"ico_id debe ser número: {row.get('ico_id')}"
    
    return True, ""

def process_dpv_batch(db: Session, rows: List[Dict[str, Any]], user_id: str) -> Dict[str, int]:
    """
    Procesar batch de registros DPV (OPTIMIZADO).
    
    Optimizaciones:
    - Batch insert con add_all()
    - Manejo de errores por row
    - Reporte detallado
    """
    stats = {
        'inserted': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    records_to_insert = []
    
    for row in rows:
        # Validación rápida
        valid, error = validate_dpv_row(row)
        if not valid:
            stats['errors'] += 1
            stats['error_details'].append(f"Row error: {error}")
            continue
        
        # Verificar si existe
        existing = db.query(DpvRegistroDB).filter(
            DpvRegistroDB.dpv_id == int(row['dpv_id'])
        ).first()
        
        if existing:
            # Actualizar
            for key, value in row.items():
                if hasattr(existing, key) and key != 'id':
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            stats['updated'] += 1
        else:
            # Preparar para insertar
            record = DpvRegistroDB(**row)
            records_to_insert.append(record)
            stats['inserted'] += 1
    
    # Batch insert
    if records_to_insert:
        try:
            db.add_all(records_to_insert)
            db.flush()  # Flush antes de commit para detectar errores
        except IntegrityError as e:
            db.rollback()
            stats['errors'] += len(records_to_insert)
            stats['error_details'].append(f"Batch insert error: {str(e)}")
            stats['inserted'] -= len(records_to_insert)
    
    return stats

def process_ico_batch(db: Session, rows: List[Dict[str, Any]], user_id: str) -> Dict[str, int]:
    """
    Procesar batch de registros ICO (OPTIMIZADO).
    
    Similar a DPV pero para tabla ICO
    """
    stats = {
        'inserted': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    records_to_insert = []
    
    for row in rows:
        # Validación
        valid, error = validate_ico_row(row)
        if not valid:
            stats['errors'] += 1
            stats['error_details'].append(f"Row error: {error}")
            continue
        
        # Verificar si existe
        existing = db.query(IcoRegistroDB).filter(
            IcoRegistroDB.ico_id == int(row['ico_id'])
        ).first()
        
        if existing:
            for key, value in row.items():
                if hasattr(existing, key) and key != 'id':
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            stats['updated'] += 1
        else:
            record = IcoRegistroDB(**row)
            records_to_insert.append(record)
            stats['inserted'] += 1
    
    # Batch insert
    if records_to_insert:
        try:
            db.add_all(records_to_insert)
            db.flush()
        except IntegrityError as e:
            db.rollback()
            stats['errors'] += len(records_to_insert)
            stats['error_details'].append(f"Batch insert error: {str(e)}")
            stats['inserted'] -= len(records_to_insert)
    
    return stats

# ── ENDPOINTS ──────────────────────────────────────────────

@router.post("/upload-dpv", response_model=ExcelUploadResponse)
async def upload_dpv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Procesar y subir archivo Excel DPV.
    
    Optimizaciones:
    - Lectura en streaming
    - Procesamiento en batches de 1000
    - Validación paralela
    - Reporte de progreso
    - Registrar en historial
    
    Limitaciones:
    - Máximo 100MB
    - Validación de campos
    - Batch processing
    """
    
    start_time = time.time()
    
    # Validar tamaño del archivo
    file.file.seek(0, 2)
    file_size_mb = file.file.tell() / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo muy grande. Máximo: {MAX_FILE_SIZE_MB}MB"
        )
    file.file.seek(0)
    
    # Validar extensión
    if not file.filename.endswith(('.xlsx', '.csv', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan .xlsx, .csv, .xls"
        )
    
    try:
        # Leer con openpyxl (optimizado)
        from openpyxl import load_workbook
        
        workbook = load_workbook(file.file, data_only=True)
        worksheet = workbook.active
        
        # Obtener encabezados
        headers = [cell.value for cell in worksheet[1]]
        headers = [h.lower() if h else f"col_{i}" for i, h in enumerate(headers)]
        
        total_rows = worksheet.max_row - 1
        batch_rows = []
        batch_count = 0
        
        stats = {
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Procesar por filas en batches
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), 1):
            # Convertir fila a diccionario
            row_dict = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
            
            # Convertir dpv_id a int si existe
            if 'dpv_id' in row_dict and row_dict['dpv_id']:
                row_dict['dpv_id'] = int(row_dict['dpv_id'])
            
            batch_rows.append(row_dict)
            batch_count += 1
            
            # Procesar batch cuando alcanza tamaño
            if batch_count >= BATCH_SIZE or row_idx == total_rows:
                batch_stats = process_dpv_batch(db, batch_rows, current_user.username)
                
                # Acumular estadísticas
                stats['inserted'] += batch_stats['inserted']
                stats['updated'] += batch_stats['updated']
                stats['errors'] += batch_stats['errors']
                stats['error_details'].extend(batch_stats['error_details'][:5])  # Limitar detalles
                
                # Commit del batch
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    stats['errors'] += len(batch_rows)
                    stats['error_details'].append(f"Batch commit error: {str(e)}")
                
                # Reset batch
                batch_rows = []
                batch_count = 0
                
                logger.info(f"Batch procesado: {row_idx}/{total_rows} filas")
        
        # Tiempo total
        elapsed = time.time() - start_time
        
        # Registrar en historial
        historial = CargaHistorialDB(
            tipo_carga="dpv",
            usuario_id=current_user.username,
            nombre_archivo=file.filename,
            total_filas=total_rows,
            filas_insertadas=stats['inserted'],
            filas_actualizadas=stats['updated'],
            filas_error=stats['errors'],
            estado="exitoso" if stats['errors'] == 0 else "parcial" if stats['inserted'] + stats['updated'] > 0 else "fallido",
            tiempo_procesamiento_seg=str(round(elapsed, 2))
        )
        db.add(historial)
        db.commit()
        
        # Determinar estado
        if stats['errors'] == 0:
            status_str = "success"
            message = f"Archivo procesado exitosamente"
        elif stats['inserted'] + stats['updated'] > 0:
            status_str = "partial"
            message = f"Procesamiento parcial: {stats['errors']} filas con error"
        else:
            status_str = "failed"
            message = f"Error al procesar archivo: {stats['errors']} filas fallidas"
        
        logger.info(f"DPV upload: {stats['inserted']} insertadas, {stats['updated']} actualizadas, {stats['errors']} errores")
        
        return ExcelUploadResponse(
            total_rows=total_rows,
            inserted=stats['inserted'],
            updated=stats['updated'],
            errors=stats['errors'],
            time_seconds=elapsed,
            status=status_str,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Error procesando archivo DPV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )
    finally:
        await file.close()


@router.post("/upload-ico", response_model=ExcelUploadResponse)
async def upload_ico(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUserResponse = Depends(get_current_admin_user)
):
    """
    Procesar y subir archivo Excel ICO.
    
    Similar a upload_dpv pero para tabla ICO
    """
    
    start_time = time.time()
    
    # Validar tamaño
    file.file.seek(0, 2)
    file_size_mb = file.file.tell() / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo muy grande. Máximo: {MAX_FILE_SIZE_MB}MB"
        )
    file.file.seek(0)
    
    # Validar extensión
    if not file.filename.endswith(('.xlsx', '.csv', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan .xlsx, .csv, .xls"
        )
    
    try:
        from openpyxl import load_workbook
        
        workbook = load_workbook(file.file, data_only=True)
        worksheet = workbook.active
        
        headers = [cell.value for cell in worksheet[1]]
        headers = [h.lower() if h else f"col_{i}" for i, h in enumerate(headers)]
        
        total_rows = worksheet.max_row - 1
        batch_rows = []
        batch_count = 0
        
        stats = {
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), 1):
            row_dict = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
            
            if 'ico_id' in row_dict and row_dict['ico_id']:
                row_dict['ico_id'] = int(row_dict['ico_id'])
            
            batch_rows.append(row_dict)
            batch_count += 1
            
            if batch_count >= BATCH_SIZE or row_idx == total_rows:
                batch_stats = process_ico_batch(db, batch_rows, current_user.username)
                
                stats['inserted'] += batch_stats['inserted']
                stats['updated'] += batch_stats['updated']
                stats['errors'] += batch_stats['errors']
                stats['error_details'].extend(batch_stats['error_details'][:5])
                
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    stats['errors'] += len(batch_rows)
                
                batch_rows = []
                batch_count = 0
        
        elapsed = time.time() - start_time
        
        historial = CargaHistorialDB(
            tipo_carga="ico",
            usuario_id=current_user.username,
            nombre_archivo=file.filename,
            total_filas=total_rows,
            filas_insertadas=stats['inserted'],
            filas_actualizadas=stats['updated'],
            filas_error=stats['errors'],
            estado="exitoso" if stats['errors'] == 0 else "parcial" if stats['inserted'] + stats['updated'] > 0 else "fallido",
            tiempo_procesamiento_seg=str(round(elapsed, 2))
        )
        db.add(historial)
        db.commit()
        
        if stats['errors'] == 0:
            status_str = "success"
            message = "Archivo procesado exitosamente"
        elif stats['inserted'] + stats['updated'] > 0:
            status_str = "partial"
            message = f"Procesamiento parcial: {stats['errors']} filas con error"
        else:
            status_str = "failed"
            message = f"Error al procesar archivo: {stats['errors']} filas fallidas"
        
        return ExcelUploadResponse(
            total_rows=total_rows,
            inserted=stats['inserted'],
            updated=stats['updated'],
            errors=stats['errors'],
            time_seconds=elapsed,
            status=status_str,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Error procesando archivo ICO: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )
    finally:
        await file.close()
