<template>
  <section class="card upload-card bot-card" aria-labelledby="t-bot">
    <div class="bot-cab">
      <h2 class="card-title" id="t-bot"><RefreshCw :size="20" aria-hidden="true" /> Actualizar datos</h2>
      <span class="bot-estado" :class="'be-' + estado.estado" role="status" aria-live="polite">{{ etiqueta }}</span>
    </div>
    <p class="upload-hint">
      Descarga el DPV, el ICO y el kilometraje de ayer, y los sube a EMANTIC. Solo funciona desde el computador donde corre la aplicación.
    </p>

    <div class="form-actions bot-acciones">
      <button type="button" class="btn-primary" :disabled="corriendo || iniciando" @click="iniciar">
        <RefreshCw :size="16" :class="{ girar: corriendo }" aria-hidden="true" />
        {{ corriendo ? 'Actualizando…' : (iniciando ? 'Iniciando…' : 'Actualizar ahora') }}
      </button>
      <button v-if="corriendo" type="button" class="btn-secondary" @click="cancelar">Cancelar</button>
      <span v-if="horaInicio" class="bot-hora"><Clock :size="14" aria-hidden="true" /> Inició a las {{ horaInicio }}</span>
    </div>

    <p v-if="estado.esperando_captcha" class="bot-aviso" role="status">
      <Info :size="16" aria-hidden="true" />
      Verifica tu sesión en la ventana de Chrome. El proceso sigue solo después.
    </p>
    <p v-if="error" class="err-msg" role="alert"><CircleAlert :size="16" aria-hidden="true" /> {{ error }}</p>

    <ul v-if="listaResultados.length" class="bot-res" role="status">
      <li v-for="r in listaResultados" :key="r.modulo">
        <CircleCheck :size="16" aria-hidden="true" />
        <span><strong>{{ NOMBRES[r.modulo] || r.modulo }}</strong> · {{ r.nuevos }} nuevos · {{ r.actualizados }} actualizados · {{ r.errores }} con error</span>
      </li>
    </ul>
    <p v-else-if="estado.estado === 'ok'" class="bot-aviso" role="status">
      <Info :size="16" aria-hidden="true" /> Terminó, pero no informó cuántos registros cargó. Revisa el detalle.
    </p>
    <p v-if="estado.estado === 'error'" class="err-msg" role="alert">
      <CircleAlert :size="16" aria-hidden="true" /> Terminó con errores. Revisa el detalle.
    </p>

    <details v-if="estado.lineas.length" class="bot-detalle">
      <summary>Ver detalle ({{ estado.lineas.length }} líneas)</summary>
      <pre class="bot-log">{{ textoLog }}</pre>
    </details>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { RefreshCw, Clock, Info, CircleAlert, CircleCheck } from 'lucide-vue-next'

const emit = defineEmits(['listo'])

const ETIQUETAS = { inactivo: 'Listo', corriendo: 'En curso…', ok: 'Terminó', error: 'Falló', cancelado: 'Cancelado' }
const NOMBRES = { DPV: 'DPV', ICO: 'ICO', KM: 'Kilometraje' }
const estado = ref({ estado: 'inactivo', lineas: [], resultado: null, esperando_captcha: false, pestanas: [], inicio: null })
const error = ref('')
const iniciando = ref(false)
let reloj = null

const corriendo = computed(() => estado.value.estado === 'corriendo')
const etiqueta = computed(() => ETIQUETAS[estado.value.estado] || estado.value.estado)
const listaResultados = computed(() => {
  const e = estado.value
  if (e.resultados && Object.keys(e.resultados).length) return Object.keys(e.resultados).map(k => ({ modulo: k, ...e.resultados[k] }))
  return e.resultado ? [{ modulo: 'DPV', ...e.resultado }] : []
})
const textoLog = computed(() => estado.value.lineas.join('\n'))
const horaInicio = computed(() => {
  const i = estado.value.inicio
  if (!i) return ''
  const d = new Date(i + 'Z')
  return isNaN(d) ? '' : d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
})

const mensajeApi = (e) => (e && e.response && e.response.data && e.response.data.detail) || (e && e.response ? `Error ${e.response.status}` : 'No se pudo conectar con el servidor')

function detener() { if (reloj) { clearInterval(reloj); reloj = null } }
function vigilar() { if (!reloj) reloj = setInterval(leer, 2000) }

async function leer() {
  try {
    const { data } = await axios.get('/api/dpv/bot/estado')
    const antes = estado.value.estado
    estado.value = data
    if (data.estado === 'corriendo') vigilar()
    else {
      detener()
      if (antes === 'corriendo' && data.estado === 'ok') emit('listo')
    }
  } catch (e) {
    error.value = mensajeApi(e)
  }
}

async function iniciar() {
  error.value = ''
  iniciando.value = true
  try {
    const { data } = await axios.post('/api/dpv/bot/iniciar')
    estado.value = data
    vigilar()
  } catch (e) {
    error.value = mensajeApi(e)
    await leer()
  } finally {
    iniciando.value = false
  }
}

async function cancelar() {
  error.value = ''
  try {
    const { data } = await axios.post('/api/dpv/bot/cancelar')
    estado.value = data
    detener()
  } catch (e) {
    error.value = mensajeApi(e)
  }
}

onMounted(leer)
onUnmounted(detener)
</script>

<style scoped>
.upload-card { padding: 24px; margin-bottom: 20px; }
.card-title  { font-size: 16px; font-weight: 700; margin-bottom: 8px; color: var(--text); display: flex; align-items: center; gap: 10px; }
.card-title svg { color: var(--primary); flex: none; }
.upload-hint { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.5; max-width: 70ch; }
.bot-cab { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.bot-estado { font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 999px; background: var(--bg); color: var(--text); border: 1px solid var(--border); }
.be-corriendo { background: var(--surface-2); color: var(--primary); border-color: var(--primary); }
.be-ok        { background: var(--success-light); color: #1f5c3a; border-color: transparent; }
.be-error     { background: var(--danger-light); color: #8a1f1f; border-color: transparent; }
.bot-acciones { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-start; margin-top: 0; }
.bot-hora { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: var(--text-muted); }
.bot-aviso { display: flex; align-items: flex-start; gap: 8px; margin-top: 14px; padding: 10px 14px; border-left: 4px solid var(--accent); background: var(--surface-2); font-size: 13.5px; line-height: 1.5; color: var(--text); }
.bot-aviso svg { flex: none; margin-top: 2px; color: var(--primary); }
.bot-res { list-style: none; margin-top: 14px; padding: 10px 14px; border-radius: 8px; background: var(--success-light); font-size: 13.5px; color: #1f3d2f; display: flex; flex-direction: column; gap: 6px; }
.bot-res li { display: flex; align-items: flex-start; gap: 8px; }
.bot-res svg { flex: none; margin-top: 2px; color: #17794f; }
.err-msg { display: flex; align-items: flex-start; gap: 8px; margin-top: 12px; font-size: 13px; color: #8a1f1f; }
.err-msg svg { flex: none; margin-top: 1px; }
.bot-detalle { margin-top: 14px; font-size: 12.5px; }
.bot-detalle summary { cursor: pointer; color: var(--text-muted); }
.bot-log { margin-top: 8px; padding: 12px; max-height: 260px; overflow: auto; background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  font-size: 11.5px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--text); }
.girar { animation: giro 1s linear infinite; }
@keyframes giro { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .girar { animation: none; } }
</style>