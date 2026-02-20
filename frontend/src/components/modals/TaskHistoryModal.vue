<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-full max-w-3xl bg-[#0f172a] rounded-2xl border border-gray-800 shadow-2xl p-6 md:p-8 relative overflow-hidden" style="box-shadow: 0 0 50px rgba(124, 58, 237, 0.1)">
      
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-xl md:text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">{{ $t('history.title') }}</h2>
          <p class="text-xs font-medium mt-1" style="color: var(--text-secondary)">{{ taskName }}</p>
        </div>
        <button @click="$emit('close')" class="p-2 rounded-xl hover:bg-white/5 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="records.length === 0" class="text-center py-16" style="color: var(--text-muted)">
        <HistoryIcon class="w-12 h-12 mx-auto mb-4 opacity-20" />
        <p class="text-sm font-medium">{{ $t('history.empty') }}</p>
      </div>

      <div v-else class="max-h-[60vh] overflow-y-auto custom-scrollbar space-y-2 pr-1">
        <div v-for="(r, i) in records" :key="i" 
             class="rounded-xl p-4 transition-colors"
             :style="{ background: 'var(--bg-elevated)' }">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
              <div :class="r.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'" class="w-2 h-2 rounded-full"></div>
              <span class="text-xs font-bold" :class="r.status === 'success' ? 'text-emerald-400' : 'text-red-400'">
                {{ r.status === 'success' ? $t('history.success') : $t('history.failed') }}
              </span>
            </div>
            <span class="text-[10px] font-mono" style="color: var(--text-muted)">{{ formatDuration(r.duration_seconds) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono" style="color: var(--text-secondary)">{{ formatTime(r.start_time) }}</span>
            <div class="flex space-x-3 text-[10px] font-bold">
              <span v-if="r.items_scanned" class="text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{{ r.items_scanned }} {{ $t('history.scanned') }}</span>
              <span v-if="r.new_files" class="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">+{{ r.new_files }}</span>
              <span v-if="r.modified_files" class="text-yellow-400 bg-yellow-500/10 px-2 py-0.5 rounded">~{{ r.modified_files }}</span>
              <span v-if="r.deleted_files" class="text-red-400 bg-red-500/10 px-2 py-0.5 rounded">-{{ r.deleted_files }}</span>
              <span v-if="r.dirs_refreshed" class="text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">{{ r.dirs_refreshed }} {{ $t('history.refreshed') }}</span>
            </div>
          </div>

          <div v-if="r.error_message" class="mt-2 text-[10px] text-red-300 bg-red-500/10 px-3 py-2 rounded-lg font-mono break-all">
            {{ r.error_message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { HistoryIcon } from 'lucide-vue-next'
import axios from 'axios'

const props = defineProps({
  isOpen: Boolean,
  taskId: String,
  taskName: String
})

defineEmits(['close'])

const records = ref([])
const loading = ref(false)

watch(() => props.isOpen, async (val) => {
  if (val && props.taskId) {
    loading.value = true
    try {
      const res = await axios.get(`/api/tasks/${props.taskId}/history`)
      records.value = res.data.reverse()
    } catch { records.value = [] }
    finally { loading.value = false }
  }
})

const formatTime = (isoStr) => {
  try {
    const d = new Date(isoStr)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  } catch { return isoStr }
}

const formatDuration = (sec) => {
  if (sec < 60) return `${sec.toFixed(1)}s`
  if (sec < 3600) return `${Math.floor(sec/60)}m ${Math.round(sec%60)}s`
  return `${Math.floor(sec/3600)}h ${Math.floor((sec%3600)/60)}m`
}
</script>
