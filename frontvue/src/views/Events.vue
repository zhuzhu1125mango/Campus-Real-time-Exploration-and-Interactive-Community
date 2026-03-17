<template>
  <div class="events-container">
    <div class="events-header">
      <h1>校园活动</h1>
      <p>发现和参与校园内的各种活动</p>
    </div>
    
    <EventCalendar />
  </div>
</template>

<script setup lang="ts">
import EventCalendar from '../components/EventCalendar.vue'
</script>

<style scoped>
.events-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.events-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 40px 0;
  background: linear-gradient(135deg, #4361ee, #3a56d4);
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.events-header h1 {
  margin: 0 0 10px;
  font-size: 2.5rem;
  font-weight: 700;
}

.events-header p {
  margin: 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .events-container {
    padding: 10px;
  }
  
  .events-header h1 {
    font-size: 2rem;
  }
  
  .events-header p {
    font-size: 1rem;
  }
}
</style>
