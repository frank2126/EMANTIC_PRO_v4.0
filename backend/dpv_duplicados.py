# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — Casos duplicados del DPV (lógica pura: sin base de datos ni FastAPI; se prueba sola)
#
#  Un caso es DUPLICADO de otro cuando, con distinto IdDPV, tiene el MISMO móvil, la MISMA fecha-hora de inmovilización
#  (al segundo) y la MISMA novedad (causa de inmovilización). Se conserva el primero (el que ya estaba en la base o, si llegan
#  juntos, el de menor IdDPV) y los demás se APARTAN en otra tabla: no cuentan en las gráficas ni en el dashboard, pero quedan
#  a la vista (qué móviles, cuántas veces, de cuál son copia) y se pueden restaurar si no eran realmente repetidos.
# ═══════════════════════════════════════════════════════════

import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

Clave = Tuple[str, datetime, str]

# Campos del evento que se copian tal cual a la tabla de duplicados (y de vuelta al restaurar)
CAMPOS = ("estado", "fecha_inicio", "fecha_cierre", "empresa", "fuente", "placa", "movil", "tipologia", "fecha_inmovilizacion", "hora",
          "causa_inmovilizacion", "descripcion_novedad", "ruta", "operador", "dia_semana", "alerta", "franja_horaria")


def _alnum(v: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def _texto(v: Any) -> str:
    s = unicodedata.normalize("NFKD", str(v or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().upper()


def clave(ev: Dict[str, Any]) -> Optional[Clave]:
    """(móvil, fecha-hora al segundo, novedad). None si falta móvil o fecha: sin ellos no se puede afirmar que sea repetido."""
    movil = _alnum(ev.get("movil")) or _alnum(ev.get("placa"))
    f = ev.get("fecha_inmovilizacion")
    if not movil or not isinstance(f, datetime):
        return None
    return (movil, f.replace(microsecond=0), _texto(ev.get("causa_inmovilizacion")))


def planificar(eventos: Dict[int, Dict[str, Any]], conservados_bd: Dict[Clave, int], ids_duplicados: Iterable[int] = (),
               ids_permitidos: Iterable[int] = ()) -> Dict[str, Any]:
    """
    eventos:         {dpv_id: evento} que llegan en esta carga.
    conservados_bd:  {clave: dpv_id} de lo que YA está en dpv_registros (el menor id de cada clave).
    ids_duplicados:  ids que ya están apartados desde una carga anterior.
    ids_permitidos:  ids restaurados a mano: nunca se vuelven a apartar.
    → {'unicos': {id: ev}, 'duplicados': [{'dpv_id','original_id','ev'}], 'promovidos': [ids que dejan de ser duplicados]}
    """
    permitidos, ya_dup = set(ids_permitidos), set(ids_duplicados)
    conservado = dict(conservados_bd)
    unicos: Dict[int, Dict[str, Any]] = {}
    duplicados: List[Dict[str, Any]] = []
    promovidos: List[int] = []
    for dpv_id in sorted(eventos):                           # el de menor IdDPV de la carga se conserva
        ev = eventos[dpv_id]
        k = clave(ev)
        if dpv_id in permitidos or k is None:
            unicos[dpv_id] = ev
            continue
        original = conservado.get(k)
        if original is not None and original != dpv_id:
            duplicados.append({"dpv_id": dpv_id, "original_id": original, "ev": ev})
            continue
        conservado[k] = dpv_id
        unicos[dpv_id] = ev
        if dpv_id in ya_dup:                                 # estaba apartado pero ya no existe su original: vuelve a contar
            promovidos.append(dpv_id)
    return {"unicos": unicos, "duplicados": duplicados, "promovidos": promovidos}


def detectar_en_registros(filas: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Para limpiar lo que YA está cargado: filas = [{dpv_id, movil, placa, fecha_inmovilizacion, causa_inmovilizacion, …}].
    Devuelve [{'dpv_id', 'original_id', 'clave'}] de los que sobran (se conserva el de menor IdDPV de cada grupo).
    """
    grupos: Dict[Clave, List[int]] = {}
    for r in filas:
        k = clave(r)
        if k is not None:
            grupos.setdefault(k, []).append(int(r["dpv_id"]))
    out = []
    for k, ids in grupos.items():
        if len(ids) > 1:
            ids.sort()
            out += [{"dpv_id": i, "original_id": ids[0], "clave": k} for i in ids[1:]]
    return sorted(out, key=lambda d: d["dpv_id"])


def resumen_por_movil(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """items = duplicados apartados → una fila por móvil: cuántas copias, de qué novedades y cuáles IdDPV (para mostrarlo)."""
    m: Dict[str, Dict[str, Any]] = {}
    for it in items:
        mov = (it.get("movil") or it.get("placa") or "S/D").strip() or "S/D"
        e = m.setdefault(mov, {"movil": mov, "placa": it.get("placa") or "", "empresa": it.get("empresa") or "", "copias": 0,
                               "novedades": set(), "ids": [], "ultima": None})
        e["copias"] += 1
        e["novedades"].add(it.get("causa_inmovilizacion") or "—")
        e["ids"].append(it["dpv_id"])
        f = it.get("fecha_inmovilizacion")
        if f and (e["ultima"] is None or f > e["ultima"]):
            e["ultima"] = f
    out = []
    for e in m.values():
        e["novedades"] = sorted(e["novedades"])
        e["ids"].sort()
        out.append(e)
    return sorted(out, key=lambda e: (-e["copias"], e["movil"]))
