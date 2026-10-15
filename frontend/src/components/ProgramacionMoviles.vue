<template>
  <div>
    <div v-if="!d.moviles.length" class="card">
      <div class="empty-state"><span class="empty-icon">📊</span><p>Carga el Excel de kilometraje para generar la programación de móviles</p></div>
    </div>

    <template v-else>
      <!-- Tarjetas interactivas: un clic filtra la tabla; otro clic quita el filtro -->
      <div class="pg-kpis">
        <button v-for="k in kpis" :key="k.key" type="button" class="pg-kpi" :class="[k.tone, { active: vista === k.key }]" :title="k.tip" @click="setVista(k.key)">
          <b>{{ k.v ?? 0 }}</b><span>{{ k.l }}</span>
        </button>
      </div>

      <div class="card pg-card">
        <div class="pg-top">
          <div class="pg-head">
            <h3 class="pg-title">{{ titulo }} · corte {{ d.fecha_corte }}</h3>
            <span v-if="vista !== 'todos'" class="pg-tag">{{ kpiActivo?.l }}<button type="button" title="Quitar filtro" @click="setVista('todos')">✕</button></span>
          </div>
          <div class="pg-row">
            <select v-model="fg" class="input"><option value="">Todos los grupos</option><option>VW</option><option>Scania</option></select>
            <select v-if="vista !== 'intervenidos'" v-model="fe" class="input"><option value="">Todos los estados</option><option>Vencido</option><option>Próximo</option><option>Al día</option></select>
            <input v-model="q" class="input" placeholder="Buscar móvil" />
          </div>
          <div v-if="isAdmin() && vista !== 'intervenidos'" class="pg-row">
            <label>Horizonte (días) <input v-model.number="hz" type="number" min="1" class="input w60" @change="load" /></label>
            <label>Capacidad por día <input v-model.number="cap" type="number" min="1" class="input w60" /></label>
            <label>Desde <input v-model="desde" type="date" class="input" /></label>
            <button type="button" class="btn-primary" @click="auto">Autoprogramar faltantes</button>
          </div>
        </div>

        <!-- Vista: intervenciones registradas del mes (con motivo y OT) -->
        <div v-if="vista === 'intervenidos'" class="pg-scroll">
          <p v-if="!intervs.length" class="pg-muted pg-pad">Aún no hay intervenciones registradas este mes.</p>
          <table v-else class="pg-table">
            <thead><tr><th>Fecha</th><th>Móvil</th><th>Grupo</th><th>Hito</th><th>Odómetro</th><th>Motivo</th><th>N.º OT</th><th>Observaciones</th><th>Registró</th><th v-if="isAdmin()"></th></tr></thead>
            <tbody>
              <tr v-for="i in intervs" :key="i.id">
                <td>{{ i.fecha }}</td><td class="pg-unit">{{ i.movil }}</td><td>{{ i.grupo }}</td><td>{{ fmt(i.hito) }}</td><td>{{ fmt(i.km) }}</td>
                <td class="pg-wrap">{{ i.motivo }}</td><td><b>{{ i.ot || '—' }}</b></td><td class="pg-wrap">{{ i.observacion }}</td><td>{{ i.por }}</td>
                <td v-if="isAdmin()"><button type="button" class="btn-tbl" @click="deshacerLista(i)">↩ Deshacer</button></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Vista: móviles -->
        <div v-else class="pg-scroll">
          <table class="pg-table">
            <thead><tr>
              <th v-for="[k, t] in cols" :key="k" @click="orden(k)">{{ t }}<span v-if="sk === k"> {{ asc ? '▲' : '▼' }}</span></th>
              <th v-if="isAdmin()">Acción</th>
            </tr></thead>
            <transition-group name="row" tag="tbody">
              <tr v-for="m in filtered" :key="m.movil" :class="{ flash: m.movil === flash }">
                <td>{{ m.pos }}</td>
                <td class="pg-unit">{{ m.movil }}</td>
                <td>{{ m.grupo }}</td>
                <td>{{ fmt(m.km_mes) }}</td>
                <td>{{ fmt(m.km_dia) }}</td>
                <td>{{ fmt(m.odometro) }}</td>
                <td>{{ m.hito ? fmt(m.hito) : '—' }}</td>
                <td>{{ fmt(m.dias) }}</td>
                <td><span class="badge" :class="st(m.estado)">{{ m.estado }}</span></td>
                <td><input type="date" class="input" :value="m.programado" :disabled="!isAdmin() || !m.hito" @change="programar(m, $event.target.value)" /></td>
                <td :title="m.ultima_motivo">{{ m.ultima }}<small v-if="m.ultima_ot" class="pg-ot"> · OT {{ m.ultima_ot }}</small></td>
                <td class="pg-warn">{{ m.alertas }}</td>
                <td v-if="isAdmin()"><button type="button" class="btn-tbl pg-ok" :disabled="!m.hito" @click="abrir(m)">✔ Intervenido</button></td>
              </tr>
            </transition-group>
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

    <!-- Formulario: registrar intervención -->
    <transition name="fade">
      <div v-if="modal" class="pg-bg" @click.self="cerrar">
        <form class="pg-modal" @submit.prevent="registrar">
          <h3>Registrar intervención · {{ modal.m.movil }}</h3>
          <p class="pg-sub">{{ modal.m.grupo }} · hito {{ fmt(modal.m.hito) }} km · odómetro {{ fmt(modal.m.odometro) }} km</p>
          <label class="pg-lbl">Fecha de intervención<input v-model="modal.fecha" type="date" class="input" required :max="hoy()" /></label>
          <label class="pg-lbl">Motivo de la intervención *<input ref="motivoEl" v-model="modal.motivo" class="input" list="pg-motivos" maxlength="300" placeholder="¿Por qué se intervino?" required /></label>
          <datalist id="pg-motivos"><option v-for="x in motivos" :key="x" :value="x" /></datalist>
          <label class="pg-lbl">N.º de orden de trabajo<input v-model="modal.ot" class="input" maxlength="50" placeholder="Ej: OT-12345" /></label>
          <label class="pg-lbl">Observaciones (opcional)<textarea v-model="modal.obs" class="input" rows="2" maxlength="300"></textarea></label>
          <p v-if="modal.err" class="pg-err">{{ modal.err }}</p>
          <div class="pg-actions">
            <button type="button" class="btn-secondary" @click="cerrar">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="modal.saving">{{ modal.saving ? 'Guardando…' : 'Registrar intervención' }}</button>
          </div>
        </form>
      </div>
    </transition>

    <transition name="toast">
      <div v-if="toast" class="pg-toast">{{ toast.msg }}<button v-if="toast.undo" type="button" @click="deshacer(toast.undo)">Deshacer</button></div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'

const props = defineProps({ version: { type: Number, default: 0 } })   // sube cuando se carga un Excel → recarga
const { isAdmin } = useAuth()
const hoy = () => { const t = new Date(); return new Date(t.getTime() - t.getTimezoneOffset() * 60000).toISOString().slice(0, 10) }
const fmt = n => (n == null || n === '') ? '' : Number(n).toLocaleString('es-CO', { maximumFractionDigits: 1 })
const d = ref({ moviles: [], resumen: {}, agenda: [], intervenciones: [], fecha_corte: '' })
const fg = ref(''), fe = ref(''), q = ref(''), hz = ref(15), cap = ref(10), desde = ref(hoy())
const sk = ref('dias'), asc = ref(true), vista = ref('todos')
const modal = ref(null), motivoEl = ref(null), flash = ref(''), toast = ref(null)
const motivos = ['Preventivo por hito', 'Correctivo', 'Falla reportada', 'Garantía', 'Inspección técnica', 'Alistamiento']
const cols = [['pos', '#'], ['movil', 'Móvil'], ['grupo', 'Grupo'], ['km_mes', 'Km mes'], ['km_dia', 'Km/día'], ['odometro', 'Odómetro'],
  ['hito', 'Hito pendiente'], ['dias', 'Días'], ['estado', 'Estado'], ['programado', 'Programado'], ['ultima', 'Últ. interv.'], ['alertas', 'Alertas']]

const load = async () => {
  try { d.value = (await axios.get('/api/kilometraje/programacion', { params: { horizonte: hz.value } })).data } catch {}
}
const orden = k => { if (sk.value === k) asc.value = !asc.value; else { sk.value = k; asc.value = true } }

// ── Tarjetas interactivas ──
const kpis = computed(() => { const r = d.value.resumen || {}
  return [
    { key: 'todos', l: 'Móviles', v: r.moviles, tip: 'Ver todos los móviles' },
    { key: 'ranking', l: 'Km flota (mes)', v: r.km_mes?.toLocaleString('es-CO'), tip: 'Ordenar de más a menos km recorridos' },
    { key: 'vencidos', l: 'Vencidos', v: r.vencidos, tone: 'rojo', tip: 'Móviles que ya cumplieron el hito' },
    { key: 'proximos', l: 'Próximos', v: r.proximos, tone: 'ambar', tip: 'Móviles que llegan al hito dentro del horizonte' },
    { key: 'programados', l: 'Programados', v: r.programados, tip: 'Móviles con fecha programada' },
    { key: 'intervenidos', l: 'Intervenidos (mes)', v: r.intervenidos, tone: 'verde', tip: 'Intervenciones registradas este mes, con motivo y OT' },
    { key: 'faltan', l: 'Faltan', v: r.faltan, tone: 'ambar', tip: 'Vencidos o próximos que aún no tienen fecha' }] })
const kpiActivo = computed(() => kpis.value.find(k => k.key === vista.value))
const TITULOS = { ranking: 'Ranking de km del mes', vencidos: 'Móviles vencidos', proximos: 'Próximos a hito', programados: 'Móviles programados', faltan: 'Faltan por programar', intervenidos: 'Intervenciones del mes' }
const titulo = computed(() => TITULOS[vista.value] || 'Programación de móviles')
const VISTAS = { vencidos: m => m.estado === 'Vencido', proximos: m => m.estado === 'Próximo', programados: m => !!m.programado,
  faltan: m => (m.estado === 'Vencido' || m.estado === 'Próximo') && !m.programado }
const setVista = k => {
  if (vista.value === k) k = 'todos'                                       // segundo clic = quitar filtro
  vista.value = k; fe.value = ''
  if (k === 'ranking') { sk.value = 'km_mes'; asc.value = false }
  else if (k === 'programados') { sk.value = 'programado'; asc.value = true }
  else if (['vencidos', 'proximos', 'faltan'].includes(k)) { sk.value = 'dias'; asc.value = true }
}
const filtered = computed(() => d.value.moviles
  .filter(m => (VISTAS[vista.value]?.(m) ?? true) && (!fg.value || m.grupo === fg.value) && (!fe.value || m.estado === fe.value) && (!q.value || m.movil.includes(q.value.toUpperCase())))
  .sort((a, b) => { const x = a[sk.value] ?? 1e12, y = b[sk.value] ?? 1e12; return (x > y ? 1 : x < y ? -1 : 0) * (asc.value ? 1 : -1) }))
const intervs = computed(() => (d.value.intervenciones || []).filter(i => (!fg.value || i.grupo === fg.value) && (!q.value || i.movil.includes(q.value.toUpperCase()))))
const st = e => ({ Vencido: 'badge-danger', 'Próximo': 'badge-warning', 'Al día': 'badge-success' }[e] || 'badge-gray')

// ── Avisos ──
let tt
const aviso = (msg, undo = null) => { toast.value = { msg, undo }; clearTimeout(tt); tt = setTimeout(() => (toast.value = null), undo ? 7000 : 3500) }

// ── Registrar intervención (formulario) ──
const abrir = m => {
  modal.value = { m, fecha: hoy(), motivo: `Preventivo por hito ${fmt(m.hito)} km`, ot: '', obs: '', err: '', saving: false }
  nextTick(() => motivoEl.value?.select())
}
const cerrar = () => { modal.value = null }
const registrar = async () => {
  const f = modal.value
  if (!f.motivo.trim()) { f.err = 'Indica por qué se intervino el móvil'; return }
  f.saving = true; f.err = ''
  try {
    const r = (await axios.post('/api/kilometraje/intervenir', { movil: f.m.movil, fecha: f.fecha, motivo: f.motivo.trim(), orden_trabajo: f.ot.trim(), observacion: f.obs.trim() })).data
    const mv = f.m.movil; cerrar(); await load()
    flash.value = mv; setTimeout(() => { if (flash.value === mv) flash.value = '' }, 2300)
    aviso(`✔ ${mv} registrado como intervenido` + (f.ot.trim() ? ` · OT ${f.ot.trim()}` : ''), r.id)
  } catch (e) { f.err = e.response?.data?.detail || 'No se pudo registrar la intervención'; f.saving = false }
}
const deshacer = async id => {
  toast.value = null
  try { await axios.delete(`/api/kilometraje/intervenciones/${id}`); await load(); aviso('Intervención deshecha: el móvil volvió a pendiente') }
  catch (e) { aviso(e.response?.data?.detail || 'No se pudo deshacer') }
}
const deshacerLista = i => confirm(`¿Deshacer la intervención de ${i.movil}? El móvil volverá a pendiente.`) && deshacer(i.id)

// ── Programar / autoprogramar ──
const act = async (ruta, body) => {
  try { const r = (await axios.post(`/api/kilometraje/${ruta}`, body)).data; await load(); return r }
  catch (e) { aviso(e.response?.data?.detail || 'No se pudo guardar'); await load() }
}
const programar = (m, f) => act('programar', { movil: m.movil, fecha: f })
const auto = async () => { const r = await act('autoprogramar', { capacidad: cap.value, desde: desde.value, horizonte: hz.value }); if (r) aviso(`✔ ${r.programados} móviles programados hasta el ${r.hasta}`) }

const onKey = e => { if (e.key === 'Escape') cerrar() }
watch(() => props.version, load)
onMounted(() => { load(); window.addEventListener('keydown', onKey) })
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.pg-kpis { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
.pg-kpi { font:inherit; text-align:left; cursor:pointer; background:#fff; border:1px solid var(--border); border-radius:12px; padding:12px 18px; min-width:120px; transition:transform .15s, box-shadow .15s, border-color .15s, background .15s; }
.pg-kpi:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.08); border-color:var(--primary); }
.pg-kpi.active { background:var(--primary-light); border-color:var(--primary); box-shadow:0 0 0 2px var(--primary) inset; }
.pg-kpi b { display:block; font-size:22px; font-weight:800; color:var(--primary); }
.pg-kpi.rojo b { color:var(--danger); } .pg-kpi.ambar b { color:var(--warning); }
.pg-kpi span { font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; }
.pg-card { margin-bottom:20px; overflow:hidden; }
.pg-top { padding:18px 24px 14px; border-bottom:1px solid var(--border); display:flex; flex-direction:column; gap:10px; }
.pg-head { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.pg-title { font-size:15px; font-weight:700; }
.pg-tag { display:inline-flex; align-items:center; gap:6px; background:var(--primary); color:#fff; font-size:12px; font-weight:600; border-radius:12px; padding:3px 6px 3px 12px; }
.pg-tag button { background:rgba(255,255,255,.25); color:#fff; border:0; border-radius:50%; width:18px; height:18px; cursor:pointer; line-height:1; }
.pg-row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; font-size:13px; }
.w60 { width:70px; }
.pg-scroll { overflow:auto; max-height:560px; }
.pg-table { width:100%; border-collapse:collapse; }
.pg-table th { position:sticky; top:0; z-index:1; padding:10px 12px; background:#f8fafc; font-size:11px; font-weight:700; color:var(--text-muted); text-align:left; text-transform:uppercase; letter-spacing:.5px; white-space:nowrap; cursor:pointer; border-bottom:1px solid var(--border); }
.pg-table td { padding:8px 12px; font-size:13px; border-bottom:1px solid var(--border); white-space:nowrap; }
.pg-table tr:hover td { background:#f8fafc; }
.pg-wrap { white-space:normal !important; min-width:160px; }
.pg-unit { font-weight:700; color:var(--primary); }
.pg-warn { font-size:11px; color:var(--warning); }
.pg-ot { color:var(--text-muted); }
.pg-pad { padding:20px 24px; }
.btn-tbl { padding:5px 12px; border-radius:6px; font-size:12px; border:1px solid var(--border); background:#fff; cursor:pointer; font-family:inherit; white-space:nowrap; }
.pg-ok { background:var(--primary); color:#fff; border-color:var(--primary); }
.btn-tbl:disabled { opacity:.5; cursor:not-allowed; }
.pg-agenda { display:flex; gap:12px; flex-wrap:wrap; padding:16px 24px; }
.pg-day { border:1px solid var(--border); border-radius:10px; padding:10px 14px; max-width:300px; font-size:13px; }
.pg-chip { display:inline-block; background:var(--primary-light); color:var(--primary); padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; margin:3px 4px 0 0; }
.pg-chip-n { background:var(--primary); color:#fff; }
.pg-muted { color:var(--text-muted); font-size:13px; }
/* transición de filas al registrar / cambiar de estado */
.row-enter-active, .row-leave-active { transition:opacity .3s, transform .3s; }
.row-enter-from, .row-leave-to { opacity:0; transform:translateX(18px); }
.flash td { animation:pgflash 2.3s ease-out; }
@keyframes pgflash { 0% { background:#bbf7d0; } 100% { background:transparent; } }
/* formulario */
.pg-bg { position:fixed; inset:0; background:rgba(0,0,0,.42); z-index:300; display:flex; align-items:center; justify-content:center; padding:24px; }
.pg-modal { background:#fff; border-radius:16px; padding:26px 28px; width:100%; max-width:460px; box-shadow:0 20px 60px rgba(0,0,0,.25); display:flex; flex-direction:column; gap:12px; }
.pg-modal h3 { font-size:17px; font-weight:700; }
.pg-sub { color:var(--text-muted); font-size:12px; margin-top:-6px; padding-bottom:10px; border-bottom:1px solid var(--border); }
.pg-lbl { display:flex; flex-direction:column; gap:5px; font-size:12px; font-weight:600; color:var(--text-muted); }
.pg-err { color:var(--danger); font-size:13px; }
.pg-actions { display:flex; gap:10px; justify-content:flex-end; margin-top:4px; }
.pg-toast { position:fixed; right:24px; bottom:24px; z-index:400; background:#0f4d3a; color:#fff; padding:12px 18px; border-radius:12px; font-size:13px; box-shadow:0 10px 30px rgba(0,0,0,.3); display:flex; gap:14px; align-items:center; }
.pg-toast button { background:transparent; color:#fff; border:1px solid rgba(255,255,255,.6); border-radius:6px; padding:3px 10px; cursor:pointer; font-family:inherit; }
.fade-enter-active, .fade-leave-active { transition:opacity .2s; } .fade-enter-from, .fade-leave-to { opacity:0; }
.toast-enter-active, .toast-leave-active { transition:all .3s; } .toast-enter-from, .toast-leave-to { opacity:0; transform:translateY(16px); }
</style>  