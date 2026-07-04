<template>
  <div class="tag-cloud">
    <h3 class="tag-cloud-title">{{ title }}</h3>
    <div class="tags-container">
      <span 
        v-for="tag in tags" 
        :key="tag.id"
        class="tag-item"
        :class="getTagClass(tag)"
        @click="$emit('select', tag)"
      >
        {{ tag.name }}
        <span class="tag-count">{{ tag.count }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Tag {
  id: number
  name: string
  count: number
}

const props = withDefaults(defineProps<{
  tags: Tag[]
  title?: string
  maxSize?: number
}>(), {
  title: '热门标签',
  maxSize: 15
})

defineEmits<{
  (e: 'select', tag: Tag): void
}>()

const getTagClass = (tag: Tag) => {
  const maxCount = Math.max(...props.tags.map(t => t.count), 1)
  const ratio = tag.count / maxCount
  
  if (ratio >= 0.7) return 'tag-large'
  if (ratio >= 0.4) return 'tag-medium'
  return 'tag-small'
}
</script>

<style scoped>
.tag-cloud {
  padding: 1rem;
}

.tag-cloud-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #333;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.tag-small {
  background-color: #f0f4ff;
  color: #4361ee;
  font-size: 0.85rem;
}

.tag-small:hover {
  background-color: #e0e8ff;
}

.tag-medium {
  background-color: #e0e8ff;
  color: #4361ee;
  font-size: 0.95rem;
}

.tag-medium:hover {
  background-color: #d0d8ff;
}

.tag-large {
  background-color: #4361ee;
  color: white;
  font-size: 1rem;
}

.tag-large:hover {
  background-color: #3650d4;
}

.tag-count {
  opacity: 0.7;
  font-size: 0.8em;
}
</style>