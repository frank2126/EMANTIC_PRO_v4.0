<template>
  <div class="login-page">
    <div class="login-left">
      <img src="/icons/icon-192.png" alt="Logo" class="login-logo" />
      <h1 class="login-brand">EMANTIX</h1>
      <p class="login-tagline">Sistema de Gestión Técnica Automotriz</p>
      <div class="login-features">
        <div class="lf-item">✅ Manuales técnicos digitales</div>
        <div class="lf-item">✅ Gestión de mantenimiento</div>
        <div class="lf-item">✅ Documentación técnica</div>
        <div class="lf-item">✅ Recursos para talleres</div>
        <div class="lf-item">✅ Analíticas Power BI</div>
        <div class="lf-item">✅ Base de datos SQL Server</div>
      </div>
      <p class="login-version">v4.0 · SQL Server · PWA</p>
    </div>

    <div class="login-right">
      <div class="login-card" :class="{ shake: shaking }">
        <div class="lc-header">
          <img src="/icons/icon-192.png" alt="Logo" class="lc-logo" />
          <div>
            <h2 class="lc-title">Iniciar sesión</h2>
            <p class="lc-sub">Ingresa tus credenciales para continuar</p>
          </div>
        </div>

        <div v-if="lockMsg"   class="alert alert--lock">🔒 {{ lockMsg }}</div>
        <div v-if="errorMsg && !lockMsg" class="alert alert--error">⚠ {{ errorMsg }}</div>
        <div v-if="successMsg" class="alert alert--success">✓ {{ successMsg }}</div>

        <div class="lc-form">
          <div class="fgroup">
            <label class="label">Usuario</label>
            <input v-model="form.username" type="text" class="input"
              placeholder="Ingresa tu usuario" autocomplete="username"
              :disabled="loading || !!lockMsg" @keyup.enter="handleLogin" />
          </div>

          <div class="fgroup">
            <div class="label-row">
              <label class="label">Contraseña</label>
              <!-- ✅ ENLACE RECUPERAR CONTRASEÑA -->
              <router-link to="/forgot-password" class="forgot-link">
                ¿Olvidaste tu contraseña?
              </router-link>
            </div>
            <div class="pass-wrap">
              <input v-model="form.password" :type="showPass ? 'text' : 'password'"
                class="input" placeholder="••••••••" autocomplete="current-password"
                :disabled="loading || !!lockMsg" @keyup.enter="handleLogin" />
              <button class="pass-btn" type="button" @click="showPass = !showPass">
                {{ showPass ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <div v-if="attemptsLeft <= 3 && attemptsLeft > 0" class="attempts-warn">
            ⚠ {{ attemptsLeft }} intento{{ attemptsLeft !== 1 ? 's' : '' }} restante{{ attemptsLeft !== 1 ? 's' : '' }}
          </div>

          <button class="btn-login"
            :disabled="loading || !form.username || !form.password || !!lockMsg"
            @click="handleLogin">
            <span v-if="!loading">Ingresar →</span>
            <span v-else class="spinner"></span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../auth.js'

const router = useRouter()
const { login } = useAuth()

const form         = ref({ username: '', password: '' })
const loading      = ref(false)
const errorMsg     = ref('')
const lockMsg      = ref('')
const successMsg   = ref('')
const showPass     = ref(false)
const shaking      = ref(false)
const attemptsLeft = ref(5)

const handleLogin = async () => {
  if (!form.value.username || !form.value.password || lockMsg.value) return
  errorMsg.value = ''; successMsg.value = ''; loading.value = true
  try {
    await login(form.value.username, form.value.password)
    successMsg.value = '¡Bienvenido! Redirigiendo...'
    setTimeout(() => router.push('/dashboard'), 700)
  } catch (e) {
    const detail = e.response?.data?.detail || 'Error de conexión con el servidor'
    if (e.response?.status === 429) {
      lockMsg.value = detail
    } else {
      errorMsg.value = detail
      const m = detail.match(/(\d+)/); if (m) attemptsLeft.value = parseInt(m[1])
      shaking.value = true; setTimeout(() => shaking.value = false, 500)
    }
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height:100vh; display:flex; }

.login-left {
  width:360px; flex-shrink:0;
  background:linear-gradient(160deg, #094535 0%, #0d6b4f 100%);
  padding:60px 48px; display:flex; flex-direction:column; justify-content:center;
}
.login-logo    { width:80px; height:80px; border-radius:18px; margin-bottom:20px; box-shadow:0 8px 24px rgba(0,0,0,0.3); }
.login-brand   { font-size:26px; font-weight:800; letter-spacing:4px; color:#fff; margin-bottom:6px; }
.login-tagline { font-size:13px; color:rgba(255,255,255,0.55); margin-bottom:36px; }
.login-features{ display:flex; flex-direction:column; gap:10px; margin-bottom:40px; }
.lf-item       { font-size:13px; color:rgba(255,255,255,0.8); }
.login-version { font-size:11px; color:rgba(255,255,255,0.3); letter-spacing:1px; }

.login-right {
  flex:1; background:#f4f6f9;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:40px 24px; gap:16px;
}

.login-card {
  background:#fff; border:1px solid #e2e8f0;
  border-radius:16px; padding:36px;
  width:100%; max-width:440px;
  box-shadow:0 4px 6px rgba(0,0,0,0.07);
}
.login-card.shake { animation:shake 0.4s ease; }
@keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-6px)} 75%{transform:translateX(6px)} }

.lc-header { display:flex; align-items:center; gap:14px; margin-bottom:24px; }
.lc-logo   { width:44px; height:44px; border-radius:10px; }
.lc-title  { font-size:20px; font-weight:700; color:#1a2332; }
.lc-sub    { font-size:13px; color:#64748b; }

.alert { padding:11px 14px; border-radius:8px; font-size:13px; margin-bottom:16px; }
.alert--error   { background:#fee2e2; border:1px solid #fecaca; color:#991b1b; }
.alert--lock    { background:#fef3c7; border:1px solid #fde68a; color:#92400e; }
.alert--success { background:#d1fae5; border:1px solid #a7f3d0; color:#065f46; }

.lc-form { display:flex; flex-direction:column; gap:16px; }
.fgroup  { display:flex; flex-direction:column; gap:6px; }

/* ── Label con enlace ── */
.label-row {
  display:flex; align-items:center; justify-content:space-between;
}
.label {
  font-size:11px; font-weight:700; color:#64748b;
  text-transform:uppercase; letter-spacing:0.5px;
}
.forgot-link {
  font-size:12px; font-weight:600;
  color:#0d5c45; text-decoration:none;
  transition:color 0.2s;
}
.forgot-link:hover { color:#094535; text-decoration:underline; }

.pass-wrap { position:relative; }
.pass-wrap .input { padding-right:44px; }
.pass-btn {
  position:absolute; right:12px; top:50%; transform:translateY(-50%);
  background:none; border:none; cursor:pointer; font-size:16px; opacity:0.5;
}

.input {
  width:100%; background:#fff; border:1.5px solid #e2e8f0;
  border-radius:8px; padding:11px 14px; color:#1a2332;
  font-size:14px; font-family:inherit; outline:none; transition:border-color 0.2s;
}
.input:focus { border-color:#0d5c45; box-shadow:0 0 0 3px rgba(13,92,69,0.1); }

.attempts-warn {
  font-size:12px; color:#92400e;
  background:#fef3c7; padding:8px 12px; border-radius:6px;
}

.btn-login {
  width:100%; background:linear-gradient(135deg,#0d5c45 0%,#1a7fbf 100%);
  color:#fff; font-weight:700; font-size:15px; font-family:inherit;
  padding:13px; border:none; border-radius:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.2s; box-shadow:0 4px 12px rgba(13,92,69,0.3);
}
.btn-login:hover:not(:disabled) { opacity:0.92; transform:translateY(-1px); }
.btn-login:disabled { opacity:0.5; cursor:not-allowed; transform:none; }

.spinner {
  width:18px; height:18px;
  border:2px solid rgba(255,255,255,0.3); border-top-color:#fff;
  border-radius:50%; animation:spin 0.7s linear infinite;
}
@keyframes spin { to { transform:rotate(360deg); } }

.security-note { font-size:11px; color:#64748b; text-align:center; margin-top:16px; }

.hint-box {
  background:#fffbeb; border:1px solid #fde68a;
  border-radius:10px; padding:14px 16px;
  width:100%; max-width:440px;
  font-size:12px; color:#78350f; line-height:1.8;
}
.hint-title { font-weight:700; font-size:11px; letter-spacing:1px; color:#92400e; margin-bottom:4px; }
.hint-warn  { color:#92400e; margin-top:4px; font-size:11px; }

@media(max-width:700px) {
  .login-left { display:none; }
  .login-right { padding:24px 16px; }
  .login-card { padding:24px 20px; }
}
</style>
