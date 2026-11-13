<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../api/user'
import { getApiErrorMessage } from '../utils/error'
import { useUserStore } from '../stores/userStore'

interface Props {
  userId: number
  following?: boolean
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  following: false,
  size: 'sm',
})

const emit = defineEmits<{
  update: [following: boolean]
}>()

const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)
const currentUserId = computed(() => userStore.user?.id)

const innerFollowing = ref(props.following)
const loading = ref(false)

watch(() => props.following, (val) => {
  innerFollowing.value = val
})

const isSelf = computed(() => props.userId === currentUserId.value)
const show = computed(() => isLoggedIn.value && !isSelf.value)

const toggleFollow = async (event: MouseEvent) => {
  event.stopPropagation()
  if (!isLoggedIn.value || loading.value) return

  loading.value = true
  const nextState = !innerFollowing.value

  try {
    if (nextState) {
      await userApi.followUser(props.userId)
      ElMessage.success('关注成功')
    } else {
      await userApi.unfollowUser(props.userId)
      ElMessage.success('已取消关注')
    }
    innerFollowing.value = nextState
    emit('update', nextState)
  } catch (error) {
    console.error('关注操作失败:', error)
    ElMessage.error(getApiErrorMessage(error, '操作失败，请重试'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button
    v-if="show"
    type="button"
    class="follow-button"
    :class="[
      size,
      { 'is-following': innerFollowing, 'is-loading': loading }
    ]"
    :disabled="loading"
    @click="toggleFollow"
  >
    <span v-if="loading" class="follow-spinner" />
    <template v-else>
      <span v-if="innerFollowing" class="i-ep-check" />
      <span v-else class="i-ep-plus" />
      {{ innerFollowing ? '已关注' : '关注' }}
    </template>
  </button>
</template>

<style scoped>
.follow-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  border-radius: var(--radius-full);
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.follow-button.sm {
  padding: 4px 10px;
  font-size: 0.8rem;
}

.follow-button.md {
  padding: 6px 14px;
  font-size: 0.875rem;
}

.follow-button:not(.is-following) {
  background: var(--primary-50);
  color: var(--primary-600);
  border: 1px solid var(--primary-200);
}

.follow-button:not(.is-following):hover {
  background: var(--primary-600);
  color: var(--text-inverse);
  border-color: var(--primary-600);
}

.follow-button.is-following {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.follow-button.is-following:hover {
  color: var(--error-color);
  border-color: var(--error-color);
  background: var(--error-bg);
}

.dark .follow-button:not(.is-following) {
  background: rgba(37, 99, 235, 0.15);
  color: var(--primary-400);
  border-color: rgba(37, 99, 235, 0.3);
}

.dark .follow-button:not(.is-following):hover {
  background: var(--primary-600);
  color: var(--text-inverse);
}

.dark .follow-button.is-following {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.follow-button span {
  width: 14px;
  height: 14px;
}

.follow-button.is-loading {
  cursor: wait;
}

.follow-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
