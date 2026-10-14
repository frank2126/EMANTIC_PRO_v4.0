<template>
  <div class="sk-root" aria-busy="true" aria-label="Cargando datos del dashboard">
    <div class="sk-row">
      <span v-for="n in 5" :key="n" class="sk sk-pill" />
    </div>
    <div class="sk-top">
      <div class="sk sk-kpi" />
      <div class="sk sk-chart" />
    </div>
    <div class="sk-grid">
      <div v-for="n in 4" :key="n" class="sk sk-table" />
    </div>
  </div>
</template>

<style scoped>
.sk-root { display: flex; flex-direction: column; gap: 14px; }

.sk {
  border-radius: 10px;
  background: linear-gradient(90deg, #eef1f0 25%, #f8faf9 37%, #eef1f0 63%);
  background-size: 400% 100%;
  animation: shimmer 1.3s ease infinite;
}
@keyframes shimmer {
  0%   { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

.sk-row   { display: flex; gap: 10px; flex-wrap: wrap; }
.sk-pill  { height: 34px; width: 110px; }
.sk-top   { display: grid; grid-template-columns: 240px 1fr; gap: 14px; }
.sk-kpi   { height: 300px; }
.sk-chart { height: 300px; }
.sk-grid  { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.sk-table { height: 320px; }

@media (max-width: 800px) {
  .sk-top, .sk-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .sk { animation: none; }
}
</style>