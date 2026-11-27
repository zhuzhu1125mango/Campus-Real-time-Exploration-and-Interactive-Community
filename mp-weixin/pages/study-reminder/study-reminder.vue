<template>
  <view class="container">
    <view class="card">
      <view class="course-title">{{ courseTitle || '学习提醒' }}</view>
      <view class="desc">每天固定时间提醒你继续学习，完成课程后自动停止。</view>

      <view class="row">
        <text class="label">开启每日提醒</text>
        <switch :checked="isActive" color="#4361ee" @change="onSwitchChange" />
      </view>

      <picker
        mode="time"
        :value="remindTime"
        :disabled="!isActive"
        @change="onTimeChange"
      >
        <view class="row">
          <text class="label">提醒时间</text>
          <text class="time-value" :class="{ disabled: !isActive }">{{ remindTime }}</text>
        </view>
      </picker>
      <view class="picker-tip" v-if="isActive">点击“提醒时间”选择每天提醒的时刻</view>
    </view>

    <view class="actions">
      <button class="save-btn" :disabled="saving" @click="save">
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
      <button v-if="reminderId" class="delete-btn" @click="remove">关闭并删除提醒</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import learningApi from '../../api/learning'
import { requestAndSaveSubscribe, SUBSCRIBE_TEMPLATE_IDS } from '../../utils/wechat'

const courseId = ref('')
const courseTitle = ref('')
const reminderId = ref(null)
const isActive = ref(true)
const remindTime = ref('20:00')
const saving = ref(false)

onLoad(async (options) => {
  if (!uni.getStorageSync('accessToken')) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 800)
    return
  }
  courseId.value = options?.course || ''
  courseTitle.value = options?.title ? decodeURIComponent(options.title) : ''
  if (!courseId.value) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  await loadReminder()
})

const loadReminder = async () => {
  try {
    const res = await learningApi.getReminders()
    const reminder = (res?.results || []).find((item) => String(item.course_id) === String(courseId.value))
    if (reminder) {
      reminderId.value = reminder.id
      isActive.value = reminder.is_active
      remindTime.value = reminder.remind_time
      if (!courseTitle.value) courseTitle.value = reminder.course_title
    }
  } catch (error) {
    console.error('加载学习提醒失败', error)
  }
}

const onSwitchChange = (event) => {
  isActive.value = event.detail.value
}

const onTimeChange = (event) => {
  remindTime.value = event.detail.value
}

const save = async () => {
  if (saving.value) return
  saving.value = true
  try {
    if (reminderId.value) {
      await learningApi.updateReminder(reminderId.value, {
        is_active: isActive.value,
        remind_time: remindTime.value
      })
    } else {
      const created = await learningApi.createReminder({
        course: Number(courseId.value),
        is_active: isActive.value,
        remind_time: remindTime.value
      })
      reminderId.value = created.id
    }
    if (isActive.value && SUBSCRIBE_TEMPLATE_IDS.reminder) {
      // 已配置学习提醒模板时，顺带申请订阅授权（失败不阻塞保存）
      await requestAndSaveSubscribe(['reminder'])
    }
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (error) {
    console.error('保存学习提醒失败', error)
    uni.showToast({ title: error?.detail || '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

const remove = async () => {
  if (!reminderId.value) return
  const res = await new Promise((resolve) => {
    uni.showModal({
      title: '关闭提醒',
      content: '确定关闭并删除该课程的学习提醒吗？',
      success: resolve
    })
  })
  if (!res.confirm) return
  try {
    await learningApi.deleteReminder(reminderId.value)
    uni.showToast({ title: '已关闭', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (error) {
    console.error('删除学习提醒失败', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 30rpx;
}

.card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 36rpx 30rpx;
}

.course-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.desc {
  font-size: 24rpx;
  color: #999;
  line-height: 1.6;
  margin-bottom: 30rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 26rpx 0;
  border-top: 1rpx solid #f5f5f5;
}

.label {
  font-size: 28rpx;
  color: #333;
}

.time-value {
  font-size: 30rpx;
  color: #4361ee;
  font-weight: 600;
}

.time-value.disabled {
  color: #ccc;
}

.picker-hidden {
  display: none;
}

.picker-tip {
  font-size: 22rpx;
  color: #bbb;
  margin-top: 10rpx;
}

.actions {
  margin-top: 30rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.save-btn {
  width: 100%;
  height: 84rpx;
  line-height: 84rpx;
  border-radius: 42rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 30rpx;
  border: none;
}

.delete-btn {
  width: 100%;
  height: 76rpx;
  line-height: 76rpx;
  border-radius: 38rpx;
  background-color: #fff;
  color: #e53935;
  border: 1rpx solid #e53935;
  font-size: 28rpx;
}
</style>
