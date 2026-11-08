// loader.js — estado compartido de la pantalla de transición (login / logout)
import { reactive } from 'vue'

const state = reactive({ visible: false, title: '', subtitle: '' })
const MAX_VISIBLE = 20000   // seguro anti-bloqueo: el loader nunca tapa la app más de 20 s
let hideTimer = null
let failTimer = null

export function useLoader() {
  const show = (title = 'Cargando', subtitle = '') => {
    clearTimeout(hideTimer)
    clearTimeout(failTimer)
    state.title = title
    state.subtitle = subtitle
    state.visible = true
    failTimer = setTimeout(() => { state.visible = false }, MAX_VISIBLE)
  }

  const hide = (delay = 0) => {
    clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      clearTimeout(failTimer)
      state.visible = false
    }, delay)
  }

  // Muestra la pantalla, ejecuta la tarea y la mantiene al menos `min` ms.
  // Si la tarea falla (p. ej. contraseña incorrecta) se cierra de inmediato y el error se propaga.
  const run = async (title, subtitle, task, { min = 800 } = {}) => {
    show(title, subtitle)
    const t0 = performance.now()
    try {
      const result = await task()
      hide(Math.max(0, min - (performance.now() - t0)))
      return result
    } catch (e) {
      hide(0)
      throw e
    }
  }

  return { state, show, hide, run }
}