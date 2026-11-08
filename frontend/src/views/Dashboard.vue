<template>
  <div class="page dash-page">

    <!-- ── CABECERA ── -->
    <div class="dash-header">
      <div class="brand-block">
        <svg viewBox="0 0 40 40" width="36" height="36">
          <rect width="40" height="40" rx="9" fill="var(--accent)"/>
          <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
            font-size="14" font-weight="900" fill="#fff" font-family="Inter, Arial">E</text>
        </svg>
        <span class="brand-name">.emasivo</span>
      </div>

      <div class="header-centro">
        <div class="header-titulo">
          <span class="t-desk">{{ tituloHeader }}</span>
          <span class="t-mob">Panel de control general</span>
        </div>
        <div class="header-sub">EMASIVO 10 / 16</div>
      </div>

      <div class="header-meta">
        <span class="fecha-badge">{{ fechaHoy }}<span class="hora-mob"> | {{ horaActual }}</span></span>
      </div>
    </div>

    <!-- ── TABS (en celular se vuelven tarjetas) ── -->
    <div class="tab-bar">
      <div class="tab-scroll" role="tablist" aria-label="Secciones del panel">
        <button class="tab-btn tab-btn--dpv" :class="{active: activeTab==='dpv'}" role="tab" :aria-selected="activeTab==='dpv'" @click="activeTab='dpv'">
          <span class="tab-ico" aria-hidden="true">
          <svg class="ic" viewBox="0 0 48 48" focusable="false">
            <defs><linearGradient id="icDpv" x1="8" y1="0" x2="40" y2="48" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#3ee0a5"/><stop offset="1" stop-color="#05905f"/></linearGradient></defs>
            <rect width="48" height="48" rx="12" fill="url(#icDpv)"/>
            <path d="M0 12a12 12 0 0 1 12-12h24a12 12 0 0 1 12 12v8C34 25 14 25 0 20z" fill="#fff" opacity=".16"/>
            <rect x="13" y="12" width="22" height="26" rx="4.5" fill="#fff"/>
            <rect x="18" y="8.5" width="12" height="7.5" rx="3" fill="#fff" stroke="#0a9a68" stroke-width="2"/>
            <path d="m18.2 26 4.2 4.2 7.6-8.4" fill="none" stroke="#0a9a68" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
          <span class="tab-lbl">DPV</span>
        </button>
        <button class="tab-btn tab-btn--ico" :class="{active: activeTab==='ico'}" role="tab" :aria-selected="activeTab==='ico'" @click="activeTab='ico'">
          <span class="tab-ico" aria-hidden="true">
          <svg class="ic" viewBox="0 0 48 48" focusable="false">
            <defs>
              <linearGradient id="icoBg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#2a3140"/><stop offset="1" stop-color="#0d1117"/></linearGradient>
              <linearGradient id="icoA" x1="0" y1="11" x2="0" y2="37" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#2fd37a"/><stop offset=".5" stop-color="#f2c40f"/><stop offset="1" stop-color="#f08a1c"/></linearGradient>
              <linearGradient id="icoB" x1="24" y1="0" x2="11" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#f08a1c"/><stop offset="1" stop-color="#e8493f"/></linearGradient>
            </defs>
            <rect width="48" height="48" rx="12" fill="url(#icoBg)"/>
            <circle cx="24" cy="24" r="12.5" fill="none" stroke="#fff" stroke-opacity=".1" stroke-width="5"/>
            <path d="M24 11.5A12.5 12.5 0 0 1 24 36.5" fill="none" stroke="url(#icoA)" stroke-width="5" stroke-linecap="round"/>
            <path d="M24 36.5A12.5 12.5 0 0 1 11.5 24" fill="none" stroke="url(#icoB)" stroke-width="5" stroke-linecap="round"/>
            <circle cx="24" cy="24" r="5" fill="#2fd37a"/>
          </svg>
        </span>
          <span class="tab-lbl">ICO</span>
        </button>
        <button class="tab-btn tab-btn--disp" :class="{active: activeTab==='disponibilidad'}" role="tab" :aria-selected="activeTab==='disponibilidad'" @click="activeTab='disponibilidad'">
          <span class="tab-ico" aria-hidden="true">
          <svg class="ic" viewBox="0 0 48 48" focusable="false">
            <defs><linearGradient id="icBus" x1="8" y1="0" x2="40" y2="48" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5aa9ff"/><stop offset="1" stop-color="#1b4fd1"/></linearGradient></defs>
            <rect width="48" height="48" rx="12" fill="url(#icBus)"/>
            <path d="M0 12a12 12 0 0 1 12-12h24a12 12 0 0 1 12 12v8C34 25 14 25 0 20z" fill="#fff" opacity=".16"/>
            <rect x="12.5" y="9" width="23" height="26" rx="5.5" fill="#fff"/>
            <rect x="16" y="13" width="16" height="9" rx="2.4" fill="#2a63dc"/>
            <circle cx="18.2" cy="29.2" r="2.1" fill="#2a63dc"/><circle cx="29.8" cy="29.2" r="2.1" fill="#2a63dc"/>
            <rect x="16" y="34.5" width="4.5" height="4.5" rx="1.8" fill="#fff"/><rect x="27.5" y="34.5" width="4.5" height="4.5" rx="1.8" fill="#fff"/>
          </svg>
        </span>
          <span class="tab-lbl">Disponibilidad</span>
        </button>
        <button class="tab-btn tab-btn--inmov" :class="{active: activeTab==='inmovilizados'}" role="tab" :aria-selected="activeTab==='inmovilizados'" @click="activeTab='inmovilizados'">
          <span class="tab-ico" aria-hidden="true">
          <svg class="ic" viewBox="0 0 48 48" focusable="false">
            <defs><linearGradient id="icInm" x1="8" y1="0" x2="40" y2="48" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffc23d"/><stop offset="1" stop-color="#ee5a0b"/></linearGradient></defs>
            <rect width="48" height="48" rx="12" fill="url(#icInm)"/>
            <path d="M0 12a12 12 0 0 1 12-12h24a12 12 0 0 1 12 12v8C34 25 14 25 0 20z" fill="#fff" opacity=".16"/>
            <g transform="translate(7.2 7.2) scale(1.4)"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="#fff" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></g>
          </svg>
        </span>
          <span class="tab-lbl">Inmovilizados</span>
        </button>
      </div>

      <!-- ── DISPONIBILIDAD DE FLOTA (solo escritorio; en celular va dentro de su tarjeta) ── -->
      <div class="disp-widget">
        <span class="disp-label">Disponibilidad</span>
        <div class="disp-item">
          <span class="disp-uf">UF-10</span>
          <span class="disp-val" :class="dispClass(store.disponibilidad.e10?.porcentaje)">
            {{ store.disponibilidad.e10 ? store.disponibilidad.e10.porcentaje + '%' : '—' }}
          </span>
        </div>
        <div class="disp-item">
          <span class="disp-uf">UF-16</span>
          <span class="disp-val" :class="dispClass(store.disponibilidad.e16?.porcentaje)">
            {{ store.disponibilidad.e16 ? store.disponibilidad.e16.porcentaje + '%' : '—' }}
          </span>
        </div>
      </div>


    </div>

    <!-- ── ERROR ── -->
    <transition name="fade-slide">
      <div v-if="store.error" class="error-banner">
        <span>⚠️ {{ store.error }}</span>
        <button @click="store.error = null" aria-label="Cerrar">✕</button>
      </div>
    </transition>

    <!-- ── LOADING (solo en recargas; la primera carga usa el skeleton) ── -->
    <transition name="fade-slide">
      <div v-if="store.loading && !primeraCarga" class="loading-banner">
        <div class="spinner"></div>
        <span>Actualizando datos...</span>
      </div>
    </transition>

    <!-- ── CONTENIDO ── -->
    <div ref="contenido" class="dash-contenido">
      <DashboardSkeleton v-if="primeraCarga" />
      <template v-else>
        <DashboardDPV v-show="activeTab === 'dpv'" />
        <DashboardICO v-if="visitados.ico" v-show="activeTab === 'ico'" />
        <DashboardDisponibilidad v-if="visitados.disponibilidad" v-show="activeTab === 'disponibilidad'" />
        <DashboardInmovilizados v-if="visitados.inmovilizados" v-show="activeTab === 'inmovilizados'" />
      </template>
    </div>

    <!-- ── BARRA INFERIOR (solo celular) ── -->
    <nav class="bnav" aria-label="Navegación del panel">
      <button v-for="b in BNAV" :key="b.key" type="button" class="bnav-btn"
        :class="{ on: navActiva === b.key }" :aria-current="navActiva === b.key ? 'true' : undefined"
        @click="irA(b.key)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="b.icono"></svg>
        <span>{{ b.label }}</span>
      </button>
    </nav>

    <!-- ── AJUSTES (hoja inferior, solo celular) ── -->
    <transition name="sheet">
      <div v-if="ajustesAbierto" class="sheet-overlay" @click="cerrarAjustes">
        <div class="sheet" role="dialog" aria-modal="true" aria-label="Ajustes del panel" @click.stop>
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-t">Ajustes del panel</h3>
          <p class="sheet-s">Última actualización: {{ store.lastSync || 'sin datos todavía' }}</p>

          <div class="sheet-disp">
            <div class="disp-item">
              <span class="disp-uf">UF-10</span>
              <span class="disp-val" :class="dispClass(store.disponibilidad.e10?.porcentaje)">
                {{ store.disponibilidad.e10 ? store.disponibilidad.e10.porcentaje + '%' : '—' }}
              </span>
            </div>
            <div class="disp-item">
              <span class="disp-uf">UF-16</span>
              <span class="disp-val" :class="dispClass(store.disponibilidad.e16?.porcentaje)">
                {{ store.disponibilidad.e16 ? store.disponibilidad.e16.porcentaje + '%' : '—' }}
              </span>
            </div>
            <span class="disp-label">Disponibilidad de flota</span>
          </div>

          <button type="button" class="btn-primary sheet-btn" :disabled="store.loading" @click="recargar">
            {{ store.loading ? 'Cargando...' : '🔄 Recargar datos' }}
          </button>
          <button type="button" class="btn-secondary sheet-btn" @click="cerrarAjustes">Cerrar</button>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import DashboardSkeleton from './DashboardSkeleton.vue'
import DashboardDPV from './DashboardDPV.vue'
import DashboardICO from './DashboardICO.vue'
import DashboardDisponibilidad from './DashboardDisponibilidad.vue'
import DashboardInmovilizados from './DashboardInmovilizados.vue'

const store     = useDashboardStore()
const activeTab = ref('dpv')
const contenido = ref(null)
const navActiva = ref('resumen')   // debe declararse ANTES del watch (immediate) que la usa

// Las pestañas ICO, Disponibilidad e Inmovilizados se montan solo la primera vez que se visitan
const visitados = reactive({ ico: false, disponibilidad: false, inmovilizados: false })
watch(activeTab, t => {
  if (t in visitados) visitados[t] = true
  navActiva.value = 'resumen'
}, { immediate: true })

// Skeleton solo mientras llega la primera respuesta
const primeraCarga = computed(() => store.loading && !store.dpvRaw.length)

const fechaHoy = new Date().toLocaleDateString('es-CO', {
  weekday:'long', year:'numeric', month:'long', day:'numeric'
}).replace(/^\w/, c => c.toUpperCase())

// Hora en vivo (solo se muestra en celular, junto a la fecha)
const ahora = ref(new Date())
let relojTimer = null
const horaActual = computed(() => ahora.value.toLocaleTimeString('es-CO', { hour: 'numeric', minute: '2-digit', second: '2-digit' }))

const tituloHeader = computed(() => {
  if (activeTab.value === 'dpv') return 'No. Eventos en Vía'
  if (activeTab.value === 'ico') return 'No. Eventos ICO'
  if (activeTab.value === 'inmovilizados') return 'Móviles Inmovilizados'
  return 'Disponibilidad de Flota'
})

// Color del porcentaje de disponibilidad: verde >=90%, ámbar >=75%, rojo por debajo
const dispClass = (pct) => {
  if (pct == null) return 'disp-na'
  if (pct >= 90) return 'disp-ok'
  if (pct >= 75) return 'disp-warn'
  return 'disp-bad'
}


// ── Barra inferior (celular) ──
const NAV_ICONOS = {
  resumen:  '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/>',
  filtros:  '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
  detalles: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r=".6" fill="currentColor"/>',
  ajustes:  '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
}
const BNAV = [
  { key: 'resumen',  label: 'Resumen',  icono: NAV_ICONOS.resumen },
  { key: 'filtros',  label: 'Filtros',  icono: NAV_ICONOS.filtros },
  { key: 'detalles', label: 'Detalles', icono: NAV_ICONOS.detalles },
  { key: 'ajustes',  label: 'Ajustes',  icono: NAV_ICONOS.ajustes },
]
const ajustesAbierto = ref(false)

// Qué buscar en cada pestaña (se toma el primer elemento visible: las pestañas ocultas usan v-show)
const OBJETIVOS = {
  filtros:  '.slicers, .inm-bar, .unidades-row',
  detalles: '.detalle-card, .tabla-card, .inm-tabla',
}
function primerVisible(selector) {
  const raiz = contenido.value
  if (!raiz) return null
  return [...raiz.querySelectorAll(selector)].find(el => el.offsetParent !== null) || null
}

function irA(key) {
  if (key === 'ajustes') { ajustesAbierto.value = true; navActiva.value = 'ajustes'; return }
  navActiva.value = key
  if (key === 'resumen') { window.scrollTo({ top: 0, behavior: 'smooth' }); return }
  const el = primerVisible(OBJETIVOS[key])
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  else window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cerrarAjustes() {
  ajustesAbierto.value = false
  navActiva.value = 'resumen'
}
async function recargar() {
  await store.cargarDatos()
  cerrarAjustes()
}
const onKey = e => { if (e.key === 'Escape' && ajustesAbierto.value) cerrarAjustes() }

// cargarDatos() ya dispara en segundo plano ICO, DPV mensual y disponibilidad
onMounted(() => {
  store.cargarDatos()
  relojTimer = setInterval(() => { ahora.value = new Date() }, 1000)
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  clearInterval(relojTimer)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.dash-page { padding: clamp(12px, 2vw, 32px); }

/* ── CABECERA ── */
.dash-header {
  display: flex; align-items: center; gap: 16px;
  background: var(--nav-gradient);
  border-radius: var(--radius);
  padding: 16px 22px;
  margin-bottom: 14px; flex-wrap: wrap;
  box-shadow: var(--shadow-lg);
}
.brand-block { display:flex; align-items:center; gap:9px; flex-shrink:0; }
.brand-name  { font-size:clamp(16px,2vw,20px); font-weight:900; color:#fff; letter-spacing:-0.5px; }

.header-centro { flex:1 1 200px; text-align:center; min-width: 160px; }
.header-titulo {
  font-size:clamp(13px,1.6vw,17px); font-weight:800; color:#fff;
  letter-spacing:.8px; text-transform:uppercase;
}
.t-mob, .hora-mob, .bnav, .sheet-overlay { display: none; }
.header-sub { font-size:11.5px; color:var(--text-on-dark-sub); margin-top:2px; letter-spacing:.4px; }

.header-meta { display:flex; flex-direction:column; align-items:flex-end; gap:4px; flex-shrink:0; }
.fecha-badge {
  background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.2);
  color:#fff; padding:5px 12px; border-radius:7px;
  font-size:11px; text-transform:capitalize; white-space:nowrap;
}
.sync-badge { font-size:10px; color:var(--text-on-dark-sub); }

/* ── TABS ── */
.tab-bar { display:flex; align-items:center; gap:10px; margin-bottom:14px; flex-wrap: wrap; }
.tab-scroll {
  display:flex; gap:8px; overflow-x:auto; -webkit-overflow-scrolling:touch;
  scrollbar-width:none; flex: 1 1 auto;
}
.tab-scroll::-webkit-scrollbar { display:none; }

.tab-btn {
  display:flex; align-items:center; gap:9px; padding:7px 18px 7px 9px;
  border:2px solid var(--border); background:var(--surface);
  border-radius:9px; font-size:13px; font-weight:700;
  cursor:pointer; color:var(--text-muted); transition:all .15s; font-family:inherit;
  white-space: nowrap; flex-shrink: 0;
}
.tab-btn:hover  { border-color:var(--accent); color:var(--accent); }
.tab-btn.active { background:var(--accent); border-color:var(--accent); color:#fff; box-shadow:0 2px 8px rgba(49,176,121,0.35); }
.tab-btn:focus-visible { outline:2px solid var(--primary); outline-offset:2px; }
/* ── Íconos tipo «app»: baldosa con degradado y símbolo blanco (dibujados a medida) ── */
.tab-btn--dpv   { --glow:rgba(5,144,95,.45); }
.tab-btn--ico   { --glow:rgba(13,17,23,.5); }
.tab-btn--disp  { --glow:rgba(27,79,209,.45); }
.tab-btn--inmov { --glow:rgba(238,90,11,.45); }
.tab-ico {
  display:inline-flex; flex-shrink:0; width:28px; height:28px; border-radius:25%;
  box-shadow:0 3px 8px -2px var(--glow, rgba(0,0,0,.3));
  transition:transform .18s ease, box-shadow .18s ease;
}
.tab-ico .ic { width:100%; height:100%; display:block; border-radius:25%; }
.tab-btn.active .tab-ico { box-shadow:0 0 0 2px rgba(255,255,255,.95), 0 4px 10px -2px rgba(0,0,0,.3); }
.tab-btn:hover .tab-ico { transform:translateY(-1px) scale(1.07); }
.tab-btn:active .tab-ico { transform:scale(.95); }
@media (prefers-reduced-motion: reduce) { .tab-ico { transition:none; } .tab-btn:hover .tab-ico, .tab-btn:active .tab-ico { transform:none; } }

.tab-btn--inmov.active { background:#a85a08; border-color:#a85a08; box-shadow:0 2px 8px rgba(217,119,6,0.35); }
.tab-btn--disp.active { background:var(--secondary); border-color:var(--secondary); box-shadow:0 2px 8px rgba(7,78,122,0.35); }

.reload-btn {
  display:flex; align-items:center; gap:6px; padding:8px 16px;
  border:1.5px solid var(--border); background:var(--surface);
  border-radius:8px; font-size:12px; font-weight:600;
  cursor:pointer; color:var(--text-muted); transition:all .15s; font-family:inherit;
  flex-shrink: 0;
}
.reload-btn:hover:not(:disabled) { border-color:var(--teal); color:var(--teal); }
.reload-btn:disabled { opacity:.5; cursor:not-allowed; }
.spin { display:inline-block; animation:spin .8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }

/* ── DISPONIBILIDAD DE FLOTA ── */
.disp-widget {
  display: flex; align-items: center; gap: 12px;
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: 9px; padding: 7px 16px;
  flex-shrink: 0;
}
.disp-label {
  font-size: 10px; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .4px; white-space: nowrap;
}
.disp-item { display: flex; align-items: baseline; gap: 5px; }
.disp-uf   { font-size: 11px; font-weight: 700; color: var(--text-muted); }
.disp-val  { font-size: 15px; font-weight: 800; }
.disp-ok   { color: var(--accent); }
.disp-warn { color: var(--warning); }
.disp-bad  { color: var(--danger); }
.disp-na   { color: var(--text-muted); }

/* ── BANNERS ── */
.error-banner {
  display:flex; align-items:center; justify-content:space-between;
  background:var(--danger-light); border:1px solid #fca5a5;
  border-radius:8px; padding:10px 16px;
  font-size:13px; color:var(--danger); margin-bottom:12px;
}
.error-banner button { background:none; border:none; color:var(--danger); cursor:pointer; font-size:14px; font-weight:700; }

.loading-banner {
  display:flex; align-items:center; gap:12px;
  background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:16px 20px; margin-bottom:12px;
  font-size:13px; color:var(--text-muted);
}
.spinner {
  width:20px; height:20px; flex-shrink:0;
  border:2px solid var(--border); border-top-color:var(--accent);
  border-radius:50%; animation:spin .7s linear infinite;
}

.fade-slide-enter-active, .fade-slide-leave-active { transition: all .2s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-6px); }

/* ══════════════════════════════════════════════════════════════
   CELULAR (≤ 720 px): cabecera tipo «panel», tarjetas KPI,
   barra inferior y hoja de ajustes
   ══════════════════════════════════════════════════════════════ */
@media (max-width: 720px) {
  /* padding inferior = alto de la barra inferior + zona segura del celular */
  .dash-page { padding: 0 12px calc(86px + env(safe-area-inset-bottom, 0px)); }
  .dash-contenido { min-width: 0; }

  /* Cabecera a todo el ancho, con esquinas inferiores redondeadas */
  .dash-header {
    flex-direction: column; align-items: center; gap: 8px; text-align: center;
    margin: 0 -12px 14px; padding: 18px 16px 16px;
    border-radius: 0 0 28px 28px;
  }
  .header-centro { order: 1; flex: 0 0 auto; min-width: 0; }
  .brand-block   { order: 2; background: rgba(255,255,255,.08); border-radius: 12px; padding: 4px 14px 4px 6px; }
  .header-meta   { order: 3; align-items: center; }
  .t-desk, .header-sub { display: none; }
  .t-mob { display: block; font-size: 17px; letter-spacing: .6px; line-height: 1.25; }
  .hora-mob { display: inline; }
  .fecha-badge { background: transparent; border: 0; padding: 0; font-size: 12.5px; text-transform: none; color: rgba(255,255,255,.88); }
  .sync-badge { display: none; }

  /* Tabs → tarjetas con scroll horizontal (se ven 3 y se asoma la cuarta) */
  .tab-bar { margin-bottom: 12px; }
  .tab-scroll {
    display: grid; grid-auto-flow: column; gap: 10px; width: 100%;
    grid-auto-columns: minmax(104px, calc((100% - 20px) / 3));
    padding: 2px 2px 8px; scroll-snap-type: x proximity;
  }
  .tab-btn {
    flex-direction: column; justify-content: center; gap: 2px; scroll-snap-align: start;
    min-height: 104px; padding: 12px 6px 10px; border-radius: 16px; border-width: 1.5px;
    box-shadow: 0 2px 10px rgba(8,69,52,.08);
  }
  .tab-ico { width: 54px; height: 54px; margin-bottom: 5px; border-radius: 25%; box-shadow: 0 8px 16px -6px var(--glow, rgba(0,0,0,.3)); }
  .tab-btn.active .tab-ico { box-shadow: 0 0 0 2.5px rgba(255,255,255,.95), 0 8px 16px -6px rgba(0,0,0,.35); }
  .tab-lbl { order: 3; font-size: 12.5px; font-weight: 700; color: var(--text); line-height: 1.2; }
  .tab-btn.active .tab-lbl { color: #fff; }

  .disp-widget, .reload-btn { display: none; }

  /* ── Barra inferior ── */
  .bnav {
    display: grid; grid-template-columns: repeat(4, 1fr);
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 90;
    background: var(--surface); border-top: 1px solid var(--border);
    box-shadow: 0 -4px 16px rgba(8,69,52,.10);
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom, 0px));
  }
  .bnav-btn {
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    min-height: 52px; padding: 6px 2px; border: 0; background: transparent; border-radius: 12px;
    color: var(--text-muted); font-family: inherit; font-size: 11.5px; font-weight: 600; cursor: pointer;
  }
  .bnav-btn svg { width: 22px; height: 22px; }
  .bnav-btn.on { color: var(--primary); font-weight: 800; }
  .bnav-btn.on svg { color: var(--accent); }
  .bnav-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }

  /* ── Hoja de ajustes ── */
  .sheet-overlay {
    display: flex; align-items: flex-end; position: fixed; inset: 0; z-index: 210;
    background: rgba(6,46,35,.45);
  }
  .sheet {
    width: 100%; background: var(--surface); border-radius: 22px 22px 0 0;
    padding: 10px 20px calc(20px + env(safe-area-inset-bottom, 0px));
    display: flex; flex-direction: column; gap: 12px; box-shadow: 0 -10px 30px rgba(0,0,0,.2);
  }
  .sheet-grip { width: 42px; height: 4px; border-radius: 4px; background: var(--border); align-self: center; }
  .sheet-t { font-size: 17px; font-weight: 800; color: var(--text); margin: 4px 0 0; }
  .sheet-s { font-size: 12.5px; color: var(--text-muted); margin: 0; }
  .sheet-disp {
    display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 18px;
    padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg);
  }
  .sheet-disp .disp-label { flex-basis: 100%; order: -1; }
  .sheet-btn { width: 100%; min-height: 46px; justify-content: center; border-radius: 12px; }

  .sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
  .sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform .25s ease; }
  .sheet-enter-from, .sheet-leave-to { opacity: 0; }
  .sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(100%); }
}

@media (max-width: 720px) and (prefers-reduced-motion: reduce) {
  .sheet-enter-active, .sheet-leave-active,
  .sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: none; }
}
</style>