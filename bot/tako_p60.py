# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — P60 de Tako (último reporte de cada bus)
#
#  La ruta que sigue es la misma que haces a mano:
#    menú «ITS» → pantalla «Seguimiento de flota» → botón de la tuerca (junto a «Controles del mapa»)
#    → «Panel de controles» → pestaña «Mapa» → botón «Ver información P60» → ventana «Data P60» → «Exportar».
#  Deja p60_<fecha>.<ext> (lo que descargue Tako: CSV o Excel) en la carpeta del módulo. Lo usa transmitools_bot.py (--modulo disp);
#  no se ejecuta solo.
# ═══════════════════════════════════════════════════════════

import csv
import re
import time
from datetime import date
from pathlib import Path

from tako_km import _clic, asegurar_sesion_tako

import os

TXT_BOTON_P60 = r"Ver\s+informaci[oó]n\s+P60"
TXT_EXPORTAR = r"^\s*Exportar\s*$|Export(ar)?\s+(a\s+)?(CSV|Excel)|Export\s+to\s+(CSV|Excel)"
JS_TABLA = """() => {
  const tablas = [...document.querySelectorAll('table')].filter(t => t.offsetParent !== null);
  let mejor = null;
  for (const t of tablas) { const n = t.querySelectorAll('tr').length; if (!mejor || n > mejor.querySelectorAll('tr').length) mejor = t; }
  if (!mejor) return null;
  return [...mejor.querySelectorAll('tr')].map(tr => [...tr.querySelectorAll('th,td')].map(c => c.innerText.replace(/\\s+/g, ' ').trim()));
}"""


def _tabla_en_pantalla(page):
    for fr in [page] + list(page.frames):
        try:
            filas = fr.evaluate(JS_TABLA)
        except Exception:                                    # noqa: BLE001
            continue
        if filas and len(filas) > 1:
            return filas
    return []


def _registros_en_pantalla(page):
    """Número del «462 registros» de la ventana Data P60 (None si aún no aparece)."""
    for fr in [page] + list(page.frames):
        try:
            t = fr.evaluate("() => document.body.innerText")
        except Exception:                                    # noqa: BLE001
            continue
        m = re.search(r"([\d.,]+)\s+registros", t or "", re.I)
        if m:
            return int(re.sub(r"\D", "", m.group(1)) or 0)
    return None


def _abrir_its(page, log, buscar) -> None:
    it = buscar(page, lambda f: f.get_by_text("ITS", exact=True), 20000)
    if it is None:
        raise RuntimeError("No encontré «ITS» en el menú lateral de Tako")
    _clic(it)
    if buscar(page, lambda f: f.get_by_text(re.compile(r"Seguimiento\s+de\s+flota", re.I)), 25000) is None:
        raise RuntimeError("Abrí ITS pero no apareció «Seguimiento de flota»")
    log("P60: pantalla «Seguimiento de flota» abierta.")


def _abrir_panel_controles(page, log, buscar) -> None:
    """La tuerca está junto al texto «CONTROLES DEL MAPA» (en la esquina superior del mapa)."""
    if buscar(page, lambda f: f.get_by_text(re.compile(r"Panel\s+de\s+controles", re.I)), 800) is not None:
        return                                               # ya estaba abierto
    page.wait_for_timeout(2500)                              # que termine de pintar el mapa
    intentos = [
        lambda f: f.get_by_role("button", name=re.compile(r"controles|configuraci[oó]n|ajustes|settings", re.I)),
        lambda f: f.locator("[title*='ontrol' i], [aria-label*='ontrol' i], [title*='onfig' i], [aria-label*='onfig' i]"),
        lambda f: f.get_by_text(re.compile(r"Controles\s+del\s+mapa", re.I)).locator("xpath=following::button[1]"),
        lambda f: f.get_by_text(re.compile(r"Controles\s+del\s+mapa", re.I)),
    ]
    for i, fab in enumerate(intentos, 1):
        el = buscar(page, fab, 3000 if i == 1 else 2500)
        if el is None:
            continue
        _clic(el)
        if buscar(page, lambda f: f.get_by_text(re.compile(r"Panel\s+de\s+controles", re.I)), 5000) is not None:
            log("P60: «Panel de controles» abierto.")
            return
    raise RuntimeError("No pude abrir el «Panel de controles» (la tuerca junto a «Controles del mapa»)")


def _ir_a_p60(page, log, buscar) -> None:
    tab = buscar(page, lambda f: f.get_by_role("tab", name=re.compile(r"^\s*Mapa\s*$", re.I)), 1500) or \
        buscar(page, lambda f: f.locator("button, [role=button], div, span").filter(has_text=re.compile(r"^\s*Mapa\s*$")), 2500)
    if tab is not None:
        try:
            _clic(tab)
        except Exception:                                    # noqa: BLE001 — si ya estaba en «Mapa», no pasa nada
            pass
        page.wait_for_timeout(600)
    boton = buscar(page, lambda f: f.get_by_text(re.compile(TXT_BOTON_P60, re.I)), 12000)
    if boton is None:
        raise RuntimeError("No encontré el botón «Ver información P60» en la pestaña «Mapa» del panel")
    try:
        boton.scroll_into_view_if_needed(timeout=3000)
    except Exception:                                        # noqa: BLE001
        pass
    _clic(boton)
    if buscar(page, lambda f: f.get_by_text(re.compile(r"Data\s+P60", re.I)), 25000) is None:
        raise RuntimeError("Pulsé «Ver información P60» pero no se abrió la ventana «Data P60»")
    log("P60: ventana «Data P60» abierta.")


def _esperar_registros(page, log, segundos=90) -> int:
    fin = time.time() + segundos
    n = None
    while time.time() < fin:
        n = _registros_en_pantalla(page)
        if n:
            page.wait_for_timeout(1500)
            return _registros_en_pantalla(page) or n
        page.wait_for_timeout(700)
    raise RuntimeError("La ventana Data P60 no mostró registros en %d s%s" % (segundos, " (decía 0 registros)" if n == 0 else ""))


def _exportar(page, cap, destino_base: Path, log, buscar):
    """Pulsa «Exportar». Si abre un menú (CSV / Excel) elige CSV. Devuelve la ruta guardada o None."""
    exp = buscar(page, lambda f: f.get_by_role("button", name=re.compile(TXT_EXPORTAR, re.I)), 8000) or \
        buscar(page, lambda f: f.get_by_text(re.compile(TXT_EXPORTAR, re.I)), 4000)
    if exp is None:
        return None
    antes = len(cap.items)
    _clic(exp)
    dl = cap.esperar(page, antes, 12)
    if dl is None:                                           # puede haber abierto un menú de formato
        for patron in (r"^\s*CSV\s*$|\.csv", r"Excel|XLSX"):
            op = buscar(page, lambda f, p=patron: f.get_by_text(re.compile(p, re.I)), 1500)
            if op is not None:
                antes = len(cap.items)
                _clic(op)
                dl = cap.esperar(page, antes, 60)
                if dl is not None:
                    break
    if dl is None:
        return None
    ext = Path(dl.suggested_filename or "").suffix.lower()
    ext = ext if ext in (".csv", ".xlsx", ".xls", ".xlsm") else ".csv"
    destino = destino_base.with_suffix(ext)
    dl.save_as(str(destino))
    return destino


def _contar(destino: Path) -> int:
    if destino.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(str(destino), read_only=True, data_only=True)
        return max(0, sum(1 for _ in wb.worksheets[0].iter_rows()) - 1)
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(destino, encoding=enc, newline="") as h:
                return max(0, sum(1 for _ in csv.reader(h)) - 1)
        except UnicodeDecodeError:
            continue
    return 0


def descargar_p60(context, cap, carpeta: Path, log, buscar, guardar_debug, espera_login_min=5) -> dict:
    """Devuelve {'etapa','estado','registros','archivo','detalle'} (misma forma que km/DPV/ICO)."""
    res = {"etapa": "P60", "estado": "error", "registros": None, "archivo": None, "detalle": ""}
    url = os.environ.get("TAKO_URL", "").strip()
    if not url:
        res["detalle"] = "Falta TAKO_URL en bot/.env"
        return res
    page = None
    try:
        page = context.new_page()
        page.bring_to_front()
        asegurar_sesion_tako(page, url, log, buscar, espera_login_min)
        _abrir_its(page, log, buscar)
        _abrir_panel_controles(page, log, buscar)
        _ir_a_p60(page, log, buscar)
        esperados = _esperar_registros(page, log)
        log(f"P60: la ventana muestra {esperados} registros.")
        carpeta.mkdir(parents=True, exist_ok=True)
        base = carpeta / f"p60_{date.today().isoformat()}"
        destino = _exportar(page, cap, base, log, buscar)
        if destino is None:
            log("P60: «Exportar» no descargó nada; copio la tabla de la pantalla (puede traer solo las filas visibles).")
            filas = _tabla_en_pantalla(page)
            if len(filas) < 2:
                raise RuntimeError("«Exportar» no descargó nada y no hay tabla legible en la pantalla")
            destino = base.with_suffix(".csv")
            with open(destino, "w", newline="", encoding="utf-8-sig") as h:
                csv.writer(h, delimiter=";").writerows(filas)
        n = _contar(destino)
        if esperados and n < 0.9 * esperados:
            log(f"AVISO: el archivo trae {n} filas y la pantalla decía {esperados}: puede estar incompleto.")
        res.update(estado="ok" if n else "vacia", registros=n, archivo=destino.name)
        log(f"P60: {n} vehículos guardados en {destino.name}")
        return res
    except Exception as e:                                   # noqa: BLE001
        res["detalle"] = str(e).splitlines()[0]
        if page is not None:
            guardar_debug(page, "tako_p60")
        return res
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:                                # noqa: BLE001
                pass
