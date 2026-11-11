# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — Casos duplicados del DPV (API + enganche con las cargas)
#
#  · aplicar_en_carga(db, eventos, origen)   lo llaman las cargas (CSV del bot y Excel): aparta los repetidos ANTES de contarlos
#  · GET  /api/dpv/duplicados                lista de apartados + resumen por móvil           (cualquier usuario)
#  · POST /api/dpv/duplicados/limpiar        limpia los que YA estaban cargados (?aplicar=true; sin eso solo simula)  (admin)
#  · POST /api/dpv/duplicados/{dpv_id}/restaurar   devuelve un caso a la base si no era realmente repetido  (admin)
# ═══════════════════════════════════════════════════════════

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import dpv_duplicados as dup
from database import DpvDuplicadoDB, DpvRegistroDB
from deps import get_current_admin_user, get_current_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dpv/duplicados", tags=["dpv-duplicados"])
BATCH = 500


# ── Acceso a la base (pequeño y aislado para poder probar la lógica sin BD) ────────────────

def _conservados_en_bd(db: Session, fechas: List[datetime]) -> Dict[Any, int]:
    """{clave: menor dpv_id} de los registros que ya están en dpv_registros con alguna de esas fechas-hora."""
    out: Dict[Any, int] = {}
    fechas = sorted(set(f.replace(microsecond=0) for f in fechas))
    for i in range(0, len(fechas), BATCH):
        rango = fechas[i:i + BATCH]
        q = db.query(DpvRegistroDB.dpv_id, DpvRegistroDB.movil, DpvRegistroDB.placa, DpvRegistroDB.fecha_inmovilizacion,
                     DpvRegistroDB.causa_inmovilizacion).filter(DpvRegistroDB.fecha_inmovilizacion.in_(rango))
        for dpv_id, movil, placa, f, causa in q.all():
            k = dup.clave({"movil": movil, "placa": placa, "fecha_inmovilizacion": f, "causa_inmovilizacion": causa})
            if k is not None and (k not in out or dpv_id < out[k]):
                out[k] = dpv_id
    return out


def _estado_ids(db: Session, ids: List[int]):
    """(ids ya apartados, ids restaurados a mano) entre los que llegan."""
    apartados, permitidos = set(), set()
    for i in range(0, len(ids), BATCH):
        for dpv_id, restaurado in db.query(DpvDuplicadoDB.dpv_id, DpvDuplicadoDB.restaurado).filter(DpvDuplicadoDB.dpv_id.in_(ids[i:i + BATCH])).all():
            (permitidos if restaurado else apartados).add(dpv_id)
    return apartados, permitidos


def _guardar_duplicado(db: Session, dpv_id: int, original_id: int, ev: Dict[str, Any], origen: str) -> None:
    obj = db.query(DpvDuplicadoDB).filter(DpvDuplicadoDB.dpv_id == dpv_id).first()
    if obj is None:
        obj = DpvDuplicadoDB(dpv_id=dpv_id, detectado_en=datetime.utcnow(), origen=origen)
        db.add(obj)
    obj.original_id = original_id
    obj.restaurado = False
    for c in dup.CAMPOS:
        if c in ev:
            setattr(obj, c, ev[c])


def aplicar_en_carga(db: Session, eventos: Dict[int, Dict[str, Any]], origen: str = "bot") -> Dict[str, Any]:
    """
    Separa los repetidos de `eventos` ({dpv_id: evento}). Los repetidos se guardan en dpv_duplicados y, si ya estaban en
    dpv_registros (carga anterior), se sacan de ahí. Devuelve {'eventos': solo los que SÍ cuentan, 'resumen': {...}}.
    """
    fechas = [e["fecha_inmovilizacion"] for e in eventos.values() if isinstance(e.get("fecha_inmovilizacion"), datetime)]
    ids = list(eventos.keys())
    apartados, permitidos = _estado_ids(db, ids) if ids else (set(), set())
    plan = dup.planificar(eventos, _conservados_en_bd(db, fechas) if fechas else {}, apartados, permitidos)
    dup_ids = [d["dpv_id"] for d in plan["duplicados"]]
    for d in plan["duplicados"]:
        _guardar_duplicado(db, d["dpv_id"], d["original_id"], d["ev"], origen)
    for i in range(0, len(dup_ids), BATCH):                    # si venían de una carga anterior, ya no deben contar
        db.query(DpvRegistroDB).filter(DpvRegistroDB.dpv_id.in_(dup_ids[i:i + BATCH])).delete(synchronize_session=False)
    for dpv_id in plan["promovidos"]:
        db.query(DpvDuplicadoDB).filter(DpvDuplicadoDB.dpv_id == dpv_id).delete(synchronize_session=False)
    db.commit()
    items = [{"dpv_id": d["dpv_id"], **{c: d["ev"].get(c) for c in ("movil", "placa", "empresa", "causa_inmovilizacion", "fecha_inmovilizacion")}}
             for d in plan["duplicados"]]
    resumen = {"total": len(items), "moviles": dup.resumen_por_movil(items), "originales": {d["dpv_id"]: d["original_id"] for d in plan["duplicados"]}}
    if items:
        logger.info("DPV: %d caso(s) duplicado(s) apartados (%s)", len(items), origen)
    return {"eventos": plan["unicos"], "resumen": resumen}


def texto_resumen(resumen: Dict[str, Any], max_moviles: int = 8) -> str:
    """Una línea para el log del bot: «3 duplicado(s): Z32-4058 ×1, Z32-7020 ×2…»."""
    if not resumen or not resumen.get("total"):
        return ""
    partes = [f"{m['movil']} ×{m['copias']}" for m in resumen["moviles"][:max_moviles]]
    mas = len(resumen["moviles"]) - max_moviles
    return f"{resumen['total']} duplicado(s) apartado(s): " + ", ".join(partes) + (f" y {mas} móvil(es) más" if mas > 0 else "")


# ── API ──────────────────────────────────────────────────────────────────────────────────

def _fila(o: DpvDuplicadoDB) -> Dict[str, Any]:
    d = {c: getattr(o, c) for c in ("dpv_id", "original_id", "estado", "empresa", "placa", "movil", "tipologia", "causa_inmovilizacion",
                                    "descripcion_novedad", "origen")}
    d["fecha_inmovilizacion"] = o.fecha_inmovilizacion.isoformat() if o.fecha_inmovilizacion else None
    d["detectado_en"] = o.detectado_en.isoformat() if o.detectado_en else None
    return d


@router.get("")
def listar(limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    q = db.query(DpvDuplicadoDB).filter(DpvDuplicadoDB.restaurado == False)  # noqa: E712
    total = q.count()
    filas = q.order_by(DpvDuplicadoDB.fecha_inmovilizacion.desc(), DpvDuplicadoDB.dpv_id.desc()).limit(limit).all()
    items = [_fila(o) for o in filas]
    base = [{**i, "fecha_inmovilizacion": o.fecha_inmovilizacion} for i, o in zip(items, filas)]
    moviles = dup.resumen_por_movil(base)
    for m in moviles:
        m["ultima"] = m["ultima"].isoformat() if m["ultima"] else None
    return {"total": total, "moviles": moviles, "items": items}


@router.post("/limpiar")
def limpiar(aplicar: bool = False, db: Session = Depends(get_db), user: Dict = Depends(get_current_admin_user)):
    """Busca repetidos entre lo que YA está en dpv_registros. Sin ?aplicar=true solo informa (simulación)."""
    filas = [{"dpv_id": i, "movil": m, "placa": p, "fecha_inmovilizacion": f, "causa_inmovilizacion": c}
             for i, m, p, f, c in db.query(DpvRegistroDB.dpv_id, DpvRegistroDB.movil, DpvRegistroDB.placa, DpvRegistroDB.fecha_inmovilizacion,
                                           DpvRegistroDB.causa_inmovilizacion).all()]
    sobran = dup.detectar_en_registros(filas)
    permitidos = {i for (i,) in db.query(DpvDuplicadoDB.dpv_id).filter(DpvDuplicadoDB.restaurado == True).all()}  # noqa: E712
    sobran = [s for s in sobran if s["dpv_id"] not in permitidos]
    por_id = {r["dpv_id"]: r for r in filas}
    vista = dup.resumen_por_movil([por_id[s["dpv_id"]] | {"dpv_id": s["dpv_id"]} for s in sobran])
    if not aplicar or not sobran:
        return {"aplicado": False, "duplicados": len(sobran), "moviles": vista}
    ids = [s["dpv_id"] for s in sobran]
    original = {s["dpv_id"]: s["original_id"] for s in sobran}
    try:
        for i in range(0, len(ids), BATCH):
            for o in db.query(DpvRegistroDB).filter(DpvRegistroDB.dpv_id.in_(ids[i:i + BATCH])).all():
                _guardar_duplicado(db, o.dpv_id, original[o.dpv_id], {c: getattr(o, c) for c in dup.CAMPOS}, "limpieza")
                db.delete(o)
        db.commit()
    except Exception as e:                                       # noqa: BLE001
        db.rollback()
        logger.error("Error limpiando duplicados del DPV", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"No se pudo limpiar: {e}")
    return {"aplicado": True, "duplicados": len(ids), "moviles": vista}


@router.post("/{dpv_id}/restaurar")
def restaurar(dpv_id: int, db: Session = Depends(get_db), user: Dict = Depends(get_current_admin_user)):
    """Devuelve el caso a dpv_registros (volverá a contar) y evita que las próximas cargas lo vuelvan a apartar."""
    o = db.query(DpvDuplicadoDB).filter(DpvDuplicadoDB.dpv_id == dpv_id).first()
    if o is None or o.restaurado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese caso no está entre los duplicados")
    if db.query(DpvRegistroDB).filter(DpvRegistroDB.dpv_id == dpv_id).first() is None:
        db.add(DpvRegistroDB(dpv_id=dpv_id, **{c: getattr(o, c) for c in dup.CAMPOS}))
    o.restaurado = True
    db.commit()
    return {"restaurado": dpv_id}
