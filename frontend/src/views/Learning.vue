<template>
  <div class="learning-page">
    <div class="learning-header">
      <h1>在线学习</h1>
      <p>探索优质课程和学习资源，提升你的知识技能</p>
    </div>
    
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
</script>

<style scoped>
.learning-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.learning-header {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: #fff;
  padding: 60px 20px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.learning-header h1 {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
}

.learning-header p {
  font-size: 18px;
  opacity: 0.9;
}

.learning-content {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.courses-section {
  margin-bottom: 60px;
}

.resources-section {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

@media (max-width: 768px) {
  .learning-header {
    padding: 40px 20px;
  }
  
  .learning-header h1 {
    font-size: 28px;
  }
  
  .learning-content {
    padding: 20px;
  }
  
  .courses-section {
    margin-bottom: 40px;
  }
}
</style>