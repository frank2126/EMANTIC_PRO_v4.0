# Pruebas de las reglas de solicitudes (sin base de datos ni red)
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace
from services import solicitudes as sv
from services import newsletter as nl


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except sv.ErrorValidacion as e:
        return str(e)
    return None


class TestNueva:
    def test_valida_y_limpia(self):
        r = sv.validar_nueva("temperatura", "  Revisión de temperatura del Z32-7036\r\n\r\n\r\n\r\nurgente  ", " z32-7036 ", "URGENTE")
        assert r == {"tipo": "temperatura", "mensaje": "Revisión de temperatura del Z32-7036\n\nurgente", "movil": "Z32-7036", "prioridad": "urgente"}

    def test_tipo_invalido(self):
        assert "tipo" in raises(sv.validar_nueva, "hack", "mensaje largo suficiente", "", "normal")

    def test_mensaje_corto_y_largo(self):
        assert "mínimo" in raises(sv.validar_nueva, "otro", "corto", "", "normal")
        assert "máximo" in raises(sv.validar_nueva, "otro", "x" * 601, "", "normal")
        assert raises(sv.validar_nueva, "otro", "x" * 600, "", "normal") is None

    def test_prioridad_invalida(self):
        assert "Prioridad" in raises(sv.validar_nueva, "otro", "mensaje largo suficiente", "", "ya")

    def test_movil_opcional_y_validado(self):
        assert sv.validar_nueva("otro", "mensaje largo suficiente", None, None)["movil"] == ""
        assert raises(sv.validar_nueva, "otro", "mensaje largo suficiente", "<script>", "normal")
        assert raises(sv.validar_nueva, "otro", "mensaje largo suficiente", "Z" * 31, "normal")

    def test_quita_caracteres_de_control(self):
        assert sv.limpiar_texto("a\x00b\x07c\td") == "abc\td"

    def test_claves_de_tipos_coinciden_con_el_frontend(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "utils", "solicitudesUtils.js"), encoding="utf-8").read() \
            if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "utils", "solicitudesUtils.js")) else None
        if src is not None:
            for k in sv.TIPOS:
                assert f"'{k}'" in src, k


def sol(**kw):
    base = dict(estado="pendiente", respuesta="", respondido_por="", respondido_at=None, visto_solicitante=True)
    base.update(kw)
    return SimpleNamespace(**base)


class TestGestion:
    AHORA = datetime.datetime(2026, 11, 3, 20, 0, 0)

    def test_responder_pasa_a_atendida_y_queda_sin_leer(self):
        s = sol()
        r = sv.aplicar_gestion(s, None, "Ya está programado para el jueves.", "Admin", self.AHORA)
        assert r == {"cambio_respuesta": True, "cambio_estado": True}
        assert (s.estado, s.respondido_por, s.respondido_at, s.visto_solicitante) == ("atendida", "Admin", self.AHORA, False)

    def test_en_proceso_sin_respuesta(self):
        s = sol()
        r = sv.aplicar_gestion(s, "en_proceso", None, "Admin")
        assert s.estado == "en_proceso" and r["cambio_respuesta"] is False and s.visto_solicitante is True

    def test_atendida_exige_respuesta(self):
        s = sol()
        assert "respuesta" in raises(sv.aplicar_gestion, s, "atendida", "", "Admin")
        assert s.estado == "pendiente"

    def test_cerrar_con_respuesta_previa(self):
        s = sol(estado="atendida", respuesta="Listo")
        sv.aplicar_gestion(s, "cerrada", None, "Admin")
        assert s.estado == "cerrada" and s.respuesta == "Listo"

    def test_misma_respuesta_no_vuelve_a_marcar_sin_leer(self):
        s = sol(estado="atendida", respuesta="Listo", visto_solicitante=True)
        r = sv.aplicar_gestion(s, "cerrada", "Listo", "Admin")
        assert r["cambio_respuesta"] is False and s.visto_solicitante is True

    def test_nada_que_hacer_y_estado_invalido(self):
        assert "nada" in raises(sv.aplicar_gestion, sol(), None, "  ", "Admin")
        assert "Estado" in raises(sv.aplicar_gestion, sol(), "borrada", None, "Admin")

    def test_respuesta_muy_larga(self):
        assert "larga" in raises(sv.aplicar_gestion, sol(), None, "x" * 4001, "Admin")


class TestSerializar:
    def test_campos_y_sin_leer(self):
        s = SimpleNamespace(id=3, tipo="programacion", movil="Z1", mensaje="m", prioridad="normal", estado="atendida", respuesta="ok",
                            respondido_por="A", respondido_at=datetime.datetime(2026, 11, 3, 20, 0, 5, 999), created_at=datetime.datetime(2026, 11, 3, 19, 0, 0),
                            visto_solicitante=False, solicitante="Frank", username="frank")
        d = sv.serializar(s, incluir_solicitante=True)
        assert d["tipo_label"] == "Sugerencias de programación de móviles" and d["sin_leer"] is True
        assert d["created_at"] == "2026-11-03T19:00:00Z" and d["respondido_at"] == "2026-11-03T20:00:05Z"
        assert d["solicitante"] == "Frank"
        assert "solicitante" not in sv.serializar(s)


class FakeSMTP:
    enviados = []
    def __init__(self, h, p, timeout=0): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, u, p): pass
    def sendmail(self, de, a, t): FakeSMTP.enviados.append((a, t))


class TestAviso:
    CFG = SimpleNamespace(smtp_user="u", smtp_password="p", smtp_host="h", smtp_port=587, smtp_from="n@x.com", secret_key="k" * 40)

    def test_envia_sin_enlace_de_baja(self):
        FakeSMTP.enviados = []
        assert nl.enviar_aviso("a@x.com", "Asunto", "Título <b>", "Cuerpo", settings=self.CFG, smtp_factory=FakeSMTP)
        _, t = FakeSMTP.enviados[0]
        assert "List-Unsubscribe" not in t and "Cancelar suscripción" not in t.replace("=", "")

    def test_correo_invalido_o_sin_smtp(self):
        assert not nl.enviar_aviso("malo", "A", "T", "C", settings=self.CFG, smtp_factory=FakeSMTP)
        cfg = SimpleNamespace(**{**vars(self.CFG), "smtp_user": ""})
        assert not nl.enviar_aviso("a@x.com", "A", "T", "C", settings=cfg, smtp_factory=FakeSMTP)
