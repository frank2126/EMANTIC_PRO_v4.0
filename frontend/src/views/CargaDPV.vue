<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span>📥</span> Carga Masiva DPV</h1>
      <span class="badge badge-info">Solo Administrador</span>
    </div>

    <section class="card guia" aria-label="Cómo se calcula el DPV">
      <p>
        El DPV de cada mes es <strong>los km del mes ÷ las inmovilizaciones del mes</strong>, y necesita dos cosas:
        los <strong>eventos</strong> (paso 1) y los <strong>km</strong> de cada mes (paso 2).
        Las inmovilizaciones y el DPV se calculan solos con los eventos cargados: si un evento cambia de estado, el DPV se actualiza
        sin volver a subir nada. El mismo libro de Excel sirve para los dos pasos.
      </p>
    </section>

    <!-- ══════════════════════════════════════════════════════
         PASO 1: EVENTOS DE INMOVILIZACIÓN
    ══════════════════════════════════════════════════════ -->
    <section class="card upload-card" aria-labelledby="t-eventos">
      <h2 class="card-title" id="t-eventos"><span class="paso">1</span> Eventos de inmovilización</h2>
      <p class="upload-hint">
        Formato: <code>.xlsx</code> · Máximo <strong>{{ MAX_MB }} MB</strong>.
        Sube el libro completo: el sistema busca solo la hoja con los eventos (la que tiene las columnas
        <code>DPV</code>, <code>ESTADO</code> y <code>PLACA</code>, por ejemplo «BASE DE DATOS»).
        Los eventos que ya existen (mismo número de DPV) se actualizan y los nuevos se agregan.<br />
        Columnas que se leen: DPV, ESTADO, F. INICIO DPV, F. CIERRE DPV, EMPRESA, FUENTE, PLACA, MOVIL, TIPOLOGIA,
        FECHA INMOVILIZACION, HORA, CAUSA DE INMOVILIZACION, DESCRIPCION DE LA NOVEDAD, RUTA, OPERADOR, DIA SEMANA, ALERTA,
        FRANJA HORARIA.
      </p>

      <label class="drop-zone"
        :class="{ 'drop-active': eventos.arrastrado, 'drop-ok': eventos.archivo, 'drop-err': eventos.error }"
        @dragover.prevent="eventos.arrastrado = true"
        @dragleave="eventos.arrastrado = false"
        @drop.prevent="soltar(eventos, $event)">
        <input type="file" class="sr-only" accept=".xlsx,.xlsm" aria-label="Elegir el libro de Excel con los eventos"
          @change="elegir(eventos, $event.target.files[0]); $event.target.value = ''" />
        <span v-if="!eventos.archivo" class="drop-content">
          <span class="drop-icon" aria-hidden="true">📊</span>
          <span class="drop-main">Arrastra el libro de Excel aquí</span>
          <span class="drop-sub">o haz clic para seleccionarlo</span>
        </span>
        <span v-else class="drop-content">
          <span class="drop-icon" aria-hidden="true">✅</span>
          <span class="drop-main">{{ eventos.archivo.name }}</span>
          <span class="drop-sub">{{ (eventos.archivo.size / 1024 / 1024).toFixed(2) }} MB</span>
        </span>
      </label>

      <p v-if="eventos.error" class="err-msg" role="alert">⚠️ {{ eventos.error }}</p>

      <div v-if="eventos.cargando" class="progress-wrap">
        <div class="progress-bar" role="progressbar" aria-label="Avance de la carga" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="eventos.progreso">
          <div class="progress-fill" :style="{ width: eventos.progreso + '%' }"></div>
        </div>
        <span class="progress-label">Procesando... {{ eventos.progreso }}%</span>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-secondary" :disabled="eventos.cargando" @click="limpiar(eventos)">Limpiar</button>
        <button type="button" class="btn-primary" :disabled="eventos.cargando || !eventos.archivo" @click="subir(eventos, '/api/dpv/upload', alCargarEventos)">
          {{ eventos.cargando ? 'Procesando...' : '⬆ Procesar eventos' }}
        </button>
      </div>
    </section>

    <transition name="slide">
      <section v-if="eventos.resultado" class="card resultado-card" role="status" aria-label="Resultado de la carga de eventos">
        <h3 class="card-title">Resultado de la carga de eventos</h3>
        <p class="res-msg" :class="eventos.resultado.errores > 0 ? 'res-warn' : 'res-ok'">{{ eventos.resultado.message }}</p>
        <div class="kpi-row">
          <div class="kpi-card"><div class="kpi-val">{{ fmt(eventos.resultado.total) }}</div><div class="kpi-label">Filas leídas</div></div>
          <div class="kpi-card kpi-green"><div class="kpi-val">{{ fmt(eventos.resultado.insertados) }}</div><div class="kpi-label">Insertados</div></div>
          <div class="kpi-card kpi-blue"><div class="kpi-val">{{ fmt(eventos.resultado.actualizados) }}</div><div class="kpi-label">Actualizados</div></div>
          <div class="kpi-card" :class="eventos.resultado.errores > 0 ? 'kpi-red' : 'kpi-green'"><div class="kpi-val">{{ fmt(eventos.resultado.errores) }}</div><div class="kpi-label">Errores</div></div>
          <div class="kpi-card kpi-teal"><div class="kpi-val">{{ eventos.resultado.tiempo_seg }}s</div><div class="kpi-label">Tiempo</div></div>
        </div>

        <p v-if="eventos.resultado.hoja" class="dato-lectura">Hoja leída: <strong>«{{ eventos.resultado.hoja }}»</strong></p>
        <ul v-if="avisosEventos.length" class="lista-avisos">
          <li v-for="a in avisosEventos" :key="a">{{ a }}</li>
        </ul>

        <div v-if="eventos.resultado.errores_detalle && eventos.resultado.errores_detalle.length" class="errores-lista">
          <h4>Detalle de errores:</h4>
          <ul>
            <li v-for="e in eventos.resultado.errores_detalle" :key="e">{{ e }}</li>
            <li v-if="eventos.resultado.errores > eventos.resultado.errores_detalle.length">
              …y {{ fmt(eventos.resultado.errores - eventos.resultado.errores_detalle.length) }} más
            </li>
          </ul>
        </div>

        <div v-if="eventos.resultado.preview && eventos.resultado.preview.length" class="preview-wrap">
          <h4>Vista previa (primeras {{ eventos.resultado.preview.length }} filas procesadas):</h4>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>DPV</th><th>Estado</th><th>Placa</th><th>Empresa</th><th>Causa</th><th>Fecha</th></tr></thead>
              <tbody>
                <tr v-for="p in eventos.resultado.preview" :key="p.dpv">
                  <td><strong>{{ p.dpv }}</strong></td>
                  <td><span class="badge badge-info">{{ p.estado }}</span></td>
                  <td>{{ p.placa }}</td>
                  <td>{{ p.empresa }}</td>
                  <td class="td-causa">{{ p.causa }}</td>
                  <td>{{ p.fecha }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </transition>

    <section class="card historial-card" aria-labelledby="t-hist-eventos">
      <h3 class="card-title" id="t-hist-eventos">Historial de cargas de eventos</h3>
      <div v-if="eventos.historial.length === 0" class="empty-state">
        <span class="empty-icon" aria-hidden="true">📭</span><p>Sin cargas registradas</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>Fecha</th><th>Usuario</th><th>Archivo</th><th>Total</th><th>Insertados</th><th>Actualizados</th><th>Errores</th><th>Tiempo</th><th>Estado</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in eventos.historial" :key="h.id">
              <td>{{ h.fecha }}</td>
              <td>{{ h.usuario }}</td>
              <td class="td-archivo">{{ h.archivo }}</td>
              <td>{{ fmt(h.total) }}</td>
              <td class="td-green">{{ fmt(h.insertados) }}</td>
              <td class="td-blue">{{ fmt(h.actualizados) }}</td>
              <td :class="h.errores > 0 ? 'td-red' : ''">{{ fmt(h.errores) }}</td>
              <td>{{ h.tiempo_seg }}s</td>
              <td>
                <span class="badge" :class="ESTADO_BADGE[h.estado] || 'badge-danger'">{{ h.estado }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════════════
         PASO 2: KM OFICIALES DE CADA MES
    ══════════════════════════════════════════════════════ -->
    <div class="seccion-divider">
      <span aria-hidden="true">📈</span>
      <h2>Km de cada mes</h2>
    </div>

    <section class="card nota" aria-label="Qué se toma del Excel de km">
      <p>
        De este paso solo se toman los <strong>km</strong> de cada mes (total y, si los tienes, por tipología).
        Las inmovilizaciones <strong>no se escriben</strong>: salen de los eventos del paso 1, sin contar los estados
        <template v-if="estadosDescartados.length">«{{ estadosDescartados.join('», «') }}»</template>
        <template v-else>descartados</template>.
        Las columnas de inmovilizaciones y DPV que traiga el Excel se guardan solo para compararlas.
        <template v-if="umbrales">
          Nivel del DPV: <strong>cumple</strong> desde {{ fmtKm(umbrales.estandar) }} km,
          <strong>crítico</strong> hasta {{ fmtKm(umbrales.critico) }} km.
        </template>
      </p>
    </section>

    <section class="card upload-card" aria-labelledby="t-km">
      <h2 class="card-title" id="t-km"><span class="paso">2</span> Subir los km desde Excel</h2>
      <p class="upload-hint">
        Formato: <code>.xlsx</code> · Máximo <strong>{{ MAX_MB }} MB</strong>.
        El libro debe tener las hojas <code>DPV_E10</code> y <code>DPV_E16</code>, con las columnas
        <code>MES</code>, <code>TOTAL KM</code> y, si las tienes, <code>KM PADRON</code> y <code>KM BUSETON</code>
        (también se leen <code>TOTAL INNMOVILIZADOS</code> y <code>DPV GENERAL</code>, solo para comparar).
        El diseño anterior (DVP_E10, No VARADOS, KMS, PADRON, BUSETON) también se entiende.
        Los meses sin km se omiten: no se guardan como cero.
      </p>

      <label class="drop-zone"
        :class="{ 'drop-active': kmMes.arrastrado, 'drop-ok': kmMes.archivo, 'drop-err': kmMes.error }"
        @dragover.prevent="kmMes.arrastrado = true"
        @dragleave="kmMes.arrastrado = false"
        @drop.prevent="soltar(kmMes, $event)">
        <input type="file" class="sr-only" accept=".xlsx" aria-label="Elegir el libro de Excel con los km de cada mes"
          @change="elegir(kmMes, $event.target.files[0]); $event.target.value = ''" />
        <span v-if="!kmMes.archivo" class="drop-content">
          <span class="drop-icon" aria-hidden="true">📈</span>
          <span class="drop-main">Arrastra el libro con las hojas DPV_E10 y DPV_E16 aquí</span>
          <span class="drop-sub">o haz clic para seleccionarlo</span>
        </span>
        <span v-else class="drop-content">
          <span class="drop-icon" aria-hidden="true">✅</span>
          <span class="drop-main">{{ kmMes.archivo.name }}</span>
          <span class="drop-sub">{{ (kmMes.archivo.size / 1024 / 1024).toFixed(2) }} MB</span>
        </span>
      </label>

      <p v-if="kmMes.error" class="err-msg" role="alert">⚠️ {{ kmMes.error }}</p>

      <div v-if="kmMes.cargando" class="progress-wrap">
        <div class="progress-bar" role="progressbar" aria-label="Avance de la carga" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="kmMes.progreso">
          <div class="progress-fill" :style="{ width: kmMes.progreso + '%' }"></div>
        </div>
        <span class="progress-label">Procesando... {{ kmMes.progreso }}%</span>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-secondary" :disabled="kmMes.cargando" @click="limpiar(kmMes)">Limpiar</button>
        <button type="button" class="btn-primary" :disabled="kmMes.cargando || !kmMes.archivo" @click="subir(kmMes, '/api/dpv-mensual/upload', alCargarKm)">
          {{ kmMes.cargando ? 'Procesando...' : '⬆ Procesar km' }}
        </button>
      </div>
    </section>

    <transition name="slide">
      <section v-if="kmMes.resultado" class="card resultado-card" role="status" aria-label="Resultado de la carga de km">
        <h3 class="card-title">Resultado de la carga de km</h3>
        <p class="res-msg" :class="kmMes.resultado.errores > 0 ? 'res-warn' : 'res-ok'">{{ kmMes.resultado.message }}</p>
        <div class="kpi-row">
          <div class="kpi-card"><div class="kpi-val">{{ fmt(kmMes.resultado.total) }}</div><div class="kpi-label">Filas leídas</div></div>
          <div class="kpi-card kpi-green"><div class="kpi-val">{{ fmt(kmMes.resultado.insertados) }}</div><div class="kpi-label">Meses nuevos</div></div>
          <div class="kpi-card kpi-blue"><div class="kpi-val">{{ fmt(kmMes.resultado.actualizados) }}</div><div class="kpi-label">Meses actualizados</div></div>
          <div class="kpi-card" :class="kmMes.resultado.errores > 0 ? 'kpi-red' : 'kpi-green'"><div class="kpi-val">{{ fmt(kmMes.resultado.errores) }}</div><div class="kpi-label">Errores</div></div>
          <div class="kpi-card kpi-teal"><div class="kpi-val">{{ kmMes.resultado.tiempo_seg }}s</div><div class="kpi-label">Tiempo</div></div>
        </div>

        <p v-if="kmMes.resultado.formato" class="dato-lectura">Formato leído: <strong>{{ FORMATO_MENSUAL[kmMes.resultado.formato] || kmMes.resultado.formato }}</strong></p>

        <div v-if="sinKmResumen.length" class="aviso" role="note">
          <strong>Meses sin km en el Excel (no se guardaron; no cuentan como cero):</strong>
          <ul>
            <li v-for="s in sinKmResumen" :key="s">{{ s }}</li>
          </ul>
          Cuando estén cerrados, escríbelos en el Excel y vuelve a subirlo, o captúralos a mano abajo.
        </div>

        <div v-if="kmMes.resultado.advertencias && kmMes.resultado.advertencias.length" class="aviso" role="note">
          <strong>Revisa estas filas:</strong>
          <ul>
            <li v-for="a in kmMes.resultado.advertencias" :key="a">{{ a }}</li>
          </ul>
        </div>

        <div v-if="kmMes.resultado.errores_detalle && kmMes.resultado.errores_detalle.length" class="errores-lista">
          <h4>Detalle de errores:</h4>
          <ul>
            <li v-for="e in kmMes.resultado.errores_detalle" :key="e">{{ e }}</li>
            <li v-if="kmMes.resultado.errores > kmMes.resultado.errores_detalle.length">
              …y {{ fmt(kmMes.resultado.errores - kmMes.resultado.errores_detalle.length) }} más
            </li>
          </ul>
        </div>
      </section>
    </transition>

    <!-- Captura manual de los km de un mes -->
    <section class="card upload-card" aria-labelledby="t-manual">
      <h2 class="card-title" id="t-manual">{{ form.editando ? 'Editar los km de un mes' : 'Escribir los km de un mes a mano' }}</h2>
      <p class="upload-hint">
        Útil para los meses que el Excel todavía no trae. El total es obligatorio; Padrón y Buseton son opcionales
        (si escribes los dos, su suma debe coincidir con el total). Puedes escribir «1.000.000» o «1000000».
      </p>

      <form class="form-grid" novalidate @submit.prevent="guardarKm">
        <div class="campo">
          <label class="label" for="km-unidad">Unidad</label>
          <select id="km-unidad" class="input" v-model="form.empresa">
            <option value="">Elige…</option>
            <option v-for="u in UNIDADES_CARGA" :key="u.key" :value="u.key">{{ u.nombre }}</option>
          </select>
        </div>
        <div class="campo">
          <label class="label" for="km-mes">Mes</label>
          <input id="km-mes" class="input" type="month" placeholder="AAAA-MM" v-model="form.mes" />
        </div>
        <div class="campo">
          <label class="label" for="km-total">Km totales</label>
          <input id="km-total" ref="campoTotal" class="input" type="text" inputmode="decimal" autocomplete="off" placeholder="1.000.000" v-model="form.total" />
        </div>
        <div class="campo">
          <label class="label" for="km-padron">Km Padrón (opcional)</label>
          <input id="km-padron" class="input" type="text" inputmode="decimal" autocomplete="off" placeholder="600.000" v-model="form.padron" />
        </div>
        <div class="campo">
          <label class="label" for="km-buseton">Km Buseton (opcional)</label>
          <input id="km-buseton" class="input" type="text" inputmode="decimal" autocomplete="off" placeholder="400.000" v-model="form.buseton" />
        </div>
        <div class="campo campo-acciones">
          <button type="button" class="btn-secondary" :disabled="form.guardando" @click="cancelarKm">Cancelar</button>
          <button type="submit" class="btn-primary" :disabled="form.guardando">{{ form.guardando ? 'Guardando...' : 'Guardar km' }}</button>
        </div>
      </form>

      <p v-if="sumaTipologias" class="suma-tipos" :class="sumaTipologias.cuadra ? 'suma-ok' : 'suma-mal'">
        Padrón + Buseton = {{ fmtKm(sumaTipologias.suma) }}
        <template v-if="sumaTipologias.total !== null">
          · {{ sumaTipologias.cuadra ? 'coincide con el total ✔' : 'no coincide con el total (' + fmtKm(sumaTipologias.total) + ') ✖' }}
        </template>
      </p>
      <p v-if="form.error" class="err-msg" role="alert">⚠️ {{ form.error }}</p>
      <p v-if="form.ok" class="ok-msg" role="status">✔ {{ form.ok }}</p>
    </section>

    <!-- Km guardados, por mes y unidad -->
    <section class="card historial-card" aria-labelledby="t-tabla">
      <div class="tabla-cab">
        <h3 class="card-title" id="t-tabla">
          Km por mes y unidad
          <span v-if="sinKmTotal > 0" class="badge badge-aviso">{{ sinKmTotal }} {{ sinKmTotal === 1 ? 'mes sin km' : 'meses sin km' }}</span>
        </h3>
        <div class="tabla-filtros">
          <label class="sr-only" for="f-unidad">Unidad</label>
          <select id="f-unidad" class="input input-chico" v-model="filtroUnidad">
            <option value="">Todas las unidades</option>
            <option v-for="u in UNIDADES_CARGA" :key="u.key" :value="u.key">{{ u.nombre }}</option>
          </select>
          <label class="chk"><input type="checkbox" v-model="soloSinKm" /> Solo meses sin km</label>
        </div>
      </div>

      <p v-if="estadoTabla.error" class="err-msg" role="alert">⚠️ {{ estadoTabla.error }}</p>
      <p v-if="estadoTabla.ok" class="ok-msg" role="status">✔ {{ estadoTabla.ok }}</p>
      <p v-if="errorMensual" class="err-msg" role="alert">⚠️ {{ errorMensual }}</p>

      <div v-if="!mensual && !errorMensual" class="empty-state"><p>Cargando…</p></div>
      <div v-else-if="mensual && filas.length === 0" class="empty-state">
        <span class="empty-icon" aria-hidden="true">📭</span>
        <p>{{ soloSinKm ? 'Todos los meses tienen km.' : 'Aún no hay meses con eventos ni km. Sube los eventos y los km.' }}</p>
      </div>
      <div v-else-if="filas.length" class="table-wrap km-wrap">
        <table class="data-table km-tabla">
          <caption class="sr-only">Km, inmovilizaciones y DPV de cada mes, del más reciente al más antiguo</caption>
          <thead>
            <tr>
              <th>Unidad</th><th>Mes</th><th class="th-r">Km total</th><th class="th-r">Padrón</th><th class="th-r">Buseton</th>
              <th class="th-r">Inmovilizaciones</th><th class="th-r">DPV</th><th>Origen</th><th><span class="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in filas" :key="f.clave" :class="{ 'fila-sin-km': f.sinKm }">
              <td class="td-unidad">{{ f.unidad }}</td>
              <td class="td-mes">{{ f.titulo }}</td>
              <td class="td-num">{{ f.sinKm ? '—' : fmtKm(f.km) }}</td>
              <td class="td-num">{{ f.kmPadron === null ? '—' : fmtKm(f.kmPadron) }}</td>
              <td class="td-num">{{ f.kmBuseton === null ? '—' : fmtKm(f.kmBuseton) }}</td>
              <td class="td-num">{{ f.inm === null ? '—' : fmt(f.inm) }}</td>
              <td class="td-num">
                <template v-if="f.dpv !== null">
                  <strong>{{ fmtKm(f.dpv) }}</strong>
                  <span v-if="f.nivel && NIVEL[f.nivel]" class="badge nivel" :class="NIVEL_BADGE[f.nivel]">{{ NIVEL[f.nivel].icono }} {{ NIVEL[f.nivel].corto }}</span>
                </template>
                <template v-else>—</template>
              </td>
              <td><span class="badge" :class="ORIGEN_BADGE[f.origen]">{{ ORIGEN_CORTO[f.origen] }}</span></td>
              <td class="td-acciones">
                <button v-if="f.sinKm" type="button" class="btn-primary btn-mini" :aria-label="'Cargar los km de ' + f.unidad + ' ' + f.titulo" @click="editarKm(f)">Cargar km</button>
                <template v-else>
                  <button type="button" class="btn-secondary btn-mini" :aria-label="'Editar los km de ' + f.unidad + ' ' + f.titulo" @click="editarKm(f)">Editar</button>
                  <button v-if="f.puedeBorrar" type="button" class="btn-secondary btn-mini btn-borrar" :aria-label="'Borrar los km de ' + f.unidad + ' ' + f.titulo" @click="borrarKm(f)">Borrar</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card historial-card" aria-labelledby="t-hist-km">
      <h3 class="card-title" id="t-hist-km">Historial de cargas de km</h3>
      <div v-if="kmMes.historial.length === 0" class="empty-state">
        <span class="empty-icon" aria-hidden="true">📭</span><p>Sin cargas registradas</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>Fecha</th><th>Usuario</th><th>Archivo</th><th>Total</th><th>Insertados</th><th>Actualizados</th><th>Errores</th><th>Tiempo</th><th>Estado</th></tr>
          </thead>
          <tbody>
            <tr v-for="h in kmMes.historial" :key="h.id">
              <td>{{ h.fecha }}</td>
              <td>{{ h.usuario }}</td>
              <td class="td-archivo">{{ h.archivo }}</td>
              <td>{{ fmt(h.total) }}</td>
              <td class="td-green">{{ fmt(h.insertados) }}</td>
              <td class="td-blue">{{ fmt(h.actualizados) }}</td>
              <td :class="h.errores > 0 ? 'td-red' : ''">{{ fmt(h.errores) }}</td>
              <td>{{ h.tiempo_seg }}s</td>
              <td>
                <span class="badge" :class="ESTADO_BADGE[h.estado] || 'badge-danger'">{{ h.estado }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import axios from 'axios'
import {
  UNIDADES_CARGA, FORMATO_MENSUAL, NIVEL, fmtKm, tituloMes,
  filasKm, resumenSinKm, avisosCalidad, validarKmManual, numeroDeTexto, mensajeError,
} from './dpvUtils.js'

const MAX_MB = 10   // mismo límite que el backend (MAX_FILE_MB en routes/datos.py)
const fmt = n => (n == null ? '—' : Number(n).toLocaleString('es-CO'))
// «badge-aviso» y «badge-manual» (abajo) son versiones con texto más oscuro de badge-warning y badge-teal: las globales no llegan a 4.5:1
const NIVEL_BADGE = { cumple: 'badge-success', alerta: 'badge-aviso', critico: 'badge-danger' }
const ORIGEN_CORTO = { excel: 'Excel', manual: 'Manual', legacy: 'Carga anterior', sin_km: 'Sin km' }
const ORIGEN_BADGE = { excel: 'badge-info', manual: 'badge-manual', legacy: 'badge-gray', sin_km: 'badge-aviso' }
const ESTADO_BADGE = { exitoso: 'badge-success', parcial: 'badge-aviso' }   // cualquier otro estado = fallido (rojo)

// ── Estado de cada carga: eventos (paso 1) y km (paso 2) ──
const nuevaCarga = (extensiones) => reactive({
  extensiones, archivo: null, arrastrado: false, cargando: false, progreso: 0, error: '', resultado: null, historial: [],
})
const eventos = nuevaCarga(['xlsx', 'xlsm'])
const kmMes = nuevaCarga(['xlsx'])

function elegir(c, f) {
  c.error = ''
  c.resultado = null
  c.archivo = null
  if (!f) return
  const ext = (f.name.split('.').pop() || '').toLowerCase()
  if (ext === 'xls') { c.error = 'El formato .xls antiguo no es compatible: ábrelo en Excel y guárdalo como .xlsx.'; return }
  if (!c.extensiones.includes(ext)) { c.error = `Solo se permiten archivos .${c.extensiones.join(' o .')}`; return }
  if (f.size > MAX_MB * 1024 * 1024) { c.error = `El archivo supera el límite de ${MAX_MB} MB`; return }
  c.archivo = f
}
const soltar = (c, ev) => { c.arrastrado = false; elegir(c, ev.dataTransfer && ev.dataTransfer.files[0]) }
const limpiar = (c) => { c.archivo = null; c.error = ''; c.resultado = null; c.progreso = 0 }

async function subir(c, url, despues) {
  if (!c.archivo || c.cargando) return
  c.cargando = true
  c.error = ''
  c.resultado = null
  c.progreso = 10
  const fd = new FormData()
  fd.append('file', c.archivo)
  try {
    const { data } = await axios.post(url, fd, {
      onUploadProgress: e => { if (e.total) c.progreso = Math.min(80, Math.round((e.loaded / e.total) * 70) + 10) },
    })
    c.progreso = 100
    c.resultado = data
    await despues()
  } catch (e) {
    c.error = mensajeError(e, 'Error al procesar el archivo')
  } finally {
    c.cargando = false
    setTimeout(() => { c.progreso = 0 }, 1500)
  }
}

async function cargarHistorial(c, tipo) {
  try {
    const { data } = await axios.get(`/api/cargas/historial?tipo=${tipo}&limit=10`)
    c.historial = data
  } catch { /* el historial es informativo: si falla no estorba */ }
}

// ── Serie mensual (km guardados + inmovilizaciones y DPV calculados con los eventos) ──
const mensual = ref(null)
const errorMensual = ref('')
async function cargarMensual() {
  try {
    const { data } = await axios.get('/api/dpv-mensual')
    mensual.value = data
    errorMensual.value = ''
  } catch (e) {
    errorMensual.value = mensajeError(e, 'No se pudo leer la serie mensual')
  }
}
const estadosDescartados = computed(() => (mensual.value && mensual.value.estados_descartados) || [])
const umbrales = computed(() => (mensual.value && mensual.value.umbrales) || null)

// Después de subir eventos cambian las inmovilizaciones de cada mes: se vuelve a leer la serie
const alCargarEventos = () => Promise.all([cargarHistorial(eventos, 'dpv'), cargarMensual()])
const alCargarKm = () => Promise.all([cargarHistorial(kmMes, 'dpv_mensual'), cargarMensual()])

const avisosEventos = computed(() => (eventos.resultado ? avisosCalidad(eventos.resultado.calidad, estadosDescartados.value) : []))
const sinKmResumen = computed(() => (kmMes.resultado ? resumenSinKm(kmMes.resultado.sin_km) : []))

// ── Tabla «Km por mes y unidad» ──
const filtroUnidad = ref('')
const soloSinKm = ref(false)
const filas = computed(() => filasKm(mensual.value, { unidad: filtroUnidad.value, soloSinKm: soloSinKm.value }))
const sinKmTotal = computed(() => filasKm(mensual.value).filter(f => f.sinKm).length)
const estadoTabla = reactive({ ok: '', error: '' })

// ── Captura manual ──
const form = reactive({ empresa: '', mes: '', total: '', padron: '', buseton: '', editando: false, guardando: false, error: '', ok: '' })
const campoTotal = ref(null)

// Mientras se escribe: ¿Padrón + Buseton cuadra con el total? (misma tolerancia que el backend: 1 % o 1 km)
const sumaTipologias = computed(() => {
  const p = numeroDeTexto(form.padron)
  const b = numeroDeTexto(form.buseton)
  if (p === null || b === null) return null
  const t = numeroDeTexto(form.total)
  return { suma: p + b, total: t, cuadra: t !== null && Math.abs(p + b - t) <= Math.max(1, t * 0.01) }
})

function mensajeGuardado(d, fila) {
  const unidad = UNIDADES_CARGA.find(u => u.key === d.empresa)
  const base = `Guardado: ${unidad ? unidad.nombre : d.empresa} · ${tituloMes(d.mes)} · ${fmtKm(d.km_total)} km.`
  if (!fila) return base
  if (fila.dpv !== null) return `${base} DPV del mes: ${fmtKm(fila.dpv)} km (${fila.inm} inmovilizaciones).`
  return `${base} Ese mes aún no tiene inmovilizaciones cargadas, por eso todavía no hay DPV.`
}

async function guardarKm() {
  form.ok = ''
  estadoTabla.ok = ''
  const v = validarKmManual(form)
  if (v.error) { form.error = v.error; return }
  form.error = ''
  form.guardando = true
  try {
    await axios.put('/api/dpv-km', v.datos)
    await alCargarKm()
    form.ok = mensajeGuardado(v.datos, filasKm(mensual.value).find(f => f.clave === `${v.datos.empresa}-${v.datos.mes}`))
    form.total = ''
    form.padron = ''
    form.buseton = ''
    form.editando = false
  } catch (e) {
    form.error = mensajeError(e, 'No se pudieron guardar los km')
  } finally {
    form.guardando = false
  }
}

function cancelarKm() {
  form.total = ''
  form.padron = ''
  form.buseton = ''
  form.editando = false
  form.error = ''
  form.ok = ''
}

// «Cargar km» / «Editar» en la tabla: deja el formulario listo con la unidad y el mes (y los km que ya hubiera)
function editarKm(f) {
  form.empresa = f.empresa
  form.mes = f.mes
  form.total = f.sinKm ? '' : String(f.km)
  form.padron = f.kmPadron === null ? '' : String(f.kmPadron)
  form.buseton = f.kmBuseton === null ? '' : String(f.kmBuseton)
  form.editando = !f.sinKm
  form.error = ''
  form.ok = ''
  estadoTabla.ok = ''
  estadoTabla.error = ''
  nextTick(() => {
    const el = campoTotal.value
    if (!el) return
    el.scrollIntoView({ block: 'center', behavior: 'smooth' })
    el.focus({ preventScroll: true })
  })
}

async function borrarKm(f) {
  const pregunta = `¿Borrar los km de ${f.unidad} · ${f.titulo}?\nEse mes quedará «sin km» y no tendrá DPV hasta que los vuelvas a cargar.`
  if (!window.confirm(pregunta)) return
  estadoTabla.ok = ''
  estadoTabla.error = ''
  try {
    await axios.delete(`/api/dpv-km/${f.empresa}/${f.mes}`)
    await alCargarKm()
    estadoTabla.ok = `Se borraron los km de ${f.unidad} · ${f.titulo}.`
  } catch (e) {
    estadoTabla.error = mensajeError(e, 'No se pudieron borrar los km')
  }
}

onMounted(() => {
  cargarHistorial(eventos, 'dpv')
  cargarHistorial(kmMes, 'dpv_mensual')
  cargarMensual()
})
</script>

<style scoped>
.guia, .nota { padding: 16px 20px; margin-bottom: 20px; font-size: 13.5px; line-height: 1.6; color: var(--text); }
.nota { background: var(--surface-2); border-left: 4px solid var(--accent); }
.upload-card    { padding: 28px; margin-bottom: 20px; }
.historial-card { padding: 24px; margin-top: 20px; }
.resultado-card { padding: 24px; margin-bottom: 20px; }
.card-title     { font-size: 16px; font-weight: 700; margin-bottom: 14px; color: var(--text); display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.paso {
  display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; flex: none;
  border-radius: 50%; background: var(--primary); color: #fff; font-size: 13px; font-weight: 800;
}
.upload-hint    { font-size: 12.5px; color: var(--text-muted); margin-bottom: 18px; line-height: 1.6; }
.upload-hint code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 11px; color: var(--primary); }

.sr-only {
  position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}

.drop-zone {
  display: block; position: relative;
  border: 2px dashed var(--border); border-radius: 12px;
  padding: 40px 20px; text-align: center; cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s; margin-bottom: 16px;   /* sin animar el anillo de foco: debe verse al instante */
}
.drop-zone:hover, .drop-active { border-color: var(--accent); background: var(--accent-light); }
.drop-zone:focus-within { outline: 2px solid var(--accent); outline-offset: 2px; }
.drop-ok  { border-color: var(--accent); border-style: solid; background: var(--success-light); }
.drop-err { border-color: var(--danger); background: var(--danger-light); }
.drop-content { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.drop-icon { font-size: 40px; }
.drop-main { font-size: 14px; color: var(--text); font-weight: 500; overflow-wrap: anywhere; }
.drop-sub  { font-size: 12px; color: var(--text-muted); font-weight: 400; }
.drop-ok .drop-sub { color: #46605a; }   /* sobre el verde claro el gris de siempre queda en 4.4:1 */

.progress-wrap  { margin: 12px 0; }
.progress-bar   { background: var(--border); border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 6px; }
.progress-fill  { height: 100%; background: var(--accent); border-radius: 8px; transition: width 0.3s; }
.progress-label { font-size: 12px; color: var(--text-muted); }

.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 16px; }
.err-msg      { color: var(--danger); font-size: 13px; margin: 8px 0; }
.ok-msg       { color: #17794f; font-size: 13px; font-weight: 600; margin: 8px 0; }

.res-msg  { font-size: 13.5px; font-weight: 600; margin-bottom: 14px; }
.res-ok   { color: #17794f; }
.res-warn { color: #8a4b05; }
.kpi-row  { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; min-width: 100px; text-align: center; }
.kpi-val  { font-size: 28px; font-weight: 800; }
.kpi-label{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.kpi-green .kpi-val { color: #17794f; }
.kpi-blue  .kpi-val { color: var(--secondary); }
.kpi-red   .kpi-val { color: var(--danger); }
.kpi-teal  .kpi-val { color: var(--teal); }

.dato-lectura { font-size: 13px; margin-bottom: 12px; color: var(--text); }
.lista-avisos { margin: 0 0 16px; padding: 12px 18px 12px 34px; background: var(--info-light); border-radius: 8px; font-size: 12.5px; color: var(--text); line-height: 1.6; }
.aviso { background: var(--warning-light); border: 1px solid #f0cf9b; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; font-size: 12.5px; color: #8a4b05; line-height: 1.6; }
.aviso ul { padding-left: 18px; margin: 6px 0; }

.errores-lista { background: var(--danger-light); border: 1px solid #fca5a5; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; }
.errores-lista h4 { font-size: 13px; color: var(--danger); margin-bottom: 8px; }
.errores-lista ul { padding-left: 18px; font-size: 12px; color: var(--danger); }
.errores-lista li { margin-bottom: 4px; }

.preview-wrap h4,
.historial-card h4 { font-size: 13px; font-weight: 700; color: var(--text-muted); margin-bottom: 10px; }
.table-wrap   { overflow-x: auto; }
.empty-state { padding: 26px 20px; }
.empty-state .empty-icon { font-size: 30px; margin-bottom: 6px; }
.td-causa     { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.td-archivo   { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }
.td-green     { color: #17794f; font-weight: 600; }
.td-blue      { color: var(--secondary); font-weight: 600; }
.td-red       { color: var(--danger); font-weight: 600; }

.slide-enter-active, .slide-leave-active { transition: all 0.25s; }
.slide-enter-from, .slide-leave-to       { opacity: 0; transform: translateY(-8px); }

/* ── Separador del paso 2 ── */
.seccion-divider {
  display: flex; align-items: center; gap: 10px;
  margin: 32px 0 18px;
  padding-top: 24px;
  border-top: 2px solid var(--border);
}
.seccion-divider span { font-size: 22px; }
.seccion-divider h2 { font-size: 18px; font-weight: 800; color: var(--text); margin: 0; }

/* ── Formulario manual ── */
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px 16px; align-items: end; }
.form-grid .input { height: 42px; }
.campo-acciones { grid-column: 1 / -1; display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; }
.suma-tipos { font-size: 12.5px; margin-top: 10px; font-weight: 600; }
.suma-ok  { color: #17794f; }
.suma-mal { color: #8a4b05; }

/* ── Tabla de km por mes ── */
.tabla-cab { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.tabla-cab .card-title { margin-bottom: 0; }
.tabla-filtros { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.input-chico { width: auto; min-width: 180px; padding: 7px 12px; font-size: 13px; }
.chk { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text); cursor: pointer; }
.chk input { width: 16px; height: 16px; accent-color: var(--accent); }
.km-wrap { max-height: 460px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; }
.km-tabla th { position: sticky; top: 0; z-index: 1; }
.km-tabla .th-r, .km-tabla .td-num { text-align: right; font-variant-numeric: tabular-nums; }
.td-unidad { font-weight: 700; white-space: nowrap; }
.td-mes { white-space: nowrap; }
.badge-aviso  { background: var(--warning-light); color: #8a4b05; }
.badge-manual { background: var(--teal-light); color: #17695d; }
.nivel { margin-left: 8px; padding: 2px 8px; font-size: 11px; }
.fila-sin-km td { background: var(--warning-light) !important; }
.td-acciones { white-space: nowrap; text-align: right; }
.btn-mini { padding: 4px 10px; font-size: 12px; border-radius: 6px; margin-left: 6px; }
.btn-borrar { color: var(--danger); border-color: var(--danger); }
.btn-borrar:hover { background: var(--danger-light); }

@media (max-width: 768px) {
  .upload-card, .historial-card, .resultado-card { padding: 18px; }
  .form-actions { justify-content: stretch; }
  .form-actions button { flex: 1; justify-content: center; }
  .campo-acciones { justify-content: stretch; }
  .campo-acciones button { flex: 1; justify-content: center; }
}
</style>
