<template>
  <el-button
    :type="type"
    :size="size"
    :plain="plain"
    :round="round"
    :circle="circle"
    :disabled="disabled"
    :loading="loading"
    :icon="icon"
    :class="customClass"
    @click="handleClick"
  >
    <slot></slot>
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ButtonType } from 'element-plus'

type ButtonSize = 'large' | 'default' | 'small'

const props = defineProps({
  type: {
    type: String as () => ButtonType,
    default: 'primary'
  },
  size: {
    type: String as () => ButtonSize,
    default: 'medium'
  },
  plain: {
    type: Boolean,
    default: false
  },
  round: {
    type: Boolean,
    default: false
  },
  circle: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  icon: {
    type: String,
    default: ''
  },
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const customClass = computed(() => {
  return {
    [props.className]: props.className
  }
})

const handleClick = (event: MouseEvent) => {
  emit('click', event)
}
</script>

<style scoped>
/* 可以添加自定义样式 */
</style>