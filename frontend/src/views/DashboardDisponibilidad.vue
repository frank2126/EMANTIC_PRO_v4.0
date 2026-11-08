<template>
  <div class="disp-root">

    <div v-if="!tieneDatos" class="card empty-card">
      <span class="empty-icon">📭</span>
      <p>Aún no hay datos de disponibilidad cargados.</p>
      <p class="empty-sub">Ve a la pestaña <strong>ICO</strong> y usa «🤖 Actualizar con el bot» o «📊 Cargar Disponibilidad».</p>
    </div>

    <template v-else>
      <!-- ══ FILTROS ══ -->
      <section class="card slicers" aria-label="Filtros de disponibilidad">
        <div class="sl-grupo">
          <span class="sl-lbl">Unidad</span>
          <div class="sl-btns" role="group" aria-label="Unidad funcional">
            <button v-for="u in unidadesLista" :key="u.key" type="button" class="sl-btn"
              :class="['sl-btn--' + u.key.toLowerCase(), { active: sel.unidad.includes(u.key) }]" :aria-pressed="sel.unidad.includes(u.key)"
              @click="clickSel('unidad', u.key, $event)">{{ u.label }}</button>
          </div>
        </div>
        <div class="sl-grupo sl-grupo--grow">
          <span class="sl-lbl">Buscar</span>
          <input type="search" class="sl-input" v-model="busqueda" placeholder="Móvil, causa o descripción…" aria-label="Buscar móvil, causa o descripción" />
        </div>
        <div class="sl-acciones">
          <div class="sl-count" aria-live="polite"><span class="sl-count-n">{{ fmt(k.noDisp) }}</span><span class="sl-count-l">no disponibles</span></div>
          <button type="button" class="sl-reset" :disabled="!hayFiltros" @click="limpiarTodo">✕ Limpiar</button>
        </div>
      </section>

      <div v-if="haySel" class="sel-bar">
        <span class="sel-titulo">Filtrando por</span>
        <button v-for="c in chips" :key="c.dim + '|' + c.key" type="button" class="sel-chip" :title="'Quitar ' + c.texto" @click="quitar(c.dim, c.key)">
          {{ c.texto }} <span aria-hidden="true">✕</span>
        </button>
        <button type="button" class="sel-limpiar" @click="sel = SELECCION_VACIA()">Borrar selección</button>
      </div>
      <p v-else class="hint">Haz clic en una unidad, un motivo, una causa, una barra de antigüedad o una fila para filtrar todo el tablero. Ctrl + clic para elegir varios.</p>

      <!-- ══ KPIs ══ -->
      <div class="kpi-row">
        <div class="card kpi"><span class="kpi-l">Flota total</span><span class="kpi-n">{{ k.flota != null ? fmt(k.flota) : '—' }}</span></div>
        <div class="card kpi"><span class="kpi-l">Disponibles</span><span class="kpi-n kpi-ok">{{ k.disponibles != null ? fmt(k.disponibles) : '—' }}</span></div>
        <div class="card kpi kpi--pct" :class="'sem-' + claseSemaforo(k.porcentaje)">
          <span class="kpi-l">Disponibilidad</span><span class="kpi-n">{{ k.porcentaje != null ? k.porcentaje + '%' : '—' }}</span>
        </div>
        <div class="card kpi">
          <span class="kpi-l">No disponibles</span><span class="kpi-n kpi-bad">{{ fmt(k.noDisp) }}</span>
          <span v-if="k.noDisp !== k.noDispReal" class="kpi-sub">de {{ fmt(k.noDispReal) }}</span>
        </div>
        <div class="card kpi"><span class="kpi-l">Promedio de días</span><span class="kpi-n">{{ k.promedioDias }}</span></div>
        <div class="card kpi"><span class="kpi-l">Máximo de días</span><span class="kpi-n" :class="claseDias(k.maxDias)">{{ k.maxDias }}</span></div>
      </div>

      <!-- ══ UNIDADES ══ -->
      <div class="unidades-row">
        <div v-for="u in unidadesVista" :key="u.key" class="card unidad-card" :class="{ sel: sel.unidad.includes(u.key), dim: sel.unidad.length && !sel.unidad.includes(u.key) }">
          <button type="button" class="unidad-click" :aria-pressed="sel.unidad.includes(u.key)" :aria-label="'Filtrar por ' + u.label" @click="clickSel('unidad', u.key, $event)">
            <div class="unidad-hdr">
              <div class="unidad-id">
                <span class="unidad-dot" :style="{ background: u.color }"></span>
                <div>
                  <div class="unidad-name">{{ u.label }} <span class="unidad-sub">{{ u.sub }}</span></div>
                  <div class="unidad-fecha">Corte: {{ u.corte || '—' }}</div>
                </div>
              </div>
              <div class="unidad-kpi">
                <div class="uk-val" :class="'uk-' + claseSemaforo(u.porcentaje)">{{ u.porcentaje != null ? u.porcentaje + '%' : '—' }}</div>
                <div class="uk-lbl">Disponibilidad</div>
              </div>
            </div>
            <div class="unidad-body">
              <svg viewBox="0 0 140 140" class="donut-svg" role="img" :aria-label="u.label + ': ' + u.disponibles + ' disponibles de ' + u.flota">
                <circle cx="70" cy="70" r="52" fill="none" stroke="#E5E7EB" stroke-width="20" />
                <circle cx="70" cy="70" r="52" fill="none" :stroke="u.color" stroke-width="20" :stroke-dasharray="u.dona.dash + ' ' + u.dona.gap"
                  style="transform:rotate(-90deg);transform-origin:70px 70px" />
                <text x="70" y="66" text-anchor="middle" font-size="22" font-weight="900" fill="#084534">{{ u.disponibles ?? '—' }}</text>
                <text x="70" y="82" text-anchor="middle" font-size="9" fill="#64748b">disponibles</text>
              </svg>
              <div class="donut-legs">
                <div class="dl-item"><span class="dl-dot" :style="{ background: u.color }"></span>Disponibles <b>{{ u.disponibles ?? '—' }}</b></div>
                <div class="dl-item"><span class="dl-dot" style="background:#E5E7EB"></span>No disponibles <b>{{ u.noDisp }}</b></div>
                <div class="dl-item dl-total">Flota total <b>{{ u.flota ?? '—' }}</b></div>
                <div v-if="haySelSinUnidad" class="dl-item dl-filtro">En la selección <b>{{ u.enSeleccion }}</b></div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- ══ VISUALES ══ -->
      <div class="charts-row">
        <!-- Motivo -->
        <div class="card chart-card">
          <div class="chart-title">Por qué no está disponible</div>
          <div class="motivos">
            <button v-for="m in motivos" :key="m.key" type="button" class="motivo" :class="{ sel: m.seleccionado, dim: sel.motivo.length && !m.seleccionado }"
              :aria-pressed="m.seleccionado" :title="m.sub" @click="clickSel('motivo', m.key, $event)">
              <span class="motivo-top"><span class="motivo-dot" :style="{ background: m.color }"></span><span class="motivo-nom">{{ m.label }}</span><b class="motivo-n">{{ fmt(m.total) }}</b></span>
              <span class="motivo-track"><span class="motivo-fill" :style="{ width: m.pct + '%', background: m.color }"></span></span>
              <span class="motivo-sub">{{ m.sub }} · {{ m.pct }}%</span>
            </button>
          </div>
        </div>

        <!-- Causas -->
        <div class="card chart-card">
          <div class="chart-title">Causa / área <span class="chart-n">{{ areas.length }}</span></div>
          <div v-if="!areas.length" class="vacio">Sin datos para este filtro</div>
          <div v-else class="bar-chart">
            <button v-for="a in areas" :key="a.key" type="button" class="bar-row" :class="{ sel: a.seleccionado, dim: sel.area.length && !a.seleccionado }"
              :aria-pressed="a.seleccionado" :title="a.label + ': ' + a.total + ' buses, promedio ' + a.promedio + ' días'" @click="clickSel('area', a.key, $event)">
              <span class="bar-label">{{ a.label }}</span>
              <span class="bar-track"><span class="bar-fill" :style="{ width: pctDe(a.total, maxArea) + '%', background: colorMotivo(a.motivo) }"></span></span>
              <span class="bar-val">{{ a.total }}</span>
            </button>
          </div>
        </div>

        <!-- Antigüedad -->
        <div class="card chart-card">
          <div class="chart-title">Días sin operar</div>
          <div class="cols">
            <button v-for="b in buckets" :key="b.key" type="button" class="col" :class="{ sel: b.seleccionado, dim: sel.bucket.length && !b.seleccionado }"
              :aria-pressed="b.seleccionado" :aria-label="b.label + ': ' + b.total + ' buses'" :title="b.label + ': ' + b.total + ' buses (' + b.pct + '%)'" @click="clickSel('bucket', b.key, $event)">
              <span class="col-num">{{ b.total || '' }}</span>
              <span class="col-wrap"><span class="col-bar" :style="{ height: (b.total ? Math.max(4, pctDe(b.total, maxBucket)) : 2) + '%' }"></span></span>
              <span class="col-lbl">{{ b.label }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ══ TABLA ══ -->
      <div class="card tabla-card">
        <div class="tabla-hdr">
          <span class="tt">Móviles no disponibles</span>
          <span class="tb">{{ fmt(filas.length) }}</span>
          <button type="button" class="hdr-btn" :disabled="!filas.length" @click="descargarCSV">⬇ CSV</button>
        </div>
        <div class="tscr">
          <div v-if="!filas.length" class="t-empty">Sin registros para este filtro</div>
          <table v-else class="t">
            <thead>
              <tr>
                <th v-for="c in COLUMNAS" :key="c.key" class="th" :class="c.cls" :style="c.ancho ? { width: c.ancho } : null" scope="col"
                  :aria-sort="orden.key === c.key ? (orden.dir === 'asc' ? 'ascending' : 'descending') : 'none'">
                  <button type="button" class="th-btn" @click="ordenarPor(c.key)">{{ c.label }}<span class="th-flecha" aria-hidden="true">{{ orden.key === c.key ? (orden.dir === 'asc' ? '▲' : '▼') : '' }}</span></button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in visibles" :key="r.unidad + r.movil + i" class="tr" :class="{ alt: i % 2 === 1, sel: sel.movil.includes(r.movil) }"
                tabindex="0" :aria-selected="sel.movil.includes(r.movil)" @click="clickSel('movil', r.movil, $event)" @keydown.enter="clickSel('movil', r.movil, $event)">
                <td class="td"><span class="uf-badge" :style="{ background: colorUnidad(r.unidad) }">{{ r.unidad }}</span></td>
                <td class="td td-bold">{{ r.movil }}</td>
                <td class="td"><span class="mot-chip" :style="{ '--c': colorMotivo(r.motivo) }">{{ r.area }}</span></td>
                <td class="td td-desc" :class="{ 'td-desc--full': sel.movil.includes(r.movil) }" :title="r.descripcion">{{ r.descripcion || '—' }}</td>
                <td class="td td-r" :class="claseDias(r.dias)">{{ r.dias }}</td>
                <td class="td td-c"><span class="badge" :class="r.inmovilizado ? 'badge-danger' : 'badge-warning'">{{ r.inmovilizado ? 'Inmovilizado' : estadoTexto(r.motivo) }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-if="filas.length > limite" class="mas"><button type="button" class="hdr-btn hdr-btn--claro" @click="limite += PAGINA">Ver más ({{ fmt(filas.length - limite) }})</button></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import {
  UNIDADES, MOTIVOS, BUCKETS, SELECCION_VACIA, normalizar, aplicarBusqueda, aplicarSeleccion, haySeleccion, alternarSeleccion, quitarSeleccion,
  chipsSeleccion, contar, rankingAreas, kpis, claseSemaforo, claseDias, ordenar, csvDisponibilidad, donaUnidad,
} from './dispUtils.js'

const store = useDashboardStore()
const PAGINA = 100
const COLUMNAS = [
  { key: 'unidad', label: 'Unidad', cls: 'th-l', ancho: '70px' },
  { key: 'movil', label: 'Móvil', cls: 'th-l', ancho: '100px' },
  { key: 'area', label: 'Área / causa', cls: 'th-l', ancho: '190px' },
  { key: 'descripcion', label: 'Descripción', cls: 'th-l' },
  { key: 'dias', label: 'Días', cls: 'th-r', ancho: '80px' },
  { key: 'motivo', label: 'Estado', cls: 'th-c', ancho: '120px' },
]

const sel = ref(SELECCION_VACIA())
const busqueda = ref('')
const orden = ref({ key: 'dias', dir: 'desc' })
const limite = ref(PAGINA)

const fmt = n => Number(n || 0).toLocaleString('es-CO')
const pctDe = (v, mx) => Math.round((v / (mx || 1)) * 100)
const colorMotivo = k => (MOTIVOS.find(m => m.key === k) || {}).color || '#64748b'
const colorUnidad = k => (UNIDADES.find(u => u.key === k) || {}).color || '#64748b'
const estadoTexto = k => (k === 'taller' ? 'En taller' : k === 'patio' ? 'En patio' : 'Apagado')

const tieneDatos = computed(() => !!(store.disponibilidad.e10 || store.disponibilidad.e16))
const datos = computed(() => normalizar(store.disponibilidad))
const unidadesLista = computed(() => UNIDADES.filter(u => datos.value.unidades[u.key]))

// El buscador es un filtro duro; la selección cruzada se combina con él
const base = computed(() => aplicarBusqueda(datos.value.filas, busqueda.value))
const filtradas = computed(() => aplicarSeleccion(base.value, sel.value))

const haySel = computed(() => haySeleccion(sel.value))
const haySelSinUnidad = computed(() => Object.entries(sel.value).some(([d, ks]) => d !== 'unidad' && ks.length) || !!busqueda.value.trim())
const hayFiltros = computed(() => haySel.value || !!busqueda.value.trim())
const chips = computed(() => chipsSeleccion(sel.value))

const k = computed(() => kpis(datos.value.filas, filtradas.value, datos.value.unidades, sel.value.unidad))

// Cada visual muestra todas sus categorías aunque esté filtrada por sí misma (se resalta la elegida)
const motivos = computed(() => contar(aplicarSeleccion(base.value, sel.value, 'motivo'), r => r.motivo, MOTIVOS, sel.value.motivo))
const buckets = computed(() => contar(aplicarSeleccion(base.value, sel.value, 'bucket'), r => r.bucket, BUCKETS, sel.value.bucket))
const areas = computed(() => rankingAreas(aplicarSeleccion(base.value, sel.value, 'area'), sel.value.area))
const maxArea = computed(() => Math.max(1, ...areas.value.map(a => a.total)))
const maxBucket = computed(() => Math.max(1, ...buckets.value.map(b => b.total)))

const unidadesVista = computed(() => {
  const sinUnidad = aplicarSeleccion(base.value, sel.value, 'unidad')
  return unidadesLista.value.map(u => {
    const d = datos.value.unidades[u.key]
    return { ...u, ...d, dona: donaUnidad(d), enSeleccion: sinUnidad.filter(r => r.unidad === u.key).length }
  })
})

const filas = computed(() => ordenar(filtradas.value, orden.value.key, orden.value.dir))
const visibles = computed(() => filas.value.slice(0, limite.value))
watch(filtradas, () => { limite.value = PAGINA })

function clickSel(dim, key, ev) {
  sel.value = alternarSeleccion(sel.value, dim, key, !!(ev && (ev.ctrlKey || ev.metaKey || ev.shiftKey)))
}
const quitar = (dim, key) => { sel.value = quitarSeleccion(sel.value, dim, key) }
const limpiarTodo = () => { sel.value = SELECCION_VACIA(); busqueda.value = '' }

function ordenarPor(key) {
  orden.value = orden.value.key === key ? { key, dir: orden.value.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: key === 'dias' ? 'desc' : 'asc' }
}

function descargarCSV() {
  const blob = new Blob(['﻿' + csvDisponibilidad(filas.value)], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `disponibilidad_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
</script>

<style scoped>
.disp-root { display:flex; flex-direction:column; gap:14px; }
button { font-family: inherit; }

.empty-card { padding:60px 20px; text-align:center; color:#9CA3AF; }
.empty-icon { font-size:40px; display:block; margin-bottom:10px; }
.empty-sub  { font-size:12px; margin-top:6px; }
.vacio { padding:20px; text-align:center; font-size:12px; color:#9CA3AF; }

/* ── Filtros ── */
.slicers { display:flex; align-items:flex-end; gap:18px; flex-wrap:wrap; padding:12px 16px; }
.sl-grupo { display:flex; flex-direction:column; gap:4px; }
.sl-grupo--grow { flex:1; min-width:200px; }
.sl-lbl { font-size:10px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; }
.sl-btns { display:flex; gap:4px; }
.sl-btn { padding:6px 14px; border-radius:16px; border:1px solid #D1D5DB; background:#fff; color:#374151; font-size:12px; font-weight:600; cursor:pointer; transition:all .15s; }
.sl-btn:hover { border-color:#0F5132; }
.sl-btn.active { color:#fff; border-color:transparent; background:#0F5132; }
.sl-btn--uf10.active { background:#074e7a; }
.sl-btn--uf16.active { background:#248a7c; }
.sl-input { height:32px; padding:0 12px; border:1px solid #D1D5DB; border-radius:16px; font-size:12px; font-family:inherit; width:100%; box-sizing:border-box; }
.sl-input:focus { outline:2px solid #31b079; outline-offset:1px; }
.sl-acciones { display:flex; align-items:center; gap:12px; margin-left:auto; }
.sl-count { display:flex; align-items:baseline; gap:5px; }
.sl-count-n { font-size:20px; font-weight:900; color:#084534; }
.sl-count-l { font-size:11px; color:#6B7280; }
.sl-reset { padding:6px 12px; border-radius:16px; border:1px solid #D1D5DB; background:#fff; font-size:12px; font-weight:600; color:#374151; cursor:pointer; }
.sl-reset:disabled { opacity:.45; cursor:default; }
.sl-reset:not(:disabled):hover { border-color:#C0392B; color:#C0392B; }

.sel-bar { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.sel-titulo { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; margin-right:2px; }
.sel-chip { padding:3px 10px; border-radius:14px; border:0; background:#0F5132; color:#fff; font-size:11.5px; font-weight:600; cursor:pointer; }
.sel-chip:hover { background:#C0392B; }
.sel-limpiar { background:none; border:0; color:#0F5132; font-size:11.5px; font-weight:700; cursor:pointer; text-decoration:underline; }
.hint { font-size:11.5px; color:#6B7280; margin:0; }

/* ── KPIs ── */
.kpi-row { display:grid; grid-template-columns:repeat(6, 1fr); gap:12px; }
.kpi { padding:12px 14px; display:flex; flex-direction:column; gap:2px; }
.kpi-l { font-size:10px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; }
.kpi-n { font-size:26px; font-weight:900; color:#084534; line-height:1.1; }
.kpi-ok { color:#22A55E; }
.kpi-bad { color:#C0392B; }
.kpi-sub { font-size:11px; color:#6B7280; }
.sem-ok .kpi-n { color:#22A55E; } .sem-warn .kpi-n { color:#D97706; } .sem-bad .kpi-n { color:#C0392B; }
.dias-ok { color:#22A55E; } .dias-warn { color:#D97706; } .dias-bad { color:#C0392B; }

/* ── Unidades ── */
.unidades-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.unidad-card { padding:0; transition:opacity .2s, box-shadow .2s; }
.unidad-card.sel { box-shadow:0 0 0 2px #0F5132; }
.unidad-card.dim { opacity:.5; }
.unidad-click { all:unset; display:flex; flex-direction:column; gap:14px; padding:16px 20px; cursor:pointer; box-sizing:border-box; width:100%; }
.unidad-click:focus-visible { outline:2px solid #31b079; outline-offset:-2px; border-radius:12px; }
.unidad-hdr  { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.unidad-id   { display:flex; align-items:center; gap:10px; }
.unidad-dot  { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.unidad-name { font-size:15px; font-weight:800; color:#111827; }
.unidad-sub  { font-size:10.5px; font-weight:600; color:#9CA3AF; margin-left:6px; }
.unidad-fecha{ font-size:10.5px; color:#9CA3AF; margin-top:2px; }
.unidad-kpi { text-align:right; }
.uk-val  { font-size:26px; font-weight:900; line-height:1; }
.uk-lbl  { font-size:10px; color:#9CA3AF; text-transform:uppercase; letter-spacing:.4px; margin-top:2px; }
.uk-ok { color:#22C55E; } .uk-warn { color:#F59E0B; } .uk-bad { color:#EF4444; }
.unidad-body { display:flex; align-items:center; gap:20px; }
.donut-svg { width:130px; height:130px; flex-shrink:0; }
.donut-legs { display:flex; flex-direction:column; gap:6px; flex:1; }
.dl-item  { display:flex; align-items:center; gap:6px; font-size:12px; color:#374151; }
.dl-item b { margin-left:auto; }
.dl-dot   { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.dl-total { border-top:1px solid #F3F4F6; padding-top:6px; margin-top:2px; font-weight:600; color:#111827; }
.dl-filtro { color:#0F5132; font-weight:600; }

/* ── Visuales ── */
.charts-row { display:grid; grid-template-columns:1.1fr 1.2fr 1fr; gap:14px; }
.chart-card { padding:16px 18px; display:flex; flex-direction:column; gap:12px; min-width:0; }
.chart-title { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; }
.chart-n { margin-left:6px; background:#F3F4F6; border-radius:9px; padding:1px 7px; font-size:10px; }

.motivos { display:flex; flex-direction:column; gap:8px; }
.motivo { all:unset; box-sizing:border-box; display:flex; flex-direction:column; gap:5px; padding:9px 11px; border-radius:10px; border:1px solid #E5E7EB; cursor:pointer; transition:all .15s; }
.motivo:hover { border-color:#0F5132; background:#F7FBF8; }
.motivo:focus-visible { outline:2px solid #31b079; }
.motivo.sel { border-color:#0F5132; background:#EDF7F1; box-shadow:0 0 0 1px #0F5132; }
.motivo.dim, .bar-row.dim, .col.dim { opacity:.4; }
.motivo-top { display:flex; align-items:center; gap:8px; }
.motivo-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.motivo-nom { font-size:12.5px; font-weight:700; color:#111827; flex:1; }
.motivo-n { font-size:18px; font-weight:900; color:#084534; }
.motivo-track { height:6px; background:#F3F4F6; border-radius:3px; overflow:hidden; }
.motivo-fill { display:block; height:100%; border-radius:3px; transition:width .35s; }
.motivo-sub { font-size:10.5px; color:#6B7280; }

.bar-chart { display:flex; flex-direction:column; gap:4px; max-height:250px; overflow-y:auto; padding-right:4px; }
.bar-row { all:unset; box-sizing:border-box; display:flex; align-items:center; gap:8px; padding:4px 6px; border-radius:6px; cursor:pointer; }
.bar-row:hover { background:#F0FBF4; }
.bar-row:focus-visible { outline:2px solid #31b079; }
.bar-row.sel { background:#EDF7F1; box-shadow:inset 0 0 0 1px #0F5132; }
.bar-label { font-size:11px; color:#374151; width:140px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar-track { flex:1; background:#F3F4F6; border-radius:4px; height:12px; overflow:hidden; }
.bar-fill  { display:block; height:100%; border-radius:4px; transition:width .35s; }
.bar-val   { font-size:11px; font-weight:700; color:#111827; width:28px; text-align:right; }

.cols { display:flex; align-items:stretch; gap:6px; height:220px; }
.col { all:unset; box-sizing:border-box; flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; cursor:pointer; padding:4px 2px; border-radius:8px; min-width:0; }
.col:hover { background:#F0FBF4; }
.col:focus-visible { outline:2px solid #31b079; }
.col.sel { background:#EDF7F1; box-shadow:inset 0 0 0 1px #0F5132; }
.col-num { font-size:11px; font-weight:800; color:#084534; height:14px; }
.col-wrap { flex:1; width:100%; display:flex; align-items:flex-end; justify-content:center; }
.col-bar { display:block; width:70%; background:#31b079; border-radius:4px 4px 0 0; transition:height .35s; }
.col:nth-child(3) .col-bar { background:#F59E0B; } .col:nth-child(4) .col-bar, .col:nth-child(5) .col-bar { background:#C0392B; }
.col-lbl { font-size:10px; color:#6B7280; text-align:center; line-height:1.2; }

/* ── Tabla ── */
.tabla-card { overflow:hidden; }
.tabla-hdr { display:flex; align-items:center; gap:12px; height:44px; padding:0 16px; background:#0F5132; }
.tt { font-size:11px; font-weight:700; color:#fff; letter-spacing:.5px; text-transform:uppercase; }
.tb { font-size:10px; font-weight:700; color:#0F5132; background:rgba(255,255,255,.92); padding:2px 9px; border-radius:10px; min-width:22px; text-align:center; }
.hdr-btn { margin-left:auto; padding:4px 12px; border-radius:14px; border:1px solid rgba(255,255,255,.4); background:transparent; color:#fff; font-size:11px; font-weight:600; cursor:pointer; }
.hdr-btn:hover:not(:disabled) { background:rgba(255,255,255,.15); }
.hdr-btn:disabled { opacity:.5; cursor:default; }
.hdr-btn--claro { margin:0; border-color:#0F5132; color:#0F5132; }
.hdr-btn--claro:hover:not(:disabled) { background:#EDF7F1; }
.mas { padding:12px; text-align:center; }
.tscr { max-height:520px; overflow-y:auto; }
.tscr::-webkit-scrollbar { width:4px; }
.tscr::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:2px; }
.t-empty { padding:24px; text-align:center; font-size:12px; color:#9CA3AF; }
.t { width:100%; border-collapse:collapse; }
.th { height:32px; padding:0; background:#EDF7F1; border-bottom:1.5px solid #C8E6D0; position:sticky; top:0; z-index:1; }
.th-btn { all:unset; box-sizing:border-box; width:100%; padding:6px 12px; font-size:10px; font-weight:700; color:#0F5132; text-transform:uppercase; letter-spacing:.3px; cursor:pointer; white-space:nowrap; }
.th-btn:hover { background:#DDEFE4; }
.th-btn:focus-visible { outline:2px solid #31b079; outline-offset:-2px; }
.th-l .th-btn { text-align:left; } .th-r .th-btn { text-align:right; } .th-c .th-btn { text-align:center; }
.th-flecha { margin-left:4px; font-size:8px; }
.tr { transition:background .12s; cursor:pointer; }
.tr:hover { background:#F0FBF4 !important; }
.tr:focus-visible { outline:2px solid #31b079; outline-offset:-2px; }
.tr.alt { background:#F9FAFB; }
.tr.sel { background:#DDEFE4 !important; box-shadow:inset 3px 0 0 #0F5132; }
.td { padding:8px 12px; font-size:12px; color:#374151; border-bottom:1px solid #F3F4F6; vertical-align:middle; }
.td-bold { font-weight:700; color:#111827; }
.td-r { text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }
.td-c { text-align:center; }
.td-desc { max-width:380px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#4B5563; }
.td-desc--full { white-space:normal; overflow:visible; }
.uf-badge { color:#fff; font-size:10px; font-weight:800; padding:2px 8px; border-radius:10px; }
.mot-chip { font-size:11px; font-weight:600; color:#374151; padding:2px 8px; border-radius:10px; background:color-mix(in srgb, var(--c) 14%, white); border:1px solid color-mix(in srgb, var(--c) 40%, white); display:inline-block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:middle; }
.badge { font-size:10.5px; font-weight:700; padding:2px 9px; border-radius:10px; }
.badge-danger { background:#FDECEA; color:#C0392B; }
.badge-warning { background:#FEF3E2; color:#B45309; }

@media (max-width: 1100px) {
  .kpi-row { grid-template-columns:repeat(3, 1fr); }
  .charts-row { grid-template-columns:1fr 1fr; }
  .charts-row > :first-child { grid-column:1 / -1; }
}
@media (max-width: 760px) {
  .kpi-row { grid-template-columns:repeat(2, 1fr); }
  .unidades-row, .charts-row { grid-template-columns:1fr; }
  .sl-acciones { margin-left:0; width:100%; justify-content:space-between; }
  .unidad-body { flex-direction:column; align-items:flex-start; }
  .td-desc { max-width:200px; }
}
</style>
