<template>
  <div class="bd-wrap">
    <button type="button" class="btn-secondary bd-boton" :disabled="corriendo || iniciando" :aria-expanded="abierto" @click="alPulsar">
      <span v-if="corriendo" class="bd-spin" aria-hidden="true"></span>
      {{ corriendo ? 'Actualizando…' : (iniciando ? 'Iniciando…' : '🤖 Actualizar con el bot') }}
    </button>

    <transition name="bd-pop">
      <section v-if="abierto" class="bd-panel card" role="dialog" aria-label="Actualización automática de disponibilidad">
        <div class="bd-cab">
          <strong>Disponibilidad automática</strong>
          <span class="bd-estado" :class="'be-' + estado.estado" role="status" aria-live="polite">{{ ETIQUETAS[estado.estado] }}</span>
          <button type="button" class="bd-x" aria-label="Cerrar" @click="abierto = false">✕</button>
        </div>

        <p v-if="corriendo" class="bd-txt">
          Bajando de Tako el kilometraje de ayer y el P60, cruzándolos con los inmovilizados y subiendo el resultado. Tarda 1–3 minutos; puedes seguir usando la app.
        </p>
        <p v-if="error" class="err-msg" role="alert">⚠️ {{ error }}</p>

        <p v-if="estado.abortado" class="err-msg" role="alert">
          ⚠️ No se actualizó: {{ estado.abortado }}
        </p>
        <ul v-if="estado.resumen.length" class="bd-lista">
          <li v-for="r in estado.resumen" :key="r">{{ r }}</li>
        </ul>
        <p v-if="estado.estado === 'ok' && !estado.abortado" class="ok-msg">
          ✅ Listo: {{ estado.subidos }} unidad(es) actualizada(s)<template v-if="estado.limpiadas.length"> · {{ estado.limpiadas.join(', ') }} quedó 100 % disponible</template>.
        </p>
        <p v-for="a in estado.avisos" :key="a" class="bd-aviso">ℹ️ {{ a }}</p>
        <p v-if="estado.estado === 'error' || estado.errores.length" class="err-msg" role="alert">
          ⚠️ {{ estado.errores.length ? estado.errores.join(' · ') : 'El bot terminó con errores.' }}
        </p>

        <div class="bd-acciones">
          <button v-if="corriendo" type="button" class="btn-secondary" @click="cancelar">Cancelar</button>
          <button v-else type="button" class="btn-primary" :disabled="iniciando" @click="iniciar">🔄 Actualizar de nuevo</button>
        </div>

        <details v-if="estado.lineas.length" class="bd-detalle">
          <summary>Ver detalle ({{ estado.lineas.length }} líneas)</summary>
          <pre class="bd-log">{{ estado.lineas.join('\n') }}</pre>
        </details>
      </section>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

// «listo»: el bot terminó y subió datos; la pantalla puede recargar la disponibilidad
const emit = defineEmits(['listo'])

const ETIQUETAS = { inactivo: 'Listo', corriendo: 'En curso…', ok: 'Terminó', error: 'Falló', cancelado: 'Cancelado' }
const VACIO = { estado: 'inactivo', lineas: [], resumen: [], avisos: [], errores: [], abortado: null, subidos: 0, limpiadas: [] }
const estado = ref({ ...VACIO })
const abierto = ref(false)
const iniciando = ref(false)
const error = ref('')
let reloj = null
let vistoCorriendo = false

const corriendo = computed(() => estado.value.estado === 'corriendo')

const detalle = (e, texto) => e.response?.data?.detail || texto

const refrescar = async () => {
  try {
    const { data } = await axios.get('/api/disponibilidad/bot/estado')
    const antes = vistoCorriendo
    estado.value = { ...VACIO, ...data }
    if (data.estado === 'corriendo') { vistoCorriendo = true; empezarReloj() }
    else {
      pararReloj()
      if (antes) {                                   // acaba de terminar en esta pantalla
        vistoCorriendo = false
        abierto.value = true
        if (data.estado === 'ok' && !data.abortado) emit('listo')
      }
    }
  } catch (e) {
    error.value = detalle(e, 'No pude consultar el estado del bot')
    pararReloj()
  }
}

const empezarReloj = () => { if (!reloj) reloj = setInterval(refrescar, 2500) }
const pararReloj = () => { if (reloj) { clearInterval(reloj); reloj = null } }

const iniciar = async () => {
  iniciando.value = true; error.value = ''
  try {
    const { data } = await axios.post('/api/disponibilidad/bot/iniciar')
    estado.value = { ...VACIO, ...data }
    vistoCorriendo = true
    abierto.value = true
    empezarReloj()
  } catch (e) {
    abierto.value = true
    error.value = detalle(e, 'No pude iniciar el bot')
  } finally {
    iniciando.value = false
  }
}

const cancelar = async () => {
  try {
    const { data } = await axios.post('/api/disponibilidad/bot/cancelar')
    estado.value = { ...VACIO, ...data }
    vistoCorriendo = false
    pararReloj()
  } catch (e) {
    error.value = detalle(e, 'No pude cancelar')
  }
}

// Con una corrida anterior a la vista (ok/error) el botón vuelve a lanzarla; con el panel cerrado solo lo abre si hay algo que contar
const alPulsar = () => { iniciar() }

onMounted(refrescar)                                 // si el bot ya estaba corriendo (recargaste la página), retoma el seguimiento
onUnmounted(pararReloj)
</script>

<style scoped>
.bd-wrap { position: relative; display: inline-block; }
.bd-boton { display: inline-flex; align-items: center; gap: 8px; }
.bd-spin { width: 12px; height: 12px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: bd-giro .8s linear infinite; }
@keyframes bd-giro { to { transform: rotate(360deg); } }
.bd-panel { position: absolute; right: 0; top: calc(100% + 8px); width: min(440px, calc(100vw - 32px)); z-index: 30; padding: 16px 18px; box-shadow: 0 12px 32px rgba(0,0,0,.16); text-align: left; }
.bd-cab { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bd-cab strong { font-size: 14px; flex: 1; }
.bd-x { background: none; border: 0; cursor: pointer; font-size: 14px; color: var(--text-muted); padding: 4px 6px; }
.bd-estado { font-size: 11px; font-weight: 700; padding: 2px 9px; border-radius: 999px; background: var(--bg); color: var(--text-muted); }
.be-corriendo { background: var(--accent-light); color: var(--accent); }
.be-ok { background: var(--success-light); color: var(--accent); }
.be-error, .be-cancelado { background: #fdecea; color: var(--danger); }
.bd-txt { font-size: 12px; color: var(--text-muted); line-height: 1.5; margin: 6px 0; }
.bd-lista { margin: 8px 0; padding-left: 18px; font-size: 12px; line-height: 1.6; }
.bd-aviso { font-size: 12px; color: var(--text-muted); margin: 6px 0; line-height: 1.4; }
.bd-acciones { display: flex; justify-content: flex-end; gap: 8px; margin-top: 10px; }
.bd-detalle { margin-top: 10px; font-size: 12px; }
.bd-log { max-height: 160px; overflow: auto; background: var(--bg); border-radius: 8px; padding: 8px 10px; font-size: 11px; white-space: pre-wrap; }
.bd-pop-enter-active, .bd-pop-leave-active { transition: opacity .15s, transform .15s; }
.bd-pop-enter-from, .bd-pop-leave-to { opacity: 0; transform: translateY(-4px); }
@media (max-width: 600px) { .bd-panel { position: fixed; left: 16px; right: 16px; top: 72px; width: auto; } }
</style>
