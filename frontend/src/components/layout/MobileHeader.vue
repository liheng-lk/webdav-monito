<template>
  <header class="lg:hidden h-16 flex items-center px-4 sticky top-0 z-40 justify-between" :style="{ background: 'var(--bg-sidebar)', borderBottom: '1px solid var(--border-color)', backdropFilter: 'blur(20px)' }">
    <div class="flex items-center space-x-2">
      <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiBmaWxsPSJub25lIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjM2NmYxIiAvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIgLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cGF0aCBkPSJNNTAgOTVDNTAgOTUgOTAgNzUgOTAgMzVWMTVMNTAgNUwxMCAxNVYzNUMxMCA3NSA1MCA5NSA1MCA5NVoiIGZpbGw9InVybCgjZzEpIiAvPjxwYXRoIGQ9Ik01MCAzNVY2NU0zNSA1MEg2NSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI2IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIC8+PC9zdmc+" alt="Logo" class="w-8 h-8" />
      <span class="text-lg font-xingkai" :style="{ color: 'var(--text-heading)' }">云端哨兵</span>
    </div>

    <div class="flex items-center space-x-2">
      <button @click="toggleTheme" class="p-2 rounded-lg" :style="{ color: 'var(--text-secondary)' }" title="切换主题">
        <SunIcon v-if="theme === 'dark'" class="w-5 h-5" />
        <MoonIcon v-else class="w-5 h-5" />
      </button>
      <button @click="$emit('open-menu')" class="p-2 rounded-lg glass-card" :style="{ color: 'var(--text-secondary)' }">
        <MenuIcon class="w-5 h-5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { LayersIcon, MenuIcon, SunIcon, MoonIcon } from 'lucide-vue-next'
import { useTheme } from '../../composables/useTheme.js'

const { theme, toggleTheme } = useTheme()

defineEmits(['open-menu'])
</script>
