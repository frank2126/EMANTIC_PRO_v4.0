<template>
  <div class="page">

    <!-- ══ HERO — BIBLIOTECA DE MANUALES ══ -->
    <div class="manuals-hero" :style="{ backgroundImage: `url(${manualsHeroImg})` }">
      <div class="manuals-hero-overlay">
        <div class="manuals-hero-content">
          <div class="manuals-hero-eyebrow">EMASIVO · DOCUMENTACIÓN TÉCNICA</div>
          <h1 class="manuals-hero-title">Biblioteca de Manuales Técnicos</h1>
          <p class="manuals-hero-sub">Manuales oficiales Scania y Volkswagen para el diagnóstico, mantenimiento y reparación de la flota.</p>

          <div v-if="heroStats.length" class="manuals-hero-stats">
            <div v-for="s in heroStats" :key="s.label" class="mh-stat">
              <div class="mh-stat-value">{{ s.value }}</div>
              <div class="mh-stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-header page-header--slim">
      <button class="btn-primary" @click="showUpload = !showUpload">
        {{ showUpload ? '✕ Cancelar' : '+ Nuevo Manual' }}
      </button>
    </div>

    <transition name="slide">
      <div v-if="showUpload" class="card upload-card">
        <h3 class="card-title">Subir nuevo manual PDF</h3>
        <div class="form-grid">
          <div class="fgroup">
            <label class="label">Título del manual</label>
            <input v-model="form.title" class="input" placeholder="Ej: Manual Motor Cummins ISB 6.7L" />
          </div>
          <div class="fgroup">
            <label class="label">Marca</label>
            <select v-model="form.brand" class="input">
              <option value="">Sin marca</option>
              <option value="Scania">Scania</option>
              <option value="Volkswagen">Volkswagen</option>
            </select>
          </div>
          <div class="fgroup">
            <label class="label">Categoría</label>
            <select v-model="form.category" class="input">
              <option v-for="c in categories" :key="c">{{ c }}</option>
            </select>
          </div>
          <div class="fgroup form-full">
            <label class="label">Descripción</label>
            <textarea v-model="form.description" class="input" rows="2" placeholder="Descripción breve del manual..."></textarea>
          </div>
          <div class="fgroup form-full">
            <div class="drop-zone" @click="$refs.fi.click()" @dragover.prevent @drop.prevent="e => form.file = e.dataTransfer.files[0]">
              <span v-if="!form.file">📄 Arrastra tu PDF aquí o haz clic para seleccionar</span>
              <span v-else style="color:var(--success)">✅ {{ form.file.name }}</span>
            </div>
            <input ref="fi" type="file" accept=".pdf" style="display:none" @change="e => form.file = e.target.files[0]" />
          </div>
        </div>
        <p v-if="uploadErr" class="err-msg">{{ uploadErr }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showUpload=false">Cancelar</button>
          <button class="btn-primary" :disabled="uploading||!form.file" @click="upload">
            {{ uploading ? 'Subiendo...' : '↑ Subir Manual' }}
          </button>
        </div>
      </div>
    </transition>

    <div class="manuals-layout">
      <div class="card cat-panel">

        <!-- ── MARCAS ── -->
        <h3 class="cat-title">Marca</h3>
        <div class="brand-cards">
        <button class="brand-card" :class="{active: activeBrand==='Scania'}" @click="toggleBrand('Scania')">
          <img :src="scaniaLogo" alt="Scania" class="brand-img" />
          <span class="brand-label">Scania</span>
            </button>

        <button class="brand-card" :class="{active: activeBrand==='Volkswagen'}" @click="toggleBrand('Volkswagen')">
          <img :src="vwLogo" alt="Volkswagen" class="brand-img" />
          <span class="brand-label">Volkswagen</span>
            </button>
        </div>

        <div class="cat-divider"></div>

        <!-- ── CATEGORÍAS ── -->
        <h3 class="cat-title">Categorías</h3>
        <button class="cat-btn" :class="{active:!activeCat}" @click="activeCat=null">
          <span class="cat-icon" v-html="iconAll"></span>
          Todos
        </button>
        <button v-for="c in categories" :key="c" class="cat-btn" :class="{active:activeCat===c}" @click="activeCat=c">
          <span class="cat-icon" v-html="catIconSvg(c)"></span>
          {{ c }}
        </button>
      </div>

      <div class="manuals-area">
        <!-- Chips de filtros activos -->
        <div v-if="activeBrand || activeCat" class="active-filters">
          <span class="filter-chip" v-if="activeBrand" @click="activeBrand=null">
            {{ activeBrand }} ✕
          </span>
          <span class="filter-chip" v-if="activeCat" @click="activeCat=null">
            {{ activeCat }} ✕
          </span>
          <button class="clear-all" @click="activeBrand=null; activeCat=null">Limpiar filtros</button>
        </div>

        <!-- ── CUADRO INFORMATIVO / TARJETA DE RESUMEN (siempre visible) ── -->
        <div class="summary-card">
          <div class="summary-icon" v-html="summaryIconSvg"></div>
          <div class="summary-body">
            <h2 class="summary-title">{{ displayedSummary.title }}</h2>
            <p class="summary-desc">{{ displayedSummary.desc }}</p>
          </div>
        </div>

        <div v-if="loading" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando manuales...</p></div>

        <!-- Sin resultados: mensaje compacto ya que el cuadro de resumen siempre está arriba -->
        <div v-else-if="filtered.length===0" class="empty-inline">
          <span>📭</span>
          <span>
            No hay manuales{{ activeCat ? ` en "${activeCat}"` : '' }}{{ activeBrand ? ` de ${activeBrand}` : '' }} disponibles todavía.
          </span>
        </div>

        <div v-else class="manuals-grid">
          <div v-for="m in filtered" :key="m.id" class="card manual-card">
            <div class="mc-top">
              <div class="mc-pdf" :class="brandClass(m)">
                 <img v-if="brandLogo(m)" :src="brandLogo(m)" class="mc-logo-img" alt="" />
                  <span v-else>{{ brandTag(m) }}</span>
                </div>
              <div class="mc-info">
                <h4 class="mc-title">{{ m.title }}</h4>
                <p class="mc-meta">{{ m.category }} · {{ m.size_mb }} MB · {{ m.uploaded_at }}</p>
                <p v-if="m.description" class="mc-desc">{{ m.description }}</p>
              </div>
            </div>
            <div class="mc-actions">
              <a :href="m.url" target="_blank" class="btn-secondary btn-sm">👁 Ver</a>
              <a :href="m.url" :download="m.title" class="btn-secondary btn-sm">⬇ Descargar</a>
              <button v-if="isAdmin()" class="btn-del-sm" @click="del(m.id)">🗑</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

import manualsHeroImg from '../assets/manuales-hero.png'
import scaniaLogo from '../assets/scania.png'
import vwLogo from '../assets/volkswagen.png'
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'
const { isAdmin } = useAuth()

const manuals    = ref([])
const categories = ref([])
const activeCat  = ref(null)
const activeBrand = ref(null)
const loading    = ref(true)
const showUpload = ref(false)
const uploading  = ref(false)
const uploadErr  = ref('')
const form = ref({ title:'', description:'', category:'', brand:'', file:null })

// Datos reales para el hero
const heroStats = computed(() => [
  { value: `${manuals.value.length}`, label: 'Manuales disponibles' },
  { value: `${categories.value.length}`, label: 'Categorías' },
  { value: '2', label: 'Marcas' },
])

// Filtra por marca Y categoría
const filtered = computed(() => {
  let list = manuals.value
  if (activeBrand.value) list = list.filter(m => {
    const t = (m.title + ' ' + (m.description||'')).toLowerCase()
    return t.includes(activeBrand.value.toLowerCase()) ||
           (m.brand && m.brand === activeBrand.value)
  })
  if (activeCat.value) list = list.filter(m => m.category === activeCat.value)
  return list
})

const toggleBrand = b => { activeBrand.value = activeBrand.value === b ? null : b }

/* ════════════════════════════════════════════════════════════════
   ICONOS SVG COMO STRINGS (v-html) — 100% confiable en Vue 3
   ════════════════════════════════════════════════════════════════ */

const svgMotor = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="16" height="12" rx="2" fill="rgba(49,176,121,0.08)"/><path d="M8 6V4" stroke-width="2"/><path d="M16 6V4" stroke-width="2"/><path d="M8 18v2" stroke-width="2"/><path d="M16 18v2" stroke-width="2"/><circle cx="12" cy="12" r="2.5" fill="rgba(49,176,121,0.2)"/><path d="M12 9.5V7" stroke-width="1.5"/><path d="M12 17v-2.5" stroke-width="1.5"/><path d="M9.5 12H7" stroke-width="1.5"/><path d="M17 12h-2.5" stroke-width="1.5"/></svg>`

const svgFrenos = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="7" fill="rgba(49,176,121,0.06)"/><circle cx="12" cy="12" r="4" fill="rgba(49,176,121,0.1)"/><circle cx="12" cy="12" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/><path d="M12 5V3" stroke-width="2"/><path d="M12 21v-2" stroke-width="2"/><path d="M5 12H3" stroke-width="2"/><path d="M21 12h-2" stroke-width="2"/><path d="M7.05 7.05L5.64 5.64" stroke-width="1.5"/><path d="M18.36 18.36l-1.41-1.41" stroke-width="1.5"/><path d="M7.05 16.95l-1.41 1.41" stroke-width="1.5"/><path d="M18.36 5.64l-1.41 1.41" stroke-width="1.5"/></svg>`

const svgElectrico = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="rgba(49,176,121,0.1)" stroke-linejoin="round"/><circle cx="19" cy="5" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/><path d="M17 7l-1.5 1.5" stroke-width="1.2"/></svg>`

const svgSuspension = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16" stroke-width="2"/><path d="M6 20V10a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v10" fill="rgba(49,176,121,0.06)"/><path d="M8 20v-6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v6" fill="rgba(49,176,121,0.08)"/><circle cx="12" cy="6" r="2" fill="rgba(49,176,121,0.15)"/><path d="M12 8v2" stroke-width="1.5"/></svg>`

const svgCarroceria = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 17a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2" fill="rgba(49,176,121,0.05)"/><path d="M3 10h18" stroke-width="1.5"/><path d="M7 14h4" stroke-width="1.5"/><circle cx="17" cy="14" r="1.5" fill="rgba(49,176,121,0.3)" stroke="none"/><path d="M2 17l2 4h16l2-4" fill="rgba(49,176,121,0.08)"/><circle cx="8" cy="20" r="1.2" fill="rgba(49,176,121,0.4)" stroke="none"/><circle cx="16" cy="20" r="1.2" fill="rgba(49,176,121,0.4)" stroke="none"/></svg>`

const svgECU = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="12" rx="2" fill="rgba(49,176,121,0.06)"/><rect x="7" y="7" width="10" height="6" rx="1" fill="rgba(49,176,121,0.1)"/><path d="M9 10h6" stroke-width="1.5"/><path d="M9 12h4" stroke-width="1.2"/><path d="M10 16v3" stroke-width="1.5"/><path d="M14 16v3" stroke-width="1.5"/><circle cx="12" cy="19.5" r="1" fill="rgba(49,176,121,0.5)" stroke="none"/></svg>`

const iconAll = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="14" y="3" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="3" y="14" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="14" y="14" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/></svg>`

const catIconSvg = c => {
  const map = {
    'Motor y Transmisión': svgMotor,
    'Sistema de Frenos': svgFrenos,
    'Sistema Eléctrico': svgElectrico,
    'Suspensión': svgSuspension,
    'Carrocería y Chasis': svgCarroceria,
    'Diagnóstico ECU': svgECU,
  }
  return map[c] || iconAll
}

// ── Descripciones técnicas por categoría ──
const CAT_DESCRIPTIONS = {
  'Motor y Transmisión': (brand) =>
    `Documentación técnica${brand ? ` oficial de ${brand}` : ''} para el diagnóstico, mantenimiento y reparación del motor y la caja de transmisión, incluyendo procedimientos de torque, calibración y códigos de falla asociados.`,
  'Sistema de Frenos': (brand) =>
    `Esta sección contiene la documentación técnica${brand ? ` oficial de ${brand}` : ''} para el diagnóstico, mantenimiento y reparación del sistema de frenos neumáticos y sus componentes asociados en buses y camiones${brand ? ' de la marca' : ' de la flota'}.`,
  'Sistema Eléctrico': (brand) =>
    `Manuales${brand ? ` de ${brand}` : ''} con diagramas de cableado, ubicación de fusibles/relés y procedimientos de diagnóstico eléctrico para la flota.`,
  'Suspensión': (brand) =>
    `Documentación${brand ? ` oficial de ${brand}` : ''} sobre el sistema de suspensión neumática y mecánica: inspección, ajuste y reemplazo de componentes.`,
  'Carrocería y Chasis': (brand) =>
    `Manuales${brand ? ` de ${brand}` : ''} de estructura de carrocería y chasis: reparación, alineación y especificaciones de soldadura.`,
  'Diagnóstico ECU': (brand) =>
    `Guías${brand ? ` oficiales de ${brand}` : ''} para el diagnóstico electrónico de la unidad de control del motor (ECU), lectura de códigos y actualización de software.`,
}

const summaryInfo = computed(() => {
  if (!activeBrand.value && !activeCat.value) return null

  const brand = activeBrand.value
  const cat   = activeCat.value

  let title
  if (brand && cat)      title = `Manuales Técnicos ${brand} — ${cat}`
  else if (brand)        title = `Manuales Técnicos ${brand}`
  else                   title = `Manuales Técnicos — ${cat}`

  let desc
  if (cat && CAT_DESCRIPTIONS[cat]) {
    desc = CAT_DESCRIPTIONS[cat](brand)
  } else if (brand) {
    desc = `Documentación técnica oficial de ${brand} disponible en la biblioteca: diagnóstico, mantenimiento y reparación de los distintos sistemas del vehículo.`
  } else {
    desc = 'Documentación técnica disponible para esta categoría.'
  }

  const icon = cat ? catIconSvg(cat) : iconAll

  return { title, desc, icon }
})

// Descripción general cuando no hay ningún filtro activo ("Todos")
const DEFAULT_SUMMARY = {
  title: 'Biblioteca de Manuales Técnicos',
  desc: 'Encuentra aquí toda la documentación técnica oficial de la flota: manuales de motor y transmisión, frenos, sistema eléctrico, suspensión, carrocería y diagnóstico ECU. Usa los filtros de marca y categoría para encontrar el manual que necesitas.',
  icon: iconAll,
}

const displayedSummary = computed(() => {
  const info = summaryInfo.value
  if (!info) return { ...DEFAULT_SUMMARY }
  return { title: info.title, desc: info.desc }
})

const summaryIconSvg = computed(() => {
  const info = summaryInfo.value
  return info ? info.icon : iconAll
})

const brandClass = m => {
  const t = (m.title + ' ' + (m.description||'')).toLowerCase()
  if (t.includes('scania'))     return 'mc-pdf--scania'
  if (t.includes('volkswagen') || t.includes('vw')) return 'mc-pdf--vw'
  return ''
}
const brandTag = m => {
  const t = (m.title + ' ' + (m.description||'')).toLowerCase()
  if (t.includes('scania'))     return 'SCN'
  if (t.includes('volkswagen') || t.includes('vw')) return 'VW'
  return 'PDF'
}
const brandLogo = m => {
  const t = (m.title + ' ' + (m.description||'')).toLowerCase()
  if (t.includes('scania')) return scaniaLogo
  if (t.includes('volkswagen') || t.includes('vw')) return vwLogo
  return null
}
const load = async () => {
  loading.value = true
  try {
    const [m, c] = await Promise.all([axios.get('/api/manuals'), axios.get('/api/manuals/categories')])
    manuals.value = m.data; categories.value = c.data
    if (!form.value.category && c.data.length) form.value.category = c.data[0]
  } catch {} finally { loading.value = false }
}

const upload = async () => {
  uploadErr.value = ''; uploading.value = true
  const fd = new FormData()
  fd.append('file', form.value.file)
  fd.append('title', form.value.title)
  fd.append('description', form.value.description)
  fd.append('category', form.value.category)
  try {
    await axios.post('/api/manuals/upload', fd)
    form.value = { title:'', description:'', category:categories.value[0]||'', brand:'', file:null }
    showUpload.value = false; await load()
  } catch(e) { uploadErr.value = e.response?.data?.detail||'Error al subir' }
  finally { uploading.value = false }
}

const del = async id => {
  if (!confirm('¿Eliminar este manual?')) return
  try { await axios.delete(`/api/manuals/${id}`); await load() } catch {}
}

onMounted(load)
</script>

<style scoped>
/* ══ HERO — BIBLIOTECA DE MANUALES ══ */
.manuals-hero {
  position: relative;
  height: 320px;
  margin: -32px -32px 32px;
  background-size: cover;
  background-position: center 40%;
  border-radius: 0 0 var(--radius) var(--radius);
  overflow: hidden;
}
@media(min-width: 900px)  { .manuals-hero { height: 440px; } }
@media(min-width: 1300px) { .manuals-hero { height: 500px; } }

.manuals-hero-overlay {
  position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(6,46,35,0.88) 0%, rgba(6,46,35,0.6) 40%, rgba(6,46,35,0.1) 75%),
    linear-gradient(180deg, rgba(8,69,52,0.1) 0%, rgba(8,69,52,0.4) 45%, rgba(6,46,35,0.9) 100%);
  display: flex; align-items: flex-end;
  padding: 32px 40px;
}
.manuals-hero-content { max-width: 720px; }
.manuals-hero-eyebrow {
  font-size: 11px; font-weight: 800; letter-spacing: 2px;
  color: var(--accent); text-transform: uppercase; margin-bottom: 8px;
}
.manuals-hero-title {
  font-size: clamp(24px, 3.4vw, 34px); font-weight: 900; color: #fff;
  line-height: 1.15; margin-bottom: 8px;
}
.manuals-hero-sub {
  font-size: 14px; color: rgba(255,255,255,0.75); line-height: 1.5;
  max-width: 52ch; margin-bottom: 22px;
}
.manuals-hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.mh-stat-value { font-size: 26px; font-weight: 900; color: #fff; line-height: 1; }
.mh-stat-label { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

.page-header--slim { justify-content: flex-end; margin-top: -8px; }

.upload-card { padding:24px; margin-bottom:24px; }
.card-title  { font-size:16px; font-weight:700; margin-bottom:16px; }
.form-grid   { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px; }
.form-full   { grid-column:1/-1; }
.fgroup      { display:flex; flex-direction:column; gap:6px; }
.drop-zone   { border:2px dashed var(--border); border-radius:10px; padding:28px; text-align:center; cursor:pointer; color:var(--text-muted); font-size:14px; transition:all 0.2s; }
.drop-zone:hover { border-color:var(--primary); color:var(--primary); }
.err-msg     { color:var(--danger); font-size:13px; margin-bottom:10px; }
.form-actions{ display:flex; gap:10px; justify-content:flex-end; }

/* Layout */
.manuals-layout { display:flex; gap:20px; align-items:flex-start; }
.cat-panel      { width:210px; flex-shrink:0; padding:20px; }
.cat-title      { font-size:13px; font-weight:700; margin-bottom:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--text-muted); }
.cat-divider    { height:1px; background:var(--border); margin:16px 0; }

/* Tarjetas de marca */
.brand-cards  { display:flex; flex-direction:column; gap:8px; margin-bottom:4px; }
.brand-card   { display:flex; align-items:center; gap:10px; padding:10px 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:10px; cursor:pointer; transition:all 0.2s; font-family:inherit; }
.brand-card:hover { border-color:var(--primary); background:#fff; box-shadow:0 2px 8px rgba(0,0,0,0.08); }
.brand-card.active { border-color:var(--primary); background:var(--primary-light); box-shadow:0 2px 8px rgba(0,0,0,0.1); }
.brand-svg    { width:40px; height:40px; flex-shrink:0; }
.brand-img {width: 40px;height: 40px;object-fit: contain;flex-shrink: 0;}
.brand-label  { font-size:13px; font-weight:600; color:var(--text); }
.brand-card.active .brand-label { color:var(--primary); }

/* Categorías */
.cat-btn     { width:100%; display:flex; align-items:center; gap:8px; padding:10px 12px; background:none; border:none; border-radius:8px; cursor:pointer; font-size:13px; color:var(--text-muted); text-align:left; transition:all 0.15s; margin-bottom:2px; font-family:inherit; }
.cat-btn:hover  { background:var(--bg); color:var(--text); }
.cat-btn.active { background:var(--primary); color:#fff; font-weight:600; }

/* Chips de filtros activos */
.active-filters { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
.filter-chip    { display:inline-flex; align-items:center; gap:4px; background:var(--primary-light); color:var(--primary); border:1px solid var(--primary); border-radius:20px; padding:4px 12px; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.15s; }
.filter-chip:hover { background:var(--primary); color:#fff; }
.clear-all      { background:none; border:none; color:var(--text-muted); font-size:12px; cursor:pointer; text-decoration:underline; font-family:inherit; }

/* ── Cuadro informativo / tarjeta de resumen ── */
.summary-card {
  display: flex; align-items: flex-start; gap: 16px;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--surface) 70%);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius);
  padding: 18px 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow);
}
.summary-icon {
  flex-shrink: 0;
  width: 52px; height: 52px;
  display: flex; align-items: center; justify-content: center;
  background: #fff; border-radius: 12px;
  border: 1px solid var(--border);
  color: var(--primary);
}
.summary-icon svg {
  width: 26px;
  height: 26px;
}
.summary-body  { flex: 1; min-width: 0; }
.summary-title { font-size: 17px; font-weight: 800; color: var(--primary); margin-bottom: 6px; line-height: 1.3; }
.summary-desc  { font-size: 13.5px; color: var(--text-muted); line-height: 1.6; max-width: 70ch; }

.empty-inline {
  display: flex; align-items: center; gap: 8px;
  color: var(--text-muted); font-size: 13px;
  padding: 12px 4px;
}

/* Grid de manuales */
.manuals-area{ flex:1; min-width:0; }
.manuals-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
.manual-card { padding:20px; display:flex; flex-direction:column; gap:14px; transition:box-shadow 0.2s; }
.manual-card:hover { box-shadow:var(--shadow-md); }
.mc-top      { display:flex; gap:14px; align-items:flex-start; }
.mc-pdf      { width:48px; height:48px; background:#dbeafe; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:800; color:#1e40af; flex-shrink:0; }
.mc-pdf--scania { background:#CC0000; color:#fff; }
.mc-pdf--vw     { background:#00205B; color:#fff; }
.mc-logo-img { width:32px; height:32px; object-fit:contain; }
.mc-title    { font-size:14px; font-weight:700; margin-bottom:4px; line-height:1.3; }
.mc-meta     { font-size:11px; color:var(--text-muted); margin-bottom:4px; }
.mc-desc     { font-size:12px; color:var(--text-muted); line-height:1.4; }
.mc-actions  { display:flex; gap:8px; flex-wrap:wrap; }
.btn-sm      { padding:6px 12px !important; font-size:12px !important; }
.btn-del-sm  { background:#fee2e2; border:1px solid #fecaca; color:var(--danger); padding:6px 10px; border-radius:8px; cursor:pointer; font-size:12px; transition:all 0.2s; }
.btn-del-sm:hover { background:var(--danger); color:#fff; }

/* ════════════════════════════════════════════════════════════════
   ICONOS SVG DE CATEGORÍAS
   ════════════════════════════════════════════════════════════════ */

.cat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  color: var(--primary);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.cat-icon svg {
  width: 18px;
  height: 18px;
}

.cat-btn:hover .cat-icon {
  transform: scale(1.15) rotate(-4deg);
}

.cat-btn.active .cat-icon {
  color: #fff;
}

/* Animación flotante sutil en iconos de categoría */
.cat-icon {
  animation: cat-float 4s ease-in-out infinite;
}

.cat-btn:nth-child(2) .cat-icon { animation-delay: 0.1s; }
.cat-btn:nth-child(3) .cat-icon { animation-delay: 0.2s; }
.cat-btn:nth-child(4) .cat-icon { animation-delay: 0.3s; }
.cat-btn:nth-child(5) .cat-icon { animation-delay: 0.4s; }
.cat-btn:nth-child(6) .cat-icon { animation-delay: 0.5s; }
.cat-btn:nth-child(7) .cat-icon { animation-delay: 0.6s; }
.cat-btn:nth-child(8) .cat-icon { animation-delay: 0.7s; }

@keyframes cat-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

.cat-btn:hover .cat-icon {
  animation: none;
  transform: scale(1.2) rotate(-6deg);
}

@media(max-width:768px){
  .manuals-layout{flex-direction:column;}
  .cat-panel{width:100%;}
  .form-grid{grid-template-columns:1fr;}
  .summary-card { flex-direction: column; align-items: flex-start; }
  .manuals-hero { height: 300px; margin: -16px -16px 24px; }
  .manuals-hero-overlay { padding: 20px; }
  .manuals-hero-stats { gap: 20px; }
}
</style>