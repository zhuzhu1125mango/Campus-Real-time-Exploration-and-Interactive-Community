<!-- 回复表单 -->
<div v-if="isLoggedIn" class="reply-form">
  <h3>回复主题</h3>
  <form @submit.prevent="submitReply">
    <div class="form-group">
      <RichTextEditor
        v-model="replyContent"
        placeholder="请输入回复内容..."
      />
    </div>
    <div class="form-footer">
      <button type="submit" class="btn-submit" :disabled="submitting">
        <span v-if="submitting" class="loading-spinner small"></span>
        <span>{{ submitting ? '提交中...' : '提交回复' }}</span>
      </button>
    </div>
  </form>
</div>

<!-- 第一篇帖子（主题内容） -->
<div v-if="firstPost" class="post first-post">
  <div class="post-author">
    <!-- 作者信息... -->
  </div>
  <div class="post-content">
    <div class="post-body rich-content" v-html="firstPost.content"></div>
    <div class="post-footer">
      <!-- 底部信息... -->
      <div v-if="firstPost.is_edited" class="post-edited-info">
        (已编辑于 {{ formatDate(firstPost.edited_at) }})
      </div>
    </div>
  </div>
</div>

<!-- 回复帖子 -->
<div v-for="(post, index) in replyPosts" :key="post.id" class="post reply-post">
  <div class="post-author">
    <!-- 作者信息... -->
  </div>
  <div class="post-content">
    <!-- 编辑模式 -->
    <div v-if="editingPostId === post.id" class="post-edit-form">
      <RichTextEditor
        v-model="editingContent"
        placeholder="请输入内容..."
      />
      <div class="edit-actions">
        <button type="button" class="btn-cancel" @click="cancelEdit">取消</button>
        <button type="submit" class="btn-save" @click="saveEdit" :disabled="saving">
          <span v-if="saving" class="loading-spinner small"></span>
          <span>{{ saving ? '保存中...' : '保存' }}</span>
        </button>
      </div>
    </div>
    
    <!-- 普通显示模式 -->
    <div v-else>
      <div class="post-body rich-content" v-html="post.content"></div>
      
      <!-- 帖子状态提示 -->
      <div v-if="post.content_status !== 'approved'" class="post-status-info">
        <span class="status-badge" :class="post.content_status">
          {{ getStatusText(post.content_status) }}
        </span>
        <span v-if="post.review_note" class="review-note">
          审核备注: {{ post.review_note }}
        </span>
      </div>
      
      <div class="post-footer">
        <!-- 底部信息... -->
        <div v-if="post.is_edited" class="post-edited-info">
          (已编辑于 {{ formatDate(post.edited_at) }})
        </div>
        <div class="post-actions">
          <div class="action-left">
            <button 
              class="btn-like" 
              :class="{ liked: post.is_liked }"
              @click.stop="toggleLike(post.id)"
            >
              <span class="icon-like"></span>
              <span>{{ post.like_count || 0 }}</span>
            </button>
            <button class="btn-report" @click.stop="reportPost(post.id)">
              <span class="icon-report"></span>
              举报
            </button>
          </div>
          
          <div class="action-right" v-if="canEditPost(post)">
            <button class="btn-edit" @click.stop="editPost(post)">
              <span class="icon-edit"></span>
              编辑
            </button>
            <button class="btn-delete" @click.stop="deletePost(post.id)">
              <span class="icon-delete"></span>
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Topic, Post } from '../types/forum'
import config from '../utils/config'
import RichTextEditor from '../components/RichTextEditor.vue'
import { useUserStore } from '../stores/userStore'

// 用户数据
const userStore = useUserStore();
const isLoggedIn = computed(() => userStore.isLoggedIn);

// 路由
const route = useRoute();
const router = useRouter();

// 帖子和主题数据
const topic = ref<Topic | null>(null);
const posts = ref<Post[]>([]);
const firstPost = ref<Post | null>(null);
const replyPosts = computed(() => posts.value.filter(p => !p.is_first_post));

// 加载状态
const loading = ref(true);
const error = ref<string | null>(null);

// 回复状态
const replyContent = ref('');
const submitting = ref(false);

// 编辑相关状态
const editingPostId = ref<number | null>(null);
const editingContent = ref('');
const saving = ref(false);

// 判断是否可以编辑帖子
const canEditPost = (post: Post) => {
  return post.author.id === userStore.user?.id || isAdmin.value;
};

// 是否是管理员或版主
const isAdmin = computed(() => {
  // 在实际项目中需要根据用户权限来判断
  return userStore.user && userStore.user.is_staff;
});

// 开始编辑帖子
const editPost = (post: Post) => {
  editingPostId.value = post.id;
  editingContent.value = post.content;
};

// 取消编辑
const cancelEdit = () => {
  editingPostId.value = null;
  editingContent.value = '';
};

// 保存编辑
const saveEdit = async () => {
  if (!editingPostId.value) return;
  
  saving.value = true;
  try {
    await forumApi.updatePost(editingPostId.value, {
      content: editingContent.value
    });
    
    // 更新帖子内容
    const postIndex = posts.value.findIndex(p => p.id === editingPostId.value);
    if (postIndex !== -1) {
      posts.value[postIndex].content = editingContent.value;
      posts.value[postIndex].is_edited = true;
      posts.value[postIndex].edited_at = new Date().toISOString();
      posts.value[postIndex].content_status = 'pending'; // 设置为待审核状态
    }
    
    // 重置编辑状态
    cancelEdit();
    
    // 提示
    alert('修改已提交，等待审核');
  } catch (error) {
    console.error('保存编辑失败:', error);
    alert('保存失败，请稍后重试');
  } finally {
    saving.value = false;
  }
};

// 转到版块页面
const goToBoard = () => {
  if (topic.value && topic.value.board) {
    router.push(`/forum/board/${topic.value.board}`);
  }
};

// 删除帖子
const deletePost = async (postId: number) => {
  if (!confirm('确定要删除这个帖子吗？此操作无法撤销')) {
    return;
  }
  
  try {
    await forumApi.deletePost(postId);
    
    // 移除帖子
    posts.value = posts.value.filter(p => p.id !== postId);
    
    // 如果是首帖，返回到版块页面
    const post = posts.value.find(p => p.id === postId);
    if (post && post.is_first_post) {
      goToBoard();
    }
  } catch (error) {
    console.error('删除帖子失败:', error);
    alert('删除失败，请稍后重试');
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
    posts.value = response.data.results;
    
    // 设置首帖
    firstPost.value = posts.value.find(p => p.is_first_post) || null;
  } catch (err) {
    console.error('加载主题失败:', err);
    error.value = '加载失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 切换点赞
const toggleLike = async (postId: number) => {
  try {
    const post = posts.value.find(p => p.id === postId);
    if (!post) return;
    
    if (post.is_liked) {
      await forumApi.unlikePost(postId);
      post.like_count = Math.max(0, post.like_count - 1);
    } else {
      await forumApi.likePost(postId);
      post.like_count += 1;
    }
    post.is_liked = !post.is_liked;
  } catch (error) {
    console.error('操作失败:', error);
  }
};

// 举报帖子处理
const reportPost = (postId: number) => {
  const reason = prompt('请输入举报原因:');
  if (!reason) return;
  
  forumApi.reportPost(postId, reason)
    .then(() => {
      alert('举报已提交');
    })
    .catch(error => {
      console.error('举报失败:', error);
      alert('举报失败，请稍后重试');
    });
};

// 提交回复
const submitReply = async () => {
  if (!topic.value || !replyContent.value.trim()) return;
  
  submitting.value = true;
  try {
    await forumApi.replyTopic({ 
      topic: topic.value.id, 
      content: replyContent.value 
    });
    
    // 重新加载帖子
    await loadTopicAndPosts();
    
    // 清空表单
    replyContent.value = '';
    
  } catch (error) {
    console.error('回复失败:', error);
    alert('回复失败，请稍后重试');
  } finally {
    submitting.value = false;
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

// 初始加载
onMounted(() => {
  loadTopicAndPosts();
});

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'flagged': '已标记'
  };
  return statusMap[status] || status;
};

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
</style> 