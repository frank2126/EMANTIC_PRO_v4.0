<template>
  <footer class="ft" aria-label="Pie de página">
    <div class="ft-main">

      <!-- Izquierda: marca -->
      <section class="ft-marca">
        <div class="ft-logo">
          <img src="/icons/icon-192.png" alt="EMANTIC" class="ft-logo-img" />
          <div>
            <div class="ft-logo-n">EMANTIC</div>
            <div class="ft-logo-s">SISTEMA TÉCNICO</div>
          </div>
        </div>
        <p class="ft-texto">
          <strong>CENTRALIZACIÓN TÉCNICA:</strong> Plataforma unificada para la gestión de datos técnicos y análisis de
          mantenimiento de flotas de transporte masivo. Optimiza la toma de decisiones con información precisa y centralizada.
        </p>
      </section>

      <!-- Derecha: solicitud al Centro de Gestión -->
      <section class="ft-form" aria-labelledby="ft-form-t">
        <h2 id="ft-form-t">MANTENTE AL DÍA</h2>
        <p class="ft-texto">
          ¿Necesitas información detallada de una novedad de mantenimiento, un informe o el estado de tus móviles?
          Solicítala aquí con un párrafo corto y el Centro de Gestión la atenderá lo más rápido posible.
        </p>

        <form class="ft-sol" novalidate @submit.prevent="enviar">
          <fieldset class="ft-tipos" :disabled="cargando">
            <legend>¿Qué necesitas?</legend>
            <div class="ft-chips" role="radiogroup" aria-label="Tipo de información">
              <button v-for="t in TIPOS" :key="t.key" type="button" role="radio" class="ft-chip"
                      :class="{ 'ft-chip--on': tipo === t.key }" :aria-checked="tipo === t.key" @click="tipo = t.key">
                {{ t.corto }}
              </button>
            </div>
          </fieldset>
          <p v-if="tocado && errores.tipo" class="ft-err" role="alert">{{ errores.tipo }}</p>

          <div class="ft-fila">
            <div class="ft-campo ft-campo--movil">
              <label for="ft-movil">Móvil <small>(opcional)</small></label>
              <input id="ft-movil" v-model="movil" type="text" maxlength="30" autocomplete="off" placeholder="Ej: Z32-7036"
                     class="ft-input" :class="{ 'ft-input--err': tocado && errores.movil }" :disabled="cargando" />
            </div>
            <label class="ft-urgente">
              <input v-model="urgente" type="checkbox" :disabled="cargando" />
              <span>Es urgente</span>
            </label>
          </div>
          <p v-if="tocado && errores.movil" class="ft-err" role="alert">{{ errores.movil }}</p>

          <div class="ft-campo">
            <label for="ft-msg">Tu solicitud</label>
            <textarea id="ft-msg" v-model="mensaje" rows="3" :maxlength="MAX_MENSAJE" class="ft-input ft-area"
                      :class="{ 'ft-input--err': tocado && errores.mensaje }" :placeholder="hint" :disabled="cargando"></textarea>
            <div class="ft-pie-campo">
              <span v-if="tocado && errores.mensaje" class="ft-err" role="alert">{{ errores.mensaje }}</span>
              <span v-else></span>
              <span class="ft-cuenta" :class="{ 'ft-cuenta--alerta': faltan < 40 }">{{ faltan }} caracteres</span>
            </div>
          </div>

          <div class="ft-acciones">
            <button type="submit" class="ft-btn" :disabled="cargando">
              <span v-if="cargando" class="ft-spin" aria-hidden="true"></span>
              {{ cargando ? 'Enviando…' : 'Enviar solicitud' }}
            </button>
            <button type="button" class="ft-btn ft-btn--sec" @click="panel = true">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Panel de respuestas
              <span v-if="insignia" class="ft-badge" :aria-label="insignia + ' novedades'">{{ insignia }}</span>
            </button>
          </div>
        </form>

        <p v-if="aviso.texto" class="ft-aviso" :class="'ft-aviso--' + aviso.tipo" role="status" aria-live="polite">
          <span aria-hidden="true">{{ aviso.tipo === 'ok' ? '✔' : '⚠' }}</span> {{ aviso.texto }}
        </p>
      </section>
    </div>

    <!-- Franja inferior -->
    <div class="ft-barra">
      <div class="ft-barra-in">
        <span class="ft-copy">© {{ anio }} EMANTIC. Todos los derechos reservados. <span class="ft-dim">Centralización Técnica de Flotas.</span></span>
        <span class="ft-estado" :title="estado.detalle">
          Estado del Sistema: <span class="ft-punto" :class="'ft-punto--' + estado.nivel"></span>
          <strong :class="'ft-e--' + estado.nivel">{{ estado.texto }}</strong>
          <span class="ft-sep">|</span>
          <button type="button" class="ft-link ft-link--tenue" @click="mapa = true">Mapa del sitio</button>
        </span>
        <time class="ft-fecha" :datetime="ahora.toISOString()">{{ fechaTxt }}</time>
      </div>
    </div>

    <!-- Panel de respuestas -->
    <PanelSolicitudes :abierto="panel" :es-admin="admin" @cerrar="panel = false" @cambio="cargarResumen" />

    <!-- Mapa del sitio -->
    <div v-if="mapa" class="ft-modal" role="dialog" aria-modal="true" aria-label="Mapa del sitio" @click.self="mapa = false" @keydown.esc="mapa = false">
      <div class="ft-modal-caja" tabindex="-1" ref="caja">
        <header><h3>Mapa del sitio</h3><button type="button" class="ft-x" aria-label="Cerrar" @click="mapa = false">✕</button></header>
        <ul class="ft-mapa">
          <li v-for="s in secciones" :key="s.to"><router-link :to="s.to" @click="mapa = false">{{ s.label }}</router-link></li>
        </ul>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'
import PanelSolicitudes from './PanelSolicitudes.vue'
import { TIPOS, TIPO_POR_CLAVE, MAX_MENSAJE, restantes, validarSolicitud, limpiar, normalizarMovil, mensajeDeError } from '../utils/solicitudesUtils.js'

const { isAdmin } = useAuth()
const admin = computed(() => isAdmin())

// ── Formulario de solicitud ──
const tipo = ref('')
const movil = ref('')
const mensaje = ref('')
const urgente = ref(false)
const tocado = ref(false)
const cargando = ref(false)
const aviso = reactive({ texto: '', tipo: 'ok' })

const errores = computed(() => validarSolicitud({ tipo: tipo.value, mensaje: mensaje.value, movil: movil.value }).errores)
const faltan = computed(() => restantes(mensaje.value))
const hint = computed(() => TIPO_POR_CLAVE[tipo.value]?.hint || 'Cuéntanos en un párrafo corto qué necesitas…')

let tAviso = null
function avisar(texto, t) {
  aviso.texto = texto; aviso.tipo = t
  clearTimeout(tAviso)
  tAviso = setTimeout(() => { aviso.texto = '' }, 8000)
}

async function enviar() {
  tocado.value = true
  aviso.texto = ''
  if (Object.keys(errores.value).length) return
  cargando.value = true
  try {
    const { data } = await axios.post('/api/solicitudes', {
      tipo: tipo.value, mensaje: limpiar(mensaje.value), movil: normalizarMovil(movil.value), prioridad: urgente.value ? 'urgente' : 'normal',
    })
    avisar(data.message || 'Solicitud enviada.', 'ok')
    tipo.value = ''; movil.value = ''; mensaje.value = ''; urgente.value = false; tocado.value = false
    cargarResumen()
  } catch (e) {
    avisar(mensajeDeError(e, 'No se pudo enviar la solicitud.'), 'error')
  } finally {
    cargando.value = false
  }
}

// ── Insignia del panel: respuestas sin leer (y, para el admin, solicitudes pendientes) ──
const panel = ref(false)
const resumen = reactive({ sin_leer: 0, pendientes: 0 })
const insignia = computed(() => resumen.sin_leer + (admin.value ? resumen.pendientes : 0))
async function cargarResumen() {
  try {
    const { data } = await axios.get('/api/solicitudes/resumen')
    resumen.sin_leer = data.sin_leer || 0
    resumen.pendientes = data.pendientes || 0
  } catch { /* la insignia es opcional: si falla, se queda como estaba */ }
}

// ── Franja inferior: fecha y estado del sistema (consulta real a /api/health) ──
const ahora = ref(new Date())
const anio = computed(() => ahora.value.getFullYear())
const fechaTxt = computed(() => {
  const f = ahora.value
  const dia = f.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
  const hora = f.toLocaleTimeString('es-CO', { hour: 'numeric', minute: '2-digit', hour12: true })
  return `${dia.charAt(0).toUpperCase() + dia.slice(1)} | ${hora}`
})

const estado = reactive({ nivel: 'cargando', texto: 'Verificando…', detalle: '' })
async function revisarEstado() {
  try {
    const { data } = await axios.get('/api/health', { timeout: 5000 })
    const ok = data?.status === 'healthy'
    Object.assign(estado, ok ? { nivel: 'ok', texto: 'Operativo', detalle: 'El servidor responde con normalidad' }
                             : { nivel: 'warn', texto: 'Degradado', detalle: 'El servidor respondió con advertencias' })
  } catch (e) {
    Object.assign(estado, e.response ? { nivel: 'warn', texto: 'Degradado', detalle: 'El servidor respondió con error' }
                                     : { nivel: 'bad', texto: 'Sin conexión', detalle: 'No se pudo contactar al servidor' })
  }
}

let relojT = null, estadoT = null
onMounted(() => {
  revisarEstado()
  cargarResumen()
  relojT = setInterval(() => { ahora.value = new Date() }, 15000)
  estadoT = setInterval(() => { revisarEstado(); cargarResumen() }, 60000)
})
onUnmounted(() => { clearInterval(relojT); clearInterval(estadoT); clearTimeout(tAviso) })

// ── Mapa del sitio ──
const mapa = ref(false)
const caja = ref(null)
watch(mapa, async m => { if (m) { await nextTick(); caja.value?.focus() } })
const secciones = computed(() => [
  { to: '/dashboard', label: 'Dashboard' }, { to: '/manuals', label: 'Manuales' }, { to: '/maintenance', label: 'Mantenimiento' },
  { to: '/documentation', label: 'Documentación' }, { to: '/resources', label: 'Recursos Taller' }, { to: '/analytics', label: 'Analíticas' },
  { to: '/reportes', label: 'Reportes' }, { to: '/dpv', label: 'Carga DPV' }, { to: '/ico', label: 'ICO' },
  ...(admin.value ? [{ to: '/users', label: 'Usuarios' }] : []),
])
</script>

<style scoped>
.ft { background: #0B0F19; color: #cbd5e1; margin-top: 8px; border-top: 1px solid rgba(49, 176, 121, .25); }
.ft-main {
  max-width: 1200px; margin: 0 auto; padding: 36px clamp(16px, 3vw, 32px) 28px;
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.5fr); gap: clamp(24px, 5vw, 64px);
}
.ft-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.ft-logo-img { width: 44px; height: 44px; border-radius: 10px; }
.ft-logo-n { color: #fff; font-weight: 800; letter-spacing: 2px; font-size: 20px; line-height: 1.1; }
.ft-logo-s { color: var(--accent); font-size: 10px; letter-spacing: 3px; font-weight: 600; margin-top: 2px; }
.ft-texto { margin: 0; font-size: 13.5px; line-height: 1.65; color: #94a3b8; }
.ft-texto strong { color: #e2e8f0; }

.ft-form h2 { margin: 0 0 10px; font-size: 14px; letter-spacing: 2px; color: #fff; font-weight: 800; padding-left: 10px; border-left: 3px solid var(--accent); }
.ft-sol { margin-top: 14px; display: flex; flex-direction: column; gap: 12px; }
.ft-tipos { border: none; padding: 0; margin: 0; min-width: 0; }
.ft-tipos legend { padding: 0; margin-bottom: 8px; font-size: 12px; font-weight: 700; letter-spacing: .5px; color: #cbd5e1; }
.ft-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ft-chip {
  padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(255,255,255,.16); background: rgba(255,255,255,.04);
  color: #cbd5e1; font: inherit; font-size: 12.5px; cursor: pointer; transition: background .15s, border-color .15s, color .15s;
}
.ft-chip:hover { border-color: var(--accent); color: #fff; }
.ft-chip--on { background: rgba(49,176,121,.2); border-color: var(--accent); color: #7ee2b4; font-weight: 700; }
.ft-chip:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.ft-fila { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.ft-campo { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.ft-campo--movil { width: 220px; max-width: 100%; }
.ft-campo label { font-size: 12px; font-weight: 700; letter-spacing: .5px; color: #cbd5e1; }
.ft-campo label small { font-weight: 400; color: #94a3b8; }
.ft-input {
  width: 100%; box-sizing: border-box; padding: 10px 13px; border-radius: 8px; border: 1px solid rgba(255,255,255,.14);
  background: #fff; color: #0f172a; font: inherit; font-size: 14px;
}
.ft-input::placeholder { color: #94a3b8; }
.ft-input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.ft-input--err { border-color: #f87171; }
.ft-area { resize: vertical; min-height: 78px; line-height: 1.5; }
.ft-pie-campo { display: flex; justify-content: space-between; gap: 12px; min-height: 16px; }
.ft-cuenta { font-size: 11.5px; color: #64748b; margin-left: auto; }
.ft-cuenta--alerta { color: #fcd34d; }
.ft-urgente { display: inline-flex; align-items: center; gap: 8px; padding-bottom: 10px; font-size: 13px; color: #cbd5e1; cursor: pointer; }
.ft-urgente input { width: 15px; height: 15px; accent-color: #f59e0b; }

.ft-acciones { display: flex; gap: 10px; flex-wrap: wrap; }
.ft-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 11px 22px; border-radius: 8px; border: none;
  background: var(--accent); color: #04281c; font: inherit; font-weight: 800; font-size: 14px; cursor: pointer; transition: filter .15s, transform .05s;
}
.ft-btn:hover:not(:disabled) { filter: brightness(1.08); }
.ft-btn:active:not(:disabled) { transform: translateY(1px); }
.ft-btn:disabled { opacity: .7; cursor: wait; }
.ft-btn:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
.ft-btn--sec { background: transparent; color: #e2e8f0; border: 1px solid rgba(255,255,255,.22); font-weight: 600; position: relative; }
.ft-btn--sec:hover:not(:disabled) { background: rgba(255,255,255,.08); filter: none; }
.ft-badge { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #ef4444; color: #fff; font-size: 11px; font-weight: 800; display: inline-grid; place-items: center; }
.ft-spin { width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(4,40,28,.3); border-top-color: #04281c; animation: ft-r .7s linear infinite; }
@keyframes ft-r { to { transform: rotate(360deg); } }

.ft-link { background: none; border: none; padding: 0; font: inherit; color: var(--accent); cursor: pointer; }
.ft-link--tenue { color: #94a3b8; }
.ft-link--tenue:hover { color: #fff; text-decoration: underline; }
.ft-err { margin: 0; font-size: 12px; color: #fca5a5; }
.ft-aviso { margin: 12px 0 0; padding: 9px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; }
.ft-aviso--ok { background: rgba(49,176,121,.14); color: #7ee2b4; border: 1px solid rgba(49,176,121,.35); }
.ft-aviso--error { background: rgba(248,113,113,.12); color: #fca5a5; border: 1px solid rgba(248,113,113,.35); }

.ft-barra { border-top: 1px solid rgba(255,255,255,.08); background: rgba(0,0,0,.25); }
.ft-barra-in {
  max-width: 1200px; margin: 0 auto; padding: 14px clamp(16px, 3vw, 32px);
  display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 8px 28px; align-items: center; font-size: 12px; color: #94a3b8;
}
.ft-dim { opacity: .75; }
.ft-estado { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.ft-punto { width: 8px; height: 8px; border-radius: 50%; background: #64748b; }
.ft-punto--ok { background: var(--accent); box-shadow: 0 0 0 3px rgba(49,176,121,.25); }
.ft-punto--warn { background: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,.25); }
.ft-punto--bad { background: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,.25); }
.ft-e--ok { color: #7ee2b4; } .ft-e--warn { color: #fcd34d; } .ft-e--bad { color: #fca5a5; } .ft-e--cargando { color: #94a3b8; }
.ft-sep { opacity: .4; }
.ft-fecha { white-space: nowrap; }

.ft-modal { position: fixed; inset: 0; z-index: 300; background: rgba(2,6,23,.6); display: grid; place-items: center; padding: 16px; }
.ft-modal-caja { background: #fff; color: var(--text); width: min(520px, 100%); max-height: 80vh; border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 20px 50px rgba(0,0,0,.4); outline: none; }
.ft-modal-caja header { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: var(--primary); color: #fff; }
.ft-modal-caja h3 { margin: 0; font-size: 16px; }
.ft-x { background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; border-radius: 6px; padding: 4px 8px; }
.ft-x:hover { background: rgba(255,255,255,.15); }
.ft-mapa { list-style: none; margin: 0; padding: 18px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; overflow: auto; }
.ft-mapa a { display: block; padding: 10px 12px; border-radius: 8px; background: var(--surface-2); border: 1px solid var(--border); color: var(--primary); font-weight: 600; text-decoration: none; }
.ft-mapa a:hover { background: var(--primary-light); }

@media (max-width: 860px) {
  .ft-main { grid-template-columns: 1fr; padding-top: 28px; }
  .ft-barra-in { grid-template-columns: 1fr; text-align: left; }
}
@media (max-width: 520px) {
  .ft-campo--movil { width: 100%; }
  .ft-acciones .ft-btn { flex: 1 1 100%; }
  .ft-mapa { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) { .ft-spin { animation: none; } .ft-btn, .ft-chip { transition: none; } }
</style>
