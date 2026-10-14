<template>
  <Transition name="loader">
    <div v-if="state.visible" class="app-loader" role="status" aria-live="polite">
      <img src="/icons/icon-192.png" alt="" class="al-logo" />
      <div class="al-name">EMANTIC</div>
      <div class="al-title">{{ state.title }}</div>
      <div v-if="state.subtitle" class="al-sub">{{ state.subtitle }}</div>
      <div class="al-bar"><i></i></div>
    </div>
  </Transition>
</template>

<script setup>
import { useLoader } from '../loader.js'
const { state } = useLoader()
</script>

<style scoped>
.app-loader {
  position: fixed; inset: 0; z-index: 9998;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px;
  background: linear-gradient(160deg, #094535 0%, #0d6b4f 100%);
}
.al-logo {
  width: 76px; height: 76px; border-radius: 16px; margin-bottom: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .3);
  animation: al-pulse 1.6s ease-in-out infinite;
}
.al-name  { color: #fff; font-size: 20px; font-weight: 800; letter-spacing: 4px; }
.al-title { color: #fff; font-size: 15px; font-weight: 600; margin-top: 6px; }
.al-sub   { color: rgba(255, 255, 255, .6); font-size: 12.5px; }

.al-bar {
  width: 160px; height: 3px; border-radius: 3px; margin-top: 12px;
  background: rgba(255, 255, 255, .18); overflow: hidden;
}
.al-bar i {
  display: block; height: 100%; width: 40%;
  background: #31b079; border-radius: 3px;
  animation: al-slide 1.1s ease-in-out infinite;
}

@keyframes al-slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(350%); } }
@keyframes al-pulse { 50% { transform: scale(1.05); } }

.loader-enter-active, .loader-leave-active { transition: opacity .3s ease; }
.loader-enter-from, .loader-leave-to { opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .al-logo, .al-bar i { animation: none; }
}
</style>    