<template>
  <!-- 第一篇帖子（主题内容） -->
  <div v-if="firstPost" class="post first-post">
    <div class="post-author">
      <!-- 作者信息... -->
    </div>
    <div class="post-content">
      <div class="post-body rich-content" v-html="sanitizeHtml(firstPost.content)"></div>
      <div class="post-footer">
        <!-- 底部信息... -->
        <div v-if="firstPost.is_edited" class="post-edited-info">
          (已编辑于 {{ firstPost.edited_at }})
        </div>
        <div class="post-actions">
          <div class="action-left">
            <button 
              class="btn-like" 
              :class="{ liked: firstPost.is_liked }"
              @click="toggleLikePost(firstPost.id)"
            >
              <span class="icon-like">👍</span>
              <span>{{ firstPost.like_count || 0 }}</span>
            </button>
          </div>
          <div class="action-right">
            <button class="btn-report" @click="openReportModal(firstPost.id)">
              <span class="icon-report">🚩</span>
              <span>举报</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 回复帖子 -->
  <div v-for="post in replyPosts" :key="post.id" class="post reply-post">
    <div class="post-author">
      <!-- 作者信息... -->
    </div>
    <div class="post-content">
      <!-- 普通显示模式 -->
      <div>
        <div class="post-body rich-content" v-html="sanitizeHtml(post.content)"></div>
        
        <!-- 帖子状态提示 -->
        <div v-if="post.content_status !== 'approved'" class="post-status-info">
          <span class="status-badge" :class="post.content_status">
            {{ post.content_status }}
          </span>
          <span v-if="post.review_note" class="review-note">
            审核备注: {{ post.review_note }}
          </span>
        </div>
        
        <div class="post-footer">
          <!-- 底部信息... -->
          <div v-if="post.is_edited" class="post-edited-info">
            (已编辑于 {{ post.edited_at }})
          </div>
          <div class="post-actions">
            <div class="action-left">
              <button 
                class="btn-like" 
                :class="{ liked: post.is_liked }"
                @click="toggleLikePost(post.id)"
              >
                <span class="icon-like">👍</span>
                <span>{{ post.like_count || 0 }}</span>
              </button>
            </div>
            <div class="action-right">
              <button class="btn-report" @click="openReportModal(post.id)">
                <span class="icon-report">🚩</span>
                <span>举报</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 举报弹窗 -->
  <div v-if="showReportModal" class="modal-overlay" @click.self="closeReportModal">
    <div class="modal-content">
      <h3>举报帖子</h3>
      <div class="report-form">
        <label>举报原因</label>
        <textarea 
          v-model="reportReason" 
          placeholder="请描述举报原因..."
          rows="4"
        ></textarea>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeReportModal">取消</button>
          <button class="btn-submit" @click="submitReport">提交举报</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { forumApi } from '../api/forum'
import { sanitizeHtml } from '../utils/xss'
import type { Topic, Post } from '../types/forum'

// 路由
const route = useRoute();

// 帖子和主题数据
const topic = ref<Topic | null>(null);
const posts = ref<Post[]>([]);
const firstPost = ref<Post | null>(null);

// 举报相关
const showReportModal = ref(false);
const reportedPostId = ref<number | null>(null);
const reportReason = ref('');

// 计算属性：回复帖子（非首帖）
const replyPosts = computed(() => {
  return posts.value.filter(p => p && !p.is_first_post);
});

// 加载状态
const loading = ref(true);
const error = ref<string | null>(null);

// 点赞帖子
const toggleLikePost = async (postId: number) => {
  try {
    const post = posts.value.find(p => p.id === postId);
    if (!post) return;
    
    if (post.is_liked) {
      await forumApi.unlikePost(postId);
      post.is_liked = false;
      post.like_count = (post.like_count || 1) - 1;
    } else {
      await forumApi.likePost(postId);
      post.is_liked = true;
      post.like_count = (post.like_count || 0) + 1;
    }
  } catch (err) {
    console.error('点赞失败:', err);
    alert('操作失败，请稍后重试');
  }
};

// 打开举报弹窗
const openReportModal = (postId: number) => {
  reportedPostId.value = postId;
  reportReason.value = '';
  showReportModal.value = true;
};

// 关闭举报弹窗
const closeReportModal = () => {
  showReportModal.value = false;
  reportedPostId.value = null;
  reportReason.value = '';
};

// 提交举报
const submitReport = async () => {
  if (!reportedPostId.value || !reportReason.value.trim()) {
    alert('请填写举报原因');
    return;
  }
  
  try {
    await forumApi.reportPost(reportedPostId.value, reportReason.value);
    alert('举报成功，管理员将尽快处理');
    closeReportModal();
  } catch (err) {
    console.error('举报失败:', err);
    alert('举报失败，请稍后重试');
  }
};

// 加载主题和帖子
const loadTopicAndPosts = async () => {
  const topicId = Number(route.params.id);
  if (!topicId) return;
  
  loading.value = true;
  try {
    // 获取主题信息
    topic.value = await forumApi.getTopic(topicId);
    
    // 获取主题的所有帖子
    const response = await forumApi.getTopicPosts(topicId, 1);
    posts.value = response.results;
    
    // 设置首帖
    firstPost.value = posts.value.find(p => p.is_first_post) || null;
  } catch (err) {
    console.error('加载主题失败:', err);
    error.value = '加载失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 初始加载
onMounted(() => {
  loadTopicAndPosts();
});
</script>

<style scoped>
/* 其他样式... */

/* 富文本内容的样式 */
.rich-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 10px 0;
}

.rich-content :deep(p) {
  margin-bottom: 16px;
  line-height: 1.6;
}

.rich-content :deep(h1), 
.rich-content :deep(h2), 
.rich-content :deep(h3), 
.rich-content :deep(h4), 
.rich-content :deep(h5), 
.rich-content :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  line-height: 1.25;
  font-weight: 600;
}

.rich-content :deep(blockquote) {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 16px 0;
}

.rich-content :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 3px;
  padding: 16px;
  overflow: auto;
  margin: 16px 0;
}

.rich-content :deep(code) {
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  padding: 0.2em 0.4em;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

.rich-content :deep(ul), 
.rich-content :deep(ol) {
  padding-left: 2em;
  margin: 16px 0;
}

.rich-content :deep(li) {
  margin: 8px 0;
}

.rich-content :deep(a) {
  color: #0366d6;
  text-decoration: none;
}

.rich-content :deep(a:hover) {
  text-decoration: underline;
}

.post-edited-info {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  font-style: italic;
}

/* 帖子状态 */
.post-status-info {
  margin: 10px 0;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.status-badge.pending {
  background-color: #f39c12;
}

.status-badge.rejected {
  background-color: #e74c3c;
}

.status-badge.flagged {
  background-color: #e67e22;
}

.status-badge.approved {
  background-color: #2ecc71;
}

.review-note {
  font-size: 13px;
  color: #666;
  margin-top: 5px;
}

/* 帖子操作 */
.post-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.action-left, .action-right {
  display: flex;
  gap: 10px;
}

.btn-edit, .btn-delete {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background-color: #f8f9fa;
  border-color: #3498db;
  color: #3498db;
}

.btn-delete:hover {
  background-color: #f8f9fa;
  border-color: #e74c3c;
  color: #e74c3c;
}

.icon-edit::before {
  content: "✏️";
}

.icon-delete::before {
  content: "🗑️";
}

/* 编辑表单 */
.post-edit-form {
  margin-bottom: 20px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  gap: 10px;
}

.btn-cancel {
  padding: 8px 15px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
}

.btn-save {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 15px;
  background-color: #3498db;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.btn-save:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

/* 点赞按钮 */
.btn-like {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 20px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-like:hover {
  background-color: #f8f9fa;
  border-color: #3498db;
  color: #3498db;
}

.btn-like.liked {
  background-color: #e8f5e9;
  border-color: #2ecc71;
  color: #2ecc71;
}

.icon-like {
  font-size: 16px;
}

/* 举报按钮 */
.btn-report {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 20px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-report:hover {
  background-color: #fff5f5;
  border-color: #e74c3c;
  color: #e74c3c;
}

.icon-report {
  font-size: 14px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 24px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #333;
}

.report-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-form label {
  font-weight: 500;
  color: #333;
}

.report-form textarea {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
}

.report-form textarea:focus {
  outline: none;
  border-color: #3498db;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.modal-actions .btn-cancel {
  padding: 8px 16px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
}

.modal-actions .btn-cancel:hover {
  background-color: #e8e8e8;
}

.modal-actions .btn-submit {
  padding: 8px 16px;
  background-color: #e74c3c;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.modal-actions .btn-submit:hover {
  background-color: #c0392b;
}
</style> 