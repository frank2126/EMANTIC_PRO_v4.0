// dashboardStore.js — carga en dos fases (mes en curso primero, resto en segundo plano)
import { defineStore } from 'pinia'
import axios from 'axios'
import {
  DIM, SELECCION_VACIA, aplicarSlicers, aplicarSeleccion, haySeleccion, ranking, dona, heatmap,
  chipsSeleccion, normTipologia, ufDeRegistro, tipoInfraccionLocal, diasParaResponder, hoyISO,
  ESTADO_PENDIENTE,
} from './icoUtils.js'
// DPV: misma mecánica que ICO (slicers + selección cruzada); la lógica pura vive en dpvUtils.js
import * as DPV from './dpvUtils.js'

// Eventos del DPV tal como llegan del backend → filas del tablero (y se unifican las causas recortadas por el Excel)
const prepararDPV = items => DPV.unificarCausas((items || []).map(DPV.normDPV))

function normICO(r) {
  const empresa = (r.empresa || '').trim()
  const movil   = (r.movil  || '').trim()
  const tipo    = (r.tipo_novedad || '').trim()
  const fechaNovedad = (r.fecha_novedad || '').slice(0, 10)
  return {
    id:           r.id,
    ico_id:       r.ico_id,
    estado:       (r.estado || '').trim(),
    empresa,
    uf:           ufDeRegistro(empresa, movil),            // 'UF10' | 'UF16' | ''
    placa:        (r.placa  || '').trim(),
    movil,
    tipo_novedad: tipo,
    // Clasificación calculada en el backend; respaldo local si el backend es anterior a este cambio
    tipo_infraccion: r.tipo_infraccion || tipoInfraccionLocal(tipo),
    // Fecha base del tablero = F. IDENTIFICACION (igual que el Power BI); respaldo: F. NOVEDAD
    fecha:        (r.fecha_identificacion || '').slice(0, 10) || fechaNovedad,
    fecha_novedad: fechaNovedad,
    fecha_notificacion: (r.fecha_notificacion || '').slice(0, 10),
    fecha_cierre: (r.fecha_cierre || '').slice(0, 10),
    hora:         (r.hora || '').slice(0, 8),
    tipologia:    normTipologia(r.tipologia),               // 'PADRON' | 'BUSETON' (sin tildes)
    puntos:       parseInt(r.puntos) || 0,                  // 0 = sin puntos asignados
    descripcion:  (r.descripcion || '').trim(),
    direccion:    (r.direccion || '').trim(),
    dia_semana:   (r.dia_semana || '').trim(),
    area:         (r.area || '').trim(),
  }
}

// Mes en curso en formato 'YYYY-MM' (hora local, no UTC)
function mesActual() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const filtrosICOVacios = () => ({
  uf: [],               // ['UF10', 'UF16']
  anio: '',             // '2026'; '' = todos los años
  meses: [],            // [9] → solo septiembre; [] = todos los meses (requiere año)
  tipo_infraccion: [],  // ['Directo', 'Hallazgo Rechazado']
  tipologia: [],        // ['PADRON', 'BUSETON']
  estado: '',
  busqueda: '',         // móvil o placa
})

// Agrega o quita `v` de la lista (la modifica en su lugar)
function alternar(lista, v) {
  const i = lista.indexOf(v)
  if (i > -1) lista.splice(i, 1)
  else lista.push(v)
}

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dpvRaw:  [],
    icoRaw:  [],
    loading: false,
    error:   null,
    lastSync: null,

    // true cuando ya se descargó TODO el DPV (necesario para las opciones de año/mes y el contador del tab)
    dpvCompleto: false,

    disponibilidad: { e10: null, e16: null },

    // ── DPV mensual = km ÷ inmovilizaciones, una serie por unidad (la calcula el backend: /api/dpv-mensual) ──
    dpvMensual: {
      e10: [],   // [{ mes, mes_label, km, inm, dpv, km_padron, inm_padron, dpv_padron, …, nivel, origen }]
      e16: [],
    },
    dpvUmbrales: { ...DPV.UMBRALES_DEFECTO },   // { estandar, critico } en km: los manda el backend (.env)
    dpvEstadosDescartados: [],                   // estados que NO cuentan como inmovilización (los manda el backend)

    // ── DPV: slicers (filtros duros) y selección cruzada por clic en las gráficas ──
    dpvFiltros: DPV.filtrosVacios(),
    dpvSel:     DPV.SELECCION_VACIA(),
    dpvInicializado: false,   // true cuando ya se aplicó el mes más reciente como filtro inicial

    // ── ICO: slicers (filtros duros) y selección cruzada por clic en las gráficas ──
    icoFiltros: filtrosICOVacios(),
    icoSel:     SELECCION_VACIA(),
    icoInicializado: false,   // true cuando ya se aplicó el mes más reciente como filtro inicial
  }),

  getters: {

    // ══════════════════════════════════════════════════════════
    //  DPV — filtros duros (slicers) + selección cruzada estilo Power BI
    //  Lógica pura en dpvUtils.js. DPV = km del mes ÷ inmovilizaciones del mes (las calcula el backend).
    // ══════════════════════════════════════════════════════════

    // Filas tras los slicers (Unidad, Año/Mes, Franja, Tipología, Estado, búsqueda)
    dpvBase(state) {
      return DPV.aplicarSlicers(state.dpvRaw, state.dpvFiltros)
    },

    // Filas tras slicers + selección cruzada: alimenta los contadores y la tabla de detalle
    dpvFiltrado(state) {
      return DPV.aplicarSeleccion(this.dpvBase, state.dpvSel)
    },

    dpvHaySeleccion(state) {
      return haySeleccion(state.dpvSel)
    },

    dpvChips(state) {
      return DPV.chipsSeleccion(state.dpvSel)
    },

    dpvKPIs() {
      return { ...DPV.kpisEventos(this.dpvFiltrado, hoyISO()), baseTotal: this.dpvBase.length }
    },

    // Eventos de TODO el histórico bajo la misma regla de estado que el resto del tablero (base del PORCENTAJE)
    dpvTotalHistorico(state) {
      return DPV.aplicarSlicers(state.dpvRaw, { ...DPV.filtrosVacios(), estado: state.dpvFiltros.estado }).length
    },

    // Qué parte del histórico es lo que se ve ahora (slicers + selección), con un decimal
    dpvPorcentaje() {
      const total = this.dpvTotalHistorico
      return total ? Math.round((this.dpvFiltrado.length / total) * 1000) / 10 : 0
    },

    // Cada visual excluye SU PROPIA dimensión de la selección para mostrar todas sus categorías
    // (con las seleccionadas resaltadas) y aplica el resto de selecciones.
    dpvHeatmap(state) {
      return DPV.heatmap(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'periodos'), state.dpvFiltros, state.dpvSel.periodos)
    },

    dpvHoras(state) {
      return DPV.horasHeat(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'hora'), state.dpvSel.hora)
    },

    dpvDona(state) {
      return DPV.dona(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'tipologia'), state.dpvSel.tipologia)
    },

    dpvCausas(state) {
      return DPV.ranking(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'causa'), DPV.DIM.causa, { seleccion: state.dpvSel.causa })
    },

    dpvRutas(state) {
      return DPV.ranking(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'ruta'), DPV.DIM.ruta, { seleccion: state.dpvSel.ruta })
    },

    dpvMoviles(state) {
      return DPV.ranking(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'movil'), DPV.DIM.movil, { seleccion: state.dpvSel.movil })
    },

    dpvOperadores(state) {
      return DPV.ranking(DPV.aplicarSeleccion(this.dpvBase, state.dpvSel, 'operador'), DPV.DIM.operador, { seleccion: state.dpvSel.operador })
    },

    // Opciones de los slicers a partir de los datos cargados
    dpvOpciones(state) {
      return DPV.opcionesSlicers(state.dpvRaw)
    },

    // DPV mensual: una tarjeta por unidad visible (todas si no hay unidad elegida). El KPI sigue el periodo de los slicers;
    // la gráfica muestra TODO el histórico con los meses del periodo resaltados. Los km son del mes completo, así que
    // ni Franja, Estado, búsqueda ni la selección cruzada lo modifican (ver dpvKpiAviso).
    dpvTarjetas(state) {
      const f = state.dpvFiltros
      const u = state.dpvUmbrales
      const campo = DPV.camposSerie(f.tipologia)
      const visibles = f.uf.length ? f.uf : DPV.UNIDADES.map(x => x.key)
      return DPV.UNIDADES.filter(x => visibles.includes(x.key)).map(x => {
        const datos = (x.key === 'UF10' ? state.dpvMensual.e10 : state.dpvMensual.e16) || []
        const geo = DPV.geometriaSerie(datos, { campo: campo.dpv, umbrales: u })
        return {
          uf: x.key, label: x.label, nombre: x.nombre, color: DPV.COLOR_UF[x.key],
          datos, campo, geo,
          kpi: DPV.kpiDpv([{ uf: x.key, datos }], f, u),
          puntos: geo.puntos.map(p => ({ ...p, enPeriodo: DPV.enPeriodo(p.mes, f) })),
          etiquetados: [...DPV.indicesEtiquetados(geo.puntos)],
        }
      })
    },

    // ¿Hay algún filtro que el DPV mensual NO aplica? (la vista lo avisa para que no se espere otra cosa)
    dpvKpiAviso(state) {
      const f = state.dpvFiltros
      return f.franja.length > 0 || !!f.estado || !!f.busqueda.trim() || haySeleccion(state.dpvSel)
    },

    // ══════════════════════════════════════════════════════════
    //  ICO — filtros duros (slicers) + selección cruzada estilo Power BI
    //  Lógica pura en icoUtils.js
    // ══════════════════════════════════════════════════════════

    // Filas tras los slicers (Unidad, Año/Mes, Tipo de infracción, Tipología, Estado, Móvil/Placa)
    icoBase(state) {
      return aplicarSlicers(state.icoRaw, state.icoFiltros)
    },

    // Filas tras slicers + selección cruzada: alimenta KPIs y tabla de detalle
    icoFiltrado(state) {
      return aplicarSeleccion(this.icoBase, state.icoSel)
    },

    icoHaySeleccion(state) {
      return haySeleccion(state.icoSel)
    },

    icoChips(state) {
      return chipsSeleccion(state.icoSel)
    },

    icoKPIs() {
      const data = this.icoFiltrado
      const hoy = hoyISO()
      const moviles = new Set()
      const codigos = new Set()
      let puntos = 0
      let sinContestar = 0
      let ventanaAbierta = 0
      for (const r of data) {
        puntos += r.puntos
        if (r.movil || r.placa) moviles.add(r.movil || r.placa)
        if (r.tipo_novedad) codigos.add(r.tipo_novedad)
        if (r.estado === ESTADO_PENDIENTE) {
          sinContestar++
          if (diasParaResponder(r, hoy) !== null) ventanaAbierta++
        }
      }
      return {
        total: data.length,
        puntos,
        moviles: moviles.size,
        tipos: codigos.size,
        sinContestar,
        ventanaAbierta,        // "No Contestado" cuya F. CIERRE DPV aún no vence
        baseTotal: this.icoBase.length,
        baseTotalPuntos: this.icoBase.reduce((s, r) => s + r.puntos, 0),
      }
    },

    // Cada visual excluye SU PROPIA dimensión de la selección para mostrar todas sus categorías
    // (con las seleccionadas resaltadas) y aplica el resto de selecciones.
    icoHeatmap(state) {
      return heatmap(aplicarSeleccion(this.icoBase, state.icoSel, 'periodos'), state.icoFiltros, state.icoSel.periodos)
    },

    icoDona(state) {
      return dona(aplicarSeleccion(this.icoBase, state.icoSel, 'tipologia'), state.icoSel.tipologia)
    },

    icoTipoNovedad(state) {
      return ranking(aplicarSeleccion(this.icoBase, state.icoSel, 'tipo_novedad'), DIM.tipo_novedad,
        { seleccion: state.icoSel.tipo_novedad })
    },

    icoTipoInfraccion(state) {
      return ranking(aplicarSeleccion(this.icoBase, state.icoSel, 'tipo_infraccion'), DIM.tipo_infraccion,
        { seleccion: state.icoSel.tipo_infraccion })
    },

    icoEstados(state) {
      return ranking(aplicarSeleccion(this.icoBase, state.icoSel, 'estado'), DIM.estado,
        { seleccion: state.icoSel.estado })
    },

    icoTopMoviles(state) {
      return ranking(aplicarSeleccion(this.icoBase, state.icoSel, 'movil'), DIM.movil,
        { seleccion: state.icoSel.movil })
    },

    // Opciones de los slicers a partir de los datos cargados
    icoOpciones(state) {
      const anios = new Set()
      const meses = {}
      const estados = new Set()
      for (const r of state.icoRaw) {
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
      return {
        anios: [...anios].sort().reverse(),
        mesesPorAnio,
        estados: [...estados].sort(),
      }
    },
  },

  actions: {
    // ── DPV: slicers ─────────────────────────────────────────
    // Cambiar un slicer limpia la selección cruzada (las claves de día/mes pueden dejar de existir).

    toggleUFDPV(uf) {
      alternar(this.dpvFiltros.uf, uf)
      this.limpiarSelDPV()
    },

    setAnioDPV(anio) {
      this.dpvFiltros.anio = anio ? String(anio) : ''
      // Al cambiar de año se conservan solo los meses que existan en ese año; sin año no hay meses
      const disponibles = this.dpvFiltros.anio ? (this.dpvOpciones.mesesPorAnio[this.dpvFiltros.anio] || []) : []
      this.dpvFiltros.meses = this.dpvFiltros.meses.filter(m => disponibles.includes(m))
      this.limpiarSelDPV()
    },

    toggleMesDPV(mes) {
      if (!this.dpvFiltros.anio) return
      alternar(this.dpvFiltros.meses, mes)
      this.limpiarSelDPV()
    },

    toggleFranjaDPV(franja) {
      alternar(this.dpvFiltros.franja, franja)
      this.limpiarSelDPV()
    },

    toggleTipoDPV(tipologia) {
      alternar(this.dpvFiltros.tipologia, tipologia)
      this.limpiarSelDPV()
    },

    // '' = solo lo que cuenta para el DPV · '*' = todos los estados · otro texto = ese estado
    setEstadoDPV(estado) {
      this.dpvFiltros.estado = estado || ''
      this.limpiarSelDPV()
    },

    setBusquedaDPV(texto) {
      this.dpvFiltros.busqueda = texto || ''
      this.limpiarSelDPV()
    },

    // "Limpiar": quita TODOS los filtros y selecciones (muestra todo el histórico)
    resetFiltrosDPV() {
      this.dpvFiltros = DPV.filtrosVacios()
      this.limpiarSelDPV()
    },

    // Filtro inicial = año y mes más recientes con datos (como abre el tablero ICO). Se aplica una sola vez.
    aplicarPorDefectoDPV() {
      const p = DPV.periodoPorDefecto(this.dpvRaw)
      if (!p) return
      this.dpvFiltros.anio  = p.anio
      this.dpvFiltros.meses = p.meses
      this.dpvInicializado  = true
    },

    // Clic en un mes de la gráfica de DPV mensual: el tablero pasa a ese mes. Clic en el único mes elegido: todo el año.
    // Ctrl / ⌘ / Shift + clic suma o quita meses (solo dentro del mismo año).
    irAMesDPV(mes, aditivo = false) {
      const anio = mes.slice(0, 4)
      const m = parseInt(mes.slice(5, 7), 10)
      const f = this.dpvFiltros
      if (aditivo && f.anio === anio) alternar(f.meses, m)
      else if (f.anio === anio && f.meses.length === 1 && f.meses[0] === m) f.meses = []
      else { f.anio = anio; f.meses = [m] }
      this.limpiarSelDPV()
    },

    // ── DPV: selección cruzada (clic en gráficas y tablas) ───────
    // Mismas reglas que ICO: clic simple reemplaza (o quita si era la única); Ctrl / ⌘ / Shift suma; entre visuales se combinan (Y).
    toggleSelDPV(dim, key, aditivo = false) {
      const actual = this.dpvSel[dim]
      if (!actual) return
      if (aditivo) {
        alternar(actual, key)
      } else {
        this.dpvSel[dim] = (actual.length === 1 && actual[0] === key) ? [] : [key]
      }
    },

    quitarSelDPV(dim, key) {
      const actual = this.dpvSel[dim]
      if (actual) this.dpvSel[dim] = actual.filter(k => k !== key)
    },

    limpiarSelDPV() {
      this.dpvSel = DPV.SELECCION_VACIA()
    },

    // ── ICO: slicers ─────────────────────────────────────────
    // Cambiar un slicer limpia la selección cruzada (las claves de día/mes pueden dejar de existir).

    toggleUFICO(uf) {
      alternar(this.icoFiltros.uf, uf)
      this.limpiarSelICO()
    },

    setAnioICO(anio) {
      this.icoFiltros.anio = anio ? String(anio) : ''
      // Al cambiar de año se conservan solo los meses que existan en ese año; sin año no hay meses
      const disponibles = this.icoFiltros.anio ? (this.icoOpciones.mesesPorAnio[this.icoFiltros.anio] || []) : []
      this.icoFiltros.meses = this.icoFiltros.meses.filter(m => disponibles.includes(m))
      this.limpiarSelICO()
    },

    toggleMesICO(mes) {
      if (!this.icoFiltros.anio) return
      alternar(this.icoFiltros.meses, mes)
      this.limpiarSelICO()
    },

    toggleTipoInfraccionICO(tipo) {
      alternar(this.icoFiltros.tipo_infraccion, tipo)
      this.limpiarSelICO()
    },

    toggleTipologiaICO(tipologia) {
      alternar(this.icoFiltros.tipologia, tipologia)
      this.limpiarSelICO()
    },

    setEstadoICO(estado) {
      this.icoFiltros.estado = estado || ''
      this.limpiarSelICO()
    },

    setBusquedaICO(texto) {
      this.icoFiltros.busqueda = texto || ''
      this.limpiarSelICO()
    },

    // "Limpiar": quita TODOS los filtros y selecciones (muestra todo el histórico)
    resetFiltrosICO() {
      this.icoFiltros = filtrosICOVacios()
      this.limpiarSelICO()
    },

    // Filtro inicial = año y mes más recientes con datos (como abre el Power BI). Se aplica una sola vez.
    aplicarPorDefectoICO() {
      let ultima = ''
      for (const r of this.icoRaw) if (r.fecha > ultima) ultima = r.fecha
      if (!ultima) return
      this.icoFiltros.anio  = ultima.slice(0, 4)
      this.icoFiltros.meses = [parseInt(ultima.slice(5, 7), 10)]
      this.icoInicializado  = true
    },

    // ── ICO: selección cruzada (clic en gráficas y tablas) ───────
    // Clic simple: reemplaza la selección de esa visual (o la quita si ya era la única elegida).
    // Ctrl / ⌘ / Shift + clic: suma o quita elementos. Entre visuales distintas las selecciones se combinan (Y).
    toggleSelICO(dim, key, aditivo = false) {
      const actual = this.icoSel[dim]
      if (!actual) return
      if (aditivo) {
        alternar(actual, key)
      } else {
        this.icoSel[dim] = (actual.length === 1 && actual[0] === key) ? [] : [key]
      }
    },

    quitarSelICO(dim, key) {
      const actual = this.icoSel[dim]
      if (actual) this.icoSel[dim] = actual.filter(k => k !== key)
    },

    limpiarSelICO() {
      this.icoSel = SELECCION_VACIA()
    },

    // ── FASE 1: solo el mes en curso (rápido) ──────────────
    // Si ya hay datos en pantalla (botón «Recargar»), no se encoge primero al mes en curso: se refresca todo de una vez.
    async cargarDatos() {
      this.loading = true
      this.error   = null
      const primeraVez = !this.dpvRaw.length
      try {
        if (primeraVez) {
          this.dpvCompleto = false
          const { data } = await axios.get('/api/dpv', {
            params: { mes: mesActual(), slim: true, limit: 5000 },
          })
          this.dpvRaw   = prepararDPV(data?.items)
          this.lastSync = new Date().toLocaleString('es-CO')
          if (!this.dpvInicializado) this.aplicarPorDefectoDPV()
        } else {
          await this.cargarDpvCompleto()
          this.lastSync = new Date().toLocaleString('es-CO')
        }
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
        console.error('[Store] Error cargando DPV:', e)
      } finally {
        this.loading = false
      }

      // ── FASE 2: en segundo plano, sin bloquear la pantalla ──
      if (primeraVez) this.cargarDpvCompleto()
      this.cargarIco()
      this.cargarDpvMensual()
      this.cargarDisponibilidad()
    },

    async cargarDpvCompleto() {
      try {
        const { data } = await axios.get('/api/dpv', {
          params: { slim: true, limit: 20000 },
        })
        this.dpvRaw      = prepararDPV(data?.items)
        this.dpvCompleto = true
        // Si el mes en curso aún no tenía eventos, el filtro inicial se decide ahora, con todo el histórico
        if (!this.dpvInicializado) this.aplicarPorDefectoDPV()
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
        console.error('[Store] Error cargando DPV completo:', e)
      }
    },

    async cargarIco() {
      try {
        const { data } = await axios.get('/api/ico', { params: { limit: 9999 } })
        const items = Array.isArray(data) ? data : (data?.items || [])
        this.icoRaw = items.map(normICO)
        if (!this.icoInicializado) this.aplicarPorDefectoICO()
      } catch (e) {
        console.error('[Store] Error cargando ICO:', e)
      }
    },

    async cargarDisponibilidad() {
      try {
        const { data } = await axios.get('/api/disponibilidad')
        this.disponibilidad.e10 = data?.e10 || null
        this.disponibilidad.e16 = data?.e16 || null
      } catch (e) {
        console.error('[Store] Error cargando disponibilidad:', e)
      }
    },

    async cargarDpvMensual() {
      try {
        const { data } = await axios.get('/api/dpv-mensual')
        this.dpvMensual.e10 = data?.e10 || []
        this.dpvMensual.e16 = data?.e16 || []
        this.dpvUmbrales = {
          estandar: data?.umbrales?.estandar ?? DPV.UMBRALES_DEFECTO.estandar,
          critico:  data?.umbrales?.critico  ?? DPV.UMBRALES_DEFECTO.critico,
        }
        this.dpvEstadosDescartados = data?.estados_descartados || []
      } catch (e) {
        console.error('[Store] Error cargando DPV mensual:', e)
      }
    },
  },
})