<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  action?: { label: string; to?: string; onClick?: () => void }
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  class?: string
}

withDefaults(defineProps<Props>(), {
  padding: 'md',
  hover: true,
})

const paddingMap = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
}
</script>

<template>
  <div
    class="glass-card"
    :class="[
      paddingMap[padding],
      { 'glass-card-hover': hover },
      $props.class,
    ]"
  >
    <div v-if="title || $slots.header" class="glass-card-header">
      <div v-if="title" class="glass-card-titles">
        <h3 class="glass-card-title">{{ title }}</h3>
        <p v-if="subtitle" class="glass-card-subtitle">{{ subtitle }}</p>
      </div>
      <slot name="header" />
      <router-link
        v-if="action?.to"
        :to="action.to"
        class="glass-card-action"
      >
        {{ action.label }}
      </router-link>
      <button
        v-else-if="action?.onClick"
        type="button"
        class="glass-card-action"
        @click="action.onClick"
      >
        {{ action.label }}
      </button>
    </div>
    <div class="glass-card-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.glass-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  transition: all 0.25s ease;
}

.glass-card-hover:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.glass-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.glass-card-titles {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.glass-card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.glass-card-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.glass-card-action {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--primary-600);
  white-space: nowrap;
  transition: color 0.2s;
}

.glass-card-action:hover {
  color: var(--primary-500);
}

.dark .glass-card-action {
  color: var(--primary-400);
}

.glass-card-body {
  color: var(--text-primary);
}
</style>
