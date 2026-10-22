// Pruebas de la lógica pura del tablero DPV (src/views/dpvUtils.js).
// No necesitan instalar nada: usan el ejecutor de pruebas de Node (18 o superior).
//
//     cd frontend
//     npm test            # = node --test tests/
//
// Todos los datos son inventados (móviles Z32-9xxx / Z34-9xxx, placas TSTxxx, operadores 9100xx). Nunca se prueba con datos reales.
import test from 'node:test'
import assert from 'node:assert/strict'
import * as U from '../src/views/dpvUtils.js'
import { CIRC } from '../src/views/icoUtils.js'

// Fila cruda tal como la entrega GET /api/dpv?slim=true
const cruda = (o = {}) => ({
  id: 1, dpv_id: 5001, estado: 'No Contestado', cuenta: true, empresa: 'EMASIVO 10', placa: 'TST001', movil: 'Z32-9001',
  tipologia: 'PADRON', fecha_inmovilizacion: '2030-01-05T00:00:00', hora: '07:05:00', causa_inmovilizacion: 'CAUSA UNO',
  descripcion_novedad: 'Prueba', ruta: 'Ruta T1', operador: '910001', dia_semana: 'SÁBADO', alerta: '',
  franja_horaria: 'AM', fecha_inicio: '2030-01-05', fecha_cierre: '2030-01-12', ...o,
})
// Fila ya normalizada, como la guarda el store
const ev = (o = {}) => U.normDPV(cruda(o))
const ids = rows => rows.map(r => r.dpv_id)

// Cuatro eventos: 2030-01 (UF10 ×2), 2030-02 (UF16, contestado con contundencia → no cuenta) y 2031-01 (UF16)
const BASE = [
  ev({ dpv_id: 5001, movil: 'Z32-9001', empresa: 'EMASIVO 10', fecha_inmovilizacion: '2030-01-05T00:00:00', franja_horaria: 'AM', hora: '07:05:00', tipologia: 'PADRON', estado: 'No Contestado' }),
  ev({ dpv_id: 5002, movil: 'Z32-9002', empresa: 'EMASIVO 10', fecha_inmovilizacion: '2030-01-20T00:00:00', franja_horaria: 'PM', hora: '15:00:00', tipologia: 'BUSETON', estado: 'Contestado No Contundente' }),
  ev({ dpv_id: 5003, movil: 'Z34-9003', empresa: 'EMASIVO 16', fecha_inmovilizacion: '2030-02-03T00:00:00', franja_horaria: 'AM', hora: '09:30:00', tipologia: 'PADRON', estado: 'Contestado Contundente', cuenta: false }),
  ev({ dpv_id: 5004, movil: 'Z34-9004', empresa: 'EMASIVO 16', fecha_inmovilizacion: '2031-01-15T00:00:00', franja_horaria: 'PM', hora: '20:00:00', tipologia: 'BUSETON', estado: 'Validado', placa: 'TST004', operador: '910004' }),
]
const F = (o = {}) => ({ ...U.filtrosVacios(), ...o })

// ── Regla de negocio ─────────────────────────────────────────────────────────

test('cuentaParaDpv: solo «Contestado Contundente» no cuenta (sin importar mayúsculas, tildes ni espacios)', () => {
  assert.equal(U.cuentaParaDpv('Contestado Contundente'), false)
  assert.equal(U.cuentaParaDpv('  contestado   CONTUNDENTE '), false)
  assert.equal(U.cuentaParaDpv('Contéstado Contundente'), false)
  for (const e of ['No Contestado', 'Contestado No Contundente', 'Validado', 'Aceptado', 'Contestado', '']) {
    assert.equal(U.cuentaParaDpv(e), true, e)
  }
})

test('nivelDpv: ≥ estándar cumple, ≤ crítico es crítico, en medio alerta, sin dato null', () => {
  assert.equal(U.nivelDpv(10000), 'cumple')
  assert.equal(U.nivelDpv(25000), 'cumple')
  assert.equal(U.nivelDpv(9999.9), 'alerta')
  assert.equal(U.nivelDpv(7000.1), 'alerta')
  assert.equal(U.nivelDpv(7000), 'critico')
  assert.equal(U.nivelDpv(0), 'critico')
  assert.equal(U.nivelDpv(null), null)
  assert.equal(U.nivelDpv(undefined), null)
  assert.equal(U.nivelDpv(NaN), null)
  assert.equal(U.nivelDpv(5000, { estandar: 6000, critico: 4000 }), 'alerta')   // umbrales que llegan del backend
})

// ── Normalización de filas ───────────────────────────────────────────────────

test('normFranja: A. M. / P. M. (con espacio duro) → AM / PM; si falta se deduce de la hora', () => {
  assert.equal(U.normFranja('A. M.'), 'AM')
  assert.equal(U.normFranja('P. M.'), 'PM')
  assert.equal(U.normFranja('pm'), 'PM')
  assert.equal(U.normFranja('', '07:05:00'), 'AM')
  assert.equal(U.normFranja(null, '12:00:00'), 'PM')
  assert.equal(U.normFranja('', ''), '')
})

test('horaDe: hora 0-23 o null', () => {
  assert.equal(U.horaDe({ hora: '07:05:00' }), 7)
  assert.equal(U.horaDe({ hora: '9:30' }), 9)
  assert.equal(U.horaDe({ hora: '00:00:00' }), 0)
  assert.equal(U.horaDe({ hora: '24:00:00' }), null)
  assert.equal(U.horaDe({ hora: '' }), null)
  assert.equal(U.horaDe({}), null)
})

test('normDPV: limpia espacios, deduce la unidad, normaliza tipología y arma fecha+hora', () => {
  const r = U.normDPV(cruda({
    empresa: ' EMASIVO 16 ', movil: ' Z34-9003 ', tipologia: 'Padrón', fecha_inmovilizacion: '2030-02-10T00:00:00',
    hora: '18:30:00.000000', franja_horaria: 'P. M.',
  }))
  assert.equal(r.uf, 'UF16')
  assert.equal(r.movil, 'Z34-9003')
  assert.equal(r.tipologia, 'PADRON')
  assert.equal(r.fecha, '2030-02-10')
  assert.equal(r.hora, '18:30:00')
  assert.equal(r.franja, 'PM')
  assert.equal(r.fh, '2030-02-10 18:30:00')
  assert.equal(r.fecha_cierre, '2030-01-12')
})

test('normDPV: la unidad sale del prefijo del móvil si la empresa no la dice', () => {
  assert.equal(U.normDPV(cruda({ empresa: '', movil: 'Z32-9001' })).uf, 'UF10')
  assert.equal(U.normDPV(cruda({ empresa: '', movil: 'Z34-9003' })).uf, 'UF16')
  assert.equal(U.normDPV(cruda({ empresa: '', movil: 'ABC' })).uf, '')
})

test('normDPV: «cuenta» manda el backend; si no llega, se aplica la regla local', () => {
  assert.equal(U.normDPV(cruda({ estado: 'Contestado Contundente', cuenta: true })).cuenta, true)    // el backend decide
  assert.equal(U.normDPV(cruda({ estado: 'No Contestado', cuenta: false })).cuenta, false)
  assert.equal(U.normDPV(cruda({ estado: 'Contestado Contundente', cuenta: undefined })).cuenta, false)
  assert.equal(U.normDPV(cruda({ estado: 'Validado', cuenta: undefined })).cuenta, true)
})

test('normDPV: entiende los nombres cortos de la versión anterior de la API', () => {
  const r = U.normDPV({ id: 9, fecha: '2030-03-01', causa: 'X', descripcion: 'd', franja: 'AM', hora: '05:00:00', movil: 'Z32-9001' })
  assert.equal(r.fecha, '2030-03-01')
  assert.equal(r.causa_inmovilizacion, 'X')
  assert.equal(r.descripcion, 'd')
  assert.equal(r.franja, 'AM')
})

test('unificarCausas: la causa recortada a 20 caracteres se une a su versión larga si es la única', () => {
  const filas = [
    ev({ causa_inmovilizacion: 'CAUSA LARGA PARA PRU' }),
    ev({ causa_inmovilizacion: 'CAUSA LARGA PARA PRUEBAS - DETALLE' }),
    ev({ causa_inmovilizacion: 'CAUSA UNO' }),
  ]
  U.unificarCausas(filas)
  assert.equal(filas[0].causa_inmovilizacion, 'CAUSA LARGA PARA PRUEBAS - DETALLE')
  assert.equal(filas[2].causa_inmovilizacion, 'CAUSA UNO')
})

test('unificarCausas: si hay dos versiones largas posibles no adivina', () => {
  const filas = [
    ev({ causa_inmovilizacion: 'CAUSA LARGA PARA PRU' }),
    ev({ causa_inmovilizacion: 'CAUSA LARGA PARA PRUEBAS - DETALLE' }),
    ev({ causa_inmovilizacion: 'CAUSA LARGA PARA PRUEBAS - OTRO' }),
  ]
  U.unificarCausas(filas)
  assert.equal(filas[0].causa_inmovilizacion, 'CAUSA LARGA PARA PRU')
})

test('filtrosVacios y SELECCION_VACIA devuelven objetos nuevos (no se comparten entre llamadas)', () => {
  assert.notEqual(U.filtrosVacios().uf, U.filtrosVacios().uf)
  assert.notEqual(U.SELECCION_VACIA().hora, U.SELECCION_VACIA().hora)
  assert.deepEqual(U.filtrosVacios().meses, [])
  assert.equal(U.filtrosVacios().estado, '')
})

// ── Slicers ──────────────────────────────────────────────────────────────────

test('slicers: sin filtros solo quedan los eventos que cuentan para el DPV', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F())), [5001, 5002, 5004])
})

test('slicer Estado: «todos» incluye lo que no cuenta; un estado concreto muestra solo ese', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ estado: U.ESTADO_TODOS }))), [5001, 5002, 5003, 5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ estado: 'Validado' }))), [5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ estado: 'Contestado Contundente' }))), [5003])
})

test('slicer Unidad', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ uf: ['UF10'] }))), [5001, 5002])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ uf: ['UF16'] }))), [5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ uf: ['UF10', 'UF16'] }))), [5001, 5002, 5004])
})

test('slicer Año / Mes: el mes solo aplica con año elegido', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '2030' }))), [5001, 5002])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '2031' }))), [5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '2030', meses: [1] }))), [5001, 5002])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '2030', meses: [2] }))), [])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '2030', meses: [2], estado: U.ESTADO_TODOS }))), [5003])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ anio: '', meses: [2] }))), [5001, 5002, 5004])    // sin año, el mes se ignora
})

test('slicers Franja y Tipología', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ franja: ['AM'] }))), [5001])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ franja: ['PM'] }))), [5002, 5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ tipologia: ['BUSETON'] }))), [5002, 5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ tipologia: ['PADRON'], franja: ['PM'] }))), [])
})

test('búsqueda: móvil, placa, operador o número de DPV (sin distinguir mayúsculas)', () => {
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ busqueda: 'z32-9002' }))), [5002])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ busqueda: ' TST004 ' }))), [5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ busqueda: '910004' }))), [5004])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ busqueda: '5003', estado: U.ESTADO_TODOS }))), [5003])
  assert.deepEqual(ids(U.aplicarSlicers(BASE, F({ busqueda: 'no-existe' }))), [])
})

test('opcionesSlicers: años de más reciente a más antiguo, meses por año y estados', () => {
  const o = U.opcionesSlicers(BASE)
  assert.deepEqual(o.anios, ['2031', '2030'])
  assert.deepEqual(o.mesesPorAnio, { 2030: [1, 2], 2031: [1] })
  assert.deepEqual(o.estados, ['Contestado Contundente', 'Contestado No Contundente', 'No Contestado', 'Validado'])
})

test('periodoPorDefecto: el último mes con datos (o null si no hay)', () => {
  assert.deepEqual(U.periodoPorDefecto(BASE), { anio: '2031', meses: [1] })
  assert.equal(U.periodoPorDefecto([]), null)
})

test('mesUnico y enPeriodo', () => {
  assert.equal(U.mesUnico({ anio: '2030', meses: [2] }), '2030-02')
  assert.equal(U.mesUnico({ anio: '2030', meses: [1, 2] }), '')
  assert.equal(U.mesUnico({ anio: '', meses: [1] }), '')
  assert.equal(U.enPeriodo('2030-02', { anio: '', meses: [] }), true)
  assert.equal(U.enPeriodo('2030-02', { anio: '2030', meses: [] }), true)
  assert.equal(U.enPeriodo('2030-02', { anio: '2030', meses: [1] }), false)
  assert.equal(U.enPeriodo('2030-02', { anio: '2031', meses: [] }), false)
})

// ── Selección cruzada ────────────────────────────────────────────────────────

test('selección: periodos por día o por mes, hora, tipología y móvil', () => {
  const rows = U.aplicarSlicers(BASE, F())
  const sel = (o) => ({ ...U.SELECCION_VACIA(), ...o })
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ periodos: ['2030-01-05'] }))), [5001])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ periodos: ['2030-01'] }))), [5001, 5002])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ periodos: ['2030-01-05', '2031-01'] }))), [5001, 5004])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ hora: ['15'] }))), [5002])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ tipologia: ['BUSETON'] }))), [5002, 5004])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ movil: ['Z34-9004'] }))), [5004])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel({ tipologia: ['BUSETON'], hora: ['15'] }))), [5002])     // dimensiones distintas: se combinan (Y)
  assert.equal(U.aplicarSeleccion(rows, U.SELECCION_VACIA()), rows)                                           // sin selección: mismas filas
})

test('selección: causa, ruta y operador; «excepto» deja a la visual propia ver todas sus categorías', () => {
  const rows = [
    ev({ dpv_id: 1, causa_inmovilizacion: 'CAUSA UNO', ruta: 'Ruta T1', operador: '910001' }),
    ev({ dpv_id: 2, causa_inmovilizacion: 'CAUSA DOS', ruta: 'Ruta T2', operador: '910002' }),
    ev({ dpv_id: 3, causa_inmovilizacion: 'CAUSA DOS', ruta: 'Ruta T1', operador: '910001' }),
  ]
  const sel = { ...U.SELECCION_VACIA(), causa: ['CAUSA DOS'], ruta: ['Ruta T1'] }
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel)), [3])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel, 'causa')), [1, 3])      // la causa no se aplica a sí misma
  assert.deepEqual(ids(U.aplicarSeleccion(rows, sel, 'ruta')), [2, 3])
  assert.deepEqual(ids(U.aplicarSeleccion(rows, { ...U.SELECCION_VACIA(), operador: ['910002'] })), [2])
})

test('DIM: valores vacíos caen en S/D y el móvil cae en la placa', () => {
  assert.equal(U.DIM.hora({ hora: '07:05:00' }), '07')
  assert.equal(U.DIM.hora({ hora: '' }), 'S/D')
  assert.equal(U.DIM.causa({ causa_inmovilizacion: '' }), 'S/D')
  assert.equal(U.DIM.ruta({ ruta: '' }), 'S/D')
  assert.equal(U.DIM.operador({ operador: '' }), 'S/D')
  assert.equal(U.DIM.movil({ movil: '', placa: 'TST001' }), 'TST001')
  assert.equal(U.DIM.movil({ movil: '', placa: '' }), 'S/D')
})

// ── Rankings, dona y contadores ──────────────────────────────────────────────

test('ranking: ordena de mayor a menor, calcula % y marca lo seleccionado', () => {
  const rows = [
    ev({ causa_inmovilizacion: 'CAUSA UNO' }), ev({ causa_inmovilizacion: 'CAUSA UNO' }), ev({ causa_inmovilizacion: 'CAUSA UNO' }),
    ev({ causa_inmovilizacion: 'CAUSA DOS' }), ev({ causa_inmovilizacion: '' }),
  ]
  const r = U.ranking(rows, U.DIM.causa, { seleccion: ['CAUSA DOS'] })
  assert.deepEqual(r.map(x => [x.key, x.total, x.pct, x.seleccionado]),
    [['CAUSA UNO', 3, 60, false], ['CAUSA DOS', 1, 20, true], ['S/D', 1, 20, false]])
  assert.deepEqual(U.ranking([], U.DIM.causa), [])
})

test('dona: siempre PADRÓN y BUSETON (aunque uno sea 0) y los arcos suman la circunferencia', () => {
  const d = U.dona([ev({ tipologia: 'PADRON' }), ev({ tipologia: 'PADRON' }), ev({ tipologia: 'BUSETON' })], ['BUSETON'])
  assert.deepEqual(d.map(s => [s.key, s.total, s.pct, s.seleccionado]), [['PADRON', 2, 67, false], ['BUSETON', 1, 33, true]])
  assert.ok(Math.abs(d.reduce((s, x) => s + x.dash, 0) - CIRC) < 1e-9)
  assert.equal(d[0].offset, 0)
  assert.ok(Math.abs(d[1].offset - d[0].dash) < 1e-9)
  assert.equal(d[0].label, 'PADRÓN')

  const solo = U.dona([ev({ tipologia: 'BUSETON' })])
  assert.deepEqual(solo.map(s => [s.key, s.total]), [['PADRON', 0], ['BUSETON', 1]])
  const vacia = U.dona([])
  assert.deepEqual(vacia.map(s => s.dash), [0, 0])
})

test('kpisEventos: móviles, causas, sin contestar y ventana abierta', () => {
  const hoy = '2030-01-10'
  const rows = [
    ev({ movil: 'Z32-9001', causa_inmovilizacion: 'CAUSA UNO', estado: 'No Contestado', fecha_cierre: '2030-01-12' }),   // ventana abierta (2 días)
    ev({ movil: 'Z32-9001', causa_inmovilizacion: 'CAUSA DOS', estado: 'No Contestado', fecha_cierre: '2030-01-09' }),   // ya venció
    ev({ movil: 'Z32-9002', causa_inmovilizacion: 'CAUSA UNO', estado: 'Validado', fecha_cierre: '2030-01-30' }),
  ]
  assert.deepEqual(U.kpisEventos(rows, hoy), { total: 3, moviles: 2, causas: 2, sinContestar: 2, ventanaAbierta: 1 })
  assert.deepEqual(U.kpisEventos([], hoy), { total: 0, moviles: 0, causas: 0, sinContestar: 0, ventanaAbierta: 0 })
})

// ── Mapas de calor ───────────────────────────────────────────────────────────

const enFecha = (fecha, n, o = {}) => Array.from({ length: n }, (_, i) => ev({ dpv_id: Number(fecha.replace(/\D/g, '')) * 100 + i, fecha_inmovilizacion: `${fecha}T00:00:00`, ...o }))

test('heatmap por día: una columna por día del mes, niveles 1-3 / 4-7 / 8+ y fin de semana', () => {
  const rows = [...enFecha('2030-01-05', 3), ...enFecha('2030-01-20', 4), ...enFecha('2030-01-21', 8)]
  const h = U.heatmap(rows, F({ anio: '2030', meses: [1] }), ['2030-01-20'])
  assert.equal(h.modo, 'dia')
  assert.equal(h.columnas.length, 31)
  const col = k => h.columnas.find(c => c.key === k)
  assert.deepEqual([col('2030-01-05').total, col('2030-01-05').nivel, col('2030-01-05').color], [3, 'bajo', U.HEAT_COLORES.bajo])
  assert.deepEqual([col('2030-01-20').total, col('2030-01-20').nivel, col('2030-01-20').seleccionado], [4, 'medio', true])
  assert.deepEqual([col('2030-01-21').total, col('2030-01-21').nivel], [8, 'alto'])
  assert.deepEqual([col('2030-01-06').total, col('2030-01-06').nivel], [0, 'vacio'])
  assert.deepEqual([col('2030-01-05').label, col('2030-01-05').sub, col('2030-01-05').finDeSemana], ['5', 'S', true])   // 5 ene 2030 = sábado
  assert.equal(col('2030-01-07').finDeSemana, false)
  assert.equal(h.max, 8)
  assert.deepEqual(h.ticks, [8, 4, 0])
})

test('heatmap por día: respeta los días de febrero (28 y bisiesto 29)', () => {
  assert.equal(U.heatmap([], F({ anio: '2030', meses: [2] })).columnas.length, 28)
  assert.equal(U.heatmap([], F({ anio: '2028', meses: [2] })).columnas.length, 29)
})

test('heatmap por mes: 12 meses del año o solo los elegidos; niveles relativos al máximo', () => {
  const rows = [...enFecha('2030-01-05', 10), ...enFecha('2030-04-05', 5), ...enFecha('2030-06-05', 2)]
  const h = U.heatmap(rows, F({ anio: '2030' }))
  assert.equal(h.modo, 'mes')
  assert.equal(h.columnas.length, 12)
  assert.deepEqual(h.columnas.filter(c => c.total).map(c => [c.label, c.total, c.nivel]),
    [['Ene', 10, 'alto'], ['Abr', 5, 'medio'], ['Jun', 2, 'bajo']])
  const dos = U.heatmap(rows, F({ anio: '2030', meses: [4, 1] }))
  assert.equal(dos.modo, 'mes')
  assert.deepEqual(dos.columnas.map(c => c.key), ['2030-01', '2030-04'])
})

test('heatmap de todo el histórico: meses seguidos, también los vacíos, con el año en enero', () => {
  const rows = [...enFecha('2030-11-05', 2), ...enFecha('2031-02-05', 1)]
  const h = U.heatmap(rows, F())
  assert.equal(h.modo, 'anio-mes')
  assert.deepEqual(h.columnas.map(c => c.key), ['2030-11', '2030-12', '2031-01', '2031-02'])
  assert.deepEqual(h.columnas.map(c => c.sub), ['', '', '2031', ''])
  assert.deepEqual(h.columnas.map(c => c.nivel), ['alto', 'vacio', 'vacio', 'medio'])
  assert.deepEqual(U.heatmap([], F()).columnas, [])
})

test('horasHeat: 24 horas, ignora eventos sin hora válida y marca la selección', () => {
  const rows = [
    ev({ hora: '07:05:00' }), ev({ hora: '07:50:00' }), ev({ hora: '15:00:00' }), ev({ hora: '' }), ev({ hora: '24:10:00' }),
  ]
  const h = U.horasHeat(rows, ['07'])
  assert.equal(h.modo, 'hora')
  assert.equal(h.columnas.length, 24)
  assert.deepEqual(h.columnas.map(c => c.key).slice(0, 3), ['00', '01', '02'])
  const c7 = h.columnas[7]
  assert.deepEqual([c7.total, c7.seleccionado, c7.nivel, c7.titulo], [2, true, 'alto', '07:00 a 07:59'])
  assert.equal(h.columnas[15].total, 1)
  assert.equal(h.columnas.reduce((s, c) => s + c.total, 0), 3)
  assert.equal(h.max, 2)
})

// ── DPV mensual ──────────────────────────────────────────────────────────────

test('camposSerie y mesAnterior', () => {
  assert.equal(U.camposSerie([]).dpv, 'dpv')
  assert.equal(U.camposSerie(['PADRON']).dpv, 'dpv_padron')
  assert.equal(U.camposSerie(['BUSETON']).km, 'km_buseton')
  assert.equal(U.camposSerie(['PADRON', 'BUSETON']).dpv, 'dpv')
  assert.equal(U.mesAnterior('2030-03'), '2030-02')
  assert.equal(U.mesAnterior('2030-01'), '2029-12')
})

// Serie de una unidad: ene cumple (10.000), feb alerta (9.000), mar crítico (6.000), abr sin km (5 inmovilizaciones)
const mes = (m, km, inm, extra = {}) => ({
  mes: m, mes_label: m, km, inm, dpv: km > 0 && inm > 0 ? Math.round((km / inm) * 10) / 10 : null,
  km_padron: null, km_buseton: null, inm_padron: null, inm_buseton: null, dpv_padron: null, dpv_buseton: null, ...extra,
})
const S10 = { uf: 'UF10', datos: [mes('2030-01', 100000, 10), mes('2030-02', 90000, 10), mes('2030-03', 60000, 10), mes('2030-04', null, 5)] }

test('kpiDpv de un mes: km ÷ inmovilizaciones, nivel y variación contra el mes anterior', () => {
  const k = U.kpiDpv([S10], F({ anio: '2030', meses: [2] }))
  assert.equal(k.dpv, 9000)
  assert.equal(k.nivel, 'alerta')
  assert.equal(k.km, 90000)
  assert.equal(k.inm, 10)
  assert.equal(k.delta, -1000)
  assert.deepEqual(k.sinKm, [])
  assert.equal(k.parcial, false)
  assert.equal(U.kpiDpv([S10], F({ anio: '2030', meses: [1] })).nivel, 'cumple')
  assert.equal(U.kpiDpv([S10], F({ anio: '2030', meses: [1] })).delta, null)       // enero: no hay mes anterior en la serie
  assert.equal(U.kpiDpv([S10], F({ anio: '2030', meses: [3] })).nivel, 'critico')
})

test('kpiDpv de varios meses: Σkm ÷ Σinmovilizaciones (no el promedio de los DPV) y avisa de los meses sin km', () => {
  const k = U.kpiDpv([S10], F({ anio: '2030' }))
  assert.equal(k.km, 250000)
  assert.equal(k.inm, 30)
  assert.ok(Math.abs(k.dpv - 250000 / 30) < 1e-9)
  assert.equal(k.nivel, 'alerta')
  assert.deepEqual(k.sinKm, [{ uf: 'UF10', mes: '2030-04', eventos: 5, motivo: 'km' }])
  assert.equal(k.parcial, true)
  assert.equal(k.meses, 3)
  assert.equal(k.delta, null)
})

test('kpiDpv de un mes sin km: sin DPV (no 0) y lo reporta', () => {
  const k = U.kpiDpv([S10], F({ anio: '2030', meses: [4] }))
  assert.equal(k.dpv, null)
  assert.equal(k.nivel, null)
  assert.equal(k.km, null)
  assert.equal(k.meses, 0)
  assert.equal(k.sinKm.length, 1)
  assert.equal(k.parcial, false)
})

test('kpiDpv con las dos unidades suma flota; con una sola da variación', () => {
  const S16 = { uf: 'UF16', datos: [mes('2030-01', 50000, 10)] }
  const k = U.kpiDpv([S10, S16], F({ anio: '2030', meses: [1] }))
  assert.equal(k.km, 150000)
  assert.equal(k.inm, 20)
  assert.equal(k.dpv, 7500)
  assert.equal(k.delta, null)
})

test('kpiDpv por tipología usa los km y las inmovilizaciones de esa tipología', () => {
  const datos = [
    mes('2030-01', 100000, 10, { km_padron: 60000, inm_padron: 5, dpv_padron: 12000, km_buseton: 40000, inm_buseton: 5, dpv_buseton: 8000 }),
    mes('2030-02', 100000, 10, { km_padron: null, inm_padron: 4 }),                              // faltan los km de Padrón
    mes('2030-03', 100000, 10, { km_padron: 50000, inm_padron: null }),                         // hay km pero no hay eventos de esa tipología
  ]
  const p = U.kpiDpv([{ uf: 'UF10', datos }], F({ anio: '2030', tipologia: ['PADRON'] }))
  assert.equal(p.dpv, 12000)
  assert.equal(p.nivel, 'cumple')
  assert.deepEqual(p.sinKm.map(s => [s.mes, s.motivo]), [['2030-02', 'km'], ['2030-03', 'eventos']])
  assert.equal(U.kpiDpv([{ uf: 'UF10', datos }], F({ anio: '2030', meses: [1], tipologia: ['BUSETON'] })).dpv, 8000)
  assert.equal(U.kpiDpv([{ uf: 'UF10', datos }], F({ anio: '2030', meses: [1], tipologia: ['BUSETON'] })).nivel, 'alerta')
})

test('kpiDpv: mes de la carga antigua (solo DPV, sin km) vale solo si es el único del periodo', () => {
  const heredado = mes('2030-05', null, null, { dpv: 12000, origen: 'legacy' })
  const solo = U.kpiDpv([{ uf: 'UF10', datos: [heredado] }], F({ anio: '2030', meses: [5] }))
  assert.equal(solo.dpv, 12000)
  assert.equal(solo.km, null)
  assert.equal(solo.nivel, 'cumple')
  const junto = U.kpiDpv([{ uf: 'UF10', datos: [mes('2030-01', 100000, 10), heredado] }], F({ anio: '2030' }))
  assert.equal(junto.dpv, 10000)                       // el mes heredado no se mezcla con km reales
  assert.deepEqual(junto.sinKm, [])
})

test('kpiDpv: hay km pero ninguna varada → no se puede calcular, y lo dice', () => {
  const k = U.kpiDpv([{ uf: 'UF10', datos: [mes('2030-06', 50000, 0)] }], F({ anio: '2030', meses: [6] }))
  assert.equal(k.dpv, null)
  assert.equal(k.sinInmovilizaciones, true)
  assert.equal(k.km, 50000)
  assert.equal(U.kpiDpv([S10], F({ anio: '2030', meses: [1] })).sinInmovilizaciones, false)
})

// ── Geometría del gráfico ────────────────────────────────────────────────────

test('pasoLindo y escalaY: marcas redondas que abarcan datos y líneas de referencia', () => {
  assert.equal(U.pasoLindo(100), 100)
  assert.equal(U.pasoLindo(140), 100)
  assert.equal(U.pasoLindo(150), 200)
  assert.equal(U.pasoLindo(500), 500)
  assert.equal(U.pasoLindo(800), 1000)
  assert.equal(U.pasoLindo(2585), 2000)
  const e = U.escalaY([17343.3, 9000])
  assert.equal(e.paso, 2000)
  assert.ok(e.minV <= 7000 && e.maxV >= 17343.3)
  assert.equal(e.minV % e.paso, 0)
  const vacia = U.escalaY([])                                    // sin datos: igual cubre estándar y crítico
  assert.ok(vacia.minV < 7000 && vacia.maxV > 10000)
  assert.ok(U.escalaY([null, undefined, NaN]).maxV > 10000)
})

test('geometriaSerie: un punto por mes, mayor DPV = más arriba, la línea se parte donde falta el km', () => {
  const datos = [mes('2030-01', 100000, 10), mes('2030-02', 90000, 10), mes('2030-03', null, 4), mes('2030-04', 60000, 10)]
  const g = U.geometriaSerie(datos, { alto: 190 })
  assert.equal(g.n, 4)
  assert.deepEqual(g.puntos.map(p => p.fx), [0.125, 0.375, 0.625, 0.875])
  assert.deepEqual(g.puntos.map(p => p.nivel), ['cumple', 'alerta', null, 'critico'])
  assert.equal(g.puntos[2].y, null)
  assert.ok(g.puntos[0].y < g.puntos[1].y && g.puntos[1].y < g.puntos[3].y)           // 10.000 > 9.000 > 6.000
  assert.ok(g.puntos.filter(p => p.y !== null).every(p => p.y >= 0 && p.y <= 190))
  assert.equal(g.lineas.length, 1)                                                   // ene-feb unidos; abr queda aislado (solo marcador)
  assert.ok(g.lineas[0].startsWith('M125,') && g.lineas[0].includes('L375,'))
  assert.equal(g.lineas[0].split('L').length, 2)                                      // un solo tramo (M…L…): el hueco de marzo parte la línea
  assert.ok(!g.lineas[0].includes('875'))
  assert.equal(g.areas.length, 1)
  assert.ok(g.yEstandar < g.yCritico)                                                // 10.000 se dibuja más arriba que 7.000
  assert.ok(g.ticks.length >= 3 && g.ticks.every((t, i, a) => !i || t.valor > a[i - 1].valor))
  assert.ok(g.ticks.every(t => t.y >= 0 && t.y <= 190))
  assert.equal(g.ticks.find(t => t.valor === 10000).label, '10.000')
})

test('geometriaSerie: sin datos o sin ningún valor no revienta', () => {
  assert.equal(U.geometriaSerie([]).n, 0)
  const g = U.geometriaSerie([mes('2030-04', null, 5)])
  assert.deepEqual(g.lineas, [])
  assert.equal(g.puntos[0].y, null)
})

test('indicesEtiquetados: todos si caben; si no, primero, último, mínimo y máximo', () => {
  const pts = n => Array.from({ length: n }, (_, i) => ({ i, valor: 8000 + ((i * 37) % 11) * 100 }))
  assert.equal(U.indicesEtiquetados(pts(5)).size, 5)
  const muchos = U.indicesEtiquetados(pts(20))
  assert.ok(muchos.has(0) && muchos.has(19))
  assert.ok(muchos.size <= 4 && muchos.size >= 3)
  const plano = U.indicesEtiquetados(Array.from({ length: 20 }, (_, i) => ({ i, valor: 9000 })))
  assert.deepEqual([...plano].sort((a, b) => a - b), [0, 19])
  const conHueco = [{ i: 0, valor: 9000 }, { i: 1, valor: null }, { i: 2, valor: 8000 }]
  assert.deepEqual([...U.indicesEtiquetados(conHueco)], [0, 2])
})

test('constantes del gráfico: el SVG de la vista usa viewBox="0 0 1000 190" y 38 px mínimos por mes', () => {
  assert.equal(U.VISTA_X, 1000)
  assert.equal(U.ALTO_GRAFICA, 190)
  assert.equal(U.ANCHO_MES_PX, 38)
  assert.equal(U.geometriaSerie([]).alto, 190)
})

test('etiquetaMesCorta y tituloMes', () => {
  assert.equal(U.etiquetaMesCorta('2030-03'), 'Mar 30')
  assert.equal(U.etiquetaMesCorta('2026-10'), 'Oct 26')
  assert.equal(U.tituloMes('2030-03'), 'Marzo 2030')
})

test('NIVEL: cada nivel lleva texto e icono propios (no depende solo del color)', () => {
  for (const k of ['cumple', 'alerta', 'critico']) {
    assert.ok(U.NIVEL[k].texto && U.NIVEL[k].corto && U.NIVEL[k].icono && U.NIVEL[k].color)
  }
  assert.equal(new Set(Object.values(U.NIVEL).map(n => n.icono)).size, 3)
})

// ── Textos y exportación ─────────────────────────────────────────────────────

test('fmtKm y chipsSeleccion', () => {
  assert.equal(U.fmtKm(17343.3), '17.343')
  assert.equal(U.fmtKm(null), '—')
  const chips = U.chipsSeleccion({ ...U.SELECCION_VACIA(), periodos: ['2030-01-05', '2030-02'], hora: ['07'], tipologia: ['PADRON'], causa: ['CAUSA UNO'] })
  assert.deepEqual(chips.map(c => c.texto), ['Periodo: 5 ene', 'Periodo: Feb 2030', 'Hora: 07:00', 'Tipología: PADRÓN', 'Causa: CAUSA UNO'])
  assert.deepEqual(U.chipsSeleccion(U.SELECCION_VACIA()), [])
})

test('claseEstado: lo que no cuenta, en verde; lo pendiente, en ámbar; el resto, informativo', () => {
  assert.equal(U.claseEstado('Contestado Contundente'), 'badge-success')
  assert.equal(U.claseEstado('No Contestado'), 'badge-warning')
  assert.equal(U.claseEstado('Contestado No Contundente'), 'badge-info')
  assert.equal(U.claseEstado('Validado'), 'badge-info')
})

test('celdaCSV: escapa comillas/comas y neutraliza fórmulas (= + - @)', () => {
  assert.equal(U.celdaCSV(null), '')
  assert.equal(U.celdaCSV('hola'), 'hola')
  assert.equal(U.celdaCSV('a,b'), '"a,b"')
  assert.equal(U.celdaCSV('di "hola"'), '"di ""hola"""')
  assert.equal(U.celdaCSV('línea 1\nlínea 2'), '"línea 1\nlínea 2"')
  assert.equal(U.celdaCSV('=1+1'), "'=1+1")
  assert.equal(U.celdaCSV('+57 300'), "'+57 300")
  assert.equal(U.celdaCSV('@usuario'), "'@usuario")
  assert.equal(U.celdaCSV('-abc'), "'-abc")
  assert.equal(U.celdaCSV('-5'), '-5')                         // un número negativo no es una fórmula
  assert.equal(U.celdaCSV(42), '42')
})

test('csvDPV: encabezado + una línea por evento, con «Sí / No» según cuente para el DPV', () => {
  const rows = [
    ev({ dpv_id: 5001, descripcion_novedad: 'con "comillas", coma y\nsalto', estado: 'No Contestado' }),
    ev({ dpv_id: 5002, estado: 'Contestado Contundente', cuenta: false, descripcion_novedad: '=HYPERLINK("x")' }),
  ]
  const csv = U.csvDPV(rows)
  const lineas = csv.split('\r\n')
  const cab = lineas[0].split(',')
  assert.equal(cab[0], 'DPV')
  assert.equal(cab.length, 18)
  assert.ok(csv.includes('5001,No Contestado,Sí,Z32-9001'))
  assert.ok(csv.includes('5002,Contestado Contundente,No,Z32-9001'))
  assert.ok(csv.includes('"con ""comillas"", coma y\nsalto"'))
  assert.ok(csv.includes(`"'=HYPERLINK(""x"")"`))              // la fórmula quedó inofensiva y entrecomillada
  assert.equal(U.csvDPV([]).split('\r\n').length, 1)
})

// ── Mensajes del DPV mensual (tooltip y avisos de las tarjetas) ──────────────

// Punto del gráfico tal como lo arma geometriaSerie() para un mes de la serie
const punto = (m, campo = U.camposSerie([])) => U.geometriaSerie([m], { campo: campo.dpv }).puntos[0]

test('ORIGEN_KM: un texto por cada origen que manda el backend', () => {
  assert.deepEqual(Object.keys(U.ORIGEN_KM).sort(), ['excel', 'legacy', 'manual', 'sin_km'])
  assert.ok(Object.values(U.ORIGEN_KM).every(t => typeof t === 'string' && t.length > 10))
})

test('detalleMes: valor, cálculo, descartados, origen y nivel', () => {
  const g = U.camposSerie([])
  const d = U.detalleMes(punto(mes('2030-01', 100000, 10, { descartadas: 1, origen: 'excel' })), g)
  assert.equal(d.titulo, 'Enero 2030')
  assert.equal(d.valor, '10.000')
  assert.equal(d.unidad, 'km entre varadas')
  assert.deepEqual(d.lineas, ['100.000 km ÷ 10 inmovilizaciones', '1 contestado con contundencia no cuenta', 'Km cargados desde el Excel'])
  assert.equal(d.nivel, 'Cumple el estándar')
  assert.equal(d.icono, '●')
  assert.equal(d.nivelColor, U.NIVEL.cumple.color)
  // singular / plural y los demás niveles
  const u = U.detalleMes(punto(mes('2030-02', 9000, 1, { descartadas: 8, origen: 'manual' })), g)
  assert.deepEqual(u.lineas, ['9.000 km ÷ 1 inmovilización', '8 contestados con contundencia no cuentan', 'Km ingresados a mano'])
  assert.equal(u.nivel, 'En alerta')
  assert.equal(u.icono, '◆')
  const c = U.detalleMes(punto(mes('2030-03', 6000, 1, { origen: 'excel' })), g)
  assert.equal(c.nivel, 'Crítico')
  assert.equal(c.icono, '▲')
  assert.ok(!c.lineas.some(l => l.includes('contundencia')))                     // sin descartados no hay línea de descartados
})

test('detalleMes: un mes sin km no inventa un DPV y cuenta las inmovilizaciones registradas', () => {
  const g = U.camposSerie([])
  const d = U.detalleMes(punto(mes('2030-04', null, 5, { origen: 'sin_km' })), g)
  assert.equal(d.valor, 'Sin km')
  assert.equal(d.unidad, 'cargados')
  assert.deepEqual(d.lineas, ['5 inmovilizaciones registradas', 'Sin km cargados'])
  assert.equal(d.nivel, '')
  assert.equal(d.icono, '')
  assert.equal(U.detalleMes(punto(mes('2030-04', null, 1)), g).lineas[0], '1 inmovilización registrada')
  assert.equal(U.detalleMes(punto(mes('2030-04', null, null)), g).lineas[0], '0 inmovilizaciones registradas')
})

test('detalleMes: un mes de la carga antigua muestra su DPV y su origen, sin cálculo', () => {
  const d = U.detalleMes(punto(mes('2030-05', null, null, { dpv: 9000, origen: 'legacy' })), U.camposSerie([]))
  assert.equal(d.valor, '9.000')
  assert.deepEqual(d.lineas, ['Carga anterior (solo guardó el DPV)'])
  assert.equal(d.nivel, 'En alerta')
})

test('detalleMes: con una tipología no se listan los descartados (solo se conocen por mes completo)', () => {
  const campo = U.camposSerie(['BUSETON'])
  const m = mes('2030-01', 100000, 10, { descartadas: 3, km_buseton: 40000, inm_buseton: 4, dpv_buseton: 10000, origen: 'excel' })
  const d = U.detalleMes(punto(m, campo), campo)
  assert.equal(d.valor, '10.000')
  assert.deepEqual(d.lineas, ['40.000 km ÷ 4 inmovilizaciones', 'Km cargados desde el Excel'])
})

test('listaMeses: uno, dos, tres o más meses', () => {
  assert.equal(U.listaMeses([]), '')
  assert.equal(U.listaMeses(['2026-10']), 'Oct 26')
  assert.equal(U.listaMeses(['2026-09', '2026-10']), 'Sep 26 y Oct 26')
  assert.equal(U.listaMeses(['2026-06', '2026-07', '2026-08']), 'Jun 26, Jul 26 y Ago 26')
  assert.equal(U.listaMeses(['2026-06', '2026-07', '2026-08', '2026-09', '2026-10']), 'Jun 26, Jul 26, Ago 26 y 2 más')
  assert.equal(U.listaMeses(['2026-06', '2026-07', '2026-08', '2026-09'], 2), 'Jun 26, Jul 26 y 2 más')
})

test('avisoDpv: sin km, sin inmovilizaciones, parcial o nada que avisar', () => {
  const f = (o = {}) => F({ anio: '2030', ...o })
  assert.deepEqual(U.avisoDpv(U.kpiDpv([S10], f({ meses: [4] }))),
    { tipo: 'sin-km', enlace: true, texto: 'Sin km cargados para Abr 30: 5 inmovilizaciones registradas. Carga los km para calcular el DPV.' })
  assert.deepEqual(U.avisoDpv(U.kpiDpv([S10], f())),
    { tipo: 'parcial', enlace: true, texto: 'Calculado con 3 de 4 meses: faltan los km de Abr 30.' })
  assert.deepEqual(U.avisoDpv(U.kpiDpv([{ uf: 'UF10', datos: [mes('2030-06', 50000, 0)] }], f({ meses: [6] }))),
    { tipo: 'sin-inm', enlace: false, texto: 'Hay km pero ninguna inmovilización en el periodo: el DPV no se puede calcular.' })
  assert.equal(U.avisoDpv(U.kpiDpv([S10], f({ meses: [2] }))), null)                       // mes con km: nada que avisar
  assert.equal(U.avisoDpv(U.kpiDpv([{ uf: 'UF10', datos: [] }], f({ meses: [2] }))), null)  // serie vacía: la tarjeta ya lo dice
  assert.ok(U.avisoDpv(U.kpiDpv([{ uf: 'UF10', datos: [mes('2030-04', null, 1)] }], f({ meses: [4] }))).texto.includes('1 inmovilización registrada.'))
  // varios meses sin km: lista corta con «y N más»
  const sinKm = ['01', '02', '03', '04', '05'].map(m => mes(`2030-${m}`, null, 2))
  assert.ok(U.avisoDpv(U.kpiDpv([{ uf: 'UF10', datos: sinKm }], f())).texto.startsWith('Sin km cargados para Ene 30, Feb 30, Mar 30 y 2 más: 10 inmovilizaciones registradas.'))
})

test('altoTooltipMes: crece con las líneas y con el nivel, y coincide con lo medido en el navegador (≈ 107 px)', () => {
  const tres = U.altoTooltipMes({ lineas: ['a', 'b', 'c'], nivel: 'Cumple' })
  assert.ok(tres > U.altoTooltipMes({ lineas: ['a', 'b'], nivel: 'Cumple' }))
  assert.ok(U.altoTooltipMes({ lineas: ['a'], nivel: 'Cumple' }) > U.altoTooltipMes({ lineas: ['a'], nivel: '' }))
  assert.ok(tres >= 100 && tres <= 120)
})

test('tooltipAbajo: encima por defecto; debajo solo si encima no cabe y debajo sí', () => {
  const alto = 107
  assert.equal(U.tooltipAbajo(150, alto), false)     // punto bajo: encima cabe
  assert.equal(U.tooltipAbajo(115, alto), false)     // justo cabe encima (115 − 8 − 107 = 0)
  assert.equal(U.tooltipAbajo(114, alto), false)     // media altura: no cabe en ninguno → encima (sobre la leyenda, sin salirse de la tarjeta)
  assert.equal(U.tooltipAbajo(89, alto), false)
  assert.equal(U.tooltipAbajo(78, alto), false)
  assert.equal(U.tooltipAbajo(77, alto), true)       // justo cabe debajo (77 + 14 + 107 = 198 = alto del gráfico + 8)
  assert.equal(U.tooltipAbajo(53, alto), true)       // punto muy alto: debajo
  assert.equal(U.tooltipAbajo(100, 80), false)       // un tooltip de 2 líneas cabe encima desde más abajo
  assert.equal(U.tooltipAbajo(50, 80), true)
  // invariante: si va debajo, cabe debajo y no cabe encima; nunca debajo si se saldría por el borde inferior
  for (let y = 0; y <= 190; y += 1) {
    for (const a of [70, 80, 107, 121, 140]) {
      if (U.tooltipAbajo(y, a)) {
        assert.ok(y + 14 + a <= 190 + 8, `y=${y} alto=${a}: se saldría por abajo`)
        assert.ok(y - 8 - a < 0, `y=${y} alto=${a}: cabía encima`)
      }
    }
  }
})

test('desplazamientoParaVer: si el tramo ya se ve completo no mueve nada (un clic en un mes visible no hace saltar el gráfico)', () => {
  assert.equal(U.desplazamientoParaVer(100, 200, 50, 300), null)
  assert.equal(U.desplazamientoParaVer(50, 350, 50, 300), null)        // justo en los bordes
  assert.equal(U.desplazamientoParaVer(0, 38, 0, 300), null)
})

test('desplazamientoParaVer: un tramo fuera de la vista se centra (sin pasarse del inicio)', () => {
  assert.equal(U.desplazamientoParaVer(700, 738, 0, 300), 569)         // a la derecha: 700 + 19 − 150
  assert.equal(U.desplazamientoParaVer(0, 38, 500, 300), 0)            // a la izquierda del todo: no hay desplazamiento negativo
  assert.equal(U.desplazamientoParaVer(190, 228, 500, 300), 59)        // 190 + 19 − 150
  assert.equal(U.desplazamientoParaVer(290, 328, 0, 300), 159)         // medio cortado en el borde derecho: se centra
  assert.equal(U.desplazamientoParaVer(-3, 35, 20, 300), 0)
})

test('desplazamientoParaVer: un tramo más ancho que la pantalla (un año en celular) se alinea por su inicio si no se ve nada de él', () => {
  assert.equal(U.desplazamientoParaVer(100, 556, 600, 300), 92)        // 456 px en 300 visibles, todo fuera de la vista: inicio − 8 de respiro
  assert.equal(U.desplazamientoParaVer(4, 460, 600, 300), 0)           // no pasa de 0
  assert.equal(U.desplazamientoParaVer(500, 792, 0, 300), 492)         // 292 + 16 > 300: tampoco cabe con respiro → por el inicio
  assert.equal(U.desplazamientoParaVer(100, 380, 0, 300), 100 + 140 - 150)   // 280 + 16 ≤ 300: cabe (aunque se vea casi todo) → centrado
})

test('desplazamientoParaVer: si el tramo no cabe pero ya se ve al menos un mes, no se mueve (sumar meses con Ctrl+clic no aleja el mes pulsado)', () => {
  assert.equal(U.desplazamientoParaVer(100, 556, 300, 300), null)      // se ve de 300 a 556
  assert.equal(U.desplazamientoParaVer(100, 392, 0, 300), null)        // se ve de 100 a 300
  assert.equal(U.desplazamientoParaVer(-200, 120, 0, 300), null)
  assert.equal(U.desplazamientoParaVer(100, 556, 518, 300), null)      // se ve justo un mes entero (38 px)
  assert.equal(U.desplazamientoParaVer(100, 556, 520, 300), 92)        // se ve apenas un pedazo (36 px): no cuenta, se alinea por el inicio
  assert.equal(U.desplazamientoParaVer(300, 756, 0, 300), 292)         // roza el borde derecho pero no entra nada: por el inicio
  assert.equal(U.desplazamientoParaVer(100, 556, 300, 300, { minimo: 400 }), 92)
})

test('desplazamientoParaVer: datos inválidos no mueven nada', () => {
  assert.equal(U.desplazamientoParaVer(100, 100, 0, 300), null)
  assert.equal(U.desplazamientoParaVer(200, 100, 0, 300), null)
  assert.equal(U.desplazamientoParaVer(100, 200, 0, 0), null)
  assert.equal(U.desplazamientoParaVer(100, 200, 0, NaN), null)
})

test('desplazamientoParaVer: invariante — tras aplicarlo se ve el tramo (si cabe) o su inicio (si no cabe); null solo si ya se ve completo o, no cabiendo, ya se ve al menos un mes', () => {
  for (const visible of [300, 657, 1162]) {
    for (let izq = 0; izq <= 1600; izq += 37) {
      for (const ancho of [38, 76, 228, 456, 836, 1500]) {
        for (const sl of [0, 120, 536, 900]) {
          const der = izq + ancho
          const cabe = ancho + 16 <= visible
          const x = U.desplazamientoParaVer(izq, der, sl, visible)
          if (x === null) {
            const completo = izq >= sl && der <= sl + visible
            const solape = Math.min(der, sl + visible) - Math.max(izq, sl)
            assert.ok(completo || (!cabe && solape >= 38), `null sin motivo: ${izq}-${der} sl=${sl} vis=${visible}`)
            continue
          }
          assert.ok(x >= 0)
          if (cabe) assert.ok(izq >= x && der <= x + visible, `no queda a la vista: ${izq}-${der} → x=${x} vis=${visible}`)
          else assert.ok(izq >= x && izq < x + visible, `el inicio no queda a la vista: ${izq} → x=${x}`)
        }
      }
    }
  }
})

// ── Pantalla «Carga Masiva DPV» ──────────────────────────────────────────────

test('numeroDeTexto: entiende km escritos a la colombiana, a la americana y sin separadores', () => {
  const casos = [
    ['1234567', 1234567], ['1.234.567', 1234567], ['1.234.567,5', 1234567.5], ['1,234,567', 1234567], ['1,234,567.5', 1234567.5],
    ['1 234 567', 1234567], ['1 234 567', 1234567], ['654321', 654321], ['12,5', 12.5], ['12.5', 12.5], ['0,5', 0.5],
    ['7.000', 7000], ['  10000 ', 10000], ['0', 0], [1234.5, 1234.5],
  ]
  for (const [entrada, esperado] of casos) assert.equal(U.numeroDeTexto(entrada), esperado, `«${entrada}»`)
})

test('numeroDeTexto: lo que no es un número (o es negativo) devuelve null', () => {
  for (const x of ['', '   ', 'abc', '12abc', '-5', '1..2', '1.2.3', '1,2,3', '1e5', '--', null, undefined, NaN, Infinity, '1.063.39'])
    assert.equal(U.numeroDeTexto(x), null, `«${x}»`)
})

const kmOk = { empresa: 'E10', mes: '2026-10', total: '1.000.000', padron: '600.000', buseton: '400.000' }

test('validarKmManual: datos correctos → objeto listo para PUT /api/dpv-km (empresa en mayúsculas, números reales)', () => {
  assert.deepEqual(U.validarKmManual(kmOk), { datos: { empresa: 'E10', mes: '2026-10', km_total: 1000000, km_padron: 600000, km_buseton: 400000 } })
  assert.deepEqual(U.validarKmManual({ ...kmOk, empresa: ' e16 ' }).datos.empresa, 'E16')
  // padrón y buseton son opcionales (juntos, solo uno o ninguno)
  assert.deepEqual(U.validarKmManual({ ...kmOk, padron: '', buseton: '' }).datos, { empresa: 'E10', mes: '2026-10', km_total: 1000000, km_padron: null, km_buseton: null })
  assert.equal(U.validarKmManual({ ...kmOk, buseton: '' }).datos.km_padron, 600000)
  assert.equal(U.validarKmManual({ ...kmOk, padron: null, buseton: undefined }).datos.km_buseton, null)
})

test('validarKmManual: cada error tiene su mensaje y se revisan en el orden del formulario', () => {
  const err = (cambio) => U.validarKmManual({ ...kmOk, ...cambio }).error
  assert.match(err({ empresa: '' }), /unidad/)
  assert.match(err({ empresa: 'E99' }), /unidad/)
  assert.match(err({ mes: '' }), /mes/)
  assert.match(err({ mes: '2026-13' }), /mes/)
  assert.match(err({ mes: '2026-00' }), /mes/)
  assert.match(err({ mes: '26-10' }), /mes/)
  assert.match(err({ total: '' }), /km totales/)
  assert.match(err({ total: '0' }), /mayor que 0/)
  assert.match(err({ total: '-4' }), /mayor que 0/)
  assert.match(err({ total: 'mil' }), /mayor que 0/)
  assert.match(err({ padron: 'x' }), /Padrón no son un número/)
  assert.match(err({ buseton: '-1' }), /Buseton no son un número/)
  assert.equal(U.validarKmManual({ empresa: '', mes: '', total: '' }).error.includes('unidad'), true)
})

test('validarKmManual: Padrón + Buseton debe cuadrar con el total (1 % o 1 km), como el backend', () => {
  const d = (padron, buseton, total = '1.000.000') => U.validarKmManual({ ...kmOk, total, padron, buseton })
  assert.ok(d('600.000', '400.000').datos)
  assert.ok(d('600.000', '409.999').datos)                       // dentro del 1 %
  assert.ok(d('600.000', '410.000').datos)                       // justo el 1 % (diferencia 10.000 = 1 % de 1.000.000)
  assert.match(d('600.000', '410.001').error, /no coincide con el total/)
  assert.match(d('600.000', '300.000').error, /Padrón \+ Buseton \(900\.000\) no coincide con el total \(1\.000\.000\)/)
  assert.ok(d('50', '50.5', '100').datos)                        // totales chicos: tolerancia mínima de 1 km
  assert.match(d('50', '52', '100').error, /no coincide/)
})

const mensualDemo = {
  e10: [
    { mes: '2026-09', km: null, km_padron: null, km_buseton: null, inm: 12, dpv: null, nivel: null, origen: 'sin_km' },
    { mes: '2025-03', km: 1000000, km_padron: 600000, km_buseton: 400000, inm: 50, dpv: 20000, nivel: 'cumple', origen: 'excel' },
    { mes: '2025-04', km: 900000, km_padron: null, km_buseton: null, inm: 50, dpv: 18000, nivel: 'cumple', origen: 'manual' },
    { mes: '2025-05', km: 800000, km_padron: null, km_buseton: null, inm: 40, dpv: 20000, nivel: 'cumple', origen: 'legacy' },
  ],
  e16: [
    { mes: '2025-03', km: 900000, km_padron: 500000, km_buseton: 400000, inm: 45, dpv: 20000, nivel: 'cumple', origen: 'excel' },
    { mes: '2026-09', km: 0, km_padron: null, km_buseton: null, inm: 3, dpv: null, nivel: null, origen: 'sin_km' },
  ],
}

test('filasKm: una fila por unidad y mes, del mes más reciente al más antiguo y EMASIVO 10 antes que EMASIVO 16', () => {
  const f = U.filasKm(mensualDemo)
  assert.deepEqual(f.map(x => x.clave), ['E10-2026-09', 'E16-2026-09', 'E10-2025-05', 'E10-2025-04', 'E10-2025-03', 'E16-2025-03'])
  assert.equal(f[0].unidad, 'EMASIVO 10')
  assert.equal(f[0].titulo, 'Septiembre 2026')
})

test('filasKm: meses sin km (null o 0) no inventan datos; solo excel y manual se pueden borrar', () => {
  const f = Object.fromEntries(U.filasKm(mensualDemo).map(x => [x.clave, x]))
  assert.equal(f['E10-2026-09'].sinKm, true)
  assert.equal(f['E10-2026-09'].km, null)
  assert.equal(f['E16-2026-09'].sinKm, true)                     // km = 0 cuenta como «sin km»
  assert.equal(f['E16-2026-09'].km, null)
  assert.equal(f['E10-2026-09'].puedeBorrar, false)
  assert.equal(f['E10-2025-03'].puedeBorrar, true)               // excel
  assert.equal(f['E10-2025-04'].puedeBorrar, true)               // manual
  assert.equal(f['E10-2025-05'].puedeBorrar, false)              // carga anterior: no está en dpv_km_mensual
  assert.deepEqual([f['E10-2025-03'].km, f['E10-2025-03'].kmPadron, f['E10-2025-03'].kmBuseton, f['E10-2025-03'].inm, f['E10-2025-03'].dpv],
    [1000000, 600000, 400000, 50, 20000])
  assert.equal(f['E10-2025-04'].kmPadron, null)
})

test('filasKm: filtros por unidad y «solo sin km»; datos vacíos no rompen', () => {
  assert.deepEqual(U.filasKm(mensualDemo, { unidad: 'E16' }).map(x => x.clave), ['E16-2026-09', 'E16-2025-03'])
  assert.deepEqual(U.filasKm(mensualDemo, { soloSinKm: true }).map(x => x.clave), ['E10-2026-09', 'E16-2026-09'])
  assert.deepEqual(U.filasKm(mensualDemo, { unidad: 'E10', soloSinKm: true }).map(x => x.clave), ['E10-2026-09'])
  assert.deepEqual(U.filasKm(null), [])
  assert.deepEqual(U.filasKm({}), [])
  assert.deepEqual(U.filasKm({ e10: [], e16: [] }, { soloSinKm: true }), [])
})

test('filasKm: un mes sin «origen» (respuesta de un backend antiguo) se toma como sin km y no se puede borrar', () => {
  const f = U.filasKm({ e10: [{ mes: '2026-01', km: null }], e16: [] })
  assert.equal(f.length, 1)
  assert.deepEqual([f[0].origen, f[0].puedeBorrar, f[0].sinKm, f[0].dpv, f[0].nivel, f[0].inm, f[0].kmPadron, f[0].kmBuseton],
    ['sin_km', false, true, null, null, null, null, null])
})

test('resumenSinKm: una frase por unidad con meses sin km; sin datos → lista vacía', () => {
  assert.deepEqual(U.resumenSinKm({ E10: ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05'], E16: ['2026-10'] }),
    ['EMASIVO 10: Ene 26, Feb 26, Mar 26, Abr 26 y 1 más', 'EMASIVO 16: Oct 26'])
  assert.deepEqual(U.resumenSinKm({ E10: [], E16: ['2026-09', '2026-10'] }), ['EMASIVO 16: Sep 26 y Oct 26'])
  assert.deepEqual(U.resumenSinKm({ E10: [], E16: [] }), [])
  assert.deepEqual(U.resumenSinKm(undefined), [])
})

test('avisosCalidad: reparados, ordenados y que no cuentan, en singular y plural; sin nada que decir → vacío', () => {
  const a = U.avisosCalidad({ textos_reparados: 2087, normalizados: { estado: 12, tipologia: 30, hora: 1, ruta: 0 }, no_cuentan_para_dpv: 162 }, ['Contestado Contundente'])
  assert.equal(a.length, 3)
  assert.equal(a[0], '2.087 textos con caracteres dañados (como «Ã³» en vez de «ó») se repararon.')
  assert.equal(a[1], 'Se ordenó el formato (espacios, mayúsculas, tildes) en: tipología (30), estado (12), hora (1).')   // de más a menos; sin los de 0
  assert.equal(a[2], '162 eventos no cuentan como inmovilización para el DPV («Contestado Contundente»).')
  const u = U.avisosCalidad({ textos_reparados: 1, normalizados: {}, no_cuentan_para_dpv: 1 })
  assert.deepEqual(u, ['1 texto con caracteres dañados (como «Ã³» en vez de «ó») se reparó.', '1 evento no cuenta como inmovilización para el DPV.'])
  assert.deepEqual(U.avisosCalidad({ textos_reparados: 0, normalizados: {}, no_cuentan_para_dpv: 0 }), [])
  assert.deepEqual(U.avisosCalidad(undefined), [])
  assert.match(U.avisosCalidad({ normalizados: { campo_raro: 2 } })[0], /campo_raro \(2\)/)    // un campo nuevo del backend se muestra tal cual
  assert.match(U.avisosCalidad({}, [])[0] || 'vacío', /vacío/)
  assert.match(U.avisosCalidad({ no_cuentan_para_dpv: 3 }, ['A', 'B'])[0], /«A», «B»/)
})

test('FORMATO_MENSUAL cubre los tres formatos que devuelve el backend', () => {
  assert.deepEqual(Object.keys(U.FORMATO_MENSUAL).sort(), ['anterior', 'mixto', 'nuevo'])
})

test('mensajeError: usa el detalle del backend (texto o lista de validación) y avisa distinto si no hay respuesta', () => {
  const resp = (status, detail) => ({ response: { status, data: detail === undefined ? {} : { detail } } })
  assert.equal(U.mensajeError(resp(400, 'Faltan columnas requeridas: DPV')), 'Faltan columnas requeridas: DPV')
  assert.equal(U.mensajeError(resp(413, 'El archivo supera 10 MB')), 'El archivo supera 10 MB')
  assert.equal(U.mensajeError(resp(422, [{ loc: ['body', 'km_total'], msg: 'field required', type: 'missing' }, { msg: 'otro' }])), 'field required · otro')
  assert.equal(U.mensajeError(resp(500), 'Error al procesar el archivo'), 'Error al procesar el archivo (error 500).')
  assert.equal(U.mensajeError(resp(500, '   ')), 'No se pudo completar la operación (error 500).')
  assert.equal(U.mensajeError(resp(502, []), 'X'), 'X (error 502).')
  assert.match(U.mensajeError({ isAxiosError: true, request: {} }), /No hay conexión con el servidor/)
  assert.match(U.mensajeError({ request: {} }), /No hay conexión/)
  assert.equal(U.mensajeError(new TypeError('x is undefined'), 'Error al procesar el archivo'), 'Error al procesar el archivo.')   // un fallo propio no se disfraza de «sin conexión»
  assert.equal(U.mensajeError(undefined), 'No se pudo completar la operación.')
})
