# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — Kilometraje diario desde Tako
#
#  Hace lo mismo que harías a mano en la plataforma Tako:
#    Inicio de sesión → menú «ITS» → «Distancias» → «Distancias recorridas»
#    → Fecha de inicio = Fecha de fin = AYER, «Distancia por vehículo»
#    → Zona «ST» → Filtrar → «Export to CSV»   y lo mismo con la zona «SF».
#  Deja km_ST_<fecha>.csv y km_SF_<fecha>.csv en la carpeta del módulo; transmitools_bot.py los sube a EMANTIC
#  (/api/kilometraje/upload-tako), que los guarda en las mismas tablas que «Cargar kilometraje (Excel)».
#
#  Este archivo lo usa transmitools_bot.py (misma carpeta): no se ejecuta solo.
# ═══════════════════════════════════════════════════════════

import csv
import hashlib
import os
import re
import time
from datetime import date, timedelta
from pathlib import Path

TEXTO_EXPORTAR = r"Export\s+to\s+CSV|Exportar\s+(a\s+)?CSV"
TEXTO_SIN_DATOS = r"No\s+hay\s+datos\s+disponibles"


def fecha_objetivo(texto=None) -> str:
    """AAAA-MM-DD. Sin parámetro: AYER (el kilometraje del día en curso aún no está completo)."""
    if texto:
        return texto
    return (date.today() - timedelta(days=1)).isoformat()


def zonas_de(texto=None):
    t = texto or os.environ.get("TAKO_ZONAS", "ST,SF")
    return [z.strip() for z in t.split(",") if z.strip()]


def _hay_login(page) -> bool:
    try:
        return page.locator("input[type=password]").count() > 0 and page.locator("input[type=password]").first.is_visible()
    except Exception:                                        # noqa: BLE001
        return False


def _hay_menu(page, buscar) -> bool:
    return buscar(page, lambda f: f.get_by_text("ITS", exact=True), 400) is not None


def asegurar_sesion_tako(page, url, log, buscar, espera_min=5) -> None:
    """Abre Tako. Si hay sesión guardada, entra sola; si no, escribe correo/clave del .env y espera (por si pide algo más)."""
    page.goto(url, wait_until="domcontentloaded")
    fin = time.time() + 45
    estado = None
    while time.time() < fin:
        if _hay_login(page):
            estado = "login"
            break
        if _hay_menu(page, buscar):
            estado = "inicio"
            break
        page.wait_for_timeout(500)
    if estado == "inicio":
        log("Tako: sesión ya iniciada.")
        return
    if estado is None:
        raise RuntimeError("Tako no mostró ni el login ni el menú en 45 s (¿TAKO_URL correcta? ¿sin internet?)")
    page.wait_for_timeout(1500)
    usuario, clave = os.environ.get("TAKO_USUARIO", ""), os.environ.get("TAKO_CLAVE", "")
    if usuario and clave:
        campo = page.locator("input[type=email], input[type=text], input:not([type])").first
        campo.fill(usuario, timeout=8000)
        page.locator("input[type=password]").first.fill(clave, timeout=8000)
        boton = page.get_by_role("button", name=re.compile(r"Access|Acceder|Ingresar|Entrar|Iniciar", re.I))
        if boton.count():
            boton.first.click()
        else:
            page.keyboard.press("Enter")
        log("Tako: usuario y contraseña escritos desde bot/.env.")
    else:
        log("No hay TAKO_USUARIO / TAKO_CLAVE en bot/.env: escribe tus datos en la ventana de Tako.")
    limite = time.time() + espera_min * 60
    while time.time() < limite:
        page.wait_for_timeout(1000)
        try:
            if not _hay_login(page) and _hay_menu(page, buscar):
                log("Tako: sesión iniciada.")
                return
        except Exception:                                    # noqa: BLE001 — la página cambió mientras navegaba
            pass
    raise RuntimeError("Tako: se acabó el tiempo esperando el inicio de sesión.")


def _clic(loc) -> None:
    try:
        loc.click(timeout=8000)
    except Exception:                                        # noqa: BLE001 — algo encima: clic por JS
        loc.evaluate("e => e.click()")


def ir_a_distancias(page, log, buscar) -> None:
    """ITS → Distancias → Distancias recorridas. El submenú de «Distancias» es un menú flotante: se abre al pasar/clic."""
    it = buscar(page, lambda f: f.get_by_text("ITS", exact=True), 20000)
    if it is None:
        raise RuntimeError("No encontré «ITS» en el menú lateral de Tako")
    _clic(it)
    dist = buscar(page, lambda f: f.get_by_text("Distancias", exact=True), 15000)
    if dist is None:
        raise RuntimeError("No apareció «Distancias» después de abrir ITS")
    try:
        dist.hover(timeout=5000)
    except Exception:                                        # noqa: BLE001
        pass
    hija = buscar(page, lambda f: f.get_by_text("Distancias recorridas", exact=True), 2500)
    if hija is None:
        _clic(dist)
        hija = buscar(page, lambda f: f.get_by_text("Distancias recorridas", exact=True), 6000)
    if hija is None:
        raise RuntimeError("No apareció «Distancias recorridas» en el submenú de Distancias")
    _clic(hija)
    if buscar(page, lambda f: f.get_by_text(re.compile(r"Distancia\s+recorrida", re.I)), 20000) is None or \
            buscar(page, lambda f: f.locator("input[type=date]"), 10000) is None:
        raise RuntimeError("No cargó la pantalla «Distancia recorrida» (no vi los campos de fecha)")
    log("Pantalla «Distancia recorrida» abierta.")


def _poner_fechas(page, fecha, buscar) -> None:
    for n in (0, 1):
        campo = buscar(page, lambda f, n=n: f.locator("input[type=date]").nth(n), 8000)
        if campo is None:
            raise RuntimeError("No encontré el campo de fecha " + ("de inicio" if n == 0 else "de fin"))
        campo.fill(fecha)
        campo.dispatch_event("change")


JS_ELEGIR = """(sel, zona) => {
  const z = zona.trim().toUpperCase();
  const ops = [...sel.options];
  const i = ops.findIndex(o => o.textContent.trim().toUpperCase() === z || (o.value || '').trim().toUpperCase() === z);
  if (i < 0) return ops.map(o => o.textContent.trim());
  sel.selectedIndex = i;
  sel.dispatchEvent(new Event('input', {bubbles: true}));
  sel.dispatchEvent(new Event('change', {bubbles: true}));
  return true;
}"""


def _elegir_zona(page, zona, log, buscar) -> None:
    """Elige la zona. 1) <select> nativo: por JS, comparando el texto sin espacios y avisando a Vue/Angular (input+change);
    2) lista desplegable propia (div/ul): clic en el campo «Selecciona una zona» y clic en la opción."""
    z_exacto = re.compile(rf"^\s*{re.escape(zona)}\s*$", re.I)
    limite = time.time() + 12                                # la lista de zonas puede llegar por red: espera a que tenga más que «Selecciona…»
    while time.time() < limite:
        try:
            if page.evaluate("() => [...document.querySelectorAll('select')].some(s => s.options.length > 1)") or \
                    any(f.evaluate("() => [...document.querySelectorAll('select')].some(s => s.options.length > 1)") for f in page.frames):
                break
        except Exception:                                    # noqa: BLE001
            pass
        page.wait_for_timeout(400)
    for n in range(3):                                       # puede haber otros <select> en la pantalla: se prueba cada uno
        sel = buscar(page, lambda f, n=n: f.locator("select").nth(n), 8000 if n == 0 else 600)
        if sel is None:
            break
        try:
            r = sel.evaluate(JS_ELEGIR, zona)
        except Exception:                                    # noqa: BLE001
            continue
        if r is True:
            actual = sel.evaluate("e => e.options[e.selectedIndex].textContent.trim()")
            log(f"   Zona elegida: {actual}")
            return
        log(f"   El selector {n + 1} no tiene «{zona}»; sus opciones: {r}")
    # lista propia: se abre y se elige por texto
    # el campo muestra «Selecciona una zona» o la zona ya elegida (ST/SF): cualquiera de los dos sirve para abrir la lista
    conocidas = "|".join(re.escape(x) for x in zonas_de())
    campo = buscar(page, lambda f: f.get_by_text(re.compile(rf"^\s*(Selecciona\s+una\s+zona|{conocidas})\s*$", re.I)), 3000) or \
        buscar(page, lambda f: f.get_by_role("combobox"), 2000)
    if campo is None:
        raise RuntimeError("No encontré el selector de Zona")
    _clic(campo)
    page.wait_for_timeout(500)
    op = buscar(page, lambda f: f.get_by_role("option", name=z_exacto), 3000) or \
        buscar(page, lambda f: f.get_by_text(z_exacto), 3000) or \
        buscar(page, lambda f: f.locator("li, div, span, button").filter(has_text=z_exacto), 3000)
    if op is None:
        raise RuntimeError(f"No encontré la zona «{zona}» en la lista (¿cambió el nombre de la zona?)")
    _clic(op)
    log(f"   Zona elegida: {zona}")


def _huella(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def _filas(p: Path) -> int:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(p, encoding=enc, newline="") as f:
                return max(0, sum(1 for _ in csv.reader(f)) - 1)
        except UnicodeDecodeError:
            continue
    return 0


def _zona_intento(page, cap, zona, fecha, carpeta: Path, log, buscar, guardar_debug, previa: dict):
    """Una zona: fechas + zona + Filtrar + «Export to CSV». `previa` guarda la huella de la zona anterior para detectar
    que la tabla NO se refrescó (el mismo contenido para dos zonas distintas)."""
    res = {"etapa": f"Zona {zona}", "estado": "error", "registros": None, "archivo": None, "detalle": ""}
    try:
        _poner_fechas(page, fecha, buscar)
        _elegir_zona(page, zona, log, buscar)
        radio = buscar(page, lambda f: f.get_by_text("Distancia por vehículo", exact=True), 3000)
        if radio is not None:
            _clic(radio)
        boton = buscar(page, lambda f: f.get_by_role("button", name=re.compile(r"Filtrar", re.I)), 8000)
        if boton is None:
            raise RuntimeError("No encontré el botón «Filtrar»")
        _clic(boton)
        page.wait_for_timeout(1200)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:                                    # noqa: BLE001 — páginas con sondeo continuo nunca quedan «idle»
            pass
        # La pantalla ya mostraba «No hay datos» (o la tabla de la zona anterior) ANTES de que llegue la respuesta: un «sin datos»
        # solo se acepta si sigue igual tras una espera de confirmación (TAKO_ESPERA_VACIA, 12 s por defecto) y sin indicador de carga.
        espera_vacia = float(os.environ.get("TAKO_ESPERA_VACIA", "12"))
        t_clic = time.time()
        limite = t_clic + 90
        estado = None
        while time.time() < limite:
            if buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_EXPORTAR, re.I)), 300) is not None and time.time() - t_clic >= 3.5:
                estado = "datos"
                break
            cargando = buscar(page, lambda f: f.locator(".spinner, .loading, .loader, .animate-spin, [role=progressbar], [aria-busy=true]"), 200) is not None
            if not cargando and time.time() - t_clic >= espera_vacia and \
                    buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_SIN_DATOS, re.I)), 300) is not None and \
                    buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_EXPORTAR, re.I)), 200) is None:
                estado = "vacia"
                break
            page.wait_for_timeout(500)
        if estado is None:
            raise RuntimeError("Filtré pero la pantalla no mostró datos ni «No hay datos disponibles» en 90 s")
        if estado == "vacia":
            res.update(estado="vacia", registros=0, detalle=f"Tako no tiene datos de la zona {zona} para {fecha}")
            return res
        page.wait_for_timeout(1500)                          # que termine de pintar la tabla
        destino = carpeta / f"km_{zona}_{fecha}.csv"
        for intento in (1, 2):
            exp = buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_EXPORTAR, re.I)), 10000)
            if exp is None:
                raise RuntimeError("No encontré el botón «Export to CSV»")
            antes = len(cap.items)
            _clic(exp)
            dl = cap.esperar(page, antes, 60)
            if dl is None:
                raise RuntimeError("«Export to CSV» no inició ninguna descarga")
            dl.save_as(str(destino))
            h = _huella(destino)
            if previa.get("huella") == h and intento == 1:   # igual que la zona anterior: la tabla seguramente no se había refrescado
                log(f"   El archivo de {zona} salió idéntico al de la zona anterior: espero 6 s y lo bajo de nuevo.")
                page.wait_for_timeout(6000)
                continue
            previa["huella"] = h
            break
        res.update(estado="ok", registros=_filas(destino), archivo=destino.name)
        return res
    except Exception as e:                                   # noqa: BLE001 — una zona que falla no impide la otra
        res["detalle"] = str(e).splitlines()[0]
        guardar_debug(page, f"tako_{zona}")
        return res


def descargar_zona(page, cap, zona, fecha, carpeta: Path, log, buscar, guardar_debug, previa: dict, intentos: int = 3):
    """Hasta `intentos` veces (TAKO_INTENTOS, 3 por defecto) si la zona falla: no encontrar la zona, no cargar la tabla, etc."""
    intentos = int(os.environ.get("TAKO_INTENTOS", intentos))
    res = {}
    for n in range(1, intentos + 1):
        res = _zona_intento(page, cap, zona, fecha, carpeta, log, buscar, guardar_debug, previa)
        if res["estado"] != "error":
            return res
        if n < intentos:
            log(f"   Intento {n} de {intentos} falló ({res['detalle']}). Reintento en {3 * n} s…")
            page.wait_for_timeout(3000 * n)
    return res


def ejecutar(context, cap, carpeta: Path, fecha: str, zonas, log, buscar, guardar_debug, espera_login_min=5):
    """Corre todo el flujo de Tako en una pestaña nueva. Devuelve la lista de resultados por zona (misma forma que DPV/ICO)."""
    url = os.environ.get("TAKO_URL", "").strip()
    if not url:
        raise RuntimeError("Falta TAKO_URL (dirección de Tako) en bot/.env")
    page = context.new_page()
    page.bring_to_front()
    asegurar_sesion_tako(page, url, log, buscar, espera_login_min)
    ir_a_distancias(page, log, buscar)
    carpeta.mkdir(parents=True, exist_ok=True)
    log(f"Kilometraje del {fecha}, zonas: {', '.join(zonas)}")
    previa: dict = {}
    resultados = []
    for z in zonas:
        log(f"Pestaña Zona {z}")
        r = descargar_zona(page, cap, z, fecha, carpeta, log, buscar, guardar_debug, previa)
        if r["estado"] == "error":
            log(f"   ERROR: {r['detalle']}")
        resultados.append(r)
    return resultados