# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Reglas de negocio de Inmovilizados
#  Reporte «Vehículos inmovilizados por concesionario de operación» (Transmitools), que se exporta cada hora.
#
#  Módulo PURO (solo librería estándar, sin FastAPI ni SQLAlchemy): lo usa routes/datos.py al cargar el Excel y lo prueba
#  tests/test_inmov_reglas.py sin base de datos.
#
#  Cómo se lee el reporte:
#    · Una fila = una inmovilización. Se identifica por PLACA + FECHA DE INMOVILIZACION (el reporte no trae un id).
#    · Sin «Fecha de Habilitación» → el móvil sigue inmovilizado; con fecha → ya fue habilitado.
#    · El reporte no trae el móvil como columna: sale del texto («Móvil 327054/…») y se escribe como en el resto de la
#      app (Z32-7054). Si no está en el texto, se busca por placa entre los eventos del DPV.
#    · Cada archivo es una foto (un «corte») de la unidad. Un evento sin habilitar que ya no aparece en el último corte
#      queda «sin confirmar»: no se da por habilitado, pero tampoco se cuenta como inmovilizado ahora.
# ═══════════════════════════════════════════════════════════

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dpv_reglas import limpiar_espacios, limpiar_texto_libre, sin_acentos, unidad_de

UNIDADES = ("E10", "E16")

ESTADO_INMOVILIZADO = "inmovilizado"      # sin habilitar y presente en el último corte de su unidad
ESTADO_HABILITADO = "habilitado"          # ya tiene fecha de habilitación
ESTADO_SIN_CONFIRMAR = "sin_confirmar"    # sin habilitar, pero ya no aparece en el último corte

LARGO_CAUSA_RECORTADA = 20                # Transmitools recorta la causa a 20 caracteres


# ── Fechas ─────────────────────────────────────────────────────────────────

_FORMATOS_FECHA = (
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",          # como sale del reporte (día primero)
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
)


def parse_fecha(v: Any) -> Optional[datetime]:
    """Fecha y hora desde datetime/date, texto 'dd/mm/aaaa hh:mm:ss' (día primero), ISO o número de serie de Excel.
    Siempre sin microsegundos. None si no se entiende."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, datetime):
        return v.replace(microsecond=0)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    if isinstance(v, (int, float)):
        if 20000 < v < 80000:                                    # serie de Excel (1954–2119)
            return (datetime(1899, 12, 30) + timedelta(days=float(v))).replace(microsecond=0)
        return None
    s = limpiar_espacios(v)
    if not s:
        return None
    for f in _FORMATOS_FECHA:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s).replace(microsecond=0, tzinfo=None)
    except ValueError:
        return None


def fecha_de_nombre_archivo(nombre: Any) -> Optional[datetime]:
    """'…_20261015134427.xlsx' → 2026-10-15 13:44:27 (el reporte lleva la hora de exportación en el nombre)."""
    for m in re.finditer(r"(?<!\d)(\d{14})(?!\d)", str(nombre or "")):
        try:
            return datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
        except ValueError:
            continue
    return None


# ── Móvil y placa ──────────────────────────────────────────────────────────

_RE_MOVIL_TEXTO = re.compile(r"M[oó]vil\s*[:#.]?\s*(\d{5,7})", re.IGNORECASE)
_RE_MOVIL_Z = re.compile(r"^Z(\d{2})\s*-?\s*(\d{4})$", re.IGNORECASE)


def movil_normalizado(v: Any) -> str:
    """'327054' → 'Z32-7054' (así se escribe el móvil en el DPV y en toda la app). 'z32 - 7054' → 'Z32-7054'.
    Si no tiene un formato conocido se devuelve limpio; vacío si no hay dato."""
    s = limpiar_espacios(v).upper()
    if not s:
        return ""
    m = _RE_MOVIL_Z.match(s)
    if m:
        return f"Z{m.group(1)}-{m.group(2)}"
    if re.fullmatch(r"\d{6}", s):
        return f"Z{s[:2]}-{s[2:]}"
    return s


def extraer_movil(*textos: Any) -> str:
    """Primer «Móvil 327054» que aparezca en los textos (en orden), ya normalizado. '' si ninguno lo trae."""
    for t in textos:
        m = _RE_MOVIL_TEXTO.search(str(t if t is not None else ""))
        if m:
            return movil_normalizado(m.group(1))
    return ""


def placa_norm(v: Any) -> str:
    """'jtr 012 ' → 'JTR012'."""
    return re.sub(r"\s+", "", str(v if v is not None else "")).upper()


# ── Texto ──────────────────────────────────────────────────────────────────

_RE_PREFIJO_FLINM = re.compile(r"^FLINM(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])")
_RE_PREFIJO_FLOTA = re.compile(r"^FLOTA\s+", re.IGNORECASE)


def limpiar_nombre(v: Any) -> str:
    """Creador / revisor / habilitador: el reporte pega el área al nombre ('FLINMPaula  Andrea  Garzon', 'FLOTA DINA  LUZ').
    Se quita ese prefijo y se juntan los espacios."""
    s = limpiar_espacios(v)
    s = _RE_PREFIJO_FLINM.sub("", s)
    s = _RE_PREFIJO_FLOTA.sub("", s)
    return s


def causa_completa(causa: Any, descripcion: Any = "") -> str:
    """La causa llega recortada a 20 caracteres ('SE APAGA Y NO ENCIEN'). La descripción de la novedad empieza con la causa
    completa antes de la primera '/' ('Se apaga y no enciende/10-10-2026/…'): si coincide, se completa con ella.
    Si no se puede completar con seguridad, se deja la causa tal cual (en mayúsculas)."""
    c = limpiar_espacios(causa).upper()
    if len(c) != LARGO_CAUSA_RECORTADA:
        return c
    seg = limpiar_espacios(str(descripcion or "").split("/")[0]).upper()
    if len(seg) > len(c) and sin_acentos(seg).startswith(sin_acentos(c)):
        return c + seg[len(c):]                      # conserva las tildes de la causa original
    return c


# ── Limpieza de una fila ───────────────────────────────────────────────────

def limpiar_fila(r: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
    """Fila del reporte (ya leída como texto/fechas) → (evento limpio, error, avisos).

    Si la fila no sirve (sin placa, sin fecha de inmovilización o sin unidad reconocible) el evento es None y `error`
    dice por qué. `avisos` son cosas raras que no impiden guardar (p. ej. habilitada antes de inmovilizarse).
    """
    avisos: List[str] = []
    placa = placa_norm(r.get("placa"))
    if not placa:
        return None, "sin placa", avisos
    f_inm = parse_fecha(r.get("fecha_inmovilizacion"))
    if f_inm is None:
        return None, f"placa {placa}: fecha de inmovilización vacía o no reconocida", avisos

    descripcion = limpiar_texto_libre(r.get("descripcion"))
    desc_rev = limpiar_texto_libre(r.get("descripcion_revision"))
    movil = extraer_movil(descripcion, desc_rev)
    empresa = limpiar_espacios(r.get("concesionario") or r.get("empresa"))
    unidad = unidad_de(empresa, movil)
    if not unidad:
        return None, f"placa {placa}: concesionario «{empresa}» no reconocido (se espera EMASIVO 10 o EMASIVO 16)", avisos

    f_hab = parse_fecha(r.get("fecha_habilitacion"))
    if f_hab is not None and f_hab < f_inm:
        avisos.append(f"placa {placa}: la habilitación ({f_hab:%d/%m/%Y %H:%M}) es anterior a la inmovilización ({f_inm:%d/%m/%Y %H:%M})")

    return {
        "unidad": unidad, "empresa": empresa[:200], "placa": placa[:20], "movil": movil[:20],
        "fecha_inmovilizacion": f_inm,
        "causa": causa_completa(r.get("causa"), descripcion)[:300],
        "descripcion": descripcion,
        "creador": limpiar_nombre(r.get("creador"))[:200],
        "fecha_revision": parse_fecha(r.get("fecha_revision")),
        "revisor": limpiar_nombre(r.get("revisor"))[:200],
        "descripcion_revision": desc_rev,
        "fecha_habilitacion": f_hab,
        "habilitador": limpiar_nombre(r.get("habilitador"))[:200],
    }, "", avisos


# ── Estado y duración ──────────────────────────────────────────────────────

def estado_evento(fecha_habilitacion: Optional[datetime], ultima_vista: Optional[datetime],
                  ultimo_corte: Optional[datetime]) -> str:
    """habilitado · inmovilizado (sin habilitar y visto en el último corte de su unidad) · sin_confirmar (sin habilitar y
    ausente del último corte). Sin ningún corte registrado se da por inmovilizado."""
    if fecha_habilitacion is not None:
        return ESTADO_HABILITADO
    if ultimo_corte is None or (ultima_vista is not None and ultima_vista >= ultimo_corte):
        return ESTADO_INMOVILIZADO
    return ESTADO_SIN_CONFIRMAR


def horas_entre(inicio: Optional[datetime], fin: Optional[datetime]) -> Optional[float]:
    """Horas (dos decimales) entre dos fechas; None si falta alguna o el orden es imposible."""
    if inicio is None or fin is None or fin < inicio:
        return None
    return round((fin - inicio).total_seconds() / 3600, 2)
