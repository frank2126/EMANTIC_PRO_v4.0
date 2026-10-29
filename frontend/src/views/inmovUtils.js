// ═══════════════════════════════════════════════════════════
//  inmovUtils.js — lógica PURA de la pestaña Inmovilizados (sin Vue ni axios: se prueba con `npm test`)
//
//  Fuente: /api/inmovilizados. Cada evento trae estado = 'inmovilizado' | 'habilitado' | 'sin_confirmar'
//  (lo decide el backend con el último archivo cargado de su unidad) y `horas` (solo si ya fue habilitado).
//  Las fechas de los eventos vienen como 'YYYY-MM-DDTHH:MM:SS' en hora local de Bogotá (así las trae el reporte);
//  las horas de los cortes vienen en UTC con «Z».
// ═══════════════════════════════════════════════════════════

export const UNIDADES = [
  { key: 'E10', nombre: 'UF-10' },
  { key: 'E16', nombre: 'UF-16' },
]

export const ESTADO = { INMOVILIZADO: 'inmovilizado', HABILITADO: 'habilitado', SIN_CONFIRMAR: 'sin_confirmar' }

// La información se espera cada hora: hasta 90 min está «al día»; hasta 3 h «atrasada»; después «desactualizada»
export const MIN_AL_DIA = 90
export const MIN_ATRASADO = 180

const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// ── Fechas ─────────────────────────────────────────────────

/** 'YYYY-MM-DDTHH:MM:SS' (sin zona) → milisegundos en hora local. null si no es válida. */
export function msDeFecha(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?$/.exec(String(s || ''))
  if (!m) return null
  return new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0), +(m[6] || 0)).getTime()
}

export const mesDe = s => (/^\d{4}-\d{2}/.test(String(s || '')) ? String(s).slice(0, 7) : '')

export function tituloMes(mes) {
  const m = /^(\d{4})-(\d{2})$/.exec(mes || '')
  return m ? `${MESES[+m[2] - 1] || m[2]} ${m[1]}` : ''
}

/** 'YYYY-MM-DDTHH:MM:SS' → '05/03 08:15' (con año si no es el actual) */
export function fmtFechaHora(s, anioActual = new Date().getFullYear()) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(String(s || ''))
  if (!m) return '—'
  const dia = `${m[3]}/${m[2]}${+m[1] === anioActual ? '' : '/' + m[1]}`
  return m[4] ? `${dia} ${m[4]}:${m[5]}` : dia
}

/** 3.5 → '3 h 30 min' · 0.25 → '15 min' · 52 → '2 d 4 h' · null → '—' */
export function fmtHoras(h) {
  if (h === null || h === undefined || Number.isNaN(h) || h < 0) return '—'
  const min = Math.round(h * 60)
  if (min < 60) return `${min} min`
  if (min < 48 * 60) {
    const hh = Math.floor(min / 60), mm = min % 60
    return mm ? `${hh} h ${mm} min` : `${hh} h`
  }
  const d = Math.floor(min / 1440), hh = Math.round((min % 1440) / 60)
  return hh ? `${d} d ${hh} h` : `${d} d`
}

// ── Frescura de la información (qué tan al día está cada unidad) ──

/**
 * `corte` = { tipo, creado:'…Z' } del último corte (carga o «sin novedades») de la unidad.
 * → { nivel: 'al_dia'|'atrasado'|'vencido'|'sin_datos', minutos, texto }
 */
export function frescura(corte, ahoraMs = Date.now()) {
  const t = corte && corte.creado ? Date.parse(corte.creado) : NaN
  if (Number.isNaN(t)) return { nivel: 'sin_datos', minutos: null, texto: 'Sin cargas' }
  const minutos = Math.max(0, Math.floor((ahoraMs - t) / 60000))
  const nivel = minutos <= MIN_AL_DIA ? 'al_dia' : minutos <= MIN_ATRASADO ? 'atrasado' : 'vencido'
  const texto = minutos < 1 ? 'hace un momento' : minutos < 60 ? `hace ${minutos} min` : `hace ${fmtHoras(minutos / 60)}`
  return { nivel, minutos, texto }
}

// ── Preparación de filas ───────────────────────────────────

/** Evento del backend → fila del tablero (con `mes` de la inmovilización y marcas de tiempo en ms). */
export function normInmov(r) {
  return {
    id: r.id,
    unidad: r.unidad || '',
    placa: r.placa || '',
    movil: r.movil || '',
    claveMovil: r.movil || r.placa || '',        // un móvil sin número se agrupa por su placa
    causa: r.causa || '',
    descripcion: r.descripcion || '',
    descripcionRevision: r.descripcion_revision || '',
    creador: r.creador || '',
    revisor: r.revisor || '',
    habilitador: r.habilitador || '',
    fechaInm: r.fecha_inmovilizacion || '',
    fechaRev: r.fecha_revision || '',
    fechaHab: r.fecha_habilitacion || '',
    msInm: msDeFecha(r.fecha_inmovilizacion),
    msHab: msDeFecha(r.fecha_habilitacion),
    mes: mesDe(r.fecha_inmovilizacion),
    estado: r.estado || ESTADO.INMOVILIZADO,
    horas: typeof r.horas === 'number' ? r.horas : null,
  }
}

/** Horas que lleva (o duró) la inmovilización: las ya habilitadas usan su duración; las abiertas, el reloj. */
export function horasDe(e, ahoraMs = Date.now()) {
  if (e.estado === ESTADO.HABILITADO) return e.horas
  if (e.msInm === null) return null
  return Math.max(0, (ahoraMs - e.msInm) / 3600000)
}

const porUnidad = (items, unidad) => (unidad ? items.filter(e => e.unidad === unidad) : items)
const mayorHorasPrimero = ahoraMs => (a, b) => (horasDe(b, ahoraMs) ?? -1) - (horasDe(a, ahoraMs) ?? -1)

// ── Vista «Ahora» ──────────────────────────────────────────

/**
 * Foto vigente: móviles inmovilizados ahora (el más antiguo primero), los «sin confirmar» (ya no salen en el último
 * archivo pero sin fecha de habilitación) y lo habilitado en las últimas `horasRecientes` horas.
 */
export function vistaAhora(items, { unidad = '', ahoraMs = Date.now(), horasRecientes = 24 } = {}) {
  const base = porUnidad(items, unidad)
  const abiertos = base.filter(e => e.estado === ESTADO.INMOVILIZADO).sort(mayorHorasPrimero(ahoraMs))
  const sinConfirmar = base.filter(e => e.estado === ESTADO.SIN_CONFIRMAR).sort(mayorHorasPrimero(ahoraMs))
  const limite = ahoraMs - horasRecientes * 3600000
  const recientes = base
    .filter(e => e.estado === ESTADO.HABILITADO && e.msHab !== null && e.msHab >= limite)
    .sort((a, b) => b.msHab - a.msHab)
  const horas = abiertos.map(e => horasDe(e, ahoraMs)).filter(h => h !== null)
  return {
    abiertos, sinConfirmar, recientes,
    kpis: {
      inmovilizados: abiertos.length,
      sinConfirmar: sinConfirmar.length,
      habilitadosRecientes: recientes.length,
      mayorHoras: horas.length ? Math.max(...horas) : null,
      masDeUnDia: horas.filter(h => h >= 24).length,
    },
  }
}

// ── Vista mensual ──────────────────────────────────────────

/** Meses con eventos (del más reciente al más antiguo). */
export function mesesDisponibles(items) {
  return [...new Set(items.map(e => e.mes).filter(Boolean))].sort().reverse()
}

/** Estado del móvil en el mes: pendiente si algún evento sigue abierto (inmovilizado o sin confirmar), si no habilitado. */
function estadoMovil(eventos) {
  if (eventos.some(e => e.estado === ESTADO.INMOVILIZADO)) return ESTADO.INMOVILIZADO
  if (eventos.some(e => e.estado === ESTADO.SIN_CONFIRMAR)) return ESTADO.SIN_CONFIRMAR
  return ESTADO.HABILITADO
}

/**
 * Resumen del mes `mes` ('YYYY-MM') por móvil. Entran los eventos inmovilizados en el mes y, como «arrastrados», los de
 * meses anteriores que siguen sin habilitar (el área de mantenimiento todavía los tiene por intervenir).
 * Cada móvil: { clave, movil, placa, unidad, eventos[], n, estado, arrastrado, ultimaInm, ultimaHab, horasTotal, causas[] }
 */
export function vistaMensual(items, mes, { unidad = '', ahoraMs = Date.now() } = {}) {
  const base = porUnidad(items, unidad)
  const delMes = base.filter(e => e.mes === mes)
  const arrastrados = base.filter(e => e.mes && e.mes < mes && e.estado !== ESTADO.HABILITADO)
  const grupos = new Map()
  for (const e of [...delMes, ...arrastrados]) {
    const k = `${e.unidad}|${e.claveMovil}`
    if (!grupos.has(k)) grupos.set(k, [])
    grupos.get(k).push(e)
  }
  const moviles = [...grupos.entries()].map(([clave, eventos]) => {
    eventos.sort((a, b) => (b.msInm ?? 0) - (a.msInm ?? 0))
    const ult = eventos[0]
    const habs = eventos.filter(e => e.msHab !== null).map(e => e.msHab)
    const horas = eventos.map(e => horasDe(e, ahoraMs)).filter(h => h !== null)
    return {
      clave, movil: ult.movil, placa: ult.placa, unidad: ult.unidad, eventos,
      n: eventos.length,
      estado: estadoMovil(eventos),
      arrastrado: eventos.every(e => e.mes < mes),
      ultimaInm: ult.fechaInm,
      ultimaHab: habs.length ? eventos.find(e => e.msHab === Math.max(...habs)).fechaHab : '',
      horasTotal: horas.length ? horas.reduce((a, b) => a + b, 0) : null,
      causas: [...new Set(eventos.map(e => e.causa).filter(Boolean))],
    }
  })
  // Pendientes primero (los que llevan más tiempo arriba), luego habilitados (los más recientes arriba)
  const orden = { [ESTADO.INMOVILIZADO]: 0, [ESTADO.SIN_CONFIRMAR]: 1, [ESTADO.HABILITADO]: 2 }
  moviles.sort((a, b) => (orden[a.estado] - orden[b.estado]) || String(a.ultimaInm).localeCompare(String(b.ultimaInm)) * (a.estado === ESTADO.HABILITADO ? -1 : 1))

  const eventosMes = delMes
  const habilitadosMes = eventosMes.filter(e => e.estado === ESTADO.HABILITADO)
  const dur = habilitadosMes.map(e => e.horas).filter(h => h !== null)
  const cuenta = est => moviles.filter(m => m.estado === est).length
  const habil = cuenta(ESTADO.HABILITADO)
  return {
    mes, titulo: tituloMes(mes), moviles,
    kpis: {
      eventos: eventosMes.length,
      moviles: moviles.length,
      habilitados: habil,
      pendientes: cuenta(ESTADO.INMOVILIZADO),
      sinConfirmar: cuenta(ESTADO.SIN_CONFIRMAR),
      arrastrados: moviles.filter(m => m.arrastrado).length,
      pctHabilitados: moviles.length ? Math.round((habil / moviles.length) * 1000) / 10 : null,
      horasPromedio: dur.length ? dur.reduce((a, b) => a + b, 0) / dur.length : null,
      reincidentes: moviles.filter(m => m.eventos.filter(e => e.mes === mes).length > 1).length,
    },
    causas: topCausas(eventosMes),
  }
}

/** [{ causa, total }] de mayor a menor (máx. `max`). */
export function topCausas(eventos, max = 6) {
  const c = new Map()
  for (const e of eventos) if (e.causa) c.set(e.causa, (c.get(e.causa) || 0) + 1)
  return [...c.entries()].map(([causa, total]) => ({ causa, total })).sort((a, b) => b.total - a.total).slice(0, max)
}

/** Filtro de la tabla mensual: estado ('' | 'pendiente' | 'habilitado') y texto (móvil, placa o causa). */
export function filtrarMoviles(moviles, { estado = '', texto = '' } = {}) {
  const q = String(texto || '').trim().toLowerCase()
  return moviles.filter(m => {
    if (estado === 'pendiente' && m.estado === ESTADO.HABILITADO) return false
    if (estado === 'habilitado' && m.estado !== ESTADO.HABILITADO) return false
    if (!q) return true
    return `${m.movil} ${m.placa} ${m.causas.join(' ')}`.toLowerCase().includes(q)
  })
}

/** Mes inicial del selector: el actual si tiene eventos; si no, el más reciente con eventos. */
export function mesInicial(meses, hoy = new Date()) {
  const actual = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`
  return meses.includes(actual) ? actual : (meses[0] || actual)
}

/** Mensaje de error legible a partir de un error de axios. */
export function mensajeError(e, porDefecto = 'No se pudo completar la operación') {
  const d = e && e.response && e.response.data && e.response.data.detail
  if (typeof d === 'string' && d) return d
  if (Array.isArray(d) && d.length) return d.map(x => x.msg || String(x)).join('; ')
  return (e && e.message) || porDefecto
}
