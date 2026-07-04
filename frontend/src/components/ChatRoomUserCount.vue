<template>
  <span class="user-count">
    在线 {{ userCount }} 人
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const userCount = ref(0)

// 导出更新用户计数的方法供外部调用
const updateUserCount = (count: number) => {
  userCount.value = count
}

// 导出给父组件使用
defineExpose({
  updateUserCount
})
</script>

<style scoped>
.user-count {
  padding: 0.25rem 0.5rem;
  background-color: rgba(67, 97, 238, 0.1);
  color: #4361ee;
  border-radius: 12px;
  font-size: 0.85rem;
  display: inline-block;
}
</style> 