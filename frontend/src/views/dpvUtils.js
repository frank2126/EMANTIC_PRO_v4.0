// dpvUtils.js — Lógica pura del tablero DPV (sin Vue ni Pinia).
//
// La usa dashboardStore.js para filtrar y agrupar, y DashboardDPV.vue para dibujar.
// Mismo modelo de interacción que el tablero ICO (icoUtils.js), que se reutiliza para lo común:
//   · SLICERS (barra superior)     → filtros duros: Unidad, Año, Mes, Franja, Tipología, Estado y búsqueda.
//   · SELECCIÓN (clic en gráficas) → filtro cruzado: cada visual muestra TODAS sus categorías con la selección
//     resaltada y filtra a las demás visuales, a los KPIs y a la tabla de detalle. Ctrl/⌘/Shift + clic suma elementos.
//
// Regla de negocio del DPV (la fuente de verdad es el backend, dpv_reglas.py):
//   DPV = km del mes ÷ inmovilizaciones del mes, por unidad (EMASIVO 10 / 16).
//   Inmovilizaciones = eventos del mes (por FECHA INMOVILIZACION) con estado distinto de «Contestado Contundente».
//   Estándar: DPV ≥ 10.000 km · Crítico: DPV ≤ 7.000 km · entre ambos: en alerta.

import {
  sinTildes, normTipologia, etiquetaTipologia, ufDeRegistro, diasParaResponder, modoHeat, nivelHeat,
  etiquetaPeriodo, HEAT_COLORES, COLOR_TIPOLOGIA, MESES_CORTOS, MESES_LARGOS, DIAS_CORTOS, CIRC,
  ESTADO_PENDIENTE,
} from './icoUtils.js'

// Lo que el tablero DPV comparte tal cual con el de ICO (mismas escalas, mismos textos, misma tabla ordenable)
export {
  ordenar, hoyISO, tituloPeriodo, modoHeat, etiquetaTipologia, haySeleccion, sinTildes, MESES_CORTOS, MESES_LARGOS,
  HEAT_COLORES, HEAT_DIA, HEAT_RELATIVO, COLOR_TIPOLOGIA, ESTADO_PENDIENTE, diasParaResponder,
} from './icoUtils.js'

// ── Reglas de negocio ajustables ─────────────────────────────────────────────

// Respaldo local: los umbrales reales llegan en /api/dpv-mensual (variables DPV_KM_ESTANDAR / DPV_KM_CRITICO del .env)
export const UMBRALES_DEFECTO = { estandar: 10000, critico: 7000 }
// Respaldo local de la regla «¿cuenta como inmovilización?». El backend manda `cuenta` en cada evento y manda la lista
// en /api/dpv-mensual (DPV_ESTADOS_DESCARTADOS); esta constante solo se usa si el backend es anterior a este cambio.
export const ESTADO_DESCARTADO = 'Contestado Contundente'
// Valor del slicer Estado: '' = solo los que cuentan para el DPV · '*' = todos · otro texto = ese estado
export const ESTADO_TODOS = '*'

// Nivel del DPV. El color solo apoya: cada nivel lleva siempre su texto, su posición frente a las líneas de referencia
// y el número. Terna verde/ámbar/rojo del mapa de calor (separa bien también para daltónicos).
export const NIVEL = {
  cumple:  { texto: 'Cumple el estándar', corto: 'Cumple',  color: HEAT_COLORES.bajo,  icono: '●' },
  alerta:  { texto: 'En alerta',          corto: 'Alerta',  color: HEAT_COLORES.medio, icono: '◆' },
  critico: { texto: 'Crítico',            corto: 'Crítico', color: HEAT_COLORES.alto,  icono: '▲' },
}
// Mismos colores por unidad que los botones de unidad del tablero
export const COLOR_UF = { UF10: '#074e7a', UF16: '#1f7a6e' }
export const UNIDADES = [{ key: 'UF10', label: 'UF-10', nombre: 'EMASIVO 10' }, { key: 'UF16', label: 'UF-16', nombre: 'EMASIVO 16' }]
// Ancho mínimo por mes en el gráfico de DPV mensual: con menos espacio las etiquetas se pisarían (se desplaza en horizontal).
// A 38 px caben 22 meses en un escritorio de 1440 px sin desplazar.
export const ANCHO_MES_PX = 38
// Alto del gráfico en px. DashboardDPV.vue lo repite en el viewBox del SVG (viewBox="0 0 1000 190"): si cambias uno, cambia el otro.
export const ALTO_GRAFICA = 190

// ── Helpers de texto y fecha ─────────────────────────────────────────────────

const pad2 = n => String(n).padStart(2, '0')
const SD = 'S/D'
const clave = s => sinTildes(s).replace(/\s+/g, ' ').trim().toUpperCase()

/** Fallback local de la regla del backend: todo estado cuenta como inmovilización salvo «Contestado Contundente». */
export function cuentaParaDpv(estado) {
  return clave(estado) !== clave(ESTADO_DESCARTADO)
}

/** 'A. M.' / 'P. M.' / 'pm' → 'AM' | 'PM'; si falta, se deduce de la hora (antes de las 12 = AM). */
export function normFranja(valor, hora = '') {
  const v = String(valor ?? '').replace(/[^A-Za-z]/g, '').toUpperCase()
  if (v === 'AM' || v === 'PM') return v
  const h = parseInt(String(hora || '').slice(0, 2), 10)
  return Number.isNaN(h) ? '' : (h < 12 ? 'AM' : 'PM')
}

/** Hora (0-23) de un evento, o null si no tiene hora válida. */
export function horaDe(r) {
  const m = /^(\d{1,2}):/.exec(r.hora || '')
  if (!m) return null
  const h = parseInt(m[1], 10)
  return h >= 0 && h < 24 ? h : null
}

/** Evento del backend (/api/dpv?slim=true) → fila del tablero. */
export function normDPV(r) {
  const empresa = String(r.empresa ?? '').trim()
  const movil = String(r.movil ?? '').trim()
  const estado = String(r.estado ?? '').trim()
  const fecha = String(r.fecha || r.fecha_inmovilizacion || '').slice(0, 10)
  const hora = String(r.hora ?? '').slice(0, 8)
  return {
    id: r.id,
    dpv_id: r.dpv_id,
    estado,
    cuenta: typeof r.cuenta === 'boolean' ? r.cuenta : cuentaParaDpv(estado),   // ¿cuenta para el DPV? (la decide el backend)
    empresa,
    uf: ufDeRegistro(empresa, movil),                                          // 'UF10' | 'UF16' | ''
    placa: String(r.placa ?? '').trim(),
    movil,
    causa_inmovilizacion: String(r.causa || r.causa_inmovilizacion || '').trim(),
    descripcion: String(r.descripcion || r.descripcion_novedad || '').trim(),
    operador: String(r.operador ?? '').trim(),
    fecha,                                                                      // FECHA INMOVILIZACION 'YYYY-MM-DD'
    hora,
    fh: `${fecha} ${hora}`,                                                     // para ordenar por fecha y hora
    fecha_inicio: String(r.fecha_inicio || '').slice(0, 10),
    fecha_cierre: String(r.fecha_cierre || '').slice(0, 10),                    // fin de la ventana para contestar
    tipologia: normTipologia(r.tipologia),                                      // 'PADRON' | 'BUSETON' (sin tildes)
    ruta: String(r.ruta ?? '').trim(),
    dia_semana: String(r.dia_semana ?? '').trim(),
    alerta: String(r.alerta ?? '').trim(),
    franja: normFranja(r.franja || r.franja_horaria, hora),                     // 'AM' | 'PM'
  }
}

// El Excel (Transmitools) guarda la causa recortada a 20 caracteres («ACELERACION - POTENC»). Si en los datos hay una
// etiqueta más larga que empieza igual y es la única, la causa recortada se unifica con ella para no partir el conteo.
export const CAUSA_LONGITUD_MAX = 20

export function unificarCausas(rows) {
  const largas = new Set()
  const cortas = new Set()
  for (const r of rows) {
    const c = r.causa_inmovilizacion
    if (!c) continue
    if (c.length > CAUSA_LONGITUD_MAX) largas.add(c)
    else if (c.length === CAUSA_LONGITUD_MAX) cortas.add(c)
  }
  if (!largas.size || !cortas.size) return rows
  const mapa = new Map()
  for (const corta of cortas) {
    const candidatas = [...largas].filter(l => l.startsWith(corta))
    if (candidatas.length === 1) mapa.set(corta, candidatas[0])               // ambigua (varias) → no se toca
  }
  if (!mapa.size) return rows
  for (const r of rows) {
    const m = mapa.get(r.causa_inmovilizacion)
    if (m) r.causa_inmovilizacion = m
  }
  return rows
}

// ── Dimensiones de selección cruzada ─────────────────────────────────────────

export const DIM = {
  periodos:  r => r.fecha,                                    // se compara por día ('YYYY-MM-DD') o mes ('YYYY-MM')
  hora:      r => { const h = horaDe(r); return h === null ? SD : pad2(h) },
  tipologia: r => r.tipologia || SD,
  causa:     r => r.causa_inmovilizacion || SD,
  ruta:      r => r.ruta || SD,
  movil:     r => r.movil || r.placa || SD,
  operador:  r => r.operador || SD,
}

export const SELECCION_VACIA = () => ({
  periodos: [], hora: [], tipologia: [], causa: [], ruta: [], movil: [], operador: [],
})

export const filtrosVacios = () => ({
  uf: [],              // ['UF10', 'UF16']
  anio: '',            // '2026'; '' = todos los años
  meses: [],           // [9] → solo septiembre; [] = todos los meses (requiere año)
  franja: [],          // ['AM', 'PM']
  tipologia: [],       // ['PADRON', 'BUSETON']
  estado: '',          // '' = los que cuentan para el DPV · ESTADO_TODOS · un estado concreto
  busqueda: '',        // móvil, placa, operador o número de DPV
})

function coincide(dim, r, keys) {
  if (dim === 'periodos') {
    return keys.some(k => (k.length === 10 ? r.fecha === k : r.fecha.slice(0, 7) === k))
  }
  return keys.includes(DIM[dim](r))
}

// ── Filtros ──────────────────────────────────────────────────────────────────

/** Slicers: Unidad, Año/Mes (sobre FECHA INMOVILIZACION), Franja, Tipología, Estado y búsqueda. */
export function aplicarSlicers(rows, f) {
  const q = sinTildes(f.busqueda || '').trim().toLowerCase()
  const meses = f.meses.length ? new Set(f.meses) : null
  const anio = f.anio ? String(f.anio) : ''
  return rows.filter(r => {
    if (f.uf.length && !f.uf.includes(r.uf)) return false
    if (anio) {
      if (r.fecha.slice(0, 4) !== anio) return false
      if (meses && !meses.has(parseInt(r.fecha.slice(5, 7), 10))) return false
    }
    if (f.franja.length && !f.franja.includes(r.franja)) return false
    if (f.tipologia.length && !f.tipologia.includes(r.tipologia)) return false
    if (f.estado === ESTADO_TODOS) { /* todos los estados */ }
    else if (f.estado) { if (r.estado !== f.estado) return false }
    else if (!r.cuenta) return false                                     // por defecto: solo lo que cuenta para el DPV
    if (q) {
      const pajar = sinTildes(`${r.movil} ${r.placa} ${r.operador} ${r.dpv_id}`).toLowerCase()
      if (!pajar.includes(q)) return false
    }
    return true
  })
}

/** Selección cruzada. `excepto` omite una dimensión (la visual propia, que debe mostrar todas sus categorías). */
export function aplicarSeleccion(rows, sel, excepto = null) {
  const activas = Object.entries(sel).filter(([dim, keys]) => dim !== excepto && keys.length)
  if (!activas.length) return rows
  return rows.filter(r => activas.every(([dim, keys]) => coincide(dim, r, keys)))
}

/** Opciones de los slicers a partir de los datos cargados. */
export function opcionesSlicers(rows) {
  const anios = new Set()
  const meses = {}
  const estados = new Set()
  for (const r of rows) {
    if (r.fecha) {
      const y = r.fecha.slice(0, 4)
      const m = parseInt(r.fecha.slice(5, 7), 10)
      anios.add(y)
      if (!meses[y]) meses[y] = new Set()
      meses[y].add(m)
    }
    if (r.estado) estados.add(r.estado)
  }
  const mesesPorAnio = {}
  for (const y of Object.keys(meses)) mesesPorAnio[y] = [...meses[y]].sort((a, b) => a - b)
  return { anios: [...anios].sort().reverse(), mesesPorAnio, estados: [...estados].sort((a, b) => a.localeCompare(b, 'es')) }
}

/** Periodo inicial = año y mes más recientes con datos (como abre el tablero ICO). null si no hay fechas. */
export function periodoPorDefecto(rows) {
  let ultima = ''
  for (const r of rows) if (r.fecha > ultima) ultima = r.fecha
  return ultima ? { anio: ultima.slice(0, 4), meses: [parseInt(ultima.slice(5, 7), 10)] } : null
}

/** 'YYYY-MM' del único mes elegido en los slicers, o '' si hay varios, ninguno o falta el año. */
export function mesUnico(f) {
  return f.anio && f.meses.length === 1 ? `${f.anio}-${pad2(f.meses[0])}` : ''
}

/** ¿El mes 'YYYY-MM' cae dentro del periodo de los slicers? (sin año = todo el histórico) */
export function enPeriodo(mes, f) {
  if (!f.anio) return true
  if (mes.slice(0, 4) !== String(f.anio)) return false
  return !f.meses.length || f.meses.includes(parseInt(mes.slice(5, 7), 10))
}

// ── Agrupaciones ─────────────────────────────────────────────────────────────

/** Ranking por dimensión: [{ key, label, total, pct, seleccionado }] de mayor a menor. */
export function ranking(rows, keyFn, { seleccion = [], labelFn = k => k } = {}) {
  const map = new Map()
  for (const r of rows) {
    const k = keyFn(r)
    map.set(k, (map.get(k) || 0) + 1)
  }
  const total = rows.length || 1
  const sel = new Set(seleccion)
  return [...map.entries()]
    .map(([key, n]) => ({ key, label: labelFn(key), total: n, pct: Math.round((n / total) * 100), seleccionado: sel.has(key) }))
    .sort((a, b) => b.total - a.total || String(a.key).localeCompare(String(b.key), 'es', { numeric: true }))
}

/** Dona de tipología: siempre PADRÓN y BUSETON (aunque sea 0) y el % se calcula sobre lo que muestra la dona. */
export function dona(rows, seleccion = []) {
  const lista = ranking(rows, DIM.tipologia, { seleccion, labelFn: etiquetaTipologia })
  for (const k of ['PADRON', 'BUSETON']) {
    if (!lista.some(s => s.key === k)) {
      lista.push({ key: k, label: etiquetaTipologia(k), total: 0, pct: 0, seleccionado: seleccion.includes(k) })
    }
  }
  const orden = k => { const i = ['PADRON', 'BUSETON'].indexOf(k); return i === -1 ? 99 : i }
  lista.sort((a, b) => orden(a.key) - orden(b.key))
  const total = rows.length
  let offset = 0
  return lista.map(seg => {
    const dash = total ? (seg.total / total) * CIRC : 0
    const out = { ...seg, color: COLOR_TIPOLOGIA[seg.key] || '#94a3b8', dash, gap: CIRC - dash, offset }
    offset += dash
    return out
  })
}

/** Contadores secundarios de la vista (sobre los eventos tras slicers + selección). */
export function kpisEventos(rows, hoy) {
  const moviles = new Set()
  const causas = new Set()
  let sinContestar = 0
  let ventanaAbierta = 0
  for (const r of rows) {
    if (r.movil || r.placa) moviles.add(r.movil || r.placa)
    if (r.causa_inmovilizacion) causas.add(r.causa_inmovilizacion)
    if (r.estado === ESTADO_PENDIENTE) {
      sinContestar++
      if (diasParaResponder(r, hoy) !== null) ventanaAbierta++
    }
  }
  return { total: rows.length, moviles: moviles.size, causas: causas.size, sinContestar, ventanaAbierta }
}

// ── Mapa de calor ────────────────────────────────────────────────────────────

/**
 * Columnas del mapa de calor por día / mes. `rows` debe venir SIN la selección de periodos (la visual propia).
 * Devuelve { modo, columnas:[{ key, label, sub, finDeSemana, titulo, total, nivel, color, seleccionado }], max, ticks }.
 */
export function heatmap(rows, f, seleccion = []) {
  const modo = modoHeat(f)
  const sel = new Set(seleccion)
  const acum = new Map()
  for (const r of rows) {
    if (!r.fecha) continue
    const k = modo === 'dia' ? r.fecha : r.fecha.slice(0, 7)
    acum.set(k, (acum.get(k) || 0) + 1)
  }

  let cols = []
  if (modo === 'dia') {
    const y = Number(f.anio)
    const m = f.meses[0]
    const n = new Date(y, m, 0).getDate()
    for (let d = 1; d <= n; d++) {
      const dow = new Date(y, m - 1, d).getDay()
      cols.push({
        key: `${y}-${pad2(m)}-${pad2(d)}`, label: String(d), sub: DIAS_CORTOS[dow],
        finDeSemana: dow === 0 || dow === 6, titulo: `${d} de ${MESES_LARGOS[m - 1].toLowerCase()} de ${y}`,
      })
    }
  } else if (modo === 'mes') {
    const y = Number(f.anio)
    const meses = f.meses.length ? [...f.meses].sort((a, b) => a - b) : MESES_CORTOS.map((_, i) => i + 1)
    cols = meses.map(m => ({
      key: `${y}-${pad2(m)}`, label: MESES_CORTOS[m - 1], sub: '', finDeSemana: false, titulo: `${MESES_LARGOS[m - 1]} ${y}`,
    }))
  } else {
    const keys = [...acum.keys()].sort()
    if (keys.length) {
      let [y, m] = keys[0].split('-').map(Number)
      const [yf, mf] = keys[keys.length - 1].split('-').map(Number)
      while (y < yf || (y === yf && m <= mf)) {
        cols.push({
          key: `${y}-${pad2(m)}`, label: MESES_CORTOS[m - 1], sub: m === 1 ? String(y) : '', finDeSemana: false,
          titulo: `${MESES_LARGOS[m - 1]} ${y}`,
        })
        m++
        if (m > 12) { m = 1; y++ }
      }
    }
  }

  const max = cols.reduce((mx, c) => Math.max(mx, acum.get(c.key) || 0), 0)
  const columnas = cols.map(c => {
    const total = acum.get(c.key) || 0
    const nivel = nivelHeat(total, max, modo)
    return { ...c, total, nivel, color: HEAT_COLORES[nivel], seleccionado: sel.has(c.key) }
  })
  const ticks = [...new Set([max, Math.round(max / 2), 0])]
  return { modo, columnas, max, ticks }
}

/** Eventos por hora del día (0-23). Mismo formato que heatmap(); `rows` debe venir SIN la selección de horas. */
export function horasHeat(rows, seleccion = []) {
  const acum = new Array(24).fill(0)
  for (const r of rows) {
    const h = horaDe(r)
    if (h !== null) acum[h]++
  }
  const sel = new Set(seleccion)
  const max = Math.max(0, ...acum)
  const columnas = acum.map((total, h) => {
    const nivel = nivelHeat(total, max, 'hora')
    return {
      key: pad2(h), label: pad2(h), sub: '', finDeSemana: false, titulo: `${pad2(h)}:00 a ${pad2(h)}:59`,
      total, nivel, color: HEAT_COLORES[nivel], seleccionado: sel.has(pad2(h)),
    }
  })
  return { modo: 'hora', columnas, max, ticks: [...new Set([max, Math.round(max / 2), 0])] }
}

// ── DPV mensual (km ÷ inmovilizaciones) ──────────────────────────────────────

/** 'cumple' (≥ estándar) · 'critico' (≤ crítico) · 'alerta' (en medio) · null sin dato. */
export function nivelDpv(dpv, u = UMBRALES_DEFECTO) {
  if (dpv == null || Number.isNaN(dpv)) return null
  if (dpv >= u.estandar) return 'cumple'
  if (dpv <= u.critico) return 'critico'
  return 'alerta'
}

/** Campos de la serie mensual según la tipología elegida: una sola → su DPV; ninguna o ambas → el general. */
export function camposSerie(tipologia = []) {
  const t = tipologia.length === 1 ? tipologia[0] : ''
  if (t === 'PADRON') return { tip: t, dpv: 'dpv_padron', km: 'km_padron', inm: 'inm_padron', etiqueta: 'DPV Padrón' }
  if (t === 'BUSETON') return { tip: t, dpv: 'dpv_buseton', km: 'km_buseton', inm: 'inm_buseton', etiqueta: 'DPV Buseton' }
  return { tip: '', dpv: 'dpv', km: 'km', inm: 'inm', etiqueta: 'DPV General' }
}

/** Mes anterior de 'YYYY-MM' ('2026-01' → '2025-12'). */
export function mesAnterior(mes) {
  let y = Number(mes.slice(0, 4))
  let m = Number(mes.slice(5, 7)) - 1
  if (m < 1) { m = 12; y-- }
  return `${y}-${pad2(m)}`
}

/**
 * DPV del periodo de los slicers a partir de la serie mensual. `series` = [{ uf, datos:[…] }] (una o varias unidades).
 * DPV = Σkm ÷ Σinmovilizaciones, solo con los meses que tienen km: los meses sin km se listan en `sinKm` y NO entran al
 * cálculo (falta el dato; no son «cero km»). Un mes de la carga antigua que solo trae el DPV (sin km) vale únicamente
 * cuando es el único mes del periodo. Con un solo mes y una sola unidad trae la variación frente al mes anterior (`delta`).
 */
export function kpiDpv(series, f, u = UMBRALES_DEFECTO) {
  const c = camposSerie(f.tipologia)
  let km = 0
  let inm = 0
  let usados = 0
  const sinKm = []
  const heredados = []
  for (const s of series) {
    for (const m of s.datos) {
      if (!enPeriodo(m.mes, f)) continue
      const kmM = m[c.km]
      const inmM = m[c.inm]
      if (kmM > 0 && inmM != null) { km += kmM; inm += inmM; usados++ }
      else if (!c.tip && m.dpv != null) heredados.push(m)               // la carga antigua solo guardó el DPV
      else sinKm.push({ uf: s.uf, mes: m.mes, eventos: m.inm || 0, motivo: kmM > 0 ? 'eventos' : 'km' })
    }
  }
  let dpv = inm > 0 ? km / inm : null
  if (dpv === null && usados === 0 && heredados.length === 1) dpv = heredados[0].dpv
  let delta = null
  const unico = mesUnico(f)
  if (unico && series.length === 1 && dpv !== null) {
    const prev = series[0].datos.find(m => m.mes === mesAnterior(unico))
    if (prev && prev[c.dpv] != null) delta = dpv - prev[c.dpv]
  }
  return {
    dpv, km: usados ? km : null, inm: usados ? inm : null, nivel: nivelDpv(dpv, u), sinKm, meses: usados,
    parcial: usados > 0 && sinKm.length > 0, delta,
    sinInmovilizaciones: usados > 0 && inm === 0,                        // hay km pero ninguna varada: el DPV no se puede calcular
    campo: c,
  }
}

/** Paso «redondo» (1, 2, 5 × 10ⁿ) para el eje Y. */
export function pasoLindo(bruto) {
  const mag = Math.pow(10, Math.floor(Math.log10(bruto || 1)))
  const n = bruto / mag
  return (n < 1.5 ? 1 : n < 3 ? 2 : n < 7 ? 5 : 10) * mag
}

/** Escala del eje Y: abarca los valores y las dos líneas de referencia, con marcas redondas. */
export function escalaY(valores, u = UMBRALES_DEFECTO) {
  const vs = valores.filter(v => v != null && !Number.isNaN(v)).concat([u.estandar, u.critico])
  const min = Math.min(...vs)
  const max = Math.max(...vs)
  const paso = pasoLindo((max - min) / 4 || max * 0.2 || 1000)
  return { minV: Math.max(0, Math.floor(min / paso) * paso - paso), maxV: Math.ceil(max / paso) * paso + paso * 0.15, paso }
}

// Ancho (unidades del viewBox) del SVG de líneas: se estira al ancho real del contenedor. Los trazos usan
// vector-effect: non-scaling-stroke y los puntos / etiquetas son HTML posicionado en %, así nada se deforma.
export const VISTA_X = 1000

/**
 * Geometría del gráfico de DPV mensual de una unidad. El eje X va en fracciones (`fx` 0–1, un mes por columna) y
 * en unidades del viewBox (`x`); el eje Y va en px (`y`), de 0 a `alto`. Devuelve puntos (con `y: null` en los meses
 * sin valor), tramos continuos de línea (un mes sin km parte la línea), áreas, marcas del eje y líneas de referencia.
 */
export function geometriaSerie(datos, { campo = 'dpv', alto = ALTO_GRAFICA, umbrales = UMBRALES_DEFECTO, padT = 24, padB = 34 } = {}) {
  const n = datos.length
  const escala = escalaY(datos.map(m => m[campo]), umbrales)
  const h = alto - padT - padB
  const yDe = v => padT + (1 - (v - escala.minV) / ((escala.maxV - escala.minV) || 1)) * h
  const r1 = v => Math.round(v * 10) / 10

  const puntos = datos.map((m, i) => {
    const v = m[campo]
    const tiene = v != null && !Number.isNaN(v)
    const fx = n ? (i + 0.5) / n : 0.5
    return {
      i, mes: m.mes, label: m.mes_label, m, valor: tiene ? v : null, fx, x: r1(fx * VISTA_X),
      y: tiene ? r1(yDe(v)) : null, nivel: tiene ? nivelDpv(v, umbrales) : null,
    }
  })

  const tramos = []
  let actual = []
  for (const p of puntos) {
    if (p.y === null) { if (actual.length) tramos.push(actual); actual = [] } else actual.push(p)
  }
  if (actual.length) tramos.push(actual)
  const base = r1(yDe(escala.minV))
  const lineas = tramos.filter(t => t.length > 1).map(t => t.map((p, i) => `${i ? 'L' : 'M'}${p.x},${p.y}`).join(' '))
  const areas = tramos.filter(t => t.length > 1).map(t =>
    `M${t[0].x},${base} ` + t.map(p => `L${p.x},${p.y}`).join(' ') + ` L${t[t.length - 1].x},${base} Z`)

  const ticks = []
  for (let v = Math.ceil(escala.minV / escala.paso) * escala.paso; v <= escala.maxV + 1e-9; v += escala.paso) {
    ticks.push({ valor: v, y: r1(yDe(v)), label: Math.round(v).toLocaleString('es-CO') })
  }
  return {
    n, alto, padT, padB, escala, puntos, lineas, areas, ticks, base, vistaX: VISTA_X,
    yEstandar: r1(yDe(umbrales.estandar)), yCritico: r1(yDe(umbrales.critico)),
  }
}

/**
 * Alto aproximado (px) del tooltip de un mes, según las líneas que lleva: título, valor, N líneas de detalle y nivel.
 * Calibrado con el CSS del tooltip (8 px de relleno; letras de 10,5 / 16 / 11 px): con 3 líneas y nivel mide ≈ 107 px.
 */
export function altoTooltipMes(d) {
  return 52 + 14 * d.lineas.length + (d.nivel ? 17 : 0)
}

/**
 * ¿El tooltip va DEBAJO del punto? Por defecto va encima. Solo va debajo si encima no cabe dentro del gráfico y debajo sí
 * (con 8 px de margen: el relleno inferior de la tarjeta). Si no cabe en ninguno va encima, porque encima puede pasar sobre
 * la leyenda sin salirse de la tarjeta, mientras que debajo se saldría por el borde inferior.
 * `y` = altura del punto dentro del gráfico (px) y `alto` = alto del tooltip (altoTooltipMes).
 */
export function tooltipAbajo(y, alto, altoGrafico = ALTO_GRAFICA) {
  const arribaCabe = y - 8 - alto >= 0
  const abajoCabe = y + 14 + alto <= altoGrafico + 8
  return !arribaCabe && abajoCabe
}

/**
 * Dónde dejar el desplazamiento horizontal (scrollLeft) de un gráfico más ancho que su tarjeta para que se vea el tramo
 * [izq, der] (px dentro del lienzo). Devuelve null cuando no hay que mover nada:
 *  · el tramo ya se ve completo (un clic sobre un mes visible no hace saltar el gráfico);
 *  · el tramo es más ancho que la pantalla (un año entero en un celular) y ya se ve al menos un mes (`minimo` px): p. ej. al
 *    sumar meses con Ctrl+clic no se aleja el mes recién pulsado.
 * Si no se ve completo, un tramo que cabe se centra; uno que no cabe se alinea por su inicio, con `margen` px de respiro.
 */
export function desplazamientoParaVer(izq, der, scrollLeft, visible, { margen = 8, minimo = 38 } = {}) {
  if (!(visible > 0) || !(der > izq)) return null
  if (izq >= scrollLeft && der <= scrollLeft + visible) return null
  const ancho = der - izq
  if (ancho + 2 * margen > visible) {
    const solape = Math.min(der, scrollLeft + visible) - Math.max(izq, scrollLeft)
    return solape >= minimo ? null : Math.max(0, Math.round(izq - margen))
  }
  return Math.max(0, Math.round(izq + ancho / 2 - visible / 2))
}

/** Qué puntos llevan su valor escrito: todos si caben (≤ max); si no, el primero, el último, el mínimo y el máximo. */
export function indicesEtiquetados(puntos, max = 14) {
  const con = puntos.filter(p => p.valor !== null)
  if (con.length <= max) return new Set(con.map(p => p.i))
  const out = new Set([con[0].i, con[con.length - 1].i])
  let mn = con[0]
  let mx = con[0]
  for (const p of con) {
    if (p.valor < mn.valor) mn = p
    if (p.valor > mx.valor) mx = p
  }
  out.add(mn.i)
  out.add(mx.i)
  return out
}

// ── Mensajes del DPV mensual (tooltip y avisos de las tarjetas) ──────────────

// De dónde salieron los km de un mes (campo `origen` de /api/dpv-mensual)
export const ORIGEN_KM = {
  excel: 'Km cargados desde el Excel',
  manual: 'Km ingresados a mano',
  legacy: 'Carga anterior (solo guardó el DPV)',
  sin_km: 'Sin km cargados',
}

const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`

/**
 * Texto del tooltip de un mes del gráfico. `p` = punto de geometriaSerie() (con `m` = registro del mes) y `campo` = camposSerie().
 * Devuelve { titulo, valor, unidad, lineas[], nivel, nivelColor, icono } ya formateados.
 */
export function detalleMes(p, campo) {
  const m = p.m || {}
  const km = m[campo.km]
  const inm = m[campo.inm]
  const lineas = []
  const out = { titulo: tituloMes(p.mes), valor: 'Sin km', unidad: 'cargados', lineas, nivel: '', nivelColor: '', icono: '' }
  if (p.valor !== null) {
    out.valor = fmtKm(p.valor)
    out.unidad = 'km entre varadas'
    if (km > 0 && inm != null) lineas.push(`${fmtKm(km)} km ÷ ${plural(inm, 'inmovilización', 'inmovilizaciones')}`)
    const nv = NIVEL[p.nivel]
    if (nv) Object.assign(out, { nivel: nv.texto, nivelColor: nv.color, icono: nv.icono })
  } else {
    lineas.push(`${plural(inm || 0, 'inmovilización registrada', 'inmovilizaciones registradas')}`)
  }
  // Los descartados solo se conocen por mes completo (no por tipología): se muestran con la serie general
  if (!campo.tip && m.descartadas > 0) lineas.push(`${plural(m.descartadas, 'contestado con contundencia no cuenta', 'contestados con contundencia no cuentan')}`)
  if (ORIGEN_KM[m.origen]) lineas.push(ORIGEN_KM[m.origen])
  return out
}

/** Lista corta de meses para los avisos: 'Oct 26', 'Sep 26 y Oct 26', 'Jul 26, Ago 26, Sep 26 y 2 más'. */
export function listaMeses(meses, max = 3) {
  const t = meses.map(etiquetaMesCorta)
  if (t.length <= 1) return t.join('')
  if (t.length <= max) return `${t.slice(0, -1).join(', ')} y ${t[t.length - 1]}`
  return `${t.slice(0, max).join(', ')} y ${t.length - max} más`
}

/** Aviso de una tarjeta de DPV mensual a partir de kpiDpv(): null si no hace falta ninguno. `enlace` = invita a cargar km. */
export function avisoDpv(kpi) {
  const faltan = kpi.sinKm.map(x => x.mes)
  if (kpi.dpv === null && kpi.sinKm.length) {
    const n = kpi.sinKm.reduce((s, x) => s + x.eventos, 0)
    return {
      tipo: 'sin-km', enlace: true,
      texto: `Sin km cargados para ${listaMeses(faltan)}: ${plural(n, 'inmovilización registrada', 'inmovilizaciones registradas')}. Carga los km para calcular el DPV.`,
    }
  }
  if (kpi.sinInmovilizaciones) {
    return { tipo: 'sin-inm', enlace: false, texto: 'Hay km pero ninguna inmovilización en el periodo: el DPV no se puede calcular.' }
  }
  if (kpi.parcial) {
    return {
      tipo: 'parcial', enlace: true,
      texto: `Calculado con ${kpi.meses} de ${kpi.meses + kpi.sinKm.length} meses: faltan los km de ${listaMeses(faltan)}.`,
    }
  }
  return null
}

// ── Textos ───────────────────────────────────────────────────────────────────

/** 'YYYY-MM' → 'Mar 26' (igual que `mes_label` del backend). */
export function etiquetaMesCorta(mes) {
  return `${MESES_CORTOS[Number(mes.slice(5, 7)) - 1]} ${mes.slice(2, 4)}`
}

/** 'YYYY-MM' → 'Marzo 2026'. */
export function tituloMes(mes) {
  return `${MESES_LARGOS[Number(mes.slice(5, 7)) - 1]} ${mes.slice(0, 4)}`
}

/** Valor y variación en km para mostrar: 17343.3 → '17.343'. */
export function fmtKm(v) {
  return v == null ? '—' : Math.round(v).toLocaleString('es-CO')
}

const NOMBRE_DIM = {
  periodos: 'Periodo', hora: 'Hora', tipologia: 'Tipología', causa: 'Causa', ruta: 'Ruta', movil: 'Móvil', operador: 'Operador',
}

/** Chips de la selección activa para mostrarlos y poder quitarlos uno a uno. */
export function chipsSeleccion(sel) {
  const out = []
  for (const [dim, keys] of Object.entries(sel)) {
    for (const key of keys) {
      const valor = dim === 'periodos' ? etiquetaPeriodo(key) : dim === 'tipologia' ? etiquetaTipologia(key)
        : dim === 'hora' ? `${key}:00` : key
      out.push({ dim, key, texto: `${NOMBRE_DIM[dim]}: ${valor}` })
    }
  }
  return out
}

/** Clase de insignia (main.css) para el estado del evento: lo que no cuenta para el DPV en verde, lo pendiente en ámbar. */
export function claseEstado(estado) {
  const e = clave(estado)
  if (e === clave(ESTADO_DESCARTADO)) return 'badge-success'      // contestado con contundencia: no cuenta para el DPV
  if (e === clave(ESTADO_PENDIENTE)) return 'badge-warning'       // sin respuesta del operador
  return 'badge-info'                                              // el resto cuenta como inmovilización
}

// ── Exportación ──────────────────────────────────────────────────────────────

/** Una celda de CSV: comillas escapadas y, si empieza como fórmula (= + - @), se antepone ' para que Excel no la ejecute. */
export function celdaCSV(v) {
  let s = v == null ? '' : String(v)
  if (/^[=+\-@\t\r]/.test(s) && !/^-?\d+([.,]\d+)?$/.test(s)) s = `'${s}`
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

/** CSV (separado por comas) con las columnas de la tabla de detalle. */
export function csvDPV(rows) {
  const cab = ['DPV', 'Estado', 'Cuenta para el DPV', 'Móvil', 'Placa', 'Empresa', 'Tipología', 'Causa', 'Ruta', 'Operador',
               'Fecha inmovilización', 'Hora', 'Franja', 'Día', 'F. inicio DPV', 'F. cierre DPV', 'Alerta', 'Descripción']
  const filas = rows.map(r => [
    r.dpv_id, r.estado, r.cuenta ? 'Sí' : 'No', r.movil, r.placa, r.empresa, r.tipologia, r.causa_inmovilizacion, r.ruta,
    r.operador, r.fecha, r.hora, r.franja, r.dia_semana, r.fecha_inicio, r.fecha_cierre, r.alerta, r.descripcion,
  ])
  return [cab, ...filas].map(f => f.map(celdaCSV).join(',')).join('\r\n')
}

// ══════════════════════════════════════════════════════════════════════════════
//  Pantalla «Carga Masiva DPV» (CargaDPV.vue)
// ══════════════════════════════════════════════════════════════════════════════

/** Unidades como las nombra el backend (E10 / E16) con el nombre que se muestra. */
export const UNIDADES_CARGA = [{ key: 'E10', nombre: 'EMASIVO 10' }, { key: 'E16', nombre: 'EMASIVO 16' }]

/** Cómo se leyó el libro de km mensuales (campo `formato` de la respuesta de POST /api/dpv-mensual/upload). */
export const FORMATO_MENSUAL = {
  nuevo: 'Diseño nuevo (TOTAL KM, KM PADRON, KM BUSETON)',
  anterior: 'Diseño anterior (KMS, PADRON, BUSETON)',
  mixto: 'Una hoja con el diseño nuevo y otra con el anterior',
}

/** Nombre con el que se cuenta cada campo que el backend ordenó al cargar los eventos. */
const CAMPO_ORDENADO = {
  estado: 'estado', tipologia: 'tipología', hora: 'hora', alerta: 'alerta', empresa: 'empresa', fuente: 'fuente',
  placa: 'placa', movil: 'móvil', causa_inmovilizacion: 'causa', ruta: 'ruta', operador: 'operador', dia_semana: 'día',
  descripcion_novedad: 'descripción',
}

const entero = n => Math.round(n).toLocaleString('es-CO')

/**
 * Número escrito a mano o pegado desde el Excel: '1234567', '1.234.567', '1.234.567,5', '1,234,567.5', '1 234 567'.
 * Con grupos de tres cifras el punto (o la coma) es separador de miles. Devuelve null si no es un número válido o es negativo.
 * Mismo criterio que el backend (num_o_none en routes/datos.py), para que lo que se escribe aquí y lo que trae el Excel se lean igual.
 */
export function numeroDeTexto(t) {
  if (t === null || t === undefined) return null
  if (typeof t === 'number') return Number.isFinite(t) ? t : null
  const s = String(t).replace(/[\s ]/g, '')
  let n
  if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(s)) n = s.replace(/\./g, '').replace(',', '.')
  else if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(s)) n = s.replace(/,/g, '')
  else if (/^\d+([.,]\d+)?$/.test(s)) n = s.replace(',', '.')
  else return null
  const v = Number(n)
  return Number.isFinite(v) ? v : null
}

/**
 * Valida el formulario de km de un mes con las mismas reglas del backend (PUT /api/dpv-km) para avisar antes de enviar.
 * `f` = { empresa, mes, total, padron, buseton } tal como se escribieron. Devuelve { error } o { datos } listo para enviar.
 */
export function validarKmManual(f) {
  const empresa = String(f.empresa || '').trim().toUpperCase()
  if (!UNIDADES_CARGA.some(u => u.key === empresa)) return { error: 'Elige la unidad (EMASIVO 10 o EMASIVO 16).' }
  const mes = String(f.mes || '').trim()
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(mes)) return { error: 'Elige el mes.' }
  const total = numeroDeTexto(f.total)
  if (total === null || total <= 0) return { error: 'Escribe los km totales del mes (un número mayor que 0).' }
  const opcional = (v, nombre) => {
    if (v === null || v === undefined || String(v).trim() === '') return { v: null }
    const n = numeroDeTexto(v)
    return n === null ? { error: `Los km de ${nombre} no son un número válido.` } : { v: n }
  }
  const p = opcional(f.padron, 'Padrón')
  if (p.error) return { error: p.error }
  const b = opcional(f.buseton, 'Buseton')
  if (b.error) return { error: b.error }
  if (p.v !== null && b.v !== null && Math.abs(p.v + b.v - total) > Math.max(1, total * 0.01)) {
    return { error: `Padrón + Buseton (${entero(p.v + b.v)}) no coincide con el total (${entero(total)}).` }
  }
  return { datos: { empresa, mes, km_total: total, km_padron: p.v, km_buseton: b.v } }
}

/**
 * Filas de la tabla «Km por mes»: una por unidad y mes de la serie del backend, del mes más reciente al más antiguo.
 * `mensual` = respuesta de GET /api/dpv-mensual ({ e10, e16 }). `unidad` = '' | 'E10' | 'E16'; `soloSinKm` deja solo los meses
 * a los que aún les faltan los km. `puedeBorrar` = el km está guardado en dpv_km_mensual (Excel o captura manual).
 */
export function filasKm(mensual, { unidad = '', soloSinKm = false } = {}) {
  const out = []
  for (const u of UNIDADES_CARGA) {
    if (unidad && unidad !== u.key) continue
    for (const m of (mensual && mensual[u.key.toLowerCase()]) || []) {
      const sinKm = !(m.km > 0)
      if (soloSinKm && !sinKm) continue
      out.push({
        clave: `${u.key}-${m.mes}`, empresa: u.key, unidad: u.nombre, mes: m.mes, titulo: tituloMes(m.mes),
        km: sinKm ? null : m.km, kmPadron: m.km_padron ?? null, kmBuseton: m.km_buseton ?? null,
        inm: m.inm ?? null, dpv: m.dpv ?? null, nivel: m.nivel || null, origen: m.origen || 'sin_km', sinKm,
        puedeBorrar: m.origen === 'excel' || m.origen === 'manual',
      })
    }
  }
  return out.sort((a, b) => (a.mes !== b.mes ? (a.mes < b.mes ? 1 : -1) : a.empresa < b.empresa ? -1 : 1))
}

/** Meses sin km que reporta la carga del Excel, por unidad: ['EMASIVO 10: Ene 26, Feb 26, Mar 26 y 7 más', …]. */
export function resumenSinKm(sinKm, max = 4) {
  return UNIDADES_CARGA.filter(u => ((sinKm && sinKm[u.key]) || []).length)
    .map(u => `${u.nombre}: ${listaMeses(sinKm[u.key], max)}`)
}

/**
 * Frases sobre lo que el backend hizo con los eventos al cargarlos (reparó, ordenó, no cuenta). `calidad` = campo `calidad` de la
 * respuesta de POST /api/dpv/upload; `estadosDescartados` = estados que no cuentan como inmovilización (GET /api/dpv-mensual).
 */
export function avisosCalidad(calidad, estadosDescartados = []) {
  if (!calidad) return []
  const out = []
  const rep = calidad.textos_reparados || 0
  if (rep > 0) {
    out.push(rep === 1
      ? '1 texto con caracteres dañados (como «Ã³» en vez de «ó») se reparó.'
      : `${entero(rep)} textos con caracteres dañados (como «Ã³» en vez de «ó») se repararon.`)
  }
  const orden = Object.entries(calidad.normalizados || {}).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1])
  if (orden.length) {
    out.push('Se ordenó el formato (espacios, mayúsculas, tildes) en: '
      + orden.map(([c, n]) => `${CAMPO_ORDENADO[c] || c} (${entero(n)})`).join(', ') + '.')
  }
  const nc = calidad.no_cuentan_para_dpv || 0
  if (nc > 0) {
    const cuales = estadosDescartados.length ? ` («${estadosDescartados.join('», «')}»)` : ''
    out.push(`${entero(nc)} ${nc === 1 ? 'evento no cuenta' : 'eventos no cuentan'} como inmovilización para el DPV${cuales}.`)
  }
  return out
}

/**
 * Texto de un error de axios para mostrarlo: el `detail` del backend (texto, o la lista de errores de validación de FastAPI),
 * o un aviso según el caso (error HTTP sin detalle, sin conexión, o un error nuestro).
 */ 
export function mensajeError(e, porDefecto = 'No se pudo completar la operación') {
  const d = e && e.response && e.response.data && e.response.data.detail
  if (typeof d === 'string' && d.trim()) return d
  if (Array.isArray(d) && d.length) return d.map(x => (x && x.msg) || String(x)).join(' · ')
  if (e && e.response) return `${porDefecto} (error ${e.response.status}).`
  if (e && (e.request || e.isAxiosError)) return 'No hay conexión con el servidor. Revisa que el backend esté en marcha e inténtalo de nuevo.'
  return `${porDefecto}.`
}
