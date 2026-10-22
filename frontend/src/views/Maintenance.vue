<template>
  <div class="page">

    <!-- ══ HERO — GESTIÓN DE MANTENIMIENTO ══ -->
    <div class="maint-hero" :style="{ backgroundImage: `url(${maintHeroImg})` }">
      <div class="maint-hero-overlay">
        <div class="maint-hero-content">
          <div class="maint-hero-eyebrow">EMASIVO · TALLER TÉCNICO</div>
          <h1 class="maint-hero-title">Gestión de Mantenimiento</h1>
          <p class="maint-hero-sub">Programación de móviles por kilometraje: hitos vencidos, pendientes de programar y seguimiento de intervenciones.</p>

          <div v-if="heroStats.length" class="maint-hero-stats">
            <div v-for="s in heroStats" :key="s.label" class="mth-stat">
              <div class="mth-stat-value">{{ s.value }}</div>
              <div class="mth-stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-header page-header--slim">
      <div class="header-actions">
        <KmUploadButtons @done="onKmDone" />
      </div>
    </div>

    <div class="tabs">
      <div class="tab active">Programación de Móviles</div>
    </div>

    <!-- La programación avisa con "resumen" cada vez que se carga o cambia (programar, intervenir, cargar Excel…) -->
    <ProgramacionMoviles :version="kmVersion" @resumen="r => resumen = r" />
  </div>
</template>

<script setup>
import maintHeroImg from '../assets/mantenimiento.png'
import { ref, computed } from 'vue'
import KmUploadButtons from '../components/KmUploadButtons.vue'
import ProgramacionMoviles from '../components/ProgramacionMoviles.vue'

const kmVersion = ref(0)
const onKmDone = () => { kmVersion.value++ }      // al cargar un Excel de kilometraje se recarga la programación
const resumen = ref(null)

const fmt = n => Number(n ?? 0).toLocaleString('es-CO')

// Los 3 datos que más importan para el taller, tomados de la programación de móviles:
//   Vencidos → ya pasaron su hito de mantenimiento · Faltan → vencidos/próximos sin fecha · Intervenidos → avance del mes
const heroStats = computed(() => {
  const r = resumen.value
  if (!r || r.moviles == null) return []
  return [
    { value: fmt(r.vencidos),     label: 'Vencidos' },
    { value: fmt(r.faltan),       label: 'Faltan por programar' },
    { value: fmt(r.intervenidos), label: 'Intervenidos (mes)' },
  ]
})
</script>

<style scoped>
/* ══ HERO — GESTIÓN DE MANTENIMIENTO ══ */
.maint-hero {
  position: relative;
  height: 320px;
  margin: -32px -32px 32px;
  background-size: cover;
  background-position: center 40%;
  border-radius: 0 0 var(--radius) var(--radius);
  overflow: hidden;
}
@media(min-width: 900px)  { .maint-hero { height: 440px; } }
@media(min-width: 1300px) { .maint-hero { height: 500px; } }

.maint-hero-overlay {
  position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(6,46,35,0.88) 0%, rgba(6,46,35,0.6) 40%, rgba(6,46,35,0.1) 75%),
    linear-gradient(180deg, rgba(8,69,52,0.1) 0%, rgba(8,69,52,0.4) 45%, rgba(6,46,35,0.9) 100%);
  display: flex; align-items: flex-end;
  padding: 32px 40px;
}
.maint-hero-content { max-width: 720px; }
.maint-hero-eyebrow {
  font-size: 11px; font-weight: 800; letter-spacing: 2px;
  color: var(--accent); text-transform: uppercase; margin-bottom: 8px;
}
.maint-hero-title {
  font-size: clamp(24px, 3.4vw, 34px); font-weight: 900; color: #fff;
  line-height: 1.15; margin-bottom: 8px;
}
.maint-hero-sub {
  font-size: 14px; color: rgba(255,255,255,0.75); line-height: 1.5;
  max-width: 52ch; margin-bottom: 22px;
}
.maint-hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.mth-stat-value { font-size: 26px; font-weight: 900; color: #fff; line-height: 1; }
.mth-stat-label { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

.page-header--slim { justify-content: flex-end; margin-top: -8px; }
.header-actions { display:flex; gap:10px; }

.tabs { display:flex; border-bottom:2px solid var(--border); margin-bottom:20px; }
.tab  { padding:12px 20px; border-bottom:3px solid transparent; margin-bottom:-2px; font-size:14px; font-weight:500; color:var(--text-muted); }
.tab.active { color:var(--primary); border-bottom-color:var(--primary); font-weight:700; }

@media(max-width:768px) {
  .maint-hero { height: 300px; margin: -16px -16px 24px; }
  .maint-hero-overlay { padding: 20px; }
  .maint-hero-stats { gap: 20px; }
}
</style>