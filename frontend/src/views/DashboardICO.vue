<template>
  <div class="ico-root" :class="{ recargando: store.loading }">

    <!-- ══ SLICERS (filtros duros: escopan todo lo que hay debajo) ══ -->
    <section class="card slicers" aria-label="Filtros de eventos ICO">
      <div class="sl-fila">
        <div class="sl-grupo">
          <span class="sl-lbl">Unidad</span>
          <div class="sl-btns" role="group" aria-label="Unidad funcional">
            <button v-for="u in UNIDADES" :key="u.key" type="button" class="sl-btn"
              :class="['sl-btn--' + u.key.toLowerCase(), { active: f.uf.includes(u.key) }]" :aria-pressed="f.uf.includes(u.key)"
              @click="store.toggleUFICO(u.key)">{{ u.label }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Año</span>
          <select class="sl-select" aria-label="Año" @change="store.setAnioICO($event.target.value)">
            <option value="" :selected="!f.anio">Todos</option>
            <option v-for="y in opciones.anios" :key="y" :value="y" :selected="y === f.anio">{{ y }}</option>
          </select>
        </div>

        <div class="sl-grupo sl-grupo--meses">
          <span class="sl-lbl">Mes</span>
          <div class="sl-btns" role="group" aria-label="Mes">
            <button v-for="(m, i) in MESES_CORTOS" :key="m" type="button" class="sl-btn sl-btn--mes"
              :class="{ active: f.meses.includes(i + 1) }" :disabled="!mesDisponible(i + 1)"
              :aria-pressed="f.meses.includes(i + 1)" @click="store.toggleMesICO(i + 1)">{{ m }}</button>
          </div>
        </div>

        <div class="sl-acciones">
          <div class="sl-count" aria-live="polite">
            <span class="sl-count-n">{{ fmt(k.total) }}</span>
            <span class="sl-count-l">eventos</span>
          </div>
          <button type="button" class="sl-reset" @click="store.resetFiltrosICO()">✕ Limpiar</button>
        </div>
      </div>

      <div class="sl-fila">
        <div class="sl-grupo">
          <span class="sl-lbl">Tipo de infracción</span>
          <div class="sl-btns" role="group" aria-label="Tipo de infracción">
            <button v-for="t in TIPOS_INFRACCION" :key="t" type="button" class="sl-btn"
              :class="{ active: f.tipo_infraccion.includes(t) }" :aria-pressed="f.tipo_infraccion.includes(t)"
              @click="store.toggleTipoInfraccionICO(t)">{{ t }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Tipología</span>
          <div class="sl-btns" role="group" aria-label="Tipología">
            <button v-for="t in TIPOLOGIAS" :key="t.key" type="button" class="sl-btn"
              :class="{ active: f.tipologia.includes(t.key) }" :aria-pressed="f.tipologia.includes(t.key)"
              @click="store.toggleTipologiaICO(t.key)">{{ t.label }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Estado</span>
          <select class="sl-select" aria-label="Estado" @change="store.setEstadoICO($event.target.value)">
            <option value="" :selected="!f.estado">Todos</option>
            <option v-for="e in opciones.estados" :key="e" :value="e" :selected="e === f.estado">{{ e }}</option>
          </select>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Móvil / placa</span>
          <input type="search" class="sl-input" :value="f.busqueda" placeholder="Buscar…" aria-label="Buscar móvil o placa"
            @input="store.setBusquedaICO($event.target.value)" />
        </div>
      </div>
    </section>

    <!-- ══ SELECCIÓN CRUZADA (chips) o ayuda ══ -->
    <div v-if="store.icoHaySeleccion" class="sel-bar">
      <span class="sel-titulo">Filtrando por</span>
      <button v-for="c in store.icoChips" :key="c.dim + '|' + c.key" type="button" class="sel-chip"
        :title="'Quitar ' + c.texto" @click="store.quitarSelICO(c.dim, c.key)">
        {{ c.texto }} <span aria-hidden="true">✕</span>
      </button>
      <button type="button" class="sel-limpiar" @click="store.limpiarSelICO()">Borrar selección</button>
    </div>
    <p v-else class="hint">
      Haz clic en un día, un segmento de la dona, una fila o una unidad para filtrar todo el tablero. Ctrl + clic para elegir varios.
    </p>

    <!-- ══ SIN DATOS ══ -->
    <div v-if="!store.icoRaw.length && !store.loading" class="card vacio vacio--grande">
      Aún no hay eventos ICO cargados. Sube el Excel desde <router-link to="/ico">Indicadores ICO</router-link>.
    </div>

    <template v-else>

      <!-- ══ KPIs SECUNDARIOS ══ -->
      <div class="mini-kpis">
        <div class="mini">
          <span class="mini-n">{{ fmt(k.moviles) }}</span>
          <span class="mini-l">Móviles con eventos</span>
        </div>
        <div class="mini">
          <span class="mini-n">{{ fmt(k.tipos) }}</span>
          <span class="mini-l">Códigos de novedad</span>
        </div>
        <div class="mini">
          <span class="mini-n">{{ fmt(k.sinContestar) }}</span>
          <span class="mini-l">Sin contestar</span>
        </div>
        <div class="mini" :class="{ 'mini--alerta': k.ventanaAbierta > 0 }"
          title="Sin contestar cuya F. cierre DPV aún no vence: todavía se pueden responder">
          <span class="mini-n">{{ fmt(k.ventanaAbierta) }}</span>
          <span class="mini-l">Por responder (ventana abierta)</span>
        </div>
      </div>

      <!-- ══ FILA SUPERIOR: KPIs + dona + mapa de calor ══ -->
      <div class="top-row">

        <div class="card panel-kpi">
          <div class="kpi-blk">
            <div class="kpi-l">No. EVENTOS</div>
            <div class="kpi-n">{{ fmt(k.total) }}</div>
            <div v-if="store.icoHaySeleccion" class="kpi-sub">de {{ fmt(k.baseTotal) }} del filtro</div>
          </div>
          <div class="kpi-blk kpi-blk--pts">
            <div class="kpi-l">PUNTOS</div>
            <div class="kpi-n kpi-pts">{{ fmt(k.puntos) }}</div>
            <div v-if="store.icoHaySeleccion" class="kpi-sub">de {{ fmt(k.baseTotalPuntos) }} del filtro</div>
          </div>

          <div class="dona-section">
            <div class="dona-title">TIPOLOGÍA</div>
            <svg viewBox="0 0 160 140" class="dona-svg" role="img"
              :aria-label="'Tipología: ' + store.icoDona.map(s => s.label + ' ' + s.total).join(', ')">
              <circle cx="80" cy="74" r="52" fill="none" stroke="#E5E7EB" stroke-width="28" />
              <template v-for="seg in store.icoDona" :key="seg.key">
                <circle v-if="seg.total > 0" class="dona-arco" cx="80" cy="74" r="52" fill="none"
                  :stroke="seg.color" stroke-width="28"
                  :stroke-dasharray="seg.dash + ' ' + seg.gap" :stroke-dashoffset="-seg.offset"
                  transform="rotate(-90 80 74)" :opacity="segOpacidad(seg)"
                  @click="clickSel('tipologia', seg.key, $event)">
                  <title>{{ seg.label }}: {{ seg.total }} ({{ seg.pct }}%)</title>
                </circle>
              </template>
              <text x="80" y="72" text-anchor="middle" font-size="19" font-weight="800" fill="#084534">{{ fmt(k.total) }}</text>
              <text x="80" y="87" text-anchor="middle" font-size="9" fill="#5a7068">eventos</text>
            </svg>
            <div class="dona-leyenda">
              <button v-for="seg in store.icoDona" :key="seg.key" type="button" class="dona-item"
                :class="{ sel: seg.seleccionado, dim: haySel('tipologia') && !seg.seleccionado }"
                :aria-pressed="seg.seleccionado" @click="clickSel('tipologia', seg.key, $event)">
                <span class="dona-dot" :style="{ background: seg.color }"></span>
                <span class="dona-info">
                  <span class="dona-tipo">{{ seg.label }}</span>
                  <span class="dona-cnt">{{ fmt(seg.total) }} ({{ seg.pct }}%)</span>
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- Mapa de calor -->
        <div class="card panel-calor" ref="calorPanel">
          <div class="calor-head">
            <div class="calor-title">No. EVENTOS POR MAPA DE CALOR</div>
            <div class="calor-sub">{{ periodoTxt }} · {{ heat.modo === 'dia' ? 'por día' : 'por mes' }}</div>
          </div>

          <div v-if="!heat.columnas.length" class="vacio">Sin datos para este filtro</div>
          <div v-else class="calor-chart">
            <div class="calor-scroll">
              <div class="calor-plot">
                <div class="calor-eje" aria-hidden="true">
                  <span v-for="t in heat.ticks" :key="t" class="eje-tick" :style="{ '--p': heat.max ? t / heat.max : 0 }">{{ t }}</span>
                </div>
                <div class="calor-area" :style="{ minWidth: anchoMinimoHeat + 'px' }">
                  <div v-for="t in heat.ticks" :key="'g' + t" class="grid-line" :style="{ '--p': heat.max ? t / heat.max : 0 }"></div>
                  <div class="calor-barras">
                    <button v-for="c in heat.columnas" :key="c.key" type="button" class="calor-col"
                      :class="{ sel: c.seleccionado, dim: haySel('periodos') && !c.seleccionado, fin: c.finDeSemana }"
                      :aria-pressed="c.seleccionado" :aria-label="etiquetaColumna(c)"
                      @click="clickSel('periodos', c.key, $event)"
                      @mouseenter="mostrarTip(c, $event)" @mouseleave="ocultarTip"
                      @focus="mostrarTip(c, $event)" @blur="ocultarTip">
                      <span class="calor-num">{{ mostrarNumeros && c.total ? c.total : '' }}</span>
                      <span class="calor-barra-wrap">
                        <span class="calor-barra" :style="estiloBarra(c)"></span>
                      </span>
                      <span class="calor-lbl">{{ etiquetaCol(c) }}</span>
                      <span class="calor-sub2">{{ c.sub }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="calor-leyenda">
            <template v-if="heat.modo === 'dia'">
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.bajo }"></span>Bajo 1–{{ HEAT_DIA.medio - 1 }}</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.medio }"></span>Medio {{ HEAT_DIA.medio }}–{{ HEAT_DIA.alto - 1 }}</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.alto }"></span>Alto {{ HEAT_DIA.alto }}+</span>
              <span class="cl-item cl-item--nota">eventos por día (F. identificación)</span>
            </template>
            <template v-else>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.bajo }"></span>Bajo</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.medio }"></span>Medio</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.alto }"></span>Alto</span>
              <span class="cl-item cl-item--nota">relativo al mes con más eventos</span>
            </template>
          </div>

          <div v-if="tip" class="tip" role="tooltip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }">
            <div class="tip-t">{{ tip.col.titulo }}</div>
            <div class="tip-v">{{ fmt(tip.col.total) }} <span class="tip-u">{{ tip.col.total === 1 ? 'evento' : 'eventos' }}</span></div>
            <div class="tip-r">{{ fmt(tip.col.puntos) }} puntos</div>
            <div class="tip-n"><span class="tip-key" :style="{ background: tip.col.color }"></span>{{ textoNivel(tip.col.nivel) }}</div>
          </div>
        </div>
      </div>

      <!-- ══ FILA INFERIOR: rankings + detalle ══ -->
      <div class="bottom-row">

        <div class="left-col">
          <div v-for="p in paneles" :key="p.dim" class="card rank-card">
            <div class="tabla-hdr">{{ p.titulo }}</div>
            <div class="rank-cab"><span>{{ p.col }}</span><span></span><span class="r">EVENTOS</span><span class="r">PTS</span></div>
            <div class="rank-lista">
              <div v-if="!p.filas.length" class="vacio">Sin datos</div>
              <button v-for="r in p.filas" :key="r.key" type="button" class="rank-row"
                :class="{ sel: r.seleccionado, dim: haySel(p.dim) && !r.seleccionado }" :aria-pressed="r.seleccionado"
                :title="r.label + ': ' + r.total + ' eventos · ' + r.puntos + ' puntos (' + r.pct + '%)'"
                @click="clickSel(p.dim, r.key, $event)">
                <span class="rank-lbl" :class="{ mono: p.mono }">{{ r.label }}</span>
                <span class="rank-track"><span class="rank-fill" :style="{ width: anchoBarra(r, p.filas) + '%' }"></span></span>
                <span class="rank-n">{{ fmt(r.total) }}</span>
                <span class="rank-pts">{{ r.puntos ? fmt(r.puntos) : '' }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="card detalle-card">
          <div class="tabla-hdr tabla-hdr--flex">
            <span>DESCRIPCIÓN DE EVENTOS</span>
            <span class="tabla-badge">{{ fmt(filas.length) }}</span>
            <button type="button" class="btn-export" :disabled="!filas.length" @click="exportarCSV">⬇ Exportar CSV</button>
          </div>
          <div class="scroll-inner">
            <table class="mt">
              <thead>
                <tr>
                  <th v-for="c in COLUMNAS" :key="c.key" :class="c.cls" :aria-sort="ariaSort(c.key)">
                    <button type="button" class="th-btn" @click="ordenarPor(c.key)">
                      {{ c.label }}<span class="sort-ind">{{ flecha(c.key) }}</span>
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                <template v-for="r in visibles" :key="r.ico_id">
                  <tr class="fila" :class="{ abierta: expandido === r.ico_id }" tabindex="0"
                    :aria-expanded="expandido === r.ico_id"
                    @click="alternarFila(r)" @keydown.enter.prevent="alternarFila(r)">
                    <td class="td-id">{{ r.ico_id }}</td>
                    <td class="td-movil">{{ r.movil || r.placa }}</td>
                    <td><span class="code-badge">{{ r.tipo_novedad }}</span></td>
                    <td>
                      <span class="badge" :class="r.tipo_infraccion === 'Directo' ? 'badge-danger' : 'badge-warning'">{{ r.tipo_infraccion }}</span>
                    </td>
                    <td class="td-pts">{{ r.puntos || '—' }}</td>
                    <td><span class="badge" :class="badgeClass(r.estado)">{{ r.estado }}</span></td>
                    <td class="td-fecha">{{ fechaCorta(r.fecha) }}</td>
                    <td class="td-fecha">{{ fechaCorta(r.fecha_cierre) }}</td>
                    <td class="td-dias">
                      <span v-if="dias(r) !== null" class="dias-chip" :class="claseDias(dias(r))">{{ dias(r) === 0 ? 'Hoy' : dias(r) + ' d' }}</span>
                      <span v-else class="muted">—</span>
                    </td>
                    <td class="td-desc" :title="r.descripcion">{{ r.descripcion }}</td>
                  </tr>
                  <tr v-if="expandido === r.ico_id" class="fila-detalle">
                    <td :colspan="COLUMNAS.length">
                      <p class="det-desc">{{ r.descripcion || 'Sin descripción' }}</p>
                      <dl class="det-meta">
                        <div><dt>Empresa</dt><dd>{{ r.empresa || '—' }}</dd></div>
                        <div><dt>Placa</dt><dd>{{ r.placa || '—' }}</dd></div>
                        <div><dt>Tipología</dt><dd>{{ r.tipologia || '—' }}</dd></div>
                        <div><dt>Dirección</dt><dd>{{ r.direccion || '—' }}</dd></div>
                        <div><dt>F. notificación</dt><dd>{{ fechaCorta(r.fecha_notificacion) }}</dd></div>
                        <div><dt>F. novedad</dt><dd>{{ fechaCorta(r.fecha_novedad) }} {{ r.hora }}</dd></div>
                        <div><dt>Día</dt><dd>{{ r.dia_semana || '—' }}</dd></div>
                      </dl>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
            <div v-if="!filas.length" class="vacio">Sin eventos para este filtro</div>
          </div>
          <div v-if="filas.length > visibles.length" class="mas">
            <button type="button" class="btn-mas" @click="mostrarMas">Mostrar {{ Math.min(PAGINA, filas.length - visibles.length) }} más</button>
            <span class="mas-txt">{{ fmt(visibles.length) }} de {{ fmt(filas.length) }}</span>
          </div>
        </div>

      </div>
    </template>

  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import { useDashboard } from './useDashboard.js'
import {
  MESES_CORTOS, HEAT_COLORES, HEAT_DIA, TIPOS_INFRACCION,
  diasParaResponder, hoyISO, ordenar, csvICO, sinTildes, tituloPeriodo as tituloPeriodoDe,
} from './icoUtils.js'

const store = useDashboardStore()
const { badgeClass } = useDashboard()

// ── Constantes de la vista ──
const UNIDADES   = [{ key: 'UF10', label: 'UF-10' }, { key: 'UF16', label: 'UF-16' }]
const TIPOLOGIAS = [{ key: 'BUSETON', label: 'BUSETON' }, { key: 'PADRON', label: 'PADRÓN' }]
const COLORES    = HEAT_COLORES
const PAGINA     = 100   // filas que se agregan cada vez en el detalle
// F. notificación no es columna (se ve al expandir la fila y va en el CSV): así la descripción cabe sin scroll horizontal
const COLUMNAS = [
  { key: 'ico_id',             label: 'ID INFRACCIÓN',  cls: '' },
  { key: 'movil',              label: 'MÓVIL',          cls: '' },
  { key: 'tipo_novedad',       label: 'CÓDIGO',         cls: '' },
  { key: 'tipo_infraccion',    label: 'TIPO INFRACCIÓN', cls: '' },
  { key: 'puntos',             label: 'PUNTOS',         cls: 'th-r' },
  { key: 'estado',             label: 'ESTADO',         cls: '' },
  { key: 'fecha',              label: 'F. IDENT.',      cls: '' },
  { key: 'fecha_cierre',       label: 'F. CIERRE DPV',  cls: '' },
  { key: 'dias',               label: 'DÍAS P/ RESPONDER', cls: 'th-r' },
  { key: 'descripcion',        label: 'DESCRIPCIÓN',    cls: 'th-desc' },
]
const DIR_INICIAL = { ico_id: 'desc', puntos: 'desc', fecha: 'desc', fecha_cierre: 'desc', dias: 'asc' }
const hoy = hoyISO()

// ── Estado derivado del store ──
const f        = computed(() => store.icoFiltros)
const k        = computed(() => store.icoKPIs)
const heat     = computed(() => store.icoHeatmap)
const opciones = computed(() => store.icoOpciones)
const periodoTxt = computed(() => tituloPeriodoDe(store.icoFiltros))

const paneles = computed(() => [
  { dim: 'tipo_novedad',    titulo: 'TIPO NOVEDAD POR No. EVENTOS',      col: 'CÓDIGO', filas: store.icoTipoNovedad, mono: true },
  { dim: 'tipo_infraccion', titulo: 'TIPO DE INFRACCIÓN POR No. EVENTOS', col: 'TIPO',   filas: store.icoTipoInfraccion, mono: false },
  { dim: 'estado',          titulo: 'ESTADO DE LA RESPUESTA',            col: 'ESTADO', filas: store.icoEstados, mono: false },
  { dim: 'movil',           titulo: 'TOP 10 UNIDADES CON MÁS ICO',       col: 'MÓVIL',  filas: store.icoTopMoviles.slice(0, 10), mono: false },
])

// ── Helpers de presentación ──
const fmt = n => Number(n || 0).toLocaleString('es-CO')
const fechaCorta = iso => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : '—')
const mesDisponible = m => !!f.value.anio && (opciones.value.mesesPorAnio[f.value.anio] || []).includes(m)
const haySel = dim => store.icoSel[dim].length > 0
const segOpacidad = seg => (haySel('tipologia') && !seg.seleccionado ? 0.35 : 1)
const anchoBarra = (r, filasPanel) => Math.max(2, Math.round((r.total / ((filasPanel[0] && filasPanel[0].total) || 1)) * 100))
const textoNivel = n => ({ bajo: 'Nivel bajo', medio: 'Nivel medio', alto: 'Nivel alto', vacio: 'Sin eventos' })[n]
const etiquetaColumna = c => `${c.titulo}: ${c.total} eventos, ${c.puntos} puntos`

// Clic en una visual → selección cruzada (Ctrl / ⌘ / Shift suma elementos)
function clickSel(dim, key, ev) {
  store.toggleSelICO(dim, key, !!(ev && (ev.ctrlKey || ev.metaKey || ev.shiftKey)))
}

// ── Mapa de calor ──
const mostrarNumeros  = computed(() => heat.value.columnas.length <= 31)
// La altura de la gráfica es fluida (se adapta a la tarjeta), por eso las barras son un % del máximo
const estiloBarra = c => ({
  height: (c.total ? (c.total / Math.max(1, heat.value.max)) * 100 : 0) + '%',
  minHeight: c.total ? '3px' : '2px',
  background: c.color,
})
const anchoMinimoHeat = computed(() => {
  const porColumna = heat.value.modo === 'dia' ? 24 : heat.value.modo === 'mes' ? 44 : 14
  return heat.value.columnas.length * porColumna
})
// Con ~60 columnas mensuales no caben todas las etiquetas: se muestra una de cada tres (Ene, Abr, Jul, Oct)
const etiquetaCol = c => (heat.value.modo === 'anio-mes' && (Number(c.key.slice(5, 7)) - 1) % 3 !== 0 ? '' : c.label)

// Tooltip propio (también con foco de teclado), anclado a la barra: valor en grande, etiqueta debajo
const calorPanel = ref(null)
const tip = ref(null)
const TIP_ALTO = 100   // alto aprox. del tooltip + margen: si la barra llega muy arriba, se baja para no salirse de la tarjeta
function mostrarTip(c, ev) {
  const panel = calorPanel.value
  const el = ev && ev.currentTarget
  if (!panel || !el) return
  const pr = panel.getBoundingClientRect()
  const cr = el.getBoundingClientRect()
  // la altura de la barra se calcula desde el dato (no desde el DOM): así no depende de la animación de altura en curso
  const wrap = el.querySelector('.calor-barra-wrap')
  const wr = wrap ? wrap.getBoundingClientRect() : cr
  const alto = c.total ? Math.max(3, (c.total / Math.max(1, heat.value.max)) * wr.height) : 2
  const arriba = wr.bottom - alto - pr.top
  const x = Math.min(Math.max(cr.left - pr.left + cr.width / 2, 90), Math.max(90, pr.width - 90))
  tip.value = { x, y: Math.max(arriba, TIP_ALTO), col: c }
}
const ocultarTip = () => { tip.value = null }
watch(heat, ocultarTip)

// ── Tabla de detalle: orden, paginación, fila expandida, CSV ──
const orden     = ref({ key: 'fecha', dir: 'desc' })
const limite    = ref(PAGINA)
const expandido = ref(null)
const filas     = computed(() => ordenar(store.icoFiltrado, orden.value.key, orden.value.dir, hoy))
const visibles  = computed(() => filas.value.slice(0, limite.value))
watch(() => store.icoFiltrado, () => { limite.value = PAGINA; expandido.value = null })

function ordenarPor(key) {
  orden.value = orden.value.key === key
    ? { key, dir: orden.value.dir === 'asc' ? 'desc' : 'asc' }
    : { key, dir: DIR_INICIAL[key] || 'asc' }
  limite.value = PAGINA
}
const ariaSort = key => (orden.value.key !== key ? 'none' : orden.value.dir === 'asc' ? 'ascending' : 'descending')
const flecha   = key => (orden.value.key !== key ? '' : orden.value.dir === 'asc' ? ' ▲' : ' ▼')
const mostrarMas  = () => { limite.value += PAGINA }
const alternarFila = r => { expandido.value = expandido.value === r.ico_id ? null : r.ico_id }
const dias      = r => diasParaResponder(r, hoy)
const claseDias = d => (d <= 1 ? 'dias-urgente' : d <= 3 ? 'dias-pronto' : 'dias-ok')

function exportarCSV() {
  const blob = new Blob(['﻿' + csvICO(filas.value)], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ICO_${sinTildes(periodoTxt.value).replace(/[^A-Za-z0-9]+/g, '_')}_${hoy}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.ico-root { display: flex; flex-direction: column; gap: 14px; min-width: 0; transition: opacity .15s; }
.ico-root.recargando { opacity: .6; pointer-events: none; }   /* al recargar se conserva el marco, sin saltos */

button { font-family: inherit; }
button:focus-visible, select:focus-visible, input:focus-visible, .fila:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px;
}
.vacio { padding: 18px; text-align: center; font-size: 12px; color: var(--text-muted); }
.vacio--grande { padding: 36px 18px; font-size: 14px; }
.vacio a { color: var(--primary); font-weight: 700; text-decoration: underline; }
.muted { color: var(--text-muted); }

/* ── Slicers ── */
.slicers { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.sl-fila { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 20px; }
.sl-grupo { display: flex; align-items: center; gap: 8px; }
.sl-lbl { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }
.sl-btns { display: flex; flex-wrap: wrap; gap: 4px; }
.sl-btn {
  padding: 5px 12px; border: 1.5px solid var(--border); background: var(--surface-2); color: var(--text-muted);
  border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s;
}
.sl-btn:hover:not(:disabled):not(.active) { border-color: var(--accent); color: var(--primary); }
/* Seleccionado = fondo oscuro + texto blanco (contraste ≈ 11:1; el verde acento con blanco solo da 2,7:1) */
.sl-btn.active { background: var(--primary); border-color: var(--primary); color: #fff; }
/* Mismos colores por unidad que la pestaña DPV */
.sl-btn--uf10.active { background: #074e7a; border-color: #074e7a; }
.sl-btn--uf16.active { background: #1f7a6e; border-color: #1f7a6e; }   /* un tono más oscuro que el de DPV (#248a7c): con blanco sube de 4,2:1 a 5,2:1 */
.sl-btn:disabled { opacity: .4; cursor: not-allowed; }
.sl-btn--mes { padding: 4px 7px; min-width: 38px; font-size: 11.5px; }
.sl-select, .sl-input {
  padding: 5px 9px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 12px;
  color: var(--text); background: var(--surface-2); font-family: inherit;
}
.sl-select { cursor: pointer; }
.sl-input { min-width: 150px; }
.sl-reset {
  padding: 5px 12px; border: 1.5px solid var(--danger-light); background: var(--danger-light); color: var(--danger);
  border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .15s; white-space: nowrap;
}
.sl-reset:hover { background: var(--danger); border-color: var(--danger); color: #fff; }
.sl-acciones { margin-left: auto; display: flex; align-items: center; gap: 14px; }
.sl-count { display: flex; align-items: baseline; gap: 5px; }
.sl-count-n { font-size: 22px; font-weight: 800; color: var(--primary); }
.sl-count-l { font-size: 11px; color: var(--text-muted); }

/* ── Selección cruzada ── */
.sel-bar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; padding: 8px 12px;
  background: var(--accent-light); border: 1px solid var(--accent); border-radius: 10px; font-size: 12px;
}
.sel-titulo { font-size: 11px; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: .4px; }
.sel-chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  background: var(--surface); border: 1px solid var(--accent); color: var(--primary);
  font-size: 11.5px; font-weight: 700; cursor: pointer;
}
.sel-chip:hover { background: var(--danger-light); border-color: var(--danger); color: var(--danger); }
.sel-limpiar {
  margin-left: auto; padding: 3px 12px; border-radius: 6px; border: 1.5px solid var(--primary);
  background: var(--primary); color: #fff; font-size: 11.5px; font-weight: 700; cursor: pointer;
}
.sel-limpiar:hover { background: var(--primary-dark); }
.hint { font-size: 11.5px; color: var(--text-muted); padding: 0 4px; }

/* ── KPIs secundarios ── */
.mini-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.mini {
  display: flex; align-items: baseline; gap: 8px; padding: 9px 14px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
}
.mini-n { font-size: 20px; font-weight: 800; color: var(--primary); }
.mini-l { font-size: 11.5px; color: var(--text-muted); line-height: 1.25; }
.mini--alerta { background: var(--warning-light); border-color: var(--warning); }
.mini--alerta .mini-n { color: #8a4b05; }   /* ámbar oscuro: --warning sobre este fondo no llega a 3:1 */

/* ── Fila superior ── */
.top-row { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 14px; align-items: stretch; }

.panel-kpi { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.kpi-blk { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; }
.kpi-blk--pts { background: var(--lime-light); border-color: var(--lime); }
.kpi-l { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 2px; }
.kpi-n { font-size: 36px; font-weight: 800; color: var(--primary); line-height: 1.05; }
.kpi-sub { font-size: 10.5px; color: var(--text-muted); margin-top: 3px; }

.dona-section { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.dona-title { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .4px; }
.dona-svg { width: 150px; height: 120px; }
.dona-arco { cursor: pointer; transition: opacity .2s; }
.dona-arco:hover { filter: brightness(1.08); }
.dona-leyenda { display: flex; flex-direction: column; gap: 4px; width: 100%; }
.dona-item {
  display: flex; align-items: center; gap: 8px; padding: 4px 8px; border: 0; background: transparent;
  border-radius: 6px; cursor: pointer; text-align: left; color: var(--text);
}
.dona-item:hover { background: var(--primary-light); }
.dona-item.sel { background: var(--accent-light); box-shadow: inset 0 0 0 1.5px var(--accent); }
/* Sobre el verde claro de lo seleccionado el gris de apoyo se oscurece para mantener contraste AA (4,4:1 → 6,3:1) */
.dona-item.sel, .rank-row.sel, .calor-col.sel { --text-muted: #46594f; }
.dona-item.dim { opacity: .45; }
.dona-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dona-info { display: flex; flex-direction: column; }
.dona-tipo { font-size: 11px; font-weight: 700; }
.dona-cnt { font-size: 10.5px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

/* ── Mapa de calor ── */
.panel-calor {
  --num-h: 14px; --lbl-h: 26px; --plot-min: 150px;   /* el alto de las barras se reparte según el alto de la tarjeta */
  position: relative; padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 10px; min-width: 0;
}
.calor-head { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 4px 12px; }
.calor-title { font-size: 12px; font-weight: 800; color: var(--text); text-transform: uppercase; letter-spacing: .4px; }
.calor-sub { font-size: 11.5px; color: var(--text-muted); }
/* El contenedor crece para llenar la tarjeta (o mide --plot-min como mínimo) y el gráfico va posicionado dentro:
   así los % de altura de las barras siempre tienen una referencia definida, también en pantallas estrechas */
.calor-chart { position: relative; flex: 1 1 auto; min-height: calc(var(--num-h) + var(--plot-min) + var(--lbl-h)); }
.calor-scroll { position: absolute; inset: 0; overflow-x: auto; overflow-y: hidden; }
/* Eje y barras comparten el mismo alto, y el eje queda fijo a la izquierda al desplazar en horizontal */
.calor-plot { display: flex; gap: 6px; height: 100%; width: max-content; min-width: 100%; padding-right: 10px; }   /* margen para que no se recorte la última etiqueta */
.calor-eje { position: sticky; left: 0; z-index: 2; flex: none; width: 28px; background: var(--surface); }
.eje-tick {
  position: absolute; right: 2px; bottom: calc(var(--lbl-h) + var(--p) * (100% - var(--num-h) - var(--lbl-h)));
  transform: translateY(50%); font-size: 10px; color: var(--text-muted); font-variant-numeric: tabular-nums;
}
.calor-area { position: relative; flex: 1 0 auto; }
.grid-line {
  position: absolute; left: 0; right: 0; height: 0; border-top: 1px solid var(--border); pointer-events: none;
  bottom: calc(var(--lbl-h) + var(--p) * (100% - var(--num-h) - var(--lbl-h)));
}
.calor-barras { position: relative; display: flex; align-items: flex-end; gap: 2px; height: 100%; }
.calor-col {
  flex: 1 1 0; min-width: 0; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center;
  padding: 0; border: 0; border-radius: 6px; background: transparent; cursor: pointer; color: inherit; font: inherit;
}
.calor-col:hover, .calor-col:focus-visible { background: var(--primary-light); }
.calor-col.sel { background: var(--accent-light); box-shadow: inset 0 0 0 1.5px var(--accent); }
.calor-col.dim .calor-barra { opacity: .35; }
.calor-col.dim .calor-num { opacity: .5; }
.calor-num { height: var(--num-h); line-height: var(--num-h); font-size: 10px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.calor-barra-wrap { flex: 1 1 0; min-height: 0; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.calor-barra { display: block; width: 70%; max-width: 24px; border-radius: 4px 4px 0 0; transition: height .25s ease, opacity .2s; }
.calor-col:hover .calor-barra { filter: brightness(1.07); }
.calor-lbl { height: 14px; line-height: 14px; font-size: 10.5px; font-weight: 600; color: var(--text-muted); }
.calor-sub2 { height: 12px; line-height: 12px; font-size: 9px; color: var(--text-muted); }
.calor-col.fin .calor-sub2 { color: #8a4b05; font-weight: 800; }

.calor-leyenda { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 4px 14px; font-size: 11px; color: var(--text); }
.cl-item { display: inline-flex; align-items: center; gap: 5px; }
.cl-item--nota { color: var(--text-muted); }
.cl-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }

.tip {
  position: absolute; z-index: 5; min-width: 128px; padding: 8px 11px; border-radius: 8px; pointer-events: none;
  transform: translate(-50%, calc(-100% - 8px)); background: var(--text); color: #fff; box-shadow: var(--shadow-md);
}
.tip-t { font-size: 10.5px; color: rgba(255, 255, 255, .72); }
.tip-v { font-size: 16px; font-weight: 800; line-height: 1.25; }
.tip-u { font-size: 11px; font-weight: 600; color: rgba(255, 255, 255, .8); }
.tip-r { font-size: 11px; color: rgba(255, 255, 255, .85); }
.tip-n { display: flex; align-items: center; gap: 6px; margin-top: 3px; font-size: 10.5px; color: rgba(255, 255, 255, .72); }
.tip-key { width: 12px; height: 3px; border-radius: 2px; flex-shrink: 0; }

/* ── Fila inferior ── */
.bottom-row { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 14px; align-items: start; }
.left-col { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.rank-card { overflow: hidden; }
.tabla-hdr { background: var(--primary); color: #fff; font-size: 10px; font-weight: 700; padding: 8px 12px; text-transform: uppercase; letter-spacing: .4px; }
.rank-cab, .rank-row { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) 40px 44px; gap: 8px; align-items: center; }
.rank-cab { padding: 5px 12px; font-size: 9.5px; font-weight: 700; color: var(--primary); background: var(--accent-light); }
.rank-cab .r { text-align: right; }
.rank-lista { max-height: 250px; overflow-y: auto; padding: 4px 6px 6px; }
.rank-row {
  width: 100%; padding: 5px 6px; border: 0; background: transparent; border-radius: 6px; cursor: pointer;
  text-align: left; color: var(--text);
}
.rank-row:hover, .rank-row:focus-visible { background: var(--primary-light); }
.rank-row.sel { background: var(--accent-light); box-shadow: inset 0 0 0 1.5px var(--accent); }
.rank-row.dim { opacity: .45; }
.rank-lbl { font-size: 11.5px; font-weight: 700; line-height: 1.25; overflow-wrap: anywhere; }   /* «Contestado No Contundente» se parte en 2 líneas en vez de cortarse */
.rank-lbl.mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
.rank-track { height: 8px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.rank-fill { display: block; height: 100%; background: var(--accent); border-radius: 0 4px 4px 0; transition: width .3s; }
.rank-n { text-align: right; font-size: 12px; font-weight: 800; color: var(--primary); font-variant-numeric: tabular-nums; }
.rank-pts { text-align: right; font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

/* ── Detalle ── */
.detalle-card { overflow: hidden; display: flex; flex-direction: column; min-width: 0; }
.tabla-hdr--flex { display: flex; align-items: center; gap: 10px; }
.tabla-badge { background: rgba(255, 255, 255, .92); color: var(--primary); border-radius: 10px; padding: 1px 8px; font-size: 10px; }
.btn-export {
  margin-left: auto; padding: 3px 10px; border: 1.5px solid rgba(255, 255, 255, .6); border-radius: 6px;
  background: transparent; color: #fff; font-size: 10.5px; font-weight: 700; cursor: pointer;
}
.btn-export:hover:not(:disabled) { background: #fff; color: var(--primary); }
.btn-export:disabled { opacity: .5; cursor: not-allowed; }
.scroll-inner { overflow: auto; max-height: 620px; }
.mt { width: 100%; border-collapse: collapse; font-size: 11.5px; }
.mt th {
  position: sticky; top: 0; z-index: 1; padding: 0; text-align: left; white-space: nowrap;
  background: var(--accent-light); border-bottom: 1.5px solid var(--border);
}
.th-r { text-align: right; }
.th-btn {
  display: block; width: 100%; padding: 6px; border: 0; background: transparent; cursor: pointer;
  color: var(--primary); font-size: 9.5px; font-weight: 700; text-align: inherit; line-height: 1.2; white-space: normal;
}
.th-btn:hover { background: var(--primary-light); }
.sort-ind { font-size: 8px; }
.mt td { padding: 5px 6px; border-bottom: 1px solid var(--border); color: var(--text); vertical-align: middle; }
.fila { cursor: pointer; }
.fila:hover td, .fila.abierta td { background: var(--primary-light); }
.td-id { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 10.5px; }
.td-movil { font-weight: 700; font-size: 11px; white-space: nowrap; }
.td-pts { text-align: right; font-weight: 800; color: var(--text); font-variant-numeric: tabular-nums; }
.td-fecha { white-space: nowrap; font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.td-dias { text-align: right; white-space: nowrap; }
/* La descripción ocupa el espacio que sobra y se corta con «…» (el texto completo está en el tooltip y al expandir la fila) */
.th-desc { width: 100%; min-width: 130px; }
.td-desc { width: 100%; max-width: 0; min-width: 130px; font-size: 10.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.code-badge {
  background: var(--primary-light); color: var(--primary); padding: 2px 7px; border-radius: 4px; white-space: nowrap;
  font-size: 10px; font-weight: 700; font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
}
.mt .badge { font-size: 10px; padding: 2px 8px; }
.mt .badge-warning { color: #8a4b05; }   /* el ámbar de main.css (#d4780a) sobre fondo claro da 2,9:1; este da 6,2:1 */
.dias-chip { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10.5px; font-weight: 800; }
.dias-urgente { background: var(--danger-light); color: var(--danger); }
.dias-pronto  { background: var(--warning-light); color: #8a4b05; }
.dias-ok      { background: var(--accent-light); color: var(--primary); }

.fila-detalle td { background: var(--surface-2); padding: 10px 14px 12px; }
.det-desc { margin: 0 0 8px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
.det-meta { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 6px 16px; margin: 0; }
.det-meta dt { font-size: 9.5px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .3px; }
.det-meta dd { margin: 0; font-size: 11.5px; }

.mas { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px; border-top: 1px solid var(--border); }
.btn-mas {
  padding: 5px 14px; border: 1.5px solid var(--accent); background: var(--surface); color: var(--primary);
  border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;
}
.btn-mas:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
.mas-txt { font-size: 11px; color: var(--text-muted); }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .top-row, .bottom-row { grid-template-columns: minmax(0, 1fr); }
  .left-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); align-items: start; }   /* rankings en 2 columnas si caben */
  .mini-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .panel-kpi { flex-direction: row; flex-wrap: wrap; align-items: stretch; }
  .panel-kpi .kpi-blk { flex: 1 1 140px; }
  .panel-kpi .dona-section { flex: 1 1 100%; flex-direction: row; justify-content: center; flex-wrap: wrap; }
  .dona-leyenda { width: auto; min-width: 150px; }
}
@media (max-width: 560px) {
  .slicers { padding: 14px; gap: 14px; }
  .sl-fila { display: contents; }   /* aplana las filas: así el contador y «Limpiar» (order) quedan al final */
  .sl-grupo { flex-direction: column; align-items: stretch; gap: 7px; }
  .sl-btns { width: 100%; }
  .sl-btn { flex: 1; text-align: center; }
  .sl-btn--mes { flex: 1 0 14%; }
  .sl-select, .sl-input { width: 100%; }
  .sl-acciones { order: 99; margin-left: 0; flex-direction: column; align-items: stretch; gap: 10px; padding-top: 12px; border-top: 1px solid var(--border); }
  .sl-count { justify-content: space-between; }
  .sl-reset { width: 100%; }
  .mini-kpis { grid-template-columns: minmax(0, 1fr); }
  .btn-export { padding: 3px 8px; }
}
</style>