<template>
  <div class="h-screen w-full flex overflow-hidden relative">
    
    <!-- 壁纸背景层 -->
    <div v-if="currentWallpaper" class="wallpaper-bg" :style="{ backgroundImage: `url(${currentWallpaper})` }"></div>
    <div class="wallpaper-overlay"></div>
    
    <!-- 侧边栏 -->
    <Sidebar 
      :current-view="currentView" 
      :is-open="isSidebarOpen"
      @update:currentView="$emit('update:currentView', $event)"
      @close="isSidebarOpen = false"
      @logout="$emit('logout')"
    />

    <!-- 主内容区 -->
    <div class="flex-1 flex flex-col min-w-0 relative z-10">
      <!-- 移动端头部 -->
      <div v-if="!isLargeScreen" class="lg:hidden">
         <MobileHeader @open-menu="isSidebarOpen = true" />
      </div>

      <!-- 桌面端顶栏 -->
      <header class="hidden lg:flex h-24 items-center justify-between px-10 pt-6 pb-2 z-30">
        <div class="flex flex-col justify-center">
           <h2 class="text-3xl font-black tracking-tight" style="color: var(--text-heading)">{{ $t(`nav.${currentView}`) }}</h2>
           <div class="flex items-center text-xs font-bold mt-1 uppercase tracking-widest space-x-2" style="color: var(--text-muted)">
              <span>{{ $t('common.breadcrumb_analytics') }}</span>
              <span style="color: var(--text-subtle)">/</span>
              <span>{{ $t('common.breadcrumb_dashboard') }}</span>
              <span style="color: var(--text-subtle)">/</span>
              <span class="text-indigo-500">{{ $t(`nav.${currentView}`) }}</span>
           </div>
        </div>
        
        <div class="flex items-center space-x-4">
           <!-- 切换壁纸按钮 -->
           <button @click="rotateWallpaper" class="p-3 rounded-2xl glass-card hover:scale-105 transition-all" style="color: var(--text-secondary)" title="换壁纸">
             <ImageIcon class="w-5 h-5" />
           </button>

           <!-- 主题切换按钮 -->
           <button @click="toggleTheme" class="p-3 rounded-2xl glass-card hover:scale-105 transition-all" style="color: var(--text-secondary)" title="切换主题">
             <SunIcon v-if="theme === 'dark'" class="w-5 h-5" />
             <MoonIcon v-else class="w-5 h-5" />
           </button>

           <!-- 通知 -->
           <NotificationPanel />

           <!-- 语言 + 头像 -->
           <div class="flex items-center space-x-4 pl-4" style="border-left: 2px solid var(--border-color)">
             <div class="flex p-1 rounded-xl glass-card">
               <button @click="$emit('change-lang', 'zh')" :class="locale === 'zh' ? 'bg-indigo-600 text-white shadow-lg' : ''" class="px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all uppercase tracking-widest" :style="locale !== 'zh' ? 'color: var(--text-muted)' : ''">CN</button>
               <button @click="$emit('change-lang', 'en')" :class="locale === 'en' ? 'bg-indigo-600 text-white shadow-lg' : ''" class="px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all uppercase tracking-widest" :style="locale !== 'en' ? 'color: var(--text-muted)' : ''">EN</button>
             </div>
             
             <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-[2px] cursor-pointer hover:scale-105 transition-transform group/avatar relative" @click="$refs.avatarInput.click()" title="点击更换头像">
               <div class="w-full h-full rounded-2xl flex items-center justify-center overflow-hidden" style="background: var(--bg-page)">
                 <img v-if="avatar" :src="avatar" alt="Profile" class="w-full h-full object-cover">
                 <span v-else class="text-lg font-black text-indigo-400">A</span>
               </div>
               <div class="absolute inset-0 rounded-2xl bg-black/40 flex items-center justify-center opacity-0 group-hover/avatar:opacity-100 transition-opacity">
                 <CameraIcon class="w-4 h-4 text-white" />
               </div>
             </div>
             <input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="handleAvatarChange" />
           </div>
        </div>
      </header>

      <!-- 主内容 -->
      <main class="flex-1 overflow-y-auto overflow-x-hidden relative custom-scrollbar p-6 lg:px-10 lg:pb-10">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { SunIcon, MoonIcon, ImageIcon, CameraIcon } from 'lucide-vue-next'
import Sidebar from './Sidebar.vue'
import MobileHeader from './MobileHeader.vue'
import NotificationPanel from '../NotificationPanel.vue'
import { useTheme } from '../../composables/useTheme.js'

defineProps({
  currentView: String,
  locale: String,
  avatar: String
})

const emit = defineEmits(['update:currentView', 'logout', 'change-lang', 'update-avatar'])

const avatarInput = ref(null)

const handleAvatarChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (file.size > 500 * 1024) {
    alert('图片不能超过 500KB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    emit('update-avatar', reader.result)
  }
  reader.readAsDataURL(file)
}

const { theme, currentWallpaper, toggleTheme, rotateWallpaper, fetchWallpapers, startRotation, stopRotation } = useTheme()

const isSidebarOpen = ref(false)
const isLargeScreen = ref(window.innerWidth >= 1024)

const onResize = () => {
  isLargeScreen.value = window.innerWidth >= 1024
  if (isLargeScreen.value) isSidebarOpen.value = false
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  fetchWallpapers()
  startRotation(30000) // 每30秒换一张壁纸
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  stopRotation()
})
</script>
