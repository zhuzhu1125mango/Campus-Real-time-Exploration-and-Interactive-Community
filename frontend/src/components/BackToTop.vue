<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
let scrollHandler: () => void

const checkScroll = () => {
  visible.value = (window.scrollY || document.documentElement.scrollTop) > 400
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  scrollHandler = checkScroll
  window.addEventListener('scroll', scrollHandler, { passive: true })
  checkScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', scrollHandler)
})
</script>

<template>
  <transition name="fade-scale">
    <button
      v-show="visible"
      type="button"
      class="back-to-top"
      aria-label="返回顶部"
      @click="scrollToTop"
    >
      <span class="i-ep-arrow-up" />
    </button>
  </transition>
</template>

<style scoped>
.back-to-top {
  position: fixed;
  right: var(--space-6);
  bottom: var(--space-6);
  z-index: 90;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-float);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  color: var(--text-secondary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.back-to-top:hover {
  color: var(--primary-600);
  background: var(--bg-primary);
  transform: translateY(-2px);
}

.dark .back-to-top:hover {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.back-to-top span {
  width: 20px;
  height: 20px;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.2s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(10px);
}
</style>
