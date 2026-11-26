<template>
  <view class="container">
    <view class="hero">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">校园实时互动社区</text>
      <text class="app-version">版本 {{ version }}</text>
    </view>

    <view class="card">
      <view class="card-title">关于本应用</view>
      <text class="card-text">
        面向高校学生的校园社区应用，提供院校查询、校园论坛、在线学习、实时聊天、
        校园活动与内容分享等能力，帮助同学快速融入校园生活。
      </text>
    </view>

    <view class="card">
      <view class="card-title">主要功能</view>
      <view class="feature" v-for="item in features" :key="item">
        <text class="dot">•</text>
        <text class="feature-text">{{ item }}</text>
      </view>
    </view>

    <view class="footer">© {{ year }} 校园实时互动社区</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'

const version = ref('1.0.0')
const year = new Date().getFullYear()
const features = [
  '院校查询与分数线、院校收藏',
  '校园论坛、板块与标签聚合',
  '内容中心与富文本发布',
  '在线学习与课程进度',
  '公共聊天室与私信',
  '校园活动报名与好友管理'
]
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 40rpx 30rpx;
}

.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0 60rpx;
}

.logo {
  width: 140rpx;
  height: 140rpx;
  border-radius: 28rpx;
  margin-bottom: 24rpx;
}

.app-name {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 10rpx;
}

.app-version {
  font-size: 24rpx;
  color: #999;
}

.card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
}

.card-text {
  font-size: 26rpx;
  color: #666;
  line-height: 1.8;
}

.feature {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12rpx;
}

.feature:last-child {
  margin-bottom: 0;
}

.dot {
  color: #4361ee;
  margin-right: 12rpx;
  font-size: 26rpx;
}

.feature-text {
  flex: 1;
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
}

.footer {
  text-align: center;
  font-size: 22rpx;
  color: #bbb;
  margin-top: 40rpx;
}
</style>
