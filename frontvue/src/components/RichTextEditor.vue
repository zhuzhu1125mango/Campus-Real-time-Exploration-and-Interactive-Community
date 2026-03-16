<template>
  <div class="rich-text-editor">
    <Editor
      v-model="content"
      :init="editorOptions"
      @editorChange="onEditorChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import Editor from '@tinymce/tinymce-vue'

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
    height: 300,
    menubar: false,
    plugins: [
      'advlist autolink lists link image charmap print preview anchor',
      'searchreplace visualblocks code fullscreen',
      'insertdatetime media table paste code help wordcount'
    ],
    toolbar: 'undo redo | formatselect | bold italic backcolor | ' +
             'alignleft aligncenter alignright alignjustify | ' +
             'bullist numlist outdent indent | removeformat | help | ' +
             'link image',
    images_upload_handler: function (blobInfo: any, success: any, failure: any) {
      // 图片上传处理，使用FileReader将图片转换为base64
      const reader = new FileReader();
      reader.onload = function () {
        if (reader.result) {
          success(reader.result as string);
        } else {
          failure('图片加载失败');
        }
      };
      reader.onerror = function () {
        failure('图片加载失败');
      };
      reader.readAsDataURL(blobInfo.blob());
    }
  }
})

// 监听外部v-model变化
watch(() => props.modelValue, (newVal) => {
  if (newVal !== content.value) {
    content.value = newVal
  }
}, { immediate: true })

// 编辑器内容变化事件处理
const onEditorChange = () => {
  if (content.value === '<p><br></p>') {
    // 清空内容时重置为空字符串
    content.value = ''
    emit('update:modelValue', '')
  } else {
    emit('update:modelValue', content.value)
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

.rich-text-editor :deep(.tox-tinymce) {
  border-radius: 4px;
}

.rich-text-editor :deep(.tox-editor-container) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

.rich-text-editor :deep(.tox-toolbar-overlord) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  background-color: #f8f9fa;
}
</style>