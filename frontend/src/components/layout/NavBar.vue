<!-- ═══════════════════════════════════════════════════════════════════════════════
     EMANTIX PRO — FASE 6 — Componente NavBar
     Barra de navegación de escritorio (>960px)
     ═══════════════════════════════════════════════════════════════════════════════ -->

<template>
  <nav class="topnav">
    <!-- Logo y Branding -->
    <div class="nav-brand">
      <img src="/icons/icon-192.png" alt="Logo EMANTIC" class="nav-logo" loading="lazy" />
      <div>
        <div class="nav-brand-name">EMANTIC</div>
        <div class="nav-brand-sub">SISTEMA TECNICO</div>
      </div>
    </div>

    <!-- Enlaces de Navegación -->
    <div class="nav-links">
      <!-- Dashboard -->
      <router-link to="/dashboard" class="nav-link nav-link--dashboard" title="Dashboard">
        <span class="nav-icon nav-icon--svg nav-icon--dashboard">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="3" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
            <rect x="14" y="3" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
            <rect x="3" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
            <rect x="14" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
          </svg>
        </span>
        Dashboard
      </router-link>

            <!-- Manuales -->
      <router-link to="/manuals" class="nav-link nav-link--manuals" title="Manuales">
        <span class="nav-icon nav-icon--svg nav-icon--manuals">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="rgba(255,255,255,0.06)"/>
          </svg>
        </span>
        Manuales
      </router-link>

      <!-- Repuestos -->
      <router-link to="/resources2" class="nav-link nav-link--resources" title="Repuestos">
        <span class="nav-icon nav-icon--svg nav-icon--resources">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(255,255,255,0.04)"/>
          </svg>
        </span>
        Repuestos
      </router-link>
      
      <!-- Mantenimiento -->
      <router-link to="/maintenance" class="nav-link nav-link--maintenance" title="Mantenimiento">
        <span class="nav-icon nav-icon--svg nav-icon--maintenance">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <circle cx="12" cy="12" r="3" fill="rgba(255,255,255,0.08)"/>
          </svg>
        </span>
        Mantenimiento
      </router-link>

      <!-- Documentación -->
      <router-link to="/documentation" class="nav-link nav-link--docs" title="Documentación">
        <span class="nav-icon nav-icon--svg nav-icon--docs">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" fill="rgba(255,255,255,0.04)"/>
          </svg>
        </span>
        Documentación
      </router-link>

      <!-- Recursos -->
      <router-link to="/resources" class="nav-link nav-link--resources" title="Recursos">
        <span class="nav-icon nav-icon--svg nav-icon--resources">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(255,255,255,0.04)"/>
          </svg>
        </span>
        Recursos
      </router-link>

      <!-- Analíticas -->
      <router-link to="/analytics" class="nav-link nav-link--analytics" title="Analíticas">
        <span class="nav-icon nav-icon--svg nav-icon--analytics">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="2" y="2" width="20" height="20" rx="3" fill="rgba(255,255,255,0.03)"/>
          </svg>
        </span>
        Analíticas
      </router-link>

      <!-- Reportes (si es admin) -->
      <router-link v-if="isAdmin" to="/reportes" class="nav-link nav-link--reports" title="Reportes">
        <span class="nav-icon nav-icon--svg nav-icon--reports">📊</span>
        Reportes
      </router-link>

      <!-- Admin (si es admin) -->
      <router-link v-if="isAdmin" to="/users" class="nav-link nav-link--users" title="Usuarios">
        <span class="nav-icon nav-icon--svg nav-icon--users">👥</span>
        Usuarios
      </router-link>
    </div>

    <!-- Perfil de Usuario -->
    <div class="nav-user">
      <div class="user-avatar">{{ userInitial }}</div>
      <div class="user-info">
        <div class="user-name">{{ username }}</div>
        <div class="user-role">{{ role }}</div>
      </div>
      <button class="logout-btn" @click="handleLogout" title="Cerrar Sesión">
        🚪
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/auth_optimized'

const router = useRouter()
const { state, logout, isAdmin } = useAuth()

const userInitial = computed(() => state.user?.name?.charAt(0).toUpperCase() || '?')
const username = computed(() => state.user?.username || 'Usuario')
const role = computed(() => state.user?.role === 'admin' ? 'Administrador' : 'Usuario')

const handleLogout = () => {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.topnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-bottom: 2px solid rgba(49, 176, 121, 0.3);
  padding: 16px 24px;
  gap: 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.nav-logo {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(49, 176, 121, 0.1);
  padding: 4px;
}

.nav-brand-name {
  font-weight: 700;
  font-size: 14px;
  color: #fff;
  letter-spacing: 1px;
}

.nav-brand-sub {
  font-size: 10px;
  color: rgba(49, 176, 121, 0.8);
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 8px;
  flex: 1;
  overflow-x: auto;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.3s ease;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 500;
}

.nav-link:hover {
  background: rgba(49, 176, 121, 0.15);
  color: #fff;
}

.nav-link.router-link-active {
  background: rgba(49, 176, 121, 0.25);
  color: #31b079;
  border-left: 3px solid #31b079;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  padding-left: 12px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(49, 176, 121, 0.3);
  border: 2px solid rgba(49, 176, 121, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #31b079;
  font-size: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
  font-size: 11px;
}

.user-name {
  color: #fff;
  font-weight: 500;
}

.user-role {
  color: rgba(49, 176, 121, 0.7);
  font-size: 10px;
}

.logout-btn {
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 6px;
  padding: 6px 10px;
  color: rgba(220, 53, 69, 0.8);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(220, 53, 69, 0.25);
  color: #dc3545;
}

@media (max-width: 960px) {
  .topnav { display: none; }
}
</style>
