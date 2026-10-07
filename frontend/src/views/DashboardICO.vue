<template>
  <div class="ico-wrap">

    <!-- ── FILTROS ICO ── -->
    <div class="filtros-bar">
      <div class="filtro-grupo">
        <span class="filtro-lbl">Desde</span>
        <input type="date" v-model="store.icoFiltros.fecha_desde" class="flt-input" />
      </div>
      <div class="filtro-grupo">
        <span class="filtro-lbl">Hasta</span>
        <input type="date" v-model="store.icoFiltros.fecha_hasta" class="flt-input" />
      </div>
      <div class="filtro-grupo">
        <span class="filtro-lbl">Empresa</span>
        <select v-model="store.icoFiltros.empresa" class="flt-select">
          <option value="">Todas</option>
          <option v-for="e in store.icoOpciones.empresas" :key="e">{{ e }}</option>
        </select>
      </div>
      <div class="filtro-grupo">
        <span class="filtro-lbl">Tipo Novedad</span>
        <select v-model="store.icoFiltros.tipo_novedad" class="flt-select">
          <option value="">Todos</option>
          <option v-for="t in store.icoOpciones.tipos" :key="t">{{ t }}</option>
        </select>
      </div>
      <div class="filtro-grupo">
        <span class="filtro-lbl">Placa / Móvil</span>
        <input v-model="store.icoFiltros.busqueda" class="flt-input flt-search" placeholder="Buscar..." />
      </div>
      <button class="flt-reset" @click="store.resetFiltrosICO()">✕ Limpiar</button>
    </div>

    <!-- ── KPIs ICO ── -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-icon">📋</div>
        <div class="kpi-val">{{ store.icoKPIs.total }}</div>
        <div class="kpi-lbl">Total ICOs</div>
      </div>
      <div class="kpi-card kpi-puntos">
        <div class="kpi-icon">⭐</div>
        <div class="kpi-val">{{ store.icoKPIs.puntos }}</div>
        <div class="kpi-lbl">Puntos Total</div>
      </div>
      <div class="kpi-card kpi-tipos">
        <div class="kpi-icon">🔖</div>
        <div class="kpi-val">{{ store.icoKPIs.tipos }}</div>
        <div class="kpi-lbl">Tipos Novedad</div>
      </div>
      <div class="kpi-card kpi-placas">
        <div class="kpi-icon">🚌</div>
        <div class="kpi-val">{{ store.icoKPIs.placas }}</div>
        <div class="kpi-lbl">Placas Únicas</div>
      </div>
      <div class="kpi-card kpi-acept">
        <div class="kpi-icon">✅</div>
        <div class="kpi-val">{{ store.icoKPIs.aceptados }}</div>
        <div class="kpi-lbl">Aceptados</div>
      </div>
    </div>

    <!-- ── FILA SUPERIOR ── -->
    <div class="top-row">

      <!-- Dona tipología -->
      <div class="card panel-kpi">
        <div class="kpi-blk">
          <div class="kpi-l">No. EVENTOS</div>
          <div class="kpi-n">{{ store.icoKPIs.total }}</div>
        </div>
        <div class="kpi-blk kpi-blk--pts">
          <div class="kpi-l">PUNTOS</div>
          <div class="kpi-n kpi-pts">{{ store.icoKPIs.puntos }}</div>
        </div>
        <div class="dona-section">
          <div class="dona-title">TIPOLOGÍA</div>
          <svg viewBox="0 0 160 140" class="dona-svg">
            <circle cx="80" cy="74" r="52" fill="none" stroke="#E5E7EB" stroke-width="28"/>
            <circle v-for="(seg,i) in store.icoDona" :key="i"
              cx="80" cy="74" r="52" fill="none"
              :stroke="seg.color" stroke-width="28"
              :stroke-dasharray="`${seg.dash} ${seg.gap}`"
              :stroke-dashoffset="-seg.offset + CIRC*0.25"
              style="transform:rotate(-90deg);transform-origin:80px 74px"/>
            <text x="80" y="70" text-anchor="middle" font-size="17" font-weight="900" fill="#084534">{{ store.icoKPIs.total }}</text>
            <text x="80" y="84" text-anchor="middle" font-size="9" fill="#64748b">ICOs</text>
          </svg>
          <div class="dona-leyenda">
            <div v-for="(seg,i) in store.icoDona" :key="i" class="dona-item">
              <span class="dona-dot" :style="{background:seg.color}"></span>
              <div class="dona-info">
                <span class="dona-tipo">{{ seg.label }}</span>
                <span class="dona-cnt">{{ seg.total }} ({{ seg.pct }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mapa de calor ICO -->
      <div class="card panel-calor">
        <div class="calor-title">No. EVENTOS POR MAPA CALOR</div>
        <div class="calor-chart">
          <div class="calor-eje-y">
            <span v-for="v in [maxHeatICO, Math.round(maxHeatICO/2), 0]" :key="v">{{ v }}</span>
          </div>
          <div class="calor-barras">
            <div v-for="(val, h) in store.icoHeatmap" :key="h" class="calor-col">
              <span class="calor-num" :class="{invisible: val===0}">{{ val || '' }}</span>
              <div class="calor-barra-wrap">
                <div class="calor-barra"
                  :style="{ height: heatHeight(val, maxHeatICO, 80)+'px', background: heatColorICO(val, maxHeatICO) }"/>
              </div>
              <span class="calor-hora">{{ h }}</span>
            </div>
          </div>
        </div>
        <div class="calor-leyenda">
          <span class="cl-dot" style="background:#F0C419"></span><span class="cl-lbl">Alto</span>
          <span class="cl-dot" style="background:#60b566"></span><span class="cl-lbl">Medio</span>
          <span class="cl-dot" style="background:#31b079"></span><span class="cl-lbl">Bajo</span>
          <span class="cl-lbl" style="margin-left:8px">Recuento de ICO</span>
        </div>
      </div>
    </div>

    <!-- ── FILA INFERIOR ── -->
    <div class="bottom-row">

      <!-- Izquierda: tablas tipo novedad -->
      <div class="left-col">
        <div class="card tabla-card">
          <div class="tabla-hdr">TIPO NOVEDAD POR No. EVENTOS</div>
          <table class="mt">
            <thead><tr><th class="th-g">TIPO NOVEDAD</th><th class="th-g th-r">EVENTOS ICO</th></tr></thead>
            <tbody>
              <tr v-for="r in store.icoTipoNovedad" :key="r.tipo_novedad">
                <td class="td-codigo">{{ r.tipo_novedad }}</td>
                <td>
                  <div class="ico-bar-row">
                    <div class="ico-track">
                      <div class="ico-fill" :style="{width: barPct(r.total, store.icoTipoNovedad[0]?.total||1)+'%'}"/>
                    </div>
                    <span class="td-n">{{ r.total }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card tabla-card mt-10">
          <div class="tabla-hdr">TIPO DE INFRACCIÓN POR No. EVENTOS</div>
          <table class="mt">
            <thead><tr><th class="th-g">TIPO DE INFRACCIÓN</th><th class="th-g th-r">EVENTOS ICO</th></tr></thead>
            <tbody>
              <tr v-for="r in store.icoTipoInfraccion" :key="r.estado">
                <td>{{ r.estado }}</td>
                <td class="td-n">{{ r.total }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Top placas con barras -->
        <div class="card tabla-card mt-10">
          <div class="tabla-hdr">TOP UNIDADES CON MÁS ICOs</div>
          <div class="movil-list">
            <div v-for="r in store.icoTopPlacas.slice(0,10)" :key="r.placa" class="movil-row">
              <span class="movil-lbl">{{ r.placa }}</span>
              <div class="movil-track">
                <div class="movil-fill-blue" :style="{width: barPct(r.total, store.icoTopPlacas[0]?.total||1)+'%'}"/>
              </div>
              <span class="movil-num">{{ r.total }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Derecha: tabla detalle ICO -->
      <div class="right-col">
        <div class="card tabla-card tabla-full">
          <div class="tabla-hdr tabla-hdr--center">DESCRIPCIÓN DE EVENTOS</div>
          <div class="scroll-inner">
            <table class="mt detail-tbl">
              <thead>
                <tr>
                  <th>ID INFRACCIÓN</th>
                  <th>MÓVIL</th>
                  <th class="th-r">DÍAS GESTIÓN</th>
                  <th>CÓDIGO</th>
                  <th>TIPO INFRACCIÓN</th>
                  <th class="th-r">PUNTOS</th>
                  <th>DESCRIPCIÓN</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in store.icoFiltrado" :key="r.id||r.ico_id">
                  <td class="td-id">{{ r.ico_id }}</td>
                  <td class="td-movil">{{ r.movil }}</td>
                  <td class="td-n">{{ r.dias_gestion || '—' }}</td>
                  <td><span class="code-badge">{{ r.tipo_novedad }}</span></td>
                  <td>
                    <span class="badge" :class="badgeClass(r.estado)">{{ r.estado }}</span>
                  </td>
                  <td class="td-pts">{{ r.puntos }}</td>
                  <td class="td-desc">{{ trunc(r.descripcion, 55) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import { useDashboard } from './useDashboard.js'

const store = useDashboardStore()
const { heatColorICO, heatHeight, barPct, badgeClass, truncar } = useDashboard()

const CIRC       = 2 * Math.PI * 52
const maxHeatICO = computed(() => Math.max(1, ...store.icoHeatmap))
const trunc      = (t, n) => truncar(t, n)
</script>

<style scoped>
/* Filtros */
.filtros-bar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:12px 16px; margin-bottom:14px; }
.filtro-grupo { display:flex; align-items:center; gap:6px; }
.filtro-lbl  { font-size:11px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.4px; white-space:nowrap; }
.flt-select, .flt-input { padding:5px 9px; border:1.5px solid var(--border); border-radius:6px; font-size:12px; color:var(--text); background:var(--bg); font-family:inherit; cursor:pointer; }
.flt-search  { min-width:110px; }
.flt-reset   { padding:5px 12px; border:1.5px solid var(--danger-light); background:var(--danger-light); color:var(--danger); border-radius:6px; font-size:12px; cursor:pointer; font-family:inherit; margin-left:auto; }
.flt-reset:hover { background:var(--danger); color:#fff; border-color:var(--danger); }

/* KPIs */
.kpi-row  { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:14px; }
.kpi-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:14px 16px; text-align:center; position:relative; overflow:hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--accent); }
.kpi-puntos::before { background:var(--warning); }
.kpi-tipos::before  { background:var(--teal); }
.kpi-placas::before { background:var(--secondary); }
.kpi-acept::before  { background:#22C55E; }
.kpi-icon { font-size:18px; margin-bottom:4px; }
.kpi-val  { font-size:26px; font-weight:800; color:var(--text); line-height:1; }
.kpi-lbl  { font-size:11px; color:var(--text-muted); margin-top:3px; }

/* Fila superior */
.top-row { display:grid; grid-template-columns:230px 1fr; gap:14px; margin-bottom:14px; }

/* Panel KPI dona */
.panel-kpi { padding:18px; display:flex; flex-direction:column; gap:10px; }
.kpi-blk   { background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px 14px; }
.kpi-blk--pts { background:var(--lime-light); border-color:var(--lime); }
.kpi-l     { font-size:9px; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:2px; }
.kpi-n     { font-size:34px; font-weight:900; color:var(--primary); line-height:1; }
.kpi-pts   { color:#084534; }
.dona-section { display:flex; flex-direction:column; align-items:center; gap:6px; }
.dona-title   { font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; }
.dona-svg     { width:148px; height:118px; }
.dona-leyenda { display:flex; flex-direction:column; gap:6px; width:100%; }
.dona-item    { display:flex; align-items:center; gap:7px; }
.dona-dot     { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.dona-info    { display:flex; flex-direction:column; }
.dona-tipo    { font-size:11px; font-weight:700; color:var(--text); }
.dona-cnt     { font-size:10px; color:var(--text-muted); }

/* Mapa de calor */
.panel-calor  { padding:16px; display:flex; flex-direction:column; gap:10px; }
.calor-title  { font-size:12px; font-weight:800; color:var(--text); text-transform:uppercase; letter-spacing:.4px; text-align:center; }
.calor-chart  { display:flex; gap:4px; align-items:flex-end; }
.calor-eje-y  { display:flex; flex-direction:column; justify-content:space-between; height:100px; font-size:9px; color:var(--text-muted); padding-bottom:18px; }
.calor-barras { display:flex; align-items:flex-end; gap:1px; flex:1; height:100px; }
.calor-col    { display:flex; flex-direction:column; align-items:center; justify-content:flex-end; flex:1; gap:1px; min-width:0; }
.calor-num    { font-size:8px; font-weight:700; color:var(--text); min-height:10px; }
.calor-num.invisible { opacity:0; }
.calor-barra-wrap { display:flex; align-items:flex-end; height:80px; width:100%; }
.calor-barra  { width:100%; border-radius:2px 2px 0 0; min-height:2px; transition:height .3s; }
.calor-hora   { font-size:7px; color:var(--text-muted); margin-top:1px; }
.calor-leyenda { display:flex; align-items:center; gap:5px; font-size:10px; color:var(--text-muted); justify-content:center; }
.cl-dot { width:10px; height:10px; border-radius:2px; display:inline-block; flex-shrink:0; }
.cl-lbl { margin-right:4px; }

/* Fila inferior */
.bottom-row { display:grid; grid-template-columns:260px 1fr; gap:14px; }
.left-col   { display:flex; flex-direction:column; gap:0; }
.right-col  { display:flex; flex-direction:column; }
.mt-10      { margin-top:10px; }

/* Tablas */
.tabla-card  { overflow:hidden; display:flex; flex-direction:column; }
.tabla-full  { flex:1; }
.tabla-hdr   { background:var(--primary); color:#fff; font-size:10px; font-weight:700; padding:7px 10px; text-transform:uppercase; letter-spacing:.3px; flex-shrink:0; }
.tabla-hdr--center { text-align:center; }
.scroll-inner{ overflow-y:auto; overflow-x:auto; max-height:380px; flex:1; }
.mt          { width:100%; border-collapse:collapse; font-size:11px; }
.mt th       { background:var(--primary-light); color:var(--primary); padding:5px 8px; font-size:10px; font-weight:700; text-align:left; border-bottom:1.5px solid var(--border); position:sticky; top:0; white-space:nowrap; }
.th-g        { background:#d4f1e4 !important; color:#084534 !important; }
.th-r        { text-align:right; }
.mt td       { padding:4px 8px; border-bottom:1px solid var(--border); color:var(--text); }
.mt tr:hover td { background:var(--primary-light); }
.td-n        { text-align:right; font-weight:700; color:var(--primary); }
.td-codigo   { font-family:monospace; font-weight:700; font-size:12px; color:var(--primary); }
.td-id       { font-family:monospace; font-size:10px; }
.td-movil    { font-weight:700; font-size:10px; white-space:nowrap; }
.td-pts      { text-align:right; font-weight:800; color:var(--warning); }
.td-desc     { font-size:10px; max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.ico-wrap { overflow-x: hidden; }
.ico-bar-row  { display:flex; align-items:center; gap:5px; }
.ico-track    { flex:1; background:var(--bg); border-radius:3px; height:10px; overflow:hidden; min-width:40px; }
.ico-fill     { height:100%; background:#22C55E; border-radius:3px; transition:width .4s; }

.code-badge  { background:var(--primary-light); color:var(--primary); padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700; font-family:monospace; }

/* Movil barras top placas */
.movil-list  { padding:10px 10px 6px; display:flex; flex-direction:column; gap:6px; }
.movil-row   { display:flex; align-items:center; gap:6px; }
.movil-lbl   { font-size:10px; color:var(--text); width:64px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-weight:600; }
.movil-track { flex:1; background:var(--bg); border-radius:3px; height:11px; overflow:hidden; }
.movil-fill-blue { height:100%; background:#1E3A5F; border-radius:3px; transition:width .4s; }
.movil-num   { font-size:10px; font-weight:700; color:var(--text); width:18px; text-align:right; }

/* Detail tabla */
.detail-tbl th { font-size:9px; }
@media(max-width:1100px) {
  .top-row, .bottom-row { grid-template-columns:1fr; }
  .kpi-row { grid-template-columns:repeat(3,1fr); }
}
@media(max-width:700px) {
  .kpi-row { grid-template-columns:repeat(2,1fr); }
}
@media(max-width:560px) {
  .filtros-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    padding: 16px;
  }
  .filtro-grupo {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 7px;
    width: 100%;
  }
  .flt-select, .flt-input, .flt-search {
    width: 100%;
    min-width: 0;
  }
  .flt-reset {
    width: 100%;
    text-align: center;
    margin: 0;
  }
}
</style>
