# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — Insumos para el bot de Disponibilidad de flota
#  GET /api/disponibilidad/bot/insumos?fecha_km=AAAA-MM-DD   (solo admin)
#
#  El bot necesita de EMANTIC dos cosas que ya están en la base:
#    · el kilometraje de un día (lecturas_km) → regla «menos de 7 km = no salió de patio»
#    · las filas actuales de Disponibilidad por unidad → para conservar lo de mantenimiento (Excel manual)
#      y los días acumulados de lo que el propio bot marcó ayer
#  La subida del resultado usa el endpoint que ya existe: POST /api/disponibilidad/upload (un Excel por unidad).
# ═══════════════════════════════════════════════════════════

import logging
import os
import re
import subprocess
import sys
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import DisponibilidadDB, LecturaKmDB
from deps import get_current_admin_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/disponibilidad/bot", tags=["disponibilidad-bot"])


def armar_insumos(filas_disp: List[Any], lecturas: List[Any], flotas: Dict[str, Optional[int]], fecha_km: str) -> Dict[str, Any]:
    """Pura (sin BD): arma la respuesta. Un móvil con recorrido 0 y odómetro Mín = Máx = 0 está «sin dato» → None."""
    km: Dict[str, Optional[float]] = {}
    for l in lecturas:
        sin_dato = not (l.recorrido or 0) and not (l.odo_min or 0) and not (l.odo_max or 0)
        km[re.sub(r"[^A-Z0-9]", "", str(l.movil).upper())] = None if sin_dato else round(float(l.recorrido or 0), 2)
    unidades: Dict[str, Any] = {}
    for emp in ("E10", "E16"):
        filas = [f for f in filas_disp if f.empresa == emp]
        cortes = [f.fecha_corte for f in filas if f.fecha_corte]
        unidades[emp] = {
            "fecha_corte": max(cortes).isoformat() if cortes else None,
            "flota_total": flotas.get(emp),
            "filas": [{"movil": f.movil, "area": f.area or "", "descripcion": f.descripcion or "",
                       "fecha_ingreso": f.fecha_ingreso.isoformat() if f.fecha_ingreso else None,
                       "dias_inoperatividad": float(f.dias_inoperatividad or 0)} for f in filas],
        }
    return {"fecha_km": fecha_km, "km_cargado": bool(lecturas), "km": km, "unidades": unidades}


@router.get("/insumos")
def insumos(fecha_km: Optional[str] = None, db: Session = Depends(get_db), user: Dict = Depends(get_current_admin_user)):
    fecha_km = fecha_km or (date.today() - timedelta(days=1)).isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha_km):
        raise HTTPException(400, "fecha_km debe ser AAAA-MM-DD")
    from routes.datos import _flota_total                      # mismo cálculo de flota que usa la pantalla (FLOTA_TOTAL_E10 / E16 del .env)
    flotas = {emp: _flota_total(db, emp) for emp in ("E10", "E16")}
    lecturas = db.query(LecturaKmDB).filter(LecturaKmDB.fecha == fecha_km).all()
    filas = db.query(DisponibilidadDB).all()
    return armar_insumos(filas, lecturas, flotas, fecha_km)


@router.post("/limpiar")
def limpiar(empresa: str, db: Session = Depends(get_db), user: Dict = Depends(get_current_admin_user)):
    """Borra el corte de una unidad (E10 / E16). Lo usa el bot cuando TODOS los buses de la unidad quedaron disponibles:
    el Excel de carga no admite un archivo vacío, así que sin esto quedaría el corte de ayer."""
    if empresa not in ("E10", "E16"):
        raise HTTPException(400, "empresa debe ser E10 o E16")
    n = db.query(DisponibilidadDB).filter(DisponibilidadDB.empresa == empresa).delete(synchronize_session=False)
    db.commit()
    return {"empresa": empresa, "borrados": n}


# ═══════════════════════════════════════════════════════════
#  Botón «Actualizar con el bot» de la pestaña ICO
#    POST /api/disponibilidad/bot/iniciar   lanza  python bot/transmitools_bot.py --auto --subir --modulo disponibilidad
#                                           (kilometraje de AYER de Tako + P60 + cruce con inmovilizados + subida)
#    GET  /api/disponibilidad/bot/estado    estado, resumen por unidad y últimas líneas del bot
#    POST /api/disponibilidad/bot/cancelar  detiene la corrida
#  El bot corre en el equipo donde está el backend (igual que el botón «Actualizar DPV»).
# ═══════════════════════════════════════════════════════════

BOT_DIR = Path(os.environ.get("BOT_DIR") or Path(__file__).resolve().parents[2] / "bot")
BOT_PYTHON = os.environ.get("BOT_PYTHON") or sys.executable
BOT_LOG = "ultima_disponibilidad.log"
MAX_LINEAS = 60

_lock = threading.Lock()
_proc: Optional[subprocess.Popen] = None
_inicio: Optional[datetime] = None
_fin: Optional[datetime] = None
_cancelado = False


def _leer_log() -> List[str]:
    f = BOT_DIR / BOT_LOG
    try:
        return [l.rstrip() for l in f.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()] if f.exists() else []
    except OSError:
        return []


def analizar_log(lineas: List[str]) -> Dict[str, Any]:
    """Lo que la pantalla necesita del texto del bot: resumen por unidad, avisos, motivo si no actualizó, errores y archivos subidos."""
    def texto(l):
        return re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", l)
    resumen, avisos, errores, abortado, subidos, limpiadas = [], [], [], None, 0, []
    for l in map(texto, lineas):
        if re.match(r"UF-\d+: \d+ NO disponibles", l):
            resumen.append(l)
        elif l.startswith("AVISO: "):
            avisos.append(l[7:])
        elif l.startswith("NO SE ACTUALIZA LA DISPONIBILIDAD: "):
            abortado = l.split(": ", 1)[1]
        elif re.search(r"^EMANTIC Disponibilidad_UF-\d+.*filas guardadas", l):
            subidos += 1
        elif re.search(r"^EMANTIC UF-\d+: corte anterior borrado", l):
            limpiadas.append(l.split(":")[0].replace("EMANTIC ", ""))
        elif re.match(r"(ERROR|EMANTIC rechaz|EMANTIC respondi|No pude|Falta )", l) or "   ERROR:" in l:
            errores.append(l.strip())
    return {"resumen": resumen, "avisos": avisos, "errores": errores[-5:], "abortado": abortado, "subidos": subidos, "limpiadas": limpiadas}


def estado_bot() -> Dict[str, Any]:
    with _lock:
        corriendo = _proc is not None and _proc.poll() is None
        codigo = None if _proc is None else _proc.poll()
        estado = "inactivo" if _proc is None else "corriendo" if corriendo else "cancelado" if _cancelado else "ok" if codigo == 0 else "error"
        lineas = _leer_log() if _proc is not None else []
        return {"estado": estado, "codigo": codigo, "lineas": lineas[-MAX_LINEAS:], **analizar_log(lineas),
                "inicio": _inicio.isoformat(timespec="seconds") if _inicio else None, "fin": _fin.isoformat(timespec="seconds") if _fin else None}


def _vigilar(proc: subprocess.Popen) -> None:
    global _fin
    proc.wait()
    with _lock:
        _fin = datetime.utcnow()


def _otro_bot_corriendo() -> bool:
    """El botón de DPV/ICO usa el mismo Chrome del bot: no se lanzan los dos a la vez."""
    try:
        from routes import dpv_bot
        p = getattr(dpv_bot, "_proc", None)
        return p is not None and p.poll() is None
    except Exception:                                        # noqa: BLE001
        return False


def iniciar_bot() -> Dict[str, Any]:
    global _proc, _inicio, _fin, _cancelado
    script = BOT_DIR / "transmitools_bot.py"
    if not script.exists():
        raise RuntimeError(f"No encuentro el bot en {script}. Si está en otra carpeta, define BOT_DIR en el .env del backend.")
    with _lock:
        if _proc is not None and _proc.poll() is None:
            raise ValueError("El bot de disponibilidad ya está corriendo")
        if _otro_bot_corriendo():
            raise ValueError("El bot de DPV/ICO está corriendo: espera a que termine para no abrir dos Chrome a la vez")
        log = open(BOT_DIR / BOT_LOG, "wb")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        flags = 0x08000000 if os.name == "nt" else 0
        try:
            _proc = subprocess.Popen([BOT_PYTHON, "-u", str(script), "--auto", "--subir", "--modulo", "disponibilidad"], cwd=str(BOT_DIR), env=env,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        except OSError as e:
            log.close()
            raise RuntimeError(f"No pude lanzar el bot ({e}). Revisa BOT_PYTHON en el .env del backend.")
        log.close()
        _inicio, _fin, _cancelado = datetime.utcnow(), None, False
        threading.Thread(target=_vigilar, args=(_proc,), daemon=True).start()
    return estado_bot()


def cancelar_bot() -> Dict[str, Any]:
    global _cancelado
    with _lock:
        if _proc is None or _proc.poll() is not None:
            raise ValueError("El bot no está corriendo")
        _cancelado = True
        _proc.terminate()
    return estado_bot()


@router.post("/iniciar")
def api_iniciar(user: Dict = Depends(get_current_admin_user)):
    try:
        out = iniciar_bot()
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except RuntimeError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    logger.info("Bot de disponibilidad iniciado por %s", user.get("username"))
    return out


@router.get("/estado")
def api_estado(user: Dict = Depends(get_current_admin_user)):
    return estado_bot()


@router.post("/cancelar")
def api_cancelar(user: Dict = Depends(get_current_admin_user)):
    try:
        return cancelar_bot()
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
