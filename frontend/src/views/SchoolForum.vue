<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { schoolApi } from '@/api/school'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '@/utils/error'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const schoolId = Number(route.params.schoolId)
  if (isNaN(schoolId) || schoolId <= 0) {
    ElMessage.error('无效的学校ID')
    router.replace('/forum')
    return
  }

  try {
    const board = await schoolApi.getSchoolForum(schoolId)
    if (board?.id) {
      router.replace(`/forum/board/${board.id}`)
    } else {
      ElMessage.error('该学校尚未开通论坛')
      router.replace('/forum')
    }
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err, '进入学校论坛失败'))
    router.replace('/forum')
  }
})
</script>

<template>
  <div class="school-forum-redirect container page-padding">
    <SectionHeader
      title="学校论坛"
      subtitle="正在为你跳转至对应学校论坛..."
      icon="i-mdi-school"
    />
    <GlassCard class="loading-card" :hover="false">
      <div class="loading-state">
        <el-skeleton :rows="3" animated />
        <p class="loading-text">正在进入学校论坛...</p>
      </div>
    </GlassCard>
  </div>
</template>

<style scoped>
.school-forum-redirect {
  max-width: 1200px;
}

.loading-card {
  padding: var(--space-8);
}

.loading-state {
  padding: var(--space-8) 0;
  text-align: center;
}

.loading-text {
  margin-top: var(--space-4);
  color: var(--text-secondary);
  font-size: 0.95rem;
}
</style>
