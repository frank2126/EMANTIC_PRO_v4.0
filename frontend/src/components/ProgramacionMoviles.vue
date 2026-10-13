<template>
  <div>
    <div v-if="!d.moviles.length" class="card">
      <div class="empty-state"><span class="empty-icon">📊</span><p>Carga el Excel de kilometraje para generar la programación de móviles</p></div>
    </div>

    <template v-else>
      <div class="pg-kpis">
        <div v-for="k in kpis" :key="k.l" class="pg-kpi"><b>{{ k.v ?? 0 }}</b><span>{{ k.l }}</span></div>
      </div>

      <div class="card pg-card">
        <div class="pg-top">
          <h3 class="pg-title">Programación de móviles · corte {{ d.fecha_corte }}</h3>
          <div class="pg-row">
            <select v-model="fg" class="input"><option value="">Todos los grupos</option><option>VW</option><option>Scania</option></select>
            <select v-model="fe" class="input"><option value="">Todos los estados</option><option>Vencido</option><option>Próximo</option><option>Al día</option></select>
            <input v-model="q" class="input" placeholder="Buscar móvil" />
            <button class="btn-tbl" @click="sk = 'km_mes'; asc = false">🏆 Ranking de km</button>
          </div>
          <div v-if="isAdmin()" class="pg-row">
            <label>Horizonte (días) <input v-model.number="hz" type="number" min="1" class="input w60" @change="load" /></label>
            <label>Capacidad por día <input v-model.number="cap" type="number" min="1" class="input w60" /></label>
            <label>Desde <input v-model="desde" type="date" class="input" /></label>
            <button class="btn-primary" @click="auto">Autoprogramar faltantes</button>
          </div>
        </div>

        <div class="pg-scroll">
          <table class="pg-table">
            <thead><tr>
              <th v-for="[k, t] in cols" :key="k" @click="orden(k)">{{ t }}<span v-if="sk === k"> {{ asc ? '▲' : '▼' }}</span></th>
              <th v-if="isAdmin()">Acción</th>
            </tr></thead>
            <tbody>
              <tr v-for="m in filtered" :key="m.movil">
                <td>{{ m.pos }}</td>
                <td class="pg-unit">{{ m.movil }}</td>
                <td>{{ m.grupo }}</td>
                <td>{{ m.km_mes.toLocaleString('es-CO') }}</td>
                <td>{{ m.km_dia }}</td>
                <td>{{ m.odometro.toLocaleString('es-CO') }}</td>
                <td>{{ m.hito ? m.hito.toLocaleString('es-CO') : '—' }}</td>
                <td>{{ m.dias ?? '' }}</td>
                <td><span class="badge" :class="st(m.estado)">{{ m.estado }}</span></td>
                <td><input type="date" class="input" :value="m.programado" :disabled="!isAdmin() || !m.hito" @change="programar(m, $event.target.value)" /></td>
                <td>{{ m.ultima }}</td>
                <td class="pg-warn">{{ m.alertas }}</td>
                <td v-if="isAdmin()"><button class="btn-tbl pg-ok" :disabled="!m.hito" @click="intervenir(m)">✔ Intervenido</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card pg-card">
        <div class="pg-top"><h3 class="pg-title">Programados por día</h3></div>
        <div class="pg-agenda">
          <p v-if="!d.agenda.length" class="pg-muted">Aún no hay móviles programados.</p>
          <div v-for="a in d.agenda" :key="a.fecha" class="pg-day">
            <b>{{ a.fecha }}</b> <span class="pg-chip pg-chip-n">{{ a.moviles.length }}</span>
            <div><span v-for="m in a.moviles" :key="m" class="pg-chip">{{ m }}</span></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'

const props = defineProps({ version: { type: Number, default: 0 } })   // sube cuando se carga un Excel → recarga
const { isAdmin } = useAuth()
const d = ref({ moviles: [], resumen: {}, agenda: [], fecha_corte: '' })
const fg = ref(''), fe = ref(''), q = ref(''), hz = ref(15), cap = ref(10)
const desde = ref(new Date().toISOString().slice(0, 10)), sk = ref('dias'), asc = ref(true)
const cols = [['pos', '#'], ['movil', 'Móvil'], ['grupo', 'Grupo'], ['km_mes', 'Km mes'], ['km_dia', 'Km/día'], ['odometro', 'Odómetro'],
  ['hito', 'Hito pendiente'], ['dias', 'Días'], ['estado', 'Estado'], ['programado', 'Programado'], ['ultima', 'Últ. interv.'], ['alertas', 'Alertas']]

const load = async () => {
  try { d.value = (await axios.get('/api/kilometraje/programacion', { params: { horizonte: hz.value } })).data } catch {}
}
const orden = k => { if (sk.value === k) asc.value = !asc.value; else { sk.value = k; asc.value = true } }
const filtered = computed(() => d.value.moviles
  .filter(m => (!fg.value || m.grupo === fg.value) && (!fe.value || m.estado === fe.value) && (!q.value || m.movil.includes(q.value.toUpperCase())))
  .sort((a, b) => { const x = a[sk.value] ?? 1e12, y = b[sk.value] ?? 1e12; return (x > y ? 1 : x < y ? -1 : 0) * (asc.value ? 1 : -1) }))
const kpis = computed(() => { const r = d.value.resumen || {}
  return [['Móviles', r.moviles], ['Km flota (mes)', r.km_mes?.toLocaleString('es-CO')], ['Vencidos', r.vencidos], ['Próximos', r.proximos],
    ['Programados', r.programados], ['Intervenidos (mes)', r.intervenidos], ['Faltan', r.faltan]].map(([l, v]) => ({ l, v })) })
const st = e => ({ Vencido: 'badge-danger', 'Próximo': 'badge-warning', 'Al día': 'badge-success' }[e] || 'badge-gray')

const act = async (ruta, body) => {
  try { const r = (await axios.post(`/api/kilometraje/${ruta}`, body)).data; await load(); return r }
  catch (e) { alert(e.response?.data?.detail || 'No se pudo guardar'); await load() }
}
const programar = (m, f) => act('programar', { movil: m.movil, fecha: f })
const intervenir = m => confirm(`¿Registrar ${m.movil} como intervenido (hito ${m.hito.toLocaleString('es-CO')} km)?`) && act('intervenir', { movil: m.movil })
const auto = async () => { const r = await act('autoprogramar', { capacidad: cap.value, desde: desde.value, horizonte: hz.value }); if (r) alert(`Programados: ${r.programados} (hasta el ${r.hasta})`) }

watch(() => props.version, load)
onMounted(load)
</script>

<style scoped>
.pg-kpis { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
.pg-kpi { background:#fff; border:1px solid var(--border); border-radius:12px; padding:12px 18px; min-width:120px; }
.pg-kpi b { display:block; font-size:22px; font-weight:800; color:var(--primary); }
.pg-kpi span { font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; }
.pg-card { margin-bottom:20px; overflow:hidden; }
.pg-top { padding:18px 24px 14px; border-bottom:1px solid var(--border); display:flex; flex-direction:column; gap:10px; }
.pg-title { font-size:15px; font-weight:700; }
.pg-row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; font-size:13px; }
.w60 { width:70px; }
.pg-scroll { overflow:auto; max-height:560px; }
.pg-table { width:100%; border-collapse:collapse; }
.pg-table th { position:sticky; top:0; z-index:1; padding:10px 12px; background:#f8fafc; font-size:11px; font-weight:700; color:var(--text-muted); text-align:left; text-transform:uppercase; letter-spacing:.5px; white-space:nowrap; cursor:pointer; border-bottom:1px solid var(--border); }
.pg-table td { padding:8px 12px; font-size:13px; border-bottom:1px solid var(--border); white-space:nowrap; }
.pg-table tr:hover td { background:#f8fafc; }
.pg-unit { font-weight:700; color:var(--primary); }
.pg-warn { font-size:11px; color:var(--warning); }
.btn-tbl { padding:5px 12px; border-radius:6px; font-size:12px; border:1px solid var(--border); background:#fff; cursor:pointer; font-family:inherit; white-space:nowrap; }
.pg-ok { background:var(--primary); color:#fff; border-color:var(--primary); }
.btn-tbl:disabled { opacity:.5; cursor:not-allowed; }
.pg-agenda { display:flex; gap:12px; flex-wrap:wrap; padding:16px 24px; }
.pg-day { border:1px solid var(--border); border-radius:10px; padding:10px 14px; max-width:300px; font-size:13px; }
.pg-chip { display:inline-block; background:var(--primary-light); color:var(--primary); padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; margin:3px 4px 0 0; }
.pg-chip-n { background:var(--primary); color:#fff; }
.pg-muted { color:var(--text-muted); font-size:13px; }
</style>