<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>📈</span> Analíticas Power BI</h1>
      <button v-if="isAdmin()" class="btn-secondary" @click="showConfig = !showConfig">⚙ Configurar URL</button>
    </div>

    <transition name="slide">
      <div v-if="showConfig && isAdmin()" class="card config-card">
        <h3 class="card-title">Conectar reporte Power BI</h3>
        <p class="config-hint">En Power BI Service → <strong>Archivo → Insertar informe → Sitio web o portal</strong> → copia la URL del iframe.</p>
        <div class="config-form">
          <div class="fgroup">
            <label class="label">URL de inserción (Embed URL)</label>
            <input v-model="embedUrl" type="url" class="input" placeholder="https://app.powerbi.com/reportEmbed?reportId=..." />
          </div>
          <div class="fgroup">
            <label class="label">Actualización automática</label>
            <select v-model="refreshMode" class="input">
              <option value="none">Sin recarga automática</option>
              <option value="30">Cada 30 segundos</option>
              <option value="60">Cada 1 minuto</option>
              <option value="300">Cada 5 minutos</option>
            </select>
          </div>
        </div>
        <p v-if="saveErr" class="err-msg">{{ saveErr }}</p>
        <div class="config-actions">
          <button class="btn-secondary" @click="showConfig=false">Cancelar</button>
          <button class="btn-primary" :disabled="saving" @click="save">{{ saving ? 'Guardando...' : 'Guardar y aplicar' }}</button>
        </div>
      </div>
    </transition>

    <p v-if="loadErr" class="err-msg">{{ loadErr }}</p>

    <div v-if="loaded && activeUrl" class="card bi-wrapper">
      <div class="bi-header">
        <div class="bi-status"><span class="status-dot"></span> Power BI conectado · {{ refreshLabel }}</div>
        <span class="bi-hint">¿Ves «Iniciar sesión»? Entra una vez con tu cuenta de Microsoft y marca «Mantener la sesión iniciada».</span>
        <button class="btn-secondary btn-sm" @click="frameKey++">↻ Recargar ahora</button>
      </div>
      <iframe :key="frameKey" :src="activeUrl" class="bi-frame" frameborder="0" allowFullScreen title="Power BI Emantic" />
    </div>

    <div v-else-if="loaded && isAdmin()" class="card empty-pbi">
      <div class="pbi-icon">📊</div>
      <h3>Conecta tu reporte de Power BI</h3>
      <p>Haz clic en <strong>⚙ Configurar URL</strong> y pega la URL de inserción de tu reporte.</p>
      <div class="steps">
        <div class="step"><span class="sn">1</span><span>Ve a tu reporte en <strong>app.powerbi.com</strong></span></div>
        <div class="step"><span class="sn">2</span><span>Clic en <strong>Archivo → Insertar informe → Sitio web o portal</strong></span></div>
        <div class="step"><span class="sn">3</span><span>Copia el enlace del <code>&lt;iframe src="..."&gt;</code></span></div>
        <div class="step"><span class="sn">4</span><span>Pégalo en la configuración y haz clic en Guardar</span></div>
      </div>
      <p class="pbi-note">💡 Los datos se actualizan según la programación configurada en Power BI Service</p>
    </div>

    <div v-else-if="loaded" class="card empty-pbi">
      <div class="pbi-icon">📊</div>
      <h3>Todavía no hay un reporte conectado</h3>
      <p>Pídele al administrador que configure la URL de Power BI.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'
const { isAdmin } = useAuth()

const embedUrl    = ref('')
const activeUrl   = ref('')
const refreshMode = ref('none')
const showConfig  = ref(false)
const frameKey    = ref(0)
const loaded      = ref(false)
const saving      = ref(false)
const saveErr     = ref('')
const loadErr     = ref('')
let timer = null

const refreshLabel = computed(() => ({'none':'manual','30':'cada 30s','60':'cada 1min','300':'cada 5min'}[refreshMode.value]||'manual'))

// Solo https y solo dominios de Power BI (el servidor valida lo mismo)
const urlValida = u => {
  try {
    const p = new URL(u)
    const h = p.hostname.toLowerCase()
    return p.protocol === 'https:' &&
      (h === 'powerbi.com' || h.endsWith('.powerbi.com') || h.endsWith('.powerbigov.us'))
  } catch { return false }
}

const guardarEnServidor = async (url, refresh) => {
  const { data } = await axios.put('/api/config/powerbi', { url, refresh })
  return data
}

const save = async () => {
  saveErr.value = ''
  const url = embedUrl.value.trim()
  if (!url) { saveErr.value = 'Pega la URL de inserción de Power BI.'; return }
  if (!urlValida(url)) {
    saveErr.value = 'La URL debe ser https y de powerbi.com (la que se copia en Archivo → Insertar informe → Sitio web o portal).'
    return
  }
  saving.value = true
  try {
    const data = await guardarEnServidor(url, refreshMode.value)
    activeUrl.value = data.url
    frameKey.value++
    showConfig.value = false
    startRefresh()
  } catch (e) {
    saveErr.value = e.response?.data?.detail || 'No se pudo guardar. Intenta de nuevo.'
  } finally {
    saving.value = false
  }
}

const startRefresh = () => {
  if (timer) clearInterval(timer)
  if (refreshMode.value !== 'none') timer = setInterval(() => frameKey.value++, parseInt(refreshMode.value) * 1000)
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/config/powerbi')
    activeUrl.value   = data.url || ''
    refreshMode.value = data.refresh || 'none'

    // Migración: si el servidor aún no tiene URL pero este navegador sí la guardó
    // (versión anterior), el administrador la sube una vez y se limpia del navegador.
    const local = localStorage.getItem('emantix_bi_url')
    if (!activeUrl.value && local && isAdmin() && urlValida(local)) {
      const saved = await guardarEnServidor(local, localStorage.getItem('emantix_bi_refresh') || 'none')
      activeUrl.value   = saved.url
      refreshMode.value = saved.refresh
      localStorage.removeItem('emantix_bi_url')
      localStorage.removeItem('emantix_bi_refresh')
    }
  } catch {
    loadErr.value = 'No se pudo cargar la configuración de Power BI.'
  }
  embedUrl.value = activeUrl.value
  loaded.value = true
  startRefresh()
})
onUnmounted(() => { if (timer) clearInterval(timer) })
watch(refreshMode, startRefresh)
</script>

<style scoped>
.config-card   { padding:24px; margin-bottom:24px; }
.card-title    { font-size:16px; font-weight:700; margin-bottom:8px; }
.config-hint   { font-size:13px; color:var(--text-muted); background:var(--primary-light); border-left:3px solid var(--primary); padding:10px 14px; border-radius:6px; margin-bottom:16px; }
.config-form   { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:16px; }
.fgroup        { display:flex; flex-direction:column; gap:6px; }
.config-actions{ display:flex; gap:10px; justify-content:flex-end; }
.btn-sm        { padding:7px 14px !important; font-size:13px !important; }
.err-msg       { color:var(--danger); font-size:13px; margin-bottom:10px; }

.bi-wrapper    { overflow:hidden; }
.bi-header     { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 20px; border-bottom:1px solid var(--border); background:#f8fafc; }
.bi-status     { display:flex; align-items:center; gap:8px; font-size:13px; color:var(--text-muted); font-weight:500; white-space:nowrap; }
.bi-hint       { flex:1; font-size:12px; color:var(--text-muted); text-align:center; }
.status-dot    { width:8px; height:8px; background:var(--success); border-radius:50%; animation:pulse 2s infinite; }
@keyframes pulse{ 0%,100%{opacity:1} 50%{opacity:0.4} }
.bi-frame      { width:100%; height:72vh; display:block; background:#fff; }

.empty-pbi     { padding:60px 40px; text-align:center; max-width:600px; margin:0 auto; }
.pbi-icon      { font-size:56px; margin-bottom:16px; }
.empty-pbi h3  { font-size:20px; font-weight:700; margin-bottom:10px; }
.empty-pbi p   { color:var(--text-muted); font-size:14px; margin-bottom:28px; }
.steps         { text-align:left; display:flex; flex-direction:column; gap:12px; margin-bottom:20px; }
.step          { display:flex; align-items:flex-start; gap:12px; font-size:14px; }
.sn            { background:var(--primary); color:#fff; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }
code           { background:var(--bg); padding:2px 6px; border-radius:4px; font-size:12px; }
.pbi-note      { font-size:12px; color:var(--text-muted); background:var(--bg); padding:10px 14px; border-radius:8px; margin-bottom:0; }

@media(max-width:900px){ .bi-header{flex-wrap:wrap;} .bi-hint{order:3; flex-basis:100%; text-align:left;} }
@media(max-width:768px){ .config-form{grid-template-columns:1fr;} .bi-frame{height:55vh;} }
</style>