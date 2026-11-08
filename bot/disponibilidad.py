# ═══════════════════════════════════════════════════════════════════════════════════════
#  EMANTIC PRO — Disponibilidad de flota (lógica pura: sin navegador ni red; se prueba sola)
#
#  Cruza tres fuentes y decide, bus por bus, si está DISPONIBLE o NO DISPONIBLE:
#    1. Excel de inmovilizados (mantenimiento, el que cargas a mano)      → NO DISPONIBLE · en taller
#    2. Kilometraje del día anterior (Tako, ya en EMANTIC): < 7 km         → NO DISPONIBLE · no salió de patio
#    3. P60 de Tako: último reporte que NO es de hoy                       → NO DISPONIBLE · apagado / sin transmitir
#    4. Todo lo demás                                                      → DISPONIBLE (no aparece en el archivo)
#  El orden de la lista es la PRIORIDAD: si un bus cumple varias, se muestra la primera y las otras van en la descripción.
#
#  Salida: un Excel por unidad (UF-10 = Z32-, UF-16 = Z34-) con las columnas que carga EMANTIC en «Disponibilidad de flota»:
#    MOVIL · FECHA DE CORTE · FECHA DE INGRESO A MANTENIMIENTO · DIAS DE INOPERATIVIDAD · DESCRIPCION DE LA FALLA  (+ AREA, opcional)
#
#  Uso suelto (para probar con tus archivos, sin Tako ni EMANTIC):
#    python disponibilidad.py --p60 p60.csv [--inmov-xlsx inmovilizados.xlsx] [--km-csv km_ST_2026-11-03.csv ...] [--salida carpeta]
# ═══════════════════════════════════════════════════════════════════════════════════════

import csv
import io
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

UNIDADES = {"Z32": ("UF-10", "E10"), "Z34": ("UF-16", "E16")}          # prefijo de la placa → (nombre, código de EMANTIC)
MIN_KM = 7.0

# Áreas que escribe el bot (así se distinguen de las que vienen del Excel de mantenimiento y NO se vuelven a leer como «manuales»)
AREA_KM = "No salió de patio"
AREA_P60 = "Apagado / sin reporte"
AREAS_AUTO = {AREA_KM, AREA_P60}
MARCA_AUTO = "[AUTO]"

COLUMNAS = ["MOVIL", "FECHA DE CORTE", "FECHA DE INGRESO A MANTENIMIENTO", "DIAS DE INOPERATIVIDAD", "DESCRIPCION DE LA FALLA", "AREA"]

_PLACA_RE = re.compile(r"Z3[24]\s*-?\s*\d{3,5}", re.I)


# ── Utilidades ─────────────────────────────────────────────────────────────────────────

def sin_tildes(s) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s or "")) if not unicodedata.combining(c))


def norm_enc(s) -> str:
    """Encabezado normalizado: sin tildes, mayúsculas, espacios simples."""
    return re.sub(r"\s+", " ", sin_tildes(s).upper().replace("_", " ")).strip()


def extraer_movil(texto) -> str:
    """'Z32-7073 INMOVILIZADO' → 'Z32-7073'. Vacío si no hay una placa Z32-/Z34-."""
    m = _PLACA_RE.search(str(texto or ""))
    if not m:
        return ""
    t = re.sub(r"\s+", "", m.group(0)).upper()
    return t if "-" in t else t[:3] + "-" + t[3:]


def clave(texto) -> str:
    """Clave para cruzar fuentes: 'Z32-7036' y 'Z327036' dan lo mismo (así guarda EMANTIC el kilometraje)."""
    return re.sub(r"[^A-Z0-9]", "", extraer_movil(texto) or str(texto or "")).upper()


def unidad_de(movil) -> Optional[str]:
    """'UF-10' | 'UF-16' | None según el prefijo de la placa."""
    m = extraer_movil(movil) or str(movil or "").strip().upper()
    u = UNIDADES.get(m[:3])
    return u[0] if u else None


def codigo_unidad(nombre: str) -> str:
    return next(c for n, c in UNIDADES.values() if n == nombre)


def a_numero(v) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(" ", "")
    if not t or t in ("-", "No Aplica", "N/A"):
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d+", t):                # 1.234,5 (es-CO)
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".") if re.fullmatch(r"-?\d+,\d+", t) else t
    try:
        return float(t)
    except ValueError:
        return None


_FECHA_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?")
_FECHA_LAT = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:[ ,]+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([ap])?\.?\s*m?\.?)?", re.I)


def a_fecha(v) -> Optional[datetime]:
    """datetime tal cual; texto '2026-11-03 22:21:01.017' o '3/11/2026 10:08 p. m.' → datetime sin zona (hora local de Bogotá)."""
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    t = str(v or "").strip()
    if not t:
        return None
    m = _FECHA_ISO.search(t)
    try:
        if m:
            a, mes, d, h, mi, s = m.groups()
            return datetime(int(a), int(mes), int(d), int(h or 0), int(mi or 0), int(s or 0))
        m = _FECHA_LAT.search(t)
        if m:
            d, mes, a, h, mi, s, ap = m.groups()
            h = int(h or 0)
            if ap and ap.lower() == "p" and h < 12:
                h += 12
            if ap and ap.lower() == "a" and h == 12:
                h = 0
            return datetime(int(a), int(mes), int(d), h, int(mi or 0), int(s or 0))
    except ValueError:
        return None
    return None


def _leer_texto(ruta: Path) -> str:
    raw = Path(ruta).read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", "replace")


# ── Fuente 1: P60 de Tako ──────────────────────────────────────────────────────────────

def leer_p60(ruta) -> List[dict]:
    """CSV (o .xlsx) de «Ver información P60» → [{movil, concesion, ultimo_reporte(datetime|None), odometro}]."""
    ruta = Path(ruta)
    if ruta.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(str(ruta), read_only=True, data_only=True)
        filas = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    else:
        texto = _leer_texto(ruta)
        try:
            dialecto = csv.Sniffer().sniff(texto[:4000], delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        filas = list(csv.reader(io.StringIO(texto, newline=""), dialecto))
    if not filas:
        return []
    enc = [norm_enc(c) for c in filas[0]]

    def col(*prefijos):
        for i, e in enumerate(enc):
            if any(e.startswith(p) for p in prefijos):
                return i
        return None
    i_veh, i_con, i_rep, i_odo = col("VEH", "MOVIL", "PLACA"), col("CONCES"), col("ULTIMO REP", "ULT. REP", "ULTIMO"), col("ODOM")
    if i_veh is None or i_rep is None:
        raise ValueError("El archivo de P60 no trae las columnas «Vehículo» y «Último reporte». Encabezados: " + ", ".join(str(c) for c in filas[0]))
    out = []
    for f in filas[1:]:
        if not f or i_veh >= len(f) or not str(f[i_veh] or "").strip():
            continue
        movil = extraer_movil(f[i_veh]) or str(f[i_veh]).strip()
        out.append({
            "movil": movil,
            "concesion": str(f[i_con]).strip() if i_con is not None and i_con < len(f) and f[i_con] is not None else "",
            "ultimo_reporte": a_fecha(f[i_rep]) if i_rep < len(f) else None,
            "odometro": a_numero(f[i_odo]) if i_odo is not None and i_odo < len(f) else None,
        })
    return out


# ── Fuente 2: kilometraje ──────────────────────────────────────────────────────────────

def leer_km_tako_csv(ruta) -> Dict[str, Optional[float]]:
    """CSV de «Distancias recorridas» de Tako (celda «Recorrido: 156.51 km\\nMín…\\nMáx…», o «-» sin dato) → {clave: km|None}."""
    out: Dict[str, Optional[float]] = {}
    for f in csv.reader(io.StringIO(_leer_texto(ruta), newline="")):
        if len(f) < 2 or not clave(f[0]) or not _PLACA_RE.search(f[0]):
            continue
        celda = " ".join(str(c) for c in f[1:])
        m = re.search(r"Recorrido:\s*([\d.,]+)", celda)
        out[clave(f[0])] = a_numero(m.group(1)) if m else None
    return out


# ── Fuente 3: Excel de inmovilizados (mantenimiento) ───────────────────────────────────

def leer_inmovilizados_xlsx(ruta) -> List[dict]:
    """Excel manual: todas las hojas (una por unidad o mezcladas; la unidad la da el prefijo de la placa). Fila sin placa Z32-/Z34-: se ignora."""
    from openpyxl import load_workbook
    wb = load_workbook(str(ruta), read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        filas = list(ws.iter_rows(values_only=True))
        if not filas:
            continue
        enc = [norm_enc(c) for c in filas[0]]

        def col(*opc):
            for o in opc:
                if o in enc:
                    return enc.index(o)
            return None
        i_mov = col("MOVIL", "MOVILES", "VEHICULO", "PLACA")
        if i_mov is None:
            continue
        i_cor, i_ing = col("FECHA DE CORTE", "FECHA CORTE"), col("FECHA DE INGRESO A MANTENIMIENTO", "FECHA INGRESO A MANTENIMIENTO", "FECHA DE INGRESO", "FECHA INGRESO")
        i_dia, i_des, i_are = col("DIAS DE INOPERATIVIDAD", "DIAS INOPERATIVIDAD", "DIAS"), col("DESCRIPCION DE LA FALLA", "DESCRIPCION FALLA", "DESCRIPCION"), col("AREA", "AREA RESPONSABLE", "SISTEMA")

        def g(f, i):
            return f[i] if i is not None and i < len(f) else None
        for f in filas[1:]:
            crudo = str(g(f, i_mov) or "").strip()
            if not extraer_movil(crudo):
                continue
            out.append({"movil": crudo, "fecha_corte": a_fecha(g(f, i_cor)), "fecha_ingreso": a_fecha(g(f, i_ing)),
                        "dias": a_numero(g(f, i_dia)), "descripcion": str(g(f, i_des) or "").strip(), "area": str(g(f, i_are) or "").strip() or "Sin área"})
    return out


def separar_filas_emantic(unidades: dict):
    """
    Respuesta de GET /api/disponibilidad/bot/insumos → (manuales, previas_auto).
    Lo que ya escribió el bot (área del bot o marca [AUTO]) NO es mantenimiento: se usa solo para conservar la fecha de ingreso
    de los buses que siguen no disponibles; si se tratara como «manual», un bus nunca volvería a quedar disponible.
    """
    manuales, previas = [], {}
    for _cod, u in (unidades or {}).items():
        corte = a_fecha((u or {}).get("fecha_corte"))
        for f in (u or {}).get("filas", []):
            es_auto = (f.get("area") or "") in AREAS_AUTO or str(f.get("descripcion") or "").startswith(MARCA_AUTO)
            ingreso = a_fecha(f.get("fecha_ingreso"))
            if es_auto:
                previas[clave(f.get("movil"))] = {"fecha_ingreso": ingreso}
            else:
                manuales.append({"movil": f.get("movil") or "", "fecha_corte": corte, "fecha_ingreso": ingreso, "dias": f.get("dias_inoperatividad"),
                                 "descripcion": f.get("descripcion") or "", "area": f.get("area") or "Sin área"})
    return manuales, previas


# ── Clasificación ──────────────────────────────────────────────────────────────────────

def _dias(ingreso: Optional[datetime], corte: datetime) -> float:
    return round(max(0.0, (corte - ingreso).total_seconds() / 86400), 1) if ingreso else 0.0


def clasificar(p60: List[dict], km: Optional[Dict[str, Optional[float]]], manuales: Iterable[dict], previas: Optional[dict] = None,
               ahora: Optional[datetime] = None, min_km: float = MIN_KM, fecha_km: str = "", flota: Optional[Dict[str, int]] = None,
               min_reportan: float = 0.2, max_no_disp: float = 0.6, forzar: bool = False) -> dict:
    """
    p60:      salida de leer_p60.
    km:       {clave: km del día anterior | None (sin dato)}; None = no hay kilometraje cargado → se omite la regla de km.
    manuales: filas del Excel de mantenimiento ({movil, fecha_ingreso, dias, fecha_corte, descripcion, area}).
    previas:  {clave: {'fecha_ingreso'}} de lo que el bot dejó ayer (para acumular los días).
    flota:    {'UF-10': 220, 'UF-16': 240} opcional: solo para avisar si P60 trae menos buses de los esperados.
    → {'unidades': {'UF-10': {'filas': [...], 'stats': {...}}, ...}, 'avisos': [...], 'abortar': None | 'motivo'}
    """
    ahora = ahora or datetime.now()
    hoy = ahora.date()
    previas = previas or {}
    avisos: List[str] = []
    res = {"unidades": {n: {"filas": [], "stats": {}} for n, _ in UNIDADES.values()}, "avisos": avisos, "abortar": None, "fecha": hoy.isoformat()}

    # Un bus por placa (si el P60 repite, vale el reporte más reciente)
    flota_p60: Dict[str, dict] = {}
    for b in p60:
        k = clave(b["movil"])
        if not k or not unidad_de(b["movil"]):
            continue
        if k not in flota_p60 or (b["ultimo_reporte"] or datetime.min) > (flota_p60[k]["ultimo_reporte"] or datetime.min):
            flota_p60[k] = b
    if not flota_p60:
        res["abortar"] = "El P60 no trae ningún bus Z32-/Z34-: no hay con qué decidir la disponibilidad."
        return res

    reportan = sum(1 for b in flota_p60.values() if b["ultimo_reporte"] and b["ultimo_reporte"].date() >= hoy)
    frac = reportan / len(flota_p60)
    if frac < min_reportan and not forzar:
        res["abortar"] = (f"Solo {reportan} de {len(flota_p60)} buses ({frac:.0%}) tienen reporte de hoy {hoy}: el P60 no parece actualizado "
                          f"o es muy temprano. No se genera nada (usa --forzar si es correcto).")
        return res

    if km is None:
        avisos.append("No hay kilometraje cargado en EMANTIC para " + (fecha_km or "el día anterior") + ": se omite la regla de «menos de "
                      f"{min_km:g} km». Corre antes el módulo km.")
    else:
        sin_cruce = sum(1 for k in flota_p60 if k not in km)
        if sin_cruce > 0.05 * len(flota_p60):
            avisos.append(f"{sin_cruce} buses del P60 no aparecen en el kilometraje de {fecha_km}: se toman como «sin dato» (0 km). "
                          "Si son muchos, revisa que los nombres coincidan.")

    filas: Dict[str, dict] = {}

    # 1) Mantenimiento: el Excel manual manda
    for m in manuales:
        mov = extraer_movil(m["movil"])
        k = clave(mov)
        if not k or k in filas:
            continue
        ingreso = m.get("fecha_ingreso")
        if ingreso:
            dias = _dias(ingreso, ahora)
        else:                                               # sin fecha de ingreso: lo que traía + lo que ha pasado desde ese corte
            base = float(m.get("dias") or 0)
            corte0 = m.get("fecha_corte")
            dias = round(base + max(0, (hoy - corte0.date()).days), 1) if corte0 else round(base, 1)
        filas[k] = {"movil": str(m["movil"]).strip(), "motivo": "mantenimiento", "fecha_ingreso": ingreso, "dias": dias,
                    "area": m.get("area") or "Sin área", "descripcion": m.get("descripcion") or "", "_extra": []}

    # 2) y 3) Reglas automáticas, en el orden de prioridad
    for k, b in flota_p60.items():
        motivos = []
        if km is not None:
            rec = km.get(k)
            if rec is None:
                motivos.append(("km", f"sin dato de kilometraje el {fecha_km} (no salió de patio ni transmitió)"))
            elif rec < min_km:
                motivos.append(("km", f"recorrió {rec:.1f} km el {fecha_km} (menos de {min_km:g} km): no salió de patio"))
        rep = b["ultimo_reporte"]
        if rep is None:
            motivos.append(("p60", "el P60 no trae último reporte: apagado, no transmite"))
        elif rep.date() < hoy:
            motivos.append(("p60", f"último reporte P60 el {rep:%Y-%m-%d %H:%M} (no es de hoy): apagado en patio, no transmite"))
        if k in filas:                                       # ya está por mantenimiento: solo se anota
            filas[k]["_extra"] += [t for _, t in motivos]
            continue
        if not motivos:
            continue
        tipo, texto = motivos[0]
        ing = (previas.get(k) or {}).get("fecha_ingreso") or ahora
        filas[k] = {"movil": b["movil"], "motivo": tipo, "fecha_ingreso": ing, "dias": _dias(ing, ahora),
                    "area": AREA_KM if tipo == "km" else AREA_P60,
                    "descripcion": f"{MARCA_AUTO} {texto[0].upper() + texto[1:]}", "_extra": [t for _, t in motivos[1:]]}

    # Descripción final y reparto por unidad
    for k, f in filas.items():
        if f["motivo"] != "mantenimiento" and f["_extra"]:
            f["descripcion"] += ". También: " + "; ".join(f["_extra"])
        elif f["motivo"] == "mantenimiento" and f["_extra"]:
            f["descripcion"] = (f["descripcion"] + " | " if f["descripcion"] else "") + "Además: " + "; ".join(f["_extra"])
        f["fecha_corte"] = ahora
        u = unidad_de(f["movil"])
        if u:
            res["unidades"][u]["filas"].append(f)

    total_flota = len(flota_p60) + sum(1 for k in filas if k not in flota_p60)
    for nombre, d in res["unidades"].items():
        d["filas"].sort(key=lambda f: (-(f["dias"] or 0), f["movil"]))
        en_p60 = [b for k, b in flota_p60.items() if unidad_de(b["movil"]) == nombre]
        cuenta = lambda m: sum(1 for f in d["filas"] if f["motivo"] == m)
        d["stats"] = {"en_p60": len(en_p60), "reportan_hoy": sum(1 for b in en_p60 if b["ultimo_reporte"] and b["ultimo_reporte"].date() >= hoy),
                      "mantenimiento": cuenta("mantenimiento"), "no_salio": cuenta("km"), "sin_reporte": cuenta("p60"), "no_disponibles": len(d["filas"])}
        esperada = (flota or {}).get(nombre)
        base = esperada or len(en_p60)
        d["stats"]["flota"] = base
        d["stats"]["porcentaje"] = round((base - len(d["filas"])) / base * 100, 1) if base else None
        if esperada and len(en_p60) < 0.95 * esperada:
            avisos.append(f"{nombre}: el P60 trae {len(en_p60)} buses y la flota esperada es {esperada}: pueden faltar buses (los que falten NO se marcan).")

    n_no = sum(len(d["filas"]) for d in res["unidades"].values())
    if total_flota and n_no / total_flota > max_no_disp and not forzar:
        res["abortar"] = (f"{n_no} de {total_flota} buses ({n_no / total_flota:.0%}) saldrían como NO disponibles, más del {max_no_disp:.0%} permitido: "
                          "casi seguro hay un problema con alguna fuente (¿P60 sin actualizar? ¿kilometraje incompleto?). No se genera nada (usa --forzar si es correcto).")
    return res


# ── Excel de salida ────────────────────────────────────────────────────────────────────

def escribir_excel(nombre_unidad: str, filas: List[dict], ruta) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = nombre_unidad
    ws.append(COLUMNAS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="084534")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for f in filas:
        ws.append([f["movil"], f["fecha_corte"], f["fecha_ingreso"], f["dias"], f["descripcion"], f["area"]])
    for fila in ws.iter_rows(min_row=2):
        fila[1].number_format = "yyyy-mm-dd"
        fila[2].number_format = "yyyy-mm-dd hh:mm"
        fila[3].number_format = "0.0"
    for i, ancho in enumerate([18, 14, 22, 14, 90, 24], 1):
        ws.column_dimensions[get_column_letter(i)].width = ancho
    ws.freeze_panes = "A2"
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(ruta))
    return ruta


def generar_archivos(resultado: dict, carpeta, prefijo: str = "Disponibilidad") -> List[Path]:
    """Un .xlsx por unidad con al menos un bus no disponible. Devuelve las rutas."""
    carpeta = Path(carpeta)
    out = []
    for nombre, d in resultado["unidades"].items():
        if d["filas"]:
            out.append(escribir_excel(nombre, d["filas"], carpeta / f"{prefijo}_{nombre}_{resultado['fecha']}.xlsx"))
    return out


def resumen_texto(resultado: dict) -> List[str]:
    L = []
    for nombre, d in resultado["unidades"].items():
        s = d["stats"]
        if not s:
            continue
        pct = f"{s['porcentaje']}%" if s.get("porcentaje") is not None else "—"
        L.append(f"{nombre}: {s['no_disponibles']} NO disponibles de {s['flota']} → disponibilidad {pct}  "
                 f"(taller {s['mantenimiento']} · no salió de patio {s['no_salio']} · sin reporte hoy {s['sin_reporte']};  P60: {s['reportan_hoy']}/{s['en_p60']} reportaron hoy)")
    return L


# ── Uso suelto ─────────────────────────────────────────────────────────────────────────

def _main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Genera el Excel de disponibilidad con tus propios archivos (sin Tako ni EMANTIC)")
    ap.add_argument("--p60", required=True, help="CSV exportado de «Ver información P60»")
    ap.add_argument("--inmov-xlsx", action="append", default=[], help="Excel de inmovilizados (mantenimiento); se puede repetir")
    ap.add_argument("--km-csv", action="append", default=[], help="CSV de Distancias recorridas de Tako del día anterior (ST y SF); se puede repetir")
    ap.add_argument("--fecha-km", default="", help="día de esos km (solo para el texto)")
    ap.add_argument("--min-km", type=float, default=MIN_KM)
    ap.add_argument("--ahora", help="AAAA-MM-DD HH:MM para simular otra fecha (por defecto, ahora)")
    ap.add_argument("--salida", default="salida_disponibilidad")
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args(argv)
    p60 = leer_p60(a.p60)
    manuales = [f for x in a.inmov_xlsx for f in leer_inmovilizados_xlsx(x)]
    km = None
    if a.km_csv:
        km = {}
        for x in a.km_csv:
            km.update(leer_km_tako_csv(x))
    r = clasificar(p60, km, manuales, ahora=a_fecha(a.ahora) if a.ahora else None, min_km=a.min_km, fecha_km=a.fecha_km, forzar=a.forzar)
    for av in r["avisos"]:
        print("AVISO:", av)
    if r["abortar"]:
        print("NO SE GENERA:", r["abortar"])
        return 1
    for l in resumen_texto(r):
        print(l)
    for p in generar_archivos(r, a.salida):
        print("Archivo:", p)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
