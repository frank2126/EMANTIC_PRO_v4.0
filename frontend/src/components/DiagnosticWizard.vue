<template>
  <div class="diag-wizard" role="dialog" aria-label="Asistente de diagnóstico">
    <div class="diag-wizard-header">
      <span class="diag-wizard-eyebrow">Diagnóstico interactivo</span>
      <button class="diag-wizard-close" @click="$emit('close')" aria-label="Cerrar">✕</button>
    </div>

    <div class="diag-wizard-path" v-if="history.length">
      <span v-for="(h, i) in history" :key="i" class="diag-crumb" :title="`Paso ${i + 1}`"></span>
      <span class="diag-crumb diag-crumb-current" title="Paso actual"></span>
    </div>

    <div class="diag-wizard-body">
      <template v-if="currentNode">
        <p class="diag-node-text">{{ currentNode.text }}</p>

        <!-- Nodo de decisión: un botón por rama -->
        <div v-if="currentNode.type === 'decision'" class="diag-branches">
          <button
            v-for="(b, i) in currentNode.branches"
            :key="i"
            class="btn-secondary diag-branch-btn"
            @click="choose(b)"
          >
            {{ b.label }}
          </button>
        </div>

        <!-- Nodo de acción: siguiente paso o fin de rama -->
        <div v-else class="diag-action-footer">
          <button v-if="currentNode.next" class="btn-primary" @click="advance(currentNode.next)">
            Siguiente paso →
          </button>
          <div v-else class="diag-end">
            <span class="diag-end-icon">✓</span>
            <span>Fin del diagnóstico para esta rama.</span>
          </div>
        </div>
      </template>
      <p v-else class="diag-node-text">No se encontró el nodo de diagnóstico.</p>
    </div>

    <div class="diag-wizard-actions">
      <button class="btn-secondary btn-sm" :disabled="!history.length" @click="goBack">← Paso anterior</button>
      <button class="btn-secondary btn-sm" @click="reset">Reiniciar</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // Estructura esperada: { start_node: "n1", nodes: { n1: {type, text, branches|next}, ... } }
  tree: { type: Object, required: true },
})
defineEmits(['close'])

const currentNodeId = ref(props.tree.start_node)
const history = ref([])

const currentNode = computed(() => props.tree.nodes[currentNodeId.value] || null)

function advance(nextId) {
  history.value.push(currentNodeId.value)
  currentNodeId.value = nextId
}
function choose(branch) {
  if (branch.next) advance(branch.next)
}
function goBack() {
  const prev = history.value.pop()
  if (prev) currentNodeId.value = prev
}
function reset() {
  history.value = []
  currentNodeId.value = props.tree.start_node
}

// Si cambia el sistema (nuevo árbol), reiniciar el asistente
watch(() => props.tree, () => reset())
</script>

<style scoped>
.diag-wizard {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: 22px;
  width: 100%;
  max-width: 560px;
}
.diag-wizard-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.diag-wizard-eyebrow { font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; color: var(--primary); }
.diag-wizard-close { background:none; border:none; cursor:pointer; font-size:16px; color: var(--text-muted); line-height:1; }
.diag-wizard-close:hover { color: var(--text); }

.diag-wizard-path { display:flex; gap:4px; margin-bottom:16px; }
.diag-crumb { width:8px; height:8px; border-radius:50%; background: var(--border); }
.diag-crumb-current { background: var(--primary); }

.diag-wizard-body { min-height: 100px; }
.diag-node-text { font-size:15px; font-weight:600; color: var(--text); line-height:1.5; margin-bottom:16px; }

.diag-branches { display:flex; flex-direction:column; gap:8px; }
.diag-branch-btn { text-align:left; }

.diag-action-footer { display:flex; align-items:center; }
.diag-end { display:flex; align-items:center; gap:8px; color: var(--success); font-weight:600; font-size:14px; }
.diag-end-icon {
  width:22px; height:22px; border-radius:50%; background: var(--success); color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:12px; flex-shrink:0;
}

.diag-wizard-actions {
  display:flex; justify-content:space-between; margin-top:20px;
  padding-top:14px; border-top:1px solid var(--border);
}
</style>