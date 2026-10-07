<template>
  <picture :class="classes">
    <!-- WebP para navegadores modernos -->
    <source v-if="webpSrc" :srcset="webpSrcSet" type="image/webp" />
    
    <!-- PNG fallback para navegadores antiguos -->
    <source v-if="srcSet" :srcset="srcSet" type="image/png" />
    
    <!-- Imagen final -->
    <img
      v-bind="imgAttrs"
      :src="src"
      :alt="alt"
      :loading="loading"
      :width="width"
      :height="height"
      @load="onLoad"
      @error="onError"
    />
  </picture>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  webpSrc: {
    type: String,
    default: null
  },
  alt: {
    type: String,
    required: true
  },
  width: {
    type: [Number, String],
    default: null
  },
  height: {
    type: [Number, String],
    default: null
  },
  srcSet: {
    type: String,
    default: null
  },
  webpSrcSet: {
    type: String,
    default: null
  },
  lazy: {
    type: Boolean,
    default: true
  },
  placeholder: {
    type: String,
    default: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3Crect fill="%23f0f0f0"/%3E%3C/svg%3E'
  },
  classes: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['load', 'error'])

const isLoaded = ref(false)
const imgAttrs = computed(() => ({
  class: {
    'lazy-image': props.lazy,
    'lazy-loading': props.lazy && !isLoaded.value,
    'lazy-loaded': props.lazy && isLoaded.value
  }
}))

const loading = computed(() => props.lazy ? 'lazy' : 'eager')

const onLoad = () => {
  isLoaded.value = true
  emit('load')
}

const onError = () => {
  emit('error')
}

onMounted(() => {
  // Si el navegador no soporta lazy loading, usar Intersection Observer
  if (props.lazy && !('loading' in HTMLImageElement.prototype)) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target
          if (img.src === props.placeholder) {
            img.src = props.src
          }
          observer.unobserve(img)
        }
      })
    })
    // observer.observe(document.querySelector('img'))
  }
})
</script>

<style scoped>
.lazy-image {
  transition: opacity 0.3s ease-in-out;
}

.lazy-loading {
  opacity: 0.7;
  background: #f0f0f0;
}

.lazy-loaded {
  opacity: 1;
}

img {
  display: block;
  width: 100%;
  height: auto;
}

picture {
  display: block;
}
</style>
