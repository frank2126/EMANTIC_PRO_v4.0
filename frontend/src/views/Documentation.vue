<template>
  <div class="page">

    <!-- ══ HERO — DOCUMENTACIÓN TÉCNICA ══ -->
    <div class="docs-hero" :style="{ backgroundImage: `url(${docsHeroImg})` }">
      <div class="docs-hero-overlay">
        <div class="docs-hero-content">
          <div class="docs-hero-eyebrow">EMASIVO · GESTIÓN DOCUMENTAL</div>
          <h1 class="docs-hero-title">Documentación Técnica</h1>
          <p class="docs-hero-sub">Actas, presentaciones, certificaciones y documentos oficiales de la operación técnica de la flota.</p>

          <div v-if="heroStats.length" class="docs-hero-stats">
            <div v-for="s in heroStats" :key="s.label" class="dh-stat">
              <div class="dh-stat-value">{{ s.value }}</div>
              <div class="dh-stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-header page-header--slim">
      <button class="btn-primary" @click="showUpload = !showUpload">↑ Subir Documento</button>
    </div>

    <transition name="slide">
      <div v-if="showUpload" class="card upload-card">
        <h3 class="card-title">Subir nuevo documento</h3>
        <div class="form-grid">
          <div class="fgroup">
            <label class="label">Título</label>
            <input v-model="form.title" class="input" placeholder="Ej: Normativa DOT 2025" />
          </div>
          <div class="fgroup">
            <label class="label">Categoría</label>
            <select v-model="form.category" class="input">
              <option v-for="c in CATEGORIES" :key="c">{{ c }}</option>
            </select>
          </div>
          <div class="fgroup form-full">
            <div class="drop-zone" @click="$refs.fi.click()" @dragover.prevent @drop.prevent="e => form.file = e.dataTransfer.files[0]">
              <span v-if="!form.file">📎 Arrastra tu archivo o haz clic (PDF, XLS, DOC, PPT...)</span>
              <span v-else style="color:var(--success)">✅ {{ form.file.name }}</span>
            </div>
            <input ref="fi" type="file" style="display:none" @change="e => form.file = e.target.files[0]" />
          </div>
        </div>
        <p v-if="uploadErr" class="err-msg">{{ uploadErr }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showUpload=false">Cancelar</button>
          <button class="btn-primary" :disabled="uploading||!form.file" @click="upload">{{ uploading?'Subiendo...':'↑ Subir' }}</button>
        </div>
      </div>
    </transition>

    <!-- Panel izquierdo + área de documentos -->
    <div class="docs-layout">

      <!-- Columna de categorías (igual que Manuales) -->
      <div class="card cat-panel">
        <h3 class="cat-title">Categorías</h3>
        <button class="cat-btn" :class="{active:!activeCat}" @click="activeCat=null">
          <span class="cat-icon" v-html="iconAll"></span>
          Todas
        </button>
        <button v-for="c in CATEGORIES" :key="c" class="cat-btn" :class="{active:activeCat===c}" @click="activeCat=c">
          <img v-if="catImage(c)" :src="catImage(c)" class="cat-icon-img" alt="" />
          <span v-else class="cat-icon" v-html="catIconSvg(c)"></span>
          {{ c }}
        </button>
      </div>

      <!-- Área de documentos -->
      <div class="docs-area">
        <div v-if="loading" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando...</p></div>
        <div v-else-if="filteredDocs.length===0" class="empty-state">
          <span class="empty-icon">📭</span>
          <p>No hay documentos{{ activeCat ? ` en "${activeCat}"` : ' cargados aún' }}</p>
          <p v-if="!activeCat" style="font-size:13px;margin-top:6px">Usa el botón "↑ Subir Documento" para agregar archivos</p>
        </div>
        <div v-else class="files-grid">
          <div v-for="doc in filteredDocs" :key="doc.id" class="card file-card">
            <div class="fc-top">
              <div class="fc-icon">{{ fileIcon(doc.ext) }}</div>
              <div class="fc-info">
                <a :href="doc.url" target="_blank" class="fc-name">{{ doc.title }}</a>
                <span class="fc-meta">{{ doc.category }} · {{ doc.ext }} · {{ doc.size_kb }} KB · {{ doc.uploaded_at }}</span>
              </div>
            </div>
            <div class="fc-actions">
              <a :href="doc.url" target="_blank" class="btn-secondary btn-sm">👁 Ver</a>
              <a :href="doc.url" :download="doc.title" class="btn-secondary btn-sm">⬇ Descargar</a>
              <button v-if="isAdmin()" class="btn-del-sm" @click="del(doc.id)">🗑</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

import docsHeroImg from '../assets/documentacion-hero.png'
import transmilenioLogo from '../assets/transmilenio-logo.png'
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'
const { isAdmin } = useAuth()

const CATEGORIES = [
  'Transmilenio',
  'Capacitaciones',
  'Mesa local presentación',
  'Presentación mensual',
  'Comité mantenimiento',
  'Capacitación operadores',
  'Capacitación técnicos',
  'Certificaciones flota',
  'RTM',
  'Auditoría'
]

const docs       = ref([])
const loading    = ref(true)
const showUpload = ref(false)
const uploading  = ref(false)
const uploadErr  = ref('')
const activeCat  = ref(null)
const form       = ref({ title:'', category:CATEGORIES[0], file:null })

const filteredDocs = computed(() =>
  activeCat.value ? docs.value.filter(d => d.category === activeCat.value) : docs.value
)

// Datos reales para el hero: total de documentos, categorías, tipos de archivo distintos
const heroStats = computed(() => {
  const tipos = new Set(docs.value.map(d => d.ext).filter(Boolean))
  return [
    { value: `${docs.value.length}`, label: 'Documentos' },
    { value: `${CATEGORIES.length}`, label: 'Categorías' },
    { value: `${tipos.size}`, label: 'Tipos de archivo' },
  ]
})

/* ════════════════════════════════════════════════════════════════
   ICONOS SVG COMO STRINGS (v-html) — 100% confiable en Vue 3
   ════════════════════════════════════════════════════════════════ */

const iconAll = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="14" y="3" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="3" y="14" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/><rect x="14" y="14" width="7" height="7" rx="1" fill="rgba(49,176,121,0.08)"/></svg>`

const svgCapacitaciones = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" fill="rgba(49,176,121,0.08)" stroke-linejoin="round"/><path d="M6 12v5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3v-5"/><circle cx="12" cy="11" r="1.5" fill="rgba(49,176,121,0.3)" stroke="none"/><path d="M12 16v2" stroke-width="1.5"/></svg>`

const svgMesaLocal = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" fill="rgba(49,176,121,0.06)"/><path d="M8 21h8" stroke-width="1.5"/><path d="M12 17v4" stroke-width="1.5"/><path d="M6 17h12" stroke-width="1.2"/><circle cx="12" cy="10" r="2" fill="rgba(49,176,121,0.15)" stroke="none"/><path d="M12 8V6" stroke-width="1.2"/></svg>`

const svgPresentacionMensual = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" fill="rgba(49,176,121,0.06)"/><path d="M16 2v4" stroke-width="2"/><path d="M8 2v4" stroke-width="2"/><path d="M3 10h18" stroke-width="1.5"/><rect x="7" y="14" width="4" height="2" rx="0.5" fill="rgba(49,176,121,0.2)" stroke="none"/><rect x="13" y="14" width="4" height="2" rx="0.5" fill="rgba(49,176,121,0.2)" stroke="none"/></svg>`

const svgComite = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="rgba(49,176,121,0.08)" stroke-linejoin="round"/></svg>`

const svgCapOperadores = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.5" fill="rgba(49,176,121,0.1)"/><path d="M4 20c0-3 3.5-5 8-5s8 2 8 5" fill="rgba(49,176,121,0.06)" stroke-linejoin="round"/><path d="M12 14v2" stroke-width="1.2"/><circle cx="12" cy="17" r="1" fill="rgba(49,176,121,0.3)" stroke="none"/></svg>`

const svgCapTecnicos = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" fill="rgba(49,176,121,0.08)" stroke-linejoin="round"/><path d="M4 14l2-2" stroke-width="1.5"/></svg>`

const svgCertificaciones = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="rgba(49,176,121,0.06)" stroke-linejoin="round"/><path d="M14 2v6h6" stroke-width="1.5"/><path d="M9 15l2 2 4-4" stroke-width="1.8"/><circle cx="12" cy="10" r="1" fill="rgba(49,176,121,0.3)" stroke="none"/></svg>`

const svgRTM = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" fill="rgba(49,176,121,0.06)"/><path d="M21 21l-4.35-4.35" stroke-width="2"/><circle cx="11" cy="11" r="3" fill="rgba(49,176,121,0.1)" stroke="none"/><path d="M11 8v6" stroke-width="1.2"/><path d="M8 11h6" stroke-width="1.2"/></svg>`

const svgAuditoria = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" fill="rgba(49,176,121,0.06)"/><path d="M3 9h18" stroke-width="1.5"/><path d="M9 21V9" stroke-width="1.2"/><rect x="6" y="12" width="3" height="4" rx="0.5" fill="rgba(49,176,121,0.15)" stroke="none"/><rect x="12" y="12" width="3" height="6" rx="0.5" fill="rgba(49,176,121,0.2)" stroke="none"/><rect x="16" y="12" width="3" height="3" rx="0.5" fill="rgba(49,176,121,0.1)" stroke="none"/></svg>`

const catIconSvg = c => {
  const map = {
    'Capacitaciones':          svgCapacitaciones,
    'Mesa local presentación': svgMesaLocal,
    'Presentación mensual':    svgPresentacionMensual,
    'Comité mantenimiento':    svgComite,
    'Capacitación operadores': svgCapOperadores,
    'Capacitación técnicos':   svgCapTecnicos,
    'Certificaciones flota':   svgCertificaciones,
    'RTM':                     svgRTM,
    'Auditoría':               svgAuditoria,
  }
  return map[c] || iconAll
}

const CAT_IMAGES = {
  'Transmilenio': transmilenioLogo,
}
const catImage = c => CAT_IMAGES[c] || null

const fileIcon = e => ({'PDF':'📄','XLS':'📊','XLSX':'📊','DOC':'📝','DOCX':'📝','PPT':'📑','PPTX':'📑','MP4':'🎬'}[e]||'📎')

const load = async () => {
  loading.value = true
  try { docs.value = (await axios.get('/api/docs')).data }
  catch {} finally { loading.value = false }
}

const upload = async () => {
  uploadErr.value = ''; uploading.value = true
  const fd = new FormData()
  fd.append('file', form.value.file)
  fd.append('title', form.value.title || form.value.file.name)
  fd.append('category', form.value.category)
  try {
    await axios.post('/api/docs/upload', fd)
    showUpload.value = false
    form.value = { title:'', category:CATEGORIES[0], file:null }
    await load()
  } catch(e) { uploadErr.value = e.response?.data?.detail || 'Error al subir' }
  finally { uploading.value = false }
}

const del = async id => {
  if (!confirm('¿Eliminar este documento?')) return
  try { await axios.delete(`/api/docs/${id}`); await load() } catch {}
}

onMounted(load)
</script>

<style scoped>
/* ══ HERO — DOCUMENTACIÓN TÉCNICA ══ */
.docs-hero {
  position: relative;
  height: 320px;
  margin: -32px -32px 32px;
  background-size: cover;
  background-position: center 40%;
  border-radius: 0 0 var(--radius) var(--radius);
  overflow: hidden;
}
@media(min-width: 900px)  { .docs-hero { height: 440px; } }
@media(min-width: 1300px) { .docs-hero { height: 500px; } }

.docs-hero-overlay {
  position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(6,46,35,0.88) 0%, rgba(6,46,35,0.6) 40%, rgba(6,46,35,0.1) 75%),
    linear-gradient(180deg, rgba(8,69,52,0.1) 0%, rgba(8,69,52,0.4) 45%, rgba(6,46,35,0.9) 100%);
  display: flex; align-items: flex-end;
  padding: 32px 40px;
}
.docs-hero-content { max-width: 720px; }
.docs-hero-eyebrow {
  font-size: 11px; font-weight: 800; letter-spacing: 2px;
  color: var(--accent); text-transform: uppercase; margin-bottom: 8px;
}
.docs-hero-title {
  font-size: clamp(24px, 3.4vw, 34px); font-weight: 900; color: #fff;
  line-height: 1.15; margin-bottom: 8px;
}
.docs-hero-sub {
  font-size: 14px; color: rgba(255,255,255,0.75); line-height: 1.5;
  max-width: 52ch; margin-bottom: 22px;
}
.docs-hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.dh-stat-value { font-size: 26px; font-weight: 900; color: #fff; line-height: 1; }
.dh-stat-label { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

.page-header--slim { justify-content: flex-end; margin-top: -8px; }

.cat-icon-img {
  width: 18px;
  height: 18px;
  object-fit: contain;
  border-radius: 3px;
  flex-shrink: 0;
}
.upload-card  { padding:24px; margin-bottom:24px; }
.card-title   { font-size:16px; font-weight:700; margin-bottom:16px; }
.form-grid    { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px; }
.form-full    { grid-column:1/-1; }
.fgroup       { display:flex; flex-direction:column; gap:6px; }
.drop-zone    { border:2px dashed var(--border); border-radius:10px; padding:24px; text-align:center; cursor:pointer; color:var(--text-muted); font-size:14px; transition:all 0.2s; }
.drop-zone:hover { border-color:var(--primary); color:var(--primary); }
.err-msg      { color:var(--danger); font-size:13px; margin-bottom:10px; }
.form-actions { display:flex; gap:10px; justify-content:flex-end; }

/* Layout igual que Manuales */
.docs-layout  { display:flex; gap:20px; align-items:flex-start; }
.cat-panel    { width:220px; flex-shrink:0; padding:20px; }
.cat-title    { font-size:13px; font-weight:700; margin-bottom:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--text-muted); }
.cat-btn      { width:100%; display:flex; align-items:center; gap:8px; padding:10px 12px; background:none; border:none; border-radius:8px; cursor:pointer; font-size:13px; color:var(--text-muted); text-align:left; transition:all 0.15s; margin-bottom:2px; font-family:inherit; }
.cat-btn:hover   { background:var(--bg); color:var(--text); }
.cat-btn.active  { background:var(--primary); color:#fff; font-weight:600; }

.docs-area    { flex:1; min-width:0; }
.files-grid   { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }

.file-card    { padding:18px; display:flex; flex-direction:column; gap:12px; transition:box-shadow 0.2s; }
.file-card:hover { box-shadow:var(--shadow-md); }
.fc-top       { display:flex; gap:12px; align-items:flex-start; }
.fc-icon      { width:44px; height:44px; background:var(--primary-light); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; }
.fc-name      { font-size:14px; font-weight:600; color:var(--primary); text-decoration:none; display:block; line-height:1.3; margin-bottom:4px; }
.fc-name:hover { text-decoration:underline; }
.fc-meta      { font-size:11px; color:var(--text-muted); line-height:1.4; }
.fc-actions   { display:flex; gap:8px; flex-wrap:wrap; }
.btn-sm       { padding:6px 12px !important; font-size:12px !important; }
.btn-del-sm   { background:#fee2e2; border:1px solid #fecaca; color:var(--danger); padding:6px 10px; border-radius:8px; cursor:pointer; font-size:12px; transition:all 0.2s; }
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
.cat-btn:nth-child(9) .cat-icon { animation-delay: 0.8s; }
.cat-btn:nth-child(10) .cat-icon { animation-delay: 0.9s; }
.cat-btn:nth-child(11) .cat-icon { animation-delay: 1.0s; }

@keyframes cat-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

.cat-btn:hover .cat-icon {
  animation: none;
  transform: scale(1.2) rotate(-6deg);
}

@media(max-width:768px){
  .docs-layout{flex-direction:column;}
  .cat-panel{width:100%;}
  .form-grid{grid-template-columns:1fr;}
  .docs-hero { height: 300px; margin: -16px -16px 24px; }
  .docs-hero-overlay { padding: 20px; }
  .docs-hero-stats { gap: 20px; }
}
</style>