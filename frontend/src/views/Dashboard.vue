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
          {{ tituloHeader }}
        </div>
        <div class="header-sub">EMASIVO 10 / 16</div>
      </div>

      <div class="header-meta">
        <span class="fecha-badge">{{ fechaHoy }}</span>
        <span v-if="store.lastSync" class="sync-badge">🔄 {{ store.lastSync }}</span>
      </div>
    </div>

    <!-- ── TABS ── -->
    <div class="tab-bar">
      <div class="tab-scroll">
        <button class="tab-btn" :class="{active: activeTab==='dpv'}" @click="activeTab='dpv'">
          <span>📥</span> DPV
          <span class="tab-count">{{ store.dpvRaw.length }}</span>
        </button>
        <button class="tab-btn" :class="{active: activeTab==='ico'}" @click="activeTab='ico'">
          <span>📊</span> ICO
          <span class="tab-count">{{ store.icoRaw.length }}</span>
        </button>
        <button class="tab-btn tab-btn--disp" :class="{active: activeTab==='disponibilidad'}" @click="activeTab='disponibilidad'">
          <span>🚌</span> Disponibilidad
          <span class="tab-count">{{ disponibilidadTotal }}</span>
        </button>
      </div>

      <!-- ── DISPONIBILIDAD DE FLOTA ── -->
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

      <button class="reload-btn" @click="store.cargarDatos()" :disabled="store.loading">
        <span :class="{spin: store.loading}">🔄</span>
        <span class="reload-txt">{{ store.loading ? 'Cargando...' : 'Recargar datos' }}</span>
      </button>
    </div>

    <!-- ── ERROR ── -->
    <transition name="fade-slide">
      <div v-if="store.error" class="error-banner">
        <span>⚠️ {{ store.error }}</span>
        <button @click="store.error = null" aria-label="Cerrar">✕</button>
      </div>
    </transition>

    <!-- ── LOADING ── -->
    <transition name="fade-slide">
      <div v-if="store.loading" class="loading-banner">
        <div class="spinner"></div>
        <span>Cargando datos desde el servidor...</span>
      </div>
    </transition>

    <!-- ── CONTENIDO ── -->
    <DashboardDPV v-show="activeTab === 'dpv'" />
    <DashboardICO v-show="activeTab === 'ico'" />
    <DashboardDisponibilidad v-show="activeTab === 'disponibilidad'" />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import DashboardDPV from './DashboardDPV.vue'
import DashboardICO from './DashboardICO.vue'
import DashboardDisponibilidad from './DashboardDisponibilidad.vue'

const store     = useDashboardStore()
const activeTab = ref('dpv')

const fechaHoy = new Date().toLocaleDateString('es-CO', {
  weekday:'long', year:'numeric', month:'long', day:'numeric'
}).replace(/^\w/, c => c.toUpperCase())

const tituloHeader = computed(() => {
  if (activeTab.value === 'dpv') return 'No. Eventos en Vía'
  if (activeTab.value === 'ico') return 'No. Eventos ICO'
  return 'Disponibilidad de Flota'
})

const disponibilidadTotal = computed(() => {
  const e10 = store.disponibilidad.e10?.no_disponibles || 0
  const e16 = store.disponibilidad.e16?.no_disponibles || 0
  return e10 + e16
})

// Color del porcentaje de disponibilidad: verde >=90%, ámbar >=75%, rojo por debajo
const dispClass = (pct) => {
  if (pct == null) return 'disp-na'
  if (pct >= 90) return 'disp-ok'
  if (pct >= 75) return 'disp-warn'
  return 'disp-bad'
}

onMounted(() => {
  store.cargarDatos()
  store.cargarDisponibilidad()
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
  display:flex; align-items:center; gap:6px; padding:9px 20px;
  border:2px solid var(--border); background:var(--surface);
  border-radius:9px; font-size:13px; font-weight:700;
  cursor:pointer; color:var(--text-muted); transition:all .15s; font-family:inherit;
  white-space: nowrap; flex-shrink: 0;
}
.tab-btn:hover  { border-color:var(--accent); color:var(--accent); }
.tab-btn.active { background:var(--accent); border-color:var(--accent); color:#fff; box-shadow:0 2px 8px rgba(49,176,121,0.35); }
.tab-count {
  font-size:10px; font-weight:700; padding:1px 7px;
  border-radius:10px; min-width:22px; text-align:center;
  background:rgba(255,255,255,0.25); color:#fff;
}
.tab-btn:not(.active) .tab-count { background:var(--primary-light); color:var(--primary); }
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

/* ── RESPONSIVE ── */
@media (max-width: 720px) {
  .dash-header { flex-direction: column; align-items: stretch; text-align: center; gap: 10px; }
  .header-meta { align-items: center; }
  .header-centro { order: -1; flex: 0 0 auto; min-width: 0; }
  .reload-txt { display: none; }
  .reload-btn { padding: 8px 12px; }
}
@media (max-width: 560px) {
  .tab-bar { flex-wrap: wrap; }
  .disp-widget { order: 3; width: 100%; justify-content: space-between; }
}
</style>