<template>
  <div class="page">

    <!-- ══ HERO — FOTO DE LA FLOTA ══ -->
    <div class="fleet-hero" :style="{ backgroundImage: `url(${fleetHeroImg})` }">
      <div class="fleet-hero-overlay">
        <div class="fleet-hero-content">
          <div class="fleet-hero-eyebrow">EMASIVO · FLOTA TÉCNICA</div>
          <h1 class="fleet-hero-title">Recursos para Talleres</h1>
          <p class="fleet-hero-sub">Especificaciones, fluidos y diagnóstico para el mantenimiento de nuestra flota.</p>

          <div v-if="heroStats.length" class="fleet-hero-stats">
            <div v-for="s in heroStats" :key="s.label" class="fh-stat">
              <div class="fh-stat-value">{{ s.value }}</div>
              <div class="fh-stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-header page-header--no-hero">
      <h1 class="page-title"><span>⚙️</span> Recursos para Talleres</h1>
    </div>

    <div class="section-label">🗄 Especificaciones Técnicas</div>
    <div class="specs-grid">
      <div v-for="s in resources.especificaciones" :key="s.unidad" class="card spec-card">
        <h3 class="spec-title">{{ s.unidad }} — Especificaciones</h3>
        <div class="spec-rows">
          <div class="spec-row"><span class="sk">Motor:</span><span class="sv">{{ s.motor }}</span></div>
          <div class="spec-row"><span class="sk">Potencia:</span><span class="sv">{{ s.potencia }}</span></div>
          <div class="spec-row"><span class="sk">Transmisión:</span><span class="sv">{{ s.transmision }}</span></div>
          <div class="spec-row"><span class="sk">Capacidad:</span><span class="sv">{{ s.capacidad }}</span></div>
          <div class="spec-row"><span class="sk">Peso:</span><span class="sv">{{ s.peso }}</span></div>
          <div class="spec-row"><span class="sk">Frenos:</span><span class="sv">{{ s.frenos }}</span></div>
        </div>
        <button class="btn-secondary btn-ficha">Descargar Ficha Técnica ⬇</button>
      </div>
    </div>

    <div class="section-label" style="margin-top:32px">🛢 Fluidos y Lubricantes Recomendados</div>
    <div class="card table-card">
      <div class="table-wrap">
        <table class="rtable">
          <thead>
            <tr><th>Sistema</th><th>Especificación</th><th>Capacidad UF-10</th><th>Capacidad UF-16</th><th>Intervalo</th></tr>
          </thead>
          <tbody>
            <tr v-for="f in resources.fluidos" :key="f.sistema">
              <td class="td-sys">{{ fluidIcon(f.sistema) }} {{ f.sistema }}</td>
              <td>{{ f.especificacion }}</td>
              <td class="tc">{{ f.cap_uf10 }}</td>
              <td class="tc">{{ f.cap_uf16 }}</td>
              <td class="ti">{{ f.intervalo }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="section-label" style="margin-top:32px">⚠️ Códigos de Falla Comunes (DTC)</div>
    <div class="card table-card">
      <div class="dtc-list">
        <div v-for="d in resources.dtc" :key="d.codigo" class="dtc-row">
          <span class="dtc-code">{{ d.codigo }}</span>
          <span class="dtc-desc">{{ d.descripcion }}</span>
          <span class="badge" :class="sevClass(d.severidad)">{{ d.severidad }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import fleetHeroImg from '../assets/flota-hero.png'

const resources = ref({ especificaciones:[], fluidos:[], dtc:[] })
const fluidIcon = s => ({'Aceite Motor':'🛢','Refrigerante':'💧','Líquido Frenos':'🔴','Aceite Transmisión':'⚙️'}[s]||'🔧')
const sevClass  = s => ({'Alta':'badge-danger','Media':'badge-warning','Baja':'badge-info'}[s]||'badge-gray')

// Extrae los primeros números de un texto como "45 pasajeros" o "380 HP @ 2100 rpm"
const firstNumber = (txt) => {
  const m = String(txt || '').match(/[\d.,]+/)
  return m ? parseInt(m[0].replace(/[.,]/g, '')) : 0
}

// Datos reales de la flota, calculados a partir de /api/resources (nada hardcodeado)
const heroStats = computed(() => {
  const specs = resources.value.especificaciones
  if (!specs.length) return []
  const capacidades = specs.map(s => firstNumber(s.capacidad))
  const potencias    = specs.map(s => firstNumber(s.potencia))
  return [
    { value: `${specs.length}`, label: 'Tipos de unidad' },
    { value: `${Math.max(...capacidades)}`, label: 'Pasajeros (máx.)' },
    { value: `${Math.max(...potencias)} HP`, label: 'Potencia (máx.)' },
  ]
})

onMounted(async () => {
  try { resources.value = (await axios.get('/api/resources')).data } catch {}
})
</script>

<style scoped>
/* ══ HERO — FOTO DE LA FLOTA ══ */
.fleet-hero {
  position: relative;
  height: 320px;
  margin: -32px -32px 32px;
  background-size: cover;
  background-position: center 40%;
  border-radius: 0 0 var(--radius) var(--radius);
  overflow: hidden;
}
@media(min-width: 900px) {
  .fleet-hero { height: 440px; }
}
@media(min-width: 1300px) {
  .fleet-hero { height: 500px; }
}
.fleet-hero-overlay {
  position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(6,46,35,0.88) 0%, rgba(6,46,35,0.6) 40%, rgba(6,46,35,0.1) 75%),
    linear-gradient(180deg, rgba(8,69,52,0.1) 0%, rgba(8,69,52,0.4) 45%, rgba(6,46,35,0.9) 100%);
  display: flex; align-items: flex-end;
  padding: 32px 40px;
}
.fleet-hero-content { max-width: 720px; }
.fleet-hero-eyebrow {
  font-size: 11px; font-weight: 800; letter-spacing: 2px;
  color: var(--accent); text-transform: uppercase; margin-bottom: 8px;
}
.fleet-hero-title {
  font-size: clamp(24px, 3.4vw, 34px); font-weight: 900; color: #fff;
  line-height: 1.15; margin-bottom: 8px;
}
.fleet-hero-sub {
  font-size: 14px; color: rgba(255,255,255,0.75); line-height: 1.5;
  max-width: 52ch; margin-bottom: 22px;
}
.fleet-hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.fh-stat-value { font-size: 26px; font-weight: 900; color: #fff; line-height: 1; }
.fh-stat-label { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

/* Oculta el título de página original (el hero ya lo muestra) */
.page-header--no-hero { display: none; }

.section-label { font-size:16px; font-weight:700; color:var(--text); margin-bottom:16px; }
.specs-grid    { display:grid; grid-template-columns:repeat(auto-fill,minmax(380px,1fr)); gap:20px; }
.spec-card     { padding:24px; }
.spec-title    { font-size:15px; font-weight:700; color:var(--primary); padding-bottom:14px; border-bottom:1px solid var(--border); margin-bottom:16px; }
.spec-rows     { display:flex; flex-direction:column; gap:12px; margin-bottom:20px; }
.spec-row      { display:flex; justify-content:space-between; align-items:baseline; gap:16px; }
.sk            { font-size:13px; font-weight:700; color:var(--text); min-width:110px; }
.sv            { font-size:13px; color:var(--text-muted); text-align:right; }
.btn-ficha     { width:100%; justify-content:center; font-size:13px; padding:8px 16px; }

.table-card    { overflow:hidden; }
.table-wrap    { overflow-x:auto; }
.rtable        { width:100%; border-collapse:collapse; }
.rtable th     { padding:13px 18px; background:#f8fafc; font-size:11px; font-weight:700; color:var(--text-muted); text-align:left; border-bottom:1px solid var(--border); white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px; }
.rtable td     { padding:14px 18px; font-size:13px; border-bottom:1px solid var(--border); }
.rtable tr:last-child td { border-bottom:none; }
.rtable tr:hover td { background:#f8fafc; }
.td-sys        { font-weight:600; }
.tc            { text-align:center; }
.ti            { color:var(--text-muted); font-size:12px; }

.dtc-list      { padding:8px 0; }
.dtc-row       { display:flex; align-items:center; gap:16px; padding:16px 20px; border-bottom:1px solid var(--border); }
.dtc-row:last-child { border-bottom:none; }
.dtc-code      { font-family:monospace; font-size:13px; font-weight:700; color:var(--primary); min-width:100px; }
.dtc-desc      { flex:1; font-size:13px; }

@media(max-width:768px){
  .specs-grid{grid-template-columns:1fr;}
  .spec-row{flex-direction:column;gap:2px;}
  .sv{text-align:left;}
  .fleet-hero { height: 260px; margin: -16px -16px 24px; }
  .fleet-hero-overlay { padding: 20px; }
  .fleet-hero-stats { gap: 20px; }
}
</style>
