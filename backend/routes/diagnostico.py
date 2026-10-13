"""
EMANTIC PRO - Diagnostico Router
Matrices de fallas, especificaciones y arbol de diagnostico interactivo
para los sistemas de la flota (VW Volksbus / Scania)
Sirve el dataset generado a partir de los manuales OEM de la flota.
"""

from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter(prefix="/api/diagnostico", tags=["diagnostico"])

# ═══════════════════════════════════════════════════════════
# Carga del dataset (JSON estatico, cacheado en memoria)
# ═══════════════════════════════════════════════════════════

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "emantic_maintenance_data.json")

_cache = None


def _load_dataset():
    """Carga el JSON una sola vez y lo mantiene en memoria."""
    global _cache
    if _cache is None:
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(
                f"No se encontro el dataset de diagnostico en: {DATA_PATH}. "
                "Copia alli el archivo emantic_maintenance_data.json."
            )
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def _find_sistema(data, sistema_id: str):
    return next((s for s in data["systems"] if s["id"] == sistema_id), None)


# ═══════════════════════════════════════════════════════════
# GET - Categorias (dinamicas, derivadas del dataset)
# ═══════════════════════════════════════════════════════════

@router.get("/categorias")
async def get_categorias():
    """
    Obtener todas las categorias de sistemas disponibles en el diagnostico
    (tren_motriz, chasis, neumatico, electrico, emisiones, accesibilidad)
    """
    try:
        data = _load_dataset()
        categorias = sorted({s["category"] for s in data["systems"]})
        return categorias
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET - Lista resumida de sistemas (para las tarjetas)
# ═══════════════════════════════════════════════════════════

@router.get("/sistemas")
async def get_sistemas(category: str = None):
    """
    Lista resumida de los sistemas documentados, opcionalmente filtrada por categoria.
    Devuelve DICTS (no el objeto completo) para que la vista de tarjetas cargue liviano.
    """
    try:
        data = _load_dataset()
        sistemas = data["systems"]
        if category:
            sistemas = [s for s in sistemas if s["category"] == category]

        result = []
        for s in sistemas:
            result.append({
                "id": s["id"],
                "name": s["name"],
                "category": s["category"],
                "applicable_brands": s["applicable_brands"],
                "total_fallas": len(s["fault_matrix"]),
                "total_pasos": len(s["procedure"]["steps"]),
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET - Sistema por ID (detalle completo)
# ═══════════════════════════════════════════════════════════

@router.get("/sistemas/{sistema_id}")
async def get_sistema(sistema_id: str):
    """
    Detalle completo de un sistema: descripcion funcional, especificaciones,
    matriz de fallas, procedimiento paso a paso y arbol de diagnostico.
    """
    try:
        data = _load_dataset()
        sistema = _find_sistema(data, sistema_id)
        if not sistema:
            raise HTTPException(status_code=404, detail="Sistema no encontrado")
        return sistema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET - Arbol de diagnostico de un sistema (para el asistente)
# ═══════════════════════════════════════════════════════════

@router.get("/sistemas/{sistema_id}/arbol")
async def get_arbol_diagnostico(sistema_id: str):
    """Solo el arbol de diagnostico (nodos de decision/accion) de un sistema."""
    try:
        data = _load_dataset()
        sistema = _find_sistema(data, sistema_id)
        if not sistema:
            raise HTTPException(status_code=404, detail="Sistema no encontrado")
        return sistema["diagnostic_tree"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET - Busqueda de sintomas en todas las matrices de fallas
# ═══════════════════════════════════════════════════════════

@router.get("/buscar/{query}")
async def buscar_fallas(query: str):
    """
    Busca un sintoma (texto libre) en la matriz de fallas de todos los sistemas.
    Devuelve cada fila que coincide, con el id y nombre del sistema al que pertenece.
    """
    try:
        data = _load_dataset()
        q = query.lower().strip()
        if not q:
            return []

        result = []
        for s in data["systems"]:
            for fila in s["fault_matrix"]:
                texto = f'{fila["symptom"]} {fila["root_cause"]}'.lower()
                if q in texto:
                    result.append({
                        "sistema_id": s["id"],
                        "sistema_name": s["name"],
                        **fila,
                    })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET - Notas de cobertura (sistemas documentados y brechas)
# ═══════════════════════════════════════════════════════════

@router.get("/cobertura")
async def get_cobertura():
    """Sistemas cubiertos en detalle, brechas documentales y recomendaciones de confiabilidad."""
    try:
        data = _load_dataset()
        return data["coverage_notes"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))