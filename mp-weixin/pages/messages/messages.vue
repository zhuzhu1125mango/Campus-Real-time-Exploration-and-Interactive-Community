<template>
  <view class="container">
    <view class="search-header">
      <view class="search-box">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          v-model="searchQuery"
          type="text"
          placeholder="搜索联系人..."
          confirm-type="search"
        />
        <text v-if="searchQuery" class="clear-icon" @click="searchQuery = ''">✕</text>
      </view>
    </view>

    <view class="loading" v-if="loading && conversations.length === 0">
      <view class="loading-spinner"></view>
      <text>加载中...</text>
    </view>

    <view class="empty-tip" v-else-if="!loading && filteredConversations.length === 0">
      <view class="empty-icon">💬</view>
      <text>{{ searchQuery ? '未找到匹配的联系人' : '暂无消息' }}</text>
      <text v-if="!searchQuery" class="sub-tip">添加好友后开始聊天</text>
      <button v-if="!searchQuery" class="add-friend-btn" @click="goToFriends">去添加好友</button>
    </view>

    <scroll-view v-else class="conversation-list" scroll-y refresher-enabled :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh" @scrolltolower="loadMore">
      <view class="conversation-item" v-for="item in filteredConversations" :key="item.user.id"
        @click="goToChat(item.user.id, item.user.username)">
        <image class="avatar" :src="formatAvatar(item.user.avatar)" mode="aspectFill" />
        <view class="content">
          <view class="header">
            <text class="username">{{ item.user.username }}</text>
            <text class="time">{{ formatTime(item.last_message?.created_at) }}</text>
          </view>
          <view class