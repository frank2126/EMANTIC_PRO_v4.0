<template>
  <div ref="raiz" class="dpv-root" :class="{ recargando: store.loading }">

    <!-- ══ SLICERS (filtros duros: escopan todo lo que hay debajo) ══ -->
    <section class="card slicers" aria-label="Filtros de eventos DPV">
      <div class="sl-fila">
        <div class="sl-grupo">
          <span class="sl-lbl">Unidad</span>
          <div class="sl-btns" role="group" aria-label="Unidad funcional">
            <button v-for="u in UNIDADES" :key="u.key" type="button" class="sl-btn"
              :class="['sl-btn--' + u.key.toLowerCase(), { active: f.uf.includes(u.key) }]" :aria-pressed="f.uf.includes(u.key)"
              @click="store.toggleUFDPV(u.key)">{{ u.label }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Año</span>
          <select class="sl-select" aria-label="Año" @change="store.setAnioDPV($event.target.value)">
            <option value="" :selected="!f.anio">Todos</option>
            <option v-for="y in opciones.anios" :key="y" :value="y" :selected="y === f.anio">{{ y }}</option>
          </select>
        </div>

        <div class="sl-grupo sl-grupo--meses">
          <span class="sl-lbl">Mes</span>
          <div class="sl-btns" role="group" aria-label="Mes">
            <button v-for="(m, i) in MESES_CORTOS" :key="m" type="button" class="sl-btn sl-btn--mes"
              :class="{ active: f.meses.includes(i + 1) }" :disabled="!mesDisponible(i + 1)"
              :aria-pressed="f.meses.includes(i + 1)" @click="store.toggleMesDPV(i + 1)">{{ m }}</button>
          </div>
        </div>

        <div class="sl-acciones">
          <div class="sl-count" aria-live="polite" :title="notaEstado">
            <span class="sl-count-n">{{ fmt(k.total) }}</span>
            <span class="sl-count-l">eventos</span>
          </div>
          <button type="button" class="sl-reset" @click="store.resetFiltrosDPV()">✕ Limpiar</button>
        </div>
      </div>

      <div class="sl-fila">
        <div class="sl-grupo">
          <span class="sl-lbl">Franja</span>
          <div class="sl-btns" role="group" aria-label="Franja horaria">
            <button v-for="fr in FRANJAS" :key="fr.key" type="button" class="sl-btn"
              :class="{ active: f.franja.includes(fr.key) }" :aria-pressed="f.franja.includes(fr.key)"
              @click="store.toggleFranjaDPV(fr.key)">{{ fr.label }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Tipología</span>
          <div class="sl-btns" role="group" aria-label="Tipología">
            <button v-for="t in TIPOLOGIAS" :key="t.key" type="button" class="sl-btn"
              :class="{ active: f.tipologia.includes(t.key) }" :aria-pressed="f.tipologia.includes(t.key)"
              @click="store.toggleTipoDPV(t.key)">{{ t.label }}</button>
          </div>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Estado</span>
          <select class="sl-select" aria-label="Estado" :title="notaEstado" @change="store.setEstadoDPV($event.target.value)">
            <option value="" :selected="f.estado === ''">Cuentan para el DPV</option>
            <option :value="ESTADO_TODOS" :selected="f.estado === ESTADO_TODOS">Todos los estados</option>
            <option v-for="e in opciones.estados" :key="e" :value="e" :selected="e === f.estado">{{ e }}</option>
          </select>
        </div>

        <div class="sl-grupo">
          <span class="sl-lbl">Móvil / operador</span>
          <input type="search" class="sl-input" :value="f.busqueda" placeholder="Móvil, placa, operador o DPV…"
            aria-label="Buscar por móvil, placa, operador o número de DPV" @input="store.setBusquedaDPV($event.target.value)" />
        </div>
      </div>
    </section>

    <!-- ══ SELECCIÓN CRUZADA (chips) o ayuda ══ -->
    <div v-if="store.dpvHaySeleccion" class="sel-bar">
      <span class="sel-titulo">Filtrando por</span>
      <button v-for="c in store.dpvChips" :key="c.dim + '|' + c.key" type="button" class="sel-chip"
        :title="'Quitar ' + c.texto" @click="store.quitarSelDPV(c.dim, c.key)">
        {{ c.texto }} <span aria-hidden="true">✕</span>
      </button>
      <button type="button" class="sel-limpiar" @click="store.limpiarSelDPV()">Borrar selección</button>
    </div>
    <p v-else class="hint">
      Haz clic en un día, una hora, un segmento de la dona, una fila de las listas o un mes del DPV mensual para filtrar todo el tablero. Ctrl + clic para elegir varios.
    </p>

    <!-- ══ SIN DATOS ══ -->
    <div v-if="!store.dpvRaw.length && !store.loading" class="card vacio vacio--grande">
      <template v-if="store.dpvCompleto">
        Aún no hay eventos DPV cargados. Sube el Excel desde <router-link to="/dpv">Carga DPV</router-link>.
      </template>
      <template v-else-if="store.error">
        No se pudieron cargar los eventos. Usa «Recargar datos» para intentarlo de nuevo.
      </template>
      <template v-else>Cargando eventos…</template>
    </div>

    <template v-else>

      <!-- ══ KPIs SECUNDARIOS ══ -->
      <div class="mini-kpis">
        <div class="mini">
          <span class="mini-n">{{ fmt(k.moviles) }}</span>
          <span class="mini-l">Móviles con eventos</span>
        </div>
        <div class="mini">
          <span class="mini-n">{{ fmt(k.causas) }}</span>
          <span class="mini-l">Causas distintas</span>
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
            <div v-if="store.dpvHaySeleccion" class="kpi-sub">de {{ fmt(k.baseTotal) }} del filtro</div>
          </div>
          <div class="kpi-blk kpi-blk--pct">
            <div class="kpi-l">PORCENTAJE</div>
            <div class="kpi-n kpi-pct">{{ store.dpvCompleto ? fmtPct(store.dpvPorcentaje) + '%' : '…' }}</div>
            <div class="kpi-sub">{{ store.dpvCompleto ? 'de ' + fmt(store.dpvTotalHistorico) + ' del histórico' : 'cargando el histórico…' }}</div>
          </div>

          <div class="dona-section">
            <div class="dona-title">TIPOLOGÍA</div>
            <svg viewBox="0 0 160 140" class="dona-svg" role="img"
              :aria-label="'Tipología: ' + store.dpvDona.map(s => s.label + ' ' + s.total).join(', ')">
              <circle cx="80" cy="74" r="52" fill="none" stroke="#E5E7EB" stroke-width="28" />
              <template v-for="seg in store.dpvDona" :key="seg.key">
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
              <button v-for="seg in store.dpvDona" :key="seg.key" type="button" class="dona-item"
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

        <!-- Mapa de calor: por día / mes, o por hora del día -->
        <div class="card panel-calor" ref="calorPanel">
          <div class="calor-head">
            <div class="calor-title">No. EVENTOS POR MAPA DE CALOR</div>
            <div class="calor-ctl">
              <div class="seg" role="group" aria-label="Agrupar el mapa de calor">
                <button type="button" class="seg-btn" :class="{ active: vistaCalor === 'periodo' }"
                  :aria-pressed="vistaCalor === 'periodo'" @click="vistaCalor = 'periodo'">{{ etiquetaVistaPeriodo }}</button>
                <button type="button" class="seg-btn" :class="{ active: vistaCalor === 'hora' }"
                  :aria-pressed="vistaCalor === 'hora'" @click="vistaCalor = 'hora'">Por hora</button>
              </div>
              <span class="calor-sub">{{ periodoTxt }}</span>
            </div>
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
                      :class="{ sel: c.seleccionado, dim: haySel(dimCalor) && !c.seleccionado, fin: c.finDeSemana }"
                      :aria-pressed="c.seleccionado" :aria-label="etiquetaColumna(c)"
                      @click="clickSel(dimCalor, c.key, $event)"
                      @mouseenter="mostrarTipCalor(c, $event)" @mouseleave="ocultarTipCalor"
                      @focus="mostrarTipCalor(c, $event)" @blur="ocultarTipCalor">
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
              <span class="cl-item cl-item--nota">eventos por día (F. inmovilización)</span>
            </template>
            <template v-else>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.bajo }"></span>Bajo</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.medio }"></span>Medio</span>
              <span class="cl-item"><span class="cl-dot" :style="{ background: COLORES.alto }"></span>Alto</span>
              <span class="cl-item cl-item--nota">{{ heat.modo === 'hora' ? 'relativo a la hora con más eventos' : 'relativo al mes con más eventos' }}</span>
            </template>
          </div>

          <div v-if="tipCalor" class="tip" role="tooltip" :style="{ left: tipCalor.x + 'px', top: tipCalor.y + 'px' }">
            <div class="tip-t">{{ tipCalor.col.titulo }}</div>
            <div class="tip-v">{{ fmt(tipCalor.col.total) }} <span class="tip-u">{{ tipCalor.col.total === 1 ? 'evento' : 'eventos' }}</span></div>
            <div class="tip-n"><span class="tip-key" :style="{ background: tipCalor.col.color }"></span>{{ textoNivel(tipCalor.col.nivel) }}</div>
          </div>
        </div>
      </div>

      <!-- ══ DPV MENSUAL: km ÷ inmovilizaciones, una tarjeta por unidad ══ -->
      <section class="dm-bloque" aria-label="DPV mensual">
        <div class="dm-bloque-head">
          <h2 class="dm-bloque-t">DPV MENSUAL</h2>
          <span class="dm-bloque-s">Distancia promedio entre varadas = km del mes ÷ inmovilizaciones del mes · clic en un mes para verlo en todo el tablero · Ctrl + clic suma meses</span>
        </div>
        <p v-if="store.dpvKpiAviso" class="nota-kpi">
          ℹ El DPV mensual responde a Unidad, Año/Mes y Tipología. Franja, Estado, la búsqueda y la selección de las gráficas no lo modifican, porque los km son del mes completo.
        </p>

        <article v-for="t in tarjetas" :key="t.uf" class="card dm-card" :aria-label="'DPV mensual ' + t.nombre">
          <header class="dm-head">
            <div class="dm-id">
              <span class="dm-dot" :style="{ background: t.color }"></span>
              <div>
                <div class="dm-name">{{ t.nombre }}</div>
                <div class="dm-sub">{{ t.campo.etiqueta }} · {{ periodoTxt }}</div>
              </div>
            </div>

            <div class="dm-kpi">
              <div class="dm-valor" :class="{ 'dm-valor--nulo': t.kpi.dpv === null }">
                {{ t.kpi.dpv === null ? '—' : fmtKm(t.kpi.dpv) }} <span v-if="t.kpi.dpv !== null" class="dm-unidad">km</span>
              </div>
              <div v-if="t.kpi.delta !== null" class="dm-delta" :class="t.kpi.delta >= 0 ? 'dm-delta--sube' : 'dm-delta--baja'">
                {{ t.kpi.delta >= 0 ? '▲' : '▼' }} {{ fmtKm(absoluto(t.kpi.delta)) }} km vs mes anterior
              </div>
              <span v-if="t.kpi.nivel" class="dm-nivel" :class="'dm-nivel--' + t.kpi.nivel">{{ NIVEL[t.kpi.nivel].icono }} {{ NIVEL[t.kpi.nivel].texto }}</span>
              <span v-else class="dm-nivel dm-nivel--nulo">Sin dato</span>
            </div>

            <button v-if="t.datos.length" type="button" class="btn-vista" :aria-pressed="vistaTabla[t.uf]" @click="alternarVista(t.uf)">
              {{ vistaTabla[t.uf] ? 'Ver gráfico' : 'Ver tabla' }}
            </button>
          </header>

          <p v-if="t.kpi.km !== null" class="dm-meta">
            {{ fmtKm(t.kpi.km) }} km ÷ {{ fmt(t.kpi.inm) }} {{ t.kpi.inm === 1 ? 'inmovilización' : 'inmovilizaciones' }}<template v-if="t.kpi.meses > 1"> · {{ t.kpi.meses }} meses acumulados</template>
          </p>
          <p v-if="t.aviso" class="dm-aviso" :class="'dm-aviso--' + t.aviso.tipo">
            {{ t.aviso.texto }} <router-link v-if="t.aviso.enlace" to="/dpv">Ir a Carga DPV</router-link>
          </p>

          <div v-if="!t.datos.length" class="vacio">
            Aún no hay DPV mensual para {{ t.nombre }}. Sube el Excel con la hoja de km desde <router-link to="/dpv">Carga DPV</router-link>.
          </div>

          <template v-else>
            <div class="dm-leyenda">
              <span class="lg"><span class="lg-linea" :style="{ background: t.color }"></span>{{ t.campo.etiqueta }}</span>
              <span class="lg"><span class="lg-ref lg-ref--ok"></span>Estándar {{ fmtKm(umbrales.estandar) }} km</span>
              <span class="lg"><span class="lg-ref lg-ref--critico"></span>Crítico {{ fmtKm(umbrales.critico) }} km</span>
              <span v-for="n in NIVELES_LEYENDA" :key="n" class="lg">
                <svg class="lg-marker" viewBox="-8 -8 16 16" aria-hidden="true" focusable="false">
                  <circle v-if="n === 'cumple'" class="mk" r="5.2" :fill="NIVEL.cumple.color"></circle>
                  <rect v-else-if="n === 'alerta'" class="mk" x="-4.6" y="-4.6" width="9.2" height="9.2" transform="rotate(45)" :fill="NIVEL.alerta.color"></rect>
                  <polygon v-else class="mk" points="0,-6.4 6.2,4.8 -6.2,4.8" :fill="NIVEL.critico.color"></polygon>
                </svg>
                {{ NIVEL[n].corto }}
              </span>
              <span v-if="t.haySinKm" class="lg">
                <svg class="lg-marker" viewBox="-8 -8 16 16" aria-hidden="true" focusable="false">
                  <circle class="mk-vacio" r="4.2"></circle>
                </svg>
                Sin km cargados
              </span>
            </div>

            <!-- Gráfico -->
            <div v-if="!vistaTabla[t.uf]" class="dm-chart">
              <div class="dm-eje" aria-hidden="true">
                <span v-for="tk in t.geo.ticks" :key="tk.valor" class="dm-tick" :style="{ top: tk.y + 'px' }">{{ tk.label }}</span>
              </div>
              <div class="dm-scroll">
                <div class="dm-lienzo" :style="{ minWidth: t.geo.n * ANCHO_MES_PX + 'px' }">
                  <div class="dm-refs" aria-hidden="true">
                    <span class="dm-ref-lbl dm-ref-lbl--ok" :style="{ top: (t.geo.yEstandar - 16) + 'px' }">Estándar {{ fmtKm(umbrales.estandar) }}</span>
                    <span class="dm-ref-lbl dm-ref-lbl--critico" :style="{ top: (t.geo.yCritico + 2) + 'px' }">Crítico {{ fmtKm(umbrales.critico) }}</span>
                  </div>
                  <svg class="dm-svg" viewBox="0 0 1000 190" preserveAspectRatio="none" aria-hidden="true" focusable="false">
                    <line v-for="tk in t.geo.ticks" :key="'g' + tk.valor" class="dm-grid" x1="0" x2="1000" :y1="tk.y" :y2="tk.y"></line>
                    <line class="dm-ref dm-ref--ok" x1="0" x2="1000" :y1="t.geo.yEstandar" :y2="t.geo.yEstandar"></line>
                    <line class="dm-ref dm-ref--critico" x1="0" x2="1000" :y1="t.geo.yCritico" :y2="t.geo.yCritico"></line>
                    <path v-for="(a, i) in t.geo.areas" :key="'a' + i" class="dm-area" :d="a" :fill="t.color"></path>
                    <path v-for="(l, i) in t.geo.lineas" :key="'l' + i" class="dm-linea" :d="l" :stroke="t.color"></path>
                  </svg>
                  <button v-for="p in t.puntos" :key="p.mes" type="button" class="dm-col"
                    :class="{ en: periodoActivo && p.enPeriodo }" :style="estiloCol(t, p)" :aria-label="etiquetaMes(t, p)"
                    @click="irAMes(p.mes, $event)"
                    @mouseenter="mostrarTipMes(t, p, $event)" @mouseleave="ocultarTipMes"
                    @focus="mostrarTipMes(t, p, $event)" @blur="ocultarTipMes">
                    <svg v-if="p.valor !== null" class="dm-marker" viewBox="-8 -8 16 16" aria-hidden="true" focusable="false"
                      :style="{ top: p.y + 'px' }">
                      <circle v-if="p.nivel === 'cumple'" class="mk" r="5.2" :fill="NIVEL.cumple.color"></circle>
                      <rect v-else-if="p.nivel === 'alerta'" class="mk" x="-4.6" y="-4.6" width="9.2" height="9.2" transform="rotate(45)" :fill="NIVEL.alerta.color"></rect>
                      <polygon v-else class="mk" points="0,-6.4 6.2,4.8 -6.2,4.8" :fill="NIVEL.critico.color"></polygon>
                    </svg>
                    <svg v-else class="dm-marker dm-marker--vacio" viewBox="-8 -8 16 16" aria-hidden="true" focusable="false"
                      :style="{ top: (t.geo.base - 9) + 'px' }">
                      <circle class="mk-vacio" r="4.2"></circle>
                    </svg>
                    <span v-if="p.valor !== null && t.etiquetados.includes(p.i)" class="dm-val" :style="{ top: (p.y - 22) + 'px' }">{{ fmtKm(p.valor) }}</span>
                    <span class="dm-mes">{{ p.label }}</span>
                  </button>
                </div>
              </div>

              <div v-if="tipMes && tipMes.uf === t.uf" class="tip" :class="{ 'tip--abajo': tipMes.abajo }" role="tooltip"
                :style="{ left: tipMes.x + 'px', top: tipMes.y + 'px' }">
                <div class="tip-t">{{ tipMes.d.titulo }}</div>
                <div class="tip-v">{{ tipMes.d.valor }} <span class="tip-u">{{ tipMes.d.unidad }}</span></div>
                <div v-for="(l, i) in tipMes.d.lineas" :key="i" class="tip-r">{{ l }}</div>
                <div v-if="tipMes.d.nivel" class="tip-n"><span class="tip-key" :style="{ background: tipMes.d.nivelColor }"></span>{{ tipMes.d.icono }} {{ tipMes.d.nivel }}</div>
              </div>
            </div>

            <!-- Tabla equivalente del gráfico (accesible y para copiar cifras) -->
            <div v-else class="dm-tabla-wrap">
              <table class="mt dm-tabla">
                <thead>
                  <tr>
                    <th><span class="th-txt">MES</span></th>
                    <th class="th-r"><span class="th-txt">KM</span></th>
                    <th class="th-r"><span class="th-txt">INMOVILIZACIONES</span></th>
                    <th class="th-r"><span class="th-txt">{{ t.campo.etiqueta.toUpperCase() }}</span></th>
                    <th><span class="th-txt">NIVEL</span></th>
                    <th><span class="th-txt">ORIGEN DE LOS KM</span></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in t.filas" :key="p.mes" class="fila" :class="{ 'fila--periodo': periodoActivo && p.enPeriodo }"
                    tabindex="0" @click="irAMes(p.mes, $event)" @keydown.enter.prevent="irAMes(p.mes, $event)">
                    <td class="td-mes">{{ tituloMes(p.mes) }}</td>
                    <td class="td-num">{{ kmDe(t, p) }}</td>
                    <td class="td-num">{{ inmDe(t, p) }}</td>
                    <td class="td-num td-dpv">{{ p.valor === null ? '—' : fmtKm(p.valor) }}</td>
                    <td>
                      <span v-if="p.nivel" class="dm-nivel dm-nivel--chico" :class="'dm-nivel--' + p.nivel">{{ NIVEL[p.nivel].icono }} {{ NIVEL[p.nivel].corto }}</span>
                      <span v-else class="muted">Sin km</span>
                    </td>
                    <td class="td-origen">{{ ORIGEN_KM[p.m.origen] || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </article>
      </section>

      <!-- ══ FILA INFERIOR: rankings + detalle ══ -->
      <div class="bottom-row">

        <div class="left-col">
          <div v-for="p in paneles" :key="p.dim" class="card rank-card">
            <div class="tabla-hdr tabla-hdr--flex">
              <span>{{ p.titulo }}</span>
              <span class="tabla-badge">{{ fmt(p.filas.length) }}</span>
            </div>
            <div class="rank-cab"><span>{{ p.col }}</span><span></span><span class="r">EVENTOS</span></div>
            <div class="rank-lista">
              <div v-if="!p.filas.length" class="vacio">Sin datos</div>
              <button v-for="r in p.filas" :key="r.key" type="button" class="rank-row"
                :class="{ sel: r.seleccionado, dim: haySel(p.dim) && !r.seleccionado }" :aria-pressed="r.seleccionado"
                :title="r.label + ': ' + r.total + ' eventos (' + r.pct + '%)'"
                @click="clickSel(p.dim, r.key, $event)">
                <span class="rank-lbl" :class="{ mono: p.mono }">{{ r.label }}</span>
                <span class="rank-track"><span class="rank-fill" :style="{ width: anchoBarra(r, p.filas) + '%' }"></span></span>
                <span class="rank-n">{{ fmt(r.total) }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="card detalle-card">
          <div class="tabla-hdr tabla-hdr--flex">
            <span>DETALLE DE EVENTOS</span>
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
                <template v-for="r in visibles" :key="r.id">
                  <tr class="fila" :class="{ abierta: expandido === r.id }" tabindex="0"
                    :aria-expanded="expandido === r.id"
                    @click="alternarFila(r)" @keydown.enter.prevent="alternarFila(r)">
                    <td class="td-id">{{ r.dpv_id }}</td>
                    <td class="td-movil">{{ r.movil || r.placa }}</td>
                    <td class="td-causa">{{ r.causa_inmovilizacion || '—' }}</td>
                    <td class="td-ruta">{{ r.ruta || '—' }}</td>
                    <td>
                      <span class="badge" :class="claseEstado(r.estado)"
                        :title="r.cuenta ? 'Cuenta como inmovilización' : 'No cuenta para el DPV'">{{ r.estado || '—' }}</span>
                    </td>
                    <td class="td-fecha">{{ fechaCorta(r.fecha) }} <span class="td-hora">{{ horaCorta(r.hora) }}</span></td>
                    <td class="td-dias">
                      <span v-if="dias(r) !== null" class="dias-chip" :class="claseDias(dias(r))">{{ dias(r) === 0 ? 'Hoy' : dias(r) + ' d' }}</span>
                      <span v-else class="muted">—</span>
                    </td>
                    <td class="td-desc" :title="r.descripcion">{{ r.descripcion }}</td>
                  </tr>
                  <tr v-if="expandido === r.id" class="fila-detalle">
                    <td :colspan="COLUMNAS.length">
                      <p class="det-desc">{{ r.descripcion || 'Sin descripción' }}</p>
                      <dl class="det-meta">
                        <div><dt>Empresa</dt><dd>{{ r.empresa || '—' }}</dd></div>
                        <div><dt>Placa</dt><dd>{{ r.placa || '—' }}</dd></div>
                        <div><dt>Tipología</dt><dd>{{ etiquetaTipologia(r.tipologia) || '—' }}</dd></div>
                        <div><dt>Operador</dt><dd>{{ r.operador || '—' }}</dd></div>
                        <div><dt>Día</dt><dd>{{ r.dia_semana || '—' }} · {{ r.franja || '—' }}</dd></div>
                        <div><dt>F. inicio DPV</dt><dd>{{ fechaCorta(r.fecha_inicio) }}</dd></div>
                        <div><dt>F. cierre DPV</dt><dd>{{ fechaCorta(r.fecha_cierre) }}</dd></div>
                        <div><dt>Alerta</dt><dd>{{ r.alerta || '—' }}</dd></div>
                        <div><dt>¿Cuenta para el DPV?</dt><dd>{{ r.cuenta ? 'Sí' : 'No' }}</dd></div>
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
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useDashboardStore } from './dashboardStore.js'
import {
  UNIDADES, NIVEL, ESTADO_TODOS, ESTADO_DESCARTADO, ORIGEN_KM, ANCHO_MES_PX,
  MESES_CORTOS, HEAT_COLORES, HEAT_DIA,
  diasParaResponder, hoyISO, ordenar, csvDPV, claseEstado, etiquetaTipologia, sinTildes,
  tituloPeriodo as tituloPeriodoDe, tituloMes, fmtKm, detalleMes, avisoDpv, altoTooltipMes, tooltipAbajo, desplazamientoParaVer,
} from './dpvUtils.js'

const store = useDashboardStore()

// ── Constantes de la vista ──
const FRANJAS    = [{ key: 'AM', label: 'A. M.' }, { key: 'PM', label: 'P. M.' }]
const TIPOLOGIAS = [{ key: 'BUSETON', label: 'BUSETON' }, { key: 'PADRON', label: 'PADRÓN' }]
const NIVELES_LEYENDA = ['cumple', 'alerta', 'critico']
const COLORES    = HEAT_COLORES
const PAGINA     = 100   // filas que se agregan cada vez en el detalle
// Los datos secundarios (empresa, operador, F. inicio / cierre, alerta…) se ven al expandir la fila y van en el CSV:
// así la descripción cabe sin scroll horizontal
const COLUMNAS = [
  { key: 'dpv_id',               label: 'DPV',                cls: '' },
  { key: 'movil',                label: 'MÓVIL',              cls: '' },
  { key: 'causa_inmovilizacion', label: 'CAUSA',              cls: '' },
  { key: 'ruta',                 label: 'RUTA',               cls: '' },
  { key: 'estado',               label: 'ESTADO',             cls: '' },
  { key: 'fh',                   label: 'FECHA Y HORA',       cls: '' },
  { key: 'dias',                 label: 'DÍAS P/ RESPONDER',  cls: 'th-r' },
  { key: 'descripcion',          label: 'DESCRIPCIÓN',        cls: 'th-desc' },
]
const DIR_INICIAL = { dpv_id: 'desc', fh: 'desc', dias: 'asc' }
const hoy = hoyISO()

// ── Estado derivado del store ──
const f        = computed(() => store.dpvFiltros)
const k        = computed(() => store.dpvKPIs)
const opciones = computed(() => store.dpvOpciones)
const umbrales = computed(() => store.dpvUmbrales)
const periodoTxt = computed(() => tituloPeriodoDe(store.dpvFiltros))
const periodoActivo = computed(() => !!store.dpvFiltros.anio)   // sin año = todo el histórico: no hay nada que resaltar
const notaEstado = computed(() => {
  const lista = store.dpvEstadosDescartados.length ? store.dpvEstadosDescartados : [ESTADO_DESCARTADO]
  return `Un evento cuenta como inmovilización salvo que su estado sea: ${lista.join(', ')}`
})

// Una tarjeta por unidad visible + lo que la vista necesita de cada una (aviso, filas de la tabla)
const tarjetas = computed(() => store.dpvTarjetas.map(t => ({
  ...t,
  aviso: avisoDpv(t.kpi),
  haySinKm: t.puntos.some(p => p.valor === null),               // ¿algún mes sin km? (entonces la leyenda explica el marcador vacío)
  filas: [...t.puntos].reverse(),                               // tabla: del mes más reciente al más antiguo
})))

const paneles = computed(() => [
  { dim: 'causa',    titulo: 'CAUSAS DE INMOVILIZACIÓN',   col: 'CAUSA',    filas: store.dpvCausas,    mono: false },
  { dim: 'ruta',     titulo: 'No. EVENTOS POR RUTA',       col: 'RUTA',     filas: store.dpvRutas,     mono: false },
  { dim: 'movil',    titulo: 'No. EVENTOS POR MÓVIL',      col: 'MÓVIL',    filas: store.dpvMoviles,   mono: true },
  { dim: 'operador', titulo: 'No. EVENTOS POR OPERADOR',   col: 'OPERADOR', filas: store.dpvOperadores, mono: false },
])

// ── Helpers de presentación ──
const fmt = n => Number(n || 0).toLocaleString('es-CO')
const fmtPct = n => Number(n || 0).toLocaleString('es-CO', { maximumFractionDigits: 1 })
const absoluto = n => Math.abs(n)
const fechaCorta = iso => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : '—')
const horaCorta = h => (h || '').slice(0, 5)
const mesDisponible = m => !!f.value.anio && (opciones.value.mesesPorAnio[f.value.anio] || []).includes(m)
const haySel = dim => store.dpvSel[dim].length > 0
const segOpacidad = seg => (haySel('tipologia') && !seg.seleccionado ? 0.35 : 1)
const anchoBarra = (r, filasPanel) => Math.max(2, Math.round((r.total / ((filasPanel[0] && filasPanel[0].total) || 1)) * 100))
const textoNivel = n => ({ bajo: 'Nivel bajo', medio: 'Nivel medio', alto: 'Nivel alto', vacio: 'Sin eventos' })[n]
const etiquetaColumna = c => `${c.titulo}: ${c.total} eventos`

// Clic en una visual → selección cruzada (Ctrl / ⌘ / Shift suma elementos)
const conTecla = ev => !!(ev && (ev.ctrlKey || ev.metaKey || ev.shiftKey))
function clickSel(dim, key, ev) {
  store.toggleSelDPV(dim, key, conTecla(ev))
}

// ── Mapa de calor: por día / mes o por hora del día ──
const vistaCalor = ref('periodo')   // 'periodo' | 'hora'
const heat = computed(() => (vistaCalor.value === 'hora' ? store.dpvHoras : store.dpvHeatmap))
const dimCalor = computed(() => (vistaCalor.value === 'hora' ? 'hora' : 'periodos'))
const etiquetaVistaPeriodo = computed(() => (store.dpvHeatmap.modo === 'dia' ? 'Por día' : 'Por mes'))
const mostrarNumeros = computed(() => heat.value.columnas.length <= 31)
// La altura de la gráfica es fluida (se adapta a la tarjeta), por eso las barras son un % del máximo
const estiloBarra = c => ({
  height: (c.total ? (c.total / Math.max(1, heat.value.max)) * 100 : 0) + '%',
  minHeight: c.total ? '3px' : '2px',
  background: c.color,
})
const anchoMinimoHeat = computed(() => {
  const porColumna = { dia: 24, mes: 44, hora: 28 }[heat.value.modo] || 14
  return heat.value.columnas.length * porColumna
})
// Con ~60 columnas mensuales no caben todas las etiquetas: se muestra una de cada tres (Ene, Abr, Jul, Oct)
const etiquetaCol = c => (heat.value.modo === 'anio-mes' && (Number(c.key.slice(5, 7)) - 1) % 3 !== 0 ? '' : c.label)

// Tooltip propio (también con foco de teclado), anclado a la barra: valor en grande, etiqueta debajo
const calorPanel = ref(null)
const tipCalor = ref(null)
const TIP_ALTO_CALOR = 100   // alto aprox. del tooltip + margen: si la barra llega muy arriba, se baja para no salirse de la tarjeta
function mostrarTipCalor(c, ev) {
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
  tipCalor.value = { x, y: Math.max(arriba, TIP_ALTO_CALOR), col: c }
}
const ocultarTipCalor = () => { tipCalor.value = null }
watch(heat, ocultarTipCalor)

// ── DPV mensual: una tarjeta por unidad ──
const vistaTabla = reactive({ UF10: false, UF16: false })   // true = la tarjeta muestra la tabla en vez del gráfico
const raiz = ref(null)
const tipMes = ref(null)

const estiloCol = (t, p) => ({ left: (p.i / t.geo.n) * 100 + '%', width: 100 / t.geo.n + '%' })
const kmDe = (t, p) => (p.m[t.campo.km] > 0 ? fmtKm(p.m[t.campo.km]) : '—')
const inmDe = (t, p) => (p.m[t.campo.inm] == null ? '—' : fmt(p.m[t.campo.inm]))
function etiquetaMes(t, p) {
  const dato = p.valor === null ? 'sin km cargados' : `DPV ${fmtKm(p.valor)} km, ${NIVEL[p.nivel].texto}`
  return `${tituloMes(p.mes)}: ${dato}${periodoActivo.value && p.enPeriodo ? ' (en el periodo elegido)' : ''}`
}

// Clic en un mes: el tablero pasa a ese mes (otro clic en el único mes elegido: todo el año). Ctrl / ⌘ / Shift suma meses.
function irAMes(mes, ev) {
  store.irAMesDPV(mes, conTecla(ev))
}

function mostrarTipMes(t, p, ev) {
  const el = ev && ev.currentTarget
  const grafico = el && el.closest('.dm-chart')
  if (!grafico) return
  const gr = grafico.getBoundingClientRect()
  const er = el.getBoundingClientRect()
  const xCol = er.left - gr.left + er.width / 2                  // centro de la columna dentro del gráfico
  const y = p.y === null ? t.geo.base - 9 : p.y
  const d = detalleMes(p, t.campo)
  // encima del punto, o debajo si encima no cabe y debajo sí (así no se sale de la tarjeta ni tapa el punto)
  tipMes.value = { uf: t.uf, x: xCol, xCol, y, abajo: tooltipAbajo(y, altoTooltipMes(d)), d }
  nextTick(ajustarTipMes)
}
// Con el tooltip ya dibujado se mide su ancho real y se corre hacia dentro si se saldría del gráfico (primer y último mes)
function ajustarTipMes() {
  const tip = raiz.value && raiz.value.querySelector('.dm-chart .tip')
  if (!tip || !tipMes.value) return
  const mitad = tip.offsetWidth / 2
  const ancho = tip.parentElement.clientWidth
  const x = Math.min(Math.max(tipMes.value.xCol, mitad), Math.max(mitad, ancho - mitad))
  if (Math.abs(x - tipMes.value.x) > 0.5) tipMes.value = { ...tipMes.value, x }
}
const ocultarTipMes = () => { tipMes.value = null }
watch(() => store.dpvTarjetas, ocultarTipMes)

// El gráfico se abre mostrando el periodo elegido o, si no hay periodo (todo el histórico), el mes más reciente: cuando hay más
// meses de los que caben, se desplaza por dentro de su tarjeta.
function scrollAlFinal() {
  const r = raiz.value
  if (!r) return
  for (const el of r.querySelectorAll('.dm-scroll')) el.scrollLeft = el.scrollWidth
}
// Trae a la vista el periodo elegido si el gráfico lo deja fuera (celular, o más meses de los que caben). Si ya se ve completo no
// mueve nada: un clic sobre un mes visible no hace saltar el gráfico.
function verPeriodo() {
  const r = raiz.value
  if (!r) return
  for (const sc of r.querySelectorAll('.dm-scroll')) {
    const cols = [...sc.querySelectorAll('.dm-col.en')]
    if (!cols.length) continue
    const x = desplazamientoParaVer(
      Math.min(...cols.map(c => c.offsetLeft)),
      Math.max(...cols.map(c => c.offsetLeft + c.offsetWidth)),
      sc.scrollLeft, sc.clientWidth)
    if (x !== null) sc.scrollLeft = x
  }
}
function acomodarGrafico() {
  scrollAlFinal()
  verPeriodo()
}
function alternarVista(uf) {
  vistaTabla[uf] = !vistaTabla[uf]
  ocultarTipMes()
  nextTick(acomodarGrafico)
}
onMounted(() => nextTick(acomodarGrafico))
// ...y también cuando aparecen o cambian las tarjetas: llegan los primeros eventos (antes solo se veía «Cargando»), llegan los
// meses, se agrega o quita una unidad. Sin esto un gráfico recién dibujado se quedaría en el mes más antiguo.
watch(() => store.dpvTarjetas.map(t => t.uf + ':' + t.datos.length).join('|') + '|' + (store.dpvRaw.length > 0),
  () => nextTick(acomodarGrafico))
// Al elegir otro periodo con los botones de arriba, el gráfico lo muestra aunque estuviera desplazado a otro lado
watch(() => store.dpvFiltros.anio + '|' + store.dpvFiltros.meses.join(','), () => nextTick(verPeriodo))

// ── Tabla de detalle: orden, paginación, fila expandida, CSV ──
const orden     = ref({ key: 'fh', dir: 'desc' })
const limite    = ref(PAGINA)
const expandido = ref(null)
const filas     = computed(() => ordenar(store.dpvFiltrado, orden.value.key, orden.value.dir, hoy))
const visibles  = computed(() => filas.value.slice(0, limite.value))
watch(() => store.dpvFiltrado, () => { limite.value = PAGINA; expandido.value = null })

function ordenarPor(key) {
  orden.value = orden.value.key === key
    ? { key, dir: orden.value.dir === 'asc' ? 'desc' : 'asc' }
    : { key, dir: DIR_INICIAL[key] || 'asc' }
  limite.value = PAGINA
}
const ariaSort = key => (orden.value.key !== key ? 'none' : orden.value.dir === 'asc' ? 'ascending' : 'descending')
const flecha   = key => (orden.value.key !== key ? '' : orden.value.dir === 'asc' ? ' ▲' : ' ▼')
const mostrarMas  = () => { limite.value += PAGINA }
const alternarFila = r => { expandido.value = expandido.value === r.id ? null : r.id }
const dias      = r => diasParaResponder(r, hoy)
const claseDias = d => (d <= 1 ? 'dias-urgente' : d <= 3 ? 'dias-pronto' : 'dias-ok')

function exportarCSV() {
  const blob = new Blob(['﻿' + csvDPV(filas.value)], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `DPV_${sinTildes(periodoTxt.value).replace(/[^A-Za-z0-9]+/g, '_')}_${hoy}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.dpv-root { display: flex; flex-direction: column; gap: 14px; min-width: 0; transition: opacity .15s; }
.dpv-root.recargando { opacity: .6; pointer-events: none; }   /* al recargar se conserva el marco, sin saltos */

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
/* Mismos colores por unidad que en el gráfico de DPV mensual y en el tablero ICO */
.sl-btn--uf10.active { background: #074e7a; border-color: #074e7a; }
.sl-btn--uf16.active { background: #1f7a6e; border-color: #1f7a6e; }
.sl-btn:disabled { opacity: .4; cursor: not-allowed; }
.sl-btn--mes { padding: 4px 7px; min-width: 38px; font-size: 11.5px; }
.sl-select, .sl-input {
  padding: 5px 9px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 12px;
  color: var(--text); background: var(--surface-2); font-family: inherit;
}
.sl-select { cursor: pointer; }
.sl-input { min-width: 210px; }
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
.kpi-blk--pct { background: var(--teal-light); border-color: var(--teal); }
.kpi-l { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 2px; }
.kpi-blk--pct .kpi-l, .kpi-blk--pct .kpi-sub { color: #3b5249; }   /* sobre el fondo teal claro el gris de apoyo se oscurece para mantener contraste AA */
.kpi-n { font-size: 36px; font-weight: 800; color: var(--primary); line-height: 1.05; }
.kpi-pct { color: #1a6a5f; }   /* el teal de la marca sobre su propio fondo claro da 3,6:1; este da 5,4:1 */
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
.dona-item.sel, .rank-row.sel, .calor-col.sel, .dm-col.en, .fila--periodo { --text-muted: #46594f; }
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
.calor-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px 12px; }
.calor-title { font-size: 12px; font-weight: 800; color: var(--text); text-transform: uppercase; letter-spacing: .4px; }
.calor-ctl { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 12px; }
.calor-sub { font-size: 11.5px; color: var(--text-muted); }
.seg { display: inline-flex; border: 1.5px solid var(--border); border-radius: 6px; overflow: hidden; background: var(--surface-2); }
.seg-btn {
  padding: 3px 11px; border: 0; background: transparent; color: var(--text-muted);
  font-size: 11px; font-weight: 700; cursor: pointer;
}
.seg-btn + .seg-btn { border-left: 1.5px solid var(--border); }
.seg-btn:hover:not(.active) { background: var(--primary-light); color: var(--primary); }
.seg-btn.active { background: var(--primary); color: #fff; }
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
  position: absolute; z-index: 5; width: max-content; min-width: 128px; max-width: 270px; padding: 8px 11px; border-radius: 8px; pointer-events: none;
  transform: translate(-50%, calc(-100% - 8px)); background: var(--text); color: #fff; box-shadow: var(--shadow-md);
}
.tip--abajo { transform: translate(-50%, 14px); }
.tip-t { font-size: 10.5px; color: rgba(255, 255, 255, .72); }
.tip-v { font-size: 16px; font-weight: 800; line-height: 1.25; }
.tip-u { font-size: 11px; font-weight: 600; color: rgba(255, 255, 255, .8); }
.tip-r { font-size: 11px; color: rgba(255, 255, 255, .85); }
.tip-n { display: flex; align-items: center; gap: 6px; margin-top: 3px; font-size: 10.5px; color: rgba(255, 255, 255, .8); }
.tip-key { width: 12px; height: 3px; border-radius: 2px; flex-shrink: 0; }

/* ── DPV mensual ── */
.dm-bloque { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.dm-bloque-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 14px; padding: 0 4px; }
.dm-bloque-t { font-size: 12px; font-weight: 800; color: var(--text); text-transform: uppercase; letter-spacing: .4px; }
.dm-bloque-s { font-size: 11.5px; color: var(--text-muted); }
.nota-kpi {
  font-size: 11.5px; line-height: 1.4; padding: 7px 12px; border-radius: 8px;
  background: var(--secondary-light); color: var(--secondary);   /* azul sobre azul claro: 7,4:1 */
}

.dm-card { padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.dm-head { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 22px; }
.dm-id { display: flex; align-items: center; gap: 10px; min-width: 170px; }
.dm-dot { width: 12px; height: 12px; border-radius: 50%; flex: none; }
.dm-name { font-size: 14px; font-weight: 800; color: var(--text); letter-spacing: .2px; }
.dm-sub { font-size: 11px; color: var(--text-muted); }
.dm-kpi { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 14px; }
.dm-valor { font-size: 28px; font-weight: 800; color: var(--primary); line-height: 1; font-variant-numeric: tabular-nums; }
.dm-valor--nulo { color: var(--text-muted); }
.dm-unidad { font-size: 13px; font-weight: 700; color: var(--text-muted); }
.dm-delta { font-size: 11.5px; font-weight: 700; font-variant-numeric: tabular-nums; }
.dm-delta--sube { color: #17794f; }    /* más km entre varadas = mejor */
.dm-delta--baja { color: var(--danger); }
.dm-nivel {
  display: inline-flex; align-items: center; gap: 5px; padding: 3px 11px; border-radius: 999px;
  font-size: 11px; font-weight: 800; white-space: nowrap;
}
.dm-nivel--cumple  { background: var(--accent-light);  color: var(--primary); }
.dm-nivel--alerta  { background: var(--warning-light); color: #8a4b05; }
.dm-nivel--critico { background: var(--danger-light);  color: var(--danger); }
.dm-nivel--nulo    { background: var(--bg); color: var(--text-muted); }
.dm-nivel--chico   { padding: 1px 8px; font-size: 10.5px; }
.btn-vista {
  margin-left: auto; padding: 4px 12px; border: 1.5px solid var(--accent); border-radius: 6px;
  background: var(--surface); color: var(--primary); font-size: 11.5px; font-weight: 700; cursor: pointer;
}
.btn-vista:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
.dm-meta { font-size: 11.5px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.dm-aviso { font-size: 11.5px; line-height: 1.4; padding: 6px 10px; border-radius: 8px; background: var(--warning-light); color: #8a4b05; }
.dm-aviso a { color: var(--primary); font-weight: 700; text-decoration: underline; margin-left: 4px; }

.dm-leyenda { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 16px; font-size: 11px; color: var(--text); }
.lg { display: inline-flex; align-items: center; gap: 6px; }
.lg-linea { width: 18px; height: 3px; border-radius: 2px; flex: none; }
.lg-ref { width: 18px; height: 0; border-top: 2px dashed; flex: none; }
.lg-ref--ok { border-color: #17794f; }
.lg-ref--critico { border-top-style: dotted; border-top-width: 3px; border-color: var(--danger); }
.lg-marker { width: 12px; height: 12px; flex: none; overflow: visible; }

/* Gráfico: el eje Y queda fijo y los meses se desplazan en horizontal solo si no caben (38 px mínimos por mes) */
.dm-chart { position: relative; display: flex; }
.dm-eje { position: relative; flex: none; width: 46px; height: 190px; }
.dm-tick {
  position: absolute; right: 6px; transform: translateY(-50%); white-space: nowrap;
  font-size: 10px; color: var(--text-muted); font-variant-numeric: tabular-nums;
}
.dm-scroll { flex: 1 1 auto; min-width: 0; overflow-x: auto; overflow-y: hidden; }
.dm-lienzo { position: relative; min-width: 100%; height: 190px; }
.dm-svg { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.dm-grid { stroke: var(--border); stroke-width: 1; vector-effect: non-scaling-stroke; }
.dm-ref { fill: none; stroke-width: 1.6; vector-effect: non-scaling-stroke; }
.dm-ref--ok { stroke: #17794f; stroke-dasharray: 7 4; }
.dm-ref--critico { stroke: var(--danger); stroke-dasharray: 2 4; stroke-linecap: round; }
.dm-area { stroke: none; fill-opacity: .1; }
.dm-linea { fill: none; stroke-width: 2.4; stroke-linejoin: round; stroke-linecap: round; vector-effect: non-scaling-stroke; }

/* Etiquetas de las líneas de referencia: se quedan pegadas al borde izquierdo aunque se desplace el gráfico */
.dm-refs { position: sticky; left: 0; z-index: 3; width: 0; height: 0; overflow: visible; }
.dm-ref-lbl {
  position: absolute; left: 6px; padding: 0 5px; border-radius: 4px; pointer-events: none; white-space: nowrap;
  font-size: 10px; font-weight: 800; line-height: 14px; background: rgba(255, 255, 255, .9);
}
.dm-ref-lbl--ok { color: #17794f; }
.dm-ref-lbl--critico { color: var(--danger); }

.dm-col {
  position: absolute; top: 0; bottom: 0; padding: 0; border: 0; border-radius: 6px;
  background: transparent; cursor: pointer; color: inherit; font: inherit;
}
.dm-col.en { background: rgba(49, 176, 121, .14); }
.dm-col:hover, .dm-col:focus-visible { background: rgba(8, 69, 52, .08); }
.dm-col.en:hover, .dm-col.en:focus-visible { background: rgba(49, 176, 121, .26); }
.dm-col:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.dm-marker {
  position: absolute; left: 50%; width: 16px; height: 16px; transform: translate(-50%, -50%);
  overflow: visible; pointer-events: none; filter: drop-shadow(0 0 1.5px #fff) drop-shadow(0 0 1px #fff);
}
.mk { stroke: var(--text); stroke-width: 1.3; }
.mk-vacio { fill: var(--surface); stroke: var(--text-muted); stroke-width: 1.4; stroke-dasharray: 2 2; }
.dm-val {
  position: absolute; left: 50%; transform: translateX(-50%); pointer-events: none; white-space: nowrap;
  font-size: 10.5px; font-weight: 800; color: var(--text); font-variant-numeric: tabular-nums;
  text-shadow: 0 0 3px #fff, 0 0 3px #fff, 0 0 2px #fff;
}
.dm-mes {
  position: absolute; left: 0; right: 0; bottom: 6px; text-align: center; pointer-events: none; white-space: nowrap;
  font-size: 10.5px; font-weight: 600; color: var(--text-muted);
}
.dm-col.en .dm-mes { color: var(--primary); font-weight: 800; }

.dm-tabla-wrap { max-height: 340px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; }
.dm-tabla .th-txt { display: block; padding: 6px 8px; font-size: 9.5px; font-weight: 700; color: var(--primary); }
.dm-tabla .th-r { text-align: right; }
.td-mes { font-weight: 700; white-space: nowrap; }
.td-num { text-align: right; font-variant-numeric: tabular-nums; }
.td-dpv { font-weight: 800; color: var(--primary); }
.td-origen { font-size: 10.5px; color: var(--text-muted); }
.fila--periodo td { background: var(--accent-light); }

/* ── Fila inferior ── */
.bottom-row { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 14px; align-items: start; }
.left-col { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.rank-card { overflow: hidden; }
.tabla-hdr { background: var(--primary); color: #fff; font-size: 10px; font-weight: 700; padding: 8px 12px; text-transform: uppercase; letter-spacing: .4px; }
.rank-cab, .rank-row { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) 40px; gap: 8px; align-items: center; }
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
.rank-lbl { font-size: 11.5px; font-weight: 700; line-height: 1.25; overflow-wrap: anywhere; }   /* las etiquetas largas se parten en 2 líneas en vez de cortarse */
.rank-lbl.mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
.rank-track { height: 8px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.rank-fill { display: block; height: 100%; background: var(--accent); border-radius: 0 4px 4px 0; transition: width .3s; }
.rank-n { text-align: right; font-size: 12px; font-weight: 800; color: var(--primary); font-variant-numeric: tabular-nums; }

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
.td-causa { min-width: 120px; max-width: 220px; font-size: 11px; line-height: 1.3; }
.td-ruta { white-space: nowrap; font-size: 11px; }
.td-fecha { white-space: nowrap; font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.td-hora { color: var(--text); font-weight: 700; }
.td-dias { text-align: right; white-space: nowrap; }
/* La descripción ocupa el espacio que sobra y se corta con «…» (el texto completo está en el tooltip y al expandir la fila) */
.th-desc { width: 100%; min-width: 130px; }
.td-desc { width: 100%; max-width: 0; min-width: 130px; font-size: 10.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
  .dm-card { padding: 12px; }
  .dm-id { min-width: 0; width: 100%; }
  .btn-vista { margin-left: 0; }
  .dm-eje { width: 40px; }
  .left-col { grid-template-columns: minmax(0, 1fr); }
}
</style>
