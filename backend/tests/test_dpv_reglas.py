# ═══════════════════════════════════════════════════════════
#  TESTS DPV — reglas de negocio (módulo puro dpv_reglas.py, sin base de datos)
#  DPV = km ÷ inmovilizaciones · «Contestado Contundente» no cuenta · el mes se cuenta completo (día con hora)
# ═══════════════════════════════════════════════════════════

from datetime import date, datetime, time

import dpv_reglas as r


def ev(dia, estado="No Contestado", empresa="EMASIVO 10 S.A.S.", movil="Z32-9001", tipologia="PADRON"):
    """(fecha_inmovilizacion, empresa, movil, tipologia, estado) como los entrega la consulta."""
    return (dia, empresa, movil, tipologia, estado)


class TestTexto:

    def test_limpiar_espacios(self):
        assert r.limpiar_espacios("  Ruta   A100 \xa0") == "Ruta A100"
        assert r.limpiar_espacios(None) == ""

    def test_estado_canonico_unifica_mayusculas_y_espacios(self):
        """✅ 'No Contestado ' y 'contestado contundente' se escriben igual que el resto"""
        assert r.estado_canonico("No Contestado ") == "No Contestado"
        assert r.estado_canonico("contestado  contundente") == "Contestado Contundente"
        assert r.estado_canonico("Validado") == "Validado"
        assert r.estado_canonico("Estado nuevo ") == "Estado nuevo"      # desconocido: se conserva

    def test_tipologia_sin_espacios_ni_tildes(self):
        assert r.tipologia_norm("BUSETON ") == "BUSETON"
        assert r.tipologia_norm("Padrón") == "PADRON"
        assert r.tipologia_norm(None) == ""

    def test_unidad_por_empresa_o_por_prefijo_del_movil(self):
        assert r.unidad_de("EMASIVO 10 S.A.S.") == "E10"
        assert r.unidad_de("EMASIVO 16 S.A.S.", "Z32-1") == "E16"       # manda la empresa
        assert r.unidad_de("", "Z34-9001") == "E16"
        assert r.unidad_de("", "z32-4021") == "E10"
        assert r.unidad_de("OTRA", "X99-1") == ""


class TestInmovilizacion:

    def test_solo_contestado_contundente_no_cuenta(self):
        """✅ Misma regla del Excel: ESTADO <> «Contestado Contundente»"""
        assert not r.es_inmovilizacion("Contestado Contundente")
        assert not r.es_inmovilizacion("  contestado CONTUNDENTE ")
        for estado in ("No Contestado", "Contestado No Contundente", "Contestado", "Aceptado", "Validado", "", None):
            assert r.es_inmovilizacion(estado), estado

    def test_el_mes_se_cuenta_completo_aunque_el_ultimo_dia_traiga_hora(self):
        """✅ El COUNTIFS del Excel ('<=2026-01-31') dejaba fuera los eventos del último día con hora"""
        m = r.agregar_inmovilizaciones([
            ev(datetime(2026, 1, 1, 0, 0)), ev(datetime(2026, 1, 31, 0, 0)),
            ev(datetime(2026, 1, 31, 18, 45)),                    # último día, con hora → SÍ cuenta
            ev(datetime(2026, 2, 1, 0, 5)),                       # ya es febrero
        ])
        assert m[("E10", "2026-01")]["inm"] == 3
        assert m[("E10", "2026-02")]["inm"] == 1

    def test_conteos_por_unidad_estado_y_tipologia(self):
        m = r.agregar_inmovilizaciones([
            ev(date(2026, 3, 5)),
            ev(date(2026, 3, 6), tipologia="BUSETON "),                            # espacio final
            ev(date(2026, 3, 7), estado="Contestado Contundente"),                 # descartada
            ev(date(2026, 3, 8), estado="Validado", tipologia="BUSETON"),
            ev(date(2026, 3, 9), empresa="EMASIVO 16 S.A.S.", movil="Z34-9001"),
            ev(date(2026, 3, 10), tipologia="OTRA"),
        ])
        e10 = m[("E10", "2026-03")]
        assert e10 == {"eventos": 5, "descartadas": 1, "inm": 4, "inm_padron": 1, "inm_buseton": 2, "inm_otra": 1}
        assert m[("E16", "2026-03")]["inm"] == 1

    def test_ignora_filas_sin_fecha_o_sin_unidad(self):
        m = r.agregar_inmovilizaciones([ev(None), ev("sin fecha"), ev(date(2026, 3, 1), empresa="X", movil="Q1")])
        assert m == {}

    def test_acepta_fechas_en_texto_iso(self):
        m = r.agregar_inmovilizaciones([ev("2026-03-05T10:00:00"), ev("2026-03-06")])
        assert m[("E10", "2026-03")]["inm"] == 2


class TestDpv:

    def test_dpv_es_km_entre_inmovilizaciones(self):
        assert r.calcular_dpv(920000, 47) == 920000 / 47

    def test_sin_km_o_sin_inmovilizaciones_no_hay_dpv(self):
        """✅ Falta el km → vacío (nunca 0): un mes sin cargar no es «0 km entre varadas»"""
        assert r.calcular_dpv(None, 10) is None
        assert r.calcular_dpv(0, 10) is None
        assert r.calcular_dpv(5000, 0) is None
        assert r.calcular_dpv(5000, None) is None

    def test_niveles_segun_estandar_y_critico(self):
        assert r.nivel_dpv(10000) == "cumple"
        assert r.nivel_dpv(9999.9) == "alerta"
        assert r.nivel_dpv(7000.1) == "alerta"
        assert r.nivel_dpv(7000) == "critico"
        assert r.nivel_dpv(3000) == "critico"
        assert r.nivel_dpv(None) is None


class TestSerieMensual:

    KM = [
        {"mes": "2026-01", "km_total": 1_000_000, "km_padron": 600_000, "km_buseton": 400_000, "fuente": "excel",
         "inm_excel": 47, "dpv_excel": 21276.6},
        {"mes": "2026-02", "km_total": 900_000, "km_padron": None, "km_buseton": None, "fuente": "manual"},
    ]

    def mapa(self):
        filas = ([ev(date(2026, 1, d)) for d in range(1, 21)]                                     # 20 padrón
                 + [ev(date(2026, 1, 25), tipologia="BUSETON") for _ in range(5)]                 # 5 buseton
                 + [ev(date(2026, 1, 26), estado="Contestado Contundente")]                        # no cuenta
                 + [ev(date(2026, 2, 3)) for _ in range(30)]
                 + [ev(date(2026, 3, 3)) for _ in range(12)])                                      # marzo: hay eventos pero no km
        return r.agregar_inmovilizaciones(filas)

    def test_dpv_total_y_por_tipologia(self):
        s = {x["mes"]: x for x in r.serie_mensual("E10", self.KM, self.mapa())}
        ene = s["2026-01"]
        assert (ene["inm"], ene["inm_padron"], ene["inm_buseton"]) == (25, 20, 5)
        assert ene["dpv"] == 40000.0 and ene["dpv_padron"] == 30000.0 and ene["dpv_buseton"] == 80000.0
        assert ene["nivel"] == "cumple" and ene["origen"] == "excel"
        assert (ene["eventos"], ene["descartadas"]) == (26, 1)
        assert ene["inm_excel"] == 47          # referencia del Excel, no se usa para calcular

    def test_sin_desglose_por_tipologia_no_hay_dpv_por_tipologia(self):
        feb = {x["mes"]: x for x in r.serie_mensual("E10", self.KM, self.mapa())}["2026-02"]
        assert feb["dpv"] == 30000.0 and feb["dpv_padron"] is None and feb["dpv_buseton"] is None
        assert feb["origen"] == "manual"

    def test_mes_con_eventos_y_sin_km_sale_vacio_no_cero(self):
        mar = {x["mes"]: x for x in r.serie_mensual("E10", self.KM, self.mapa())}["2026-03"]
        assert mar["dpv"] is None and mar["km"] is None and mar["origen"] == "sin_km" and mar["inm"] == 12

    def test_la_serie_va_en_orden_y_solo_trae_la_unidad_pedida(self):
        serie = r.serie_mensual("E10", self.KM, self.mapa())
        assert [x["mes"] for x in serie] == ["2026-01", "2026-02", "2026-03"]
        assert r.serie_mensual("E16", [], self.mapa()) == []

    def test_las_inmovilizaciones_siempre_salen_de_los_eventos(self):
        """✅ Si el Excel decía 47 pero los eventos dicen 25, manda lo calculado"""
        ene = r.serie_mensual("E10", self.KM, self.mapa())[0]
        assert ene["inm"] == 25 != ene["inm_excel"]

    def test_km_sin_eventos_en_la_bd_usa_las_inmovilizaciones_del_excel(self):
        serie = r.serie_mensual("E10", [{"mes": "2025-05", "km_total": 100000, "inm_excel": 10, "fuente": "excel"}], {})
        assert serie[0]["inm"] == 10 and serie[0]["dpv"] == 10000.0

    def test_meses_de_la_tabla_antigua_se_respetan_si_no_hay_km_nuevo(self):
        legado = [{"mes": "2024-12", "dpv": 15000, "kms": 900000, "varados": 60},
                  {"mes": "2025-01", "dpv": 0, "kms": 0, "varados": 0}]          # ceros: no es un dato real
        serie = r.serie_mensual("E10", [], {}, legado)
        assert [x["mes"] for x in serie] == ["2024-12"]
        assert serie[0]["dpv"] == 15000 and serie[0]["origen"] == "legacy"

    def test_el_km_nuevo_manda_sobre_la_tabla_antigua(self):
        legado = [{"mes": "2026-01", "dpv": 1, "kms": 1, "varados": 1}]
        ene = r.serie_mensual("E10", self.KM, self.mapa(), legado)[0]
        assert ene["origen"] == "excel" and ene["dpv"] == 40000.0

    def test_etiqueta_del_mes(self):
        assert r.etiqueta_mes("2026-03") == "Mar 26"
        assert r.etiqueta_mes("2025-12") == "Dic 25"


class TestLimpiezaDeEventos:

    def evento(self, **kw):
        base = {
            "estado": "No Contestado ", "empresa": "EMASIVO 10 S.A.S.", "placa": "AAA000", "movil": "Z32-9401",
            "tipologia": "BUSETON ", "fecha_inmovilizacion": datetime(2025, 1, 1), "hora": "22:04:00",
            "causa_inmovilizacion": "LIMPIAPARABRISAS", "descripcion_novedad": "Limpiaparabrisas  no  funciona",
            "ruta": "Ruta  A100 ", "operador": "320000", "dia_semana": "", "alerta": "", "franja_horaria": "P.\xa0M.",
        }
        base.update(kw)
        return base

    def test_normaliza_y_cuenta_solo_los_arreglos_reales(self):
        out, cambios = r.limpiar_evento(self.evento())
        assert out["estado"] == "No Contestado" and out["tipologia"] == "BUSETON"
        assert out["ruta"] == "Ruta A100"
        assert out["descripcion_novedad"] == "Limpiaparabrisas no funciona"
        assert set(cambios) == {"estado", "tipologia", "ruta", "descripcion_novedad"}

    def test_franja_siempre_am_pm_y_dia_se_deduce_de_la_fecha(self):
        out, cambios = r.limpiar_evento(self.evento())
        assert out["franja_horaria"] == "PM"
        assert out["dia_semana"] == "MIÉRCOLES"          # 2025-01-01 fue miércoles
        assert "franja_horaria" not in cambios and "dia_semana" not in cambios

    def test_sin_franja_se_deduce_de_la_hora(self):
        assert r.limpiar_evento(self.evento(franja_horaria="", hora="08:15:00"))[0]["franja_horaria"] == "AM"
        assert r.limpiar_evento(self.evento(franja_horaria=None, hora="12:00:00"))[0]["franja_horaria"] == "PM"

    def test_un_evento_ya_limpio_no_registra_cambios(self):
        out, _ = r.limpiar_evento(self.evento())
        out2, cambios = r.limpiar_evento(out)
        assert cambios == {} and out2 == out

    def test_descripcion_conserva_saltos_de_linea(self):
        out, _ = r.limpiar_evento(self.evento(descripcion_novedad="Linea 1  con   espacios\nLinea 2"))
        assert out["descripcion_novedad"] == "Linea 1 con espacios\nLinea 2"


class TestHoraFranjaDia:

    def test_hora_desde_time_datetime_texto_y_fraccion_de_excel(self):
        assert r.hora_de(time(22, 4)) == "22:04:00"
        assert r.hora_de(datetime(1900, 1, 1, 7, 5, 9)) == "07:05:09"        # celda HORA con fecha completa
        assert r.hora_de("8:30") == "08:30:00"
        assert r.hora_de("08:30:15") == "08:30:15"
        assert r.hora_de(0.5) == "12:00:00"
        assert r.hora_de("no es hora") == "" and r.hora_de(None) == ""

    def test_franja_entiende_las_variantes_del_excel(self):
        for v in ("A. M.", "A.\xa0M.", "am", "AM"):
            assert r.franja_de(v) == "AM", v
        for v in ("P. M.", "P.\xa0M.", "pm"):
            assert r.franja_de(v) == "PM", v
        assert r.franja_de("", "13:00:00") == "PM"
        assert r.franja_de("", "") == ""

    def test_dia_de_la_semana_en_espanol(self):
        assert r.dia_semana_de(date(2026, 10, 12)) == "LUNES"
        assert r.dia_semana_de("2026-10-17") == "SÁBADO"
        assert r.dia_semana_de(None) == ""


class TestAlerta:

    def test_quita_el_emoji_y_unifica_la_redaccion(self):
        """✅ '⚠️ Móvil inválido:operdor inexistente' (con la errata del Excel) → texto limpio"""
        assert r.normalizar_alerta("⚠️ Móvil inválido:operdor inexistente") == r.ALERTA_OPERADOR_INEXISTENTE
        assert r.normalizar_alerta("⚠️ Alerta:no coinciden") == r.ALERTA_NO_COINCIDEN
        assert r.normalizar_alerta("⚠️ Móvil inválido") == r.ALERTA_MOVIL_INVALIDO

    def test_en_sql_server_el_emoji_llega_como_signos_de_interrogacion(self):
        assert r.normalizar_alerta("?? Alerta:no coinciden") == r.ALERTA_NO_COINCIDEN

    def test_vacio_y_texto_desconocido(self):
        assert r.normalizar_alerta(None) == "" and r.normalizar_alerta("  ") == ""
        assert r.normalizar_alerta("⚠️ Revisar conductor") == "Revisar conductor"

    def test_operador_numerico_sin_decimales(self):
        assert r.texto_entero(320000.0) == "320000"
        assert r.texto_entero(320000) == "320000"
        assert r.texto_entero(" 32-1 ") == "32-1"
