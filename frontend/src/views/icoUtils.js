// icoUtils.js — Lógica pura del tablero ICO (sin Vue ni Pinia).
//
// La usa dashboardStore.js para filtrar y agrupar, y DashboardICO.vue para dibujar.
// Todo lo que sea regla de negocio o umbral está aquí arriba, para ajustarlo en un solo lugar.
//
// Modelo de interacción (igual que Power BI):
//   · SLICERS  (barra superior)  → filtros duros: Unidad, Año, Mes, Tipo de infracción, Tipología, Estado, Móvil.
//   · SELECCIÓN (clic en gráficas) → filtro cruzado: cada visual muestra TODAS sus categorías con la selección
//     resaltada, y filtra a las demás visuales, KPIs y tabla de detalle. Ctrl/⌘/Shift + clic suma elementos.

// ── Reglas de negocio ajustables ─────────────────────────────────────────────

// Respaldo local de la clasificación "Directo". La fuente de verdad es el backend
// (variable ICO_CODIGOS_DIRECTO del .env); el resto de códigos son "Hallazgo Rechazado".
export const ICO_CODIGOS_DIRECTO = ['I5006', 'I5013', 'I5022', 'I5023']
export const TIPOS_INFRACCION = ['Directo', 'Hallazgo Rechazado']

// Mapa de calor por DÍA (eventos/día): bajo 1-3 · medio 4-7 · alto 8+ (misma escala que la leyenda del DPV).
// En vistas por mes (no por día) los umbrales son relativos al mes con más eventos.
export const HEAT_DIA = { medio: 4, alto: 8 }
export const HEAT_RELATIVO = { medio: 0.4, alto: 0.7 }
// Verde de marca (--accent) · ámbar · rojo del tema (--danger). Esta terna separa bien también para daltónicos
// (protanopía ΔE 8.7). Aun así NUNCA se depende solo del color: cada barra lleva su número, tooltip y leyenda.
export const HEAT_COLORES = { vacio: '#E5E7EB', bajo: '#31b079', medio: '#F59E0B', alto: '#C0392B' }

export const COLOR_TIPOLOGIA = { PADRON: '#084534', BUSETON: '#60b566' }
export const ESTADO_PENDIENTE = 'No Contestado'   // ICO aún sin respuesta del operador

export const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
export const MESES_LARGOS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
                             'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
export const DIAS_CORTOS = ['D', 'L', 'M', 'X', 'J', 'V', 'S']   // getDay(): 0 = domingo

export const CIRC = 2 * Math.PI * 52   // circunferencia de la dona (r = 52)

// ── Helpers de texto y fecha ─────────────────────────────────────────────────

const pad2 = n => String(n).padStart(2, '0')

export function sinTildes(s) {
  return String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '')
}

export function normTipologia(t) {
  return sinTildes(t).trim().toUpperCase()
}

export function etiquetaTipologia(k) {
  return k === 'PADRON' ? 'PADRÓN' : k
}

/** UF-10 / UF-16 según la empresa (igual que el filtro EMPRESA del Power BI); si falta, por prefijo del móvil. */
export function ufDeRegistro(empresa, movil) {
  const e = String(empresa || '').toUpperCase()
  if (/\b10\b/.test(e)) return 'UF10'
  if (/\b16\b/.test(e)) return 'UF16'
  const m = String(movil || '').toUpperCase()
  if (m.startsWith('Z32')) return 'UF10'
  if (m.startsWith('Z34')) return 'UF16'
  return ''
}

export function tipoInfraccionLocal(codigo) {
  return ICO_CODIGOS_DIRECTO.includes(String(codigo || '').trim().toUpperCase()) ? 'Directo' : 'Hallazgo Rechazado'
}

/** Fecha local de hoy en 'YYYY-MM-DD'. */
export function hoyISO(d = new Date()) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

/** Días de calendario entre dos fechas 'YYYY-MM-DD' (a − b). */
export function diffDias(aISO, bISO) {
  const t = s => {
    const [y, m, d] = String(s).slice(0, 10).split('-').map(Number)
    return Date.UTC(y, m - 1, d)
  }
  return Math.round((t(aISO) - t(bISO)) / 86400000)
}

/**
 * Días que le quedan al operador para responder un ICO "No Contestado" (hasta F. CIERRE DPV, inclusive).
 * Devuelve null si el ICO ya no está pendiente, no tiene fecha de cierre o la ventana ya venció.
 */
export function diasParaResponder(r, hoy = hoyISO()) {
  if (r.estado !== ESTADO_PENDIENTE || !r.fecha_cierre) return null
  const d = diffDias(r.fecha_cierre, hoy)
  return d >= 0 ? d : null
}

// ── Dimensiones de selección cruzada ─────────────────────────────────────────

const SD = 'S/D'
export const DIM = {
  periodos:        r => r.fecha,                         // se compara por día ('YYYY-MM-DD') o mes ('YYYY-MM')
  tipologia:       r => r.tipologia || SD,
  tipo_novedad:    r => r.tipo_novedad || SD,
  tipo_infraccion: r => r.tipo_infraccion || SD,
  estado:          r => r.estado || SD,
  movil:           r => r.movil || r.placa || SD,
}

export const SELECCION_VACIA = () => ({
  periodos: [], tipologia: [], tipo_novedad: [], tipo_infraccion: [], estado: [], movil: [],
})

function coincide(dim, r, keys) {
  if (dim === 'periodos') {
    return keys.some(k => (k.length === 10 ? r.fecha === k : r.fecha.slice(0, 7) === k))
  }
  return keys.includes(DIM[dim](r))
}

// ── Filtros ──────────────────────────────────────────────────────────────────

/** Slicers: Unidad, Año/Mes (sobre F. IDENTIFICACION), Tipo de infracción, Tipología, Estado y búsqueda de móvil/placa. */
export function aplicarSlicers(rows, f) {
  const q = (f.busqueda || '').trim().toLowerCase()
  const meses = f.meses.length ? new Set(f.meses) : null
  const anio = f.anio ? String(f.anio) : ''
  return rows.filter(r => {
    if (f.uf.length && !f.uf.includes(r.uf)) return false
    if (anio) {
      if (r.fecha.slice(0, 4) !== anio) return false
      if (meses && !meses.has(parseInt(r.fecha.slice(5, 7), 10))) return false
    }
    if (f.tipo_infraccion.length && !f.tipo_infraccion.includes(r.tipo_infraccion)) return false
    if (f.tipologia.length && !f.tipologia.includes(r.tipologia)) return false
    if (f.estado && r.estado !== f.estado) return false
    if (q && !r.movil.toLowerCase().includes(q) && !r.placa.toLowerCase().includes(q)) return false
    return true
  })
}

/** Selección cruzada. `excepto` omite una dimensión (la visual propia, que debe mostrar todas sus categorías). */
export function aplicarSeleccion(rows, sel, excepto = null) {
  const activas = Object.entries(sel).filter(([dim, keys]) => dim !== excepto && keys.length)
  if (!activas.length) return rows
  return rows.filter(r => activas.every(([dim, keys]) => coincide(dim, r, keys)))
}

export function haySeleccion(sel) {
  return Object.values(sel).some(keys => keys.length > 0)
}

// ── Agrupaciones ─────────────────────────────────────────────────────────────

/** Ranking por dimensión: [{ key, label, total, puntos, pct, seleccionado }] de mayor a menor. */
export function ranking(rows, keyFn, { seleccion = [], labelFn = k => k } = {}) {
  const map = new Map()
  for (const r of rows) {
    const k = keyFn(r)
    const e = map.get(k) || { key: k, total: 0, puntos: 0 }
    e.total++
    e.puntos += r.puntos
    map.set(k, e)
  }
  const lista = [...map.values()]
  const total = lista.reduce((s, e) => s + e.total, 0) || 1
  const sel = new Set(seleccion)
  return lista
    .map(e => ({ ...e, label: labelFn(e.key), pct: Math.round((e.total / total) * 100), seleccionado: sel.has(e.key) }))
    .sort((a, b) => b.total - a.total || b.puntos - a.puntos || String(a.key).localeCompare(String(b.key), 'es'))
}

/** Dona de tipología: siempre PADRÓN y BUSETON (aunque sea 0) y el % se calcula sobre lo que muestra la dona. */
export function dona(rows, seleccion = []) {
  const lista = ranking(rows, DIM.tipologia, { seleccion, labelFn: etiquetaTipologia })
  for (const k of ['PADRON', 'BUSETON']) {
    if (!lista.some(s => s.key === k)) {
      lista.push({ key: k, label: etiquetaTipologia(k), total: 0, puntos: 0, pct: 0, seleccionado: seleccion.includes(k) })
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

// ── Mapa de calor ────────────────────────────────────────────────────────────

/** 'dia' (un solo mes elegido) · 'mes' (un año, varios o todos los meses) · 'anio-mes' (todos los años). */
export function modoHeat(f) {
  if (f.anio && f.meses.length === 1) return 'dia'
  if (f.anio) return 'mes'
  return 'anio-mes'
}

export function nivelHeat(valor, max, modo) {
  if (!valor) return 'vacio'
  if (modo === 'dia') return valor >= HEAT_DIA.alto ? 'alto' : valor >= HEAT_DIA.medio ? 'medio' : 'bajo'
  const r = valor / (max || 1)
  return r >= HEAT_RELATIVO.alto ? 'alto' : r >= HEAT_RELATIVO.medio ? 'medio' : 'bajo'
}

/**
 * Columnas del mapa de calor. `rows` debe venir SIN la selección de periodos (la visual propia).
 * Devuelve { modo, columnas:[{ key, label, sub, finDeSemana, titulo, total, puntos, nivel, color, seleccionado }], max, ticks }.
 */
export function heatmap(rows, f, seleccion = []) {
  const modo = modoHeat(f)
  const sel = new Set(seleccion)
  const acum = new Map()
  for (const r of rows) {
    if (!r.fecha) continue
    const k = modo === 'dia' ? r.fecha : r.fecha.slice(0, 7)
    const e = acum.get(k) || { total: 0, puntos: 0 }
    e.total++
    e.puntos += r.puntos
    acum.set(k, e)
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

  const max = cols.reduce((mx, c) => Math.max(mx, acum.get(c.key)?.total || 0), 0)
  const columnas = cols.map(c => {
    const e = acum.get(c.key) || { total: 0, puntos: 0 }
    const nivel = nivelHeat(e.total, max, modo)
    return { ...c, total: e.total, puntos: e.puntos, nivel, color: HEAT_COLORES[nivel], seleccionado: sel.has(c.key) }
  })
  const ticks = [...new Set([max, Math.round(max / 2), 0])]
  return { modo, columnas, max, ticks }
}

// ── Textos ───────────────────────────────────────────────────────────────────

/** 'YYYY-MM-DD' → '21 sep'; 'YYYY-MM' → 'Sep 2026'. */
export function etiquetaPeriodo(key) {
  const p = String(key).split('-').map(Number)
  if (p.length === 3) return `${p[2]} ${MESES_CORTOS[p[1] - 1].toLowerCase()}`
  return `${MESES_CORTOS[p[1] - 1]} ${p[0]}`
}

export function tituloPeriodo(f) {
  if (!f.anio) return 'Todo el histórico'
  if (!f.meses.length) return String(f.anio)
  const meses = [...f.meses].sort((a, b) => a - b)
  if (meses.length === 1) return `${MESES_LARGOS[meses[0] - 1]} ${f.anio}`
  return `${meses.map(m => MESES_CORTOS[m - 1]).join(', ')} ${f.anio}`
}

const NOMBRE_DIM = {
  periodos: 'Periodo', tipologia: 'Tipología', tipo_novedad: 'Código', tipo_infraccion: 'Infracción',
  estado: 'Estado', movil: 'Móvil',
}

/** Chips de la selección activa para mostrarlos y poder quitarlos uno a uno. */
export function chipsSeleccion(sel) {
  const out = []
  for (const [dim, keys] of Object.entries(sel)) {
    for (const key of keys) {
      const valor = dim === 'periodos' ? etiquetaPeriodo(key) : dim === 'tipologia' ? etiquetaTipologia(key) : key
      out.push({ dim, key, texto: `${NOMBRE_DIM[dim]}: ${valor}` })
    }
  }
  return out
}

// ── Tabla de detalle ─────────────────────────────────────────────────────────

/** Ordena sin mutar; los vacíos van siempre al final. `dias` ordena por días para responder. */
export function ordenar(rows, key, dir = 'desc', hoy = hoyISO()) {
  const val = key === 'dias' ? r => diasParaResponder(r, hoy) : r => r[key]
  const signo = dir === 'asc' ? 1 : -1
  // 0 puntos = sin puntos asignados (vacío); 0 días = "vence hoy" (el más urgente, NO es vacío)
  const vacio = v => v == null || v === '' || (key === 'puntos' && v === 0)
  return [...rows].sort((a, b) => {
    const va = val(a)
    const vb = val(b)
    const ea = vacio(va)
    const eb = vacio(vb)
    if (ea && eb) return 0
    if (ea) return 1
    if (eb) return -1
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * signo
    return String(va).localeCompare(String(vb), 'es', { numeric: true }) * signo
  })
}

/** CSV (separado por comas, comillas escapadas) con las columnas de la tabla de detalle. */
export function csvICO(rows) {
  const cab = ['ICO', 'Móvil', 'Placa', 'Código', 'Tipo de infracción', 'Puntos', 'Estado', 'F. identificación',
               'F. notificación', 'F. cierre DPV', 'Empresa', 'Tipología', 'Dirección', 'Descripción']
  const esc = v => {
    const s = v == null ? '' : String(v)
    return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const filas = rows.map(r => [
    r.ico_id, r.movil, r.placa, r.tipo_novedad, r.tipo_infraccion, r.puntos || '', r.estado, r.fecha,
    r.fecha_notificacion, r.fecha_cierre, r.empresa, r.tipologia, r.direccion, r.descripcion,
  ])
  return [cab, ...filas].map(f => f.map(esc).join(',')).join('\r\n')
}