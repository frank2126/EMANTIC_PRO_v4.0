# ═══════════════════════════════════════════════════════════
#  EMANTIC PRO — Bot de TransMiTools (descarga de las pestañas del DPV)
#
#  Recorre lo mismo que harías a mano:
#    Inicio de sesión → «Plataforma EIC» (abre otra pestaña) → menú «Debido Proceso» → «Etapa 1» → «DPV»
#    → para cada una de las 6 pestañas (Información Habilitada, Etapa 1.1 … 1.4, Información Cerrada) → «Exportar Archivo».
#
#  Cosas que NO hace (a propósito):
#    · No resuelve ni salta el reCAPTCHA «No soy un robot». Escribe el usuario y la contraseña por ti y espera a que TÚ marques
#      la casilla y pulses INGRESAR. Como el navegador guarda la sesión en bot/perfil/, la mayoría de las veces no te lo pedirá.
#    · No guarda ni imprime la contraseña: sale de bot/.env (que Git ignora) o de variables de entorno.
#
#  Uso (desde la carpeta bot/):
#    python transmitools_bot.py                       descarga las 6 pestañas
#    python transmitools_bot.py --solo 1,2            solo las pestañas 1 y 2 (número = orden de la lista)
#    python transmitools_bot.py --desde 2026-10-01 --hasta 2026-10-26
#    python transmitools_bot.py --inspeccionar        modo calibración: vuelca los textos/botones de cada pantalla
# ═══════════════════════════════════════════════════════════

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):                       # consola de Windows (cp1252): que no falle con tildes
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve().parent
PERFIL = AQUI / "perfil"          # sesión del navegador (cookies): NO se sube a Git
DESCARGAS = AQUI / "descargas"    # archivos bajados: NO se sube a Git (son datos reales)
DEBUG = AQUI / "debug"            # capturas y HTML cuando algo falla

# ── LO QUE TIENES QUE AJUSTAR SI TRANSMITOOLS CAMBIA ─────────────────────────────────────
# Menú lateral, en orden: cada texto se busca en pantalla y se le da clic.
RUTA_MENU = ["Debido Proceso", "Etapa 1", "DPV"]
RUTA_MENU_EXACTO = {"Debido Proceso": True, "Etapa 1": True, "DPV": True}   # el texto debe coincidir exacto
# Botón de las tres rayitas (se prueba en este orden hasta que aparezca el menú)
ABRIR_MENU = [
    "[aria-label*='menu' i]", "[aria-label*='menú' i]", "button.menu-toggle", ".hamburger", "#menu-toggle",
    "header button", "header [role=button]", "nav button",
]
# Las 6 pestañas: (clave para el nombre del archivo, expresión que reconoce su rótulo en pantalla)
ETAPAS = [
    ("1_informacion_habilitada", r"Informaci[oó]n\s+Habilitada"),
    ("2_etapa_1_1_concesionario", r"Etapa\s*1\.1"),
    ("3_etapa_1_2_transmilenio", r"Etapa\s*1\.2"),
    ("4_etapa_1_3_concesionario", r"Etapa\s*1\.3"),
    ("5_etapa_1_4_transmilenio", r"Etapa\s*1\.4"),
    ("6_informacion_cerrada", r"Informaci[oó]n\s+Cerrada"),
]
NO_POR_DEFECTO = {6}                       # números de pestaña que NO se bajan salvo con --solo N o --con-cerrada (6 = Información Cerrada)
TEXTO_EXPORTAR = r"Exportar\s+Archivo"
# La plataforma «solo permite las descargas aplicando un filtro»: el bot escribe Desde/Hasta antes de exportar.
FORMATO_FECHA = "%Y-%m-%d"                 # como las muestra la tabla (2026-10-20). Cámbialo con BOT_FORMATO_FECHA en .env
DIAS_ATRAS = 31                            # filtro de respaldo si el sitio no deja exportar sin filtro: últimos 31 días (BOT_DIAS_ATRAS)
TEXTO_REGISTROS = r"No\.\s*de\s*Registros:\s*([\d.,]+)"
TEXTO_TITULO = r"\s-\sDPV"                  # el título de la tabla: «Etapa 1.1: 5 días Concesionario - DPV»
PAUSA_TRAS_CLIC = 1.5                      # segundos para que la tabla se refresque al cambiar de pestaña
# ──────────────────────────────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def cargar_env() -> None:
    """Lee bot/.env (CLAVE=valor) sin pisar las variables que ya existan en el entorno."""
    f = AQUI / ".env"
    if not f.exists():
        return
    for linea in f.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def guardar_debug(page, nombre: str) -> None:
    """Captura de pantalla + HTML de lo que se veía cuando falló (sirve para calibrar los textos)."""
    if os.environ.get("BOT_DEBUG", "1") == "0":              # BOT_DEBUG=0 en .env: no guarda capturas de errores
        return
    DEBUG.mkdir(exist_ok=True)
    base = DEBUG / f"{datetime.now():%Y%m%d_%H%M%S}_{slug(nombre)}"
    try:
        page.screenshot(path=str(base) + ".png", full_page=True)
        Path(str(base) + ".html").write_text(page.content(), encoding="utf-8")
        log(f"   (captura guardada en {base.name}.png / .html)")
    except Exception as e:                                   # noqa: BLE001 — el debug nunca debe tumbar el bot
        log(f"   (no se pudo guardar la captura: {e})")


def buscar(page, fabrica, espera_ms=15000, visible=True):
    """Busca un elemento en la página Y EN TODOS SUS MARCOS (iframes): TransMiTools/EIC es una página antigua (Menu.jsp)
    que mete el contenido dentro de marcos, y un buscador normal solo mira la página exterior (vacía).
    `fabrica(marco)` devuelve el localizador; se devuelve el primero VISIBLE o None si pasa el tiempo."""
    limite = time.time() + espera_ms / 1000
    while True:
        for marco in page.frames:
            try:
                loc = fabrica(marco)
                n = loc.count()
                if n and not visible:
                    return loc.first
                # La página guarda copias OCULTAS de cada pestaña: hay que devolver la primera VISIBLE, no la primera a secas.
                for i in range(min(n, 40)):
                    if loc.nth(i).is_visible():
                        return loc.nth(i)
            except Exception:                                # noqa: BLE001 — un marco que se está recargando
                pass
        if time.time() >= limite:
            return None
        page.wait_for_timeout(300)


def clic_texto(page, texto, exacto=False, espera=15000):
    """Clic al primer elemento visible con ese texto (enlace, botón o cualquier texto), en la página o en sus marcos."""
    patron = re.compile(rf"^\s*{re.escape(texto)}\s*$", re.I) if exacto else re.compile(re.escape(texto), re.I)
    fabricas = [lambda f: f.get_by_role("link", name=patron), lambda f: f.get_by_role("button", name=patron),
                lambda f: f.get_by_text(patron)]
    limite = time.time() + espera / 1000
    while time.time() < limite:
        for fab in fabricas:
            el = buscar(page, fab, 300)
            if el is not None:
                el.click()
                return
    raise PWTimeout(f"No encontré «{texto}» en pantalla")


ARRIBA_JS = """e => { const r = e.getBoundingClientRect(); if (!r.width || !r.height) return false;
  const t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!t && (e === t || e.contains(t)); }"""


def clic_arriba(page, texto, exacto=True, espera=15000):
    """Clic al elemento con ese texto que realmente se VE encima. El menú tipo mmenu deja apilados los paneles anteriores
    (p. ej. el DPV de Etapa 3 queda debajo del de Etapa 1): un clic al «primer visible» podía caer en el panel equivocado."""
    patron = re.compile(rf"^\s*{re.escape(texto)}\s*$", re.I) if exacto else re.compile(re.escape(texto), re.I)
    fabricas = [lambda f: f.get_by_role("link", name=patron), lambda f: f.get_by_text(patron)]
    limite = time.time() + espera / 1000
    while time.time() < limite:
        for fr in page.frames:
            for fab in fabricas:
                try:
                    cand = fab(fr).all()
                except Exception:                            # noqa: BLE001
                    continue
                for el in cand:
                    try:
                        if el.is_visible() and el.evaluate(ARRIBA_JS):
                            el.click(timeout=3000)
                            return
                    except Exception:                        # noqa: BLE001
                        continue
        page.wait_for_timeout(300)
    raise PWTimeout(f"No encontré «{texto}» visible y encima en el menú")


def panel_actual(page) -> str:
    """Texto del encabezado del panel de menú abierto (el que está junto a la flecha «<»), para comprobar dónde estamos."""
    try:
        el = page.main_frame.locator("a.mm-subclose, .mm-navbar .mm-title, .mm-navbar a").filter(has_text=re.compile(r"\S"))
        for i in range(el.count()):
            if el.nth(i).is_visible():
                return el.nth(i).inner_text().strip()
    except Exception:                                        # noqa: BLE001
        pass
    return ""


class Capturador:
    """Anota TODA descarga que inicie cualquier pestaña (también las ventanas emergentes). Los eventos de Playwright solo se
    procesan mientras se llama a su API: por eso `esperar` y `bombear` hacen pequeñas esperas."""

    def __init__(self, context):
        self.items = []
        self.mensajes = []                                   # textos de alert()/confirm() que mostró el sitio
        for p in context.pages:
            self._atar(p)
        context.on("page", self._atar)

    def _atar(self, page):
        page.on("download", lambda d: self.items.append(d))
        page.on("dialog", self._dialogo)

    def _dialogo(self, d):
        self.mensajes.append(d.message)
        try:
            d.accept()
        except Exception:                                    # noqa: BLE001
            pass

    def esperar(self, page, desde: int, segundos: float):
        limite = time.time() + segundos
        while time.time() < limite:
            if len(self.items) > desde:
                return self.items[desde]
            page.wait_for_timeout(250)
        return None


# ── 1. Sesión ─────────────────────────────────────────────────────────────────────────────

def hay_formulario_login(page) -> bool:
    return page.locator("input[type=password]").count() > 0 and page.locator("input[type=password]").first.is_visible()


def esperar_pantalla_inicial(page, timeout_s: int = 45):
    """La página (Angular) tarda en pintarse: espera al formulario de login O a la pantalla de inicio. Devuelve 'login', 'inicio' o None."""
    fin = time.time() + timeout_s
    while time.time() < fin:
        try:
            if hay_formulario_login(page):
                return "login"
            if page.get_by_text(re.compile(r"Plataforma\s+EIC", re.I)).first.is_visible():
                return "inicio"
        except Exception:                                    # noqa: BLE001 — la página puede estar cambiando
            pass
        page.wait_for_timeout(500)
    return None


def asegurar_sesion(page, url: str, espera_min: int) -> None:
    page.goto(url, wait_until="domcontentloaded")
    estado = esperar_pantalla_inicial(page)
    if estado == "inicio":
        log("Sesión ya iniciada (se reutilizó la del navegador).")
        return
    if estado is None:
        guardar_debug(page, "sin_pantalla_inicial")
        raise RuntimeError("La página no mostró ni el login ni el inicio en 45 s (¿URL correcta? ¿sin internet?)")
    page.wait_for_timeout(2500)          # a veces el formulario aparece un instante y la sesión guardada entra sola
    if not hay_formulario_login(page):
        log("Sesión ya iniciada (entró sola con la sesión guardada).")
        return
    usuario, clave = os.environ.get("TRANSMITOOLS_USUARIO", ""), os.environ.get("TRANSMITOOLS_CLAVE", "")
    if usuario and clave:
        try:
            campo_usuario = page.get_by_label(re.compile("usuario", re.I))
            if campo_usuario.count() == 0:
                campo_usuario = page.locator("input[type=text], input:not([type])")
            campo_usuario.first.fill(usuario, timeout=8000)
            page.locator("input[type=password]").first.fill(clave, timeout=8000)
            log("Usuario y contraseña escritos desde bot/.env.")
        except Exception as e:                               # noqa: BLE001
            log(f"No pude escribir las credenciales solo ({str(e).splitlines()[0]}); escríbelas tú.")
    else:
        log("No hay TRANSMITOOLS_USUARIO / TRANSMITOOLS_CLAVE en bot/.env: escribe tus datos en el navegador.")
    log(f">>> En el navegador: marca «No soy un robot» y pulsa INGRESAR. Te espero hasta {espera_min} min.")
    limite = time.time() + espera_min * 60
    while time.time() < limite:
        page.wait_for_timeout(1000)
        try:
            if not hay_formulario_login(page):
                page.wait_for_load_state("domcontentloaded")
                log("Sesión iniciada.")
                return
        except Exception:                                    # la página cambió mientras se navegaba: es buena señal
            return
    raise RuntimeError("Se acabó el tiempo esperando el inicio de sesión.")


# ── 2. Plataforma EIC → Debido Proceso → Etapa 1 → DPV ───────────────────────────────────

def abrir_plataforma(context, page):
    """«Plataforma EIC» abre otra pestaña: se devuelve esa. Si abriera en la misma, se sigue con la misma."""
    log("Abriendo «Plataforma EIC»…")
    if buscar(page, lambda f: f.get_by_text(re.compile(r"Plataforma\s+EIC", re.I)), 30000) is None:
        raise PWTimeout("No apareció la tarjeta «Plataforma EIC» en la pantalla de inicio")
    try:
        with context.expect_page(timeout=10000) as nueva:
            clic_texto(page, "Plataforma EIC")
        eic = nueva.value
    except PWTimeout:
        eic = page
    eic.wait_for_load_state("domcontentloaded")
    eic.bring_to_front()
    eic.wait_for_timeout(2000)
    return eic


def menu_visible(page) -> bool:
    return buscar(page, lambda f: f.get_by_text(re.compile(re.escape(RUTA_MENU[0]), re.I)), 400) is not None


def burger(page):
    """El botón de las tres rayitas de Menu.jsp es un <a> SIN texto en la página principal (no en el marco «funcionalidad»,
    donde hay muchos enlaces vacíos). Se excluyen las flechas del propio menú (mm-subopen / mm-subclose)."""
    cand = page.main_frame.locator("a:not(.mm-subopen):not(.mm-subclose)").filter(has_not_text=re.compile(r"\S"))
    for i in range(cand.count()):
        if cand.nth(i).is_visible():
            return cand.nth(i)
    return None


def abrir_menu_si_hace_falta(page) -> None:
    if menu_visible(page):
        return
    try:
        b = burger(page)
        if b is not None:
            b.click(timeout=3000)
            page.wait_for_timeout(800)
            if menu_visible(page):
                return
    except Exception:                                        # noqa: BLE001 — se prueban los selectores alternativos
        pass
    for sel in ABRIR_MENU:
        try:
            el = buscar(page, lambda f, sel=sel: f.locator(sel), 800)
            if el is None:
                continue
            el.click(timeout=2000)
            page.wait_for_timeout(600)
            if menu_visible(page):
                return
        except Exception:                                    # noqa: BLE001
            continue
    raise PWTimeout("No pude abrir el menú de las tres rayitas (revisa ABRIR_MENU en el bot)")


def _patron_exacto(texto: str):
    return re.compile(rf"^\s*{re.escape(texto)}\s*$", re.I)


def _clic_primero_encima(locator, espera=15000):
    limite = time.time() + espera / 1000
    while time.time() < limite:
        try:
            for el in locator.all():
                if el.is_visible() and el.evaluate(ARRIBA_JS):
                    el.click(timeout=3000)
                    return
        except Exception:                                    # noqa: BLE001
            pass
        locator.page.wait_for_timeout(300)
    raise PWTimeout("elemento del menú no encontrado")


def paso_mmenu(page, i: int) -> None:
    """Menú real de TransMiTools (jquery.mmenu): cada opción con submenú tiene DOS enlaces: la flechita vacía «a.mm-subopen» (abre el
    submenú) y el texto (que recarga el marco «funcionalidad» con la propia Menu.jsp: pantalla en blanco con el encabezado repetido).
    Por eso, para entrar a un submenú se pulsa la FLECHITA; solo la opción final (DPV) se pulsa por su texto, y dentro del panel
    cuyo título es el paso anterior (hay un «DPV» en Etapa 1, 2 y 3)."""
    main = page.main_frame
    paso = RUTA_MENU[i]
    if i < len(RUTA_MENU) - 1:
        fila = main.locator("nav li").filter(has=main.locator("a:not(.mm-subopen)", has_text=_patron_exacto(paso)))
        _clic_primero_encima(fila.locator("a.mm-subopen"))
    else:
        panel = main.locator("ul.mm-panel").filter(has=main.locator("a.mm-subclose", has_text=_patron_exacto(RUTA_MENU[i - 1])))
        _clic_primero_encima(panel.locator("a:not(.mm-subopen):not(.mm-subclose)", has_text=_patron_exacto(paso)))


def cerrar_menu(page) -> None:
    """El menú lateral queda abierto tras elegir DPV: empuja la página y su capa transparente (#mm-blocker) tapa las pestañas de
    etapas, y por eso los clics en «Etapa 1.1…» se agotaban. Se cierra pulsando fuera del menú."""
    main = page.main_frame
    def abierto():
        try:
            return bool(main.evaluate("document.documentElement.classList.contains('mm-opened')"))
        except Exception:                                    # noqa: BLE001
            return False
    for intento in range(3):
        if not abierto():
            return
        try:
            if intento == 0:
                bl = main.locator("#mm-blocker")
                if bl.count() and bl.first.is_visible():
                    bl.first.click(timeout=2000)
            elif intento == 1:
                page.keyboard.press("Escape")
            else:
                main.evaluate("""() => { try { $('#menu').trigger('close'); } catch (e) {}
                  document.documentElement.classList.remove('mm-opened', 'mm-opening'); }""")
        except Exception:                                    # noqa: BLE001
            pass
        page.wait_for_timeout(600)


def ir_a_dpv(page) -> None:
    log("Menú: " + " → ".join(RUTA_MENU))
    # Siempre se parte del menú recién cargado: así no importa en qué panel (p. ej. «Etapa 3») quedó la vez anterior.
    try:
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
    except Exception:                                        # noqa: BLE001
        pass
    abrir_menu_si_hace_falta(page)
    for i, paso in enumerate(RUTA_MENU):
        try:
            paso_mmenu(page, i)
        except PWTimeout:
            log(f"  (estructura mmenu no reconocida en «{paso}»: uso el método general)")
            clic_arriba(page, paso, exacto=RUTA_MENU_EXACTO.get(paso, True))
        page.wait_for_timeout(900)
        log(f"  clic en «{paso}»" + (f" (panel abierto: «{panel_actual(page)}»)" if i < len(RUTA_MENU) - 1 else ""))
    if buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_REGISTROS)), 40000) is None:
        raise PWTimeout("No apareció la tabla del DPV («No. de Registros») después del menú")
    cerrar_menu(page)
    log("Pantalla del DPV abierta.")


# ── 3. Descarga de cada pestaña ──────────────────────────────────────────────────────────

def registros_en_pantalla(page):
    try:
        el = buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_REGISTROS)), 5000)
        m = re.search(TEXTO_REGISTROS, el.inner_text(timeout=3000)) if el is not None else None
        return int(re.sub(r"\D", "", m.group(1))) if m else None
    except Exception:                                        # noqa: BLE001
        return None


def fechas_por_defecto():
    hoy = datetime.now()
    fmt = os.environ.get("BOT_FORMATO_FECHA", FORMATO_FECHA)
    dias = int(os.environ.get("BOT_DIAS_ATRAS", DIAS_ATRAS))
    return (hoy - timedelta(days=dias)).strftime(fmt), hoy.strftime(fmt)


def poner_fechas(page, desde, hasta) -> None:
    """Escribe Desde/Hasta como si lo teclearas (la tabla filtra al soltar cada tecla)."""
    for placeholder, valor in (("Desde", desde), ("Hasta", hasta)):
        if valor:
            campo = buscar(page, lambda f, ph=placeholder: f.get_by_placeholder(ph), 8000)
            if campo is None:
                raise PWTimeout(f"No encontré el campo «{placeholder}»")
            campo.click()
            campo.fill("")
            campo.press_sequentially(valor, delay=40)
            campo.dispatch_event("change")
            campo.dispatch_event("keyup")
            campo.press("Tab")
    if desde or hasta:
        page.wait_for_timeout(PAUSA_TRAS_CLIC * 1000)


def exportar(page, cap: Capturador, formato: str):
    """Clic en «Exportar Archivo». Si el sitio pide elegir formato (Excel/CSV), se elige el configurado."""
    boton = buscar(page, lambda f: f.locator("#ExportDataSet1"), 3000) or \
        buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_EXPORTAR, re.I)), 10000)
    if boton is None:
        raise PWTimeout("No encontré el botón «Exportar Archivo»")
    antes, msgs = len(cap.items), len(cap.mensajes)
    boton.click()
    dl = cap.esperar(page, antes, 9)
    if dl is not None:
        return dl
    patron = re.compile(r"excel|xlsx" if formato == "excel" else r"csv", re.I)
    opcion = buscar(page, lambda f: f.get_by_text(patron), 5000)
    if opcion is None:
        extra = f" Mensaje del sitio: «{cap.mensajes[-1]}»." if len(cap.mensajes) > msgs else ""
        raise PWTimeout("«Exportar Archivo» no inició ninguna descarga: la plataforma solo permite descargar aplicando un filtro "
                        "de fechas (revisa --desde/--hasta y el formato BOT_FORMATO_FECHA)." + extra)
    opcion.click()
    dl = cap.esperar(page, antes, 90)
    if dl is None:
        raise PWTimeout("Elegí el formato pero no llegó ninguna descarga")
    return dl


def huella(archivo: Path) -> str:
    """Huella del CONTENIDO (no de los bytes: un .xlsx cambia de bytes aunque los datos sean iguales)."""
    import hashlib
    h = hashlib.sha1()
    if archivo.suffix.lower() == ".xlsx":
        try:
            from openpyxl import load_workbook
            wb = load_workbook(str(archivo), read_only=True, data_only=True)
            for ws in wb.worksheets:
                for fila in ws.iter_rows(values_only=True):
                    h.update(repr(fila).encode("utf-8", "replace"))
            return h.hexdigest()
        except Exception:                                    # noqa: BLE001 — si no se puede leer, se cae a los bytes
            h = hashlib.sha1()
    h.update(archivo.read_bytes())
    return h.hexdigest()


def titulo_panel(page) -> str:
    """Texto del título de la tabla («Etapa 1.1: 5 días Concesionario - DPV»); sirve para notar si la pantalla cambió de pestaña."""
    try:
        el = buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_TITULO)), 2000)
        return el.inner_text(timeout=2000).strip() if el is not None else ""
    except Exception:                                        # noqa: BLE001
        return ""


def resumen_pantalla(page, n=220) -> str:
    """Texto visible de cada marco (recortado), para entender qué pantalla quedó cuando algo falla."""
    partes = []
    for fr in page.frames:
        try:
            t = re.sub(r"\s+", " ", fr.locator("body").inner_text(timeout=1500)).strip()
            if t:
                partes.append(t[:n])
        except Exception:                                    # noqa: BLE001
            continue
    return " | ".join(partes) or "(vacía)"


def descargar_etapa(page, cap: Capturador, etapa, carpeta: Path, formato: str, desde, hasta, incluir_vacias: bool, vistas: dict,
                    sin_filtro: bool = False) -> dict:
    """`vistas` = {huella: nombre de la pestaña}: si dos pestañas dan el MISMO contenido, es que la pantalla no cambió
    (p. ej. una pestaña bloqueada con candado) y no se guarda el archivo repetido con otro nombre."""
    clave, patron = etapa
    res = {"etapa": clave, "estado": "error", "registros": None, "archivo": None, "detalle": ""}
    antes = titulo_panel(page)
    paso = buscar(page, lambda f: f.locator("a.StepKpi", has_text=re.compile(patron, re.I)), 8000) or \
        buscar(page, lambda f: f.get_by_text(re.compile(patron, re.I)), 10000)
    if paso is None:
        raise PWTimeout("No encontré el rótulo de la pestaña en pantalla")
    paso.click(timeout=15000)
    page.wait_for_timeout(PAUSA_TRAS_CLIC * 1000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PWTimeout:
        pass                                                 # la página puede tener llamadas en segundo plano: no es un error
    if buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_REGISTROS)), 6000) is None:
        # Tras exportar una pestaña, el sitio a veces deja el marco sin la tabla: se vuelve a abrir DPV y se repite la pestaña.
        log(f"   {clave}: no apareció la tabla. Vuelvo a abrir DPV y reintento la pestaña.")
        ir_a_dpv(page)
        paso = buscar(page, lambda f: f.locator("a.StepKpi", has_text=re.compile(patron, re.I)), 8000) or \
            buscar(page, lambda f: f.get_by_text(re.compile(patron, re.I)), 10000)
        if paso is None:
            raise PWTimeout("No encontré el rótulo de la pestaña en pantalla")
        paso.click(timeout=15000)
        page.wait_for_timeout(PAUSA_TRAS_CLIC * 1000)
        if buscar(page, lambda f: f.get_by_text(re.compile(TEXTO_REGISTROS)), 8000) is None:
            raise PWTimeout("La pestaña no muestra la tabla del DPV. Pantalla: " + resumen_pantalla(page))
    poner_fechas(page, desde, hasta)
    res["registros"] = registros_en_pantalla(page)
    log(f"   {clave}: {res['registros'] if res['registros'] is not None else '?'} registros en pantalla")
    if vistas and titulo_panel(page) == antes and antes:
        log("   AVISO: el título de la tabla no cambió al pulsar la pestaña (¿está bloqueada?). Verifico con el contenido.")
    if res["registros"] == 0 and not incluir_vacias:
        res.update(estado="vacia", detalle="0 registros: no se descarga (usa --incluir-vacias para bajarla igual)")
        return res
    try:
        dl = exportar(page, cap, formato)
    except PWTimeout:
        if desde or hasta or sin_filtro:
            raise
        d, h = fechas_por_defecto()
        log(f"   El sitio no dejó exportar sin filtro: reintento con fechas {d} → {h}")
        poner_fechas(page, d, h)
        res["registros"] = registros_en_pantalla(page)
        dl = exportar(page, cap, formato)
    ext = Path(dl.suggested_filename).suffix or (".xlsx" if formato == "excel" else ".csv")
    destino = carpeta / f"{clave}{ext}"
    dl.save_as(str(destino))
    h = huella(destino)
    if h in vistas:
        destino.unlink()
        res.update(detalle=f"el contenido es idéntico al de «{vistas[h]}»: la pantalla no cambió de pestaña (¿bloqueada o sin permiso?). No se guardó.")
        return res
    vistas[h] = clave
    res.update(estado="ok", archivo=destino.name, detalle=f"{destino.stat().st_size / 1024:.0f} KB")
    return res


# ── Modo calibración ─────────────────────────────────────────────────────────────────────

_JS_VOLCADO = """() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' }
  const t = e => (e.innerText || e.value || '').trim().replace(/\\s+/g, ' ').slice(0, 80)
  const pick = sel => [...document.querySelectorAll(sel)].filter(vis).map(e => ({
    tag: e.tagName.toLowerCase(), texto: t(e), id: e.id || '', clase: (e.className && e.className.toString().slice(0, 60)) || '',
    aria: e.getAttribute('aria-label') || '', placeholder: e.getAttribute('placeholder') || '', type: e.getAttribute('type') || '',
    onclick: (e.getAttribute('onclick') || '').slice(0, 80)
  }))
  return { url: location.href, titulo: document.title,
           enlaces: pick('a'), botones: pick("button, [role=button], input[type=button], input[type=submit], img[onclick], [onclick]"),
           campos: pick('input, select, textarea'), rotulos: pick('h1, h2, h3, h4, li, .step, [class*=step], [class*=titulo]').slice(0, 60),
           encabezados_tabla: pick('th').map(x => x.texto),
           mensajes: [...document.querySelectorAll('.modal.in, .modal.show, .swal2-container, .swal-modal, .bootbox, [role=dialog], .alert')]
                       .filter(vis).map(e => (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 400)) }
}"""


def volcar_pantalla(page, n: int) -> Path:
    """Lista lo que el bot puede «ver» en la página y en CADA marco: textos de enlaces/botones/campos y encabezados de las
    tablas. No incluye el contenido de las filas (datos)."""
    DEBUG.mkdir(exist_ok=True)
    marcos = []
    for marco in page.frames:
        try:
            info = marco.evaluate(_JS_VOLCADO)
            info["marco_nombre"] = marco.name
            info["es_principal"] = marco == page.main_frame
            marcos.append(info)
        except Exception as e:                               # noqa: BLE001
            marcos.append({"url": marco.url, "error": str(e).splitlines()[0]})
    f = DEBUG / f"inspeccion_{n}_{datetime.now():%H%M%S}.json"
    f.write_text(json.dumps({"pagina": page.url, "marcos": marcos}, ensure_ascii=False, indent=1), encoding="utf-8")
    page.screenshot(path=str(f.with_suffix(".png")), full_page=True)
    return f


def modo_inspeccion(context, cap: Capturador) -> None:
    log("MODO CALIBRACIÓN: navega tú a cada pantalla (con Alt+Tab, sin hacer clic en esta ventana) y vuelve aquí a pulsar ENTER.")
    log("Escribe 'salir' para terminar. Si haces clic en «Exportar Archivo», el bot te dirá si el sitio descargó algo.")
    n = 0
    vistos = 0
    mensajes_vistos = 0
    carpeta = DESCARGAS / "inspeccion"
    while True:
        r = input("ENTER = registrar la pantalla actual · 'salir' = terminar > ").strip().lower()
        pagina = context.pages[-1]
        pagina.wait_for_timeout(800)                         # deja que Playwright reciba los eventos de descarga
        while vistos < len(cap.items):
            d = cap.items[vistos]
            vistos += 1
            carpeta.mkdir(parents=True, exist_ok=True)
            destino = carpeta / f"{datetime.now():%H%M%S}_{d.suggested_filename}"
            d.save_as(str(destino))
            log(f"   >>> DESCARGA DETECTADA: «{d.suggested_filename}» ({destino.stat().st_size / 1024:.0f} KB) guardada en {destino}")
        for m in cap.mensajes[mensajes_vistos:]:
            log(f"   >>> MENSAJE DEL SITIO (alert): {m}")
        mensajes_vistos = len(cap.mensajes)
        if r in ("salir", "s", "q"):
            break
        n += 1
        log(f"   pantalla guardada: {volcar_pantalla(pagina, n)}")
    if not cap.items:
        log("No se detectó ninguna descarga en esta sesión.")
    log(f"Listo. Envíame los archivos de {DEBUG} (.json y .png) y los encabezados del archivo descargado.")


def ruta_chrome():
    """Busca chrome.exe (Windows) o el comando de Chrome (Linux/Mac). Se puede fijar con BOT_CHROME_RUTA en .env."""
    ruta = os.environ.get("BOT_CHROME_RUTA", "").strip()
    candidatos = [ruta] if ruta else [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidatos:
        if c and Path(c).exists():
            return c
    return None


def abrir_chrome_propio(url: str, puerto: int, avisar: bool = True) -> int:
    """Abre TU Chrome normal (sin automatizar) con un puerto de conexión. Tú inicias sesión y marcas el reCAPTCHA como siempre;
    después el bot se conecta con --conectar y solo hace la descarga."""
    chrome = ruta_chrome()
    if not chrome:
        log("No encontré Chrome. Escribe su ruta en bot/.env como BOT_CHROME_RUTA=C:\\...\\chrome.exe")
        return 2
    perfil = AQUI / "perfil_chrome"
    extra = os.environ.get("BOT_CHROME_EXTRA", "").split()      # solo para pruebas en servidores sin pantalla
    subprocess.Popen([chrome, f"--remote-debugging-port={puerto}", f"--user-data-dir={perfil}", "--no-first-run", *extra, url])
    if not avisar:
        return 0
    log("Chrome abierto. 1) Inicia sesión en TransMiTools (marca tú el «No soy un robot»).")
    log(f"2) Déjalo abierto y, en otra terminal, ejecuta:  python transmitools_bot.py --conectar   (puerto {puerto})")
    return 0


# ── Principal ────────────────────────────────────────────────────────────────────────────

# ── 4. Subida a EMANTIC ──────────────────────────────────────────────────────────────────

def subir_a_emantic(carpeta: Path) -> int:
    """Sube los CSV de una carpeta de descargas a EMANTIC (POST /api/dpv/upload-csv), en orden de etapa. 0 = bien."""
    try:
        import requests
    except ImportError:
        log("Falta la librería «requests». Ejecuta:  pip install requests")
        return 2
    base = os.environ.get("EMANTIC_URL", "http://localhost:8000").rstrip("/")
    usuario, clave = os.environ.get("EMANTIC_USUARIO", "").strip(), os.environ.get("EMANTIC_CLAVE", "")
    if not usuario or not clave:
        log("Falta EMANTIC_USUARIO / EMANTIC_CLAVE en bot/.env (un usuario administrador de tu app).")
        return 2
    archivos = sorted(carpeta.glob("*.csv"))                 # 2_…, 3_…, 4_…: el nombre empieza con el número de etapa
    if not archivos:
        log(f"No hay archivos .csv en {carpeta}: nada que subir (¿el bot bajó en formato Excel? usa BOT_FORMATO=csv).")
        return 2
    try:
        r = requests.post(f"{base}/api/auth/login", json={"username": usuario, "password": clave}, timeout=30)
        if r.status_code != 200:
            log(f"EMANTIC rechazó el usuario/clave ({r.status_code}): {r.text[:200]}")
            return 1
        token = r.json()["access_token"]
        log(f"Subiendo {len(archivos)} archivo(s) a {base}…")
        r = requests.post(f"{base}/api/dpv/upload-csv", headers={"Authorization": f"Bearer {token}"}, timeout=300,
                          files=[("files", (a.name, a.read_bytes(), "text/csv")) for a in archivos])
    except requests.exceptions.ConnectionError:
        log(f"No pude conectar con EMANTIC en {base}. ¿Está encendido el backend? (EMANTIC_URL en bot/.env)")
        return 1
    if r.status_code != 200:
        log(f"EMANTIC respondió {r.status_code}: {r.text[:300]}")
        return 1
    j = r.json()
    log(f"EMANTIC: {j.get('insertados', 0)} nuevos, {j.get('actualizados', 0)} actualizados, {j.get('errores', 0)} con error.")
    if j.get("sin_tipologia"):
        log(f"   Aviso: {j['sin_tipologia']} registro(s) nuevos sin tipología (móvil que no estaba en el DPV): complétalos en la app.")
    for e in j.get("errores_detalle", [])[:5]:
        log(f"   {e}")
    return 0


def conectar_cdp(p, puerto: int, url_abrir=None):
    """Se conecta al Chrome con puerto de depuración. Con `url_abrir` (modo --auto) lo abre si no estaba abierto."""
    destino = f"http://127.0.0.1:{puerto}"
    try:
        return p.chromium.connect_over_cdp(destino)
    except Exception as e:                                   # noqa: BLE001
        if url_abrir is None:
            log(f"No pude conectarme al Chrome en el puerto {puerto} ({str(e).splitlines()[0]}).")
            log("Primero ejecuta:  python transmitools_bot.py --abrir-chrome   e inicia sesión en esa ventana.")
            return None
    log("El Chrome del bot no estaba abierto: lo abro.")
    if abrir_chrome_propio(url_abrir, puerto, avisar=False) != 0:
        return None
    limite = time.time() + 40
    while time.time() < limite:
        try:
            return p.chromium.connect_over_cdp(destino)
        except Exception:                                    # noqa: BLE001
            time.sleep(1)
    log("El Chrome no respondió a tiempo.")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Descarga las pestañas del DPV de TransMiTools")
    ap.add_argument("--solo", help="números de las pestañas a bajar, p. ej. 1,2 (por defecto, las 5 primeras)")
    ap.add_argument("--desde", help="fecha inicial del filtro (AAAA-MM-DD, como la pida la pantalla)")
    ap.add_argument("--hasta", help="fecha final del filtro")
    ap.add_argument("--formato", choices=["excel", "csv"], default=None, help="si el sitio pregunta el formato (por defecto, excel)")
    ap.add_argument("--sin-filtro", action="store_true", help="no escribir fechas (la plataforma suele no dejar descargar así)")
    ap.add_argument("--subir", action="store_true", help="al terminar de descargar, sube los CSV a EMANTIC (también con BOT_SUBIR=1)")
    ap.add_argument("--subir-carpeta", metavar="RUTA", help="solo sube a EMANTIC los CSV de esa carpeta (no abre el navegador)")
    ap.add_argument("--con-cerrada", action="store_true", help="incluir también «Información Cerrada» (por defecto no se baja)")
    ap.add_argument("--incluir-vacias", action="store_true", help="descargar también las pestañas con 0 registros")
    ap.add_argument("--abrir-chrome", action="store_true", help="abre TU Chrome para que inicies sesión tú (sin automatizar) y sale")
    ap.add_argument("--conectar", action="store_true", help="en vez de abrir otro navegador, se conecta al Chrome abierto con --abrir-chrome")
    ap.add_argument("--auto", action="store_true", help="como --conectar, pero abre el Chrome del bot si no estaba abierto (lo usa el botón de la app)")
    ap.add_argument("--inspeccionar", action="store_true", help="modo calibración (no descarga nada)")
    ap.add_argument("--url", default=None, help="dirección de inicio (por defecto TRANSMITOOLS_URL del .env)")
    args = ap.parse_args()
    if args.auto:
        args.conectar = True

    cargar_env()
    if args.subir_carpeta:
        return subir_a_emantic(Path(args.subir_carpeta))
    url = args.url or os.environ.get("TRANSMITOOLS_URL", "").strip()
    if not url:
        log("Falta TRANSMITOOLS_URL (dirección de inicio de TransMiTools) en bot/.env")
        return 2
    puerto = int(os.environ.get("BOT_PUERTO_CDP", "9222"))
    if args.abrir_chrome:
        return abrir_chrome_propio(url, puerto)
    formato = args.formato or os.environ.get("BOT_FORMATO", "excel").lower()
    fmt_fecha = os.environ.get("BOT_FORMATO_FECHA", FORMATO_FECHA)
    if args.desde or args.hasta:
        log(f"Filtro de fechas: {args.desde or '—'} → {args.hasta or '—'}")
    else:
        log("Sin filtro de fechas: se exporta directo; si el sitio no deja, se aplica el filtro por defecto.")
    espera_login = int(os.environ.get("BOT_ESPERA_LOGIN_MIN", "5"))
    etapas = [e for i, e in enumerate(ETAPAS, 1) if args.con_cerrada or i not in NO_POR_DEFECTO]
    if args.solo:
        idx = {int(x) for x in args.solo.split(",") if x.strip().isdigit()}
        etapas = [e for i, e in enumerate(ETAPAS, 1) if i in idx]
        if not etapas:
            log("--solo no coincide con ninguna pestaña (usa números del 1 al 6)")
            return 2

    carpeta = DESCARGAS / datetime.now().strftime("%Y%m%d_%H%M")
    resultados = []
    with sync_playwright() as p:
        browser = None
        if args.conectar:
            browser = conectar_cdp(p, puerto, url if args.auto else None)
            if browser is None:
                return 2
            context = browser.contexts[0]
        else:
            # chromium_sandbox=True: no se usa --no-sandbox (Chrome muestra «no se admite el indicador --no-sandbox»)
            opciones = dict(user_data_dir=str(PERFIL), headless=os.environ.get("BOT_HEADLESS") == "1", accept_downloads=True,
                            viewport=None, args=["--start-maximized"], locale="es-CO", timezone_id="America/Bogota",
                            chromium_sandbox=os.environ.get("BOT_SIN_SANDBOX") != "1")   # BOT_SIN_SANDBOX=1 solo para servidores/Linux como root
            canal = os.environ.get("BOT_NAVEGADOR", "chrome").strip().lower()
            try:
                context = p.chromium.launch_persistent_context(**opciones, **({"channel": canal} if canal in ("chrome", "msedge") else {}))
            except Exception as e:                           # noqa: BLE001
                log(f"No pude abrir «{canal}» ({str(e).splitlines()[0]}); pruebo con Chromium de Playwright.")
                context = p.chromium.launch_persistent_context(**opciones)
        try:
            inicio = context.new_page() if args.conectar else (context.pages[0] if context.pages else context.new_page())
            cap = Capturador(context)
            asegurar_sesion(inicio, url, espera_login)
            eic = abrir_plataforma(context, inicio)
            if args.inspeccionar:
                modo_inspeccion(context, cap)
                return 0
            ir_a_dpv(eic)
            carpeta.mkdir(parents=True, exist_ok=True)
            vistas: dict = {}
            for etapa in etapas:
                log(f"Pestaña {etapa[0]}")
                try:
                    r = descargar_etapa(eic, cap, etapa, carpeta, formato, args.desde, args.hasta, args.incluir_vacias, vistas, args.sin_filtro)
                    if r["estado"] == "error":
                        log(f"   ERROR: {r['detalle']}")
                        guardar_debug(eic, etapa[0])
                    resultados.append(r)
                except Exception as e:                       # noqa: BLE001 — una pestaña que falla no impide las demás
                    log(f"   ERROR: {str(e).splitlines()[0]}")
                    guardar_debug(eic, etapa[0])
                    resultados.append({"etapa": etapa[0], "estado": "error", "registros": None, "archivo": None, "detalle": str(e).splitlines()[0]})
        except Exception as e:                               # noqa: BLE001
            log(f"ERROR GENERAL: {str(e).splitlines()[0]}")
            for pg in context.pages[-1:]:
                guardar_debug(pg, "general")
            return 1
        finally:
            if browser is not None:
                browser.close()                      # solo se desconecta: tu Chrome sigue abierto
            else:
                context.close()

    if carpeta.exists():
        (carpeta / "manifiesto.json").write_text(json.dumps(
            {"fecha": datetime.now().isoformat(timespec="seconds"), "desde": args.desde, "hasta": args.hasta, "etapas": resultados},
            ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nRESUMEN")
    for r in resultados:
        print(f"  [{ {'ok': 'OK', 'vacia': '--', 'error': 'XX'}[r['estado']] }] {r['etapa']:<28} registros={r['registros']}  {r['archivo'] or r['detalle']}")
    if carpeta.exists():
        print(f"\nArchivos en: {carpeta}")
    rc = 0 if all(r["estado"] != "error" for r in resultados) else 1
    if (args.subir or os.environ.get("BOT_SUBIR") == "1") and carpeta.exists():
        rc_sub = subir_a_emantic(carpeta)
        rc = rc or rc_sub
    return rc


if __name__ == "__main__":
    sys.exit(main())
