//  EMANTIC PRO 
import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

// ── RUTAS CON LAZY LOADING ─────────────────────────────────────────────────
// Cada componente se carga solo cuando se navega a esa ruta
const Login = () => import('./views/Login.vue')
const ForgotPassword = () => import('./views/ForgotPassword.vue')
const Dashboard = () => import('./views/Dashboard.vue')
const Manuals = () => import('./views/Manuals.vue')
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

// ──(Guard) ──────────────────────────────────────────
// Verifica autenticación, autorización y valida token con backend

let tokenValidationCache = { token: null, isValid: null, validatedAt: null }

/**
 * Validar token con backend
 */
async function validateTokenWithBackend(token) {
  const now = Date.now()
  
  // Si token en cache es el mismo y fue validado hace < 5 min, usar cache ///
  if (
    tokenValidationCache.token === token &&
    tokenValidationCache.isValid !== null &&
    (now - tokenValidationCache.validatedAt) < 5 * 60 * 1000
  ) {
    return tokenValidationCache.isValid
  }
  
  try {
    await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    // Token válido
    tokenValidationCache = { token, isValid: true, validatedAt: now }
    return true
    
  } catch (error) {

    // Token inválido o expirado
    tokenValidationCache = { token, isValid: false, validatedAt: now }
    return false
  }
}

// ── BEFOREEACH GUARD ──────────────────────────────────////

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('emantix_access_token')
  const user = JSON.parse(sessionStorage.getItem('emantix_user') || 'null')
  
  // Ruta pública - permitir acceso
  if (to.meta.public) {
    // Si está logueado y va a login, redirigir a dashboard
    if (token && to.path === '/login') {
      return next('/dashboard')
    }
    return next()
  }
  
  // Ruta protegida - requiere autenticación
  if (to.meta.requiresAuth) {
    // Sin token
    if (!token) {
      return next('/login')
    }
    
    // Validar token con backend (solo si pasó > 5 min)
    
    const isTokenValid = await validateTokenWithBackend(token)
    if (!isTokenValid) {
        
      // Token inválido, limpiar y logout
      localStorage.removeItem('emantix_access_token')
      sessionStorage.removeItem('emantix_user')
      return next('/login')
    }
    
    // Verificar permisos de admin
    if (to.meta.requiresAdmin && user?.role !== 'admin') {
      console.warn(`Acceso denegado: usuario no es admin`)
      return next('/dashboard')
    }
    
    return next()
  }
  
  next()
})
// Actualizar título de página

router.afterEach((to) => {
  // Esperar a que se renderice el componente
  setTimeout(() => {
    document.title = to.meta.title || 'EMANTIC Pro v4.0'
  }, 0)
})

export default router
