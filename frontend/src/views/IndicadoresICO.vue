<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>📈</span> Indicadores ICO</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showUploadDisp = !showUploadDisp">
          {{ showUploadDisp ? '✕ Cancelar' : '📊 Cargar Disponibilidad' }}
        </button>
        <button class="btn-primary" @click="showUpload = !showUpload">
          {{ showUpload ? '✕ Cancelar' : '⬆ Cargar Excel ICO' }}
        </button>
      </div>
    </div>

    <!-- ── CARGA ICO ── -->
    <transition name="slide">
      <div v-if="showUpload" class="card upload-card">
        <h3 class="card-title">Subir archivo Excel ICO</h3>
        <p class="upload-hint">
          Columnas requeridas: ICO, ID NOVEDAD, ESTADO, F. INICIO DPV, F. CIERRE DPV, EMPRESA, TIPO NOVEDAD, F. NOVEDAD, F. IDENTIFICACION, F. NOTIFICACION, FUENTE, AREA, DIRECCION, PLACA, MOVIL, TIPOLOGIA, DIA SEMANA, PUNTOS, DESCRIPCION
        </p>
        <div class="drop-zone"
          :class="{ 'drop-active': arrastrado, 'drop-ok': archivoIco }"
          @click="$refs.fiIco.click()"
          @dragover.prevent="arrastrado=true"
          @dragleave="arrastrado=false"
          @drop.prevent="e => setArchivo(e.dataTransfer.files[0])">
          <span class="drop-icon">{{ archivoIco ? '✅' : '📊' }}</span>
          <p>{{ archivoIco ? archivoIco.name : 'Arrastra el Excel ICO o haz clic' }}</p>
          <p class="drop-sub" v-if="archivoIco">{{ (archivoIco.size/1024/1024).toFixed(2) }} MB</p>
          <input ref="fiIco" type="file" accept=".xlsx,.xls" style="display:none"
            @change="e => setArchivo(e.target.files[0])" />
        </div>
        <p v-if="uploadErr" class="err-msg">{{ uploadErr }}</p>
        <p v-if="uploadOk"  class="ok-msg">{{ uploadOk }}</p>
        <div v-if="cargando" class="progress-wrap">
          <div class="progress-bar"><div class="progress-fill" :style="{width: progreso+'%'}"></div></div>
          <span class="progress-label">Procesando... {{ progreso }}%</span>
        </div>
        <div class="form-actions">
          <button class="btn-secondary" @click="showUpload=false; archivoIco=null">Cancelar</button>
          <button class="btn-primary" :disabled="cargando || !archivoIco" @click="subirIco">
            {{ cargando ? 'Procesando...' : '⬆ Procesar ICO' }}
          </button>
        </div>
      </div>
    </transition>

    <!-- ── CARGA DISPONIBILIDAD ── -->
    <transition name="slide">
      <div v-if="showUploadDisp" class="card upload-card">
        <h3 class="card-title">Subir archivo Excel de Disponibilidad de Flota</h3>
        <p class="upload-hint">
          Formato: <code>.xlsx</code> · Sube el archivo de cada unidad por separado (UF-10, luego UF-16) — la unidad se detecta automáticamente por el prefijo de la placa (Z32-/Z34-).<br/>
          Columnas requeridas: MOVIL, FECHA DE CORTE, FECHA DE INGRESO A MANTENIMIENTO, DIAS DE INOPERATIVIDAD, DESCRIPCIÓN DE LA FALLA
        </p>
        <div class="drop-zone"
          :class="{ 'drop-active': arrastradoDisp, 'drop-ok': archivoDisp }"
          @click="$refs.fiDisp.click()"
          @dragover.prevent="arrastradoDisp=true"
          @dragleave="arrastradoDisp=false"
          @drop.prevent="e => setArchivoDisp(e.dataTransfer.files[0])">
          <span class="drop-icon">{{ archivoDisp ? '✅' : '📊' }}</span>
          <p>{{ archivoDisp ? archivoDisp.name : 'Arrastra el Excel de Disponibilidad o haz clic' }}</p>
          <p class="drop-sub" v-if="archivoDisp">{{ (archivoDisp.size/1024/1024).toFixed(2) }} MB</p>
          <input ref="fiDisp" type="file" accept=".xlsx,.xls" style="display:none"
            @change="e => setArchivoDisp(e.target.files[0])" />
        </div>
        <p v-if="uploadErrDisp" class="err-msg">{{ uploadErrDisp }}</p>
        <p v-if="uploadOkDisp"  class="ok-msg">{{ uploadOkDisp }}</p>
        <div v-if="cargandoDisp" class="progress-wrap">
          <div class="progress-bar"><div class="progress-fill" :style="{width: progresoDisp+'%'}"></div></div>
          <span class="progress-label">Procesando... {{ progresoDisp }}%</span>
        </div>
        <div class="form-actions">
          <button class="btn-secondary" @click="showUploadDisp=false; archivoDisp=null">Cancelar</button>
          <button class="btn-primary" :disabled="cargandoDisp || !archivoDisp" @click="subirDisponibilidad">
            {{ cargandoDisp ? 'Procesando...' : '⬆ Procesar Disponibilidad' }}
          </button>
        </div>
      </div>
    </transition>

    <!-- ── KPIs ── -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-icon">📋</div>
        <div class="kpi-val">{{ resumen.total || 0 }}</div>
        <div class="kpi-label">Total ICOs</div>
      </div>
      <div class="kpi-card kpi-blue">
        <div class="kpi-icon">🔍</div>
        <div class="kpi-val">{{ resumen.por_tipo?.length || 0 }}</div>
        <div class="kpi-label">Tipos de novedad</div>
      </div>
      <div class="kpi-card kpi-teal">
        <div class="kpi-icon">🚌</div>
        <div class="kpi-val">{{ resumen.top_placas?.length || 0 }}</div>
        <div class="kpi-label">Placas únicas</div>
      </div>
      <div class="kpi-card kpi-green">
        <div class="kpi-icon">✅</div>
        <div class="kpi-val">{{ aceptados }}</div>
        <div class="kpi-label">Aceptados</div>
      </div>
    </div>

    <!-- ── FILTROS ── -->
    <div class="card filter-bar">
      <div class="filter-group">
        <label class="label">Fecha desde</label>
        <input type="date" v-model="filtros.fecha_desde" class="input input-sm" />
      </div>
      <div class="filter-group">
        <label class="label">Fecha hasta</label>
        <input type="date" v-model="filtros.fecha_hasta" class="input input-sm" />
      </div>
      <div class="filter-group">
        <label class="label">Empresa</label>
        <select v-model="filtros.empresa" class="input input-sm">
          <option value="">Todas</option>
          <option v-for="e in filtrosOpc.empresas" :key="e">{{ e }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="label">Tipo novedad</label>
        <select v-model="filtros.tipo_novedad" class="input input-sm">
          <option value="">Todos</option>
          <option v-for="t in filtrosOpc.tipos" :key="t">{{ t }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="label">Estado</label>
        <select v-model="filtros.estado" class="input input-sm">
          <option value="">Todos</option>
          <option v-for="s in filtrosOpc.estados" :key="s">{{ s }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="label">Placa / Móvil</label>
        <input v-model="filtros.placa" class="input input-sm" placeholder="Ej: ABC123" />
      </div>
      <button class="btn-secondary btn-sm" @click="limpiarFiltros">✕ Limpiar</button>
      <button class="btn-primary btn-sm"   @click="buscar">🔍 Buscar</button>
      <button class="btn-secondary btn-sm" @click="exportarExcel">📊 Excel</button>
    </div>

    <!-- ── GRÁFICOS ── -->
    <div class="charts-grid">
      <!-- Barras: por tipo novedad -->
      <div class="card chart-card">
        <h4 class="chart-title">ICOs por Tipo de Novedad</h4>
        <div class="bar-chart">
          <div v-for="item in resumen.por_tipo?.slice(0,10)" :key="item.tipo" class="bar-row">
            <span class="bar-label">{{ item.tipo || 'Sin tipo' }}</span>
            <div class="bar-track">
              <div class="bar-fill"
                :style="{ width: pct(item.total, maxTipo) + '%' }"
                :title="item.total"></div>
            </div>
            <span class="bar-val">{{ item.total }}</span>
          </div>
        </div>
      </div>

      <!-- Circular: por estado -->
      <div class="card chart-card">
        <h4 class="chart-title">Distribución por Estado</h4>
        <div class="donut-wrap">
          <svg viewBox="0 0 160 160" class="donut-svg">
            <circle cx="80" cy="80" r="60" fill="none" stroke="var(--border)" stroke-width="28"/>
            <circle v-for="(seg, i) in donutSegments" :key="i"
              cx="80" cy="80" r="60" fill="none"
              :stroke="seg.color" stroke-width="28"
              :stroke-dasharray="`${seg.dash} ${seg.gap}`"
              :stroke-dashoffset="seg.offset"
              style="transform: rotate(-90deg); transform-origin: 80px 80px;"/>
          </svg>
          <div class="donut-legend">
            <div v-for="(seg, i) in donutSegments" :key="i" class="legend-item">
              <span class="legend-dot" :style="{ background: seg.color }"></span>
              <span class="legend-label">{{ seg.label }}</span>
              <span class="legend-val">{{ seg.total }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top placas -->
      <div class="card chart-card">
        <h4 class="chart-title">Top Unidades con más ICOs</h4>
        <div class="bar-chart">
          <div v-for="item in resumen.top_placas?.slice(0,10)" :key="item.placa" class="bar-row">
            <span class="bar-label">{{ item.placa || 'Sin placa' }}</span>
            <div class="bar-track">
              <div class="bar-fill bar-fill--blue"
                :style="{ width: pct(item.total, maxPlaca) + '%' }"></div>
            </div>
            <span class="bar-val">{{ item.total }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── TABLA PAGINADA ── -->
    <div class="card tabla-card">
      <div class="tabla-header">
        <h3 class="card-title">Registros ICO</h3>
        <span class="total-label">{{ totalRegistros }} registros</span>
      </div>
      <div v-if="loadingTabla" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando...</p></div>
      <div v-else-if="registros.length === 0" class="empty-state">
        <span class="empty-icon">📭</span><p>Sin registros. Carga un archivo ICO.</p>
      </div>
      <div v-else>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>ICO</th><th>ID Nov.</th><th>Estado</th><th>Empresa</th>
                <th>Tipo Novedad</th><th>Placa</th><th>Móvil</th>
                <th>Fecha</th><th>Área</th><th>Puntos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in registros" :key="r.id">
                <td><strong>{{ r.ico_id }}</strong></td>
                <td>{{ r.id_novedad }}</td>
                <td>
                  <span class="badge"
                    :class="r.estado==='Aceptado' ? 'badge-success' : r.estado==='Rechazado' ? 'badge-danger' : 'badge-info'">
                    {{ r.estado }}
                  </span>
                </td>
                <td>{{ r.empresa }}</td>
                <td><code class="tipo-code">{{ r.tipo_novedad }}</code></td>
                <td>{{ r.placa }}</td>
                <td>{{ r.movil }}</td>
                <td>{{ r.fecha_novedad }}</td>
                <td>{{ r.area }}</td>
                <td>{{ r.puntos || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Paginación -->
        <div class="pagination">
          <button class="btn-secondary btn-sm" :disabled="pagina === 0" @click="pagina--; buscar()">← Anterior</button>
          <span class="pag-info">Página {{ pagina + 1 }} de {{ totalPaginas }}</span>
          <button class="btn-secondary btn-sm" :disabled="pagina >= totalPaginas - 1" @click="pagina++; buscar()">Siguiente →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from './dashboardStore.js'

const store = useDashboardStore()

const COLORES = ['#31b079','#074e7a','#248a7c','#60b566','#d4780a','#c0392b','#6c5ce7','#e17055']

// Estado carga ICO
const showUpload = ref(false)
const archivoIco = ref(null)
const arrastrado = ref(false)
const cargando   = ref(false)
const progreso   = ref(0)
const uploadErr  = ref('')
const uploadOk   = ref('')

// Estado carga Disponibilidad
const showUploadDisp = ref(false)
const archivoDisp    = ref(null)
const arrastradoDisp = ref(false)
const cargandoDisp   = ref(false)
const progresoDisp   = ref(0)
const uploadErrDisp  = ref('')
const uploadOkDisp   = ref('')

// Datos
const resumen       = ref({ total: 0, por_tipo: [], por_estado: [], top_placas: [] })
const filtrosOpc    = ref({ empresas: [], tipos: [], estados: [] })
const registros     = ref([])
const totalRegistros = ref(0)
const loadingTabla  = ref(false)
const pagina        = ref(0)
const POR_PAGINA    = 50

const filtros = ref({
  fecha_desde: '', fecha_hasta: '', empresa: '',
  tipo_novedad: '', estado: '', placa: ''
})

const totalPaginas = computed(() => Math.max(1, Math.ceil(totalRegistros.value / POR_PAGINA)))
const aceptados    = computed(() => resumen.value.por_estado?.find(e => e.estado === 'Aceptado')?.total || 0)
const maxTipo      = computed(() => Math.max(1, ...( resumen.value.por_tipo?.map(t => t.total) || [1])))
const maxPlaca     = computed(() => Math.max(1, ...( resumen.value.top_placas?.map(t => t.total) || [1])))

const pct = (val, max) => Math.round((val / max) * 100)

// Donut chart
const donutSegments = computed(() => {
  const data = resumen.value.por_estado || []
  const total = data.reduce((s, d) => s + d.total, 0) || 1
  const circ  = 2 * Math.PI * 60  // ~376.99
  let offset  = 0
  return data.map((d, i) => {
    const dash = (d.total / total) * circ
    const seg  = { label: d.estado, total: d.total, color: COLORES[i % COLORES.length], dash, gap: circ - dash, offset }
    offset += dash
    return seg
  })
})

const setArchivo = (f) => {
  uploadErr.value = ''; uploadOk.value = ''
  if (!f) return
  if (!f.name.match(/\.(xlsx|xls)$/i)) { uploadErr.value = 'Solo .xlsx o .xls'; return }
  if (f.size > 10 * 1024 * 1024)       { uploadErr.value = 'Supera 10 MB'; return }
  archivoIco.value = f
}

const subirIco = async () => {
  if (!archivoIco.value) return
  cargando.value = true; uploadErr.value = ''; uploadOk.value = ''; progreso.value = 10
  const fd = new FormData()
  fd.append('file', archivoIco.value)
  try {
    progreso.value = 30
    const { data } = await axios.post('/api/ico/upload', fd, {
      onUploadProgress: e => { progreso.value = Math.min(80, Math.round((e.loaded/e.total)*70)+10) }
    })
    progreso.value = 100
    uploadOk.value = `✅ ${data.message} — ${data.insertados} insertados, ${data.actualizados} actualizados`
    archivoIco.value = null
    await cargarTodo()
  } catch (e) {
    uploadErr.value = e.response?.data?.detail || 'Error al procesar'
  } finally {
    cargando.value = false
    setTimeout(() => { progreso.value = 0 }, 1500)
  }
}

// ── Disponibilidad de flota ──
const setArchivoDisp = (f) => {
  uploadErrDisp.value = ''; uploadOkDisp.value = ''
  if (!f) return
  if (!f.name.match(/\.(xlsx|xls)$/i)) { uploadErrDisp.value = 'Solo .xlsx o .xls'; return }
  if (f.size > 10 * 1024 * 1024)       { uploadErrDisp.value = 'Supera 10 MB'; return }
  archivoDisp.value = f
}

const subirDisponibilidad = async () => {
  if (!archivoDisp.value) return
  cargandoDisp.value = true; uploadErrDisp.value = ''; uploadOkDisp.value = ''; progresoDisp.value = 10
  const fd = new FormData()
  fd.append('file', archivoDisp.value)
  try {
    progresoDisp.value = 30
    const { data } = await axios.post('/api/disponibilidad/upload', fd, {
      onUploadProgress: e => { progresoDisp.value = Math.min(80, Math.round((e.loaded/e.total)*70)+10) }
    })
    progresoDisp.value = 100
    uploadOkDisp.value = `✅ ${data.message} — ${data.insertados} insertados, ${data.actualizados} actualizados`
    archivoDisp.value = null
    await store.cargarDisponibilidad()
  } catch (e) {
    uploadErrDisp.value = e.response?.data?.detail || 'Error al procesar'
  } finally {
    cargandoDisp.value = false
    setTimeout(() => { progresoDisp.value = 0 }, 1500)
  }
}

const buscar = async () => {
  loadingTabla.value = true
  try {
    const params = { limit: POR_PAGINA, offset: pagina.value * POR_PAGINA }
    Object.entries(filtros.value).forEach(([k, v]) => { if (v) params[k] = v })
    const { data } = await axios.get('/api/ico', { params })
    registros.value     = data.items
    totalRegistros.value = data.total
  } catch {} finally { loadingTabla.value = false }
}

const limpiarFiltros = () => {
  filtros.value = { fecha_desde:'', fecha_hasta:'', empresa:'', tipo_novedad:'', estado:'', placa:'' }
  pagina.value = 0
  buscar()
}

const exportarExcel = async () => {
  const params = new URLSearchParams({ limit: 9999, offset: 0 })
  Object.entries(filtros.value).forEach(([k, v]) => { if (v) params.set(k, v) })
  const { data } = await axios.get(`/api/ico?${params}`)
  const rows = data.items
  const headers = ['ICO','ID Novedad','Estado','Empresa','Tipo Novedad','Placa','Móvil','Fecha','Área','Puntos','Descripción']
  const csv = [
    headers.join(','),
    ...rows.map(r => [
      r.ico_id, r.id_novedad, r.estado, `"${r.empresa}"`, r.tipo_novedad,
      r.placa, r.movil, r.fecha_novedad, r.area, r.puntos, `"${(r.descripcion||'').replace(/"/g,'""')}"`
    ].join(','))
  ].join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = `ICO_reporte_${new Date().toISOString().slice(0,10)}.csv`
  a.click(); URL.revokeObjectURL(url)
}

const cargarTodo = async () => {
  try {
    const [res, filt] = await Promise.all([
      axios.get('/api/ico/resumen'),
      axios.get('/api/ico/filtros'),
    ])
    resumen.value    = res.data
    filtrosOpc.value = filt.data
  } catch {}
  await buscar()
}

onMounted(cargarTodo)
</script>

<style scoped>
.header-actions { display: flex; gap: 10px; }
.upload-card  { padding: 24px; margin-bottom: 20px; }
.card-title   { font-size: 16px; font-weight: 700; margin-bottom: 14px; }
.upload-hint  { font-size: 11px; color: var(--text-muted); margin-bottom: 14px; line-height: 1.6; }
.upload-hint code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 11px; color: var(--primary); }
.drop-zone    { border: 2px dashed var(--border); border-radius: 12px; padding: 32px; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 14px; }
.drop-zone:hover, .drop-active { border-color: var(--accent); background: var(--accent-light); }
.drop-ok      { border-color: var(--accent); border-style: solid; background: var(--success-light); }
.drop-icon    { font-size: 36px; display: block; margin-bottom: 8px; }
.drop-sub     { font-size: 12px; color: var(--text-muted); }
.err-msg      { color: var(--danger); font-size: 13px; margin: 8px 0; }
.ok-msg       { color: var(--accent); font-size: 13px; margin: 8px 0; font-weight: 600; }
.progress-wrap { margin: 10px 0; }
.progress-bar  { background: var(--border); border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 4px; }
.progress-fill { height: 100%; background: var(--accent); border-radius: 8px; transition: width 0.3s; }
.progress-label{ font-size: 12px; color: var(--text-muted); }
.form-actions  { display: flex; gap: 10px; justify-content: flex-end; margin-top: 14px; }

/* KPIs */
.kpi-row  { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; flex: 1; min-width: 120px; text-align: center; }
.kpi-icon { font-size: 22px; margin-bottom: 6px; }
.kpi-val  { font-size: 30px; font-weight: 800; color: var(--primary); }
.kpi-label{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.kpi-blue  .kpi-val { color: var(--secondary); }
.kpi-teal  .kpi-val { color: var(--teal); }
.kpi-green .kpi-val { color: var(--accent); }

/* Filtros */
.filter-bar   { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; padding: 16px 20px; margin-bottom: 20px; }
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.input-sm     { padding: 7px 10px; font-size: 13px; min-width: 130px; }
.btn-sm       { padding: 8px 14px; font-size: 13px; align-self: flex-end; }

/* Gráficos */
.charts-grid  { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.chart-card   { padding: 20px; }
.chart-title  { font-size: 13px; font-weight: 700; color: var(--text-muted); margin-bottom: 16px; text-transform: uppercase; letter-spacing: .5px; }

/* Barras horizontales */
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row   { display: flex; align-items: center; gap: 8px; }
.bar-label { font-size: 11px; color: var(--text-muted); width: 70px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; background: var(--bg); border-radius: 4px; height: 14px; overflow: hidden; }
.bar-fill  { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.5s; }
.bar-fill--blue { background: var(--secondary); }
.bar-val   { font-size: 11px; font-weight: 700; color: var(--text); width: 28px; text-align: right; }

/* Donut */
.donut-wrap   { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.donut-svg    { width: 140px; height: 140px; flex-shrink: 0; }
.donut-legend { display: flex; flex-direction: column; gap: 8px; flex: 1; }
.legend-item  { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.legend-dot   { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-label { flex: 1; color: var(--text-muted); }
.legend-val   { font-weight: 700; color: var(--text); }

/* Tabla */
.tabla-card   { padding: 0; overflow: hidden; margin-top: 0; }
.tabla-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 0; }
.total-label  { font-size: 13px; color: var(--text-muted); }
.table-wrap   { overflow-x: auto; }
.tipo-code    { background: var(--primary-light); color: var(--primary); padding: 2px 7px; border-radius: 4px; font-size: 11px; font-family: monospace; }

/* Paginación */
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 16px; border-top: 1px solid var(--border); }
.pag-info   { font-size: 13px; color: var(--text-muted); }

@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
  .filter-bar  { flex-direction: column; }
  .header-actions { flex-direction: column; align-items: stretch; }
}
.slide-enter-active, .slide-leave-active { transition: all 0.25s; }
.slide-enter-from,   .slide-leave-to     { opacity: 0; transform: translateY(-8px); }
</style>