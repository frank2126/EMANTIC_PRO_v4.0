// ═══════════════════════════════════════════════════════════════════════════════
//  EMANTIX PRO — FASE 6 — Auth.js Optimizado
//  - sessionStorage para datos sensibles
//  - localStorage solo para token si es persistente
//  - Manejo seguro de token
//  - Refresh token automático
// ═══════════════════════════════════════════════════════════════════════════════

import { reactive } from 'vue'
import axios from 'axios'

// ── ESTADO REACTIVO ────────────────────────────────────────────────────────

const state = reactive({
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  error: null
})

// ── RESTAURAR SESIÓN AL RECARGAR ──────────────────────────────────────────

function restoreSession() {
  // Intentar restaurar access_token del localStorage (persistente)
  const savedAccessToken = localStorage.getItem('emantix_access_token')
  
  // Intentar restaurar refresh_token del localStorage
  const savedRefreshToken = localStorage.getItem('emantix_refresh_token')
  
  // Intentar restaurar usuario del sessionStorage (solo para esta sesión)
  const savedUser = sessionStorage.getItem('emantix_user')
  
  if (savedAccessToken && savedRefreshToken && savedUser) {
    try {
      state.accessToken = savedAccessToken
      state.refreshToken = savedRefreshToken
      state.user = JSON.parse(savedUser)
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedAccessToken}`
    } catch (error) {
      console.error('Error restaurando sesión:', error)
      clearSession()
    }
  }
}

// ── LIMPIAR SESIÓN ────────────────────────────────────────────────────────

function clearSession() {
  state.accessToken = null
  state.refreshToken = null
  state.user = null
  state.error = null
  localStorage.removeItem('emantix_access_token')
  localStorage.removeItem('emantix_refresh_token')
  sessionStorage.removeItem('emantix_user')
  delete axios.defaults.headers.common['Authorization']
}

// ── COMPOSABLE USEAUTH ─────────────────────────────────────────────────────

export const useAuth = () => {
  
  /**
   * Login del usuario
   * @param {string} username
   * @param {string} password
   * @returns {Promise} Datos del usuario
   */
  const login = async (username, password) => {
    state.isLoading = true
    state.error = null
    
    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password
      })
      
      const { access_token, refresh_token, user } = response.data
      
      // Guardar tokens en localStorage (persistente)
      localStorage.setItem('emantix_access_token', access_token)
      localStorage.setItem('emantix_refresh_token', refresh_token)
      
      // Guardar usuario en sessionStorage (NO exponer en localStorage)
      sessionStorage.setItem('emantix_user', JSON.stringify(user))
      
      // Actualizar estado
      state.accessToken = access_token
      state.refreshToken = refresh_token
      state.user = user
      
      // Configurar header de autorización
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return { success: true, user }
    } catch (error) {
      const message = error.response?.data?.detail || 'Error en login'
      state.error = message
      console.error('Login error:', message)
      throw error
    } finally {
      state.isLoading = false
    }
  }
  
  /**
   * Logout del usuario
   * Limpia todo lo relacionado con la sesión
   */
  const logout = () => {
    clearSession()
    state.isLoading = false
  }
  
  /**
   * Refrescar access token usando refresh token
   * Extender la sesión del usuario
   */
  const refreshAccessToken = async () => {
    if (!state.refreshToken) {
      console.warn('No hay refresh token disponible')
      return false
    }
    
    try {
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: state.refreshToken
      })
      
      if (response.data.access_token) {
        const newAccessToken = response.data.access_token
        localStorage.setItem('emantix_access_token', newAccessToken)
        state.accessToken = newAccessToken
        axios.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`
        console.log('Access token refrescado exitosamente')
        return true
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      // Si refresh falla, limpiar sesión completa
      clearSession()
      return false
    }
  }
  
  /**
   * Cambiar contraseña
   */
  const changePassword = async (oldPassword, newPassword) => {
    try {
      await axios.post('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      return true
    } catch (error) {
      state.error = error.response?.data?.detail || 'Error al cambiar contraseña'
      throw error
    }
  }
  
  /**
   * Verificar si el usuario está logueado
   */
  const isLoggedIn = () => !!state.accessToken && !!state.user
  
  /**
   * Verificar si el usuario es admin
   */
  const isAdmin = () => state.user?.role === 'admin'
  
  /**
   * Obtener rol del usuario
   */
  const getRole = () => state.user?.role || null
  
  /**
   * Obtener nombre del usuario
   */
  const getUsername = () => state.user?.username || null
  
  return {
    state,
    login,
    logout,
    refreshAccessToken,
    changePassword,
    isLoggedIn,
    isAdmin,
    getRole,
    getUsername,
    restoreSession,
    clearSession
  }
}

// Restaurar sesión al cargar el módulo
restoreSession()
