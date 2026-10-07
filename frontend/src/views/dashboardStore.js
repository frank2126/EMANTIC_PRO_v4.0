// dashboardStore.js — VERSION DEFINITIVA CORREGIDA + DPV MENSUAL
import { defineStore } from 'pinia'
import axios from 'axios'

function normDPV(r) {
  return {
    id:                   r.id,
    dpv_id:               r.dpv_id,
    estado:               r.estado || '',
    empresa:              (r.empresa || '').trim(),
    placa:                (r.placa  || '').trim(),
    movil:                (r.movil  || '').trim(),
    causa_inmovilizacion: (r.causa  || r.causa_inmovilizacion || '').trim(),
    descripcion:          (r.descripcion || '').trim(),
    fecha:                (r.fecha || r.fecha_inmovilizacion || '').slice(0, 10),
    hora:                 (r.hora  || '').slice(0, 8),
    tipologia:            (r.tipologia || '').trim().toUpperCase(),
    ruta:                 (r.ruta  || '').trim(),
    dia_semana:           (r.dia_semana || '').trim(),
    alerta:               r.alerta || '',
    franja:               (r.franja || r.franja_horaria || '')
                            .replace(/\u00a0/g, '')
                            .replace(/\s/g, '')
                            .replace(/\./g, '')
                            .toUpperCase()
                            .trim(),
  }
}

function normICO(r) {
  return {
    id:           r.id,
    ico_id:       r.ico_id,
    estado:       (r.estado || '').trim(),
    empresa:      (r.empresa || '').trim(),
    placa:        (r.placa  || '').trim(),
    movil:        (r.movil  || '').trim(),
    tipo_novedad: (r.tipo_novedad || '').trim(),
    fecha_novedad:(r.fecha_novedad || '').slice(0, 10),
    hora:         (r.hora || '').slice(0, 8),
    tipologia:    (r.tipologia || '').trim().toUpperCase(),
    puntos:       parseInt(r.puntos) || 0,
    descripcion:  (r.descripcion || '').trim(),
    area:         (r.area || '').trim(),
  }
}

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dpvRaw:  [],
    icoRaw:  [],
    loading: false,
    error:   null,
    lastSync: null,

    // en state():
disponibilidad: { e10: null, e16: null },

// en actions:
async cargarDisponibilidad() {
  try {
    const { data } = await axios.get('/api/disponibilidad')
    this.disponibilidad.e10 = data?.e10 || null
    this.disponibilidad.e16 = data?.e16 || null
  } catch (e) {
    console.error('[Store] Error cargando disponibilidad:', e)
  }
},

    // ── DPV Mensual por Kilometraje ──────────────────────────
    dpvMensual: {
      e10: [],   // [{ mes, mes_label, dpv, estandar, critico, varados, kms, padron, buseton }]
      e16: [],
    },

    dpvFiltros: {
      franja:    [],
      mes:       '',   // formato 'YYYY-MM', ej: '2026-07'
      tipologia: [],
      uf:        [],
    },

    icoFiltros: {
      fecha_desde:  '',
      fecha_hasta:  '',
      empresa:      '',
      tipo_novedad: '',
      estado:       '',
      busqueda:     '',
    },
  }),

  getters: {

      dpvFiltrado(state) {
      return state.dpvRaw.filter(r => {
      if (state.dpvFiltros.mes && r.fecha.slice(0, 7) !== state.dpvFiltros.mes) return false

    if (state.dpvFiltros.franja.length > 0) {
          const f = r.franja
          const okAM = state.dpvFiltros.franja.includes('AM') && f === 'AM'
          const okPM = state.dpvFiltros.franja.includes('PM') && f === 'PM'
          if (!okAM && !okPM) return false
        }

        if (state.dpvFiltros.tipologia.length > 0) {
          const t = r.tipologia
          const match = state.dpvFiltros.tipologia.some(tp => t.includes(tp))
          if (!match) return false
        }

        if (state.dpvFiltros.uf.length > 0) {
          const m = (r.movil || '').toUpperCase()
          const esZ32 = m.startsWith('Z32')
          const esZ34 = m.startsWith('Z34')
          const okUF10 = state.dpvFiltros.uf.includes('UF10') && esZ32
          const okUF16 = state.dpvFiltros.uf.includes('UF16') && esZ34
          if (!okUF10 && !okUF16) return false
        }

        return true
      })
    },

    dpvPorcentaje(state) {
      if (!state.dpvRaw.length) return 0
      return Math.round((this.dpvFiltrado.length / state.dpvRaw.length) * 100)
    },

    dpvDona() {
      const counts = { PADRÓN: 0, BUSETON: 0 }
      this.dpvFiltrado.forEach(r => {
        if (r.tipologia.includes('PAD')) counts['PADRÓN']++
        else counts['BUSETON']++
      })
      const total = this.dpvFiltrado.length || 1
      const CIRC  = 2 * Math.PI * 52
      let offset  = 0
      return [
        { label: 'PADRÓN',  color: '#084534', total: counts['PADRÓN'] },
        { label: 'BUSETON', color: '#31b079', total: counts['BUSETON'] },
      ].map(seg => {
        const dash = (seg.total / total) * CIRC
        const out  = { ...seg, pct: Math.round(seg.total/total*100), dash, gap: CIRC-dash, offset }
        offset += dash
        return out
      })
    },

    dpvHeatmapDias() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        if (r.fecha) {
          map[r.fecha] = (map[r.fecha] || 0) + 1
        }
      })
      return Object.entries(map)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([fecha, total]) => ({
          fecha,
          dia: fecha.slice(8, 10),
          total,
        }))
    },

    dpvHeatmap() {
      const arr = Array(24).fill(0)
      this.dpvFiltrado.forEach(r => {
        if (r.hora) {
          const h = parseInt(r.hora.split(':')[0], 10)
          if (!isNaN(h) && h >= 0 && h < 24) arr[h]++
        }
      })
      return arr
    },

    dpvCausas() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        const v = r.causa_inmovilizacion || 'SIN ESPECIFICAR'
        if (v) map[v] = (map[v] || 0) + 1
      })
      return Object.entries(map)
        .map(([k, total]) => ({ causa_inmovilizacion: k, total }))
        .sort((a, b) => b.total - a.total)
    },

    dpvCausaMovil() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        const movil = r.movil || 'S/M'
        const causa = r.causa_inmovilizacion || 'S/C'
        const key   = `${movil}|||${causa}`
        map[key]    = (map[key] || 0) + 1
      })
      return Object.entries(map)
        .map(([k, total]) => {
          const [movil, causa] = k.split('|||')
          return { movil, causa, total }
        })
        .sort((a, b) => b.total - a.total)
    },

    dpvOperadores() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        const v = String(r.operador || 'DESCONOCIDO').trim()
        if (v) map[v] = (map[v] || 0) + 1
      })
      return Object.entries(map)
        .map(([k, total]) => ({ operador: k, total }))
        .sort((a, b) => b.total - a.total)
    },

    dpvRutas() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        const v = r.ruta || 'S/R'
        if (v) map[v] = (map[v] || 0) + 1
      })
      return Object.entries(map)
        .map(([k, total]) => ({ ruta: k, total }))
        .sort((a, b) => b.total - a.total)
    },

    dpvMoviles() {
      const map = {}
      this.dpvFiltrado.forEach(r => {
        const v = r.movil || 'S/M'
        if (v) map[v] = (map[v] || 0) + 1
      })
      return Object.entries(map)
        .map(([k, total]) => ({ movil: k, total }))
        .sort((a, b) => b.total - a.total)
    },

    icoFiltrado(state) {
      return state.icoRaw.filter(r => {
        if (state.icoFiltros.fecha_desde && r.fecha_novedad < state.icoFiltros.fecha_desde) return false
        if (state.icoFiltros.fecha_hasta && r.fecha_novedad > state.icoFiltros.fecha_hasta) return false
        if (state.icoFiltros.empresa      && r.empresa      !== state.icoFiltros.empresa)      return false
        if (state.icoFiltros.tipo_novedad && r.tipo_novedad !== state.icoFiltros.tipo_novedad) return false
        if (state.icoFiltros.estado       && r.estado       !== state.icoFiltros.estado)       return false
        if (state.icoFiltros.busqueda) {
          const q = state.icoFiltros.busqueda.toLowerCase()
          if (!r.movil.toLowerCase().includes(q) && !r.placa.toLowerCase().includes(q)) return false
        }
        return true
      })
    },

    icoKPIs() {
      const data = this.icoFiltrado
      return {
        total:     data.length,
        puntos:    data.reduce((s, r) => s + r.puntos, 0),
        tipos:     new Set(data.map(r => r.tipo_novedad).filter(Boolean)).size,
        placas:    new Set(data.map(r => r.movil || r.placa).filter(Boolean)).size,
        aceptados: data.filter(r => r.estado.toLowerCase().includes('acept')).length,
      }
    },

    icoDona() {
      const counts = { PADRÓN: 0, BUSETON: 0 }
      this.icoFiltrado.forEach(r => {
        if (r.tipologia.includes('PAD')) counts['PADRÓN']++
        else counts['BUSETON']++
      })
      const total = this.icoFiltrado.length || 1
      const CIRC  = 2 * Math.PI * 52
      let offset  = 0
      return [
        { label: 'PADRÓN',  color: '#084534', total: counts['PADRÓN'] },
        { label: 'BUSETON', color: '#60b566', total: counts['BUSETON'] },
      ].map(seg => {
        const dash = (seg.total / total) * CIRC
        const out  = { ...seg, pct: Math.round(seg.total/total*100), dash, gap: CIRC-dash, offset }
        offset += dash
        return out
      })
    },

    icoHeatmap() {
      const arr = Array(24).fill(0)
      this.icoFiltrado.forEach(r => {
        if (r.hora) {
          const h = parseInt(r.hora.split(':')[0], 10)
          if (!isNaN(h) && h >= 0 && h < 24) arr[h]++
        }
      })
      return arr
    },

    icoTipoNovedad() {
      const map = {}
      this.icoFiltrado.forEach(r => { const v=r.tipo_novedad||'S/D'; map[v]=(map[v]||0)+1 })
      return Object.entries(map).map(([k,total])=>({tipo_novedad:k,total})).sort((a,b)=>b.total-a.total)
    },

    icoTipoInfraccion() {
      const map = {}
      this.icoFiltrado.forEach(r => { const v=r.estado||'S/D'; map[v]=(map[v]||0)+1 })
      return Object.entries(map).map(([k,total])=>({estado:k,total})).sort((a,b)=>b.total-a.total)
    },

    icoTopPlacas() {
      const map = {}
      this.icoFiltrado.forEach(r => { const v=r.movil||r.placa||'S/M'; map[v]=(map[v]||0)+1 })
      return Object.entries(map).map(([k,total])=>({placa:k,total})).sort((a,b)=>b.total-a.total)
    },

    icoOpciones(state) {
      return {
        empresas: [...new Set(state.icoRaw.map(r=>r.empresa).filter(Boolean))].sort(),
        tipos:    [...new Set(state.icoRaw.map(r=>r.tipo_novedad).filter(Boolean))].sort(),
        estados:  [...new Set(state.icoRaw.map(r=>r.estado).filter(Boolean))].sort(),
      }
    },
  },

  actions: {
    toggleFranjaDPV(f) {
      const idx = this.dpvFiltros.franja.indexOf(f)
      if (idx > -1) this.dpvFiltros.franja.splice(idx, 1)
      else          this.dpvFiltros.franja.push(f)
    },

    toggleTipoDPV(t) {
      const idx = this.dpvFiltros.tipologia.indexOf(t)
      if (idx > -1) this.dpvFiltros.tipologia.splice(idx, 1)
      else          this.dpvFiltros.tipologia.push(t)
    },

    toggleUFDPV(uf) {
      const idx = this.dpvFiltros.uf.indexOf(uf)
      if (idx > -1) this.dpvFiltros.uf.splice(idx, 1)
      else          this.dpvFiltros.uf.push(uf)
    },

    resetFiltrosDPV() {
      this.dpvFiltros = { franja: [], mes: '', tipologia: [], uf: [] }
    },

    resetFiltrosICO() {
      this.icoFiltros = { fecha_desde:'', fecha_hasta:'', empresa:'', tipo_novedad:'', estado:'', busqueda:'' }
    },

    async cargarDatos() {
      this.loading = true
      this.error   = null
      try {
        const [resDPV, resICO] = await Promise.all([
          axios.get('/api/dpv?limit=9999').catch(() => ({ data: { items: [] } })),
          axios.get('/api/ico?limit=9999').catch(() => ({ data: { items: [] } })),
        ])

        const dpvItems = Array.isArray(resDPV.data) ? resDPV.data : (resDPV.data?.items || [])
        const icoItems = Array.isArray(resICO.data) ? resICO.data : (resICO.data?.items || [])

        this.dpvRaw  = dpvItems.map(normDPV)
        this.icoRaw  = icoItems.map(normICO)
        this.lastSync = new Date().toLocaleString('es-CO')

        // Carga en paralelo el DPV mensual (no bloquea si falla)
        this.cargarDpvMensual()

      } catch (e) {
        this.error = e.message
        console.error('[Store] Error cargando datos:', e)
      } finally {
        this.loading = false
      }
    },

    async cargarDpvMensual() {
      try {
        const { data } = await axios.get('/api/dpv-mensual')
        this.dpvMensual.e10 = data?.e10 || []
        this.dpvMensual.e16 = data?.e16 || []
      } catch (e) {
        console.error('[Store] Error cargando DPV mensual:', e)
      }
    },
  },
})