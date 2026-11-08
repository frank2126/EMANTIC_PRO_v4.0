<template>
  <div class="ep" :class="{ 'ep--oscuro': oscuro }">
    <label class="ep-fila" :class="{ 'ep-fila--off': !puede }">
      <span class="ep-texto">
        <strong>Informes técnicos por correo</strong>
        <small v-if="!cargado">Cargando…</small>
        <small v-else-if="!puede">Tu usuario no tiene correo registrado. Pide a un administrador que lo agregue.</small>
        <small v-else>Recibir informes técnicos semanales y alertas del sistema en mi correo electrónico</small>
      </span>
      <button type="button" class="ep-sw" role="switch" :aria-checked="activo" :disabled="!puede || guardando"
              :class="{ 'ep-sw--on': activo }" aria-label="Recibir informes técnicos y alertas por correo" @click.prevent="cambiar">
        <span class="ep-knob"></span>
      </button>
    </label>
    <p v-if="mensaje" class="ep-msg" :class="'ep-msg--' + tipo" role="status">{{ mensaje }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

defineProps({ oscuro: { type: Boolean, default: false } })

const activo = ref(false)
const tieneCorreo = ref(true)
const cargado = ref(false)
const guardando = ref(false)
const mensaje = ref('')
const tipo = ref('ok')
let temporizador = null

const puede = computed(() => cargado.value && tieneCorreo.value)

function avisar(texto, t = 'ok') {
  mensaje.value = texto; tipo.value = t
  clearTimeout(temporizador)
  temporizador = setTimeout(() => { mensaje.value = '' }, 3500)
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/subscriptions/me')
    activo.value = !!data.subscribed
    tieneCorreo.value = !!data.tiene_correo
  } catch {
    avisar('No se pudo consultar tu preferencia.', 'error')
  } finally {
    cargado.value = true
  }
})

// Se guarda al instante; si el servidor falla, el interruptor vuelve a su estado anterior
async function cambiar() {
  if (!puede.value || guardando.value) return
  const nuevo = !activo.value
  activo.value = nuevo
  guardando.value = true
  try {
    await axios.patch('/api/users/me/email-preferences', { enabled: nuevo })
    avisar(nuevo ? 'Listo: recibirás los informes en tu correo.' : 'Desactivado: ya no recibirás informes.')
  } catch (e) {
    activo.value = !nuevo
    avisar(e.response?.data?.detail || 'No se pudo guardar. Intenta de nuevo.', 'error')
  } finally {
    guardando.value = false
  }
}
</script>

<style scoped>
.ep { padding: 10px 14px; }
.ep-fila { display: flex; align-items: center; justify-content: space-between; gap: 12px; cursor: pointer; }
.ep-fila--off { cursor: default; opacity: .75; }
.ep-texto { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ep-texto strong { font-size: 13px; color: var(--text); }
.ep-texto small { font-size: 11.5px; line-height: 1.35; color: var(--text-muted); }
.ep--oscuro .ep-texto strong { color: #fff; }
.ep--oscuro .ep-texto small { color: rgba(255,255,255,.65); }

.ep-sw {
  flex: none; position: relative; width: 42px; height: 24px; border-radius: 999px; border: none; padding: 0;
  background: #c5d3cc; cursor: pointer; transition: background .2s;
}
.ep-sw--on { background: var(--accent); }
.ep-sw:disabled { cursor: not-allowed; opacity: .6; }
.ep-sw:focus-visible { outline: 2px solid var(--secondary); outline-offset: 2px; }
.ep-knob { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.3); transition: transform .2s; }
.ep-sw--on .ep-knob { transform: translateX(18px); }

.ep-msg { margin: 8px 0 0; font-size: 11.5px; font-weight: 600; }
.ep-msg--ok { color: var(--accent-hover); }
.ep-msg--error { color: var(--danger); }
@media (prefers-reduced-motion: reduce) { .ep-sw, .ep-knob { transition: none; } }
</style>
