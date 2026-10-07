<template>
  <div class="disp-root">

    <div v-if="!tieneDatos" class="card empty-card">
      <span class="empty-icon">📭</span>
      <p>Aún no hay datos de disponibilidad cargados.</p>
      <p class="empty-sub">Ve a la pestaña <strong>ICO</strong> y usa el botón "📊 Cargar Disponibilidad".</p>
    </div>

    <template v-else>
      <!-- ══ FILA POR UNIDAD ══ -->
      <div class="unidades-row">

        <!-- ── UF-10 ── -->
        <div class="card unidad-card" v-if="store.disponibilidad.e10">
          <div class="unidad-hdr">
            <div class="unidad-id">
              <span class="unidad-dot" style="background:#074e7a"></span>
              <div>
                <div class="unidad-name">UF-10 <span class="unidad-sub">EMASIVO10</span></div>
                <div class="unidad-fecha">Corte: {{ store.disponibilidad.e10.fecha_corte || '—' }}</div>
              </div>
            </div>
            <div class="unidad-kpi">
              <div class="uk-val" :class="pctClass(store.disponibilidad.e10.porcentaje)">
                {{ store.disponibilidad.e10.porcentaje }}%
              </div>
              <div class="uk-lbl">Disponibilidad</div>
            </div>
          </div>

          <div class="unidad-body">
            <!-- Donut disponibles vs taller -->
            <div class="donut-block">
              <svg viewBox="0 0 140 140" class="donut-svg">
                <circle cx="70" cy="70" r="52" fill="none" stroke="#E5E7EB" stroke-width="20"/>
                <circle cx="70" cy="70" r="52" fill="none" stroke="#074e7a" stroke-width="20"
                  :stroke-dasharray="`${donutDash(store.disponibilidad.e10)} ${donutGap(store.disponibilidad.e10)}`"
                  stroke-dashoffset="0"
                  style="transform:rotate(-90deg);transform-origin:70px 70px"/>
                <text x="70" y="66" text-anchor="middle" font-size="20" font-weight="900" fill="#084534">{{ store.disponibilidad.e10.disponibles }}</text>
                <text x="70" y="82" text-anchor="middle" font-size="9" fill="#64748b">disponibles</text>
              </svg>
              <div class="donut-legs">
                <div class="dl-item"><span class="dl-dot" style="background:#074e7a"></span>Disponibles <b>{{ store.disponibilidad.e10.disponibles }}</b></div>
                <div class="dl-item"><span class="dl-dot" style="background:#E5E7EB"></span>En taller <b>{{ store.disponibilidad.e10.no_disponibles }}</b></div>
                <div class="dl-item dl-total">Flota total <b>{{ store.disponibilidad.e10.flota_total }}</b></div>
              </div>
            </div>

            <!-- Causas por área -->
            <div class="causas-block">
              <div class="causas-title">Buses en taller por causa</div>
              <div class="bar-chart">
                <div v-for="a in store.disponibilidad.e10.por_area" :key="a.area" class="bar-row">
                  <span class="bar-label" :title="a.area">{{ a.area }}</span>
                  <div class="bar-track">
                    <div class="bar-fill" style="background:#074e7a"
                      :style="{ width: pct(a.total, maxArea(store.disponibilidad.e10)) + '%' }"></div>
                  </div>
                  <span class="bar-val">{{ a.total }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── UF-16 ── -->
        <div class="card unidad-card" v-if="store.disponibilidad.e16">
          <div class="unidad-hdr">
            <div class="unidad-id">
              <span class="unidad-dot" style="background:#248a7c"></span>
              <div>
                <div class="unidad-name">UF-16 <span class="unidad-sub">EMASIVO16</span></div>
                <div class="unidad-fecha">Corte: {{ store.disponibilidad.e16.fecha_corte || '—' }}</div>
              </div>
            </div>
            <div class="unidad-kpi">
              <div class="uk-val" :class="pctClass(store.disponibilidad.e16.porcentaje)">
                {{ store.disponibilidad.e16.porcentaje }}%
              </div>
              <div class="uk-lbl">Disponibilidad</div>
            </div>
          </div>

          <div class="unidad-body">
            <div class="donut-block">
              <svg viewBox="0 0 140 140" class="donut-svg">
                <circle cx="70" cy="70" r="52" fill="none" stroke="#E5E7EB" stroke-width="20"/>
                <circle cx="70" cy="70" r="52" fill="none" stroke="#248a7c" stroke-width="20"
                  :stroke-dasharray="`${donutDash(store.disponibilidad.e16)} ${donutGap(store.disponibilidad.e16)}`"
                  stroke-dashoffset="0"
                  style="transform:rotate(-90deg);transform-origin:70px 70px"/>
                <text x="70" y="66" text-anchor="middle" font-size="20" font-weight="900" fill="#084534">{{ store.disponibilidad.e16.disponibles }}</text>
                <text x="70" y="82" text-anchor="middle" font-size="9" fill="#64748b">disponibles</text>
              </svg>
              <div class="donut-legs">
                <div class="dl-item"><span class="dl-dot" style="background:#248a7c"></span>Disponibles <b>{{ store.disponibilidad.e16.disponibles }}</b></div>
                <div class="dl-item"><span class="dl-dot" style="background:#E5E7EB"></span>En taller <b>{{ store.disponibilidad.e16.no_disponibles }}</b></div>
                <div class="dl-item dl-total">Flota total <b>{{ store.disponibilidad.e16.flota_total }}</b></div>
              </div>
            </div>

            <div class="causas-block">
              <div class="causas-title">Buses en taller por causa</div>
              <div class="bar-chart">
                <div v-for="a in store.disponibilidad.e16.por_area" :key="a.area" class="bar-row">
                  <span class="bar-label" :title="a.area">{{ a.area }}</span>
                  <div class="bar-track">
                    <div class="bar-fill" style="background:#248a7c"
                      :style="{ width: pct(a.total, maxArea(store.disponibilidad.e16)) + '%' }"></div>
                  </div>
                  <span class="bar-val">{{ a.total }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ TABLA DETALLE MÓVILES EN TALLER ══ -->
      <div class="card tabla-card">
        <div class="tabla-hdr">
          <span class="tt">Móviles en Taller</span>
          <div class="hdr-tabs">
            <button class="hdr-tab" :class="{active: filtroUnidad==='todas'}" @click="filtroUnidad='todas'">Todas</button>
            <button class="hdr-tab" :class="{active: filtroUnidad==='UF10'}" @click="filtroUnidad='UF10'">UF-10</button>
            <button class="hdr-tab" :class="{active: filtroUnidad==='UF16'}" @click="filtroUnidad='UF16'">UF-16</button>
          </div>
          <span class="tb">{{ detalleFiltrado.length }}</span>
        </div>
        <div class="tscr">
          <div v-if="!detalleFiltrado.length" class="t-empty">Sin registros</div>
          <table v-else class="t">
            <thead>
              <tr>
                <th class="th th-l" style="width:60px">Unidad</th>
                <th class="th th-l" style="width:100px">Móvil</th>
                <th class="th th-l">Área / Causa</th>
                <th class="th th-l">Descripción</th>
                <th class="th th-r" style="width:80px">Días</th>
                <th class="th th-c" style="width:100px">Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r,i) in detalleFiltrado" :key="i" class="tr" :class="{alt:i%2===1}">
                <td class="td">
                  <span class="uf-badge" :style="{background: r.unidad==='UF10' ? '#074e7a' : '#248a7c'}">{{ r.unidad }}</span>
                </td>
                <td class="td td-bold">{{ r.movil }}</td>
                <td class="td td-muted">{{ r.area }}</td>
                <td class="td td-desc" :title="r.descripcion">{{ r.descripcion }}</td>
                <td class="td td-r" :class="diasClass(r.dias_inoperatividad)">{{ r.dias_inoperatividad }}</td>
                <td class="td td-c">
                  <span class="badge" :class="r.inmovilizado ? 'badge-danger' : 'badge-warning'">
                    {{ r.inmovilizado ? 'Inmovilizado' : 'En taller' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from './dashboardStore.js'

const store = useDashboardStore()
const filtroUnidad = ref('todas')

const tieneDatos = computed(() =>
  !!(store.disponibilidad.e10 || store.disponibilidad.e16)
)

const pct = (v, mx) => Math.round((v / (mx || 1)) * 100)
const maxArea = (u) => Math.max(1, ...(u?.por_area?.map(a => a.total) || [1]))

const pctClass = (p) => {
  if (p == null) return ''
  if (p >= 90) return 'uk-ok'
  if (p >= 75) return 'uk-warn'
  return 'uk-bad'
}

const diasClass = (d) => {
  if (d >= 10) return 'dias-bad'
  if (d >= 3) return 'dias-warn'
  return 'dias-ok'
}

const CIRC = 2 * Math.PI * 52
const donutDash = (u) => {
  if (!u || !u.flota_total) return 0
  return (u.disponibles / u.flota_total) * CIRC
}
const donutGap = (u) => CIRC - donutDash(u)

const detalleFiltrado = computed(() => {
  const e10 = (store.disponibilidad.e10?.detalle || []).map(r => ({ ...r, unidad: 'UF10' }))
  const e16 = (store.disponibilidad.e16?.detalle || []).map(r => ({ ...r, unidad: 'UF16' }))
  let lista = [...e10, ...e16]
  if (filtroUnidad.value !== 'todas') lista = lista.filter(r => r.unidad === filtroUnidad.value)
  return lista.sort((a, b) => b.dias_inoperatividad - a.dias_inoperatividad)
})
</script>

<style scoped>
.disp-root { display:flex; flex-direction:column; gap:14px; }

.empty-card { padding:60px 20px; text-align:center; color:#9CA3AF; }
.empty-icon { font-size:40px; display:block; margin-bottom:10px; }
.empty-sub  { font-size:12px; margin-top:6px; }

/* ── Fila por unidad ── */
.unidades-row {
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:14px;
}

.unidad-card { padding:18px 20px; display:flex; flex-direction:column; gap:14px; }
.unidad-hdr  { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.unidad-id   { display:flex; align-items:center; gap:10px; }
.unidad-dot  { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.unidad-name { font-size:15px; font-weight:800; color:#111827; }
.unidad-sub  { font-size:10.5px; font-weight:600; color:#9CA3AF; margin-left:6px; }
.unidad-fecha{ font-size:10.5px; color:#9CA3AF; margin-top:2px; }

.unidad-kpi { text-align:right; }
.uk-val  { font-size:26px; font-weight:900; line-height:1; }
.uk-lbl  { font-size:10px; color:#9CA3AF; text-transform:uppercase; letter-spacing:.4px; margin-top:2px; }
.uk-ok   { color:#22C55E; }
.uk-warn { color:#F59E0B; }
.uk-bad  { color:#EF4444; }

.unidad-body { display:grid; grid-template-columns: 190px 1fr; gap:16px; align-items:start; }

.donut-block { display:flex; flex-direction:column; align-items:center; gap:8px; }
.donut-svg   { width:150px; height:150px; }
.donut-legs  { display:flex; flex-direction:column; gap:5px; width:100%; }
.dl-item  { display:flex; align-items:center; gap:6px; font-size:11.5px; color:#374151; }
.dl-dot   { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.dl-total { border-top:1px solid #F3F4F6; padding-top:5px; margin-top:3px; font-weight:600; color:#111827; }

.causas-block { min-width:0; }
.causas-title { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; margin-bottom:10px; }
.bar-chart { display:flex; flex-direction:column; gap:9px; }
.bar-row   { display:flex; align-items:center; gap:8px; }
.bar-label { font-size:11px; color:#6B7280; width:150px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar-track { flex:1; background:#F3F4F6; border-radius:4px; height:12px; overflow:hidden; }
.bar-fill  { height:100%; border-radius:4px; transition:width .4s; }
.bar-val   { font-size:11px; font-weight:700; color:#111827; width:20px; text-align:right; }

/* ── Tabla detalle ── */
.tabla-card { overflow:hidden; }
.tabla-hdr {
  display:flex; align-items:center; gap:12px;
  height:44px; padding:0 16px; background:#0F5132; flex-wrap:wrap;
}
.tt { font-size:11px; font-weight:700; color:#fff; letter-spacing:.5px; text-transform:uppercase; }
.hdr-tabs { display:flex; gap:4px; margin-left:auto; }
.hdr-tab {
  padding:4px 12px; border-radius:14px; border:1px solid rgba(255,255,255,0.3);
  background:transparent; color:rgba(255,255,255,0.75); font-size:11px; font-weight:600;
  cursor:pointer; font-family:inherit; transition:all .15s;
}
.hdr-tab:hover  { background:rgba(255,255,255,0.1); color:#fff; }
.hdr-tab.active { background:#fff; color:#0F5132; border-color:#fff; }
.tb { font-size:10px; font-weight:700; color:#0F5132; background:rgba(255,255,255,0.92); padding:2px 9px; border-radius:10px; min-width:22px; text-align:center; }

.tscr { max-height:460px; overflow-y:auto; }
.tscr::-webkit-scrollbar { width:4px; }
.tscr::-webkit-scrollbar-track { background:#F3F4F6; }
.tscr::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:2px; }

.t-empty { padding:24px; text-align:center; font-size:12px; color:#9CA3AF; }
.t  { width:100%; border-collapse:collapse; }
.th { height:32px; padding:6px 12px; font-size:10px; font-weight:700; color:#0F5132; background:#EDF7F1; border-bottom:1.5px solid #C8E6D0; text-transform:uppercase; letter-spacing:.3px; position:sticky; top:0; white-space:nowrap; }
.th-l { text-align:left; }
.th-r { text-align:right; }
.th-c { text-align:center; }
.tr { transition:background .12s; }
.tr:hover { background:#F0FBF4 !important; }
.tr.alt { background:#F9FAFB; }
.td { padding:8px 12px; font-size:12px; color:#374151; border-bottom:1px solid #F3F4F6; vertical-align:middle; }
.td-bold { font-weight:700; color:#111827; white-space:nowrap; }
.td-muted { font-size:11.5px; color:#6B7280; white-space:nowrap; }
.td-desc { font-size:11.5px; max-width:280px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.td-r { text-align:right; font-weight:700; }
.td-c { text-align:center; }
.dias-ok   { color:#22C55E; }
.dias-warn { color:#F59E0B; }
.dias-bad  { color:#EF4444; }

.uf-badge { color:#fff; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; white-space:nowrap; }

/* ── Responsive ── */
@media(max-width:1000px) {
  .unidades-row { grid-template-columns: 1fr; }
}
@media(max-width:640px) {
  .unidad-body { grid-template-columns: 1fr; }
  .donut-block { flex-direction:row; flex-wrap:wrap; justify-content:center; }
  .bar-label { width:110px; }
}
</style>