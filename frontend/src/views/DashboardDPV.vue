<template>
  <div class="dpv-root">

    <!-- ══ FILTROS ══ -->
    <div class="filtros-bar">
      <div class="fg">
        <span class="fl">Franja</span>
        <div class="bg">
          <button class="fb" :class="{active: store.dpvFiltros.franja.includes('AM')}" @click="store.toggleFranjaDPV('AM')">A. M.</button>
          <button class="fb" :class="{active: store.dpvFiltros.franja.includes('PM')}" @click="store.toggleFranjaDPV('PM')">P. M.</button>
        </div>
      </div>
      <div class="fg">
        <span class="fl">Mes</span>
        <input type="month" v-model="store.dpvFiltros.mes" class="fd" />
      </div>
      <div class="fg">
        <span class="fl">Tipología</span>
        <div class="bg">
          <button class="fb" :class="{active: store.dpvFiltros.tipologia.includes('BUSETON')}" @click="store.toggleTipoDPV('BUSETON')">BUSETON</button>
          <button class="fb" :class="{active: store.dpvFiltros.tipologia.includes('PADRON')}"  @click="store.toggleTipoDPV('PADRON')">PADRÓN</button>
        </div>
      </div>
      <div class="fg">
        <span class="fl">Unidad</span>
        <div class="bg">
          <button class="fb fb-uf10" :class="{active: store.dpvFiltros.uf.includes('UF10')}" @click="store.toggleUFDPV('UF10')">
            <span class="uf-dot uf-z32"></span>UF-10
          </button>
          <button class="fb fb-uf16" :class="{active: store.dpvFiltros.uf.includes('UF16')}" @click="store.toggleUFDPV('UF16')">
            <span class="uf-dot uf-z34"></span>UF-16
          </button>
        </div>
      </div>
      <button class="fr" @click="store.resetFiltrosDPV()">✕ Limpiar</button>
      <div class="fi">
        <span class="fin">{{ store.dpvFiltrado.length }}</span>
        <span class="fil">eventos</span>
      </div>
    </div>

    <!-- ══ FILA SUPERIOR ══ -->
<div class="top-row">

  <!-- KPI + Dona -->
  <div class="card kpi-panel">
    <div class="kpi-blk">
      <div class="kl">No. EVENTOS</div>
      <div class="kn">{{ store.dpvFiltrado.length }}</div>
    </div>
    <div class="kpi-blk kpi-pct-blk">
      <div class="kl">PORCENTAJE</div>
      <div class="kn kn-pct">{{ store.dpvPorcentaje }}%</div>
    </div>
    <div class="dona-wrap">
      <div class="dona-lbl">TIPOLOGÍA</div>
      <svg viewBox="0 0 160 140" width="148" height="118">
        <circle cx="80" cy="74" r="52" fill="none" stroke="#E5E7EB" stroke-width="28"/>
        <circle v-for="(s,i) in store.dpvDona" :key="i"
          cx="80" cy="74" r="52" fill="none" :stroke="s.color" stroke-width="28"
          :stroke-dasharray="`${s.dash} ${s.gap}`"
          :stroke-dashoffset="-s.offset + CIRC*0.25"
          style="transform:rotate(-90deg);transform-origin:80px 74px"/>
        <text x="80" y="70" text-anchor="middle" font-size="17" font-weight="900" fill="#084534">{{ store.dpvFiltrado.length }}</text>
        <text x="80" y="84" text-anchor="middle" font-size="9" fill="#64748b">eventos</text>
      </svg>
      <div class="dona-legs">
        <div v-for="(s,i) in store.dpvDona" :key="i" class="dona-leg">
          <span class="dl-dot" :style="{background:s.color}"></span>
          <div>
            <div class="dl-t">{{ s.label }}</div>
            <div class="dl-c">{{ s.total }} ({{ s.pct }}%)</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Columna derecha: Mapa de calor + EMASIVO10 + EMASIVO16 -->
  <div class="right-col">

    <!-- Mapa de calor por DÍA -->
    <div class="card calor-panel">
      <div class="calor-title">No. EVENTOS POR MAPA CALOR</div>
      <div class="calor-chart">
        <div class="calor-eje-y">
          <span v-for="v in [maxHeatDia, Math.round(maxHeatDia/2), 0]" :key="v">{{ v }}</span>
        </div>
        <div class="calor-barras">
          <div v-for="d in store.dpvHeatmapDias" :key="d.fecha" class="calor-col">
            <span class="calor-num" :class="{invisible: d.total===0}">{{ d.total || '' }}</span>
            <div class="calor-barra-wrap">
              <div class="calor-barra"
                :style="{ height: h$(d.total,maxHeatDia)+'px', background: heatColorDPV(d.total, maxHeatDia) }"/>
            </div>
            <span class="calor-hora">{{ d.dia }}</span>
          </div>
        </div>
      </div>
      <div class="calor-leyenda">
        <span class="cl-dot" style="background:#22C55E"></span><span class="cl-lbl">1-3</span>
        <span class="cl-dot" style="background:#F59E0B"></span><span class="cl-lbl">4-7</span>
        <span class="cl-dot" style="background:#EF4444"></span><span class="cl-lbl">8+</span>
        <span class="cl-lbl" style="margin-left:8px">No. Eventos por día</span>
      </div>
    </div>

    <!-- DPV Mensual — EMASIVO10 -->
    <div class="card fleet-card">
      <div class="fleet-block">
        <div class="fleet-header">
          <div class="fleet-id">
            <span class="fleet-dot" style="background:#1f6fb3"></span>
            <div>
              <div class="fleet-name">EMASIVO10</div>
              <div class="fleet-sub">DPV mensual · Flota</div>
            </div>
          </div>
          <div class="fleet-kpi" v-if="e10Latest">
            <div class="fk-value">{{ e10Latest.dpv?.toLocaleString('es-CO') }} <span class="fk-unit">km</span></div>
            <div class="fk-delta" :class="e10DeltaClass">{{ e10DeltaLabel }}</div>
            <span class="fk-status" :style="{background:e10StatusColor+'1A', color:e10StatusColor}">{{ e10StatusLabel }}</span>
          </div>
        </div>

        <div class="fleet-legend">
          <span class="lg-chip" style="background:#1f6fb31a;color:#1f6fb3">● DPV General</span>
          <span class="lg-chip lg-chip-dash" style="color:#22C55E">- - Estándar 10.000 km</span>
          <span class="lg-chip lg-chip-dash" style="color:#EF4444">- - Crítico 7.000 km</span>
        </div>

        <div v-if="!store.dpvMensual.e10.length" class="t-empty">Sin datos</div>
        <svg v-else viewBox="0 0 900 130" class="mensual-svg" preserveAspectRatio="none">
          <defs>
            <linearGradient id="fillE10" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#1f6fb3" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="#1f6fb3" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line v-for="(t,i) in e10Ticks" :key="'g10-'+i" :x1="PAD_LEFT" :x2="900-PAD_RIGHT" :y1="t.y" :y2="t.y" class="grid-line" />
          <text v-for="(t,i) in e10Ticks" :key="'y10-'+i" :x="PAD_LEFT-8" :y="t.y+4" class="axis-txt" text-anchor="end">{{ t.label }}</text>
          <path :d="e10EstandarPath" class="ref-line ref-green" />
          <path :d="e10CriticoPath" class="ref-line ref-red" />
          <path :d="e10AreaPath" fill="url(#fillE10)" stroke="none" />
          <path :d="e10Path" class="main-line" stroke="#1f6fb3" />
          <g v-for="(p,i) in e10Points" :key="'p10-'+i">
            <circle :cx="p.x" :cy="p.y" r="6"
              :fill="dpvStatusColor(store.dpvMensual.e10[i]?.dpv, store.dpvMensual.e10[i]?.estandar, store.dpvMensual.e10[i]?.critico)"
              opacity="0.16" />
            <circle :cx="p.x" :cy="p.y" r="3.2"
              :fill="dpvStatusColor(store.dpvMensual.e10[i]?.dpv, store.dpvMensual.e10[i]?.estandar, store.dpvMensual.e10[i]?.critico)"
              stroke="#fff" stroke-width="1.6" />
            <text :x="p.x" :y="p.y-9" class="pt-txt" text-anchor="middle">{{ store.dpvMensual.e10[i]?.dpv?.toLocaleString('es-CO') }}</text>
            <text :x="p.x" :y="140-24" class="x-txt" text-anchor="middle">{{ store.dpvMensual.e10[i]?.mes_label }}</text>
          </g>
        </svg>
      </div>
    </div>

    <!-- DPV Mensual — EMASIVO16 -->
    <div class="card fleet-card">
      <div class="fleet-block">
        <div class="fleet-header">
          <div class="fleet-id">
            <span class="fleet-dot" style="background:#16a34a"></span>
            <div>
              <div class="fleet-name">EMASIVO16</div>
              <div class="fleet-sub">DPV mensual · Flota</div>
            </div>
          </div>
          <div class="fleet-kpi" v-if="e16Latest">
            <div class="fk-value">{{ e16Latest.dpv?.toLocaleString('es-CO') }} <span class="fk-unit">km</span></div>
            <div class="fk-delta" :class="e16DeltaClass">{{ e16DeltaLabel }}</div>
            <span class="fk-status" :style="{background:e16StatusColor+'1A', color:e16StatusColor}">{{ e16StatusLabel }}</span>
          </div>
        </div>

        <div class="fleet-legend">
          <span class="lg-chip" style="background:#16a34a1a;color:#16a34a">● DPV General</span>
          <span class="lg-chip lg-chip-dash" style="color:#22C55E">- - Estándar 10.000 km</span>
          <span class="lg-chip lg-chip-dash" style="color:#EF4444">- - Crítico 7.000 km</span>
        </div>

        <div v-if="!store.dpvMensual.e16.length" class="t-empty">Sin datos</div>
        <svg v-else viewBox="0 0 900 130" class="mensual-svg" preserveAspectRatio="none">
          <defs>
            <linearGradient id="fillE16" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#16a34a" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="#16a34a" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line v-for="(t,i) in e16Ticks" :key="'g16-'+i" :x1="PAD_LEFT" :x2="900-PAD_RIGHT" :y1="t.y" :y2="t.y" class="grid-line" />
          <text v-for="(t,i) in e16Ticks" :key="'y16-'+i" :x="PAD_LEFT-8" :y="t.y+4" class="axis-txt" text-anchor="end">{{ t.label }}</text>
          <path :d="e16EstandarPath" class="ref-line ref-green" />
          <path :d="e16CriticoPath" class="ref-line ref-red" />
          <path :d="e16AreaPath" fill="url(#fillE16)" stroke="none" />
          <path :d="e16Path" class="main-line" stroke="#16a34a" />
          <g v-for="(p,i) in e16Points" :key="'p16-'+i">
            <circle :cx="p.x" :cy="p.y" r="6"
              :fill="dpvStatusColor(store.dpvMensual.e16[i]?.dpv, store.dpvMensual.e16[i]?.estandar, store.dpvMensual.e16[i]?.critico)"
              opacity="0.16" />
            <circle :cx="p.x" :cy="p.y" r="3.2"
              :fill="dpvStatusColor(store.dpvMensual.e16[i]?.dpv, store.dpvMensual.e16[i]?.estandar, store.dpvMensual.e16[i]?.critico)"
              stroke="#fff" stroke-width="1.6" />
            <text :x="p.x" :y="p.y-9" class="pt-txt" text-anchor="middle">{{ store.dpvMensual.e16[i]?.dpv?.toLocaleString('es-CO') }}</text>
            <text :x="p.x" :y="140-24" class="x-txt" text-anchor="middle">{{ store.dpvMensual.e16[i]?.mes_label }}</text>
          </g>
        </svg>
      </div>
    </div>

  </div><!-- fin right-col -->
</div><!-- fin top-row -->

    <!-- ══ PANEL TABLAS — GRID COMPLETO ══ -->
    <div class="tablas-grid">

      <!-- ── COL 1: Causas apiladas ── -->
      <div class="tcol-stack">



            <div class="tblk tblk-flex">
              <div class="thdr">
                <span class="tt">Causas por Móvil</span>
                <span class="tb">{{ store.dpvCausaMovil.length }}</span>
              </div>
              <div class="tscr tscr-flex">
            <div v-if="!store.dpvCausaMovil.length" class="t-empty">Sin datos</div>
            <table v-else class="t">
              <thead>
                <tr>
                  <th class="th th-l" style="width:95px">Móvil</th>
                  <th class="th th-l">Causa</th>
                  <th class="th th-r" style="width:36px">No.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r,i) in store.dpvCausaMovil.slice(0,50)" :key="i"
                    class="tr" :class="{alt:i%2===1}">
                  <td class="td td-bold" style="width:95px;white-space:nowrap">{{ r.movil }}</td>
                  <td class="td td-muted">{{ r.causa || '—' }}</td>
                  <td class="td td-r td-bold">{{ r.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── COL 2: Detalle Eventos ── -->
      <div class="tcol-single">
        <div class="tblk tblk-flex">
          <div class="thdr">
            <span class="tt">Detalle Eventos</span>
            <span class="tb">{{ store.dpvFiltrado.length }}</span>
          </div>
          <div class="tscr tscr-flex">
            <div v-if="!store.dpvFiltrado.length" class="t-empty">Sin datos</div>
            <table v-else class="t">
              <thead>
                <tr>
                  <th class="th th-l" style="min-width:95px">Móvil</th>
                  <th class="th th-l">Causa</th>
                  <th class="th th-c" style="width:46px">Día</th>
                  <th class="th th-c" style="width:52px">Hora</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r,i) in store.dpvFiltrado.slice(0,300)" :key="r.id||i"
                    class="tr" :class="{alt:i%2===1}">
                  <td class="td td-bold" style="white-space:nowrap;min-width:95px">{{ r.movil || '—' }}</td>
                  <td class="td td-muted" style="min-width:140px">{{ r.causa_inmovilizacion || '—' }}</td>
                  <td class="td td-c td-dia">{{ (r.dia_semana||'').slice(0,3) || '—' }}</td>
                  <td class="td td-c td-hora">{{ (r.hora||'').slice(0,5) || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── COL 4: Ruta ── -->
      <div class="tcol-single">
        <div class="tblk tblk-flex">
          <div class="thdr">
            <span class="tt">No. Eventos Ruta</span>
            <span class="tb">{{ store.dpvRutas.length }}</span>
          </div>
          <div class="tscr tscr-flex">
            <div v-if="!store.dpvRutas.length" class="t-empty">Sin datos</div>
            <table v-else class="t">
              <thead>
                <tr>
                  <th class="th th-l">Ruta</th>
                  <th class="th th-r" style="width:120px">No. Eventos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r,i) in store.dpvRutas" :key="i"
                    class="tr" :class="{alt:i%2===1}">
                  <td class="td">{{ r.ruta }}</td>
                  <td class="td">
                    <div class="brow">
                      <div class="bbar bbar-t" :style="{width: pct(r.total, store.dpvRutas[0]?.total||1)+'%'}"></div>
                      <span class="bnum">{{ r.total }}</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── COL 5: Móvil ── -->
      <div class="tcol-single">
        <div class="tblk tblk-flex">
          <div class="thdr">
            <span class="tt">No. Eventos por Móvil</span>
            <span class="tb">{{ store.dpvMoviles.length }}</span>
          </div>
          <div class="tscr tscr-flex">
            <div v-if="!store.dpvMoviles.length" class="t-empty">Sin datos</div>
            <div v-else class="mvl">
              <div v-for="(r,i) in store.dpvMoviles" :key="i"
                   class="mi" :class="{mia:i%2===1}">
                <span class="mlbl">{{ r.movil }}</span>
                <div class="mtrk">
                  <div class="mfil" :style="{width: pct(r.total, store.dpvMoviles[0]?.total||1)+'%'}"></div>
                </div>
                <span class="mnum">{{ r.total }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div><!-- fin tablas-grid -->
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useDashboardStore } from './dashboardStore.js'

const store = useDashboardStore()
const CIRC  = 2 * Math.PI * 52

// ── Mapa de calor por DÍA ──
const maxHeatDia = computed(() => Math.max(1, ...store.dpvHeatmapDias.map(d => d.total)))
const maxCausa   = computed(() => Math.max(1, ...store.dpvCausas.map(c => c.total)))

const h$ = (val, max) => {
  if (!max || max <= 0) return 0
  return val === 0 ? 2 : Math.max(4, Math.round((val / max) * 80))
}
const heatColorDPV = (val, max) => {
  if (!val || val === 0) return '#E5E7EB'
  const r = val / (max || 1)
  if (r >= 0.7) return '#EF4444'
  if (r >= 0.4) return '#F59E0B'
  return '#22C55E'
}
const pct = (v, mx) => Math.round((v / mx) * 100)
const causaColor = (v, mx) => {
  const r = v / mx
  if (r >= 0.7) return '#EF4444'
  if (r >= 0.4) return '#F59E0B'
  return '#22C55E'
}

// ══ DPV MENSUAL POR KILOMETRAJE — gráficas lineales (SVG puro) ══
onMounted(() => {
  if (!store.dpvMensual.e10.length && !store.dpvMensual.e16.length) {
    store.cargarDpvMensual()
  }
})

const CHART_W = 900, CHART_H = 130
const PAD_LEFT = 55, PAD_RIGHT = 15, PAD_TOP = 14, PAD_BOTTOM = 26

// Calcula un rango "redondo" (múltiplos de 5.000/10.000/etc) para que el eje Y
// se vea como en el reporte de referencia (20.000 / 15.000 / 10.000 / 5.000 ...)
function niceStep(rawStep) {
  const mag  = Math.pow(10, Math.floor(Math.log10(rawStep || 1)))
  const norm = rawStep / mag
  let niceNorm
  if (norm < 1.5) niceNorm = 1
  else if (norm < 3) niceNorm = 2
  else if (norm < 7) niceNorm = 5
  else niceNorm = 10
  return niceNorm * mag
}

function buildScale(data, estandar, critico) {
  const vals  = data.map(d => d.dpv).concat([estandar, critico])
  const rawMin = Math.min(...vals)
  const rawMax = Math.max(...vals)
  const step   = niceStep((rawMax - rawMin) / 4 || rawMax * 0.2 || 1000)
  const minV   = Math.max(0, Math.floor(rawMin / step) * step - step)
  const maxV   = Math.ceil(rawMax / step) * step + step * 0.15
  return { minV, maxV, step }
}
function scaleY(v, minV, maxV) {
  return PAD_TOP + (1 - (v - minV) / ((maxV - minV) || 1)) * (CHART_H - PAD_TOP - PAD_BOTTOM)
}
function scaleX(i, n) {
  const usableW = CHART_W - PAD_LEFT - PAD_RIGHT
  return PAD_LEFT + (n > 1 ? (i / (n - 1)) * usableW : usableW / 2)
}
function buildLine(data, minV, maxV) {
  const n = data.length
  if (!n) return ''
  return data.map((d, i) => {
    const x = scaleX(i, n)
    const y = scaleY(d.dpv, minV, maxV)
    return `${i === 0 ? 'M' : 'L'}${x},${y}`
  }).join(' ')
}
function buildFlatLine(value, n, minV, maxV) {
  if (!n) return ''
  const y  = scaleY(value, minV, maxV)
  const x1 = scaleX(0, n)
  const x2 = scaleX(n - 1, n)
  return `M${x1},${y} L${x2},${y}`
}
function buildPoints(data, minV, maxV) {
  const n = data.length
  return data.map((d, i) => ({ x: scaleX(i, n), y: scaleY(d.dpv, minV, maxV) }))
}
function buildTicks(minV, maxV, step) {
  const ticks = []
  for (let v = Math.ceil(minV / step) * step; v <= maxV; v += step) {
    ticks.push({ y: scaleY(v, minV, maxV), label: Math.round(v).toLocaleString('es-CO') })
  }
  return ticks
}
// ── Color semáforo por umbral (mismo criterio del mapa de calor) ──
function dpvStatusColor(value, estandar = 10000, critico = 7000) {
  if (value == null) return '#9CA3AF'
  if (value >= estandar) return '#22C55E'
  if (value <= critico) return '#EF4444'
  return '#F59E0B'
}

// ── Área degradada bajo la línea ──
function buildAreaPath(data, minV, maxV) {
  const n = data.length
  if (!n) return ''
  const baseY = scaleY(minV, minV, maxV)
  let d = `M${scaleX(0, n)},${baseY} `
  data.forEach((pt, i) => { d += `L${scaleX(i, n)},${scaleY(pt.dpv, minV, maxV)} ` })
  d += `L${scaleX(n - 1, n)},${baseY} Z`
  return d
}

// ── Helpers de KPI por flota (último valor, variación, estado) ──
function fleetKpi(data) {
  const latest = data[data.length - 1]
  const prev   = data[data.length - 2]
  const delta  = latest && prev ? latest.dpv - prev.dpv : null
  const est    = latest?.estandar || 10000
  const crit   = latest?.critico || 7000
  const color  = latest ? dpvStatusColor(latest.dpv, est, crit) : '#9CA3AF'
  const label  = !latest ? '' : latest.dpv >= est ? 'Sobre estándar' : latest.dpv <= crit ? 'Crítico' : 'En alerta'
  const deltaLabel = delta == null ? '' : `${delta >= 0 ? '▲' : '▼'} ${Math.abs(delta).toLocaleString('es-CO')} km vs mes anterior`
  const deltaClass = delta == null ? '' : (delta >= 0 ? 'fk-up' : 'fk-down')
  return { latest, deltaLabel, deltaClass, color, label }
}

const e10Scale = computed(() => {
  const d = store.dpvMensual.e10
  if (!d.length) return { minV: 0, maxV: 1, step: 1 }
  return buildScale(d, d[0]?.estandar || 10000, d[0]?.critico || 7000)
})
const e10Path         = computed(() => buildLine(store.dpvMensual.e10, e10Scale.value.minV, e10Scale.value.maxV))
const e10EstandarPath = computed(() => buildFlatLine(store.dpvMensual.e10[0]?.estandar || 10000, store.dpvMensual.e10.length, e10Scale.value.minV, e10Scale.value.maxV))
const e10CriticoPath  = computed(() => buildFlatLine(store.dpvMensual.e10[0]?.critico || 7000, store.dpvMensual.e10.length, e10Scale.value.minV, e10Scale.value.maxV))
const e10Points       = computed(() => buildPoints(store.dpvMensual.e10, e10Scale.value.minV, e10Scale.value.maxV))
const e10Ticks        = computed(() => buildTicks(e10Scale.value.minV, e10Scale.value.maxV, e10Scale.value.step))

const e16Scale = computed(() => {
  const d = store.dpvMensual.e16
  if (!d.length) return { minV: 0, maxV: 1, step: 1 }
  return buildScale(d, d[0]?.estandar || 10000, d[0]?.critico || 7000)
})
const e16Path         = computed(() => buildLine(store.dpvMensual.e16, e16Scale.value.minV, e16Scale.value.maxV))
const e16EstandarPath = computed(() => buildFlatLine(store.dpvMensual.e16[0]?.estandar || 10000, store.dpvMensual.e16.length, e16Scale.value.minV, e16Scale.value.maxV))
const e16CriticoPath  = computed(() => buildFlatLine(store.dpvMensual.e16[0]?.critico || 7000, store.dpvMensual.e16.length, e16Scale.value.minV, e16Scale.value.maxV))
const e16Points       = computed(() => buildPoints(store.dpvMensual.e16, e16Scale.value.minV, e16Scale.value.maxV))
const e16Ticks        = computed(() => buildTicks(e16Scale.value.minV, e16Scale.value.maxV, e16Scale.value.step))

const e10AreaPath = computed(() => buildAreaPath(store.dpvMensual.e10, e10Scale.value.minV, e10Scale.value.maxV))
const e16AreaPath = computed(() => buildAreaPath(store.dpvMensual.e16, e16Scale.value.minV, e16Scale.value.maxV))

const e10Kpi = computed(() => fleetKpi(store.dpvMensual.e10))
const e10Latest      = computed(() => e10Kpi.value.latest)
const e10DeltaLabel  = computed(() => e10Kpi.value.deltaLabel)
const e10DeltaClass  = computed(() => e10Kpi.value.deltaClass)
const e10StatusColor = computed(() => e10Kpi.value.color)
const e10StatusLabel = computed(() => e10Kpi.value.label)

const e16Kpi = computed(() => fleetKpi(store.dpvMensual.e16))
const e16Latest      = computed(() => e16Kpi.value.latest)
const e16DeltaLabel  = computed(() => e16Kpi.value.deltaLabel)
const e16DeltaClass  = computed(() => e16Kpi.value.deltaClass)
const e16StatusColor = computed(() => e16Kpi.value.color)
const e16StatusLabel = computed(() => e16Kpi.value.label)

</script>

<style scoped>
.dpv-root { display:flex; flex-direction:column; gap:14px; }

/* ── FILTROS ── */
.filtros-bar {
  display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  background:#fff; border:1px solid #E5E7EB;
  border-radius:10px; padding:10px 16px;
}
.fg  { display:flex; align-items:center; gap:6px; }
.fl  { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; white-space:nowrap; }
.bg  { display:flex; gap:4px; }
.fb  { padding:5px 12px; border:1.5px solid #E5E7EB; background:#F9FAFB; color:#6B7280; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; transition:all .15s; font-family:inherit; display:flex; align-items:center; gap:5px; }
.fb:hover   { border-color:#22C55E; color:#22C55E; }
.fb.active  { background:#22C55E; border-color:#22C55E; color:#fff; }
.fd  { padding:5px 8px; border:1.5px solid #E5E7EB; border-radius:6px; font-size:12px; color:#374151; background:#F9FAFB; font-family:inherit; }
.fd:focus { outline:none; border-color:#22C55E; }
.fr  { padding:5px 12px; border:1.5px solid #fee2e2; background:#fee2e2; color:#dc2626; border-radius:6px; font-size:12px; cursor:pointer; font-family:inherit; transition:all .15s; white-space:nowrap; }
.fr:hover { background:#dc2626; color:#fff; }
.fi  { margin-left:auto; display:flex; align-items:baseline; gap:4px; flex-shrink:0; }
.fin { font-size:22px; font-weight:800; color:#22C55E; }
.fil { font-size:11px; color:#6B7280; }

.uf-dot   { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.uf-z32   { background:#074e7a; }
.uf-z34   { background:#248a7c; }
.fb-uf10.active { background:#074e7a !important; border-color:#074e7a !important; color:#fff !important; }
.fb-uf10.active .uf-z32 { background:rgba(255,255,255,0.6); }
.fb-uf16.active { background:#248a7c !important; border-color:#248a7c !important; color:#fff !important; }
.fb-uf16.active .uf-z34 { background:rgba(255,255,255,0.6); }

/* ── FILA SUPERIOR ── */
.top-row {
  display:grid;
  grid-template-columns: 240px 1fr;
  gap:14px;
  align-items:start;
}
.right-col {
  display:flex;
  flex-direction:column;
  gap:14px;
  min-width:0;
}

.kpi-panel  { padding:18px; display:flex; flex-direction:column; gap:10px; }
.kpi-blk    { background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; }
.kpi-pct-blk { background:#e0f4f1; border-color:#248a7c; }
.kl  { font-size:9px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.5px; margin-bottom:2px; }
.kn  { font-size:34px; font-weight:900; color:#084534; line-height:1; }
.kn-pct { color:#248a7c; }

.dona-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; }
.dona-lbl  { font-size:10px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; }
.dona-legs { display:flex; flex-direction:column; gap:6px; width:100%; }
.dona-leg  { display:flex; align-items:center; gap:7px; }
.dl-dot    { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.dl-t      { font-size:11px; font-weight:700; color:#111827; }
.dl-c      { font-size:10px; color:#6B7280; }

/* Calor por día */
.calor-panel  { padding:16px; display:flex; flex-direction:column; gap:10px; }
.calor-title  { font-size:12px; font-weight:800; color:#111827; text-transform:uppercase; letter-spacing:.4px; text-align:center; }
.calor-chart  { display:flex; gap:6px; align-items:flex-end; height:110px; }
.calor-eje-y  { display:flex; flex-direction:column; justify-content:space-between; height:100px; font-size:9px; color:#6B7280; padding-bottom:18px; min-width:16px; text-align:right; }
.calor-barras { display:flex; align-items:flex-end; gap:2px; flex:1; height:100px; }
.calor-col    { display:flex; flex-direction:column; align-items:center; justify-content:flex-end; flex:1; gap:1px; min-width:0; }
.calor-num    { font-size:8px; font-weight:700; color:#111827; min-height:11px; line-height:1; }
.calor-num.invisible { opacity:0; }
.calor-barra-wrap { display:flex; align-items:flex-end; height:80px; width:100%; }
.calor-barra  { width:100%; border-radius:2px 2px 0 0; min-height:2px; transition:height .3s; }
.calor-hora   { font-size:7px; color:#6B7280; margin-top:2px; font-weight:500; }
.calor-leyenda { display:flex; align-items:center; gap:5px; font-size:10px; color:#374151; justify-content:center; flex-wrap:wrap; }
.cl-dot { width:10px; height:10px; border-radius:2px; display:inline-block; flex-shrink:0; }
.cl-lbl { margin-right:4px; color:#6B7280; }

/* ── DPV MENSUAL POR KILOMETRAJE (estilo compacto tipo reporte) ── */
/* ── DPV MENSUAL — REDISEÑO MODERNO ── */
.mensual-card {
  padding:16px;
  display:flex; flex-direction:column; gap:4px;
}
.mensual-maintitle {
  font-size:12px; font-weight:800; color:#111827;
  text-align:center; text-transform:uppercase; letter-spacing:.4px;
  margin-bottom:8px;
}

.fleet-block { display:flex; flex-direction:column; gap:6px; padding:2px 0; }

.fleet-header { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.fleet-id { display:flex; align-items:center; gap:10px; }
.fleet-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.fleet-name { font-size:13px; font-weight:800; color:#111827; letter-spacing:.2px; }
.fleet-sub { font-size:10px; color:#9CA3AF; font-weight:600; }

.fleet-kpi { display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }
.fk-value { font-size:19px; font-weight:900; color:#084534; line-height:1; }
.fk-unit  { font-size:13px; font-weight:700; color:#9CA3AF; }
.fk-delta { font-size:11px; font-weight:700; }
.fk-up    { color:#22C55E; }
.fk-down  { color:#EF4444; }
.fk-status {
  font-size:10px; font-weight:800; padding:3px 10px;
  border-radius:20px; text-transform:uppercase; letter-spacing:.3px;
}

.fleet-legend { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.lg-chip {
  font-size:10.5px; font-weight:700; padding:3px 10px;
  border-radius:20px; display:inline-flex; align-items:center; gap:4px;
}
.lg-chip-dash { background:#F9FAFB; border:1px dashed currentColor; }

.sub-divider { height:1px; background:#EEF1F0; margin:10px 0; }

.mensual-svg { width:100%; height:140px; display:block; }
.grid-line  { stroke:#F3F5F4; stroke-width:1; }
.axis-txt   { font-size:9px; fill:#9CA3AF; }
.axis-title { font-size:9px; fill:#9CA3AF; font-weight:700; letter-spacing:.3px; }
.x-txt      { font-size:9px; fill:#9CA3AF; font-weight:600; }
.pt-txt     { font-size:9.5px; font-weight:800; fill:#111827; }
.main-line  { fill:none; stroke-width:2.5; stroke-linecap:round; stroke-linejoin:round; }
.ref-line   { fill:none; stroke-width:1.3; stroke-dasharray:4 4; opacity:.7; }
.ref-green  { stroke:#22C55E; }
.ref-red    { stroke:#EF4444; }

/* ── GRID TABLAS ── */
.tablas-grid {
  display:grid;
  grid-template-columns: repeat(4, 1fr);
  gap:12px;
  align-items:start;
  min-width:0;
}

.tcol-stack  { display:flex; flex-direction:column; gap:0; min-width:0; }
.tcol-single { display:flex; flex-direction:column; min-width:0; }

.tblk {
  background:#fff;
  border:1px solid #E5E7EB;
  border-radius:10px;
  overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
  transition:box-shadow .15s;
  display:flex;
  flex-direction:column;
}
.tblk:hover   { box-shadow:0 4px 12px rgba(15,81,50,0.10); }
.tblk-flex    { flex:1; }

.thdr {
  display:flex; align-items:center; justify-content:space-between;
  height:36px; padding:0 10px;
  background:#0F5132; flex-shrink:0;
}
.tt { font-size:10px; font-weight:700; color:#fff; letter-spacing:.5px; text-transform:uppercase; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tb { font-size:10px; font-weight:700; color:#0F5132; background:rgba(255,255,255,0.92); padding:2px 8px; border-radius:10px; flex-shrink:0; margin-left:6px; min-width:22px; text-align:center; }

.tscr      { overflow-y:auto; }
.tscr-flex { overflow-y:auto; max-height:440px; }

.tscr::-webkit-scrollbar,
.tscr-flex::-webkit-scrollbar { width:4px; }
.tscr::-webkit-scrollbar-track,
.tscr-flex::-webkit-scrollbar-track { background:#F3F4F6; }
.tscr::-webkit-scrollbar-thumb,
.tscr-flex::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:2px; }
.tscr::-webkit-scrollbar-thumb:hover,
.tscr-flex::-webkit-scrollbar-thumb:hover { background:#248a7c; }

.t-empty { padding:18px; text-align:center; font-size:12px; color:#9CA3AF; }

.t  { width:100%; border-collapse:collapse; }

.th {
  height:30px; padding:6px 10px;
  font-size:10px; font-weight:700; color:#0F5132;
  background:#EDF7F1; border-bottom:1.5px solid #C8E6D0;
  text-transform:uppercase; letter-spacing:.3px;
  position:sticky; top:0; z-index:1;
  white-space:nowrap;
}
.th-l { text-align:left; }
.th-r { text-align:right; }
.th-c { text-align:center; }

.tr  { transition:background .12s; }
.tr:hover { background:#F0FBF4 !important; }
.tr.alt   { background:#F9FAFB; }

.td {
  padding:6px 10px;
  font-size:12px; color:#374151;
  border-bottom:1px solid #F3F4F6;
  vertical-align:middle;
  white-space:normal;
  word-break:break-word;
  line-height:1.35;
}
.td-r    { text-align:right; }
.td-c    { text-align:center; }
.td-bold { font-weight:700; color:#111827; white-space:nowrap; }
.td-muted { font-size:11px; color:#6B7280; }
.td-mono  { font-family:'SF Mono','Fira Code',monospace; font-size:11px; white-space:nowrap; }
.td-dia   { font-size:11px; color:#6B7280; white-space:nowrap; }
.td-hora  { font-size:11px; font-weight:600; color:#248a7c; white-space:nowrap; }

.cdot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:6px; vertical-align:middle; flex-shrink:0; }

.brow { display:flex; align-items:center; gap:6px; justify-content:flex-end; min-width:80px; }
.bbar { height:6px; border-radius:3px; background:#22C55E; min-width:3px; flex:1; max-width:60px; transition:width .15s; }
.bbar-t { background:#248a7c; }
.bnum { font-size:12px; font-weight:700; color:#0F5132; min-width:20px; text-align:right; white-space:nowrap; }

.mvl { padding:4px 8px; display:flex; flex-direction:column; gap:2px; }
.mi  { display:flex; align-items:center; gap:7px; padding:5px 4px; border-radius:5px; min-height:28px; transition:background .12s; }
.mi:hover { background:#F0FBF4; }
.mia { background:#F9FAFB; }
.mia:hover { background:#F0FBF4; }
.mlbl { font-size:11px; font-weight:600; color:#111827; width:84px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mtrk { flex:1; height:8px; background:#E5E7EB; border-radius:4px; overflow:hidden; }
.mfil { height:100%; background:#22C55E; border-radius:4px; transition:width 400ms ease; }
.mnum { font-size:11px; font-weight:700; color:#0F5132; min-width:18px; text-align:right; flex-shrink:0; }

/* ── RESPONSIVE ── */
@media(max-width:1400px) {
  .tablas-grid { grid-template-columns: repeat(4, 1fr); }
}
@media(max-width:1300px) {
  .top-row { grid-template-columns: 1fr; }
}
@media(max-width:1100px) {
  .tablas-grid { grid-template-columns: 1fr 1fr 1fr; }
}
@media(max-width:800px) {
  .tablas-grid { grid-template-columns: 1fr 1fr; }
  .top-row     { grid-template-columns: 1fr; }
}
@media(max-width:560px) {
  .tablas-grid { grid-template-columns: 1fr; }

  .filtros-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    padding: 16px;
  }
  .fg {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 7px;
    width: 100%;
  }
  .fg .bg { width: 100%; }
  .fb { flex: 1; justify-content: center; }
  .fd { width: 100%; }

  .fr {
    width: 100%;
    justify-content: center;
    margin: 0;
  }
  .fi {
    width: 100%;
    justify-content: space-between;
    margin: 0;
    padding-top: 12px;
    border-top: 1px solid var(--border);
  }
}
</style>
