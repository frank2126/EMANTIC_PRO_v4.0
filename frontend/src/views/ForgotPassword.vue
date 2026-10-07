<template>
  <div class="recovery-page">
    <div class="recovery-left">
      <img src="/icons/icon-192.png" alt="Logo" class="r-logo" />
      <h1 class="r-brand">EMANTIX</h1>
      <p class="r-tagline">Sistema de Gestión Técnica</p>
      <div class="r-features">
        <div class="rf-item">✅ Manuales técnicos digitales</div>
        <div class="rf-item">✅ Gestión de mantenimiento</div>
        <div class="rf-item">✅ Base de datos SQL Server</div>
      </div>
    </div>

    <div class="recovery-right">
      <div class="recovery-card">

        <!-- ── PASO 1: Ingresar usuario ── -->
        <div v-if="step === 1">
          <div class="rc-header">
            <div class="rc-icon">🔐</div>
            <div>
              <h2 class="rc-title">¿Olvidaste tu contraseña?</h2>
              <p class="rc-sub">Ingresa tu usuario y te enviaremos un código de verificación al correo registrado.</p>
            </div>
          </div>

          <div v-if="error" class="alert alert--error">⚠ {{ error }}</div>

          <div class="fgroup">
            <label class="label">Nombre de usuario</label>
            <div class="input-wrap">
              <span class="input-icon">👤</span>
              <input v-model="username" type="text" class="input" placeholder="Ingresa tu usuario"
                autocomplete="username" :disabled="loading" @keyup.enter="sendCode" />
            </div>
          </div>

          <button class="btn-primary btn-full" :disabled="loading || !username.trim()" @click="sendCode">
            <span v-if="!loading">Enviar código →</span>
            <span v-else class="spinner"></span>
          </button>

          <router-link to="/login" class="back-link">← Volver al inicio de sesión</router-link>
        </div>

        <!-- ── PASO 2: Verificar código ── -->
        <div v-else-if="step === 2">
          <div class="rc-header">
            <div class="rc-icon">📧</div>
            <div>
              <h2 class="rc-title">Revisa tu correo</h2>
              <p class="rc-sub">Enviamos un código de 6 dígitos a <strong>{{ maskedEmail }}</strong></p>
            </div>
          </div>

          <div v-if="error"   class="alert alert--error">⚠ {{ error }}</div>
          <div v-if="success" class="alert alert--success">✓ {{ success }}</div>

          <!-- Código de 6 dígitos -->
          <div class="fgroup">
            <label class="label">Código de verificación</label>
            <div class="code-inputs">
              <input v-for="(d, i) in codeDigits" :key="i"
                :ref="el => codeRefs[i] = el"
                v-model="codeDigits[i]"
                type="text" maxlength="1" class="code-digit"
                @input="onDigitInput(i)"
                @keydown.backspace="onBackspace(i)"
                @paste.prevent="onPaste" />
            </div>
            <p class="code-timer" :class="{ expired: timeLeft === 0 }">
              {{ timeLeft > 0 ? `⏰ Expira en ${formatTime(timeLeft)}` : '❌ Código expirado' }}
            </p>
          </div>

          <button class="btn-primary btn-full" :disabled="loading || codeValue.length < 6 || timeLeft === 0" @click="verifyCode">
            <span v-if="!loading">Verificar código →</span>
            <span v-else class="spinner"></span>
          </button>

          <div class="resend-row">
            <span class="resend-txt">¿No recibiste el código?</span>
            <button class="btn-link" :disabled="resendCooldown > 0" @click="sendCode">
              {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : 'Reenviar código' }}
            </button>
          </div>

          <router-link to="/login" class="back-link">← Volver al inicio de sesión</router-link>
        </div>

        <!-- ── PASO 3: Nueva contraseña ── -->
        <div v-else-if="step === 3">
          <div class="rc-header">
            <div class="rc-icon">🔑</div>
            <div>
              <h2 class="rc-title">Nueva contraseña</h2>
              <p class="rc-sub">Crea una contraseña segura para tu cuenta.</p>
            </div>
          </div>

          <div v-if="error"   class="alert alert--error">⚠ {{ error }}</div>

          <div class="fgroup">
            <label class="label">Nueva contraseña</label>
            <div class="input-wrap">
              <span class="input-icon">🔒</span>
              <input v-model="newPassword" :type="showPass1 ? 'text' : 'password'"
                class="input" placeholder="Mínimo 8 caracteres" :disabled="loading"
                @input="checkStrength" />
              <button class="toggle-pass" type="button" @click="showPass1=!showPass1">
                {{ showPass1 ? '🙈' : '👁' }}
              </button>
            </div>
            <!-- Barra de seguridad -->
            <div v-if="newPassword" class="strength-wrap">
              <div class="strength-bar">
                <div class="strength-fill" :style="{width: strengthPct+'%', background: strengthColor}"></div>
              </div>
              <span class="strength-label" :style="{color: strengthColor}">{{ strengthLabel }}</span>
            </div>
            <!-- Requisitos -->
            <div v-if="newPassword" class="requirements">
              <div class="req" :class="req.length >= 8 ? 'req--ok' : 'req--no'">
                {{ req.length >= 8 ? '✅' : '❌' }} Mínimo 8 caracteres
              </div>
              <div class="req" :class="req.upper ? 'req--ok' : 'req--no'">
                {{ req.upper ? '✅' : '❌' }} Al menos 1 mayúscula
              </div>
              <div class="req" :class="req.number ? 'req--ok' : 'req--no'">
                {{ req.number ? '✅' : '❌' }} Al menos 1 número
              </div>
            </div>
          </div>

          <div class="fgroup">
            <label class="label">Confirmar contraseña</label>
            <div class="input-wrap">
              <span class="input-icon">🔒</span>
              <input v-model="confirmPassword" :type="showPass2 ? 'text' : 'password'"
                class="input" placeholder="Repite la contraseña" :disabled="loading"
                @keyup.enter="resetPassword" />
              <button class="toggle-pass" type="button" @click="showPass2=!showPass2">
                {{ showPass2 ? '🙈' : '👁' }}
              </button>
            </div>
            <p v-if="confirmPassword && newPassword !== confirmPassword" class="match-error">
              ❌ Las contraseñas no coinciden
            </p>
            <p v-if="confirmPassword && newPassword === confirmPassword" class="match-ok">
              ✅ Las contraseñas coinciden
            </p>
          </div>

          <button class="btn-primary btn-full"
            :disabled="loading || !passwordValid || newPassword !== confirmPassword"
            @click="resetPassword">
            <span v-if="!loading">Guardar nueva contraseña →</span>
            <span v-else class="spinner"></span>
          </button>
        </div>

        <!-- ── PASO 4: Éxito ── -->
        <div v-else-if="step === 4" class="success-step">
          <div class="success-icon">🎉</div>
          <h2 class="rc-title">¡Contraseña actualizada!</h2>
          <p class="rc-sub">Tu contraseña fue cambiada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña.</p>
          <button class="btn-primary btn-full" @click="$router.push('/login')">
            Ir al inicio de sesión →
          </button>
        </div>

        <!-- Indicador de pasos -->
        <div class="steps-indicator" v-if="step < 4">
          <div v-for="s in 3" :key="s" class="step-dot" :class="{active: step === s, done: step > s}">
            {{ step > s ? '✓' : s }}
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// ── Estado ────────────────────────────────────────
const step            = ref(1)
const username        = ref('')
const maskedEmail     = ref('')
const codeDigits      = ref(['', '', '', '', '', ''])
const codeRefs        = ref([])
const newPassword     = ref('')
const confirmPassword = ref('')
const showPass1       = ref(false)
const showPass2       = ref(false)
const loading         = ref(false)
const error           = ref('')
const success         = ref('')
const timeLeft        = ref(900) // 15 minutos en segundos
const resendCooldown  = ref(0)
let countdownTimer    = null
let resendTimer       = null

// ── Computed ──────────────────────────────────────
const codeValue = computed(() => codeDigits.value.join(''))

const req = computed(() => ({
  length: newPassword.value.length,
  upper:  /[A-Z]/.test(newPassword.value),
  number: /[0-9]/.test(newPassword.value),
}))

const passwordValid = computed(() =>
  req.value.length >= 8 && req.value.upper && req.value.number
)

const strengthPct = computed(() => {
  const p = newPassword.value; let s = 0
  if (p.length >= 8) s += 30; if (p.length >= 12) s += 10
  if (/[A-Z]/.test(p)) s += 20; if (/[0-9]/.test(p)) s += 20
  if (/[^A-Za-z0-9]/.test(p)) s += 20
  return Math.min(s, 100)
})
const strengthColor = computed(() =>
  strengthPct.value < 40 ? '#ef4444' : strengthPct.value < 70 ? '#f59e0b' : '#10b981'
)
const strengthLabel = computed(() =>
  strengthPct.value < 40 ? 'Débil' : strengthPct.value < 70 ? 'Moderada' : 'Fuerte ✅'
)

// ── Helpers ───────────────────────────────────────
const formatTime = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`

const checkStrength = () => {} // reactivo automáticamente

const startCountdown = () => {
  timeLeft.value = 900
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    if (timeLeft.value > 0) timeLeft.value--
    else clearInterval(countdownTimer)
  }, 1000)
}

const startResendCooldown = () => {
  resendCooldown.value = 60
  if (resendTimer) clearInterval(resendTimer)
  resendTimer = setInterval(() => {
    if (resendCooldown.value > 0) resendCooldown.value--
    else clearInterval(resendTimer)
  }, 1000)
}

// ── Inputs del código ─────────────────────────────
const onDigitInput = (i) => {
  const val = codeDigits.value[i]
  if (val && !/^\d$/.test(val)) {
    codeDigits.value[i] = ''
    return
  }
  if (val && i < 5) {
    codeRefs.value[i + 1]?.focus()
  }
  if (codeValue.value.length === 6) {
    verifyCode()
  }
}

const onBackspace = (i) => {
  if (!codeDigits.value[i] && i > 0) {
    codeDigits.value[i - 1] = ''
    codeRefs.value[i - 1]?.focus()
  }
}

const onPaste = (e) => {
  const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
  text.split('').forEach((d, i) => { codeDigits.value[i] = d })
  if (text.length === 6) {
    codeRefs.value[5]?.focus()
    verifyCode()
  }
}

// ── API calls ─────────────────────────────────────
const sendCode = async () => {
  error.value = ''; success.value = ''
  if (!username.value.trim()) return
  loading.value = true
  try {
    const res = await axios.post('/api/auth/forgot-password', {
      username: username.value.trim()
    })
    maskedEmail.value = res.data.masked_email
    step.value = 2
    codeDigits.value = ['', '', '', '', '', '']
    startCountdown()
    startResendCooldown()
    setTimeout(() => codeRefs.value[0]?.focus(), 100)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al enviar el código. Intenta de nuevo.'
  } finally { loading.value = false }
}

const verifyCode = async () => {
  error.value = ''
  if (codeValue.value.length < 6) return
  loading.value = true
  try {
    await axios.post('/api/auth/verify-code', {
      username: username.value.trim(),
      code: codeValue.value
    })
    step.value = 3
  } catch (e) {
    error.value = e.response?.data?.detail || 'Código incorrecto. Intenta de nuevo.'
    codeDigits.value = ['', '', '', '', '', '']
    setTimeout(() => codeRefs.value[0]?.focus(), 100)
  } finally { loading.value = false }
}

const resetPassword = async () => {
  error.value = ''
  if (!passwordValid.value || newPassword.value !== confirmPassword.value) return
  loading.value = true
  try {
    await axios.post('/api/auth/reset-password', {
      username:         username.value.trim(),
      code:             codeValue.value,
      new_password:     newPassword.value,
      confirm_password: confirmPassword.value,
    })
    step.value = 4
    clearInterval(countdownTimer)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al actualizar la contraseña.'
  } finally { loading.value = false }
}

onUnmounted(() => {
  clearInterval(countdownTimer)
  clearInterval(resendTimer)
})
</script>

<style scoped>
.recovery-page { min-height:100vh; display:flex; }

/* Panel izquierdo */
.recovery-left {
  width:360px; flex-shrink:0;
  background:linear-gradient(160deg, #094535 0%, #0d6b4f 100%);
  padding:60px 48px; display:flex; flex-direction:column; justify-content:center;
}
.r-logo    { width:80px; height:80px; border-radius:18px; margin-bottom:20px; box-shadow:0 8px 24px rgba(0,0,0,0.3); }
.r-brand   { font-size:26px; font-weight:800; letter-spacing:4px; color:#fff; margin-bottom:6px; }
.r-tagline { font-size:13px; color:rgba(255,255,255,0.55); margin-bottom:36px; }
.r-features{ display:flex; flex-direction:column; gap:10px; }
.rf-item   { font-size:13px; color:rgba(255,255,255,0.8); }

/* Panel derecho */
.recovery-right {
  flex:1; background:#f4f6f9;
  display:flex; align-items:center; justify-content:center; padding:40px 24px;
}

.recovery-card {
  background:#fff; border:1px solid #e2e8f0;
  border-radius:16px; padding:36px;
  width:100%; max-width:460px;
  box-shadow:0 4px 6px rgba(0,0,0,0.07);
}

.rc-header { display:flex; align-items:flex-start; gap:14px; margin-bottom:24px; }
.rc-icon   { font-size:32px; flex-shrink:0; }
.rc-title  { font-size:20px; font-weight:700; color:#1a2332; margin-bottom:4px; }
.rc-sub    { font-size:13px; color:#64748b; line-height:1.5; }

.alert { padding:11px 14px; border-radius:8px; font-size:13px; margin-bottom:16px; }
.alert--error   { background:#fee2e2; border:1px solid #fecaca; color:#991b1b; }
.alert--success { background:#d1fae5; border:1px solid #a7f3d0; color:#065f46; }

.fgroup { display:flex; flex-direction:column; gap:6px; margin-bottom:16px; }
.label  { font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; }

.input-wrap { position:relative; display:flex; align-items:center; }
.input-icon { position:absolute; left:12px; font-size:15px; z-index:1; }
.input-wrap .input { padding-left:40px; }
.toggle-pass { position:absolute; right:12px; background:none; border:none; cursor:pointer; font-size:15px; opacity:0.5; }

.input {
  width:100%; background:#fff; border:1.5px solid #e2e8f0;
  border-radius:8px; padding:11px 14px; color:#1a2332;
  font-size:14px; font-family:inherit; outline:none; transition:border-color 0.2s;
}
.input:focus { border-color:#0d5c45; box-shadow:0 0 0 3px rgba(13,92,69,0.1); }

/* Código de 6 dígitos */
.code-inputs { display:flex; gap:8px; justify-content:center; margin-bottom:8px; }
.code-digit  {
  width:48px; height:56px; text-align:center;
  font-size:24px; font-weight:800; font-family:monospace;
  border:2px solid #e2e8f0; border-radius:10px;
  background:#fff; color:#1a2332; outline:none;
  transition:all 0.2s; padding:0;
}
.code-digit:focus { border-color:#0d5c45; box-shadow:0 0 0 3px rgba(13,92,69,0.1); }

.code-timer { font-size:12px; text-align:center; color:#64748b; margin-top:4px; }
.code-timer.expired { color:#ef4444; font-weight:700; }

/* Fortaleza */
.strength-wrap { display:flex; align-items:center; gap:10px; margin-top:6px; }
.strength-bar  { flex:1; height:4px; background:#e2e8f0; border-radius:2px; overflow:hidden; }
.strength-fill { height:100%; transition:width 0.3s,background 0.3s; }
.strength-label{ font-size:12px; font-weight:700; min-width:80px; }

/* Requisitos */
.requirements { display:flex; flex-direction:column; gap:4px; margin-top:8px; }
.req       { font-size:12px; }
.req--ok   { color:#065f46; }
.req--no   { color:#94a3b8; }

.match-error { font-size:12px; color:#ef4444; margin-top:4px; }
.match-ok    { font-size:12px; color:#065f46; margin-top:4px; }

/* Botón principal */
.btn-primary {
  background:linear-gradient(135deg,#0d5c45 0%,#1a7fbf 100%);
  color:#fff; font-weight:700; font-size:15px; font-family:inherit;
  padding:13px; border:none; border-radius:10px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all 0.2s; box-shadow:0 4px 12px rgba(13,92,69,0.3);
}
.btn-primary:hover:not(:disabled) { opacity:0.92; transform:translateY(-1px); }
.btn-primary:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
.btn-full { width:100%; margin-bottom:14px; }

.spinner { width:18px; height:18px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 0.7s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }

/* Reenvío */
.resend-row  { display:flex; align-items:center; justify-content:center; gap:6px; margin-bottom:14px; }
.resend-txt  { font-size:13px; color:#64748b; }
.btn-link    { background:none; border:none; color:#0d5c45; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; text-decoration:underline; }
.btn-link:disabled { color:#94a3b8; cursor:not-allowed; text-decoration:none; }

.back-link { display:block; text-align:center; color:#64748b; font-size:13px; text-decoration:none; transition:color 0.2s; }
.back-link:hover { color:#0d5c45; }

/* Éxito */
.success-step { text-align:center; padding:20px 0; }
.success-icon { font-size:64px; margin-bottom:16px; animation:bounce 0.6s ease; }
@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.success-step .rc-title { margin-bottom:10px; }
.success-step .rc-sub   { margin-bottom:24px; }

/* Indicador de pasos */
.steps-indicator { display:flex; align-items:center; justify-content:center; gap:8px; margin-top:20px; }
.step-dot {
  width:28px; height:28px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:12px; font-weight:700;
  background:#f1f5f9; color:#94a3b8;
  transition:all 0.3s;
}
.step-dot.active { background:#0d5c45; color:#fff; box-shadow:0 0 0 3px rgba(13,92,69,0.2); }
.step-dot.done   { background:#10b981; color:#fff; }

@media(max-width:700px) {
  .recovery-left { display:none; }
  .recovery-right { padding:24px 16px; }
  .recovery-card  { padding:24px 20px; }
  .code-digit { width:40px; height:48px; font-size:20px; }
}
</style>
