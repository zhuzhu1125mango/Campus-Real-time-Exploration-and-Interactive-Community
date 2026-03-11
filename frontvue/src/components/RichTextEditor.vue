<template>
  <div class="rich-text-editor">
    <QuillEditor
      v-model:content="content"
      :options="editorOptions"
      contentType="html"
      theme="snow"
      toolbar="full"
      @update:content="updateContent"
      @textChange="onTextChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

// 定义组件的props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入内容...'
  }
})

// 定义事件
const emit = defineEmits(['update:modelValue'])

// 编辑器内容
const content = ref(props.modelValue || '')

// 编辑器配置选项
const editorOptions = computed(() => {
  return {
    placeholder: props.placeholder,
    modules: {
      toolbar: [
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ 'header': 1 }, { 'header': 2 }],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        [{ 'indent': '-1' }, { 'indent': '+1' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'align': [] }],
        ['clean'],
        ['link', 'image']
      ],
      imageUploader: {
        upload: (file: File) => {
          return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const reader = new FileReader();
            reader.onload = (e) => {
              if (e.target && e.target.result) {
                resolve(e.target.result.toString());
              } else {
                reject(new Error('图片加载失败'));
              }
            };
            reader.onerror = (e) => {
              reject(new Error('图片加载失败'));
            };
            reader.readAsDataURL(file);
          });
        }
      }
    }
  }
})

// 监听外部v-model变化
watch(() => props.modelValue, (newVal) => {
  if (newVal !== content.value) {
    content.value = newVal
  }
}, { immediate: true })

// 监听内部内容变化并向上传递
const updateContent = (newContent: string) => {
  emit('update:modelValue', newContent)
}

// 文本变化事件处理
const onTextChange = () => {
  if (content.value === '<p><br></p>') {
    // 清空内容时重置为空字符串
    content.value = ''
    emit('update:modelValue', '')
  }
}

// 组件挂载时确保与modelValue同步
onMounted(() => {
  // 确保初始内容与v-model一致
  content.value = props.modelValue
  emit('update:modelValue', content.value)
})
</script>

<style scoped>
.rich-text-editor {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 4px;
}

.rich-text-editor :deep(.ql-toolbar) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  background-color: #f8f9fa;
}

.rich-text-editor :deep(.ql-container) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  min-height: 150px;
}

.rich-text-editor :deep(.ql-editor) {
  min-height: 150px;
  font-size: 16px;
  line-height: 1.6;
}
</style> 