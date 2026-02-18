<template>
  <div class="glass-card glass-card-hover rounded-[2rem] p-6 flex flex-col justify-between transition-all group overflow-hidden relative h-full">
    
    <div class="absolute top-0 right-0 w-24 h-24 p-6 pointer-events-none">
      <div :class="type === 'webdav' ? 'bg-blue-500/10' : 'bg-emerald-500/10'" class="w-full h-full rounded-full blur-2xl"></div>
    </div>
    
    <div class="space-y-4 relative z-10">
      <div class="flex items-center justify-between mb-2">
        <span :class="type === 'webdav' ? 'bg-blue-500/20 text-blue-400 border-blue-500/20' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/20'" class="px-4 py-1.5 rounded-xl font-black text-[10px] tracking-widest border uppercase">
          {{ type }}
        </span>
        <div class="flex space-x-1">
          <button @click="$emit('test', account)" class="hover:bg-white/10 p-2 rounded-lg transition-all" :title="$t('accounts.test_conn')">
            <PlayIcon class="w-4 h-4 text-indigo-400" />
          </button>
          <button @click="$emit('delete', account.id)" class="hover:bg-red-500/10 p-2 rounded-lg transition-all group-hover:opacity-100 opacity-0" :title="$t('accounts.delete')">
            <TrashIcon class="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>
      
      <div>
        <h3 class="text-xl font-bold group-hover:text-indigo-400 transition-colors truncate" style="color: var(--text-heading)">{{ account.name }}</h3>
        <p class="text-xs break-all font-mono opacity-60 mt-1 line-clamp-2" style="color: var(--text-secondary)">{{ account.url }}</p>
      </div>
    </div>
    
    <div class="mt-6 pt-6 flex items-center space-x-2" style="border-top: 1px solid var(--border-color)">
      <UserIcon class="w-3 h-3" style="color: var(--text-muted)" />
      <span class="text-xs font-semibold truncate" style="color: var(--text-secondary)">{{ account.username || '-' }}</span>
    </div>
  </div>
</template>

<script setup>
import { PlayIcon, TrashIcon, UserIcon } from 'lucide-vue-next'

defineProps({
  account: Object,
  type: String
})

defineEmits(['test', 'delete'])
</script>
