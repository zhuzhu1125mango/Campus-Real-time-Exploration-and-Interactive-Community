<script setup lang="ts">
interface Props {
  icon: string
  label: string
  description?: string
  to?: string
  color?: 'primary' | 'orange' | 'green' | 'red' | 'purple'
}

withDefaults(defineProps<Props>(), {
  color: 'primary',
})

const colorMap: Record<string, { bg: string; light: string; icon: string }> = {
  primary: { bg: 'var(--primary-600)', light: 'var(--primary-50)', icon: 'var(--primary-600)' },
  orange: { bg: 'var(--accent-orange)', light: 'var(--accent-orange-light)', icon: 'var(--accent-orange)' },
  green: { bg: 'var(--accent-green)', light: 'var(--accent-green-light)', icon: 'var(--accent-green)' },
  red: { bg: 'var(--error-color)', light: 'var(--error-bg)', icon: 'var(--error-color)' },
  purple: { bg: '#8b5cf6', light: '#f3e8ff', icon: '#8b5cf6' },
}
</script>

<template>
  <component
    :is="to ? 'router-link' : 'button'"
    :to="to"
    type="button"
    class="quick-action"
    :style="{
      '--qa-bg': colorMap[color].bg,
      '--qa-light': colorMap[color].light,
      '--qa-icon': colorMap[color].icon,
    }"
  >
    <span class="quick-action-icon" :class="icon" />
    <div class="quick-action-text">
      <span class="quick-action-label">{{ label }}</span>
      <span v-if="description" class="quick-action-desc">{{ description }}</span>
    </div>
  </component>
</template>

<style scoped>
.quick-action {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  text-align: left;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.quick-action:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--qa-bg);
}

.quick-action-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  background: var(--qa-light);
  color: var(--qa-icon);
}

.quick-action-icon::before {
  width: 22px;
  height: 22px;
}

.quick-action-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-action-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.quick-action-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
</style>
