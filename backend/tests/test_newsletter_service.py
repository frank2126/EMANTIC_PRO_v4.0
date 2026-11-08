# Pruebas del servicio de correos técnicos (sin base de datos ni red)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace
from services import newsletter as nl

SECRET = "x" * 40


class TestEmail:
    def test_validos(self):
        for e in ["a@b.co", "Frank.R+emantic@Emasivo.com.co", " tec@x.org "]:
            assert nl.email_valido(e)

    def test_invalidos(self):
        for e in ["", "sin-arroba", "a@b", "a@@b.com", "a b@c.com", "a..b@c.com", "a@b.c", "x" * 260 + "@a.com"]:
            assert not nl.email_valido(e), e

    def test_normaliza(self):
        assert nl.normalizar_email("  Frank@MAIL.com ") == "frank@mail.com"

    def test_roles(self):
        assert nl.rol_suscripcion("admin") == "Administrador"
        assert nl.rol_suscripcion("tecnico") == "Tecnico"
        assert nl.rol_suscripcion("lector") == "Externo"
        assert nl.rol_suscripcion(None) == "Externo"


class TestTokenBaja:
    def test_ida_y_vuelta(self):
        t = nl.crear_token_baja(SECRET, 7, "a@b.com")
        assert nl.leer_token_baja(SECRET, t, lambda i: "a@b.com") == 7

    def test_correo_en_mayusculas_da_el_mismo_token(self):
        assert nl.crear_token_baja(SECRET, 7, "A@B.com") == nl.crear_token_baja(SECRET, 7, "a@b.com")

    def test_rechaza_manipulados(self):
        t = nl.crear_token_baja(SECRET, 7, "a@b.com")
        assert nl.leer_token_baja("otra" * 10, t, lambda i: "a@b.com") is None      # otra clave
        assert nl.leer_token_baja(SECRET, t, lambda i: "otro@b.com") is None        # el correo cambió
        assert nl.leer_token_baja(SECRET, t, lambda i: None) is None                # ya no existe
        for malo in ["", "abc", "!!!", "MTIzLmZpcm1h"]:
            assert nl.leer_token_baja(SECRET, malo, lambda i: "a@b.com") is None

    def test_no_se_puede_dar_de_baja_a_otro(self):
        t = nl.crear_token_baja(SECRET, 7, "a@b.com")
        # mismo token pero apuntando al id 8: la firma no coincide
        import base64
        falso = base64.urlsafe_b64encode(("8." + base64.urlsafe_b64decode(t + "==").decode().split(".")[1]).encode()).decode().rstrip("=")
        assert nl.leer_token_baja(SECRET, falso, lambda i: "c@d.com") is None


class TestPlantilla:
    def test_escapa_html_del_cuerpo(self):
        h = nl.plantilla_html("Hola <b>", "<script>alert(1)</script>\n\nSegundo", "https://x/y?token=a&b=1")
        assert "<script>" not in h and "&lt;script&gt;" in h
        assert "Hola &lt;b&gt;" in h
        assert h.count("<p ") == 3          # 2 párrafos del cuerpo + el pie
        assert "Cancelar suscripción" in h and "EMANTIC" in h

    def test_pagina_baja(self):
        assert "Suscripción cancelada" in nl.pagina_baja(True, "a@b.com")
        assert "&lt;" in nl.pagina_baja(True, "<x>@b.com")
        assert "Enlace no válido" in nl.pagina_baja(False)


class FakeSMTP:
    enviados, fallar_a, login_ok = [], set(), True
    def __init__(self, host, port, timeout=0): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, u, p):
        if not FakeSMTP.login_ok: raise RuntimeError("auth")
    def sendmail(self, de, a, texto):
        if a in FakeSMTP.fallar_a: raise RuntimeError("buzón lleno")
        FakeSMTP.enviados.append((a, texto))


def _cfg(**kw):
    base = dict(smtp_user="u", smtp_password="p", smtp_host="h", smtp_port=587, smtp_from="EMANTIC <n@x.com>", secret_key=SECRET)
    base.update(kw)
    return SimpleNamespace(**base)


class TestEnvio:
    def setup_method(self):
        FakeSMTP.enviados, FakeSMTP.fallar_a, FakeSMTP.login_ok = [], set(), True
        os.environ["APP_PUBLIC_URL"] = "https://emantic.test/"

    def test_envia_a_todos_con_su_propio_enlace(self):
        r = nl.enviar_boletin([(1, "a@x.com"), (2, "b@x.com")], "Asunto", "Hola", settings=_cfg(), smtp_factory=FakeSMTP)
        assert r == {"enviados": 2, "fallidos": 0, "sin_smtp": False}
        (a, ta), (b, tb) = FakeSMTP.enviados
        assert "List-Unsubscribe: <https://emantic.test/api/subscriptions/unsubscribe?token=" in ta
        assert "List-Unsubscribe-Post: List-Unsubscribe=One-Click" in ta
        assert ta != tb                                          # cada correo lleva su enlace

    def test_un_fallo_no_frena_al_resto(self):
        FakeSMTP.fallar_a = {"a@x.com"}
        r = nl.enviar_boletin([(1, "a@x.com"), (2, "b@x.com")], "A", "B", settings=_cfg(), smtp_factory=FakeSMTP)
        assert (r["enviados"], r["fallidos"]) == (1, 1)

    def test_sin_smtp_no_lanza(self):
        r = nl.enviar_boletin([(1, "a@x.com")], "A", "B", settings=_cfg(smtp_user=""), smtp_factory=FakeSMTP)
        assert r["sin_smtp"] and r["enviados"] == 0

    def test_login_fallido_cuenta_todos_como_fallidos(self):
        FakeSMTP.login_ok = False
        r = nl.enviar_boletin([(1, "a@x.com"), (2, "b@x.com")], "A", "B", settings=_cfg(), smtp_factory=FakeSMTP)
        assert (r["enviados"], r["fallidos"]) == (0, 2)
