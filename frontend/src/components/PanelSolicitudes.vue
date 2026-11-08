<template>
  <transition name="ps">
    <div v-if="abierto" class="ps-fondo" @click.self="$emit('cerrar')" @keydown.esc="$emit('cerrar')">
      <aside ref="caja" class="ps" role="dialog" aria-modal="true" aria-label="Panel de respuestas" tabindex="-1">

        <header class="ps-head">
          <div>
            <h3>Panel de respuestas</h3>
            <p>Centro de Gestión · solicitudes y respuestas</p>
          </div>
          <button type="button" class="ps-x" aria-label="Cerrar panel" @click="$emit('cerrar')">✕</button>
        </header>

        <div v-if="esAdmin" class="ps-tabs" role="tablist">
          <button type="button" role="tab" class="ps-tab" :class="{ 'ps-tab--on': vista === 'mias' }" :aria-selected="vista === 'mias'" @click="cambiarVista('mias')">Mis solicitudes</button>
          <button type="button" role="tab" class="ps-tab" :class="{ 'ps-tab--on': vista === 'bandeja' }" :aria-selected="vista === 'bandeja'" @click="cambiarVista('bandeja')">
            Bandeja del Centro <span v-if="conteo.pendiente" class="ps-cnt">{{ conteo.pendiente }}</span>
          </button>
        </div>

        <div v-if="vista === 'bandeja'" class="ps-filtros" role="group" aria-label="Filtrar por estado">
          <button type="button" class="ps-f" :class="{ 'ps-f--on': filtro === '' }" @click="setFiltro('')">Todas</button>
          <button v-for="e in ESTADOS" :key="e.key" type="button" class="ps-f" :class="{ 'ps-f--on': filtro === e.key }" @click="setFiltro(e.key)">
            {{ e.label }} <small>{{ conteo[e.key] || 0 }}</small>
          </button>
        </div>

        <div class="ps-cuerpo">
          <p v-if="cargando" class="ps-info">Cargando…</p>
          <p v-else-if="error" class="ps-info ps-info--err" role="alert">{{ error }}</p>
          <p v-else-if="!items.length" class="ps-info">
            {{ vista === 'mias' ? 'Aún no has enviado solicitudes. Usa el formulario del pie de página para pedir información al Centro de Gestión.' : 'No hay solicitudes en esta vista.' }}
          </p>

          <ul v-else class="ps-lista">
            <li v-for="s in items" :key="s.id" class="ps-item" :class="{ 'ps-item--nuevo': s.sin_leer && vista === 'mias', 'ps-item--urg': s.prioridad === 'urgente' && s.estado !== 'cerrada' }">
              <div class="ps-top">
                <span class="ps-num">#{{ s.id }}</span>
                <span class="ps-tipo">{{ s.tipo_label }}</span>
                <span class="ps-estado" :class="'ps-e--' + claseEstado(s.estado)">{{ labelEstado(s.estado) }}</span>
              </div>
              <div class="ps-meta">
                <span v-if="s.sin_leer && vista === 'mias'" class="ps-nuevo">NUEVA RESPUESTA</span>
                <span v-if="s.prioridad === 'urgente'" class="ps-urg">URGENTE</span>
                <span v-if="s.movil">Móvil {{ s.movil }}</span>
                <span v-if="vista === 'bandeja' && s.solicitante">{{ s.solicitante }}</span>
                <span>{{ haceCuanto(s.created_at) }}</span>
              </div>
              <p class="ps-msg">{{ s.mensaje }}</p>

              <div v-if="s.respuesta" class="ps-resp">
                <div class="ps-resp-h"><strong>Centro de Gestión<template v-if="s.respondido_por"> · {{ s.respondido_por }}</template></strong><small>{{ haceCuanto(s.respondido_at) }}</small></div>
                <p>{{ s.respuesta }}</p>
              </div>
              <p v-else-if="vista === 'mias'" class="ps-espera">Esperando respuesta del Centro de Gestión…</p>

              <div v-if="vista === 'bandeja' && borrador[s.id]" class="ps-gestion">
                <label :for="'ps-r-' + s.id">{{ s.respuesta ? 'Editar respuesta' : 'Responder' }}</label>
                <textarea :id="'ps-r-' + s.id" v-model="borrador[s.id].respuesta" rows="3" maxlength="4000" placeholder="Escribe la respuesta para el solicitante…"></textarea>
                <div class="ps-gfila">
                  <select v-model="borrador[s.id].estado" :aria-label="'Estado de la solicitud ' + s.id">
                    <option v-for="e in ESTADOS" :key="e.key" :value="e.key">{{ e.label }}</option>
                  </select>
                  <button type="button" class="ps-guardar" :disabled="guardando === s.id" @click="guardar(s)">{{ guardando === s.id ? 'Guardando…' : 'Guardar' }}</button>
                </div>
                <p v-if="mensajes[s.id]" class="ps-gmsg" :class="'ps-gmsg--' + mensajes[s.id].tipo" role="status">{{ mensajes[s.id].texto }}</p>
              </div>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import axios from 'axios'
import { ESTADOS, ESTADO_POR_CLAVE, haceCuanto, limpiar, mensajeDeError } from '../utils/solicitudesUtils.js'

const props = defineProps({ abierto: { type: Boolean, default: false }, esAdmin: { type: Boolean, default: false } })
const emit = defineEmits(['cerrar', 'cambio'])

const vista = ref('mias')            // 'mias' | 'bandeja' (solo admin)
const filtro = ref('')
const items = ref([])
const conteo = reactive({ pendiente: 0, en_proceso: 0, atendida: 0, cerrada: 0 })
const cargando = ref(false)
const error = ref('')
const guardando = ref(0)
const borrador = reactive({})        // lo que el admin va escribiendo, por id de solicitud
const mensajes = reactive({})
const caja = ref(null)

const labelEstado = k => ESTADO_POR_CLAVE[k]?.label || k
const claseEstado = k => ESTADO_POR_CLAVE[k]?.clase || 'pend'

async function cargar(silencioso = false) {
  if (!silencioso) cargando.value = true
  error.value = ''
  try {
    if (vista.value === 'mias') {
      const { data } = await axios.get('/api/solicitudes/mias')
      items.value = data.items || []
      if (data.sin_leer) {            // al abrir el panel las respuestas pasan a «leídas» (aquí siguen resaltadas)
        try { await axios.post('/api/solicitudes/mias/vistas') } catch { /* no es crítico */ }
        emit('cambio')
      }
    } else {
      const { data } = await axios.get('/api/solicitudes/bandeja', { params: filtro.value ? { estado: filtro.value } : {} })
      items.value = data.items || []
      Object.assign(conteo, { pendiente: 0, en_proceso: 0, atendida: 0, cerrada: 0 }, data.conteo || {})
      for (const s of items.value) {
        if (!borrador[s.id]) borrador[s.id] = { respuesta: s.respuesta || '', estado: s.estado }
      }
    }
  } catch (e) {
    error.value = mensajeDeError(e, 'No se pudo cargar el panel.')
  } finally {
    cargando.value = false
  }
}

watch(() => props.abierto, async a => {
  if (!a) return
  vista.value = 'mias'; filtro.value = ''
  cargar()
  if (props.esAdmin) {                // para que la pestaña muestre cuántas pendientes hay sin entrar a ella
    try { const { data } = await axios.get('/api/solicitudes/bandeja', { params: { estado: 'pendiente' } }); conteo.pendiente = data.conteo?.pendiente || 0 } catch { /* opcional */ }
  }
  await nextTick(); caja.value?.focus()
})

function cambiarVista(v) { if (vista.value !== v) { vista.value = v; filtro.value = ''; cargar() } }
function setFiltro(f) { filtro.value = f; cargar() }

async function guardar(s) {
  const b = borrador[s.id]
  const cambios = {}
  if (limpiar(b.respuesta) !== (s.respuesta || '')) cambios.respuesta = b.respuesta
  if (b.estado !== s.estado) cambios.estado = b.estado
  if (!Object.keys(cambios).length) { mensajes[s.id] = { tipo: 'error', texto: 'No hay cambios para guardar.' }; return }
  guardando.value = s.id
  mensajes[s.id] = null
  try {
    const { data } = await axios.patch(`/api/solicitudes/${s.id}`, cambios)
    borrador[s.id] = { respuesta: data.item.respuesta || '', estado: data.item.estado }
    mensajes[s.id] = { tipo: 'ok', texto: cambios.respuesta ? 'Respuesta enviada al solicitante.' : 'Estado actualizado.' }
    await cargar(true)
    emit('cambio')
  } catch (e) {
    mensajes[s.id] = { tipo: 'error', texto: mensajeDeError(e, 'No se pudo guardar.') }
  } finally {
    guardando.value = 0
  }
}
</script>

<style scoped>
.ps-fondo { position: fixed; inset: 0; z-index: 310; background: rgba(2, 6, 23, .55); display: flex; justify-content: flex-end; }
.ps { background: var(--surface, #fff); color: var(--text); width: min(480px, 100%); height: 100%; display: flex; flex-direction: column; box-shadow: -12px 0 40px rgba(0,0,0,.35); outline: none; }
.ps-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 16px 18px; background: var(--primary); color: #fff; }
.ps-head h3 { margin: 0; font-size: 17px; }
.ps-head p { margin: 2px 0 0; font-size: 12px; color: rgba(255,255,255,.7); }
.ps-x { background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; border-radius: 6px; padding: 4px 8px; }
.ps-x:hover { background: rgba(255,255,255,.15); }

.ps-tabs { display: flex; border-bottom: 1px solid var(--border); }
.ps-tab { flex: 1; padding: 12px 10px; border: none; background: none; font: inherit; font-size: 13px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 3px solid transparent; }
.ps-tab--on { color: var(--primary); border-bottom-color: var(--accent); }
.ps-cnt { margin-left: 4px; padding: 1px 7px; border-radius: 999px; background: #ef4444; color: #fff; font-size: 11px; font-weight: 800; }

.ps-filtros { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 14px; border-bottom: 1px solid var(--border); background: var(--surface-2); }
.ps-f { padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border); background: #fff; font: inherit; font-size: 12px; color: var(--text-muted); cursor: pointer; }
.ps-f small { opacity: .7; margin-left: 2px; }
.ps-f--on { background: var(--primary); border-color: var(--primary); color: #fff; }

.ps-cuerpo { flex: 1; overflow-y: auto; padding: 14px; background: var(--bg); }
.ps-info { margin: 24px 6px; text-align: center; font-size: 13.5px; line-height: 1.6; color: var(--text-muted); }
.ps-info--err { color: var(--danger); }
.ps-lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }

.ps-item { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; }
.ps-item--urg { border-left: 4px solid #f59e0b; }
.ps-item--nuevo { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(49,176,121,.18); }
.ps-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ps-num { font-weight: 800; color: var(--primary); }
.ps-tipo { font-size: 13px; font-weight: 600; flex: 1; min-width: 0; }
.ps-estado { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.ps-e--pend { background: #fff4d6; color: #8a5a00; }
.ps-e--proc { background: #ddeef8; color: #074e7a; }
.ps-e--ok   { background: #d4f1e4; color: #0a5c3b; }
.ps-e--cerr { background: #e5e7eb; color: #4b5563; }
.ps-meta { display: flex; flex-wrap: wrap; gap: 4px 10px; margin: 6px 0 8px; font-size: 11.5px; color: var(--text-muted); }
.ps-urg { color: #b45309; font-weight: 800; }
.ps-nuevo { color: #0a7a4d; font-weight: 800; }
.ps-msg { margin: 0; font-size: 13.5px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; }
.ps-resp { margin-top: 10px; padding: 10px 12px; border-radius: 10px; background: var(--primary-light); border-left: 3px solid var(--accent); }
.ps-resp-h { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--primary); }
.ps-resp-h small { color: var(--text-muted); }
.ps-resp p { margin: 6px 0 0; font-size: 13.5px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; }
.ps-espera { margin: 10px 0 0; font-size: 12.5px; color: var(--text-muted); font-style: italic; }

.ps-gestion { margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--border); display: flex; flex-direction: column; gap: 6px; }
.ps-gestion label { font-size: 12px; font-weight: 700; color: var(--text-muted); }
.ps-gestion textarea, .ps-gestion select { width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font: inherit; font-size: 13px; background: #fff; color: var(--text); }
.ps-gestion textarea { resize: vertical; min-height: 64px; }
.ps-gfila { display: flex; gap: 8px; }
.ps-gfila select { flex: 1; }
.ps-guardar { padding: 8px 18px; border: none; border-radius: 8px; background: var(--primary); color: #fff; font: inherit; font-weight: 700; font-size: 13px; cursor: pointer; }
.ps-guardar:hover:not(:disabled) { background: var(--primary-dark); }
.ps-guardar:disabled { opacity: .6; cursor: wait; }
.ps-gmsg { margin: 0; font-size: 12px; font-weight: 600; }
.ps-gmsg--ok { color: var(--accent-hover); }
.ps-gmsg--error { color: var(--danger); }

.ps-enter-active, .ps-leave-active { transition: opacity .2s; }
.ps-enter-active .ps, .ps-leave-active .ps { transition: transform .25s ease; }
.ps-enter-from, .ps-leave-to { opacity: 0; }
.ps-enter-from .ps, .ps-leave-to .ps { transform: translateX(100%); }
@media (prefers-reduced-motion: reduce) { .ps-enter-active, .ps-leave-active, .ps-enter-active .ps, .ps-leave-active .ps { transition: none; } }
</style>
