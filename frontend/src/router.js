//  EMANTIC PRO - Router Actualizado
//  - Usa auth.js para autenticación
//  - Incluye Resources2.vue para repuestos

import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from './auth.js'

// ── RUTAS CON LAZY LOADING ─────────────────────────────────────────────────
// Cada componente se carga solo cuando se navega a esa ruta
const Login = () => import('./views/Login.vue')
const ForgotPassword = () => import('./views/ForgotPassword.vue')
const Dashboard = () => import('./views/Dashboard.vue')
const Manuals = () => import('./views/Manuals.vue')
const Resources2 = () => import('./views/Resources2.vue')
const Maintenance = () => import('./views/Maintenance.vue')
const Documentation = () => import('./views/Documentation.vue')
const Resources = () => import('./views/Resources.vue')
const Analytics = () => import('./views/Analytics.vue')
const Users = () => import('./views/Users.vue')
const ReportesCampo = () => import('./views/ReportesCampo.vue')
const CargaDPV = () => import('./views/CargaDPV.vue')
const IndicadoresICO = () => import('./views/IndicadoresICO.vue')

// ── RUTAS ──────────────────────────────────────────────────────────────────

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    component: Login,
    meta: {
      public: true,
      title: 'Login - EMANTIC Pro'
    }
  },
  {
    path: '/forgot-password',
    component: ForgotPassword,
    meta: {
      public: true,
      title: 'Recuperar Contraseña - EMANTIC Pro'
    }
  },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: {
      requiresAuth: true,
      title: 'Dashboard - EMANTIC Pro'
    }
  },
  {
    path: '/manuals',
    component: Manuals,
    meta: {
      requiresAuth: true,
      title: 'Manuales Técnicos - EMANTIC Pro'
    }
  },
  {
    path: '/resources2',
    name: 'resources2',
    component: Resources2,
    meta: {
      requiresAuth: true,
      title: 'Repuestos y Piezas - EMANTIC Pro'
    }
  },
  {
    path: '/maintenance',
    component: Maintenance,
    meta: {
      requiresAuth: true,
      title: 'Gestión de Mantenimiento - EMANTIC Pro'
    }
  },
  {
    path: '/documentation',
    component: Documentation,
    meta: {
      requiresAuth: true,
      title: 'Documentación - EMANTIC Pro'
    }
  },
  {
    path: '/resources',
    component: Resources,
    meta: {
      requiresAuth: true,
      title: 'Recursos de Taller - EMANTIC Pro'
    }
  },
  {
    path: '/analytics',
    component: Analytics,
    meta: {
      requiresAuth: true,
      title: 'Analíticas - EMANTIC Pro'
    }
  },
  {
    path: '/users',
    component: Users,
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Gestión de Usuarios - EMANTIC Pro'
    }
  },
  {
    path: '/reportes',
    component: ReportesCampo,
    meta: {
      requiresAuth: true,
      title: 'Reportes de Campo - EMANTIC Pro'
    }
  },
  {
    path: '/dpv',
    component: CargaDPV,
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Carga DPV - EMANTIC Pro'
    }
  },
  {
    path: '/ico',
    component: IndicadoresICO,
    meta: {
      requiresAuth: true,
      title: 'Indicadores ICO - EMANTIC Pro'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

// ── CREAR ROUTER ───────────────────────────────────────────────────────────

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ── GUARD DE AUTENTICACIÓN ──────────────────────────────────────────────────
// Verifica autenticación y autorización usando auth.js

router.beforeEach((to, from, next) => {
  const { state, isLoggedIn, isAdmin } = useAuth()
  
  // Ruta pública - permitir acceso
  if (to.meta.public) {
    // Si está logueado y va a login, redirigir a dashboard
    if (isLoggedIn() && to.path === '/login') {
      return next('/dashboard')
    }
    return next()
  }
  
  // Ruta protegida - requiere autenticación
  if (to.meta.requiresAuth) {
    // Sin sesión activa
    if (!isLoggedIn()) {
      return next('/login')
    }
    
    // Verificar permisos de admin
    if (to.meta.requiresAdmin && !isAdmin()) {
      console.warn(`Acceso denegado: usuario no es admin`)
      return next('/dashboard')
    }
    
    return next()
  }
  
  next()
})

// ── ACTUALIZAR TÍTULO DE PÁGINA ────────────────────────────────────────────

router.afterEach((to) => {
  // Esperar a que se renderice el componente
  setTimeout(() => {
    document.title = to.meta.title || 'EMANTIC Pro v4.0'
  }, 0)
})

export default router