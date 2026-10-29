<template>
  <section class="card upload-card bot-card" aria-labelledby="t-bot">
    <div class="bot-cab">
      <h2 class="card-title" id="t-bot"><span aria-hidden="true">🤖</span> Actualizar DPV desde TransMiTools</h2>
      <span class="bot-estado" :class="'be-' + estado.estado" role="status" aria-live="polite">{{ etiqueta }}</span>
    </div>
    <p class="upload-hint">
      Abre Chrome en este equipo, baja de TransMiTools las pestañas del DPV que tengan datos (Etapas 1.1 a 1.4) y las sube a EMANTIC.
      Si el portal muestra «No soy un robot», márcalo en esa ventana: el bot espera hasta 5 minutos.
      Solo funciona si la aplicación está corriendo en este mismo computador.
    </p>

    <div class="form-actions bot-acciones">
      <button type="button" class="btn-primary" :disabled="corriendo || iniciando" @click="iniciar">
        {{ corriendo ? 'Actualizando…' : (iniciando ? 'Iniciando…' : '🔄 Actualizar DPV ahora') }}
      </button>
      <button v-if="corriendo" type="button" class="btn-secondary" @click="cancelar">Cancelar</button>
      <span v-if="horaInicio" class="bot-hora">Iniciado a las {{ horaInicio }}</span>
    </div>

    <p v-if="estado.esperando_captcha" class="bot-aviso" role="status">
      👉 Mira la ventana de Chrome que se abrió: marca «No soy un robot» e inicia sesión en TransMiTools. El bot continúa solo.
    </p>
    <p v-if="error" class="err-msg" role="alert">⚠️ {{ error }}</p>

    <div v-if="estado.resultado" class="bot-res" role="status">
      ✅ Cargado en EMANTIC: <strong>{{ estado.resultado.nuevos }}</strong> nuevos ·
      <strong>{{ estado.resultado.actualizados }}</strong> actualizados ·
      <strong>{{ estado.resultado.errores }}</strong> con error
    </div>
    <p v-else-if="estado.estado === 'ok'" class="bot-aviso" role="status">
      El bot terminó, pero no informó cuántos registros se cargaron. Revisa el detalle.
    </p>
    <p v-if="estado.estado === 'error'" class="err-msg" role="alert">
      ⚠️ El bot terminó con errores. Revisa el detalle de abajo.
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

// «listo»: el bot terminó bien; la pantalla que lo contiene puede refrescar historial y totales
const emit = defineEmits(['listo'])

const ETIQUETAS = { inactivo: 'Listo', corriendo: 'En curso…', ok: 'Terminó', error: 'Falló', cancelado: 'Cancelado' }
const estado = ref({ estado: 'inactivo', lineas: [], resultado: null, esperando_captcha: false, pestanas: [], inicio: null })
const error = ref('')
const iniciando = ref(false)
let reloj = null

const corriendo = computed(() => estado.value.estado === 'corriendo')
const etiqueta = computed(() => ETIQUETAS[estado.value.estado] || estado.value.estado)
const textoLog = computed(() => estado.value.lineas.join('\n'))
const horaInicio = computed(() => {
  const i = estado.value.inicio
  if (!i) return ''
  const d = new Date(i + 'Z')                                  // el backend manda hora UTC sin «Z»
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
    error.value = mensajeApi(e)                                // si falla una consulta no se rompe nada: se reintenta en el próximo ciclo
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
    await leer()                                               // p. ej. «ya está corriendo»: se muestra su estado real
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

onMounted(leer)                                                // si recargas la página con el bot corriendo, retoma el seguimiento
onUnmounted(detener)
</script>

<style scoped>
.upload-card { padding: 24px; margin-bottom: 20px; }
.card-title  { font-size: 16px; font-weight: 700; margin-bottom: 12px; color: var(--text); display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.upload-hint { font-size: 12.5px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.6; }
.bot-cab { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.bot-estado { font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 999px; background: var(--bg); color: var(--text); border: 1px solid var(--border); }
.be-corriendo { background: var(--surface-2); color: var(--primary); border-color: var(--primary); }
.be-ok        { background: var(--success-light); color: #1f5c3a; border-color: transparent; }
.be-error     { background: var(--danger-light); color: #8a1f1f; border-color: transparent; }
.bot-acciones { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.bot-hora { font-size: 12px; color: var(--text-muted); }
.bot-aviso { margin-top: 14px; padding: 10px 14px; border-left: 4px solid var(--accent); background: var(--surface-2); font-size: 13.5px; line-height: 1.5; color: var(--text); }
.bot-res { margin-top: 14px; padding: 10px 14px; border-radius: 8px; background: var(--success-light); font-size: 13.5px; color: #1f3d2f; }
.err-msg { margin-top: 12px; font-size: 13px; color: #8a1f1f; }
.bot-detalle { margin-top: 14px; font-size: 12.5px; }
.bot-detalle summary { cursor: pointer; color: var(--text-muted); }
.bot-log { margin-top: 8px; padding: 12px; max-height: 260px; overflow: auto; background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  font-size: 11.5px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--text); }
</style>
