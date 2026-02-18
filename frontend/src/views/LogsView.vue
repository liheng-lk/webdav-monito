<template>
  <div class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div class="glass-card rounded-[2rem] p-6 md:p-8">
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-xl md:text-2xl font-black" style="color: var(--text-heading)">
          {{ $t('logs.title') }}
        </h3>
        <button @click="$emit('refresh')" class="text-indigo-400 hover:text-indigo-300 font-bold text-[10px] uppercase tracking-widest bg-indigo-500/10 px-3 py-1.5 rounded-lg transition-colors">
            {{ $t('logs.refresh') }}
        </button>
      </div>
      
      <div v-if="logs.length === 0" class="text-center py-16" style="color: var(--text-muted)">
        <ActivityIcon class="w-12 h-12 mx-auto mb-4 opacity-20" />
        <p class="text-sm font-medium">{{ $t('logs.no_logs') }}</p>
      </div>
      
      <div v-else class="rounded-2xl p-4 md:p-6 font-mono text-xs leading-relaxed max-h-[500px] overflow-y-auto custom-scrollbar space-y-1.5" style="background: var(--bg-input); color: var(--text-secondary)">
        <div v-for="(log, i) in logs" :key="i" class="flex items-start space-x-2 border-b border-gray-800/50 pb-1 last:border-0 last:pb-0">
          <span class="text-gray-500 whitespace-nowrap text-[10px]">{{ log.time }}</span>
          <span :class="getLevelClass(log.level)" class="font-bold text-[10px] w-12 text-center rounded bg-opacity-10 px-1">{{ log.level }}</span>
          <span class="break-all" :class="log.level === 'ERROR' ? 'text-red-300' : 'text-gray-300'">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ActivityIcon } from 'lucide-vue-next'

defineProps({
  logs: { type: Array, default: () => [] }
})

defineEmits(['refresh'])

const getLevelClass = (level) => {
  switch (level) {
    case 'INFO': return 'text-blue-400 bg-blue-500/10'
    case 'WARNING': return 'text-yellow-400 bg-yellow-500/10'
    case 'ERROR': return 'text-red-400 bg-red-500/10'
    default: return 'text-gray-400'
  }
}
</script>
