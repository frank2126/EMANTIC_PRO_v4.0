import { createApp } from 'vue'
import App from './App.vue'
import AppLoader from './components/AppLoader.vue'
import router from './router'
import './assets/main.css'
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// ── Pantalla de transición (login / cerrar sesión) ──────────────────────
// Se monta APARTE de App.vue, directamente en <body>. Así no desaparece cuando
// App.vue cambia de layout (login ↔ navbar) al iniciar o cerrar sesión.
// El estado se comparte con loader.js (mismo módulo = misma instancia).
const loaderHost = document.createElement('div')
loaderHost.id = 'app-loader-host'
document.body.appendChild(loaderHost)
createApp(AppLoader).mount(loaderHost)

// ── Pantalla de carga inicial (definida en index.html) ──────────────────
// - Se muestra al menos SPLASH_MIN ms desde que abrió la página (evita un parpadeo
//   si todo cargó muy rápido). performance.now() ya cuenta el tiempo transcurrido,
//   así que si la carga tardó más que eso, se oculta de inmediato.
// - Nunca se queda más de SPLASH_MAX ms, pase lo que pase.
const SPLASH_MIN = 700
const SPLASH_MAX = 8000

let splashHidden = false
function hideSplash() {
  if (splashHidden) return
  splashHidden = true
  const splash = document.getElementById('splash')
  if (!splash) return
  splash.classList.add('hide')
  setTimeout(() => splash.remove(), 400)
}

router.isReady().then(() => {
  setTimeout(hideSplash, Math.max(0, SPLASH_MIN - performance.now()))
})
setTimeout(hideSplash, SPLASH_MAX)