<template>
  <aside 
    :class="[
      isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      'fixed lg:static inset-y-0 left-0 w-72 flex flex-col z-[60] transition-transform duration-300 ease-in-out'
    ]"
    :style="{ background: 'var(--bg-sidebar)', borderRight: '1px solid var(--border-sidebar)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)' }"
  >
    <!-- Logo -->
    <div class="h-24 flex items-center px-8" :style="{ borderBottom: '1px solid var(--border-sidebar)' }">
      <div class="flex items-center space-x-3">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiBmaWxsPSJub25lIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjM2NmYxIiAvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIgLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cGF0aCBkPSJNNTAgOTVDNTAgOTUgOTAgNzUgOTAgMzVWMTVMNTAgNUwxMCAxNVYzNUMxMCA3NSA1MCA5NSA1MCA5NVoiIGZpbGw9InVybCgjZzEpIiAvPjxwYXRoIGQ9Ik01MCAzNVY2NU0zNSA1MEg2NSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI2IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIC8+PC9zdmc+" alt="Logo" class="w-10 h-10" />
        <span class="text-2xl font-xingkai tracking-wide" :style="{ color: 'var(--text-heading)' }">云端哨兵</span>
      </div>
      
      <button @click="$emit('close')" class="lg:hidden ml-auto p-2 hover:text-white" :style="{ color: 'var(--text-secondary)' }">
        <XIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 px-6 py-8 space-y-2 overflow-y-auto custom-scrollbar">
      <div v-for="section in navSections" :key="section.title" class="mb-8">
        <h3 v-if="section.title" class="px-4 mb-3 text-[10px] font-black uppercase tracking-widest" :style="{ color: 'var(--text-muted)' }">{{ section.title }}</h3>
        <div class="space-y-2">
          <button 
            v-for="item in section.items" 
            :key="item.id" 
            @click="navigate(item.id)" 
            :class="[
              currentView === item.id 
                ? 'glass-card shadow-lg' 
                : 'glass-card-hover',
              'w-full flex items-center space-x-4 px-4 py-3.5 rounded-2xl transition-all text-sm font-bold group'
            ]"
            :style="{ color: currentView === item.id ? 'var(--text-heading)' : 'var(--text-muted)' }"
          >
            <component 
              :is="item.icon" 
              class="w-5 h-5 transition-colors"
              :class="currentView === item.id ? 'text-indigo-500' : ''"
              :style="{ color: currentView !== item.id ? 'var(--text-muted)' : '' }"
            />
            <span>{{ $t(`nav.${item.id}`) }}</span>
            
            <div v-if="currentView === item.id" class="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]"></div>
          </button>
        </div>
      </div>
    </nav>

    <!-- 退出 -->
    <div class="p-6" :style="{ borderTop: '1px solid var(--border-sidebar)' }">
      <button @click="$emit('logout')" class="w-full flex items-center space-x-4 px-4 py-4 hover:text-red-400 rounded-2xl transition-all text-sm font-bold group" :style="{ color: 'var(--text-muted)' }">
        <LogOutIcon class="w-5 h-5 group-hover:rotate-12 transition-transform" />
        <span>{{ $t('nav.logout') }}</span>
      </button>
    </div>
  </aside>
  
  <!-- 移动端遮罩 -->
  <div 
    v-if="isOpen" 
    @click="$emit('close')" 
    class="fixed inset-0 z-50 lg:hidden animate-in fade-in duration-200"
    :style="{ background: 'var(--modal-overlay)', backdropFilter: 'blur(4px)' }"
  ></div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  LayersIcon, LayoutDashboardIcon, CloudIcon, ServerIcon, 
  ActivityIcon, Settings2Icon, LogOutIcon, XIcon 
} from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  currentView: String,
  isOpen: Boolean
})

const emit = defineEmits(['update:currentView', 'close', 'logout'])

const navSections = computed(() => [
  {
    title: '',
    items: [
      { id: 'dashboard', icon: LayoutDashboardIcon }
    ]
  },
  {
    title: t('nav.modules'),
    items: [
      { id: 'webdav', icon: CloudIcon },
      { id: 'alist', icon: ServerIcon }
    ]
  },
  {
    title: t('nav.system'),
    items: [
      { id: 'logs', icon: ActivityIcon },
      { id: 'settings', icon: Settings2Icon }
    ]
  }
])

const navigate = (view) => {
  emit('update:currentView', view)
  emit('close')
}
</script>
