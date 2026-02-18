<template>
  <div class="relative">
    <!-- 铃铛按钮 -->
    <button @click="toggle" class="p-3 rounded-2xl glass-card hover:scale-105 transition-all relative" style="color: var(--text-secondary)">
      <BellIcon class="w-5 h-5" />
      <span v-if="unreadCount > 0" class="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></span>
    </button>

    <!-- 通知面板 -->
    <Transition name="notif">
      <div v-if="isOpen" class="absolute right-0 top-16 w-96 max-h-[480px] glass-card rounded-2xl shadow-2xl z-50 overflow-hidden flex flex-col"
           style="border: 1px solid var(--border-color)">
        <!-- 头部 -->
        <div class="flex items-center justify-between px-5 py-4" style="border-bottom: 1px solid var(--border-color)">
          <div class="flex items-center space-x-2">
            <h4 class="text-sm font-bold" style="color: var(--text-heading)">{{ $t('notifications.title') }}</h4>
            <span v-if="unreadCount > 0" class="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">{{ unreadCount }}</span>
          </div>
          <div class="flex items-center space-x-2">
            <button v-if="unreadCount > 0" @click="markAllRead" class="text-[10px] font-bold px-2 py-1 rounded-lg hover:bg-indigo-600/20 transition-colors text-indigo-400">
              {{ $t('notifications.mark_read') }}
            </button>
            <button v-if="notifications.length > 0" @click="clearAll" class="text-[10px] font-bold px-2 py-1 rounded-lg hover:bg-red-600/20 transition-colors text-red-400">
              {{ $t('notifications.clear') }}
            </button>
          </div>
        </div>

        <!-- 通知列表 -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center py-12" style="color: var(--text-muted)">
            <BellOffIcon class="w-8 h-8 mb-3 opacity-30" />
            <p class="text-xs font-bold">{{ $t('notifications.empty') }}</p>
          </div>

          <div v-for="n in notifications" :key="n.id"
               class="px-5 py-3.5 transition-colors hover:bg-white/5 cursor-default"
               :class="{ 'opacity-50': n.read }"
               :style="{ borderBottom: '1px solid var(--border-color)' }">
            <div class="flex items-start space-x-3">
              <div class="mt-0.5 w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0"
                   :class="{
                     'bg-emerald-500/15': n.type === 'success',
                     'bg-red-500/15': n.type === 'error',
                     'bg-blue-500/15': n.type === 'info'
                   }">
                <CheckCircleIcon v-if="n.type === 'success'" class="w-4 h-4 text-emerald-400" />
                <AlertCircleIcon v-else-if="n.type === 'error'" class="w-4 h-4 text-red-400" />
                <InfoIcon v-else class="w-4 h-4 text-blue-400" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-bold truncate" style="color: var(--text-heading)">{{ n.title }}</p>
                <p class="text-[11px] mt-0.5 line-clamp-2" style="color: var(--text-secondary)">{{ n.message }}</p>
                <p class="text-[10px] mt-1 font-bold" style="color: var(--text-muted)">{{ n.time }}</p>
              </div>
              <div v-if="!n.read" class="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0"></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 点击外部关闭 -->
    <div v-if="isOpen" class="fixed inset-0 z-40" @click="isOpen = false"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { BellIcon, BellOffIcon, CheckCircleIcon, AlertCircleIcon, InfoIcon } from 'lucide-vue-next'
import axios from 'axios'

const isOpen = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
let pollTimer = null

const fetchNotifications = async () => {
  try {
    const res = await axios.get('/api/notifications')
    notifications.value = res.data.notifications
    unreadCount.value = res.data.unread
  } catch {}
}

const toggle = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) fetchNotifications()
}

const markAllRead = async () => {
  try {
    await axios.put('/api/notifications/read')
    unreadCount.value = 0
    notifications.value.forEach(n => n.read = true)
  } catch {}
}

const clearAll = async () => {
  try {
    await axios.delete('/api/notifications')
    notifications.value = []
    unreadCount.value = 0
  } catch {}
}

onMounted(() => {
  fetchNotifications()
  pollTimer = setInterval(fetchNotifications, 15000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.notif-enter-active,
.notif-leave-active {
  transition: all 0.2s ease;
}
.notif-enter-from,
.notif-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
