<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>📊</span> Reportes de Campo</h1>
      <button class="btn-primary" @click="showUpload = !showUpload">
        {{ showUpload ? '✕ Cancelar' : '⬆ Cargar CSV' }}
      </button>
    </div>

    <!-- ── CARGA CSV ── -->
    <transition name="slide">
      <div v-if="showUpload" class="card upload-card">
        <h3 class="card-title">Importar reporte desde CSV</h3>
        <p class="upload-hint">
          El CSV debe tener las columnas:
          <code>fecha, pir, unidad_funcional, tecnico, supervisor, protocolo, bus, novedad, tipo_novedad</code>
        </p>
        <div class="drop-zone"
          @click="$refs.csvInput.click()"
          @dragover.prevent
          @drop.prevent="e => csvFile = e.dataTransfer.files[0]"
          :class="{ 'drop-active': csvFile }">
          <span v-if="!csvFile">📄 Arrastra el CSV aquí o haz clic para seleccionar</span>
          <span v-else style="color:var(--success)">✅ {{ csvFile.name }}</span>
        </div>
        <input ref="csvInput" type="file" accept=".csv" style="display:none"
          @change="e => csvFile = e.target.files[0]" />
        <p v-if="uploadErr" class="err-msg">{{ uploadErr }}</p>
        <p v-if="uploadOk" class="ok-msg">{{ uploadOk }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showUpload=false; csvFile=null; uploadErr=''; uploadOk=''">Cancelar</button>
          <button class="btn-primary" :disabled="uploading || !csvFile" @click="uploadCSV">
            {{ uploading ? 'Importando...' : '⬆ Importar' }}
          </button>
        </div>
      </div>
    </transition>

    <!-- ── FILTROS ── -->
    <div class="card filter-bar">
      <div class="filter-group">
        <label class="label">Fecha</label>
        <input type="date" v-model="filtros.fecha" class="input input-sm" />
      </div>
      <div class="filter-group">
        <label class="label">PIR</label>
        <select v-model="filtros.pir" class="input input-sm">
          <option value="">Todos</option>
          <option>Bilbao</option>
          <option>Gaitana</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="label">Tipo novedad</label>
        <select v-model="filtros.tipo_novedad" class="input input-sm">
          <option value="">Todos</option>
          <option>OK</option>
          <option>Aceite</option>
          <option>Refrigerante</option>
          <option>Regeneración</option>
          <option>Alerta</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="label">N° Bus</label>
        <input type="number" v-model="filtros.bus" class="input input-sm" placeholder="Ej: 4003" />
      </div>
      <button class="btn-secondary btn-sm" @click="limpiarFiltros">✕ Limpiar</button>
      <button class="btn-primary btn-sm" @click="cargar">🔍 Buscar</button>
    </div>

    <!-- ── RESUMEN ── -->
    <div v-if="resumen" class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-val">{{ resumen.total_inspecciones }}</div>
        <div class="kpi-label">Total inspecciones</div>
      </div>
      <div class="kpi-card kpi-warn">
        <div class="kpi-val">{{ resumen.total_novedades }}</div>
        <div class="kpi-label">Con novedad</div>
      </div>
      <div v-for="(val, tipo) in resumen.por_tipo" :key="tipo" class="kpi-card" :class="kpiClass(tipo)">
        <div class="kpi-val">{{ val }}</div>
        <div class="kpi-label">{{ tipo }}</div>
      </div>
    </div>

    <!-- ── TABLA ── -->
    <div class="card table-card">
      <div v-if="loading" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando reportes...</p></div>
      <div v-else-if="reportes.length === 0" class="empty-state">
        <span class="empty-icon">📭</span>
        <p>No hay reportes. Carga un CSV para comenzar.</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>PIR</th>
              <th>UF</th>
              <th>Técnico</th>
              <th>Supervisor</th>
              <th>Protocolo</th>
              <th>Bus</th>
              <th>Novedad</th>
              <th>Tipo</th>
              <th v-if="isAdmin()"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reportes" :key="r.id" :class="rowClass(r.tipo_novedad)">
              <td>{{ r.fecha }}</td>
              <td>{{ r.pir }}</td>
              <td>{{ r.unidad_funcional }}</td>
              <td>{{ r.tecnico }}</td>
              <td>{{ r.supervisor || '—' }}</td>
              <td>{{ r.protocolo }}</td>
              <td><strong>{{ r.bus }}</strong></td>
              <td>{{ r.novedad }}</td>
              <td><span class="badge" :class="badgeClass(r.tipo_novedad)">{{ r.tipo_novedad }}</span></td>
              <td v-if="isAdmin()">
                <button class="btn-del-sm" @click="eliminar(r.id)" title="Eliminar">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'

const { isAdmin } = useAuth()

const reportes   = ref([])
const resumen    = ref(null)
const loading    = ref(false)
const showUpload = ref(false)
const csvFile    = ref(null)
const uploading  = ref(false)
const uploadErr  = ref('')
const uploadOk   = ref('')

const filtros = ref({ fecha: '', pir: '', tipo_novedad: '', bus: '' })

const limpiarFiltros = () => {
  filtros.value = { fecha: '', pir: '', tipo_novedad: '', bus: '' }
  cargar()
}

const cargar = async () => {
  loading.value = true
  try {
    const params = {}
    if (filtros.value.fecha)        params.fecha        = filtros.value.fecha
    if (filtros.value.pir)          params.pir          = filtros.value.pir
    if (filtros.value.tipo_novedad) params.tipo_novedad = filtros.value.tipo_novedad
    if (filtros.value.bus)          params.bus          = filtros.value.bus

    const [rep, res] = await Promise.all([
      axios.get('/api/reportes', { params }),
      axios.get('/api/reportes/resumen', { params: {
        fecha_desde: filtros.value.fecha || undefined,
        fecha_hasta: filtros.value.fecha || undefined,
      }})
    ])
    reportes.value = rep.data
    resumen.value  = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const uploadCSV = async () => {
  uploadErr.value = ''; uploadOk.value = ''; uploading.value = true
  const fd = new FormData()
  fd.append('file', csvFile.value)
  try {
    const { data } = await axios.post('/api/reportes/upload-csv', fd)
    uploadOk.value = data.message
    if (data.errores?.length) uploadErr.value = 'Advertencias: ' + data.errores.join(' | ')
    csvFile.value = null
    await cargar()
  } catch (e) {
    uploadErr.value = e.response?.data?.detail || 'Error al importar CSV'
  } finally {
    uploading.value = false
  }
}

const eliminar = async id => {
  if (!confirm('¿Eliminar este registro?')) return
  try { await axios.delete(`/api/reportes/${id}`); await cargar() } catch {}
}

const rowClass = tipo => ({
  'row-ok':    tipo === 'OK',
  'row-warn':  ['Aceite','Refrigerante'].includes(tipo),
  'row-regen': tipo === 'Regeneración',
  'row-alert': tipo === 'Alerta',
})

const badgeClass = tipo => ({
  'badge-ok':    tipo === 'OK',
  'badge-warn':  ['Aceite','Refrigerante'].includes(tipo),
  'badge-regen': tipo === 'Regeneración',
  'badge-alert': tipo === 'Alerta',
})

const kpiClass = tipo => ({
  'kpi-ok':    tipo === 'OK',
  'kpi-warn':  ['Aceite','Refrigerante'].includes(tipo),
  'kpi-regen': tipo === 'Regeneración',
  'kpi-alert': tipo === 'Alerta',
})

onMounted(cargar)
</script>

<style scoped>
.upload-card  { padding: 24px; margin-bottom: 20px; }
.card-title   { font-size: 16px; font-weight: 700; margin-bottom: 10px; }
.upload-hint  { font-size: 12px; color: var(--text-muted); margin-bottom: 14px; }
.upload-hint code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.drop-zone    { border: 2px dashed var(--border); border-radius: 10px; padding: 28px; text-align: center; cursor: pointer; color: var(--text-muted); font-size: 14px; transition: all 0.2s; }
.drop-zone:hover, .drop-active { border-color: var(--primary); color: var(--primary); }
.err-msg      { color: var(--danger); font-size: 13px; margin-top: 8px; }
.ok-msg       { color: var(--success); font-size: 13px; margin-top: 8px; }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 16px; }

/* Filtros */
.filter-bar   { display: flex; gap: 14px; align-items: flex-end; flex-wrap: wrap; padding: 16px 20px; margin-bottom: 20px; }
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.input-sm     { padding: 7px 10px; font-size: 13px; }
.btn-sm       { padding: 8px 14px; font-size: 13px; align-self: flex-end; }

/* KPIs */
.kpi-row  { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; min-width: 110px; text-align: center; }
.kpi-val  { font-size: 28px; font-weight: 800; color: var(--primary); }
.kpi-label{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.kpi-warn  .kpi-val { color: #E65100; }
.kpi-regen .kpi-val { color: #F57F17; }
.kpi-alert .kpi-val { color: var(--danger); }

/* Tabla */
.table-card { padding: 0; overflow: hidden; }
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: var(--primary-dark); color: #fff; padding: 11px 14px; text-align: left; font-size: 12px; white-space: nowrap; }
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
.row-warn  td { background: #FFFDE7; }
.row-regen td { background: #FFF3E0; }
.row-alert td { background: #FCE4EC; }

/* Badges */
.badge        { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-ok     { background: #E8F5E9; color: #1B6B35; }
.badge-warn   { background: #FFF9C4; color: #F57F17; }
.badge-regen  { background: #FFF3E0; color: #E65100; }
.badge-alert  { background: #FCE4EC; color: #B71C1C; }

.btn-del-sm { background: #fee2e2; border: 1px solid #fecaca; color: var(--danger); padding: 5px 9px; border-radius: 7px; cursor: pointer; font-size: 12px; }
.btn-del-sm:hover { background: var(--danger); color: #fff; }

@media(max-width: 768px) { .filter-bar { flex-direction: column; } }

.slide-enter-active, .slide-leave-active { transition: all 0.25s; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>