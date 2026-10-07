// ═══════════════════════════════════════════════════════════════════════════════
//  EMANTIX PRO — FASE 6 — Axios Interceptor
//  - Manejo global de errores
//  - Validación automática de token
//  - Refresh token automático
//  - Logging de peticiones
// ═══════════════════════════════════════════════════════════════════════════════

import axios from 'axios'

/**
 * Configurar interceptores de axios
 * @param {Object} router - Vue Router instance
 * @param {Object} auth - Auth composable
 */
export function setupAxiosInterceptors(router, auth) {
  
  // ── INTERCEPTOR DE RESPUESTA ───────────────────────────────────────────
  // Manejar errores global mente
  
  axios.interceptors.response.use(
    // Respuesta exitosa
    (response) => {
      return response
    },
    
    // Error en respuesta
    async (error) => {
      const originalRequest = error.config
      
      // Token expirado (401) - intentar refrescar
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true
        
        console.warn('Access token expirado, intentando refrescar...')
        
        // Intentar refrescar access token
        const { refreshAccessToken } = auth
        const tokenRefreshed = await refreshAccessToken()
        
        if (tokenRefreshed) {
          // Reintentar petición original
          return axios(originalRequest)
        } else {
          // Refresh falló, logout
          const { logout } = auth
          logout()
          router.push('/login')
        }
      }
      
      // Acceso denegado (403)
      if (error.response?.status === 403) {
        console.error('Acceso denegado - No tienes permisos')
      }
      
      // Error del servidor (500)
      if (error.response?.status === 500) {
        console.error('Error en servidor')
      }
      
      // Sin conexión
      if (!error.response) {
        console.error('Error de conexión', error.message)
      }
      
      return Promise.reject(error)
    }
  )
  
  // ── INTERCEPTOR DE PETICIÓN ───────────────────────────────────────────
  // Agregar access token a cada petición
  
  axios.interceptors.request.use(
    (config) => {
      // Usar access token (de corta duración)
      const accessToken = localStorage.getItem('emantix_access_token')
      
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`
      }
      
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )
}

/**
 * Handler global de errores Vue
 * @param {Object} app - Vue app instance
 * @param {Object} router - Vue Router instance
 */
export function setupGlobalErrorHandler(app, router) {
  
  app.config.errorHandler = (err, instance, info) => {
    console.error(`Error [${info}]:`, err)
    
    // Si es error de red, mostrar notificación
    if (err.message === 'Network Error') {
      console.error('Error de conexión - Revisa tu conexión a internet')
      return
    }
    
    // Si es error 401, logout automático
    if (err.response?.status === 401) {
      console.warn('Sesión expirada - Redirigiendo a login')
      localStorage.removeItem('emantix_access_token')
      localStorage.removeItem('emantix_refresh_token')
      sessionStorage.removeItem('emantix_user')
      router.push('/login')
      return
    }
    
    // Log para debugging
    if (process.env.NODE_ENV === 'development') {
      console.error('Full error:', {
        message: err.message,
        stack: err.stack,
        response: err.response?.data,
        status: err.response?.status
      })
    }
  }
}

/**
 * Configurar instancia de axios con base URL y timeout
 */
export function configureAxios() {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  axios.defaults.timeout = 30000 // 30 segundos
  axios.defaults.withCredentials = true
}
