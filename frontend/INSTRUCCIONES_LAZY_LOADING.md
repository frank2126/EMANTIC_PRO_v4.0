# 🖼️ INSTRUCCIONES LAZY LOADING — EMANTIC PRO

## Uso del Componente LazyImage

### Instalación

El componente `LazyImage.vue` está en:
```
/frontend/src/components/LazyImage.vue
```

### Uso Básico

```vue
<template>
  <LazyImage
    src="@/assets/manuales-hero.png"
    webpSrc="@/assets/manuales-hero.webp"
    alt="Manuales Hero Image"
    lazy
  />
</template>

<script setup>
import LazyImage from '@/components/LazyImage.vue'
</script>
```

### Uso con srcSet (Responsive)

```vue
<LazyImage
  src="@/assets/manuales-hero.png"
  webpSrc="@/assets/manuales-hero.webp"
  srcSet="
    @/assets/manuales-hero.png 1920w,
    @/assets/manuales-hero.png 1024w,
    @/assets/manuales-hero.png 768w,
    @/assets/manuales-hero.png 480w
  "
  webpSrcSet="
    @/assets/manuales-hero.webp 1920w,
    @/assets/manuales-hero.webp 1024w,
    @/assets/manuales-hero.webp 768w,
    @/assets/manuales-hero.webp 480w
  "
  alt="Manuales"
  width="1920"
  height="600"
  lazy
/>
```

### Props

| Prop | Tipo | Descripción |
|------|------|-------------|
| `src` | String | Imagen PNG (fallback) |
| `webpSrc` | String | Imagen WebP (preferida) |
| `alt` | String | Texto alternativo |
| `width` | Number/String | Ancho de la imagen |
| `height` | Number/String | Alto de la imagen |
| `srcSet` | String | srcSet para PNG responsive |
| `webpSrcSet` | String | srcSet para WebP responsive |
| `lazy` | Boolean | Activar lazy loading (default: true) |
| `classes` | String | Clases CSS personalizadas |

### Eventos

```vue
<LazyImage
  src="..."
  @load="onImageLoaded"
  @error="onImageError"
/>
```

### Ejemplo Completo: Manuals.vue

```vue
<template>
  <div class="manuals-container">
    <!-- Hero con lazy loading -->
    <div class="hero-section">
      <LazyImage
        src="@/assets/manuales-hero.png"
        webpSrc="@/assets/manuales-hero.webp"
        alt="Manuales Hero"
        lazy
        classes="hero-image"
      />
    </div>

    <!-- Resto del contenido -->
  </div>
</template>

<script setup>
import LazyImage from '@/components/LazyImage.vue'
import manualsHeroImg from '../assets/manuales-hero.png'
import manualsHeroWebp from '../assets/manuales-hero.webp'

// Ya no necesitas los imports directos
</script>

<style scoped>
.hero-image {
  width: 100%;
  height: auto;
  min-height: 300px;
  object-fit: cover;
}
</style>
```

## Ventajas del Lazy Loading

✅ **Carga Inicial Más Rápida**
- Solo carga imágenes visibles
- Hero images se cargan cuando el usuario scrollea
- Menos datos en carga inicial

✅ **WebP Automático**
- Navegadores modernos → WebP (25% más pequeño)
- Navegadores antiguos → PNG fallback
- Mejor compatibilidad

✅ **Responsive**
- srcSet automático según resolución
- Menos datos en dispositivos móviles
- Mejor UX en conexiones lentas

✅ **Progressive Enhancement**
- Funciona sin JavaScript (loading="lazy")
- Fallback a Intersection Observer en navegadores antiguos
- Siempre carga algo

## Impacto Esperado

### Antes
```
Carga inicial: ~18 MB
├─ Todas las imágenes descargadas
└─ Hero images cargadas incluso si no se ven
```

### Después
```
Carga inicial: ~50 KB (sin imágenes)
└─ Solo HTML/CSS/JS

Al scrollear:
├─ Imagen visible → Carga WebP (100-200 KB)
└─ Carga progresiva según lo que ve el usuario
```

## Performance

### Core Web Vitals

**LCP (Largest Contentful Paint):**
- Antes: ~3-4 segundos
- Después: ~1-2 segundos

**FID (First Input Delay):**
- Sin cambios (no afecta)

**CLS (Cumulative Layout Shift):**
- Mejora si especificas width/height
- Previene reflow al cargar imagen

## Tamaño de Bundle

### JavaScript
```
Sin cambios (componente es pequeño)
```

### Imágenes
```
Descarga inicial: 0 KB (lazy loading)
Total en un viaje completo: ~2-3 MB
Ahorro: ~15 MB en visitas parciales
```

## Build de Producción

Las imágenes WebP se incluyen automáticamente:

```bash
npm run build
```

Vite optimizará automáticamente:
✅ Compresión de PNG
✅ Conversión a WebP
✅ Hashing de archivos
✅ Source maps

---

## Checklist de Implementación

### Paso 1: Verificar Imágenes
- [x] PNG comprimido
- [x] WebP generado
- [x] Archivos en assets/
- [x] Archivos en public/icons/

### Paso 2: Crear Componente
- [x] LazyImage.vue creado
- [ ] Agregar a componentes globales (opcional)

### Paso 3: Actualizar Vistas
- [ ] Manuals.vue → LazyImage
- [ ] Documentation.vue → LazyImage
- [ ] Maintenance.vue → LazyImage
- [ ] Resources.vue → LazyImage
- [ ] Dashboard.vue → LazyImage (logos)

### Paso 4: Build y Test
- [ ] npm run build
- [ ] Verificar tamaño de bundle
- [ ] Verificar imágenes cargan correctamente
- [ ] Test en mobile
- [ ] Test en conexión 3G (DevTools)

### Paso 5: Deploy
- [ ] Verificar en staging
- [ ] Verificar métricas de performance
- [ ] Deploy a producción

---

## Notas Importantes

⚠️ **No Cambies Diseño**
- Las imágenes siguen siendo idénticas
- Solo cambia cómo se cargan
- Identidad visual preservada

⚠️ **Compatibilidad**
- WebP: 95%+ de navegadores (2020+)
- PNG fallback: 100% de navegadores
- Lazy loading: Soporte nativo + polyfill

⚠️ **Métricas de Importancia**
- Primero: Carga inicial (más importante)
- Segundo: Total de datos (importante)
- Tercero: Rendering (menos importante)

---

**Instrucciones Completas ✅**
