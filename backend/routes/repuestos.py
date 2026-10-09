"""
EMANTIC PRO - Repuestos Router
Gestión de repuestos/piezas con búsqueda rápida y carga desde Excel
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from database import get_db, RepuestoDB
import openpyxl
from datetime import datetime

router = APIRouter(prefix="/api/repuestos", tags=["repuestos"])

# ═══════════════════════════════════════════════════════════
# GET - Listar Todos los Repuestos (Con Paginación)
# ═══════════════════════════════════════════════════════════

@router.get("/")
async def get_repuestos(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtener lista de repuestos con paginación
    Por defecto retorna 50 repuestos
    """
    try:
        repuestos = (
            db.query(RepuestoDB)
            .filter_by(activo=True)
            .order_by(RepuestoDB.pieza.asc())  # Ordenar por código
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        total = db.query(RepuestoDB).filter_by(activo=True).count()
        
        # Convertir a dicts
        result = [_repuesto_to_dict(r) for r in repuestos]
        
        return {
            "success": True,
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Búsqueda Rápida (⚡ LO MÁS IMPORTANTE)
# ═══════════════════════════════════════════════════════════

@router.get("/search/{query}")
async def search_repuestos(
    query: str,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Búsqueda RÁPIDA de repuestos
    Busca en: Código (Pieza), Descripción, Clase, Nivel de sistema
    
    Ejemplo: /api/repuestos/search/tornillo?limit=30
    """
    try:
        # Búsqueda case-insensitive y flexible
        search_term = f"%{query}%"
        
        repuestos = (
            db.query(RepuestoDB)
            .filter(
                and_(
                    RepuestoDB.activo == True,
                    or_(
                        RepuestoDB.pieza.ilike(search_term),  # Código
                        RepuestoDB.descripcion.ilike(search_term),  # Descripción
                        RepuestoDB.clase.ilike(search_term),  # Clase
                        RepuestoDB.nivel_sistema.ilike(search_term),  # Nivel sistema
                        RepuestoDB.numero_pieza_fabricante.ilike(search_term)  # Número fabricante
                    )
                )
            )
            .order_by(
                # Priorizar coincidencias exactas en código
                RepuestoDB.pieza.startswith(query),
                RepuestoDB.pieza.asc()
            )
            .limit(limit)
            .all()
        )
        
        result = [_repuesto_to_dict(r) for r in repuestos]
        
        return {
            "success": True,
            "data": result,
            "count": len(result),
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Obtener Repuesto por Código
# ═══════════════════════════════════════════════════════════

@router.get("/codigo/{pieza_codigo}")
async def get_repuesto_por_codigo(pieza_codigo: str, db: Session = Depends(get_db)):
    """
    Obtener un repuesto específico por su código/pieza
    Ejemplo: /api/repuestos/codigo/ACT00175
    """
    try:
        repuesto = (
            db.query(RepuestoDB)
            .filter(
                and_(
                    RepuestoDB.pieza == pieza_codigo,
                    RepuestoDB.activo == True
                )
            )
            .first()
        )
        
        if not repuesto:
            raise HTTPException(
                status_code=404,
                detail=f"Repuesto con código {pieza_codigo} no encontrado"
            )
        
        return {
            "success": True,
            "data": _repuesto_to_dict(repuesto)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Filtrar por Clase
# ═══════════════════════════════════════════════════════════

@router.get("/clase/{clase}")
async def get_repuestos_por_clase(
    clase: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtener repuestos filtrados por clase
    Ejemplo: /api/repuestos/clase/BAS
    """
    try:
        repuestos = (
            db.query(RepuestoDB)
            .filter(
                and_(
                    RepuestoDB.clase == clase,
                    RepuestoDB.activo == True
                )
            )
            .order_by(RepuestoDB.pieza.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        total = (
            db.query(RepuestoDB)
            .filter(
                and_(
                    RepuestoDB.clase == clase,
                    RepuestoDB.activo == True
                )
            )
            .count()
        )
        
        result = [_repuesto_to_dict(r) for r in repuestos]
        
        return {
            "success": True,
            "data": result,
            "total": total,
            "clase": clase,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Obtener Clases Disponibles (Para filtros)
# ═══════════════════════════════════════════════════════════

@router.get("/filtros/clases")
async def get_clases_disponibles(db: Session = Depends(get_db)):
    """
    Obtener todas las clases/categorías disponibles
    Útil para llenar dropdowns de filtros
    """
    try:
        clases = (
            db.query(RepuestoDB.clase)
            .filter(RepuestoDB.activo == True)
            .distinct()
            .order_by(RepuestoDB.clase.asc())
            .all()
        )
        
        clase_list = [c[0] for c in clases if c[0]]  # Filtrar None
        
        return {
            "success": True,
            "data": clase_list,
            "total": len(clase_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GET - Obtener Niveles de Sistema Disponibles
# ═══════════════════════════════════════════════════════════

@router.get("/filtros/niveles-sistema")
async def get_niveles_sistema_disponibles(db: Session = Depends(get_db)):
    """
    Obtener todos los niveles de sistema disponibles
    """
    try:
        niveles = (
            db.query(RepuestoDB.nivel_sistema)
            .filter(RepuestoDB.activo == True)
            .distinct()
            .order_by(RepuestoDB.nivel_sistema.asc())
            .all()
        )
        
        niveles_list = [n[0] for n in niveles if n[0]]  # Filtrar None
        
        return {
            "success": True,
            "data": niveles_list,
            "total": len(niveles_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# POST - Cargar Repuestos desde Excel
# ═══════════════════════════════════════════════════════════

@router.post("/upload-excel")
async def upload_repuestos_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Cargar repuestos desde archivo Excel
    Reemplaza los repuestos existentes con los del Excel
    
    Esperado: Archivo .xlsx con las columnas del inventario
    """
    try:
        # Validar que sea Excel
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos Excel (.xlsx o .xls)"
            )
        
        # Leer el archivo
        content = await file.read()
        
        # Usar openpyxl para procesar
        import io
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        
        # Obtener encabezados (primera fila)
        headers = []
        for cell in ws[1]:
            if cell.value:
                headers.append(str(cell.value).lower().replace(" ", "_"))
        
        # Mapeo de columnas esperadas
        column_map = {
            "pieza": "pieza",
            "descripción": "descripcion",
            "udm": "udm",
            "clase": "clase",
            "jerarquía_de_la_pieza": "jerarquia_pieza",
            "nivel_de_sistema": "nivel_sistema",
            "nivel_de_montaje": "nivel_montaje",
            "nivel_de_componente": "nivel_componente",
            "condición": "condicion",
            "número_de_pieza_del_fabricante_principal": "numero_pieza_fabricante",
            "suministrador_sugerido": "suministrador_sugerido",
            "seguimiento_de_piezas_reparables": "seguimiento_piezas_reparables",
            "seguimiento_por_activo": "seguimiento_por_activo",
            "días_de_garantía": "dias_garantia",
            "evitar_nuevos_pedidos": "evitar_nuevos_pedidos"
        }
        
        # Contar inserciones
        insertados = 0
        actualizados = 0
        errores = 0
        
        # Procesar filas (desde la fila 2 en adelante)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            try:
                # Extraer datos por índice de columna
                data = {}
                for col_idx, cell in enumerate(row):
                    if col_idx < len(headers):
                        header = headers[col_idx]
                        if cell.value is not None:
                            data[header] = str(cell.value).strip()
                
                # Campo obligatorio: Pieza (código)
                if "pieza" not in data or not data["pieza"]:
                    continue
                
                pieza_codigo = data.get("pieza", "").upper()
                
                # Buscar si ya existe
                repuesto_existente = db.query(RepuestoDB).filter_by(
                    pieza=pieza_codigo
                ).first()
                
                # Preparar datos
                repuesto_data = {
                    "pieza": pieza_codigo,
                    "descripcion": data.get("descripcion", ""),
                    "udm": data.get("udm", "UN"),
                    "clase": data.get("clase", ""),
                    "jerarquia_pieza": data.get("jerarquia_de_la_pieza", ""),
                    "nivel_sistema": data.get("nivel_de_sistema", ""),
                    "nivel_montaje": data.get("nivel_de_montaje", ""),
                    "nivel_componente": data.get("nivel_de_componente", ""),
                    "condicion": data.get("condición", ""),
                    "numero_pieza_fabricante": data.get("número_de_pieza_del_fabricante_principal", ""),
                    "suministrador_sugerido": data.get("suministrador_sugerido", ""),
                    "seguimiento_piezas_reparables": data.get("seguimiento_de_piezas_reparables", "NO"),
                    "seguimiento_por_activo": data.get("seguimiento_por_activo", "NO"),
                    "dias_garantia": _parse_int(data.get("días_de_garantía", 0)),
                    "evitar_nuevos_pedidos": data.get("evitar_nuevos_pedidos", "NO"),
                    "activo": True,
                    "updated_at": datetime.utcnow()
                }
                
                if repuesto_existente:
                    # Actualizar existente
                    for key, value in repuesto_data.items():
                        setattr(repuesto_existente, key, value)
                    actualizados += 1
                else:
                    # Crear nuevo
                    nuevo_repuesto = RepuestoDB(**repuesto_data)
                    db.add(nuevo_repuesto)
                    insertados += 1
                
            except Exception as e:
                errores += 1
                continue
        
        # Confirmar cambios
        db.commit()
        
        return {
            "success": True,
            "message": "Repuestos cargados correctamente",
            "stats": {
                "insertados": insertados,
                "actualizados": actualizados,
                "errores": errores,
                "total_procesados": insertados + actualizados + errores
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cargar repuestos: {str(e)}")

# ═══════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════

def _repuesto_to_dict(repuesto: RepuestoDB) -> dict:
    """Convertir objeto RepuestoDB a diccionario"""
    return {
        "id": repuesto.id,
        "pieza": repuesto.pieza,
        "descripcion": repuesto.descripcion,
        "udm": repuesto.udm or "UN",
        "clase": repuesto.clase or "",
        "jerarquia_pieza": repuesto.jerarquia_pieza or "",
        "nivel_sistema": repuesto.nivel_sistema or "",
        "nivel_montaje": repuesto.nivel_montaje or "",
        "nivel_componente": repuesto.nivel_componente or "",
        "condicion": repuesto.condicion or "",
        "numero_pieza_fabricante": repuesto.numero_pieza_fabricante or "",
        "suministrador_sugerido": repuesto.suministrador_sugerido or "",
        "seguimiento_piezas_reparables": repuesto.seguimiento_piezas_reparables or "NO",
        "seguimiento_por_activo": repuesto.seguimiento_por_activo or "NO",
        "dias_garantia": repuesto.dias_garantia or 0,
        "evitar_nuevos_pedidos": repuesto.evitar_nuevos_pedidos or "NO",
        "activo": repuesto.activo,
        "created_at": repuesto.created_at.isoformat() if repuesto.created_at else None,
        "updated_at": repuesto.updated_at.isoformat() if repuesto.updated_at else None
    }

def _parse_int(value):
    """Parsear valor a entero de forma segura"""
    try:
        return int(value) if value else 0
    except (ValueError, TypeError):
        return 0