<template>
  <div class="page">

    <!-- ══ HERO — GESTIÓN DE MANTENIMIENTO ══ -->
    <div class="maint-hero" :style="{ backgroundImage: `url(${maintHeroImg})` }">
      <div class="maint-hero-overlay">
        <div class="maint-hero-content">
          <div class="maint-hero-eyebrow">EMASIVO · TALLER TÉCNICO</div>
          <h1 class="maint-hero-title">Gestión de Mantenimiento</h1>
          <p class="maint-hero-sub">Órdenes preventivas y correctivas, seguimiento de kilometraje y estado de la flota.</p>

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
        <button class="btn-secondary" @click="showForm = !showForm">+ Nueva Orden</button>
      </div>
    </div>

    <transition name="slide">
      <div v-if="showForm" class="card form-card">
        <h3 class="card-title">Nueva orden de mantenimiento</h3>
        <div class="form-grid">
          <div class="fgroup"><label class="label">Unidad *</label><input v-model="form.unidad" class="input" placeholder="Ej: Z32-001" /></div>
          <div class="fgroup"><label class="label">Tipo de servicio *</label><input v-model="form.tipo" class="input" placeholder="Ej: Cambio Aceite" /></div>
          <div class="fgroup"><label class="label">Km Actual</label><input v-model.number="form.km_actual" type="number" class="input" /></div>
          <div class="fgroup"><label class="label">Km Próximo Servicio</label><input v-model.number="form.km_servicio" type="number" class="input" /></div>
          <div class="fgroup"><label class="label">Fecha Programada</label><input v-model="form.fecha" type="date" class="input" /></div>
          <div class="fgroup">
            <label class="label">Estado</label>
            <select v-model="form.estado" class="input">
              <option>Programado</option><option>Próximo</option><option>Urgente</option><option>Completado</option>
            </select>
          </div>
        </div>
        <p v-if="formErr" class="err-msg">{{ formErr }}</p>
        <div class="form-actions">
          <button class="btn-secondary" @click="showForm=false">Cancelar</button>
          <button class="btn-primary" :disabled="saving" @click="create">{{ saving ? 'Guardando...' : 'Crear Orden' }}</button>
        </div>
      </div>
    </transition>

    <div class="tabs">
      <button class="tab" :class="{active:tab==='preventivo'}" @click="tab='preventivo'">Mantenimiento Preventivo</button>
      <button class="tab" :class="{active:tab==='correctivo'}" @click="tab='correctivo'">Mantenimiento Correctivo</button>
      <button class="tab" :class="{active:tab==='historial'}"  @click="tab='historial'">Historial Completo</button>
    </div>

    <div class="card table-card">
      <div class="table-top">
        <div>
          <h3 class="table-title">Calendario — {{ currentMonth }}</h3>
          <div class="unit-tags">
            <span v-for="u in uniqueUnits" :key="u" class="unit-tag">{{ u }}</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="empty-state"><span class="empty-icon">⏳</span><p>Cargando...</p></div>
      <div v-else-if="filtered.length===0" class="empty-state"><span class="empty-icon">📭</span><p>No hay registros</p></div>
      <div v-else class="table-wrap">
        <table class="mtable">
          <thead>
            <tr><th>Unidad</th><th>Tipo Servicio</th><th>Km Actual</th><th>Km Servicio</th><th>Fecha</th><th>Estado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id">
              <td class="td-unit">{{ item.unidad }}</td>
              <td>{{ item.tipo }}</td>
              <td>{{ item.km_actual?.toLocaleString() }} km</td>
              <td>
                {{ item.km_servicio?.toLocaleString() }} km
                <span class="km-diff" :class="kmClass(item)">({{ (item.km_servicio - item.km_actual).toLocaleString() }} km)</span>
              </td>
              <td>{{ item.fecha }}</td>
              <td><span class="badge" :class="stClass(item.estado)">{{ item.estado }}</span></td>
              <td>
                <div class="row-actions">
                  <button class="btn-tbl" @click="selected=item">Detalles</button>
                  <button v-if="item.estado!=='Completado'" class="btn-tbl btn-complete" @click="complete(item)">Completar</button>
                  <button v-if="isAdmin()" class="btn-tbl btn-del" @click="del(item.id)">🗑</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal detalle -->
    <div v-if="selected" class="modal-backdrop" @click="selected=null">
      <div class="modal" @click.stop>
        <h3 class="modal-title">Detalle — {{ selected.unidad }}</h3>
        <div class="modal-grid">
          <div><span class="ml">Tipo:</span>{{ selected.tipo }}</div>
          <div><span class="ml">Km Actual:</span>{{ selected.km_actual?.toLocaleString() }} km</div>
          <div><span class="ml">Km Servicio:</span>{{ selected.km_servicio?.toLocaleString() }} km</div>
          <div><span class="ml">Diferencia:</span>{{ (selected.km_servicio - selected.km_actual)?.toLocaleString() }} km</div>
          <div><span class="ml">Fecha:</span>{{ selected.fecha }}</div>
          <div><span class="ml">Estado:</span><span class="badge" :class="stClass(selected.estado)">{{ selected.estado }}</span></div>
          <div><span class="ml">Técnico:</span>{{ selected.tecnico }}</div>
        </div>
        <button class="btn-primary" style="width:100%;margin-top:20px" @click="selected=null">Cerrar</button>
      </div>
    </div>
  </div>
</template>

<script setup>

import maintHeroImg from '../assets/mantenimiento.png'
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'
const { isAdmin } = useAuth()

const items = ref([]), loading = ref(true), saving = ref(false)
const showForm = ref(false), formErr = ref(''), selected = ref(null)
const tab = ref('preventivo')
const form = ref({ unidad:'', tipo:'', km_actual:0, km_servicio:0, fecha:'', estado:'Programado' })

const currentMonth = new Date().toLocaleDateString('es-CO', { month:'long', year:'numeric' })
const uniqueUnits  = computed(() => [...new Set(items.value.map(i=>i.unidad))])
const filtered = computed(() => {
  if (tab.value==='preventivo') return items.value.filter(i=>['Programado','Próximo','Urgente'].includes(i.estado))
  if (tab.value==='correctivo') return items.value.filter(i=>i.estado==='Urgente')
  return items.value
})

// Datos reales para el hero: total de órdenes, urgentes y completadas
const heroStats = computed(() => {
  const urgentes    = items.value.filter(i => i.estado === 'Urgente').length
  const completadas = items.value.filter(i => i.estado === 'Completado').length
  return [
    { value: `${items.value.length}`, label: 'Órdenes totales' },
    { value: `${urgentes}`, label: 'Urgentes' },
    { value: `${completadas}`, label: 'Completadas' },
  ]
})

const stClass = s => ({'Programado':'badge-info','Próximo':'badge-warning','Urgente':'badge-danger','Completado':'badge-success'}[s]||'badge-gray')
const kmClass = item => { const d=item.km_servicio-item.km_actual; return d<2000?'km-red':d<5000?'km-orange':'km-gray' }

const load = async () => { loading.value=true; try { items.value=(await axios.get('/api/maintenance')).data } catch {} finally { loading.value=false } }

const create = async () => {
  formErr.value=''
  if (!form.value.unidad||!form.value.tipo) { formErr.value='Completa unidad y tipo de servicio'; return }
  saving.value=true
  try { await axios.post('/api/maintenance',form.value); showForm.value=false; form.value={unidad:'',tipo:'',km_actual:0,km_servicio:0,fecha:'',estado:'Programado'}; await load() }
  catch(e) { formErr.value=e.response?.data?.detail||'Error al crear' }
  finally { saving.value=false }
}

const complete = async item => {
  try { await axios.patch(`/api/maintenance/${item.id}?estado=Completado`); await load() } catch {}
}

const del = async id => {
  if (!confirm('¿Eliminar esta orden?')) return
  try { await axios.delete(`/api/maintenance/${id}`); await load() } catch {}
}
onMounted(load)
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
.form-card { padding:24px; margin-bottom:24px; }
.card-title { font-size:16px; font-weight:700; margin-bottom:16px; }
.form-grid  { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:16px; }
.fgroup     { display:flex; flex-direction:column; gap:6px; }
.err-msg    { color:var(--danger); font-size:13px; margin-bottom:10px; }
.form-actions { display:flex; gap:10px; justify-content:flex-end; }

.tabs { display:flex; border-bottom:2px solid var(--border); margin-bottom:20px; }
.tab  { padding:12px 20px; background:none; border:none; border-bottom:3px solid transparent; margin-bottom:-2px; cursor:pointer; font-size:14px; font-weight:500; color:var(--text-muted); transition:all 0.2s; font-family:inherit; }
.tab:hover  { color:var(--text); }
.tab.active { color:var(--primary); border-bottom-color:var(--primary); font-weight:700; }

.table-card { overflow:hidden; }
.table-top  { padding:20px 24px 16px; border-bottom:1px solid var(--border); }
.table-title{ font-size:15px; font-weight:700; margin-bottom:8px; }
.unit-tags  { display:flex; gap:8px; flex-wrap:wrap; }
.unit-tag   { background:var(--primary-light); color:var(--primary); padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.table-wrap { overflow-x:auto; }
.mtable     { width:100%; border-collapse:collapse; }
.mtable th  { padding:12px 16px; background:#f8fafc; font-size:11px; font-weight:700; color:var(--text-muted); text-align:left; border-bottom:1px solid var(--border); white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px; }
.mtable td  { padding:14px 16px; font-size:13px; border-bottom:1px solid var(--border); vertical-align:middle; }
.mtable tr:last-child td { border-bottom:none; }
.mtable tr:hover td { background:#f8fafc; }
.td-unit    { font-weight:700; color:var(--primary); }
.km-diff    { font-size:11px; margin-left:4px; }
.km-red     { color:var(--danger); }
.km-orange  { color:var(--warning); }
.km-gray    { color:var(--text-muted); }
.row-actions{ display:flex; gap:6px; flex-wrap:wrap; }
.btn-tbl    { padding:5px 12px; border-radius:6px; font-size:12px; font-weight:500; cursor:pointer; border:1px solid var(--border); background:#fff; color:var(--text); transition:all 0.15s; white-space:nowrap; font-family:inherit; }
.btn-tbl:hover    { background:var(--bg); }
.btn-complete     { background:var(--primary); color:#fff; border-color:var(--primary); }
.btn-complete:hover { background:var(--primary-dark); }
.btn-del          { color:var(--danger); border-color:#fecaca; }
.btn-del:hover    { background:#fee2e2; }

.modal-backdrop   { position:fixed; inset:0; background:rgba(0,0,0,0.4); z-index:300; display:flex; align-items:center; justify-content:center; padding:24px; }
.modal            { background:#fff; border-radius:16px; padding:32px; width:100%; max-width:480px; box-shadow:0 20px 60px rgba(0,0,0,0.2); }
.modal-title      { font-size:18px; font-weight:700; margin-bottom:20px; padding-bottom:12px; border-bottom:1px solid var(--border); }
.modal-grid       { display:grid; grid-template-columns:1fr 1fr; gap:14px; font-size:13px; }
.ml               { font-weight:700; color:var(--text-muted); font-size:11px; display:block; margin-bottom:2px; text-transform:uppercase; letter-spacing:0.5px; }

@media(max-width:768px) {
  .form-grid{grid-template-columns:1fr 1fr;}
  .modal-grid{grid-template-columns:1fr;}
  .maint-hero { height: 300px; margin: -16px -16px 24px; }
  .maint-hero-overlay { padding: 20px; }
  .maint-hero-stats { gap: 20px; }
}
</style>
