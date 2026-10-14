<template>
  <div>
    <!-- ── Barra superior ── -->
    <div class="card cl-bar">
      <div class="cl-kpis">
        <div class="cl-kpi"><b>{{ d.resumen.moviles_a_programar ?? 0 }}</b><span>Móviles a programar</span></div>
        <div class="cl-kpi cl-warn"><b>{{ d.resumen.sin_programar ?? 0 }}</b><span>Sin programar</span></div>
        <div class="cl-kpi"><b>{{ d.resumen.programados ?? 0 }}</b><span>Programados</span></div>
        <div class="cl-kpi cl-ok"><b>{{ d.resumen.intervenidos_mes ?? 0 }}</b><span>Intervenidos (mes)</span></div>
      </div>
      <div class="cl-row">
        <input v-model="q" class="input input-sm" placeholder="Buscar móvil" />
        <label class="cl-chk">Mín. reportes <input v-model.number="minRep" type="number" min="1" class="input input-sm w60" @change="load" /></label>
        <label class="cl-chk">Mín. operadores distintos <input v-model.number="minOps" type="number" min="1" class="input input-sm w60" @change="load" /></label>
        <label class="cl-chk"><input v-model="obs" type="checkbox" @change="load" /> Ver también en observación</label>
        <label v-if="isAdmin()" class="btn-primary cl-up" :class="{ busy: subiendo }">
          ⬆ Cargar Excel check list
          <input type="file" hidden accept=".xlsx" @change="subir" />
        </label>
      </div>
      <p v-if="msg" class="cl-msg" :class="{ err }">{{ msg }}</p>
      <p class="cl-hint">Regla: el mismo ítem reportado ≥ {{ minRep }} veces por ≥ {{ minOps }} operadores distintos.
        <span v-if="d.ultimo_reporte"> Último reporte cargado: {{ d.ultimo_reporte }}</span></p>
    </div>

    <div v-if="!filtrados.length" class="card"><div class="empty-state"><span class="empty-icon">📭</span>
      <p>{{ d.moviles.length ? 'Sin resultados' : 'No hay móviles para programar. Carga el Excel del check list.' }}</p></div></div>

    <!-- ── Móviles ── -->
    <div v-for="m in filtrados" :key="m.movil" class="card cl-card" :class="{ obs: !m.cumple }">
      <div class="cl-head">
        <div class="cl-mv">
          <button class="cl-link" @click="verHistorial(m.movil)" title="Ver historial del móvil">{{ m.movil }}</button>
          <span class="badge" :class="m.cumple ? (m.programado ? 'badge-info' : 'badge-danger') : 'badge-gray'">
            {{ m.cumple ? (m.programado ? 'Programado' : 'Programar') : 'En observación' }}</span>
          <span class="cl-muted">{{ m.n_items }} ítem(s) · {{ m.total_reportes }} reporte(s)</span>
        </div>
        <div v-if="isAdmin()" class="cl-row">
          <input v-model="otMovil[m.movil]" class="input input-sm w140" placeholder="N° orden de trabajo (opcional)" />
          <button class="btn-primary btn-sm" @click="intervenir(m.movil, null, otMovil[m.movil])">✔ Todo intervenido</button>
        </div>
      </div>

      <table class="cl-table">
        <thead><tr><th>Ítem</th><th>Reportes</th><th>Operadores</th><th>Hist.</th><th v-if="isAdmin()">Seguimiento</th></tr></thead>
        <tbody>
          <tr v-for="i in m.items" :key="i.item">
            <td class="cl-item">{{ i.item }}<span v-if="!i.cumple" class="cl-muted"> · no cumple regla</span></td>
            <td><b>{{ i.reportes }}</b></td>
            <td>
              <span v-for="r in i.reportes_detalle" :key="r.fecha + r.codigo" class="cl-chip" :title="r.fecha">
                {{ r.operador || r.codigo }} · {{ r.fecha.slice(5, 10) }}</span>
            </td>
            <td class="cl-muted">{{ i.total_historico }} total<span v-if="i.veces_intervenido"> · {{ i.veces_intervenido }} interv.</span></td>
            <td v-if="isAdmin()">
              <div class="cl-row">
                <input type="date" class="input input-sm" v-model="ed(m.movil, i).fecha_programada" title="Fecha programada" />
                <input class="input input-sm w140" v-model="ed(m.movil, i).orden_trabajo" placeholder="N° OT (opcional)" />
                <input class="input input-sm w200" v-model="ed(m.movil, i).observacion" placeholder="Seguimiento / observación" />
                <button class="btn-tbl" @click="guardar(m.movil, i)">Guardar</button>
                <button class="btn-tbl cl-okbtn" @click="intervenir(m.movil, i.item, ed(m.movil, i).orden_trabajo)">✔ Intervenido</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Historial del móvil ── -->
    <div v-if="hist" class="cl-backdrop" @click="hist = null">
      <div class="cl-modal" @click.stop>
        <div class="cl-head"><h3>Historial · {{ hist.movil }}</h3><button class="btn-tbl" @click="hist = null">Cerrar</button></div>
        <p class="cl-muted">{{ hist.total_reportes }} reporte(s) de “Necesita atención” cargados.</p>

        <h4>Veces reportado por ítem</h4>
        <table class="cl-table">
          <thead><tr><th>Ítem</th><th>Total</th><th>Ciclo actual</th><th>Intervenido</th><th>Estado</th></tr></thead>
          <tbody>
            <tr v-for="p in hist.por_item" :key="p.item">
              <td>{{ p.item }}</td><td><b>{{ p.total }}</b></td><td>{{ p.ciclo_actual }}</td><td>{{ p.veces_intervenido }}</td>
              <td>{{ p.seguimiento.estado }}<span v-if="p.seguimiento.fecha_programada"> · {{ p.seguimiento.fecha_programada }}</span></td>
            </tr>
            <tr v-if="!hist.por_item.length"><td colspan="5" class="cl-muted">Sin ítems de mantenimiento reportados</td></tr>
          </tbody>
        </table>

        <h4>Intervenciones</h4>
        <table class="cl-table">
          <thead><tr><th>Fecha</th><th>Ítem</th><th>Orden de trabajo</th><th>Observación</th><th v-if="isAdmin()"></th></tr></thead>
          <tbody>
            <tr v-for="s in hist.intervenciones" :key="s.id">
              <td>{{ s.fecha }}</td><td>{{ s.item }}</td><td>{{ s.orden_trabajo || '—' }}</td><td>{{ s.observacion }}</td>
              <td v-if="isAdmin()"><button class="btn-tbl" @click="deshacer(s.id)">Deshacer</button></td>
            </tr>
            <tr v-if="!hist.intervenciones.length"><td colspan="5" class="cl-muted">Aún sin intervenciones registradas</td></tr>
          </tbody>
        </table>

        <h4>Reportes (más recientes primero)</h4>
        <div class="cl-scroll">
          <table class="cl-table">
            <thead><tr><th>Fecha</th><th>Operador</th><th>Ruta</th><th>Ítems de mantenimiento</th><th>Notas</th></tr></thead>
            <tbody>
              <tr v-for="(r, k) in hist.reportes" :key="k">
                <td class="nw">{{ r.fecha }}</td><td>{{ r.operador }}</td><td>{{ r.ruta }}</td>
                <td>{{ r.items.join(' · ') || '—' }}</td><td class="cl-muted">{{ r.notas }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'

const { isAdmin } = useAuth()
const d = ref({ moviles: [], resumen: {}, ultimo_reporte: '' })
const q = ref(''), minRep = ref(2), minOps = ref(2), obs = ref(false)
const msg = ref(''), err = ref(false), subiendo = ref(false)
const hist = ref(null)
const otMovil = reactive({})
const edits = reactive({})          // borrador por móvil+ítem

// Borrador editable inicializado con lo guardado en el servidor
const ed = (mv, i) => {
  const k = mv + '|' + i.item
  if (!edits[k]) edits[k] = { fecha_programada: i.seguimiento.fecha_programada, orden_trabajo: i.seguimiento.orden_trabajo, observacion: i.seguimiento.observacion }
  return edits[k]
}

const filtrados = computed(() => d.value.moviles.filter(m => !q.value || m.movil.includes(q.value.trim().toUpperCase())))

const load = async () => {
  try {
    d.value = (await axios.get('/api/checklist/programacion', { params: { min_reportes: minRep.value, min_operadores: minOps.value, incluir_observacion: obs.value } })).data
    Object.keys(edits).forEach(k => delete edits[k])
  } catch { /* se mantiene lo anterior */ }
}
const aviso = (t, e = false) => { msg.value = t; err.value = e }
const fallo = e => aviso(e.response?.data?.detail || 'No se pudo guardar', true)

const subir = async ev => {
  const f = ev.target.files[0]; ev.target.value = ''
  if (!f) return
  subiendo.value = true; aviso('Procesando…')
  const fd = new FormData(); fd.append('file', f)
  try {
    const r = (await axios.post('/api/checklist/upload', fd)).data
    aviso(`✔ ${r.reportes_nuevos} reportes nuevos · ${r.duplicados} ya cargados · ${r.items_relevantes} ítems de mantenimiento · ${r.moviles} móviles`)
    await load()
  } catch (e) { fallo(e) } finally { subiendo.value = false }
}

const guardar = async (movil, i) => {
  const e = ed(movil, i)
  try { await axios.post('/api/checklist/seguimiento', { movil, item: i.item, ...e }); aviso('✔ Seguimiento guardado'); await load() } catch (x) { fallo(x) }
}
const intervenir = async (movil, item, orden_trabajo) => {
  const t = item ? `“${item}” de ${movil}` : `todos los ítems pendientes de ${movil}`
  if (!confirm(`¿Marcar como intervenido ${t}?`)) return
  try { await axios.post('/api/checklist/intervenir', { movil, item, orden_trabajo: orden_trabajo || null }); aviso('✔ Marcado como intervenido'); await load() } catch (x) { fallo(x) }
}
const verHistorial = async movil => {
  try { hist.value = (await axios.get(`/api/checklist/historial/${encodeURIComponent(movil)}`)).data } catch { aviso('No se pudo cargar el historial', true) }
}
const deshacer = async id => {
  if (!confirm('¿Deshacer esta intervención? Los reportes volverán a contar.')) return
  try { await axios.post('/api/checklist/deshacer', { id }); await Promise.all([load(), verHistorial(hist.value.movil)]) } catch (x) { fallo(x) }
}
onMounted(load)
</script>

<style scoped>
.cl-bar { padding:16px 20px; margin-bottom:16px; display:flex; flex-direction:column; gap:12px; }
.cl-kpis { display:flex; gap:12px; flex-wrap:wrap; }
.cl-kpi { background:#fff; border:1px solid var(--border); border-radius:10px; padding:10px 16px; min-width:130px; }
.cl-kpi b { display:block; font-size:22px; font-weight:800; color:var(--primary); }
.cl-kpi span { font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.4px; }
.cl-warn b { color:var(--danger); } .cl-ok b { color:var(--success); }
.cl-row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.cl-chk { font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:6px; }
.cl-up { cursor:pointer; margin-left:auto; } .cl-up.busy { opacity:.6; pointer-events:none; }
.cl-msg { font-size:12px; color:var(--primary); } .cl-msg.err { color:var(--danger); }
.cl-hint { font-size:11px; color:var(--text-muted); }
.input-sm { padding:6px 9px; font-size:12px; } .w60 { width:64px; } .w140 { width:150px; } .w200 { width:200px; }
.cl-card { padding:14px 18px; margin-bottom:14px; } .cl-card.obs { opacity:.8; }
.cl-head { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px; }
.cl-mv { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.cl-link { background:none; border:none; font-size:17px; font-weight:800; color:var(--primary); cursor:pointer; text-decoration:underline; font-family:inherit; }
.cl-muted { font-size:11.5px; color:var(--text-muted); }
.cl-table { width:100%; border-collapse:collapse; font-size:12.5px; }
.cl-table th { text-align:left; font-size:10.5px; text-transform:uppercase; color:var(--text-muted); padding:6px 8px; background:#f8fafc; border-bottom:1px solid var(--border); }
.cl-table td { padding:7px 8px; border-bottom:1px solid var(--border); vertical-align:middle; }
.cl-item { font-weight:600; } .nw { white-space:nowrap; }
.cl-chip { display:inline-block; background:var(--primary-light); color:var(--primary); border-radius:10px; padding:2px 8px; font-size:11px; margin:2px 4px 2px 0; }
.btn-tbl { padding:5px 10px; border-radius:6px; font-size:12px; border:1px solid var(--border); background:#fff; cursor:pointer; font-family:inherit; white-space:nowrap; }
.cl-okbtn { background:var(--primary); color:#fff; border-color:var(--primary); }
.cl-backdrop { position:fixed; inset:0; background:rgba(0,0,0,.4); z-index:300; display:flex; align-items:center; justify-content:center; padding:20px; }
.cl-modal { background:#fff; border-radius:14px; padding:22px; width:100%; max-width:900px; max-height:88vh; overflow:auto; }
.cl-modal h4 { margin:16px 0 6px; font-size:13px; color:var(--primary); text-transform:uppercase; }
.cl-scroll { max-height:260px; overflow:auto; }
</style>