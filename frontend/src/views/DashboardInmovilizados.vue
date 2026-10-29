<template>
  <div class="inm-root">

    <!-- ══ BARRA: vista · unidad · estado de la información ══ -->
    <div class="inm-bar">
      <div class="seg" role="tablist" aria-label="Vista de inmovilizados">
        <button role="tab" :aria-selected="vista === 'ahora'" :class="{ on: vista === 'ahora' }" @click="vista = 'ahora'">⏱ Ahora</button>
        <button role="tab" :aria-selected="vista === 'mes'" :class="{ on: vista === 'mes' }" @click="vista = 'mes'">📅 Mensual</button>
      </div>

      <div class="seg" role="group" aria-label="Unidad">
        <button :class="{ on: unidad === '' }" @click="unidad = ''">Todas</button>
        <button v-for="u in UNIDADES" :key="u.key" :class="{ on: unidad === u.key }" @click="unidad = u.key">{{ u.nombre }}</button>
      </div>

      <!-- Estado de la información: discreto, solo un punto de color y la hora del último corte -->
      <div class="frescura" aria-live="polite">
        <span v-for="f in frescuras" :key="f.key" class="fr-item" :title="f.titulo">
          <span class="fr-dot" :class="'fr-' + f.nivel" aria-hidden="true"></span>
          <span class="fr-uf">{{ f.nombre }}</span>
          <span class="fr-txt" :class="{ 'fr-aviso': f.nivel === 'vencido' }">{{ f.texto }}</span>
        </span>
      </div>
    </div>

    <p v-if="store.inmov.error" class="inm-error" role="alert">
      ⚠️ No se pudo actualizar: {{ store.inmov.error }}
      <span v-if="store.inmov.cargado">(se muestran los últimos datos recibidos)</span>
    </p>

    <div v-if="!store.inmov.cargado && !store.inmov.error" class="card empty-card">Cargando inmovilizados…</div>

    <div v-else-if="!store.inmov.items.length" class="card empty-card">
      <span class="empty-icon" aria-hidden="true">📭</span>
      <p>Aún no hay inmovilizados cargados.</p>
      <p class="empty-sub">Sube el Excel en <strong>Carga DPV → Inmovilizados</strong>.</p>
    </div>

    <!-- ══════════ VISTA AHORA ══════════ -->
    <template v-else-if="vista === 'ahora'">
      <div class="kpis">
        <div class="kpi kpi-bad">
          <div class="kpi-val">{{ ahoraV.kpis.inmovilizados }}</div>
          <div class="kpi-lbl">Inmovilizados ahora</div>
        </div>
        <div class="kpi kpi-ok">
          <div class="kpi-val">{{ ahoraV.kpis.habilitadosRecientes }}</div>
          <div class="kpi-lbl">Habilitados en 24 h</div>
        </div>
        <div class="kpi">
          <div class="kpi-val">{{ fmtHoras(ahoraV.kpis.mayorHoras) }}</div>
          <div class="kpi-lbl">Lleva más tiempo</div>
        </div>
        <div class="kpi" :class="{ 'kpi-warn': ahoraV.kpis.masDeUnDia > 0 }">
          <div class="kpi-val">{{ ahoraV.kpis.masDeUnDia }}</div>
          <div class="kpi-lbl">Con más de 24 h</div>
        </div>
      </div>

      <section class="card bloque">
        <h3 class="bloque-t">Móviles inmovilizados <span class="cnt">{{ ahoraV.abiertos.length }}</span></h3>
        <p v-if="!ahoraV.abiertos.length" class="vacio">Ningún móvil inmovilizado en este momento 🎉</p>
        <div v-else class="table-wrap">
          <table class="data-table inm-tabla">
            <caption class="sr-only">Móviles inmovilizados ahora, del que lleva más tiempo al que menos</caption>
            <thead><tr><th>Móvil</th><th>Placa</th><th>UF</th><th>Causa</th><th>Desde</th><th class="th-r">Lleva</th><th>Reportó</th></tr></thead>
            <tbody>
              <tr v-for="e in ahoraV.abiertos" :key="e.id">
                <td class="td-movil">{{ e.movil || '—' }}</td>
                <td>{{ e.placa }}</td>
                <td>{{ nombreUF(e.unidad) }}</td>
                <td class="td-causa" :title="e.descripcion">{{ e.causa || '—' }}</td>
                <td>{{ fmtFechaHora(e.fechaInm) }}</td>
                <td class="td-num"><span class="horas" :class="claseHoras(horasDe(e, ahora))">{{ fmtHoras(horasDe(e, ahora)) }}</span></td>
                <td class="td-sub">{{ e.creador || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="ahoraV.sinConfirmar.length" class="card bloque bloque-aviso">
        <h3 class="bloque-t">Sin confirmar <span class="cnt">{{ ahoraV.sinConfirmar.length }}</span></h3>
        <p class="nota">Estaban inmovilizados y ya no aparecen en el último archivo, pero tampoco traen fecha de habilitación. Revisa si ya fueron habilitados.</p>
        <div class="chips">
          <span v-for="e in ahoraV.sinConfirmar" :key="e.id" class="chip" :title="`${e.causa} · desde ${fmtFechaHora(e.fechaInm)}`">
            {{ e.movil || e.placa }}
          </span>
        </div>
      </section>

      <section class="card bloque">
        <h3 class="bloque-t">Habilitados en las últimas 24 h <span class="cnt">{{ ahoraV.recientes.length }}</span></h3>
        <p v-if="!ahoraV.recientes.length" class="vacio">Sin habilitaciones en las últimas 24 horas.</p>
        <div v-else class="table-wrap">
          <table class="data-table inm-tabla">
            <thead><tr><th>Móvil</th><th>Placa</th><th>UF</th><th>Causa</th><th>Habilitado</th><th class="th-r">Duró</th><th>Habilitó</th></tr></thead>
            <tbody>
              <tr v-for="e in ahoraV.recientes" :key="e.id">
                <td class="td-movil">{{ e.movil || '—' }}</td>
                <td>{{ e.placa }}</td>
                <td>{{ nombreUF(e.unidad) }}</td>
                <td class="td-causa">{{ e.causa || '—' }}</td>
                <td>{{ fmtFechaHora(e.fechaHab) }}</td>
                <td class="td-num">{{ fmtHoras(e.horas) }}</td>
                <td class="td-sub">{{ e.habilitador || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- ══════════ VISTA MENSUAL ══════════ -->
    <template v-else>
      <div class="mes-bar">
        <label class="mes-lbl" for="inm-mes">Mes</label>
        <select id="inm-mes" class="input input-mes" v-model="mes">
          <option v-for="m in meses" :key="m" :value="m">{{ tituloMes(m) }}</option>
        </select>
        <span class="nota">Incluye los móviles de meses anteriores que siguen sin habilitar.</span>
      </div>

      <div class="kpis">
        <div class="kpi">
          <div class="kpi-val">{{ mensualV.kpis.moviles }}</div>
          <div class="kpi-lbl">Móviles con novedad</div>
        </div>
        <div class="kpi kpi-ok">
          <div class="kpi-val">{{ mensualV.kpis.habilitados }}</div>
          <div class="kpi-lbl">Habilitados <span v-if="mensualV.kpis.pctHabilitados !== null">({{ mensualV.kpis.pctHabilitados }}%)</span></div>
        </div>
        <div class="kpi kpi-bad">
          <div class="kpi-val">{{ mensualV.kpis.pendientes + mensualV.kpis.sinConfirmar }}</div>
          <div class="kpi-lbl">Por intervenir</div>
        </div>
        <div class="kpi">
          <div class="kpi-val">{{ fmtHoras(mensualV.kpis.horasPromedio) }}</div>
          <div class="kpi-lbl">Tiempo promedio</div>
        </div>
        <div class="kpi" :class="{ 'kpi-warn': mensualV.kpis.reincidentes > 0 }">
          <div class="kpi-val">{{ mensualV.kpis.reincidentes }}</div>
          <div class="kpi-lbl">Reincidentes en el mes</div>
        </div>
      </div>

      <section v-if="mensualV.causas.length" class="card bloque">
        <h3 class="bloque-t">Causas del mes</h3>
        <div class="barras">
          <div v-for="c in mensualV.causas" :key="c.causa" class="barra-fila">
            <span class="barra-lbl" :title="c.causa">{{ c.causa }}</span>
            <div class="barra-pista"><div class="barra-rel" :style="{ width: (c.total / mensualV.causas[0].total) * 100 + '%' }"></div></div>
            <span class="barra-val">{{ c.total }}</span>
          </div>
        </div>
      </section>

      <section class="card bloque">
        <div class="tabla-cab">
          <h3 class="bloque-t">Móviles de {{ mensualV.titulo }} <span class="cnt">{{ movilesFiltrados.length }}</span></h3>
          <div class="tabla-filtros">
            <div class="seg seg-chico" role="group" aria-label="Estado">
              <button :class="{ on: filtroEstado === '' }" @click="filtroEstado = ''">Todos</button>
              <button :class="{ on: filtroEstado === 'pendiente' }" @click="filtroEstado = 'pendiente'">Por intervenir</button>
              <button :class="{ on: filtroEstado === 'habilitado' }" @click="filtroEstado = 'habilitado'">Habilitados</button>
            </div>
            <label class="sr-only" for="inm-buscar">Buscar</label>
            <input id="inm-buscar" class="input input-buscar" type="search" placeholder="Móvil, placa o causa" v-model="texto" />
          </div>
        </div>

        <p v-if="!movilesFiltrados.length" class="vacio">No hay móviles con ese filtro.</p>
        <div v-else class="table-wrap">
          <table class="data-table inm-tabla">
            <caption class="sr-only">Móviles del mes con su estado de habilitación</caption>
            <thead>
              <tr><th>Móvil</th><th>Placa</th><th>UF</th><th>Estado</th><th class="th-r">Veces</th><th>Última inmovilización</th><th>Habilitado</th><th>Causa</th><th class="th-r">Tiempo</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in movilesFiltrados" :key="m.clave">
                <td class="td-movil">{{ m.movil || '—' }}</td>
                <td>{{ m.placa }}</td>
                <td>{{ nombreUF(m.unidad) }}</td>
                <td>
                  <span class="badge" :class="BADGE[m.estado].clase">{{ BADGE[m.estado].texto }}</span>
                  <span v-if="m.arrastrado" class="arrastre" title="Inmovilizado en un mes anterior y sin habilitar">mes anterior</span>
                </td>
                <td class="td-num">{{ m.n }}</td>
                <td>{{ fmtFechaHora(m.ultimaInm) }}</td>
                <td>{{ m.ultimaHab ? fmtFechaHora(m.ultimaHab) : '—' }}</td>
                <td class="td-causa" :title="m.causas.join(' · ')">{{ m.causas[0] || '—' }}<span v-if="m.causas.length > 1" class="mas"> +{{ m.causas.length - 1 }}</span></td>
                <td class="td-num">{{ fmtHoras(m.horasTotal) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import {
  UNIDADES, fmtHoras, fmtFechaHora, tituloMes, frescura, horasDe, vistaAhora, vistaMensual,
  mesesDisponibles, filtrarMoviles, mesInicial,
} from './inmovUtils.js'

const store = useDashboardStore()

const vista = ref('ahora')
const unidad = ref('')
const mes = ref('')
const filtroEstado = ref('')
const texto = ref('')

// Reloj: refresca los «hace X min» y las horas acumuladas sin recargar; los datos se vuelven a pedir cada 5 min
const ahora = ref(Date.now())
let relojTimer = null
let datosTimer = null
onMounted(() => {
  if (!store.inmov.cargado) store.cargarInmovilizados()
  relojTimer = setInterval(() => { ahora.value = Date.now() }, 30000)
  datosTimer = setInterval(() => store.cargarInmovilizados(), 5 * 60000)
})
onUnmounted(() => { clearInterval(relojTimer); clearInterval(datosTimer) })

const nombreUF = k => (UNIDADES.find(u => u.key === k) || { nombre: k }).nombre

const meses = computed(() => mesesDisponibles(store.inmov.items))
watch(meses, (lista) => { if (!lista.includes(mes.value)) mes.value = mesInicial(lista) }, { immediate: true })

const ahoraV = computed(() => vistaAhora(store.inmov.items, { unidad: unidad.value, ahoraMs: ahora.value }))
const mensualV = computed(() => vistaMensual(store.inmov.items, mes.value, { unidad: unidad.value, ahoraMs: ahora.value }))
const movilesFiltrados = computed(() => filtrarMoviles(mensualV.value.moviles, { estado: filtroEstado.value, texto: texto.value }))

const frescuras = computed(() =>
  UNIDADES.filter(u => !unidad.value || u.key === unidad.value).map(u => {
    const corte = store.inmov.cortes[u.key]
    const f = frescura(corte && corte.ultimo, ahora.value)
    const titulo = corte && corte.ultimo
      ? `Última actualización: ${new Date(corte.ultimo.creado).toLocaleString('es-CO')} · ${corte.ultimo.tipo === 'sin_novedades' ? 'sin novedades' : 'archivo ' + (corte.ultimo.archivo || '')}`
      : 'Todavía no se ha cargado nada'
    return { key: u.key, nombre: u.nombre, nivel: f.nivel, texto: f.texto, titulo }
  }))

const BADGE = {
  inmovilizado:  { clase: 'badge-danger', texto: 'Por intervenir' },
  sin_confirmar: { clase: 'badge-aviso', texto: 'Sin confirmar' },
  habilitado:    { clase: 'badge-success', texto: 'Habilitado' },
}

// Color de las horas que lleva un móvil: rojo desde 24 h, ámbar desde 8 h
const claseHoras = h => (h === null ? '' : h >= 24 ? 'h-rojo' : h >= 8 ? 'h-ambar' : '')
</script>

<style scoped>
.inm-root { display: flex; flex-direction: column; gap: 14px; }

/* ── barra superior ── */
.inm-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.seg { display: inline-flex; background: var(--surface); border: 1.5px solid var(--border); border-radius: 9px; padding: 2px; gap: 2px; }
.seg button {
  border: none; background: transparent; padding: 6px 14px; border-radius: 7px; font-size: 12.5px; font-weight: 700;
  color: var(--text-muted); cursor: pointer; font-family: inherit;
}
.seg button:hover { color: var(--text); }
.seg button.on { background: var(--secondary); color: #fff; }
.seg-chico button { padding: 4px 10px; font-size: 12px; }

/* Estado de la información: muy discreto */
.frescura { margin-left: auto; display: flex; align-items: center; gap: 14px; font-size: 11.5px; color: var(--text-muted); }
.fr-item { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.fr-dot { width: 7px; height: 7px; border-radius: 50%; background: #9ca3af; flex: none; }
.fr-al_dia { background: var(--accent); }
.fr-atrasado { background: var(--warning); }
.fr-vencido { background: var(--danger); }
.fr-uf { font-weight: 700; }
.fr-aviso { color: var(--danger); font-weight: 600; }

.inm-error { background: var(--danger-light); color: var(--danger); border-radius: 8px; padding: 9px 14px; font-size: 12.5px; margin: 0; }

/* ── KPIs ── */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.kpi { background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius); padding: 14px 16px; border-left: 4px solid var(--secondary); }
.kpi-val { font-size: 26px; font-weight: 800; color: var(--text); line-height: 1.1; }
.kpi-lbl { font-size: 11.5px; color: var(--text-muted); margin-top: 4px; font-weight: 600; }
.kpi-bad { border-left-color: var(--danger); }
.kpi-bad .kpi-val { color: var(--danger); }
.kpi-ok { border-left-color: var(--accent); }
.kpi-warn { border-left-color: var(--warning); }

/* ── bloques ── */
.bloque { padding: 18px 20px; }
.bloque-t { font-size: 15px; font-weight: 800; color: var(--text); margin: 0 0 12px; display: flex; align-items: center; gap: 8px; }
.cnt { font-size: 11px; font-weight: 700; background: var(--primary-light); color: var(--primary); padding: 1px 8px; border-radius: 10px; }
.bloque-aviso { border-left: 4px solid var(--warning); }
.nota { font-size: 12px; color: var(--text-muted); margin: 0 0 10px; line-height: 1.5; }
.vacio { font-size: 13px; color: var(--text-muted); margin: 4px 0; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { background: var(--warning-light); color: #8a4b05; border-radius: 14px; padding: 3px 11px; font-size: 12px; font-weight: 700; }

.empty-card { padding: 50px 20px; text-align: center; color: var(--text-muted); }
.empty-icon { font-size: 40px; display: block; margin-bottom: 8px; }
.empty-sub { font-size: 12.5px; }

/* ── tablas ── */
.table-wrap { overflow-x: auto; }
.inm-tabla th, .inm-tabla td { padding: 9px 12px; white-space: nowrap; }
.th-r, .td-num { text-align: right; font-variant-numeric: tabular-nums; }
.td-movil { font-weight: 800; color: var(--secondary); }
.td-causa { max-width: 260px; overflow: hidden; text-overflow: ellipsis; }
.td-sub { color: var(--text-muted); font-size: 12px; }
.horas { font-weight: 700; }
.h-ambar { color: var(--warning); }
.h-rojo { color: var(--danger); }
.badge-aviso { background: var(--warning-light); color: #8a4b05; }
.arrastre { margin-left: 6px; font-size: 10.5px; color: var(--text-muted); font-style: italic; }
.mas { color: var(--text-muted); font-size: 11px; }

/* ── mensual ── */
.mes-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.mes-bar .nota { margin: 0; }
.mes-lbl { font-size: 12px; font-weight: 700; color: var(--text-muted); }
.input-mes { width: auto; min-width: 170px; padding: 7px 12px; }
.input-buscar { width: 200px; padding: 6px 12px; font-size: 12.5px; }
.tabla-cab { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.tabla-cab .bloque-t { margin: 0; }
.tabla-filtros { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.barras { display: flex; flex-direction: column; gap: 7px; }
.barra-fila { display: grid; grid-template-columns: minmax(110px, 220px) 1fr 32px; align-items: center; gap: 10px; font-size: 12.5px; }
.barra-lbl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.barra-pista { background: var(--surface-2); border-radius: 4px; height: 10px; overflow: hidden; }
.barra-rel { background: var(--secondary); height: 100%; border-radius: 4px; }
.barra-val { text-align: right; font-weight: 700; color: var(--text); }

.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

@media (max-width: 720px) {
  .frescura { margin-left: 0; width: 100%; }
  .input-buscar { width: 100%; }
}
</style>
