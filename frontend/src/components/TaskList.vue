<template>
  <div v-if="tasks.length === 0" class="glass-card border-dashed rounded-3xl py-12 text-center" style="color: var(--text-subtle)">
    <ZapIcon class="w-8 h-8 mx-auto mb-4 opacity-20" />
    <p class="text-sm font-medium">{{ $t('dashboard.no_tasks') }}</p>
  </div>
  
  <div v-else>
    <!-- 桌面端表格 -->
    <div class="hidden md:block glass-card rounded-3xl overflow-hidden">
       <div class="overflow-x-auto">
         <table class="w-full text-left">
           <thead>
             <tr class="font-bold text-[10px] uppercase tracking-widest" style="color: var(--text-muted); border-bottom: 1px solid var(--border-color)">
               <th class="p-6">{{ $t('tasks.name') }}</th>
               <th class="p-6">{{ $t('tasks.status') }}</th>
               <th class="p-6">{{ $t('tasks.interval') }}</th>
               <th class="p-6">{{ $t('tasks.last_run') }}</th>
               <th class="p-6 text-right">{{ $t('accounts.actions') }}</th>
             </tr>
           </thead>
           <tbody>
             <tr v-for="task in tasks" :key="task.id" class="group transition-colors" style="border-bottom: 1px solid var(--border-color)">
               <td class="p-6">
                 <div class="flex items-center space-x-4">
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center font-black text-indigo-400 text-xs" style="background: var(--bg-elevated)">{{ task.name.charAt(0).toUpperCase() }}</div>
                    <span class="font-bold text-sm" style="color: var(--text-heading)">{{ task.name }}</span>
                 </div>
               </td>
               <td class="p-6">
                 <div class="flex items-center space-x-2">
                   <div :class="getStatusClass(task.status)" class="w-1.5 h-1.5 rounded-full"></div>
                   <span class="text-[10px] font-bold tracking-widest truncate max-w-[100px]" style="color: var(--text-secondary)" :title="task.status">
                     {{ formatStatus(task.status) }}
                   </span>
                 </div>
               </td>
               <td class="p-6 text-xs font-medium" style="color: var(--text-secondary)">{{ Math.round(task.interval/60) }} {{ $t('tasks.minutes') }}</td>
               <td class="p-6 text-[10px] font-mono" style="color: var(--text-muted)">{{ formatTime(task.last_run) }}</td>
               <td class="p-6 text-right space-x-3">
                 <button @click="$emit('trigger', task.id)" class="text-indigo-400 font-bold text-[10px] uppercase hover:text-indigo-300 transition-colors" :title="$t('tasks.run_now')">
                    <PlayIcon class="w-4 h-4" />
                 </button>
                 <button @click="$emit('edit', task)" class="text-emerald-400 font-bold text-[10px] uppercase hover:text-emerald-300 transition-colors" :title="$t('common.edit')">
                    <Settings2Icon class="w-4 h-4" />
                 </button>
                 <button @click="$emit('delete', task.id)" class="bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white p-2 rounded-lg transition-all" :title="$t('common.delete')">
                    <TrashIcon class="w-4 h-4" />
                 </button>
               </td>
             </tr>
           </tbody>
         </table>
       </div>
    </div>

    <!-- 移动端卡片 -->
    <div class="md:hidden space-y-4">
      <div v-for="task in tasks" :key="task.id" class="glass-card glass-card-hover rounded-2xl p-5 transition-all">
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center space-x-3">
             <div class="w-10 h-10 rounded-xl flex items-center justify-center font-black text-indigo-400" style="background: var(--bg-elevated)">{{ task.name.charAt(0).toUpperCase() }}</div>
             <div>
               <h4 class="font-bold text-sm" style="color: var(--text-heading)">{{ task.name }}</h4>
               <div class="flex items-center mt-1 space-x-2">
                 <div :class="getStatusClass(task.status)" class="w-1.5 h-1.5 rounded-full"></div>
                 <span class="text-[10px] font-bold tracking-widest truncate max-w-[120px]" style="color: var(--text-muted)" :title="task.status">
                   {{ formatStatus(task.status) }}
                 </span>
               </div>
             </div>
          </div>
          <button @click="$emit('trigger', task.id)" class="bg-indigo-600/20 text-indigo-400 p-2 rounded-lg">
            <PlayIcon class="w-4 h-4" />
          </button>
        </div>
        
        <div class="grid grid-cols-2 gap-4 text-[10px] pt-4 mt-2" style="color: var(--text-muted); border-top: 1px solid var(--border-color)">
          <div>
            <span class="block uppercase tracking-wider mb-1">{{ $t('tasks.interval') }}</span>
            <span class="font-mono" style="color: var(--text-body)">{{ Math.round(task.interval/60) }} {{ $t('tasks.minutes') }}</span>
          </div>
          <div class="text-right">
            <span class="block uppercase tracking-wider mb-1">{{ $t('tasks.last_run') }}</span>
            <span class="font-mono" style="color: var(--text-body)">{{ task.last_run || $t('common.never') }}</span>
          </div>
        </div>

        <div class="flex justify-end space-x-4 mt-4 pt-4" style="border-top: 1px solid var(--border-color)">
           <button @click="$emit('edit', task)" class="text-emerald-400 font-bold text-xs flex items-center">
             <Settings2Icon class="w-3 h-3 mr-1" /> {{ $t('common.edit') }}
           </button>
           <button @click="$emit('delete', task.id)" class="bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white px-3 py-1.5 rounded-lg text-xs font-bold flex items-center transition-all">
             <TrashIcon class="w-3 h-3 mr-1" /> {{ $t('common.delete') }}
           </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ZapIcon, PlayIcon, Settings2Icon, TrashIcon } from 'lucide-vue-next'

import { useI18n } from 'vue-i18n'

const props = defineProps({
  tasks: Array
})

const emit = defineEmits(['trigger', 'edit', 'delete'])

const { t } = useI18n()

const formatStatus = (status) => {
  if (status === 'idle') return t('dashboard.idle')
  if (status === 'running') return t('dashboard.running')
  if (status && status.startsWith('error')) return t('dashboard.error')
  return status
}

const getStatusClass = (status) => {
  if (status === 'idle') return 'bg-blue-500'
  if (status === 'running') return 'bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.5)] animate-pulse'
  if (status && status.startsWith('error')) return 'bg-red-500'
  return 'bg-gray-500'
}

const formatTime = (isoStr) => {
  if (!isoStr) return t('common.never')
  try {
    const d = new Date(isoStr)
    const pad = n => String(n).padStart(2, '0')
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return isoStr
  }
}
</script>
