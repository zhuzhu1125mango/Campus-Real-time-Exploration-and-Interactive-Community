<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'radix-vue'

export interface NavDropdownItem {
  label: string
  icon?: string
  to?: string
  divider?: boolean
  danger?: boolean
  action?: () => void
}

interface Props {
  items: NavDropdownItem[]
}

const props = defineProps<Props>()
const router = useRouter()

const handleClick = (item: NavDropdownItem) => {
  if (item.action) {
    item.action()
    return
  }
  if (item.to) {
    router.push(item.to)
  }
}
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <button type="button" class="nav-dropdown-trigger">
        <slot />
      </button>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        class="nav-dropdown-content"
        side="bottom"
        align="end"
        :side-offset="8"
      >
        <template v-for="(item, index) in props.items" :key="index">
          <DropdownMenuSeparator v-if="item.divider" class="nav-dropdown-separator" />
          <DropdownMenuItem
            v-else
            class="nav-dropdown-item"
            :class="{ danger: item.danger }"
            @click="handleClick(item)"
          >
            <span v-if="item.icon" class="nav-dropdown-icon" :class="item.icon" />
            <span class="nav-dropdown-label">{{ item.label }}</span>
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<style scoped>
.nav-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-weight: 500;
  background: transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-dropdown-trigger:hover {
  color: var(--primary-600);
  background: var(--primary-50);
}

.dark .nav-dropdown-trigger:hover {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.nav-dropdown-content {
  min-width: 180px;
  padding: var(--space-2);
  border-radius: var(--radius-xl);
  background: var(--glass-bg);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  z-index: 200;
}

.dark .nav-dropdown-content {
  background: var(--glass-bg);
  border-color: var(--glass-border);
}

.nav-dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}

.nav-dropdown-item:hover,
.nav-dropdown-item:focus {
  background: var(--primary-50);
  color: var(--primary-600);
}

.dark .nav-dropdown-item:hover,
.dark .nav-dropdown-item:focus {
  background: var(--bg-tertiary);
  color: var(--primary-400);
}

.nav-dropdown-item.danger {
  color: var(--error-color);
}

.nav-dropdown-item.danger:hover,
.nav-dropdown-item.danger:focus {
  background: var(--error-bg);
}

.nav-dropdown-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-dropdown-label {
  flex: 1;
}

.nav-dropdown-separator {
  height: 1px;
  margin: var(--space-2) 0;
  background: var(--border-color-light);
}

.dark .nav-dropdown-separator {
  background: var(--border-color);
}
</style>
