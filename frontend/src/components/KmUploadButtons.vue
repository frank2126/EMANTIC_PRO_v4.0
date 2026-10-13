<template>
  <div class="km-up">
    <label class="btn-secondary km-btn" :class="{ busy }">⬆ Cargar kilometraje (Excel)
      <input type="file" hidden multiple accept=".xlsx,.csv" @change="subir($event, 'upload', 'files')" />
    </label>
    <label class="btn-secondary km-btn" :class="{ busy }">⬆ Informar intervenidos / programados
      <input type="file" hidden accept=".xlsx,.csv" @change="subir($event, 'seguimiento', 'file')" />
    </label>
    <span v-if="msg" class="km-msg" :class="{ err }">{{ msg }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
const emit = defineEmits(['done'])
const busy = ref(false), msg = ref(''), err = ref(false)

async function subir(e, ruta, campo) {
  const fs = [...e.target.files]; e.target.value = ''
  if (!fs.length) return
  const fd = new FormData(); fs.forEach(f => fd.append(campo, f))
  busy.value = true; err.value = false; msg.value = 'Procesando…'
  try {
    const d = (await axios.post(`/api/kilometraje/${ruta}`, fd)).data
    msg.value = ruta === 'upload'
      ? `✔ ${d.moviles} móviles · ${d.dias} días (${d.desde} → ${d.hasta}) · ${d.insertadas} nuevas, ${d.actualizadas} actualizadas`
      : `✔ ${d.aplicados} aplicados` + (d.no_aplicados.length ? ` · sin aplicar: ${d.no_aplicados.join(', ')}` : '')
    emit('done')
  } catch (x) {
    err.value = true; msg.value = x.response?.data?.detail || 'Error al procesar el archivo'
  } finally { busy.value = false }
}
</script>

<style scoped>
.km-up { display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:flex-end; }
.km-btn { cursor:pointer; user-select:none; }
.km-btn.busy { opacity:.6; pointer-events:none; }
.km-msg { font-size:12px; color:var(--primary); max-width:420px; }
.km-msg.err { color:var(--danger); }
</style>