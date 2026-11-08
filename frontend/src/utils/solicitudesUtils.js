// ═══════════════════════════════════════════════════════════
//  solicitudesUtils.js — lógica PURA de las solicitudes al Centro de Gestión (sin Vue ni axios: se prueba con `npm test`)
//  Las claves de TIPOS son las mismas de backend/services/solicitudes.py
// ═══════════════════════════════════════════════════════════

export const MIN_MENSAJE = 10
export const MAX_MENSAJE = 600

export const TIPOS = [
  { key: 'mantenimiento',        corto: 'Novedad de mantenimiento',   hint: 'Ej: Necesito el detalle de la novedad de mantenimiento del móvil Z32-7036…' },
  { key: 'informe_detallado',    corto: 'Informes detallados',        hint: 'Ej: Necesito el informe detallado de ICO de octubre por empresa…' },
  { key: 'temperatura',          corto: 'Diagnóstico de temperatura', hint: 'Ej: Diagnóstico de temperatura de los móviles con eventos repetidos esta semana…' },
  { key: 'reporte_revision',     corto: 'Reportes y revisión',        hint: 'Ej: Necesito revisar el reporte de inmovilizados de ayer, hay datos que no cuadran…' },
  { key: 'analisis_operativo',   corto: 'Análisis operativo',         hint: 'Ej: Análisis operativo del DPV por tipología del último mes…' },
  { key: 'actualizacion_bases',  corto: 'Actualización de bases',     hint: 'Ej: Actualizar la base de DPV / ICO, la última carga no incluye el día de hoy…' },
  { key: 'moviles_contundentes', corto: 'Contestados contundentes',   hint: 'Ej: Móviles contestados contundentes y su estado actual…' },
  { key: 'programacion',         corto: 'Programación de móviles',    hint: 'Ej: Sugerencias de programación de mantenimiento para los móviles próximos al hito…' },
  { key: 'otro',                 corto: 'Otra información',           hint: 'Cuéntanos en un párrafo corto qué necesitas…' },
]

export const TIPO_POR_CLAVE = Object.fromEntries(TIPOS.map(t => [t.key, t]))

export const ESTADOS = [
  { key: 'pendiente',  label: 'Pendiente',  clase: 'pend' },
  { key: 'en_proceso', label: 'En proceso', clase: 'proc' },
  { key: 'atendida',   label: 'Atendida',   clase: 'ok' },
  { key: 'cerrada',    label: 'Cerrada',    clase: 'cerr' },
]
export const ESTADO_POR_CLAVE = Object.fromEntries(ESTADOS.map(e => [e.key, e]))

/** Quita los saltos de línea sobrantes y los espacios de los extremos (igual que el servidor). */
export function limpiar(s) {
  return String(s ?? '').replace(/\r\n?/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
}

export const restantes = mensaje => MAX_MENSAJE - limpiar(mensaje).length

const MOVIL_RE = /^[A-Z0-9][A-Z0-9 .\-/]*$/

export function normalizarMovil(m) {
  return String(m ?? '').trim().replace(/\s+/g, ' ').toUpperCase()
}

/** → { ok, errores: { tipo?, mensaje?, movil? } } con los textos que ve la persona. */
export function validarSolicitud({ tipo, mensaje, movil }) {
  const errores = {}
  if (!TIPO_POR_CLAVE[tipo]) errores.tipo = 'Elige qué tipo de información necesitas.'
  const n = limpiar(mensaje).length
  if (n < MIN_MENSAJE) errores.mensaje = `Cuéntanos un poco más (mínimo ${MIN_MENSAJE} caracteres).`
  else if (n > MAX_MENSAJE) errores.mensaje = `El mensaje es muy largo (máximo ${MAX_MENSAJE} caracteres).`
  const m = normalizarMovil(movil)
  if (m && (m.length > 30 || !MOVIL_RE.test(m))) errores.movil = 'Usa solo letras, números y guiones (ej: Z32-7036).'
  return { ok: Object.keys(errores).length === 0, errores }
}

/** '2026-11-03T20:00:00Z' → «hace 5 min», «hace 3 h», «hace 2 días», o «03/11/2026» si pasó una semana. */
export function haceCuanto(iso, ahoraMs = Date.now()) {
  const t = Date.parse(iso || '')
  if (Number.isNaN(t)) return ''
  const min = Math.max(0, Math.floor((ahoraMs - t) / 60000))
  if (min < 1) return 'hace un momento'
  if (min < 60) return `hace ${min} min`
  const h = Math.floor(min / 60)
  if (h < 24) return `hace ${h} h`
  const d = Math.floor(h / 24)
  if (d < 7) return `hace ${d} ${d === 1 ? 'día' : 'días'}`
  const f = new Date(t)
  return `${String(f.getDate()).padStart(2, '0')}/${String(f.getMonth() + 1).padStart(2, '0')}/${f.getFullYear()}`
}

/** Texto de error legible a partir de la respuesta del servidor. */
export function mensajeDeError(e, porDefecto = 'No se pudo completar la solicitud.') {
  const s = e?.response?.status
  const d = e?.response?.data?.detail
  if (s === 429) return 'Demasiados intentos. Prueba de nuevo en un rato.'
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d[0]?.msg) return d[0].msg
  if (!e?.response) return 'Sin conexión con el servidor.'
  return porDefecto
}
