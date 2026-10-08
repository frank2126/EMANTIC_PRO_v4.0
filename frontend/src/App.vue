"<template>
  <!-- Layout autenticado -->
  <div v-if="isLoggedIn()">

    <!-- ── Navbar escritorio ── -->
    <nav class="topnav">
      <div class="nav-brand">
        <img src="/icons/icon-192.png" alt="Logo" class="nav-logo" />
        <div>
          <div class="nav-brand-name">EMANTIC</div>
          <div class="nav-brand-sub">SISTEMA TECNICO</div>
        </div>
      </div>

      <div class="nav-links">
        <!-- Dashboard -->
        <router-link to="/dashboard" class="nav-link nav-link--dashboard">
          <span class="nav-icon nav-icon--svg nav-icon--dashboard">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
              <rect x="14" y="3" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
              <rect x="3" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.08)"/>
              <line x1="6" y1="6" x2="7" y2="6" stroke-width="2"/>
              <line x1="17" y1="6" x2="18" y2="6" stroke-width="2"/>
              <line x1="6" y1="17" x2="7" y2="17" stroke-width="2"/>
              <line x1="17" y1="17" x2="18" y2="17" stroke-width="2"/>
            </svg>
          </span>
          Dashboard
        </router-link>

        <!-- Manuales -->
        <router-link to="/manuals" class="nav-link nav-link--manuals">
          <span class="nav-icon nav-icon--svg nav-icon--manuals">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="rgba(255,255,255,0.06)"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <line x1="10" y1="9" x2="8" y2="9"/>
              <circle cx="18" cy="18" r="3" fill="rgba(49,176,121,0.2)" stroke="rgba(49,176,121,0.6)"/>
              <path d="M17 18l1 1 2-2" stroke="rgba(49,176,121,0.8)" stroke-width="1.5"/>
            </svg>
          </span>
          Manuales
        </router-link>

        <!-- Mantenimiento -->
        <router-link to="/maintenance" class="nav-link nav-link--maintenance">
          <span class="nav-icon nav-icon--svg nav-icon--maintenance">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" fill="rgba(255,255,255,0.08)"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              <circle cx="12" cy="12" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/>
            </svg>
          </span>
          Mantenimiento
        </router-link>

        <!-- Documentación -->
        <router-link to="/documentation" class="nav-link nav-link--docs">
          <span class="nav-icon nav-icon--svg nav-icon--docs">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" fill="rgba(255,255,255,0.04)"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" fill="rgba(255,255,255,0.04)"/>
              <line x1="8" y1="6" x2="16" y2="6"/>
              <line x1="8" y1="10" x2="14" y2="10"/>
              <line x1="8" y1="14" x2="12" y2="14"/>
              <path d="M16 2v6l3-3-3-3z" fill="rgba(49,176,121,0.15)" stroke="rgba(49,176,121,0.5)"/>
            </svg>
          </span>
          Documentación
        </router-link>

        <!-- Recursos Taller -->
        <router-link to="/resources" class="nav-link nav-link--resources">
          <span class="nav-icon nav-icon--svg nav-icon--resources">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(255,255,255,0.04)"/>
              <circle cx="12" cy="11" r="3" fill="rgba(49,176,121,0.1)"/>
              <path d="M12 8v6" stroke-width="1.5"/>
              <path d="M9 11h6" stroke-width="1.5"/>
              <path d="M12 14l-1.5 2" stroke-width="1.2"/>
              <path d="M12 14l1.5 2" stroke-width="1.2"/>
            </svg>
          </span>
          Recursos Taller
        </router-link>

        <!-- Analíticas -->
        <router-link to="/analytics" class="nav-link nav-link--analytics">
          <span class="nav-icon nav-icon--svg nav-icon--analytics">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="3" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
              <circle cx="18" cy="8" r="1.5" fill="rgba(49,176,121,0.6)" stroke="none"/>
              <circle cx="12" cy="5" r="1.5" fill="rgba(49,176,121,0.6)" stroke="none"/>
              <circle cx="6" cy="12" r="1.5" fill="rgba(49,176,121,0.6)" stroke="none"/>
              <path d="M6 12l6-7 6 3" stroke="rgba(49,176,121,0.4)" stroke-width="1" stroke-dasharray="2 2"/>
            </svg>
          </span>
          Analíticas
        </router-link>

        <!-- Reportes -->
        <router-link to="/reportes" class="nav-link nav-link--reports">
          <span class="nav-icon nav-icon--svg nav-icon--reports">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.21 15.89A10 10 0 1 1 8 2.83" fill="rgba(255,255,255,0.03)"/>
              <path d="M22 12A10 10 0 0 0 12 2v10z" fill="rgba(49,176,121,0.1)"/>
              <circle cx="12" cy="12" r="2" fill="rgba(49,176,121,0.3)"/>
              <line x1="12" y1="12" x2="12" y2="7" stroke-width="1.5"/>
              <line x1="12" y1="12" x2="16" y2="12" stroke-width="1.5"/>
              <path d="M18 6l1-1" stroke-width="1.2"/>
              <path d="M19 7l1 1" stroke-width="1.2"/>
            </svg>
          </span>
          Reportes
        </router-link>

        <!-- Carga DPV -->
        <router-link v-if="isAdmin()" to="/dpv" class="nav-link nav-link--dpv">
          <span class="nav-icon nav-icon--svg nav-icon--dpv">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" fill="rgba(255,255,255,0.03)"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
              <rect x="9" y="15" width="6" height="3" rx="1" fill="rgba(49,176,121,0.15)" stroke="rgba(49,176,121,0.5)"/>
              <line x1="11" y1="16.5" x2="13" y2="16.5" stroke="rgba(49,176,121,0.8)" stroke-width="1"/>
            </svg>
          </span>
          Carga DPV
        </router-link>

        <!-- ICO -->
        <router-link to="/ico" class="nav-link nav-link--ico">
          <span class="nav-icon nav-icon--svg nav-icon--ico">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v4" stroke-width="2"/>
              <path d="M12 18v4" stroke-width="2"/>
              <path d="M4.93 4.93l2.83 2.83" stroke-width="2"/>
              <path d="M16.24 16.24l2.83 2.83" stroke-width="2"/>
              <path d="M2 12h4" stroke-width="2"/>
              <path d="M18 12h4" stroke-width="2"/>
              <path d="M4.93 19.07l2.83-2.83" stroke-width="2"/>
              <path d="M16.24 7.76l2.83-2.83" stroke-width="2"/>
              <circle cx="12" cy="12" r="4" fill="rgba(49,176,121,0.1)" stroke="rgba(49,176,121,0.5)"/>
              <circle cx="12" cy="12" r="1.5" fill="rgba(49,176,121,0.6)" stroke="none"/>
            </svg>
          </span>
          ICO
        </router-link>

        <!-- Usuarios -->
        <router-link v-if="isAdmin()" to="/users" class="nav-link nav-link--users">
          <span class="nav-icon nav-icon--svg nav-icon--users">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" fill="rgba(255,255,255,0.04)"/>
              <circle cx="9" cy="7" r="4" fill="rgba(255,255,255,0.06)"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke-width="1.2"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke-width="1.2"/>
            </svg>
          </span>
          Usuarios
        </router-link>
      </div>

      <div class="nav-user">
        <div class="nav-user-info">
          <span class="nav-user-name">{{ state.user?.name }}</span>
          <span class="nav-user-role">{{ state.user?.role === 'admin' ? 'Administrador' : 'Técnico' }}</span>
        </div>
        <div class="nav-avatar" @click="menuOpen = !menuOpen">
          {{ userInitial }}
          <div v-if="menuOpen" class="user-menu" @click.stop>
            <div class="user-menu-header">
              <strong>{{ state.user?.name }}</strong>
              <span>@{{ state.user?.username }}</span>
            </div>
            <button class="user-menu-item danger" @click="handleLogout">⏻ Cerrar sesión</button>
          </div>
        </div>
      </div>
    </nav>

    <div v-if="menuOpen" class="overlay-transparent" @click="menuOpen = false"></div>

    <!-- ── Header móvil ── -->
    <header class="mobile-header">
      <div class="mh-brand">
        <img src="/icons/icon-192.png" alt="Logo" class="mh-logo" />
        <span class="mh-name">EMANTIC</span>
      </div>
      <button class="mh-btn" @click="drawerOpen = !drawerOpen">☰</button>
    </header>

    <!-- ── Drawer móvil ── -->
    <transition name="drawer">
      <div v-if="drawerOpen" class="drawer-overlay" @click="drawerOpen = false">
        <div class="drawer" @click.stop>
          <div class="drawer-header">
            <img src="/icons/icon-192.png" alt="Logo" class="drawer-logo" />
            <div>
              <div class="drawer-name">{{ state.user?.name }}</div>
              <div class="drawer-role">{{ state.user?.role }}</div>
            </div>
          </div>

          <!-- Dashboard -->
          <router-link to="/dashboard" class="drawer-link drawer-link--dashboard" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--dashboard">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1.5" fill="rgba(49,176,121,0.08)"/>
                <rect x="14" y="3" width="7" height="7" rx="1.5" fill="rgba(49,176,121,0.08)"/>
                <rect x="3" y="14" width="7" height="7" rx="1.5" fill="rgba(49,176,121,0.08)"/>
                <rect x="14" y="14" width="7" height="7" rx="1.5" fill="rgba(49,176,121,0.08)"/>
                <line x1="6" y1="6" x2="7" y2="6" stroke-width="2"/>
                <line x1="17" y1="6" x2="18" y2="6" stroke-width="2"/>
              </svg>
            </span>
            Dashboard
          </router-link>

          <!-- Manuales -->
          <router-link to="/manuals" class="drawer-link drawer-link--manuals" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--manuals">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="rgba(49,176,121,0.06)"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <circle cx="18" cy="18" r="2.5" fill="rgba(49,176,121,0.15)" stroke="rgba(49,176,121,0.5)"/>
                <path d="M17 18l1 1 1.5-1.5" stroke="rgba(49,176,121,0.8)" stroke-width="1.5"/>
              </svg>
            </span>
            Manuales Técnicos
          </router-link>

          <!-- Mantenimiento -->
          <router-link to="/maintenance" class="drawer-link drawer-link--maintenance" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--maintenance">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3" fill="rgba(49,176,121,0.08)"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                <circle cx="12" cy="12" r="1.5" fill="rgba(49,176,121,0.6)" stroke="none"/>
              </svg>
            </span>
            Mantenimiento
          </router-link>

          <!-- Documentación -->
          <router-link to="/documentation" class="drawer-link drawer-link--docs" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--docs">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" fill="rgba(49,176,121,0.04)"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" fill="rgba(49,176,121,0.04)"/>
                <line x1="8" y1="6" x2="16" y2="6"/>
                <line x1="8" y1="10" x2="14" y2="10"/>
                <line x1="8" y1="14" x2="12" y2="14"/>
                <path d="M16 2v6l3-3-3-3z" fill="rgba(49,176,121,0.12)" stroke="rgba(49,176,121,0.4)"/>
              </svg>
            </span>
            Documentación
          </router-link>

          <!-- Recursos Taller -->
          <router-link to="/resources" class="drawer-link drawer-link--resources" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--resources">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(49,176,121,0.04)"/>
                <circle cx="12" cy="11" r="3" fill="rgba(49,176,121,0.08)"/>
                <path d="M12 8v6" stroke-width="1.5"/>
                <path d="M9 11h6" stroke-width="1.5"/>
                <path d="M12 14l-1.5 2" stroke-width="1.2"/>
                <path d="M12 14l1.5 2" stroke-width="1.2"/>
              </svg>
            </span>
            Recursos Taller
          </router-link>

          <!-- Analíticas -->
          <router-link to="/analytics" class="drawer-link drawer-link--analytics" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--analytics">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="2" width="20" height="20" rx="3" fill="rgba(49,176,121,0.03)" stroke="rgba(49,176,121,0.15)" stroke-width="1"/>
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
                <circle cx="18" cy="8" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/>
                <circle cx="12" cy="5" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/>
                <circle cx="6" cy="12" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/>
                <path d="M6 12l6-7 6 3" stroke="rgba(49,176,121,0.3)" stroke-width="1" stroke-dasharray="2 2"/>
              </svg>
            </span>
            Analíticas
          </router-link>

          <!-- Reportes -->
          <router-link to="/reportes" class="drawer-link drawer-link--reports" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--reports">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.21 15.89A10 10 0 1 1 8 2.83" fill="rgba(49,176,121,0.03)"/>
                <path d="M22 12A10 10 0 0 0 12 2v10z" fill="rgba(49,176,121,0.08)"/>
                <circle cx="12" cy="12" r="2" fill="rgba(49,176,121,0.25)"/>
                <line x1="12" y1="12" x2="12" y2="7" stroke-width="1.5"/>
                <line x1="12" y1="12" x2="16" y2="12" stroke-width="1.5"/>
                <path d="M18 6l1-1" stroke-width="1.2"/>
                <path d="M19 7l1 1" stroke-width="1.2"/>
              </svg>
            </span>
            Reportes
          </router-link>

          <!-- Carga DPV -->
          <router-link to="/dpv" class="drawer-link drawer-link--dpv" v-if="isAdmin()" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--dpv">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" fill="rgba(49,176,121,0.03)"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
                <rect x="9" y="15" width="6" height="3" rx="1" fill="rgba(49,176,121,0.12)" stroke="rgba(49,176,121,0.4)"/>
                <line x1="11" y1="16.5" x2="13" y2="16.5" stroke="rgba(49,176,121,0.7)" stroke-width="1"/>
              </svg>
            </span>
            Carga DPV
          </router-link>

          <!-- ICO -->
          <router-link to="/ico" class="drawer-link drawer-link--ico" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--ico">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v4" stroke-width="2"/>
                <path d="M12 18v4" stroke-width="2"/>
                <path d="M4.93 4.93l2.83 2.83" stroke-width="2"/>
                <path d="M16.24 16.24l2.83 2.83" stroke-width="2"/>
                <path d="M2 12h4" stroke-width="2"/>
                <path d="M18 12h4" stroke-width="2"/>
                <path d="M4.93 19.07l2.83-2.83" stroke-width="2"/>
                <path d="M16.24 7.76l2.83-2.83" stroke-width="2"/>
                <circle cx="12" cy="12" r="4" fill="rgba(49,176,121,0.08)" stroke="rgba(49,176,121,0.4)"/>
                <circle cx="12" cy="12" r="1.5" fill="rgba(49,176,121,0.5)" stroke="none"/>
              </svg>
            </span>
            ICO
          </router-link>

          <!-- Usuarios -->
          <router-link v-if="isAdmin()" to="/users" class="drawer-link drawer-link--users" @click="drawerOpen=false">
            <span class="drawer-icon drawer-icon--svg drawer-icon--users">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" fill="rgba(49,176,121,0.04)"/>
                <circle cx="9" cy="7" r="4" fill="rgba(49,176,121,0.06)"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke-width="1.2"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke-width="1.2"/>
              </svg>
            </span>
            Usuarios
          </router-link>

          <button class="drawer-logout" @click="handleLogout">⏻ Cerrar sesión</button>
        </div>
      </div>
    </transition>

    <!-- ── Contenido principal ── -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- ── Footer ── -->
    <footer class="app-footer">
      <div class="footer-main">

        <div class="footer-col footer-brand">
          <div class="footer-logo-row">
            <div class="footer-logo-icon">
              <svg viewBox="0 0 40 40" width="40" height="40" xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="10" fill="#31b079"/>
                <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
                  font-size="14" font-weight="900" fill="#fff" font-family="Arial">E</text>
              </svg>
            </div>
            <div>
              <div class="footer-brand-name">EMANTIX</div>
              <div class="footer-brand-sub">Sistema Técnico Automotriz</div>
            </div>
          </div>
          <p class="footer-desc">
            Plataforma de gestión técnica de flota desarrollada para
            <strong>Emasivo Capital</strong>. Integra manuales, mantenimiento,
            documentación y analíticas en un solo sistema.
          </p>
          <div class="footer-socials">
            <a href="https://www.linkedin.com/company/emasivobog/" target="_blank" rel="noopener noreferrer" class="social-btn" title="LinkedIn">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
            </a>
              <a href="https://www.facebook.com/Emasivo1016.SAS" target="_blank" rel="noopener noreferrer" class="social-btn" title="Facebook">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
             </a>
            <a href="https://www.tiktok.com/@emasivo10_16s.a.s" target="_blank" rel="noopener noreferrer" class="social-btn" title="TikTok">
             <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
               <path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0115.54 3h-3.09v12.4a2.592 2.592 0 01-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 004.3 1.38V7.3s-1.88.09-3.24-1.48z"/>
             </svg>
            </a>
          </div>
        </div>

        <div class="footer-col">
          <h4 class="footer-col-title">Flota</h4>
          <ul class="footer-links">
            <li><span>🚌</span> Unidades Z32 (UF-10)</li>
            <li><span>🚌</span> Unidades Z34 (UF-16)</li>
            <li><span>🚌</span> Flota UF-17</li>
            <li><span>🔧</span> Mantenimiento Preventivo</li>
            <li><span>🔧</span> Mantenimiento Correctivo</li>
            <li><span>📊</span> Historial de Flota</li>
          </ul>
        </div>

        <div class="footer-col">
          <h4 class="footer-col-title">Sistemas</h4>
          <ul class="footer-links">
            <li><span>⚙️</span> Motor y Transmisión</li>
            <li><span>🛑</span> Sistema de Frenos</li>
            <li><span>⚡</span> Sistema Eléctrico</li>
            <li><span>🔄</span> Suspensión</li>
            <li><span>🚌</span> Carrocería y Chasis</li>
            <li><span>💻</span> Diagnóstico ECU</li>
          </ul>
        </div>

        <div class="footer-col">
          <h4 class="footer-col-title">Recursos</h4>
          <ul class="footer-links">
            <li><span>📋</span> Manuales Técnicos</li>
            <li><span>📁</span> Documentación</li>
            <li><span>🔍</span> Códigos DTC</li>
            <li><span>💧</span> Tabla de Fluidos</li>
            <li><span>📈</span> Analíticas</li>
            <li><span>📊</span> Reportes de Campo</li>
          </ul>
        </div>

        <div class="footer-col">
          <h4 class="footer-col-title">Emasivo Capital</h4>
          <ul class="footer-links">
            <li><span>🏢</span> Sobre nosotros</li>
            <li><span>📍</span> Punto de Inicio de Ruta (PIR) Bilbao Calle 144 #148-10</li>
            <li><span>📍</span> Centro de Operación La Gaitana Carrera 129 # 132- 30</li>
            <li><span>📍</span> Centro de Operación San Andrés 500 M Puente Guadua Calle 80 Autopista Bogotá – Villeta sentido Occidente – Oriente</li>
            <li><span>👥</span> Equipo técnico</li>
            <li><span>📞</span> Línea de Contacto (+57) 317 329 09 93</li>
            <li><span>🛡️</span> Política de calidad</li>
          </ul>
        </div>

      </div>

      <div class="footer-bottom">
        <div class="footer-bottom-left">
          <span>© {{ currentYear }} Emasivo Capital. Todos los derechos reservados.</span>
          <span class="footer-dot">·</span>
          <span>Emantix Pro v4.0</span>
        </div>
        <div class="footer-bottom-right">
          <span>Aviso de privacidad</span>
          <span class="footer-dot">·</span>
          <span>Términos de uso</span>
          <span class="footer-dot">·</span>
          <span>Certificación ISO 9001</span>
          <span class="footer-dot">·</span>
          <span>RTM</span>
        </div>
      </div>
    </footer>

  </div>

  <!-- Login sin navbar -->
  <router-view v-else />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './auth.js'

const router      = useRouter()
const { state, logout, isAdmin, isLoggedIn } = useAuth()
const menuOpen    = ref(false)
const drawerOpen  = ref(false)
const userInitial = computed(() => state.user?.name?.charAt(0).toUpperCase() || '?')
const currentYear = computed(() => new Date().getFullYear())

const handleLogout = () => {
  logout()
  menuOpen.value  = false
  drawerOpen.value = false
  router.push('/login')
}
</script>

<style scoped>
/* ══ NAVBAR ══════════════════════════════════════════════════════ */
.topnav {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--nav-h); z-index: 100;
  background: var(--primary);                        /* Verde oscuro #084534 */
  background: var(--nav-gradient);
  display: flex; align-items: center;
  padding: 0 20px; gap: 16px;
  box-shadow: 0 2px 12px rgba(6,46,35,0.35);
}

.nav-brand     { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.nav-logo      { width: 36px; height: 36px; border-radius: 8px; object-fit: cover; }
.nav-brand-name { font-size: 13px; font-weight: 800; letter-spacing: 2px; color: #fff; line-height: 1.2; }
.nav-brand-sub  { font-size: 9px; color: rgba(255,255,255,0.4); letter-spacing: 1.5px; }

.nav-links {
  display: flex; align-items: center; gap: 2px;
  flex: 1; overflow-x: auto; scrollbar-width: none;
}
.nav-links::-webkit-scrollbar { display: none; }

.nav-link {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 12px; border-radius: 7px;
  color: rgba(255,255,255,0.65); text-decoration: none;
  font-size: 13px; font-weight: 500; white-space: nowrap;
  transition: all 0.2s;
}
.nav-link:hover              { color: #fff; background: rgba(255,255,255,0.12); }
.nav-link.router-link-active { color: #fff; background: var(--accent); font-weight: 600; }
.nav-link--admin.router-link-active { background: var(--secondary); }

.nav-user      { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.nav-user-info { display: flex; flex-direction: column; text-align: right; }
.nav-user-name { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; }
.nav-user-role { font-size: 11px; color: rgba(255,255,255,0.45); }

.nav-avatar {
  width: 36px; height: 36px;
  background: var(--accent);
  border: 2px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 15px; color: #fff;
  cursor: pointer; position: relative; flex-shrink: 0;
  transition: transform 0.2s, box-shadow 0.2s;
}
.nav-avatar:hover { transform: scale(1.06); box-shadow: 0 0 0 3px rgba(49,176,121,0.4); }

.user-menu {
  position: absolute; top: 44px; right: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  min-width: 200px; overflow: hidden; z-index: 200;
}
.user-menu-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 2px;
  background: var(--primary-light);
}
.user-menu-header strong { font-size: 14px; color: var(--text); }
.user-menu-header span   { font-size: 12px; color: var(--text-muted); }
.user-menu-item {
  width: 100%; padding: 12px 16px; background: none;
  border: none; cursor: pointer; font-size: 14px;
  text-align: left; font-family: inherit; transition: background 0.15s;
}
.user-menu-item.danger { color: var(--danger); }
.user-menu-item:hover  { background: var(--bg); }

.overlay-transparent { position: fixed; inset: 0; z-index: 99; }

/* ══ MAIN ════════════════════════════════════════════════════════ */
.main-content { padding-top: var(--nav-h); min-height: 100vh; }

/* ══ MOBILE HEADER ═══════════════════════════════════════════════ */
.mobile-header {
  display: none;
  position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 100;
  background: var(--primary);
  padding: 0 16px;
  align-items: center; justify-content: space-between;
  box-shadow: 0 2px 8px rgba(6,46,35,0.3);
}
.mh-brand { display: flex; align-items: center; gap: 8px; }
.mh-logo  { width: 28px; height: 28px; border-radius: 6px; object-fit: cover; }
.mh-name  { font-size: 14px; font-weight: 800; letter-spacing: 2px; color: #fff; }
.mh-btn   { background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; padding: 4px; }

/* ══ DRAWER ══════════════════════════════════════════════════════ */
.drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(8,69,52,0.45);
  z-index: 200;
  display: flex; align-items: stretch;
}
.drawer {
  width: 280px; background: #fff;
  display: flex; flex-direction: column; overflow-y: auto;
}
.drawer-header {
  display: flex; align-items: center; gap: 12px;
  padding: 20px 16px;
  background: var(--nav-gradient);
}
.drawer-logo { width: 40px; height: 40px; border-radius: 10px; }
.drawer-name { font-size: 14px; font-weight: 700; color: #fff; }
.drawer-role { font-size: 11px; color: rgba(255,255,255,0.55); text-transform: capitalize; }
.drawer-link {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 20px; color: var(--text); text-decoration: none;
  font-size: 14px; font-weight: 500;
  border-bottom: 1px solid var(--border); transition: background 0.15s;
}
.drawer-link:hover,
.drawer-link.router-link-active { background: var(--primary-light); color: var(--primary); }
.drawer-link.router-link-active { border-left: 3px solid var(--accent); }
.drawer-logout {
  margin-top: auto; padding: 16px 20px;
  background: none; border: none;
  border-top: 1px solid var(--border);
  color: var(--danger); font-size: 14px; font-weight: 600;
  cursor: pointer; text-align: left; font-family: inherit;
}

/* ══ FOOTER ══════════════════════════════════════════════════════ */
.app-footer {
  background: var(--footer-gradient);
  color: rgba(255,255,255,0.65);
  font-family: 'Inter', sans-serif;
  margin-top: 48px;
  border-top: 3px solid var(--teal);         /* línea teal de conexión verde→azul */
}
.footer-main {
  display: flex; gap: 40px; flex-wrap: wrap;
  padding: 52px 40px 40px;
  max-width: 1400px; margin: 0 auto;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.footer-brand { flex: 1.8; min-width: 220px; }
.footer-col   { flex: 1; min-width: 140px; }

.footer-logo-row   { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.footer-brand-name { font-size: 16px; font-weight: 900; letter-spacing: 2px; color: #fff; }
.footer-brand-sub  { font-size: 10px; color: rgba(255,255,255,0.38); letter-spacing: 1px; }
.footer-desc       { font-size: 13px; line-height: 1.75; color: rgba(255,255,255,0.48); margin-bottom: 22px; }
.footer-desc strong { color: var(--accent); }

.footer-socials { display: flex; gap: 10px; }
.social-btn {
  width: 34px; height: 34px;
  background: rgba(49,176,121,0.12);
  border: 1px solid rgba(49,176,121,0.25);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,0.55); text-decoration: none;
  transition: all 0.2s;
}
.social-btn:hover { background: var(--accent); border-color: var(--accent); color: #fff; }

.footer-col-title {
  font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
  text-transform: uppercase; color: var(--accent);
  margin-bottom: 16px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(49,176,121,0.25);
}
.footer-links { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.footer-links li {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: rgba(255,255,255,0.48);
  transition: color 0.15s; cursor: default;
}
.footer-links li:hover { color: rgba(255,255,255,0.85); }
.footer-links li span  { font-size: 14px; }

.footer-bottom {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 10px;
  padding: 18px 40px;
  max-width: 1400px; margin: 0 auto;
  font-size: 12px; color: rgba(255,255,255,0.28);
}
.footer-bottom-left  { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.footer-bottom-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.footer-dot { opacity: 0.25; }

/* ══ RESPONSIVE ══════════════════════════════════════════════════ */
@media (max-width: 960px) {
  .topnav        { display: none; }
  .mobile-header { display: flex; }
  .main-content  { padding-top: 56px; }
}
@media (max-width: 768px) {
  .footer-main   { padding: 32px 20px 24px; gap: 24px; }
  .footer-bottom { padding: 14px 20px; flex-direction: column; text-align: center; }
  .footer-brand  { flex: 100%; }
}

/* ════════════════════════════════════════════════════════════════
   ICONOS SVG DETALLADOS + ANIMACIONES
   ════════════════════════════════════════════════════════════════ */

/* ── Base icono SVG navbar ── */
.nav-icon--svg {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: rgba(49, 176, 121, 0.12) !important;
  border: 1px solid rgba(49, 176, 121, 0.25);
  border-radius: 8px;
  padding: 0;
  margin-right: 2px;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.nav-icon--svg svg {
  width: 20px;
  height: 20px;
  color: #fff;
}

/* ── Hover general ── */
.nav-link:hover .nav-icon--svg {
  transform: scale(1.18) rotate(-5deg);
  background: rgba(49, 176, 121, 0.28) !important;
  box-shadow: 0 6px 20px rgba(49, 176, 121, 0.45);
  border-color: rgba(49, 176, 121, 0.5);
}

.nav-link.router-link-active .nav-icon--svg {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3);
}

/* ── Animaciones flotantes por icono (stagger) ── */
.nav-icon--dashboard    { animation: icon-float 4s ease-in-out infinite; }
.nav-icon--manuals      { animation: icon-float 4s ease-in-out infinite 0.2s; }
.nav-icon--maintenance  { animation: icon-float 4s ease-in-out infinite 0.4s; }
.nav-icon--docs         { animation: icon-float 4s ease-in-out infinite 0.6s; }
.nav-icon--resources    { animation: icon-float 4s ease-in-out infinite 0.8s; }
.nav-icon--analytics    { animation: icon-float 4s ease-in-out infinite 1.0s; }
.nav-icon--reports      { animation: icon-float 4s ease-in-out infinite 1.2s; }
.nav-icon--dpv          { animation: icon-float 4s ease-in-out infinite 1.4s; }
.nav-icon--ico          { animation: icon-float 4s ease-in-out infinite 1.6s; }
.nav-icon--users        { animation: icon-float 4s ease-in-out infinite 1.8s; }

@keyframes icon-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* ── Pulse en activo ── */
.nav-link.router-link-active .nav-icon--dashboard,
.nav-link.router-link-active .nav-icon--manuals,
.nav-link.router-link-active .nav-icon--maintenance,
.nav-link.router-link-active .nav-icon--docs,
.nav-link.router-link-active .nav-icon--resources,
.nav-link.router-link-active .nav-icon--analytics,
.nav-link.router-link-active .nav-icon--reports,
.nav-link.router-link-active .nav-icon--dpv,
.nav-link.router-link-active .nav-icon--ico,
.nav-link.router-link-active .nav-icon--users {
  animation: icon-pulse 2s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(49, 176, 121, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(49, 176, 121, 0); }
}

/* ════════════════════════════════════════════════════════════════
   DRAWER — Iconos SVG
   ════════════════════════════════════════════════════════════════ */

.drawer-icon--svg {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: rgba(49, 176, 121, 0.08);
  border: 1px solid rgba(49, 176, 121, 0.15);
  border-radius: 6px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.drawer-icon--svg svg {
  width: 14px;
  height: 14px;
  color: var(--primary);
}

.drawer-link:hover .drawer-icon--svg,
.drawer-link.router-link-active .drawer-icon--svg {
  transform: scale(1.15) rotate(-4deg);
  background: rgba(49, 176, 121, 0.18);
  border-color: rgba(49, 176, 121, 0.35);
}

/* ══ TRANSICIONES ════════════════════════════════════════════════ */
.fade-enter-active,   .fade-leave-active   { transition: opacity 0.15s; }
.fade-enter-from,     .fade-leave-to       { opacity: 0; }
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s; }
.drawer-enter-from,   .drawer-leave-to     { opacity: 0; }
.drawer-enter-active .drawer,
.drawer-leave-active .drawer               { transition: transform 0.2s; }
.drawer-enter-from .drawer,
.drawer-leave-to .drawer                   { transform: translateX(-100%); }
</style>