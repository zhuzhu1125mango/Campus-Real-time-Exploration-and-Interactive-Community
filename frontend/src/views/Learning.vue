<template>
  <div class="learning-page container-wide page-padding">
    <SectionHeader
      title="课程中心"
      subtitle="发现优质课程，开启学习之旅"
      icon="i-ep-reading"
    />

    <div class="learning-content">
      <div class="courses-section">
        <CourseList title="推荐课程" />
      </div>

      <div class="resources-section">
        <LearningResources title="学习资源" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CourseList from '../components/CourseList.vue'
import LearningResources from '../components/LearningResources.vue'
import SectionHeader from '../components/SectionHeader.vue'
</script>

<style scoped>
.learning-page {
  min-height: 100vh;
  background: var(--bg-secondary);
}

.learning-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.courses-section,
.resources-section {
  width: 100%;
}

@media (max-width: 640px) {
  .learning-content {
    gap: var(--space-6);
  }
}
</style>
