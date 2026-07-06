<script setup lang="ts">
import { isDark, toggleDark } from '@/composables/useTheme'
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="isDark ? '切换到浅色模式' : '切换到暗色模式'"
    @click="toggleDark()"
  >
    <span
      class="icon"
      :class="isDark ? 'i-ep-moon' : 'i-ep-sunny'"
    />
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  background: transparent;
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  color: var(--primary-600);
  background: var(--primary-50);
}

.dark .theme-toggle:hover {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.icon {
  width: 20px;
  height: 20px;
}
</style>
