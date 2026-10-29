# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Carga del DPV desde los CSV que baja el bot de TransMiTools
#  POST /api/dpv/upload-csv  (solo admin)
#
#  Los CSV del portal NO traen las mismas columnas que el Excel del DPV: el id se llama «IdDPV», las fechas «F. Inicio DP»
#  y no vienen tipología, ruta, operador ni alerta. Por eso NO se reutiliza /api/dpv/upload: aquí
#    · se aceptan los encabezados del portal,
#    · los registros que ya existen solo se actualizan con los campos que el CSV SÍ trae (no se borran tipología/ruta/operador),
#    · la tipología de un registro nuevo se toma de otro evento del mismo móvil,
#    · hora, franja y día de la semana se deducen de «F. Inmovilización».
#
#  Además, el botón «Actualizar DPV» de la pantalla de carga:
#    POST /api/dpv/bot/iniciar   lanza  python bot/transmitools_bot.py --auto --subir  en el equipo donde corre este backend
#    GET  /api/dpv/bot/estado    estado y últimas líneas de lo que va haciendo el bot
#    POST /api/dpv/bot/cancelar  detiene la corrida
# ═══════════════════════════════════════════════════════════

import csv
import io
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import dpv_reglas as reglas
from database import DpvRegistroDB
from deps import get_db, get_current_admin_user
from routes.datos import (
    BATCH, MAX_FILE_MB, DPV_LEN, norm_header, pick, to_dt, to_int, to_str, registrar_historial, respuesta,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dpv-bot"])

# campo de la BD → encabezados del CSV del portal (ya normalizados con norm_header: sin tildes, mayúsculas, sin puntuación)
CSV_COLS = {
    "dpv_id": ("IDDPV", "ID DPV", "DPV"),
    "estado": ("ESTADO",),
    "fecha_inicio": ("F INICIO DP", "F INICIO DPV", "FECHA INICIO DPV"),
    "fecha_cierre": ("F CIERRE DP", "F CIERRE DPV", "FECHA CIERRE DPV"),
    "empresa": ("EMPRESA",),
    "fuente": ("FUENTE",),
    "placa": ("PLACA",),
    "movil": ("MOVIL",),
    "fecha_inmovilizacion": ("F INMOVILIZACION", "FECHA INMOVILIZACION"),
    "causa_inmovilizacion": ("CAUSA DE LA INMOVILIZACION", "CAUSA DE INMOVILIZACION", "CAUSA INMOVILIZACION"),
    "descripcion_novedad": ("DESCRIPCION DE LA NOVEDAD", "DESCRIPCION NOVEDAD", "DESCRIPCION"),
}
REQUERIDAS = ("IDDPV", "ESTADO", "PLACA")      # al menos una variante del id (ver _tiene_id)


def _decodificar(contenido: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return contenido.decode(enc)
        except UnicodeDecodeError:
            continue
    return contenido.decode("latin-1", errors="replace")


def _leer_csv(contenido: bytes):
    """Devuelve (encabezados_normalizados, lista de dicts por fila). Detecta , ; o tabulador."""
    texto = _decodificar(contenido)
    primera = texto.splitlines()[0] if texto.strip() else ""
    delim = max((",", ";", "\t"), key=primera.count)
    lector = csv.reader(io.StringIO(texto), delimiter=delim)
    filas = list(lector)
    if not filas:
        return [], []
    headers = [norm_header(h) for h in filas[0]]
    out = []
    for r in filas[1:]:
        if not r or all(not c.strip() for c in r):
            continue
        out.append({headers[i]: r[i] for i in range(min(len(headers), len(r))) if headers[i]})
    return headers, out


def _tiene_id(headers: List[str]) -> bool:
    return any(h in headers for h in CSV_COLS["dpv_id"])


def _fila_a_registro(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dpv_id = to_int(pick(row, *CSV_COLS["dpv_id"]), None)
    if dpv_id is None:
        return None
    r: Dict[str, Any] = {"dpv_id": dpv_id}
    for campo, keys in CSV_COLS.items():
        if campo == "dpv_id":
            continue
        v = pick(row, *keys)
        r[campo] = to_dt(v) if campo.startswith("fecha") else to_str(v, DPV_LEN.get(campo))
    if r.get("fecha_inmovilizacion"):
        r["hora"] = reglas.hora_de(r["fecha_inmovilizacion"])        # el CSV no trae HORA: sale de la fecha con hora
    r, _ = reglas.limpiar_evento(r)                                  # estado canónico, franja AM/PM y día de la semana
    return r


@router.post("/dpv/upload-csv")
async def upload_dpv_csv(files: List[UploadFile] = File(...), db: Session = Depends(get_db),
                         user: Dict = Depends(get_current_admin_user)):
    """Recibe uno o varios CSV del bot (en orden de etapa: si un DPV aparece en varios, manda el último)."""
    t0 = time.time()
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún archivo")

    eventos: Dict[int, Dict[str, Any]] = {}
    errores: List[str] = []
    total = 0
    por_archivo: List[Dict[str, Any]] = []
    for f in files:
        nombre = f.filename or ""
        if not nombre.lower().endswith(".csv"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"«{nombre}»: solo se permiten archivos .csv")
        contenido = await f.read()
        if len(contenido) > MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"«{nombre}» supera {MAX_FILE_MB} MB")
        headers, filas = _leer_csv(contenido)
        if not headers:
            por_archivo.append({"archivo": nombre, "filas": 0})
            continue
        falta = [h for h in ("ESTADO", "PLACA") if h not in headers] + ([] if _tiene_id(headers) else ["IdDPV"])
        if falta:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"«{nombre}»: faltan columnas requeridas: {', '.join(falta)}")
        n_ok = 0
        for n, row in enumerate(filas, start=2):
            total += 1
            reg = _fila_a_registro(row)
            if reg is None:
                errores.append(f"{nombre} fila {n}: IdDPV vacío o no numérico")
                continue
            eventos[reg["dpv_id"]] = reg
            n_ok += 1
        por_archivo.append({"archivo": nombre, "filas": n_ok})

    ids = list(eventos.keys())
    existentes: Dict[int, DpvRegistroDB] = {}
    for i in range(0, len(ids), BATCH):
        for o in db.query(DpvRegistroDB).filter(DpvRegistroDB.dpv_id.in_(ids[i:i + BATCH])).all():
            existentes[o.dpv_id] = o

    # Tipología de los registros NUEVOS: la de otro evento del mismo móvil (el CSV no la trae)
    moviles = sorted({e["movil"] for k, e in eventos.items() if k not in existentes and e.get("movil")})
    tipologia_de: Dict[str, str] = {}
    for i in range(0, len(moviles), BATCH):
        q = db.query(DpvRegistroDB.movil, DpvRegistroDB.tipologia) \
              .filter(DpvRegistroDB.movil.in_(moviles[i:i + BATCH]), DpvRegistroDB.tipologia != "") \
              .order_by(DpvRegistroDB.fecha_inmovilizacion.asc())
        for movil, tip in q.all():
            tipologia_de[movil] = tip                         # el más reciente queda al final

    ins = upd = sin_tipologia = 0
    for dpv_id, ev in eventos.items():
        obj = existentes.get(dpv_id)
        if obj is None:
            if not ev.get("tipologia"):
                ev["tipologia"] = tipologia_de.get(ev.get("movil", ""), "")
            if not ev["tipologia"]:
                sin_tipologia += 1
            db.add(DpvRegistroDB(**ev))
            ins += 1
            continue
        for campo, v in ev.items():
            if v not in (None, ""):                           # solo lo que el CSV trae: no se borra tipología, ruta, operador…
                setattr(obj, campo, v)
        obj.updated_at = datetime.utcnow()
        upd += 1
    try:
        db.commit()
    except Exception as e:                                    # noqa: BLE001
        db.rollback()
        logger.error("Error guardando DPV desde CSV", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error guardando en BD: {e}")

    seg = time.time() - t0
    nombres = ", ".join(a["archivo"] for a in por_archivo)
    registrar_historial(db, "dpv", user, nombres, total, ins, upd, len(errores), seg, "\n".join(errores[:50]))
    return respuesta(total, ins, upd, errores, seg, {"archivos": por_archivo, "sin_tipologia": sin_tipologia})


# ═══════════════════════════════════════════════════════════
#  BOTÓN «ACTUALIZAR DPV»: lanza el bot de TransMiTools en ESTE equipo
#  (solo tiene sentido si el backend corre en el computador del analista: abre Chrome en su pantalla)
# ═══════════════════════════════════════════════════════════

BOT_DIR = Path(os.environ.get("BOT_DIR") or Path(__file__).resolve().parents[2] / "bot")   # <proyecto>/bot
BOT_PYTHON = os.environ.get("BOT_PYTHON") or sys.executable     # Python que tiene instalado playwright (si el del backend no lo tiene)
BOT_LOG = "ultima_corrida.log"
MAX_LINEAS = 60

_lock = threading.Lock()
_proc: Optional[subprocess.Popen] = None
_inicio: Optional[datetime] = None
_fin: Optional[datetime] = None
_cancelado = False


def _leer_log() -> List[str]:
    f = BOT_DIR / BOT_LOG
    if not f.exists():
        return []
    try:
        texto = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [l.rstrip() for l in texto.splitlines() if l.strip()]


def analizar_log(lineas: List[str], terminado: bool) -> Dict[str, Any]:
    """Lo que la pantalla necesita saber del texto que imprime el bot (sin depender de cómo lo muestre)."""
    resultado = None
    for l in lineas:
        m = re.search(r"EMANTIC: (\d+) nuevos, (\d+) actualizados, (\d+) con error", l)
        if m:
            resultado = {"nuevos": int(m.group(1)), "actualizados": int(m.group(2)), "errores": int(m.group(3))}
    ultimo_captcha = max((i for i, l in enumerate(lineas) if "No soy un robot" in l), default=-1)
    ultima_sesion = max((i for i, l in enumerate(lineas) if "Sesión iniciada" in l or "Sesión ya iniciada" in l), default=-1)
    return {
        "resultado": resultado,
        "esperando_captcha": (not terminado) and ultimo_captcha > ultima_sesion,
        "pestanas": [l.split("Pestaña ", 1)[1].strip() for l in lineas if "] Pestaña " in l],
    }


def estado_bot() -> Dict[str, Any]:
    with _lock:
        corriendo = _proc is not None and _proc.poll() is None
        codigo = None if _proc is None else _proc.poll()
        lineas = _leer_log()
        if _proc is None:
            estado = "inactivo"
        elif corriendo:
            estado = "corriendo"
        elif _cancelado:
            estado = "cancelado"
        else:
            estado = "ok" if codigo == 0 else "error"
        extra = analizar_log(lineas, terminado=not corriendo)
        return {
            "estado": estado, "codigo": codigo,
            "inicio": _inicio.isoformat(timespec="seconds") if _inicio else None,
            "fin": _fin.isoformat(timespec="seconds") if _fin else None,
            "lineas": lineas[-MAX_LINEAS:], **extra,
        }


def _vigilar(proc: subprocess.Popen) -> None:
    global _fin
    proc.wait()
    with _lock:
        _fin = datetime.utcnow()


def iniciar_bot() -> Dict[str, Any]:
    """Lanza el bot. Lanza RuntimeError con un texto para el usuario si no se puede."""
    global _proc, _inicio, _fin, _cancelado
    script = BOT_DIR / "transmitools_bot.py"
    if not script.exists():
        raise RuntimeError(f"No encuentro el bot en {script}. Si está en otra carpeta, define BOT_DIR en el .env del backend.")
    with _lock:
        if _proc is not None and _proc.poll() is None:
            raise ValueError("El bot ya está corriendo")
        log = open(BOT_DIR / BOT_LOG, "wb")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        flags = 0x08000000 if os.name == "nt" else 0           # CREATE_NO_WINDOW: sin ventana de consola; Chrome sí se ve
        try:
            _proc = subprocess.Popen([BOT_PYTHON, "-u", str(script), "--auto", "--subir"], cwd=str(BOT_DIR), env=env,
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
        _proc.terminate()                                       # el Chrome del bot queda abierto; el próximo intento lo reutiliza
    return estado_bot()


@router.post("/dpv/bot/iniciar")
def api_bot_iniciar(user: Dict = Depends(get_current_admin_user)):
    try:
        out = iniciar_bot()
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except RuntimeError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    logger.info("Bot de TransMiTools iniciado por %s", user.get("username"))
    return out


@router.get("/dpv/bot/estado")
def api_bot_estado(user: Dict = Depends(get_current_admin_user)):
    return estado_bot()


@router.post("/dpv/bot/cancelar")
def api_bot_cancelar(user: Dict = Depends(get_current_admin_user)):
    try:
        return cancelar_bot()
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
