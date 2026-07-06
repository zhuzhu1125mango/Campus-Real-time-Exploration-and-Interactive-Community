<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
  action?: { label: string; to?: string; onClick?: () => void }
  icon?: string
}

defineProps<Props>()
</script>

<template>
  <div class="section-header">
    <div class="section-header-main">
      <span v-if="icon" class="section-header-icon" :class="icon" />
      <div class="section-header-titles">
        <h2 class="section-header-title">{{ title }}</h2>
        <p v-if="subtitle" class="section-header-subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <router-link
      v-if="action?.to"
      :to="action.to"
      class="section-header-action"
    >
      {{ action.label }}
    </router-link>
    <button
      v-else-if="action?.onClick"
      type="button"
      class="section-header-action"
      @click="action.onClick"
    >
      {{ action.label }}
    </button>
  </div>
</template>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.section-header-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.section-header-icon {
  width: 24px;
  height: 24px;
  color: var(--primary-600);
}

.dark .section-header-icon {
  color: var(--primary-400);
}

.section-header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section-header-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.section-header-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.section-header-action {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--primary-600);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.section-header-action:hover {
  color: var(--primary-500);
  background: var(--primary-50);
}

.dark .section-header-action {
  color: var(--primary-400);
}

.dark .section-header-action:hover {
  background: var(--bg-tertiary);
}

@media (max-width: 640px) {
  .section-header {
    flex-wrap: wrap;
  }

  .section-header-main {
    width: 100%;
  }
}
</style>
