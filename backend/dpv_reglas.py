# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Reglas de negocio del DPV
#  DPV = Distancia Promedio entre Varadas = kilómetros ÷ inmovilizaciones
#
#  Módulo PURO (solo librería estándar, sin FastAPI ni SQLAlchemy): lo usa routes/datos.py para cargar
#  el Excel y calcular el DPV mensual, y lo prueba tests/test_dpv_reglas.py sin base de datos.
#  Todo lo que sea regla o umbral está aquí arriba, para ajustarlo en un solo lugar.
#
#  Las reglas salen de las fórmulas del Excel «DPV» (hojas DPV_E10 y DPV_E16):
#    · Inmovilizaciones del mes = eventos cuya FECHA INMOVILIZACION cae en ese mes (día completo, con hora),
#      de la empresa, y cuyo ESTADO NO es «Contestado Contundente» (el operador demostró que no fue varada).
#    · DPV del mes = km del mes ÷ inmovilizaciones del mes, en total y por tipología (PADRON / BUSETON).
#    · Estándar: DPV ≥ 10.000 km · Crítico: DPV ≤ 7.000 km · entre ambos: en alerta.
# ═══════════════════════════════════════════════════════════

import os
import re
import unicodedata
from datetime import date, datetime, time as dtime
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _entero_env(nombre: str, defecto: int) -> int:
    try:
        return int((os.getenv(nombre) or "").strip() or defecto)
    except ValueError:
        return defecto


def _lista_env(nombre: str, defecto: str) -> List[str]:
    return [x.strip() for x in (os.getenv(nombre) or defecto).split(",") if x.strip()]


# ── Umbrales ajustables (.env: DPV_KM_ESTANDAR, DPV_KM_CRITICO, DPV_ESTADOS_DESCARTADOS) ────────────
ESTANDAR_KM = _entero_env("DPV_KM_ESTANDAR", 10000)
CRITICO_KM = _entero_env("DPV_KM_CRITICO", 7000)

# Estados que NO cuentan como inmovilización. Hoy solo «Contestado Contundente»; el resto
# (No Contestado, Contestado No Contundente, Contestado, Aceptado, Validado…) sí cuentan.
ESTADOS_DESCARTADOS_TXT = _lista_env("DPV_ESTADOS_DESCARTADOS", "Contestado Contundente")

# Estados conocidos del Excel, con su escritura canónica (para unificar mayúsculas y espacios).
ESTADOS_CONOCIDOS = ["No Contestado", "Contestado Contundente", "Contestado No Contundente",
                     "Contestado", "Aceptado", "Validado"]

UNIDADES = ("E10", "E16")
PREFIJO_UNIDAD = {"Z32": "E10", "Z34": "E16"}
TIPOLOGIAS = ("PADRON", "BUSETON")
DIAS_SEMANA = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
MES_LABEL = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

ALERTA_MOVIL_INVALIDO = "Móvil inválido"
ALERTA_OPERADOR_INEXISTENTE = "Móvil inválido: operador inexistente"
ALERTA_NO_COINCIDEN = "Alerta: no coinciden"


# ── Texto ──────────────────────────────────────────────────────────────────

def limpiar_espacios(v: Any) -> str:
    """Recorta y deja un solo espacio entre palabras (también convierte NBSP): 'Ruta  A100 ' → 'Ruta A100'."""
    return " ".join(str(v if v is not None else "").split())


def sin_acentos(v: Any) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(v if v is not None else "")) if unicodedata.category(c) != "Mn")


def clave(v: Any) -> str:
    """Forma de comparación: sin espacios sobrantes, sin tildes y en mayúsculas."""
    return sin_acentos(limpiar_espacios(v)).upper()


ESTADOS_DESCARTADOS = tuple(clave(e) for e in ESTADOS_DESCARTADOS_TXT)
_CANON_ESTADO = {clave(e): e for e in ESTADOS_CONOCIDOS}


def estado_canonico(v: Any) -> str:
    """'No Contestado ' → 'No Contestado'; 'contestado contundente' → 'Contestado Contundente'.
    Un estado desconocido se conserva (con los espacios normalizados)."""
    t = limpiar_espacios(v)
    return _CANON_ESTADO.get(clave(t), t)


def es_inmovilizacion(estado: Any) -> bool:
    """True si el evento cuenta para el DPV (todo estado excepto «Contestado Contundente»)."""
    return clave(estado) not in ESTADOS_DESCARTADOS


def tipologia_norm(v: Any) -> str:
    """'BUSETON ' → 'BUSETON'; 'Padrón' → 'PADRON'. Vacío si no hay dato."""
    return clave(v)


def unidad_de(empresa: Any, movil: Any = "") -> str:
    """'E10' / 'E16' según la empresa (EMASIVO 10 / 16); si falta, por el prefijo del móvil (Z32 / Z34)."""
    e = clave(empresa)
    if re.search(r"\b10\b", e):
        return "E10"
    if re.search(r"\b16\b", e):
        return "E16"
    return PREFIJO_UNIDAD.get(clave(movil)[:3], "")


# ── Fecha, hora, franja, día ───────────────────────────────────────────────

def fecha_de(v: Any) -> Optional[date]:
    """Fecha (sin hora) desde datetime/date o texto ISO 'YYYY-MM-DD…'."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(v or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def mes_de(v: Any) -> str:
    """'YYYY-MM' de una fecha (datetime, date o ISO); '' si no hay."""
    f = fecha_de(v)
    return f"{f.year:04d}-{f.month:02d}" if f else ""


def hora_de(v: Any) -> str:
    """'HH:MM:SS' desde time, datetime (una celda de HORA con fecha completa), texto 'H:MM[:SS]' o fracción de día de Excel."""
    if isinstance(v, datetime):
        v = v.time()
    if isinstance(v, dtime):
        return v.strftime("%H:%M:%S")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 0 <= v < 1:
            seg = int(round(float(v) * 86400)) % 86400
            return f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}"
        return ""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?", str(v or ""))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return ""
    return f"{int(m.group(1)):02d}:{m.group(2)}:{m.group(3) or '00'}"


def franja_de(valor: Any, hora: Any = "") -> str:
    """'AM' / 'PM'. Entiende 'A. M.', 'P.\\xa0M.', 'am'…; si no hay valor la deduce de la hora."""
    v = re.sub(r"[^A-Z]", "", clave(valor))
    if v in ("AM", "PM"):
        return v
    h = hora_de(hora)
    if h:
        return "AM" if int(h[:2]) < 12 else "PM"
    return ""


def dia_semana_de(v: Any) -> str:
    f = fecha_de(v)
    return DIAS_SEMANA[f.weekday()] if f else ""


# ── Alerta de datos (columna ALERTA del Excel) ─────────────────────────────

def normalizar_alerta(v: Any) -> str:
    """Deja el texto de la alerta sin el emoji inicial (en SQL Server llega como '??') y con una redacción única.

    Excel: '⚠️ Móvil inválido:operdor inexistente' (la columna OPERADOR no tiene 6 dígitos),
           '⚠️ Móvil inválido' (el móvil no es Z32 ni Z34),
           '⚠️ Alerta:no coinciden' (los 2 primeros dígitos del operador no son los de la unidad del móvil).
    """
    t = limpiar_espacios(re.sub(r"^[^\w]+", "", limpiar_espacios(v)))   # quita símbolos/emoji del inicio
    if not t:
        return ""
    k = clave(t)
    if "INEXISTENTE" in k or "OPERDOR" in k:
        return ALERTA_OPERADOR_INEXISTENTE
    if "INVALIDO" in k:
        return ALERTA_MOVIL_INVALIDO
    if "NO COINCIDEN" in k or "NOCOINCIDEN" in k:
        return ALERTA_NO_COINCIDEN
    return t


def texto_entero(v: Any) -> str:
    """OPERADOR / PLACA: un número de Excel llega como int o float; se guarda sin '.0'."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return limpiar_espacios(v)


# ── Limpieza de una fila del Excel ─────────────────────────────────────────

CAMPOS_CATEGORICOS = ("estado", "empresa", "fuente", "placa", "movil", "tipologia", "causa_inmovilizacion",
                      "ruta", "operador", "dia_semana", "alerta")
# Campos cuyo arreglo se informa al cargar (la franja y el día se unifican o rellenan sin contarse)
CAMPOS_INFORMADOS = CAMPOS_CATEGORICOS + ("hora", "descripcion_novedad")


def limpiar_texto_libre(v: Any) -> str:
    """Descripción: junta espacios repetidos dentro de cada línea y conserva los saltos de línea."""
    lineas = (" ".join(l.split()) for l in str(v if v is not None else "").splitlines())
    return "\n".join(l for l in lineas if l)


def limpiar_evento(r: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Normaliza un evento ya convertido a texto/fechas. Devuelve (evento_limpio, {campo: 1} con lo que cambió).

    Arregla espacios repetidos o finales, mayúsculas del estado, tildes de la tipología, hora y alerta;
    la franja queda siempre 'AM'/'PM' y el día en mayúsculas (si faltan, se deducen de la hora/fecha).
    """
    out = dict(r)
    for campo in CAMPOS_CATEGORICOS:
        if out.get(campo) is not None:
            out[campo] = texto_entero(out[campo])
    if "estado" in out:
        out["estado"] = estado_canonico(out["estado"])
    if "tipologia" in out:
        out["tipologia"] = tipologia_norm(out["tipologia"])
    if "alerta" in out:
        out["alerta"] = normalizar_alerta(out["alerta"])
    if out.get("hora") is not None:
        out["hora"] = hora_de(out["hora"]) or limpiar_espacios(out["hora"])
    if out.get("descripcion_novedad"):
        out["descripcion_novedad"] = limpiar_texto_libre(out["descripcion_novedad"])

    cambios = {c: 1 for c in CAMPOS_INFORMADOS if c in r and (out.get(c) or "") != (r.get(c) or "")}

    out["franja_horaria"] = franja_de(out.get("franja_horaria"), out.get("hora"))
    out["dia_semana"] = limpiar_espacios(out.get("dia_semana") or dia_semana_de(out.get("fecha_inmovilizacion"))).upper()
    return out, cambios


# ── DPV: conteo de inmovilizaciones y serie mensual ────────────────────────

def agregar_inmovilizaciones(filas: Iterable[Tuple[Any, Any, Any, Any, Any]]) -> Dict[Tuple[str, str], Dict[str, int]]:
    """filas = (fecha_inmovilizacion, empresa, movil, tipologia, estado) → {(unidad, 'YYYY-MM'): conteos}.

    conteos: eventos (todos), descartadas (Contestado Contundente), inm (los que cuentan para el DPV)
    e inm_padron / inm_buseton / inm_otra (la suma de las tres es inm).
    Las filas sin fecha o sin unidad (ni empresa ni prefijo de móvil conocido) no se cuentan.
    """
    acum: Dict[Tuple[str, str], Dict[str, int]] = {}
    for fecha, empresa, movil, tipologia, estado in filas:
        mes, unidad = mes_de(fecha), unidad_de(empresa, movil)
        if not mes or not unidad:
            continue
        e = acum.setdefault((unidad, mes), {"eventos": 0, "descartadas": 0, "inm": 0,
                                            "inm_padron": 0, "inm_buseton": 0, "inm_otra": 0})
        e["eventos"] += 1
        if not es_inmovilizacion(estado):
            e["descartadas"] += 1
            continue
        e["inm"] += 1
        t = tipologia_norm(tipologia)
        e["inm_padron" if t == "PADRON" else "inm_buseton" if t == "BUSETON" else "inm_otra"] += 1
    return acum


def calcular_dpv(km: Optional[float], inm: Optional[int]) -> Optional[float]:
    """km ÷ inmovilizaciones. None si falta el km (o es 0) o si no hubo inmovilizaciones."""
    if not km or km <= 0 or not inm or inm <= 0:
        return None
    return km / inm


def nivel_dpv(dpv: Optional[float], estandar: int = None, critico: int = None) -> Optional[str]:
    """'cumple' (≥ estándar) · 'critico' (≤ crítico) · 'alerta' (en medio) · None sin dato."""
    estandar = ESTANDAR_KM if estandar is None else estandar
    critico = CRITICO_KM if critico is None else critico
    if dpv is None:
        return None
    if dpv >= estandar:
        return "cumple"
    if dpv <= critico:
        return "critico"
    return "alerta"


def etiqueta_mes(mes: str) -> str:
    """'2026-03' → 'Mar 26'."""
    return f"{MES_LABEL[int(mes[5:7]) - 1]} {mes[2:4]}"


def _num(v: Any) -> Optional[float]:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def serie_mensual(unidad: str, km_filas: Iterable[Dict[str, Any]], inm_mapa: Dict[Tuple[str, str], Dict[str, int]],
                  legado: Iterable[Dict[str, Any]] = (), estandar: int = None, critico: int = None) -> List[Dict[str, Any]]:
    """Serie mensual de una unidad (una entrada por mes), de más antiguo a más reciente.

    · km_filas: kilómetros cargados {mes:'YYYY-MM', km_total, km_padron, km_buseton, inm_excel, dpv_excel, fuente}.
    · inm_mapa: resultado de agregar_inmovilizaciones (las inmovilizaciones se calculan SIEMPRE desde los eventos).
    · legado: filas de la tabla antigua dpv_mensual {mes, dpv, kms, varados}; solo se usan para meses sin km cargado y con DPV > 0.
    · Un mes con eventos pero sin km sale con dpv = None y origen 'sin_km' (no es 0: simplemente falta el km).
    """
    estandar = ESTANDAR_KM if estandar is None else estandar
    critico = CRITICO_KM if critico is None else critico
    km_por_mes = {f["mes"]: f for f in km_filas if f.get("mes")}
    legado_por_mes = {f["mes"]: f for f in legado if f.get("mes") and (_num(f.get("dpv")) or 0) > 0}
    meses_eventos = {m for (u, m) in inm_mapa if u == unidad}
    meses = sorted(set(km_por_mes) | set(legado_por_mes) | meses_eventos)

    out = []
    for mes in meses:
        c = inm_mapa.get((unidad, mes))
        k = km_por_mes.get(mes)
        lg = legado_por_mes.get(mes) if k is None else None
        km = _num(k.get("km_total")) if k else (_num(lg.get("kms")) if lg else None)
        km = km if km and km > 0 else None                  # 0 significa «sin km», no «cero kilómetros»
        km_p = _num(k.get("km_padron")) if k else None
        km_b = _num(k.get("km_buseton")) if k else None
        km_p = km_p if km_p and km_p > 0 else None
        km_b = km_b if km_b and km_b > 0 else None
        if c is not None:
            inm, inm_p, inm_b = c["inm"], c["inm_padron"], c["inm_buseton"]
        elif k and k.get("inm_excel") is not None:        # km del Excel pero sin eventos en la BD: se usa lo que traía el Excel
            inm, inm_p, inm_b = int(k["inm_excel"]), None, None
        elif lg:
            inm, inm_p, inm_b = int(_num(lg.get("varados")) or 0) or None, None, None
        else:
            inm, inm_p, inm_b = 0, 0, 0
        dpv = calcular_dpv(km, inm)
        if dpv is None and lg:                              # mes de la tabla antigua: se respeta el DPV que ya tenía
            dpv = _num(lg.get("dpv"))
        dpv_p, dpv_b = calcular_dpv(km_p, inm_p), calcular_dpv(km_b, inm_b)
        origen = ((k.get("fuente") or "excel") if k else "legacy" if lg else "sin_km")
        out.append({
            "mes": mes, "mes_label": etiqueta_mes(mes),
            "km": km, "km_padron": km_p, "km_buseton": km_b,
            "inm": inm, "inm_padron": inm_p, "inm_buseton": inm_b,
            "eventos": c["eventos"] if c else 0, "descartadas": c["descartadas"] if c else 0,
            "dpv": None if dpv is None else round(dpv, 1),
            "dpv_padron": None if dpv_p is None else round(dpv_p, 1),
            "dpv_buseton": None if dpv_b is None else round(dpv_b, 1),
            "nivel": nivel_dpv(dpv, estandar, critico),
            "estandar": estandar, "critico": critico,
            "origen": origen,
            "inm_excel": k.get("inm_excel") if k else None,
            "dpv_excel": _num(k.get("dpv_excel")) if k else None,
            # claves de la versión anterior de /api/dpv-mensual (por si alguna pantalla vieja aún las lee)
            "varados": inm, "kms": None if km is None else int(round(km)),
            "padron": None if km_p is None else int(round(km_p)), "buseton": None if km_b is None else int(round(km_b)),
        })
    return out
