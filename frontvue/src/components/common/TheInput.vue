<template>
  <div class="the-input" :class="inputClass">
    <label v-if="label" class="input-label">{{ label }}</label>
    <el-input
      :type="type"
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :size="size"
      :maxlength="maxlength"
      :show-word-limit="showWordLimit"
      :prefix-icon="prefixIcon"
      :suffix-icon="suffixIcon"
      :clearable="clearable"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
      @clear="handleClear"
    >
      <template v-if="$slots.prefix" #prefix>
        <slot name="prefix"></slot>
      </template>
      <template v-if="$slots.suffix" #suffix>
        <slot name="suffix"></slot>
      </template>
    </el-input>
    <div v-if="error" class="input-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InputType } from 'element-plus'

type InputSize = 'large' | 'default' | 'small'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  type: {
    type: String as () => InputType,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  size: {
    type: String as () => InputSize,
    default: 'default'
  },
  maxlength: {
    type: Number,
    default: 0
  },
  showWordLimit: {
    type: Boolean,
    default: false
  },
  prefixIcon: {
    type: String,
    default: ''
  },
  suffixIcon: {
    type: String,
    default: ''
  },
  clearable: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
  (e: 'input', value: string | number): void
  (e: 'blur', event: FocusEvent): void
  (e: 'focus', event: FocusEvent): void
  (e: 'clear'): void
}>()

const inputClass = computed(() => {
  return {
    'the-input--has-error': props.error,
    [props.className]: props.className
  }
})

const handleInput = (value: string | number) => {
  emit('update:modelValue', value)
  emit('input', value)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleClear = () => {
  emit('clear')
}
</script>

<style scoped>
.the-input {
  margin-bottom: 16px;
}

.input-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.input-error {
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
}
</style>