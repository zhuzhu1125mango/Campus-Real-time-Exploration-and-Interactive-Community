<script setup lang="ts">
import EventCalendar from '../components/EventCalendar.vue'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'
</script>

<template>
  <div class="events-page container-wide page-padding">
    <SectionHeader
      title="校园活动"
      subtitle="发现和参与校园内的各种活动"
      icon="i-ep-calendar"
    />

    <GlassCard :hover="false" class="events-card">
      <EventCalendar />
    </GlassCard>
  </div>
</template>

<style scoped>
.events-page {
  min-height: calc(100vh - 200px);
}

.events-card {
  overflow: visible;
}
</style>
