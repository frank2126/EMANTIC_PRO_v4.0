// loader.js — estado compartido de la pantalla de transición (login / logout)
import { reactive } from 'vue'

const state = reactive({ visible: false, title: '', subtitle: '' })
let hideTimer = null

export function useLoader() {
  const show = (title = 'Cargando', subtitle = '') => {
    clearTimeout(hideTimer)
    state.title = title
    state.subtitle = subtitle
    state.visible = true
  }

  const hide = (delay = 0) => {
    clearTimeout(hideTimer)
    hideTimer = setTimeout(() => { state.visible = false }, delay)
  }

  // Muestra la pantalla, ejecuta la tarea y la mantiene al menos `min` ms
  // (evita parpadeos si la tarea termina muy rápido).
  const run = async (title, subtitle, task, { min = 800 } = {}) => {
    show(title, subtitle)
    const t0 = performance.now()
    try {
      await task()
    } finally {
      hide(Math.max(0, min - (performance.now() - t0)))
    }
  }

  return { state, show, hide, run }
}