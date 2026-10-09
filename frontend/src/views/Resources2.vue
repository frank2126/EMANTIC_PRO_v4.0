<template>
  <div class="resources-container">
    <!-- Header -->
    <div class="header-section">
      <h1>Repuestos y Piezas</h1>
      <p class="subtitle">Catálogo completo de repuestos disponibles</p>
    </div>

    <!-- Controles -->
    <div class="controls-section">
      <!-- Búsqueda Rápida -->
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por código, descripción, marca..."
          class="search-input"
          @input="performSearch"
        />
        <span class="search-icon">🔍</span>
      </div>

      <!-- Botón Cargar Excel -->
      <div class="upload-section">
        <label class="upload-btn">
          Cargar Excel
          <input
            type="file"
            accept=".xlsx,.xls"
            @change="handleExcelUpload"
            style="display: none"
          />
        </label>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters-section">
      <div class="filter-group">
        <select v-model="filterClase" @change="applyFilters" class="filter-select">
          <option value="">Todas las Clases</option>
          <option v-for="clase in clases" :key="clase" :value="clase">
            {{ clase }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <select v-model="filterNivel" @change="applyFilters" class="filter-select">
          <option value="">Todos los Niveles</option>
          <option v-for="nivel in niveles" :key="nivel" :value="nivel">
            {{ nivel }}
          </option>
        </select>
      </div>

      <!-- Información -->
      <div class="info-text">
        {{ displayInfo }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Buscando repuestos...</p>
    </div>

    <!-- Tabla de Repuestos -->
    <div v-else class="table-container">
      <table class="repuestos-table">
        <thead>
          <tr>
            <th>Código</th>
            <th>Descripción</th>
            <th>Clase</th>
            <th>Sistema</th>
            <th>UDM</th>
            <th>Fabricante</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredRepuestos.length === 0" class="no-data">
            <td colspan="7">
              <p>No se encontraron repuestos</p>
            </td>
          </tr>
          <tr v-for="repuesto in filteredRepuestos" :key="repuesto.id" class="table-row">
            <td class="codigo">
              <strong>{{ repuesto.pieza }}</strong>
            </td>
            <td class="descripcion">{{ repuesto.descripcion }}</td>
            <td class="clase">
              <span class="badge">{{ repuesto.clase }}</span>
            </td>
            <td class="nivel">{{ repuesto.nivel_sistema }}</td>
            <td class="udm">{{ repuesto.udm }}</td>
            <td class="fabricante">{{ repuesto.numero_pieza_fabricante || "—" }}</td>
            <td class="acciones">
              <button
                @click="copiarCodigo(repuesto.pieza)"
                class="btn-copy"
                :title="`Copiar ${repuesto.pieza}`"
              >
                📋 Copiar
              </button>
              <button
                @click="verDetalles(repuesto)"
                class="btn-detail"
                title="Ver detalles"
              >
                👁️ Ver
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación -->
    <div v-if="!loading && filteredRepuestos.length > 0" class="pagination">
      <button
        :disabled="paginaActual === 1"
        @click="paginaActual--"
        class="btn-pagination"
      >
        ← Anterior
      </button>
      <span class="page-info">Página {{ paginaActual }} de {{ totalPaginas }}</span>
      <button
        :disabled="paginaActual >= totalPaginas"
        @click="paginaActual++"
        class="btn-pagination"
      >
        Siguiente →
      </button>
    </div>

    <!-- Modal Detalles -->
    <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
      <div class="modal-content" @click.stop>
        <button class="modal-close" @click="showDetailModal = false">✕</button>
        
        <h2>{{ selectedRepuesto.pieza }}</h2>
        <p class="modal-descripcion">{{ selectedRepuesto.descripcion }}</p>

        <div class="modal-grid">
          <div class="modal-item">
            <strong>Clase:</strong>
            <p>{{ selectedRepuesto.clase }}</p>
          </div>
          <div class="modal-item">
            <strong>Sistema:</strong>
            <p>{{ selectedRepuesto.nivel_sistema }}</p>
          </div>
          <div class="modal-item">
            <strong>Unidad:</strong>
            <p>{{ selectedRepuesto.udm }}</p>
          </div>
          <div class="modal-item">
            <strong>Fabricante:</strong>
            <p>{{ selectedRepuesto.numero_pieza_fabricante || "—" }}</p>
          </div>
          <div class="modal-item">
            <strong>Jerarquía:</strong>
            <p>{{ selectedRepuesto.jerarquia_pieza || "—" }}</p>
          </div>
          <div class="modal-item">
            <strong>Suministrador:</strong>
            <p>{{ selectedRepuesto.suministrador_sugerido || "—" }}</p>
          </div>
          <div class="modal-item">
            <strong>Montaje:</strong>
            <p>{{ selectedRepuesto.nivel_montaje || "—" }}</p>
          </div>
          <div class="modal-item">
            <strong>Componente:</strong>
            <p>{{ selectedRepuesto.nivel_componente || "—" }}</p>
          </div>
        </div>

        <div class="modal-actions">
          <button
            @click="copiarCodigo(selectedRepuesto.pieza)"
            class="btn-modal-copy"
          >
            📋 Copiar Código
          </button>
          <button
            @click="showDetailModal = false"
            class="btn-modal-close"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notificación -->
    <div v-if="showToast" class="toast" :class="toastType">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "@/auth.js";

// Estado
const searchQuery = ref("");
const filterClase = ref("");
const filterNivel = ref("");
const allRepuestos = ref([]);
const clases = ref([]);
const niveles = ref([]);
const loading = ref(false);
const paginaActual = ref(1);
const itemsPorPagina = 50;

// Modal y Notificaciones
const showDetailModal = ref(false);
const selectedRepuesto = ref(null);
const showToast = ref(false);
const toastMessage = ref("");
const toastType = ref("success");

// ═══════════════════════════════════════════════════════════
// Búsqueda
// ═══════════════════════════════════════════════════════════

const performSearch = async () => {
  paginaActual.value = 1;
  
  if (searchQuery.value.length < 2) {
    loadAllRepuestos();
    return;
  }

  loading.value = true;
  try {
    const response = await api.get(
      `/api/repuestos/search/${searchQuery.value}?limit=100`
    );
    
    if (response.data.success) {
      allRepuestos.value = response.data.data;
    }
  } catch (error) {
    mostrarToast("Error en la búsqueda", "error");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// ═══════════════════════════════════════════════════════════
// Cargar Todos
// ═══════════════════════════════════════════════════════════

const loadAllRepuestos = async () => {
  loading.value = true;
  try {
    const response = await api.get("/api/repuestos/?skip=0&limit=100");
    
    if (response.data.success) {
      allRepuestos.value = response.data.data;
    }
  } catch (error) {
    mostrarToast("Error al cargar repuestos", "error");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// ═══════════════════════════════════════════════════════════
// Cargar Filtros
// ═══════════════════════════════════════════════════════════

const loadFiltros = async () => {
  try {
    const [clasesRes, nivelesRes] = await Promise.all([
      api.get("/api/repuestos/filtros/clases"),
      api.get("/api/repuestos/filtros/niveles-sistema")
    ]);

    if (clasesRes.data.success) {
      clases.value = clasesRes.data.data;
    }
    if (nivelesRes.data.success) {
      niveles.value = nivelesRes.data.data;
    }
  } catch (error) {
    console.error("Error al cargar filtros:", error);
  }
};

// ═══════════════════════════════════════════════════════════
// Aplicar Filtros
// ═══════════════════════════════════════════════════════════

const applyFilters = () => {
  paginaActual.value = 1;
  // Los filtros se aplican en el computed
};

// ═══════════════════════════════════════════════════════════
// Repuestos Filtrados
// ═══════════════════════════════════════════════════════════

const filteredRepuestos = computed(() => {
  let result = allRepuestos.value;

  if (filterClase.value) {
    result = result.filter((r) => r.clase === filterClase.value);
  }

  if (filterNivel.value) {
    result = result.filter((r) => r.nivel_sistema === filterNivel.value);
  }

  // Paginación
  const inicio = (paginaActual.value - 1) * itemsPorPagina;
  const fin = inicio + itemsPorPagina;

  return result.slice(inicio, fin);
});

const totalPaginas = computed(() => {
  let result = allRepuestos.value;

  if (filterClase.value) {
    result = result.filter((r) => r.clase === filterClase.value);
  }

  if (filterNivel.value) {
    result = result.filter((r) => r.nivel_sistema === filterNivel.value);
  }

  return Math.ceil(result.length / itemsPorPagina);
});

const displayInfo = computed(() => {
  const total = allRepuestos.value.length;
  const mostrados = filteredRepuestos.value.length;
  
  if (searchQuery.value) {
    return `${mostrados} resultados para "${searchQuery.value}"`;
  }
  
  return `Total: ${total} repuestos`;
});

// ═══════════════════════════════════════════════════════════
// Acciones
// ═══════════════════════════════════════════════════════════

const copiarCodigo = (codigo) => {
  navigator.clipboard.writeText(codigo);
  mostrarToast(`Código ${codigo} copiado al portapapeles`, "success");
};

const verDetalles = (repuesto) => {
  selectedRepuesto.value = repuesto;
  showDetailModal.value = true;
};

const handleExcelUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  loading.value = true;
  try {
    const response = await api.post("/api/repuestos/upload-excel", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });

    if (response.data.success) {
      mostrarToast(
        `Cargados: ${response.data.stats.insertados} | Actualizados: ${response.data.stats.actualizados}`,
        "success"
      );
      await loadAllRepuestos();
      await loadFiltros();
    }
  } catch (error) {
    mostrarToast("Error al cargar el Excel", "error");
    console.error(error);
  } finally {
    loading.value = false;
    event.target.value = "";
  }
};

// ═══════════════════════════════════════════════════════════
// Toast Notificación
// ═══════════════════════════════════════════════════════════

const mostrarToast = (message, type = "success") => {
  toastMessage.value = message;
  toastType.value = type;
  showToast.value = true;

  setTimeout(() => {
    showToast.value = false;
  }, 3000);
};

// ═══════════════════════════════════════════════════════════
// Ciclo de vida
// ═══════════════════════════════════════════════════════════

onMounted(() => {
  loadAllRepuestos();
  loadFiltros();
});
</script>

<style scoped>
.resources-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* Header */
.header-section {
  margin-bottom: 30px;
}

.header-section h1 {
  font-size: 28px;
  color: #1a1a1a;
  margin: 0 0 5px 0;
}

.subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
}

/* Controles */
.controls-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.search-box {
  flex: 1;
  max-width: 500px;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  font-size: 18px;
}

.upload-section {
  display: flex;
}

.upload-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

/* Filtros */
.filters-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-group {
  flex: 1;
  min-width: 180px;
}

.filter-select {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-select:focus {
  outline: none;
  border-color: #4a90e2;
}

.info-text {
  color: #666;
  font-size: 13px;
  white-space: nowrap;
}

/* Loading */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top: 4px solid #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Tabla */
.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.repuestos-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.repuestos-table thead {
  background: #f5f7fa;
  border-bottom: 2px solid #e0e0e0;
}

.repuestos-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  color: #1a1a1a;
}

.repuestos-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e0e0e0;
}

.table-row:hover {
  background: #fafbfc;
}

.codigo {
  font-weight: 700;
  color: #4a90e2;
  min-width: 100px;
}

.descripcion {
  max-width: 250px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.clase {
  min-width: 80px;
}

.badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.nivel {
  min-width: 100px;
}

.udm {
  min-width: 50px;
  text-align: center;
}

.fabricante {
  max-width: 150px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.acciones {
  display: flex;
  gap: 8px;
  min-width: 150px;
}

.btn-copy,
.btn-detail {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-copy {
  background: #f0f0f0;
  color: #333;
}

.btn-copy:hover {
  background: #e0e0e0;
}

.btn-detail {
  background: #e8f4f8;
  color: #0066cc;
}

.btn-detail:hover {
  background: #d0e8f0;
}

.no-data {
  text-align: center;
}

.no-data td {
  padding: 40px 15px;
  color: #999;
  font-size: 14px;
}

/* Paginación */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}

.btn-pagination {
  padding: 10px 15px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-pagination:hover:not(:disabled) {
  border-color: #4a90e2;
  color: #4a90e2;
}

.btn-pagination:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-weight: 600;
  min-width: 150px;
  text-align: center;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-close:hover {
  color: #333;
}

.modal-content h2 {
  margin: 0 0 5px 0;
  color: #1a1a1a;
  font-size: 22px;
}

.modal-descripcion {
  color: #666;
  margin: 0 0 20px 0;
  font-size: 14px;
}

.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.modal-item {
  display: flex;
  flex-direction: column;
}

.modal-item strong {
  color: #666;
  font-size: 12px;
  margin-bottom: 5px;
}

.modal-item p {
  margin: 0;
  color: #1a1a1a;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-modal-copy,
.btn-modal-close {
  padding: 10px 15px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-modal-copy {
  background: #4a90e2;
  color: white;
}

.btn-modal-copy:hover {
  background: #357abd;
}

.btn-modal-close {
  background: #f0f0f0;
  color: #333;
}

.btn-modal-close:hover {
  background: #e0e0e0;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 6px;
  color: white;
  font-weight: 600;
  animation: slideIn 0.3s ease;
  z-index: 2000;
  max-width: 300px;
}

.toast.success {
  background: #4caf50;
}

.toast.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .controls-section {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: 100%;
  }

  .filters-section {
    flex-direction: column;
  }

  .filter-group {
    min-width: auto;
  }

  .repuestos-table {
    font-size: 12px;
  }

  .repuestos-table th,
  .repuestos-table td {
    padding: 10px;
  }

  .acciones {
    flex-direction: column;
    min-width: auto;
  }

  .modal-grid {
    grid-template-columns: 1fr;
  }
}
</style>