// Lógica pura de la pestaña «Disponibilidad» interactiva (sin Vue ni red: se prueba sola con node --test).
// Modelo: cada bus no disponible es una fila; las visuales filtran entre sí (selección cruzada, estilo Power BI).

export const UNIDADES = [
  { key: 'UF10', label: 'UF-10', sub: 'EMASIVO10', color: '#074e7a', campo: 'e10' },
  { key: 'UF16', label: 'UF-16', sub: 'EMASIVO16', color: '#248a7c', campo: 'e16' },
]

// Áreas que escribe el bot automático; cualquier otra área viene del Excel de mantenimiento
export const AREA_PATIO = 'No salió de patio'
export const AREA_APAGADO = 'Apagado / sin reporte'

export const MOTIVOS = [
  { key: 'taller',  label: 'En taller',            sub: 'Mantenimiento (Excel de inmovilizados)', color: '#C0392B' },
  { key: 'patio',   label: 'No salió de patio',    sub: 'Menos de 7 km recorridos',               color: '#F59E0B' },
  { key: 'apagado', label: 'Apagado / sin reporte', sub: 'P60 sin reporte de hoy',                 color: '#64748b' },
]

export const BUCKETS = [
  { key: 'b0', label: '< 3 días',    min: 0,  max: 3 },
  { key: 'b1', label: '3 – 9 días',  min: 3,  max: 10 },
  { key: 'b2', label: '10 – 29 días', min: 10, max: 30 },
  { key: 'b3', label: '30 – 89 días', min: 30, max: 90 },
  { key: 'b4', label: '90+ días',    min: 90, max: Infinity },
]

export const NOMBRE_DIM = { unidad: 'Unidad', motivo: 'Motivo', area: 'Causa / área', bucket: 'Antigüedad', movil: 'Móvil' }
export const SELECCION_VACIA = () => ({ unidad: [], motivo: [], area: [], bucket: [], movil: [] })

const SIN_AREA = 'Sin área'

export function motivoDeArea(area) {
  if (area === AREA_PATIO) return 'patio'
  if (area === AREA_APAGADO) return 'apagado'
  return 'taller'
}

export function bucketDe(dias) {
  const d = Number(dias) || 0
  return (BUCKETS.find(b => d >= b.min && d < b.max) || BUCKETS[0]).key
}

/** 'Z32-7073 INMOVILIZADO' → { placa: 'Z32-7073', inmov: true }. Si no hay placa reconocible deja el texto tal cual. */
export function limpiarMovil(raw) {
  const txt = String(raw ?? '').trim()
  const m = txt.match(/Z3[24]\s*-?\s*\d{3,5}/i)
  let placa = txt
  if (m) {
    placa = m[0].replace(/\s+/g, '').toUpperCase()
    if (!placa.includes('-')) placa = placa.slice(0, 3) + '-' + placa.slice(3)
  }
  return { placa, inmov: /inmoviliz/i.test(txt) }
}

/** Respuesta de /api/disponibilidad (store.disponibilidad) → { filas, flotas: {UF10:{...}}, cortes }. */
export function normalizar(disp) {
  const filas = []
  const unidades = {}
  for (const u of UNIDADES) {
    const d = disp && disp[u.campo]
    if (!d) continue
    unidades[u.key] = { ...u, flota: d.flota_total, noDisp: d.no_disponibles, disponibles: d.disponibles, porcentaje: d.porcentaje, corte: d.fecha_corte }
    for (const r of d.detalle || []) {
      const { placa, inmov } = limpiarMovil(r.movil)
      const area = (r.area || '').trim() || SIN_AREA
      const dias = Number(r.dias_inoperatividad) || 0
      filas.push({
        unidad: u.key, movil: placa, movilOriginal: r.movil, area, descripcion: String(r.descripcion || '').replace(/^\[AUTO\]\s*/, ''),
        dias, bucket: bucketDe(dias), motivo: motivoDeArea(area), inmovilizado: !!r.inmovilizado || inmov, fechaIngreso: r.fecha_ingreso || null,
      })
    }
  }
  return { filas, unidades }
}

// ── Filtros ──────────────────────────────────────────────────────────────────

export const DIM = {
  unidad: r => r.unidad, motivo: r => r.motivo, area: r => r.area, bucket: r => r.bucket, movil: r => r.movil,
}

/** Búsqueda libre (slicer): móvil, área o descripción. */
export function aplicarBusqueda(rows, q) {
  const t = (q || '').trim().toLowerCase()
  if (!t) return rows
  return rows.filter(r => r.movil.toLowerCase().includes(t) || r.area.toLowerCase().includes(t) || r.descripcion.toLowerCase().includes(t))
}

/** Selección cruzada. `excepto` omite una dimensión (la visual propia sigue mostrando todas sus categorías). */
export function aplicarSeleccion(rows, sel, excepto = null) {
  const activas = Object.entries(sel).filter(([dim, keys]) => dim !== excepto && keys.length)
  if (!activas.length) return rows
  return rows.filter(r => activas.every(([dim, keys]) => keys.includes(DIM[dim](r))))
}

export function haySeleccion(sel) {
  return Object.values(sel).some(k => k.length > 0)
}

/** Clic simple: reemplaza (o quita si era la única). Ctrl/⌘/Shift: suma o quita. Devuelve una selección nueva (no muta). */
export function alternarSeleccion(sel, dim, key, aditivo = false) {
  const actual = sel[dim] || []
  let nuevo
  if (aditivo) nuevo = actual.includes(key) ? actual.filter(k => k !== key) : [...actual, key]
  else nuevo = actual.length === 1 && actual[0] === key ? [] : [key]
  return { ...sel, [dim]: nuevo }
}

export function quitarSeleccion(sel, dim, key) {
  return { ...sel, [dim]: (sel[dim] || []).filter(k => k !== key) }
}

export function chipsSeleccion(sel) {
  const out = []
  for (const [dim, keys] of Object.entries(sel)) {
    for (const key of keys) {
      const texto = dim === 'motivo' ? (MOTIVOS.find(m => m.key === key) || {}).label
        : dim === 'bucket' ? (BUCKETS.find(b => b.key === key) || {}).label
        : dim === 'unidad' ? (UNIDADES.find(u => u.key === key) || {}).label : key
      out.push({ dim, key, texto: `${NOMBRE_DIM[dim]}: ${texto || key}` })
    }
  }
  return out
}

// ── Agrupaciones ─────────────────────────────────────────────────────────────

/** Cuenta por dimensión con el orden/etiquetas dados (incluye categorías con 0). → [{key,label,total,pct,seleccionado,...extra}] */
export function contar(rows, keyFn, categorias, seleccion = []) {
  const m = new Map(categorias.map(c => [c.key, 0]))
  for (const r of rows) { const k = keyFn(r); m.set(k, (m.get(k) || 0) + 1) }
  const total = rows.length || 1
  const sel = new Set(seleccion)
  const conocidas = new Set(categorias.map(c => c.key))
  const lista = categorias.map(c => ({ ...c, total: m.get(c.key) || 0 }))
  for (const [k, n] of m) if (!conocidas.has(k)) lista.push({ key: k, label: k, total: n })
  return lista.map(c => ({ ...c, pct: Math.round((c.total / total) * 100), seleccionado: sel.has(c.key) }))
}

/** Ranking de causas (áreas): de mayor a menor, solo las que tienen buses. */
export function rankingAreas(rows, seleccion = []) {
  const m = new Map()
  for (const r of rows) {
    const e = m.get(r.area) || { key: r.area, label: r.area, total: 0, motivo: r.motivo, dias: 0 }
    e.total++; e.dias += r.dias
    m.set(r.area, e)
  }
  const sel = new Set(seleccion)
  const total = rows.length || 1
  return [...m.values()]
    .map(e => ({ ...e, pct: Math.round((e.total / total) * 100), promedio: e.total ? Math.round((e.dias / e.total) * 10) / 10 : 0, seleccionado: sel.has(e.key) }))
    .sort((a, b) => b.total - a.total || a.label.localeCompare(b.label, 'es'))
}

/** KPIs. Flota y disponibles dependen SOLO de las unidades elegidas (no de otras visuales); «no disponibles» sí sigue toda la selección. */
export function kpis(todas, filtradas, unidades, selUnidad = []) {
  const keys = selUnidad.length ? selUnidad : Object.keys(unidades)
  let flota = 0, noDispReal = 0, hayFlota = false
  for (const k of keys) {
    const u = unidades[k]
    if (!u) continue
    if (u.flota) { flota += u.flota; hayFlota = true }
    noDispReal += todas.filter(r => r.unidad === k).length
  }
  const disponibles = hayFlota ? Math.max(0, flota - noDispReal) : null
  const dias = filtradas.reduce((s, r) => s + r.dias, 0)
  return {
    flota: hayFlota ? flota : null,
    noDispReal,
    noDisp: filtradas.length,
    disponibles,
    porcentaje: hayFlota && flota ? Math.round((disponibles / flota) * 1000) / 10 : null,
    promedioDias: filtradas.length ? Math.round((dias / filtradas.length) * 10) / 10 : 0,
    maxDias: filtradas.reduce((m, r) => Math.max(m, r.dias), 0),
  }
}

export function claseSemaforo(p) {
  if (p == null) return ''
  return p >= 90 ? 'ok' : p >= 75 ? 'warn' : 'bad'
}

export function claseDias(d) {
  return d >= 10 ? 'dias-bad' : d >= 3 ? 'dias-warn' : 'dias-ok'
}

// ── Tabla ────────────────────────────────────────────────────────────────────

export function ordenar(rows, key, dir = 'desc') {
  const signo = dir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const va = a[key], vb = b[key]
    const ea = va == null || va === '', eb = vb == null || vb === ''
    if (ea && eb) return 0
    if (ea) return 1
    if (eb) return -1
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * signo
    return String(va).localeCompare(String(vb), 'es', { numeric: true }) * signo
  })
}

export function csvDisponibilidad(rows) {
  const cab = ['Unidad', 'Móvil', 'Motivo', 'Área / causa', 'Descripción', 'Días', 'Inmovilizado', 'Fecha de ingreso']
  const esc = v => { const s = v == null ? '' : String(v); return /[",\r\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s }
  const lab = k => (MOTIVOS.find(m => m.key === k) || {}).label || k
  const filas = rows.map(r => [UNIDADES.find(u => u.key === r.unidad)?.label || r.unidad, r.movil, lab(r.motivo), r.area, r.descripcion, r.dias, r.inmovilizado ? 'Sí' : 'No', r.fechaIngreso || ''])
  return [cab, ...filas].map(f => f.map(esc).join(',')).join('\r\n')
}

/** Dona de una unidad: disponibles (color de la unidad) vs no disponibles. r = 52 como el resto de donas del tablero. */
export const CIRC = 2 * Math.PI * 52
export function donaUnidad(u) {
  if (!u || !u.flota) return { dash: 0, gap: CIRC }
  const dash = Math.min(1, Math.max(0, u.disponibles / u.flota)) * CIRC
  return { dash, gap: CIRC - dash }
}
