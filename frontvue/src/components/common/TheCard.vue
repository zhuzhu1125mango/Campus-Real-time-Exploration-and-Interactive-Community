<template>
  <div :class="cardClass" :style="cardStyle">
    <div v-if="header" class="card-header">
      <slot name="header">{{ header }}</slot>
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
    <div v-if="footer" class="card-footer">
      <slot name="footer">{{ footer }}</slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  header: {
    type: String,
    default: ''
  },
  footer: {
    type: String,
    default: ''
  },
  shadow: {
    type: String,
    default: 'default',
    validator: (value: string) => {
      return ['default', 'hover', 'always'].includes(value)
    }
  },
  bordered: {
    type: Boolean,
    default: true
  },
  padding: {
    type: String,
    default: '16px'
  },
  className: {
    type: String,
    default: ''
  }
})

const cardClass = computed(() => {
  return {
    'the-card': true,
    'the-card--bordered': props.bordered,
    'the-card--shadow-default': props.shadow === 'default',
    'the-card--shadow-hover': props.shadow === 'hover',
    'the-card--shadow-always': props.shadow === 'always',
    [props.className]: props.className
  }
})

const cardStyle = computed(() => {
  return {
    padding: props.padding
  }
})
</script>

<style scoped>
.the-card {
  background-color: #fff;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.the-card--bordered {
  border: 1px solid #e8e8e8;
}

.the-card--shadow-default {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.the-card--shadow-hover:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.the-card--shadow-always {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card-header {
  padding: 12px 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.card-body {
  min-height: 100px;
}

.card-footer {
  padding: 12px 0;
  border-top: 1px solid #e8e8e8;
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>