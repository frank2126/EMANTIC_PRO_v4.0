<template>
  <section v-if="visible" class="card dup" aria-label="Casos duplicados del DPV">
    <div class="dup-top">
      <span class="dup-ico" aria-hidden="true">{{ total ? '⚠️' : '✅' }}</span>
      <div class="dup-txt">
        <strong v-if="total">{{ fmt(total) }} caso(s) duplicado(s) retirados del conteo · {{ moviles.length }} móvil(es)</strong>
        <strong v-else>Sin casos duplicados apartados</strong>
        <span class="dup-sub">Mismo móvil, misma fecha-hora y misma novedad con distinto IdDPV: se conserva el primero y no cuentan en las gráficas ni en el dashboard.</span>
      </div>
      <button v-if="total" type="button" class="dup-btn" :aria-expanded="abierto" @click="abierto = !abierto">{{ abierto ? 'Ocultar' : 'Ver detalle' }}</button>
      <button v-if="admin" type="button" class="dup-btn dup-btn--sec" :disabled="trabajando" @click="buscar">🔎 Buscar en lo ya cargado</button>
    </div>

    <p v-if="error" class="dup-err" role="alert">⚠️ {{ error }}</p>

    <div v-if="propuesta" class="dup-prop" role="status">
      <template v-if="propuesta.duplicados">
        Se encontraron <b>{{ fmt(propuesta.duplicados) }}</b> caso(s) repetido(s) en <b>{{ propuesta.moviles.length }}</b> móvil(es) que ya están cargados en el DPV.
        <button type="button" class="dup-btn" :disabled="trabajando" @click="aplicar">Apartarlos ahora</button>
        <button type="button" class="dup-btn dup-btn--sec" @click="propuesta = null">Cancelar</button>
      </template>
      <template v-else>No hay repetidos en lo que ya está cargado. ✔ <button type="button" class="dup-btn dup-btn--sec" @click="propuesta = null">Cerrar</button></template>
    </div>

    <div v-if="abierto && total" class="dup-detalle">
      <div class="dup-scroll">
        <table class="dup-tabla">
          <caption class="sr-only">Móviles con casos duplicados</caption>
          <thead><tr><th scope="col">Móvil</th><th scope="col">Empresa</th><th scope="col" class="num">Copias</th><th scope="col">Novedades repetidas</th><th scope="col">Última fecha</th></tr></thead>
          <tbody>
            <tr v-for="m in moviles" :key="m.movil" class="dup-fila" :class="{ sel: movilSel === m.movil }" tabindex="0" @click="alternarMovil(m.movil)" @keydown.enter="alternarMovil(m.movil)">
              <td class="b">{{ m.movil }}</td><td>{{ corto(m.empresa) }}</td><td class="num"><span class="dup-n">{{ m.copias }}</span></td>
              <td class="nov">{{ m.novedades.join(' · ') }}</td><td>{{ fechaHora(m.ultima) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="dup-casos">
        <div class="dup-casos-t">
          {{ movilSel ? 'Casos de ' + movilSel : 'Todos los casos apartados' }}
          <button v-if="movilSel" type="button" class="dup-link" @click="movilSel = ''">ver todos</button>
        </div>
        <ul class="dup-lista">
          <li v-for="i in casos" :key="i.dpv_id">
            <span class="dup-id">{{ i.dpv_id }}</span>
            <span class="dup-copia">copia de <b>{{ i.original_id ?? '—' }}</b></span>
            <span class="dup-casos-m">{{ i.movil }} · {{ i.causa_inmovilizacion || '—' }} · {{ fechaHora(i.fecha_inmovilizacion) }}</span>
            <button v-if="admin" type="button" class="dup-link" :disabled="trabajando" title="Si no era realmente repetido: vuelve a contar" @click="restaurar(i)">Restaurar</button>
          </li>
        </ul>
        <p v-if="casos.length < total && !movilSel" class="dup-sub">Se muestran los {{ casos.length }} más recientes de {{ fmt(total) }}.</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useAuth } from '../auth.js'

// `recargando`: true mientras el DPV se recarga; al terminar (true → false) se vuelve a consultar.
// `cambio`: se emite cuando se apartan o restauran casos, para que el DPV recalcule sus gráficas.
const props = defineProps({ recargando: { type: Boolean, default: false } })
const emit = defineEmits(['cambio'])
const { isAdmin } = useAuth()
const admin = computed(() => isAdmin())

const total = ref(0)
const moviles = ref([])
const items = ref([])
const abierto = ref(false)
const movilSel = ref('')
const propuesta = ref(null)
const trabajando = ref(false)
const error = ref('')
const cargado = ref(false)

const visible = computed(() => total.value > 0 || admin.value)   // sin duplicados solo lo ve el admin (para poder buscar)
const casos = computed(() => (movilSel.value ? items.value.filter(i => i.movil === movilSel.value) : items.value))

const fmt = n => Number(n || 0).toLocaleString('es-CO')
const corto = e => String(e || '').replace(/\s*S\.A\.S\.?/i, '').replace(/^EMASIVO\s*/i, 'EMASIVO ')
const fechaHora = iso => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)} ${iso.slice(11, 16)}` : '—')
const detalle = (e, txt) => e?.response?.data?.detail || txt

async function cargar() {
  try {
    const { data } = await axios.get('/api/dpv/duplicados')
    total.value = data?.total || 0
    moviles.value = data?.moviles || []
    items.value = data?.items || []
    error.value = ''
    if (!total.value) abierto.value = false
  } catch (e) {
    if (e?.response?.status !== 404) error.value = detalle(e, 'No pude consultar los duplicados')   // 404 = backend sin actualizar: no estorba
  } finally {
    cargado.value = true
  }
}

const alternarMovil = m => { movilSel.value = movilSel.value === m ? '' : m }

async function buscar() {
  trabajando.value = true; error.value = ''
  try {
    const { data } = await axios.post('/api/dpv/duplicados/limpiar', null, { params: { aplicar: false } })
    propuesta.value = data
  } catch (e) { error.value = detalle(e, 'No pude buscar duplicados') } finally { trabajando.value = false }
}

async function aplicar() {
  trabajando.value = true; error.value = ''
  try {
    await axios.post('/api/dpv/duplicados/limpiar', null, { params: { aplicar: true } })
    propuesta.value = null
    await cargar()
    abierto.value = total.value > 0
    emit('cambio')
  } catch (e) { error.value = detalle(e, 'No pude apartar los duplicados') } finally { trabajando.value = false }
}

async function restaurar(i) {
  if (!window.confirm(`¿Restaurar el caso ${i.dpv_id}? Volverá a contar en el DPV y no se apartará en próximas cargas.`)) return
  trabajando.value = true; error.value = ''
  try {
    await axios.post(`/api/dpv/duplicados/${i.dpv_id}/restaurar`)
    await cargar()
    emit('cambio')
  } catch (e) { error.value = detalle(e, 'No pude restaurar el caso') } finally { trabajando.value = false }
}

watch(() => props.recargando, (ahora, antes) => { if (antes && !ahora) cargar() })
onMounted(cargar)
</script>

<style scoped>
.dup { padding:12px 16px; display:flex; flex-direction:column; gap:10px; border-left:4px solid #F59E0B; }
.dup-top { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.dup-ico { font-size:18px; }
.dup-txt { display:flex; flex-direction:column; gap:2px; flex:1; min-width:240px; }
.dup-txt strong { font-size:13px; color:#111827; }
.dup-sub { font-size:11px; color:#6B7280; line-height:1.4; }
.dup-btn { padding:5px 13px; border-radius:14px; border:1px solid #0F5132; background:#0F5132; color:#fff; font-size:11.5px; font-weight:600; cursor:pointer; font-family:inherit; }
.dup-btn--sec { background:#fff; color:#0F5132; }
.dup-btn:hover:not(:disabled) { filter:brightness(1.12); }
.dup-btn:disabled { opacity:.5; cursor:default; }
.dup-err { margin:0; font-size:12px; color:#C0392B; }
.dup-prop { background:#FEF3E2; border-radius:10px; padding:9px 12px; font-size:12px; color:#7C4A03; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.dup-detalle { display:grid; grid-template-columns:1.2fr 1fr; gap:14px; }
.dup-scroll { max-height:260px; overflow:auto; border:1px solid #E5E7EB; border-radius:10px; }
.dup-tabla { width:100%; border-collapse:collapse; font-size:12px; }
.dup-tabla th { position:sticky; top:0; background:#EDF7F1; color:#0F5132; font-size:10px; text-transform:uppercase; letter-spacing:.3px; text-align:left; padding:6px 10px; }
.dup-tabla td { padding:6px 10px; border-top:1px solid #F3F4F6; color:#374151; }
.dup-fila { cursor:pointer; }
.dup-fila:hover { background:#F0FBF4; }
.dup-fila:focus-visible { outline:2px solid #31b079; outline-offset:-2px; }
.dup-fila.sel { background:#DDEFE4; }
.num { text-align:right !important; }
.b { font-weight:700; color:#111827; }
.nov { max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dup-n { background:#FEF3E2; color:#B45309; font-weight:800; border-radius:10px; padding:1px 9px; }
.dup-casos { min-width:0; }
.dup-casos-t { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.4px; margin-bottom:6px; }
.dup-lista { list-style:none; margin:0; padding:0; max-height:230px; overflow:auto; display:flex; flex-direction:column; gap:4px; }
.dup-lista li { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:11.5px; padding:4px 8px; border-radius:8px; background:#F9FAFB; }
.dup-id { font-weight:800; color:#C0392B; font-variant-numeric:tabular-nums; }
.dup-copia { color:#6B7280; }
.dup-casos-m { color:#374151; flex:1; min-width:140px; }
.dup-link { background:none; border:0; color:#0F5132; font-size:11px; font-weight:700; text-decoration:underline; cursor:pointer; font-family:inherit; padding:0; }
.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }
@media (max-width: 800px) { .dup-detalle { grid-template-columns:1fr; } }
</style>
