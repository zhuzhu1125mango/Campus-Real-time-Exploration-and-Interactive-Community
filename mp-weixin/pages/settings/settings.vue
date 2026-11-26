<template>
  <view class="container">
    <view class="group">
      <view class="group-title">通知</view>
      <view class="cell" @click="openSubscribeSettings">
        <text class="cell-label">通知设置</text>
        <text class="cell-value">{{ subscribeState }}</text>
        <text class="arrow">></text>
      </view>
    </view>

    <view class="group">
      <view class="group-title">通用</view>
      <view class="cell" @click="clearCache">
        <text class="cell-label">清除缓存</text>
        <text class="arrow">></text>
      </view>
      <view class="cell" @click="goAbout">
        <text class="cell-label">关于我们</text>
        <text class="arrow">></text>
      </view>
    </view>

    <view class="version">版本 {{ version }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { requestAndSaveSubscribe, SUBSCRIBE_TEMPLATE_KEYS } from '../../utils/wechat'

const version = ref('1.0.0')
const subscribeState = ref('去设置')

const openSubscribeSettings = async () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  const accepted = await requestAndSaveSubscribe(SUBSCRIBE_TEMPLATE_KEYS)
  subscribeState.value = accepted.length ? '已开启' : '未开启'
  uni.showToast({
    title: accepted.length ? '已开启通知' : '未开启通知',
    icon: 'none'
  })
}

const clearCache = () => {
  uni.showModal({
    title: '清除缓存',
    content: '将清除本地缓存的图片与临时数据，不会退出登录。',
    success: (res) => {
      if (!res.confirm) return
      try {
        const info = uni.getStorageInfoSync()
        info.keys
          .filter((key) => key.startsWith('cache_'))
          .forEach((key) => uni.removeStorageSync(key))
        uni.showToast({ title: '已清除', icon: 'success' })
      } catch (error) {
        console.error('清除缓存失败:', error)
        uni.showToast({ title: '清除失败', icon: 'none' })
      }
    }
  })
}

const goAbout = () => {
  uni.navigateTo({ url: '/pages/about/about' })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-top: 20rpx;
}

.group {
  background-color: #fff;
  margin-bottom: 20rpx;
}

.group-title {
  font-size: 24rpx;
  color: #999;
  padding: 24rpx 30rpx 10rpx;
}

.cell {
  display: flex;
  align-items: center;
  padding: 30rpx;
  border-top: 1rpx solid #f5f5f5;
}

.cell-label {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.cell-value {
  font-size: 26rpx;
  color: #999;
  margin-right: 12rpx;
}

.arrow {
  font-size: 28rpx;
  color: #ccc;
}

.version {
  text-align: center;
  font-size: 24rpx;
  color: #bbb;
  margin-top: 60rpx;
}
</style>
