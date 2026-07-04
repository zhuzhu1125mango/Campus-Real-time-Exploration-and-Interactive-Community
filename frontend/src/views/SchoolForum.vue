<template>
  <div class="school-forum-redirect">
    <div class="loading-state">
      <el-skeleton :rows="3" animated />
      <p>正在进入学校论坛...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { schoolApi } from '@/api/school'
import { ElMessage } from 'element-plus'

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
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '进入学校论坛失败'
    ElMessage.error(msg)
    router.replace('/forum')
  }
})
</script>

<style scoped>
.school-forum-redirect {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.loading-state {
  padding: 4rem 0;
  text-align: center;
}
</style>
