<template>
  <div v-if="isOpen" class="fixed inset-0 z-[200] flex items-center justify-center p-4 md:p-6 backdrop-blur-2xl animate-in zoom-in duration-300" :style="{ background: 'var(--modal-overlay)' }">
    <div class="w-full max-w-lg rounded-[2rem] overflow-hidden flex flex-col h-[500px] md:h-[600px] glass-card" style="box-shadow: 0 0 80px rgba(0,0,0,0.2)">
      
      <div class="p-6 md:p-8 flex justify-between items-center" :style="{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-heading)' }">
        <div class="min-w-0 pr-4">
          <h3 class="font-bold text-lg md:text-xl truncate">{{ $t('tasks.browse') }}</h3>
          <p class="text-xs font-mono mt-1 w-full truncate" style="color: var(--text-muted)">{{ path }}</p>
        </div>
        <button @click="$emit('close')" class="p-2 shrink-0 hover:opacity-70 transition-opacity" style="color: var(--text-muted)">
          <PlusIcon class="w-6 h-6 rotate-45" />
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto p-4 space-y-1 custom-scrollbar">
        <div v-if="loading" class="flex flex-col items-center justify-center h-full space-y-4">
          <div class="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <p class="text-xs tracking-widest uppercase font-bold" style="color: var(--text-muted)">Loading...</p>
        </div>
        
        <template v-else>
          <button v-if="path !== '/'" @click="$emit('go-up')" class="w-full flex items-center space-x-3 p-3 md:p-4 hover:bg-white/5 rounded-xl transition-all group" style="color: var(--text-heading)">
            <div class="w-8 h-8 md:w-10 md:h-10 rounded-lg flex items-center justify-center group-hover:bg-indigo-500/20 transition-all" style="background: var(--bg-elevated)">
              <LayoutDashboardIcon class="w-4 h-4 md:w-5 md:h-5 group-hover:text-indigo-400" style="color: var(--text-secondary)" />
            </div>
            <span class="font-bold text-sm">..</span>
          </button>
          
          <div v-for="item in items" :key="item.path" @click="$emit('select', item)" :class="path === item.path ? 'bg-indigo-600/20 border-indigo-500/30 text-indigo-300' : 'hover:bg-white/5 border-transparent'" class="w-full flex items-center justify-between p-3 md:p-4 rounded-xl cursor-pointer border transition-all group" :style="path !== item.path ? { color: 'var(--text-heading)' } : {}">
            <div class="flex items-center space-x-3 min-w-0">
              <div :class="item.is_dir ? 'bg-indigo-600/10' : ''" class="w-8 h-8 md:w-10 md:h-10 rounded-lg flex items-center justify-center shrink-0" :style="!item.is_dir ? { background: 'var(--bg-elevated)' } : {}">
                <CloudIcon v-if="item.is_dir" class="w-4 h-4 md:w-5 md:h-5 text-indigo-400" />
                <LayersIcon v-else class="w-4 h-4 md:w-5 md:h-5" style="color: var(--text-muted)" />
              </div>
              <span class="font-medium truncate text-sm md:text-base">{{ item.name }}</span>
            </div>
            <div v-if="item.is_dir" class="w-1.5 h-1.5 rounded-full bg-indigo-500/40 shrink-0"></div>
          </div>
        </template>
      </div>
      
      <div class="p-6 md:p-8 flex justify-end space-x-4" :style="{ borderTop: '1px solid var(--border-color)', background: 'var(--bg-elevated)' }">
        <button @click="$emit('close')" class="font-bold px-4 py-2 md:px-6 md:py-3 text-sm transition-colors hover:opacity-70" style="color: var(--text-muted)">{{ $t('common.cancel') }}</button>
        <button @click="$emit('confirm')" class="bg-indigo-600 hover:bg-indigo-500 text-white font-black px-6 py-2 md:px-10 md:py-3 rounded-xl transition-all shadow-lg active:scale-95 text-sm">{{ $t('common.save') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { PlusIcon, LayoutDashboardIcon, CloudIcon, LayersIcon } from 'lucide-vue-next'

defineProps({
  isOpen: Boolean,
  path: String,
  items: Array,
  loading: Boolean
})

defineEmits(['close', 'confirm', 'go-up', 'select'])
</script>
