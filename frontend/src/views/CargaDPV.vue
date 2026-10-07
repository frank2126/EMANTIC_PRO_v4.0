<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>📥</span> Carga Masiva DPV</h1>
      <span class="badge badge-info">Solo Administrador</span>
    </div>

    <!-- ══════════════════════════════════════════════════════
         SECCIÓN 1: CARGA DPV (eventos) — existente, sin cambios
    ══════════════════════════════════════════════════════ -->
    <div class="card upload-card">
      <h3 class="card-title">Subir archivo Excel DPV</h3>
      <p class="upload-hint">
        Formato requerido: <code>.xlsx</code> o <code>.xls</code> · Máximo <strong>10 MB</strong><br/>
        Columnas requeridas: DPV, ESTADO, F. INICIO DPV, F. CIERRE DPV, EMPRESA, FUENTE, PLACA, MOVIL, TIPOLOGIA, FECHA INMOVILIZACION, HORA, CAUSA DE INMOVILIZACION, DESCRIPCION DE LA NOVEDAD, RUTA, OPERADOR, DIA SEMANA, ALERTA, FRANJA HORARIA
      </p>

      <div class="drop-zone"
        :class="{ 'drop-active': arrastrado, 'drop-ok': archivo, 'drop-err': errorLocal }"
        @click="$refs.fi.click()"
        @dragover.prevent="arrastrado=true"
        @dragleave="arrastrado=false"
        @drop.prevent="onDrop">
        <div v-if="!archivo" class="drop-content">
          <span class="drop-icon">📊</span>
          <p>Arrastra el archivo Excel aquí</p>
          <p class="drop-sub">o haz clic para seleccionar</p>
        </div>
        <div v-else class="drop-content">
          <span class="drop-icon">✅</span>
          <p><strong>{{ archivo.name }}</strong></p>
          <p class="drop-sub">{{ (archivo.size / 1024 / 1024).toFixed(2) }} MB</p>
        </div>
        <input ref="fi" type="file" accept=".xlsx,.xls" style="display:none"
          @change="e => setArchivo(e.target.files[0])" />
      </div>

      <p v-if="errorLocal" class="err-msg">⚠️ {{ errorLocal }}</p>

      <div v-if="cargando" class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progreso + '%' }"></div>
        </div>
        <span class="progress-label">Procesando... {{ progreso }}%</span>
      </div>

      <div class="form-actions">
        <button class="btn-secondary" @click="limpiar" :disabled="cargando">Limpiar</button>
        <button class="btn-primary" :disabled="cargando || !archivo" @click="subir">
          {{ cargando ? 'Procesando...' : '⬆ Procesar DPV' }}
        </button>
      </div>
    </div>

    <transition name="slide">
      <div v-if="resultado" class="card resultado-card">
        <h3 class="card-title">Resultado de la carga</h3>
        <div class="kpi-row">
          <div class="kpi-card kpi-green"><div class="kpi-val">{{ resultado.insertados }}</div><div class="kpi-label">Insertados</div></div>
          <div class="kpi-card kpi-blue"><div class="kpi-val">{{ resultado.actualizados }}</div><div class="kpi-label">Actualizados</div></div>
          <div class="kpi-card" :class="resultado.errores > 0 ? 'kpi-red' : 'kpi-green'"><div class="kpi-val">{{ resultado.errores }}</div><div class="kpi-label">Errores</div></div>
          <div class="kpi-card kpi-teal"><div class="kpi-val">{{ resultado.tiempo_seg }}s</div><div class="kpi-label">Tiempo</div></div>
        </div>

        <div v-if="resultado.errores_detalle?.length" class="errores-lista">
          <h4>Detalle de errores:</h4>
          <ul><li v-for="e in resultado.errores_detalle" :key="e">{{ e }}</li></ul>
        </div>

        <div v-if="resultado.preview?.length" class="preview-wrap">
          <h4>Vista previa (primeras 5 filas procesadas):</h4>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>DPV</th><th>Estado</th><th>Placa</th><th>Empresa</th><th>Causa</th><th>Fecha</th></tr></thead>
              <tbody>
                <tr v-for="p in resultado.preview" :key="p.dpv">
                  <td><strong>{{ p.dpv }}</strong></td>
                  <td><span class="badge badge-info">{{ p.estado }}</span></td>
                  <td>{{ p.placa }}</td>
                  <td>{{ p.empresa }}</td>
                  <td class="td-causa">{{ p.causa }}</td>
                  <td>{{ p.fecha }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </transition>

    <div class="card historial-card">
      <h3 class="card-title">Historial de cargas DPV</h3>
      <div v-if="historial.length === 0" class="empty-state">
        <span class="empty-icon">📭</span><p>Sin cargas registradas</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>Fecha</th><th>Usuario</th><th>Archivo</th><th>Total</th><th>Insertados</th><th>Actualizados</th><th>Errores</th><th>Tiempo</th><th>Estado</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in historial" :key="h.id">
              <td>{{ h.fecha }}</td>
              <td>{{ h.usuario }}</td>
              <td class="td-archivo">{{ h.archivo }}</td>
              <td>{{ h.total }}</td>
              <td class="td-green">{{ h.insertados }}</td>
              <td class="td-blue">{{ h.actualizados }}</td>
              <td :class="h.errores > 0 ? 'td-red' : ''">{{ h.errores }}</td>
              <td>{{ h.tiempo_seg }}s</td>
              <td>
                <span class="badge" :class="h.estado==='exitoso' ? 'badge-success' : h.estado==='parcial' ? 'badge-warning' : 'badge-danger'">{{ h.estado }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════
         SECCIÓN 2: CARGA DPV MENSUAL POR KILOMETRAJE — NUEVA
    ══════════════════════════════════════════════════════ -->
    <div class="seccion-divider">
      <span>📈</span>
      <h2>Carga DPV Mensual por Kilometraje</h2>
    </div>

    <div class="card upload-card">
      <h3 class="card-title">Subir archivo Excel DPV Mensual</h3>
      <p class="upload-hint">
        Formato requerido: <code>.xlsx</code> · Máximo <strong>10 MB</strong><br/>
        El archivo debe contener exactamente <strong>dos hojas</strong>: <code>DPV_E10</code> y <code>DPV_E16</code><br/>
        Columnas por hoja: DVP_E10 / DVP_E16, DPV ESTANDAR, DPV CRITICO, FECHA, MES, EMPRESA, No VARADOS, KMS, PADRON, BUSETON
      </p>

      <div class="drop-zone"
        :class="{ 'drop-active': arrastradoMensual, 'drop-ok': archivoMensual, 'drop-err': errorLocalMensual }"
        @click="$refs.fiMensual.click()"
        @dragover.prevent="arrastradoMensual=true"
        @dragleave="arrastradoMensual=false"
        @drop.prevent="onDropMensual">
        <div v-if="!archivoMensual" class="drop-content">
          <span class="drop-icon">📈</span>
          <p>Arrastra el archivo DPV MENSUAL.xlsx aquí</p>
          <p class="drop-sub">o haz clic para seleccionar</p>
        </div>
        <div v-else class="drop-content">
          <span class="drop-icon">✅</span>
          <p><strong>{{ archivoMensual.name }}</strong></p>
          <p class="drop-sub">{{ (archivoMensual.size / 1024 / 1024).toFixed(2) }} MB</p>
        </div>
        <input ref="fiMensual" type="file" accept=".xlsx" style="display:none"
          @change="e => setArchivoMensual(e.target.files[0])" />
      </div>

      <p v-if="errorLocalMensual" class="err-msg">⚠️ {{ errorLocalMensual }}</p>

      <div v-if="cargandoMensual" class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progresoMensual + '%' }"></div>
        </div>
        <span class="progress-label">Procesando... {{ progresoMensual }}%</span>
      </div>

      <div class="form-actions">
        <button class="btn-secondary" @click="limpiarMensual" :disabled="cargandoMensual">Limpiar</button>
        <button class="btn-primary" :disabled="cargandoMensual || !archivoMensual" @click="subirMensual">
          {{ cargandoMensual ? 'Procesando...' : '⬆ Procesar DPV Mensual' }}
        </button>
      </div>
    </div>

    <transition name="slide">
      <div v-if="resultadoMensual" class="card resultado-card">
        <h3 class="card-title">Resultado de la carga mensual</h3>
        <div class="kpi-row">
          <div class="kpi-card kpi-green"><div class="kpi-val">{{ resultadoMensual.insertados }}</div><div class="kpi-label">Insertados</div></div>
          <div class="kpi-card kpi-blue"><div class="kpi-val">{{ resultadoMensual.actualizados }}</div><div class="kpi-label">Actualizados</div></div>
          <div class="kpi-card" :class="resultadoMensual.errores > 0 ? 'kpi-red' : 'kpi-green'"><div class="kpi-val">{{ resultadoMensual.errores }}</div><div class="kpi-label">Errores</div></div>
          <div class="kpi-card kpi-teal"><div class="kpi-val">{{ resultadoMensual.tiempo_seg }}s</div><div class="kpi-label">Tiempo</div></div>
        </div>

        <div v-if="resultadoMensual.errores_detalle?.length" class="errores-lista">
          <h4>Detalle de errores:</h4>
          <ul><li v-for="e in resultadoMensual.errores_detalle" :key="e">{{ e }}</li></ul>
        </div>
      </div>
    </transition>

    <div class="card historial-card">
      <h3 class="card-title">Historial de cargas DPV Mensual</h3>
      <div v-if="historialMensual.length === 0" class="empty-state">
        <span class="empty-icon">📭</span><p>Sin cargas registradas</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>Fecha</th><th>Usuario</th><th>Archivo</th><th>Total</th><th>Insertados</th><th>Actualizados</th><th>Errores</th><th>Tiempo</th><th>Estado</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in historialMensual" :key="h.id">
              <td>{{ h.fecha }}</td>
              <td>{{ h.usuario }}</td>
              <td class="td-archivo">{{ h.archivo }}</td>
              <td>{{ h.total }}</td>
              <td class="td-green">{{ h.insertados }}</td>
              <td class="td-blue">{{ h.actualizados }}</td>
              <td :class="h.errores > 0 ? 'td-red' : ''">{{ h.errores }}</td>
              <td>{{ h.tiempo_seg }}s</td>
              <td>
                <span class="badge" :class="h.estado==='exitoso' ? 'badge-success' : h.estado==='parcial' ? 'badge-warning' : 'badge-danger'">{{ h.estado }}</span>
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

const MAX_MB = 10

/* ── SECCIÓN 1: DPV eventos (sin cambios) ── */
const archivo    = ref(null)
const arrastrado = ref(false)
const cargando   = ref(false)
const progreso   = ref(0)
const errorLocal = ref('')
const resultado  = ref(null)
const historial  = ref([])

const setArchivo = (f) => {
  errorLocal.value = ''
  resultado.value  = null
  if (!f) return
  if (!f.name.match(/\.(xlsx|xls)$/i)) { errorLocal.value = 'Solo se permiten archivos .xlsx o .xls'; return }
  if (f.size > MAX_MB * 1024 * 1024) { errorLocal.value = `El archivo supera el límite de ${MAX_MB} MB`; return }
  archivo.value = f
}
const onDrop = (e) => { arrastrado.value = false; const f = e.dataTransfer.files[0]; if (f) setArchivo(f) }
const limpiar = () => { archivo.value = null; errorLocal.value = ''; resultado.value = null; progreso.value = 0 }

const subir = async () => {
  if (!archivo.value) return
  cargando.value = true; errorLocal.value = ''; resultado.value = null; progreso.value = 10
  const fd = new FormData(); fd.append('file', archivo.value)
  try {
    progreso.value = 30
    const { data } = await axios.post('/api/dpv/upload', fd, {
      onUploadProgress: e => { progreso.value = Math.min(80, Math.round((e.loaded / e.total) * 70) + 10) }
    })
    progreso.value = 100
    resultado.value = data
    await cargarHistorial()
  } catch (e) {
    errorLocal.value = e.response?.data?.detail || 'Error al procesar el archivo'
  } finally {
    cargando.value = false
    setTimeout(() => { progreso.value = 0 }, 1500)
  }
}

const cargarHistorial = async () => {
  try {
    const { data } = await axios.get('/api/cargas/historial?tipo=dpv&limit=10')
    historial.value = data
  } catch {}
}

/* ── SECCIÓN 2: DPV Mensual por Kilometraje (NUEVA) ── */
const archivoMensual    = ref(null)
const arrastradoMensual = ref(false)
const cargandoMensual   = ref(false)
const progresoMensual   = ref(0)
const errorLocalMensual = ref('')
const resultadoMensual  = ref(null)
const historialMensual  = ref([])

const setArchivoMensual = (f) => {
  errorLocalMensual.value = ''
  resultadoMensual.value  = null
  if (!f) return
  if (!f.name.match(/\.xlsx$/i)) { errorLocalMensual.value = 'Solo se permiten archivos .xlsx'; return }
  if (f.size > MAX_MB * 1024 * 1024) { errorLocalMensual.value = `El archivo supera el límite de ${MAX_MB} MB`; return }
  archivoMensual.value = f
}
const onDropMensual = (e) => { arrastradoMensual.value = false; const f = e.dataTransfer.files[0]; if (f) setArchivoMensual(f) }
const limpiarMensual = () => { archivoMensual.value = null; errorLocalMensual.value = ''; resultadoMensual.value = null; progresoMensual.value = 0 }

const subirMensual = async () => {
  if (!archivoMensual.value) return
  cargandoMensual.value = true; errorLocalMensual.value = ''; resultadoMensual.value = null; progresoMensual.value = 10
  const fd = new FormData(); fd.append('file', archivoMensual.value)
  try {
    progresoMensual.value = 30
    const { data } = await axios.post('/api/dpv-mensual/upload', fd, {
      onUploadProgress: e => { progresoMensual.value = Math.min(80, Math.round((e.loaded / e.total) * 70) + 10) }
    })
    progresoMensual.value = 100
    resultadoMensual.value = data
    await cargarHistorialMensual()
  } catch (e) {
    errorLocalMensual.value = e.response?.data?.detail || 'Error al procesar el archivo'
  } finally {
    cargandoMensual.value = false
    setTimeout(() => { progresoMensual.value = 0 }, 1500)
  }
}

const cargarHistorialMensual = async () => {
  try {
    const { data } = await axios.get('/api/cargas/historial?tipo=dpv_mensual&limit=10')
    historialMensual.value = data
  } catch {}
}

onMounted(() => {
  cargarHistorial()
  cargarHistorialMensual()
})
</script>

<style scoped>
.upload-card    { padding: 28px; margin-bottom: 20px; }
.historial-card { padding: 24px; margin-top: 20px; }
.resultado-card { padding: 24px; margin-bottom: 20px; }
.card-title     { font-size: 16px; font-weight: 700; margin-bottom: 14px; color: var(--text); }
.upload-hint    { font-size: 12px; color: var(--text-muted); margin-bottom: 18px; line-height: 1.6; }
.upload-hint code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 11px; color: var(--primary); }

.drop-zone {
  border: 2px dashed var(--border); border-radius: 12px;
  padding: 40px 20px; text-align: center; cursor: pointer;
  transition: all 0.2s; margin-bottom: 16px;
}
.drop-zone:hover, .drop-active { border-color: var(--accent); background: var(--accent-light); }
.drop-ok  { border-color: var(--accent); border-style: solid; background: var(--success-light); }
.drop-err { border-color: var(--danger); background: var(--danger-light); }
.drop-content { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.drop-icon { font-size: 40px; }
.drop-content p { font-size: 14px; color: var(--text); font-weight: 500; }
.drop-sub  { font-size: 12px; color: var(--text-muted) !important; font-weight: 400 !important; }

.progress-wrap  { margin: 12px 0; }
.progress-bar   { background: var(--border); border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 6px; }
.progress-fill  { height: 100%; background: var(--accent); border-radius: 8px; transition: width 0.3s; }
.progress-label { font-size: 12px; color: var(--text-muted); }

.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 16px; }
.err-msg      { color: var(--danger); font-size: 13px; margin: 8px 0; }

.kpi-row  { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; min-width: 100px; text-align: center; }
.kpi-val  { font-size: 28px; font-weight: 800; }
.kpi-label{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.kpi-green .kpi-val { color: var(--accent); }
.kpi-blue  .kpi-val { color: var(--secondary); }
.kpi-red   .kpi-val { color: var(--danger); }
.kpi-teal  .kpi-val { color: var(--teal); }

.errores-lista { background: var(--danger-light); border: 1px solid #fca5a5; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; }
.errores-lista h4 { font-size: 13px; color: var(--danger); margin-bottom: 8px; }
.errores-lista ul { padding-left: 18px; font-size: 12px; color: var(--danger); }
.errores-lista li { margin-bottom: 4px; }

.preview-wrap h4,
.historial-card h4 { font-size: 13px; font-weight: 700; color: var(--text-muted); margin-bottom: 10px; }
.table-wrap   { overflow-x: auto; }
.td-causa     { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.td-archivo   { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }
.td-green     { color: var(--accent); font-weight: 600; }
.td-blue      { color: var(--secondary); font-weight: 600; }
.td-red       { color: var(--danger); font-weight: 600; }

.slide-enter-active, .slide-leave-active { transition: all 0.25s; }
.slide-enter-from, .slide-leave-to       { opacity: 0; transform: translateY(-8px); }

/* ── Separador de sección nueva ── */
.seccion-divider {
  display: flex; align-items: center; gap: 10px;
  margin: 32px 0 18px;
  padding-top: 24px;
  border-top: 2px solid var(--border);
}
.seccion-divider span { font-size: 22px; }
.seccion-divider h2 {
  font-size: 18px; font-weight: 800; color: var(--text);
  margin: 0;
}
</style>
