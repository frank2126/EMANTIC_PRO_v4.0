<template>
  <div class="reader">

    <div class="reader-top">
      <button class="btn-secondary btn-sm" @click="$emit('close')">← Volver a documentos</button>
      <span class="reader-cat">{{ active?.category }}</span>
    </div>

    <!-- ── PESTAÑAS: un documento por pestaña (misma categoría) ── -->
    <div v-if="docs.length > 1" class="tabs-wrap">
      <button class="tabs-arrow" :disabled="!canLeft" aria-label="Pestañas anteriores" @click="scrollTabs(-1)">‹</button>
      <div ref="tabsEl" class="tabs-scroll" role="tablist" @scroll="updateArrows">
        <button
          v-for="d in docs" :key="d.id"
          class="rtab" :class="{ active: d.id === activeId }"
          role="tab" :aria-selected="d.id === activeId" :title="d.title"
          @click="select(d.id)">
          <span class="rtab-ext">{{ d.ext }}</span>
          <span class="rtab-title">{{ shortTitle(d.title) }}</span>
        </button>
      </div>
      <button class="tabs-arrow" :disabled="!canRight" aria-label="Pestañas siguientes" @click="scrollTabs(1)">›</button>
    </div>

    <div v-if="active" class="reader-grid">

      <!-- ── COLUMNA PRINCIPAL ── -->
      <main class="reader-main">
        <header class="doc-head">
          <h2 class="doc-title">{{ summary?.titulo || active.title }}</h2>
          <p v-if="summary?.subtitulo" class="doc-sub">{{ summary.subtitulo }}</p>
          <p v-if="summary" class="doc-meta">
            {{ summary.codigo }} · versión {{ summary.version }} · {{ summary.fecha }} · {{ summary.paginas }} páginas
          </p>
        </header>

        <div class="view-switch" role="tablist">
          <button class="vs-btn" :class="{ active: view === 'resumen' }" role="tab" :aria-selected="view === 'resumen'" :disabled="!summary" @click="view = 'resumen'">Resumen rápido</button>
          <button class="vs-btn" :class="{ active: view === 'pdf' }" role="tab" :aria-selected="view === 'pdf'" :disabled="!isPdf" @click="view = 'pdf'">Documento completo</button>
        </div>

        <div v-if="loading" class="state-box">Cargando resumen…</div>

        <!-- RESUMEN -->
        <template v-else-if="view === 'resumen' && summary">
          <p class="lead">{{ summary.resumen }}</p>

          <div class="facts">
            <div v-for="f in summary.datos_clave" :key="f.etiqueta" class="fact">
              <div class="fact-val">{{ f.valor }}</div>
              <div class="fact-lbl">{{ f.etiqueta }}</div>
            </div>
          </div>

          <section class="priority">
            <h3 class="priority-title">Lo que más importa en el taller</h3>
            <ul>
              <li v-for="(p, i) in summary.para_taller" :key="i">{{ p }}</li>
            </ul>
          </section>

          <div class="sec-tools">
            <input v-model="query" class="input sec-search" type="search" placeholder="Buscar en el resumen (ej: llantas, plazo, grúa)" aria-label="Buscar en el resumen" />
            <button class="btn-secondary btn-sm" @click="toggleAll">{{ allOpen ? 'Contraer todo' : 'Expandir todo' }}</button>
          </div>

          <p v-if="!visibleSections.length" class="state-box">No hay secciones que coincidan con «{{ query }}».</p>

          <article v-for="s in visibleSections" :id="`sec-${s.id}`" :key="s.id" class="sec" :class="{ open: isOpen(s.id) }">
            <button class="sec-head" :aria-expanded="isOpen(s.id)" @click="toggle(s.id)">
              <span class="sec-name">{{ s.titulo }}</span>
              <span class="sec-ref">{{ s.capitulo }} · pág. {{ s.paginas }}</span>
              <span class="sec-chev" aria-hidden="true">{{ isOpen(s.id) ? '−' : '+' }}</span>
            </button>

            <div v-show="isOpen(s.id)" class="sec-body">
              <p v-if="s.alerta" class="callout">{{ s.alerta }}</p>
              <ul class="bullets">
                <li v-for="(p, i) in s.puntos" :key="i">{{ p }}</li>
              </ul>

              <div v-for="(t, ti) in s.tablas || []" :key="ti" class="tbl-block">
                <h4 class="tbl-title">{{ t.titulo }}</h4>
                <div class="tbl-wrap">
                  <table class="tbl">
                    <thead><tr><th v-for="c in t.columnas" :key="c">{{ c }}</th></tr></thead>
                    <tbody>
                      <tr v-for="(row, ri) in t.filas" :key="ri">
                        <td v-for="(cell, ci) in row" :key="ci" :class="cellClass(t.columnas[ci])">
                          <span v-if="cell === 'Sí' || cell === 'No'" class="pill" :class="cell === 'Sí' ? 'pill-yes' : 'pill-no'">{{ cell }}</span>
                          <template v-else>{{ cell }}</template>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </article>

          <p v-if="summary.aviso" class="notice">{{ summary.aviso }}</p>
        </template>

        <!-- PDF COMPLETO -->
        <template v-else-if="view === 'pdf' && isPdf">
          <iframe class="pdf-frame" :src="`${active.url}#view=FitH`" :title="active.title"></iframe>
        </template>

        <!-- SIN RESUMEN -->
        <div v-else class="state-box">
          <p>Este documento todavía no tiene resumen de lectura rápida.</p>
          <p v-if="!isPdf" class="state-sub">Descárgalo desde el panel lateral para abrirlo.</p>
        </div>
      </main>

      <!-- ── PANEL LATERAL ── -->
      <aside class="reader-aside">
        <div class="aside-card">
          <h3 class="aside-title">Descargar</h3>
          <a class="btn-primary dl-btn" :href="active.url" :download="active.title">Descargar {{ active.ext }}</a>
          <a class="dl-link" :href="active.url" target="_blank" rel="noopener">Abrir en otra pestaña</a>
          <dl class="file-meta">
            <div><dt>Tamaño</dt><dd>{{ active.size_kb }} KB</dd></div>
            <div><dt>Subido</dt><dd>{{ active.uploaded_at }}</dd></div>
            <div v-if="active.uploaded_by"><dt>Por</dt><dd>{{ active.uploaded_by }}</dd></div>
          </dl>
        </div>

        <nav v-if="summary && view === 'resumen'" class="aside-card">
          <h3 class="aside-title">En este resumen</h3>
          <ol class="toc">
            <li v-for="s in summary.secciones" :key="s.id">
              <button class="toc-link" @click="goTo(s.id)">{{ s.titulo }}</button>
            </li>
          </ol>
        </nav>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps({
  docs:      { type: Array,  required: true },   // documentos de la misma categoría
  initialId: { type: String, required: true },
})
defineEmits(['close'])

const activeId = ref(props.initialId)
const active   = computed(() => props.docs.find(d => d.id === activeId.value) || props.docs[0] || null)
const isPdf    = computed(() => (active.value?.ext || '').toUpperCase() === 'PDF')

// Resúmenes ya consultados: { [docId]: objeto | null }
const cache   = reactive({})
const loading = ref(false)
const summary = computed(() => (active.value ? cache[active.value.id] : null) || null)

const view  = ref('resumen')
const query = ref('')
const open  = reactive({})

const shortTitle = t => {
  const base = (t || '').replace(/\.[a-z0-9]{2,4}$/i, '')
  return base.length > 30 ? base.slice(0, 30) + '…' : base
}

async function loadSummary(id) {
  if (id in cache) return
  loading.value = true
  try {
    const { data } = await axios.get(`/api/docs/${id}/resumen`)
    cache[id] = data.resumen || null
  } catch {
    cache[id] = null
  } finally {
    loading.value = false
  }
}

async function select(id) {
  activeId.value = id
  query.value = ''
  Object.keys(open).forEach(k => delete open[k])
  await loadSummary(id)
  // Sin resumen: ir directo al PDF si se puede
  view.value = cache[id] ? 'resumen' : (isPdf.value ? 'pdf' : 'resumen')
}

// ── Secciones (acordeón + búsqueda) ──
const norm = s => (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

const visibleSections = computed(() => {
  const all = summary.value?.secciones || []
  const q = norm(query.value.trim())
  if (!q) return all
  return all.filter(s => {
    const texto = [
      s.titulo, s.capitulo, s.alerta, ...(s.puntos || []),
      ...(s.tablas || []).flatMap(t => [t.titulo, ...t.filas.flat()]),
    ].join(' ')
    return norm(texto).includes(q)
  })
})

const searching = computed(() => !!query.value.trim())
const isOpen    = id => searching.value || !!open[id]
const toggle    = id => { open[id] = !open[id] }
const allOpen   = computed(() => visibleSections.value.length > 0 && visibleSections.value.every(s => isOpen(s.id)))
const toggleAll = () => {
  const target = !allOpen.value
  visibleSections.value.forEach(s => { open[s.id] = target })
}
const goTo = async id => {
  query.value = ''
  open[id] = true
  await nextTick()
  document.getElementById(`sec-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const cellClass = col => ({
  'c-code': col === 'Código',
  'c-num':  col === 'Puntos' || col === 'Plazo (días)',
  'c-pill': col === 'Inmoviliza',
})

// ── Flechas de las pestañas ──
const tabsEl   = ref(null)
const canLeft  = ref(false)
const canRight = ref(false)
function updateArrows() {
  const el = tabsEl.value
  if (!el) return
  canLeft.value  = el.scrollLeft > 4
  canRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}
function scrollTabs(dir) {
  tabsEl.value?.scrollBy({ left: dir * 260, behavior: 'smooth' })
}

onMounted(async () => {
  // Primer resumen: abrir la primera sección para mostrar cómo funciona
  await select(props.initialId)
  const first = summary.value?.secciones?.[0]
  if (first) open[first.id] = true
  await nextTick()
  updateArrows()
})
watch(() => props.docs.length, () => nextTick(updateArrows))
</script>

<style scoped>
.reader { display:flex; flex-direction:column; gap:16px; }

.reader-top { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.reader-cat { font-size:13px; color:var(--text-muted); font-weight:600; }

/* ── Pestañas ── */
.tabs-wrap { display:flex; align-items:stretch; gap:6px; border-bottom:1px solid var(--border); }
.tabs-scroll { display:flex; gap:4px; overflow-x:auto; flex:1; scrollbar-width:none; }
.tabs-scroll::-webkit-scrollbar { display:none; }
.tabs-arrow {
  background:none; border:none; font-size:22px; line-height:1; width:30px; cursor:pointer;
  color:var(--text-muted); border-radius:8px;
}
.tabs-arrow:hover:not(:disabled) { background:var(--bg); color:var(--text); }
.tabs-arrow:disabled { opacity:.25; cursor:default; }
.rtab {
  flex:0 0 auto; display:flex; align-items:center; gap:8px; max-width:280px;
  background:none; border:none; border-bottom:3px solid transparent; margin-bottom:-1px;
  padding:10px 14px; font-family:inherit; font-size:13px; font-weight:600;
  color:var(--text-muted); cursor:pointer; transition:color .15s, border-color .15s;
}
.rtab:hover { color:var(--text); }
.rtab.active { color:var(--primary); border-bottom-color:var(--primary); }
.rtab:focus-visible, .vs-btn:focus-visible, .sec-head:focus-visible, .toc-link:focus-visible, .tabs-arrow:focus-visible {
  outline:2px solid var(--primary); outline-offset:-2px;
}
.rtab-ext { font-size:10px; font-weight:800; background:var(--primary-light); color:var(--primary); border-radius:6px; padding:2px 6px; }
.rtab-title { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* ── Layout ── */
.reader-grid { display:grid; grid-template-columns:minmax(0,1fr) 280px; gap:24px; align-items:start; }
.reader-main { min-width:0; }
.reader-aside { position:sticky; top:calc(var(--nav-h, 64px) + 16px); display:flex; flex-direction:column; gap:14px; }

.doc-head { margin-bottom:16px; }
.doc-title { font-size:22px; font-weight:800; color:var(--text); line-height:1.25; margin-bottom:4px; }
.doc-sub   { font-size:14px; color:var(--text-muted); margin-bottom:6px; }
.doc-meta  { font-size:12px; color:var(--text-muted); }

.view-switch { display:inline-flex; background:var(--bg); border:1px solid var(--border); border-radius:10px; padding:3px; margin-bottom:18px; }
.vs-btn {
  background:none; border:none; padding:7px 16px; border-radius:8px; font-family:inherit;
  font-size:13px; font-weight:600; color:var(--text-muted); cursor:pointer;
}
.vs-btn.active { background:#fff; color:var(--primary); box-shadow:var(--shadow); }
.vs-btn:disabled { opacity:.4; cursor:default; }

.lead { font-size:15px; line-height:1.7; color:var(--text); max-width:72ch; margin-bottom:18px; }

.facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:20px; }
.fact { background:var(--bg); border:1px solid var(--border); border-radius:10px; padding:12px 14px; }
.fact-val { font-size:20px; font-weight:800; color:var(--primary); line-height:1.1; }
.fact-lbl { font-size:12px; color:var(--text-muted); margin-top:4px; line-height:1.35; }

.priority { background:var(--primary-light); border-left:4px solid var(--accent); border-radius:10px; padding:16px 20px; margin-bottom:22px; }
.priority-title { font-size:15px; font-weight:800; color:var(--primary); margin-bottom:8px; }
.priority ul { margin:0; padding-left:18px; display:flex; flex-direction:column; gap:7px; }
.priority li { font-size:13.5px; line-height:1.55; color:var(--text); }

.sec-tools { display:flex; gap:10px; align-items:center; margin-bottom:12px; flex-wrap:wrap; }
.sec-search { flex:1 1 260px; min-width:200px; }

/* ── Secciones ── */
.sec { border:1px solid var(--border); border-radius:12px; background:#fff; margin-bottom:10px; overflow:hidden; scroll-margin-top:calc(var(--nav-h, 64px) + 12px); }
.sec.open { border-color:var(--primary); }
.sec-head {
  width:100%; display:flex; align-items:center; gap:12px; text-align:left;
  background:none; border:none; padding:14px 18px; cursor:pointer; font-family:inherit;
}
.sec-head:hover { background:var(--bg); }
.sec-name { flex:1; font-size:14.5px; font-weight:700; color:var(--text); }
.sec-ref  { font-size:11.5px; color:var(--text-muted); white-space:nowrap; }
.sec-chev { width:22px; text-align:center; font-size:18px; font-weight:700; color:var(--primary); }
.sec-body { padding:2px 20px 18px; border-top:1px solid var(--border); }

.callout { margin:14px 0 4px; background:#fef3c7; color:#92400e; border-radius:8px; padding:10px 14px; font-size:13px; line-height:1.5; }
.bullets { margin:14px 0 0; padding-left:18px; display:flex; flex-direction:column; gap:9px; max-width:78ch; }
.bullets li { font-size:13.5px; line-height:1.6; color:var(--text); }

.tbl-block { margin-top:18px; }
.tbl-title { font-size:13px; font-weight:800; color:var(--primary); margin-bottom:8px; }
.tbl-wrap { overflow-x:auto; border:1px solid var(--border); border-radius:10px; }
.tbl { width:100%; border-collapse:collapse; font-size:12.5px; }
.tbl th { text-align:left; padding:9px 12px; font-size:11px; font-weight:700; color:var(--text-muted); background:var(--bg); border-bottom:1px solid var(--border); white-space:nowrap; }
.tbl td { padding:9px 12px; border-bottom:1px solid var(--border); vertical-align:top; line-height:1.45; }
.tbl tr:last-child td { border-bottom:none; }
.c-code { font-family:monospace; font-weight:700; color:var(--primary); white-space:nowrap; }
.c-num  { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
.c-pill { white-space:nowrap; }
.pill { display:inline-block; font-size:11px; font-weight:800; padding:2px 10px; border-radius:20px; }
.pill-yes { background:#fee2e2; color:#991b1b; }
.pill-no  { background:#f1f5f9; color:#64748b; }

.notice { font-size:12px; color:var(--text-muted); line-height:1.5; margin-top:18px; max-width:78ch; }

.pdf-frame { width:100%; height:78vh; border:1px solid var(--border); border-radius:12px; background:#fff; }
.state-box { padding:36px 16px; text-align:center; color:var(--text-muted); font-size:14px; border:1px dashed var(--border); border-radius:12px; }
.state-sub { font-size:13px; margin-top:6px; }

/* ── Panel lateral ── */
.aside-card { background:#fff; border:1px solid var(--border); border-radius:12px; padding:16px; }
.aside-title { font-size:13px; font-weight:800; color:var(--text); margin-bottom:12px; }
.dl-btn { display:flex; align-items:center; justify-content:center; width:100%; text-decoration:none; padding:11px 14px; }
.dl-link { display:block; text-align:center; margin-top:10px; font-size:12.5px; color:var(--primary); }
.file-meta { margin:14px 0 0; display:flex; flex-direction:column; gap:6px; }
.file-meta div { display:flex; justify-content:space-between; gap:10px; font-size:12px; }
.file-meta dt { color:var(--text-muted); }
.file-meta dd { margin:0; font-weight:600; color:var(--text); text-align:right; }

.toc { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:2px; max-height:46vh; overflow-y:auto; }
.toc-link {
  width:100%; text-align:left; background:none; border:none; padding:7px 8px; border-radius:6px;
  font-family:inherit; font-size:12.5px; line-height:1.35; color:var(--text-muted); cursor:pointer;
}
.toc-link:hover { background:var(--bg); color:var(--primary); }

@media (max-width: 960px) {
  .reader-grid { grid-template-columns:1fr; }
  .reader-aside { position:static; order:-1; }
  .toc { max-height:none; }
}
@media (max-width: 560px) {
  .sec-head { flex-wrap:wrap; }
  .sec-ref { order:3; flex-basis:100%; }
  .pdf-frame { height:65vh; }
}
@media (prefers-reduced-motion: reduce) {
  .rtab { transition:none; }
}
</style>