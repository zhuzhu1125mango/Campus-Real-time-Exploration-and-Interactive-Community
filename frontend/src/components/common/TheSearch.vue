<template>
  <div class="the-search" :class="searchClass">
    <el-input
      v-model="searchValue"
      :placeholder="placeholder"
      :size="size"
      :prefix-icon="prefixIcon"
      :suffix-icon="searching ? 'el-icon-loading' : 'el-icon-search'"
      :disabled="disabled"
      @keyup.enter="handleSearch"
      clearable
      @clear="handleClear"
    >
      <template v-if="$slots.prepend" #prepend>
        <slot name="prepend"></slot>
      </template>
      <template v-if="$slots.append" #append>
        <slot name="append"></slot>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

type InputSize = 'large' | 'default' | 'small'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入搜索内容'
  },
  size: {
    type: String as () => InputSize,
    default: 'default'
  },
  prefixIcon: {
    type: String,
    default: 'el-icon-search'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', value: string): void
  (e: 'clear'): void
}>()

const searchValue = ref(props.modelValue)
const searching = ref(false)

const searchClass = computed(() => {
  return {
    [props.className]: props.className
  }
})

const handleSearch = () => {
  searching.value = true
  emit('update:modelValue', searchValue.value)
  emit('search', searchValue.value)
  
  // 模拟搜索完成
  setTimeout(() => {
    searching.value = false
  }, 500)
}

const handleClear = () => {
  searchValue.value = ''
  emit('update:modelValue', '')
  emit('clear')
}
</script>

<style scoped>
.the-search {
  width: 100%;
}
</style>