<template>
  <div class="dashboard-view">
    <h1>数据仪表盘</h1>
    <Dashboard />
  </div>
</template>

<script setup lang="ts">
import Dashboard from '@/components/Dashboard.vue'
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
  font-size: 24px;
  color: #333;
}
</style>