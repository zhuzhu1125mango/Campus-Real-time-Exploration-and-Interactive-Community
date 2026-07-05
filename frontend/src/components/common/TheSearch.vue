<template>
  <div class="the-search" :class="searchClass">
    <el-input
      v-model="searchValue"
      :placeholder="placeholder"
      :size="size"
      :disabled="disabled"
      @keyup.enter="handleSearch"
      clearable
      @clear="handleClear"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
      <template #suffix>
        <el-icon v-if="searching" class="is-loading"><Loading /></el-icon>
        <el-icon v-else><Search /></el-icon>
      </template>
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
import { Search, Loading } from '@element-plus/icons-vue'

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