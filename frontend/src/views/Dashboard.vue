<template>
  <div class="dashboard-page container-wide page-padding">
    <SectionHeader
      title="学习仪表盘"
      subtitle="今日学习状态概览"
      icon="i-ep-data-board"
    />
    <Dashboard />
  </div>
</template>

<script setup lang="ts">
import SectionHeader from '@/components/SectionHeader.vue'
import Dashboard from '@/components/Dashboard.vue'
</script>

<style scoped>
.dashboard-page {
  min-height: 100%;
}
</style>
