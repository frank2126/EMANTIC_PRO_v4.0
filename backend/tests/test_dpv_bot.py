# ═══════════════════════════════════════════════════════════
#  TESTS — carga de los CSV del bot de TransMiTools (POST /api/dpv/upload-csv)
#  Ids propios (8xxx) para no depender del orden ni de otros tests.
# ═══════════════════════════════════════════════════════════

import io
from datetime import datetime, time

from fastapi import status
from openpyxl import Workbook

from tests.test_dpv import excel_dpv, fila, subir

CABECERA = ('"IdDPV","Estado","F. Inicio DP","F. Cierre DP","Empresa","Fuente","Placa","Móvil","F. Inmovilización",'
            '"Causa de la inmovilización","Descripción de la novedad","Corrección de la novedad"')


def csv_bytes(filas, cabecera=CABECERA, enc="utf-8-sig", sep=","):
    txt = "\n".join([cabecera.replace(",", sep)] + [sep.join(f'"{c}"' for c in r) for r in filas]) + "\n"
    return txt.encode(enc)


def fila_csv(dpv, estado="Validado", placa="JTR508", movil="Z34-7133", fecha="2026-10-20 08:25:10", causa="CAJA - TEMPERATURA"):
    return [dpv, estado, "2026-10-22 00:00:00", "2026-10-28 23:59:59", "EMASIVO 16 S.A.S.", "URBANO", placa, movil, fecha, causa,
            "Se detiene", ""]


def subir_csv(client, headers, archivos):
    return client.post("/api/dpv/upload-csv", headers=headers,
                       files=[("files", (n, c, "text/csv")) for n, c in archivos])


class TestCargaCSVBot:

    def test_inserta_con_encabezados_del_portal(self, client, admin_headers, db_session):
        r = subir_csv(client, admin_headers, [("2_etapa_1_1_concesionario.csv", csv_bytes([fila_csv(8001), fila_csv(8002, placa="JTR831")]))])
        assert r.status_code == status.HTTP_200_OK, r.text
        j = r.json()
        assert j["insertados"] == 2 and j["errores"] == 0 and j["archivos"][0]["filas"] == 2
        from database import DpvRegistroDB
        e = db_session.query(DpvRegistroDB).filter_by(dpv_id=8001).one()
        assert e.hora == "08:25:10" and e.franja_horaria == "AM" and e.dia_semana == "MARTES"
        assert e.estado == "Validado" and e.placa == "JTR508" and e.movil == "Z34-7133"

    def test_no_borra_los_datos_que_el_csv_no_trae(self, client, admin_headers, db_session):
        """✅ Un registro ya cargado desde el Excel conserva tipología, ruta y operador al actualizarse con el CSV"""
        subir(client, admin_headers, "/api/dpv/upload", excel_dpv([fila(8101, estado="No Contestado", tipologia="BUSETON", ruta="Ruta B9", operador=555111)]))
        r = subir_csv(client, admin_headers, [("3.csv", csv_bytes([fila_csv(8101, estado="Contestado")]))])
        assert r.json()["actualizados"] == 1 and r.json()["insertados"] == 0
        from database import DpvRegistroDB
        db = db_session
        if True:
            o = db.query(DpvRegistroDB).filter_by(dpv_id=8101).one()
            assert o.estado == "Contestado" and o.tipologia == "BUSETON" and o.ruta == "Ruta B9" and o.operador == "555111"

    def test_tipologia_nueva_se_toma_del_mismo_movil(self, client, admin_headers, db_session):
        subir(client, admin_headers, "/api/dpv/upload", excel_dpv([fila(8201, tipologia="BUSETON", movil="Z32-8201")]))
        r = subir_csv(client, admin_headers, [("4.csv", csv_bytes([fila_csv(8202, movil="Z32-8201"), fila_csv(8203, movil="Z32-0000")]))])
        j = r.json()
        assert j["insertados"] == 2 and j["sin_tipologia"] == 1
        from database import DpvRegistroDB
        db = db_session
        if True:
            assert db.query(DpvRegistroDB).filter_by(dpv_id=8202).one().tipologia == "BUSETON"

    def test_varios_archivos_el_ultimo_manda_y_acepta_punto_y_coma(self, client, admin_headers, db_session):
        a = ("2.csv", csv_bytes([fila_csv(8301, estado="Validado")]))
        b = ("3.csv", csv_bytes([fila_csv(8301, estado="Contestado")], sep=";", enc="cp1252"))
        r = subir_csv(client, admin_headers, [a, b])
        assert r.status_code == 200, r.text
        assert r.json()["insertados"] == 1
        from database import DpvRegistroDB
        db = db_session
        if True:
            assert db.query(DpvRegistroDB).filter_by(dpv_id=8301).one().estado == "Contestado"

    def test_rechaza_otros_formatos_y_columnas_faltantes(self, client, admin_headers):
        assert subir_csv(client, admin_headers, [("x.xlsx", b"abc")]).status_code == 400
        r = subir_csv(client, admin_headers, [("x.csv", b'"A","B","C"\n"1","2","3"\n')])
        assert r.status_code == 400 and "faltan columnas" in r.json()["detail"]

    def test_solo_admin(self, client, tecnico_headers):
        r = subir_csv(client, tecnico_headers, [("2.csv", csv_bytes([fila_csv(8401)]))])
        assert r.status_code in (401, 403)
        assert client.post("/api/dpv/upload-csv", files=[("files", ("2.csv", b"x", "text/csv"))]).status_code in (401, 403)


# ═══════════════════════════════════════════════════════════
#  Botón «Actualizar DPV»: iniciar / estado / cancelar el bot
# ═══════════════════════════════════════════════════════════

class TestBotonActualizar:

    def test_estado_para_admin(self, client, admin_headers):
        r = client.get("/api/dpv/bot/estado", headers=admin_headers)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert r.json()["estado"] in ("inactivo", "corriendo", "ok", "error", "cancelado")

    def test_solo_admin(self, client, tecnico_headers):
        for metodo, url in (("get", "/api/dpv/bot/estado"), ("post", "/api/dpv/bot/iniciar"), ("post", "/api/dpv/bot/cancelar")):
            assert getattr(client, metodo)(url, headers=tecnico_headers).status_code in (401, 403)

    def test_iniciar_sin_bot_explica_que_falta(self, client, admin_headers, monkeypatch, tmp_path):
        from routes import dpv_bot
        monkeypatch.setattr(dpv_bot, "BOT_DIR", tmp_path)
        r = client.post("/api/dpv/bot/iniciar", headers=admin_headers)
        assert r.status_code == 500 and "No encuentro el bot" in r.text

    def test_corrida_completa_con_un_bot_de_mentira(self, client, admin_headers, monkeypatch, tmp_path):
        """✅ Lanza un «bot» que imprime lo mismo que el real: se ve corriendo, luego ok con el resumen"""
        import sys
        import time
        from routes import dpv_bot
        (tmp_path / "transmitools_bot.py").write_text(
            "import time\n"
            "print('[10:00:00] Sesión iniciada.', flush=True)\n"
            "time.sleep(1)\n"
            "print('[10:00:02] EMANTIC: 3 nuevos, 2 actualizados, 0 con error.', flush=True)\n", encoding="utf-8")
        monkeypatch.setattr(dpv_bot, "BOT_DIR", tmp_path)
        monkeypatch.setattr(dpv_bot, "BOT_PYTHON", sys.executable)
        monkeypatch.setattr(dpv_bot, "_proc", None)
        r = client.post("/api/dpv/bot/iniciar", headers=admin_headers)
        assert r.status_code == 200 and r.json()["estado"] == "corriendo"
        assert client.post("/api/dpv/bot/iniciar", headers=admin_headers).status_code == status.HTTP_409_CONFLICT
        for _ in range(60):
            e = client.get("/api/dpv/bot/estado", headers=admin_headers).json()
            if e["estado"] != "corriendo":
                break
            time.sleep(0.25)
        assert e["estado"] == "ok" and e["resultado"] == {"nuevos": 3, "actualizados": 2, "errores": 0}
