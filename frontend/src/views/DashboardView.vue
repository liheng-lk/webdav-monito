<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    
    <!-- 顶部统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- 任务总数 -->
      <div class="glass-card p-6 rounded-[2rem] relative overflow-hidden group">
        <div class="flex justify-between items-start mb-4">
          <div>
            <p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--text-secondary)">{{ $t('dashboard.total_tasks') }}</p>
            <h3 class="text-4xl font-black" style="color: var(--text-heading)">{{ stats.total }}</h3>
          </div>
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center group-hover:bg-[#6366f1]/20 transition-colors" style="background: var(--bg-elevated)">
            <LayersIcon class="w-6 h-6 text-[#6366f1]" />
          </div>
        </div>
        <div class="flex items-center text-xs font-bold space-x-2">
          <span class="text-blue-400 bg-blue-400/10 px-2 py-1 rounded-lg">{{ stats.enabled }} {{ $t('dashboard.enabled') }}</span>
          <span style="color: var(--text-muted)">{{ stats.disabled }} {{ $t('dashboard.disabled') }}</span>
        </div>
      </div>

      <!-- 运行中 -->
      <div class="glass-card p-6 rounded-[2rem] relative overflow-hidden group">
         <div class="flex justify-between items-start mb-4">
           <div>
             <p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--text-secondary)">{{ $t('dashboard.running_now') }}</p>
             <h3 class="text-4xl font-black" style="color: var(--text-heading)">{{ stats.running }}</h3>
           </div>
           <div class="w-12 h-12 rounded-2xl flex items-center justify-center group-hover:bg-[#f59e0b]/20 transition-colors" style="background: var(--bg-elevated)">
             <ZapIcon class="w-6 h-6 text-[#f59e0b]" />
           </div>
         </div>
         <div class="flex items-center text-xs font-bold space-x-2">
           <span v-if="stats.running > 0" class="text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-lg animate-pulse">{{ $t('dashboard.active') }}</span>
           <span v-else class="px-2 py-1 rounded-lg" style="color: var(--text-muted); background: var(--bg-elevated)">{{ $t('dashboard.idle') }}</span>
         </div>
       </div>

      <!-- 账号总数 -->
      <div class="glass-card p-6 rounded-[2rem] relative overflow-hidden group">
         <div class="flex justify-between items-start mb-4">
           <div>
             <p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--text-secondary)">{{ $t('dashboard.total_accounts') }}</p>
             <h3 class="text-4xl font-black" style="color: var(--text-heading)">{{ stats.accounts }}</h3>
           </div>
           <div class="w-12 h-12 rounded-2xl flex items-center justify-center group-hover:bg-[#ec4899]/20 transition-colors" style="background: var(--bg-elevated)">
             <UsersIcon class="w-6 h-6 text-[#ec4899]" />
           </div>
         </div>
         <div class="flex items-center text-xs font-bold space-x-2">
           <span class="text-indigo-400 bg-indigo-400/10 px-2 py-1 rounded-lg">{{ stats.webdavCount }} WebDAV</span>
           <span class="text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-lg">{{ stats.alistCount }} Alist</span>
         </div>
       </div>
    </div>

    <!-- 下半区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- 任务状态概览 -->
      <div class="lg:col-span-2 glass-card p-8 rounded-[2rem]">
        <div class="flex justify-between items-center mb-6">
           <h3 class="text-lg font-bold" style="color: var(--text-heading)">{{ $t('dashboard.tasks_by_status') }}</h3>
           <div class="flex space-x-4 text-xs font-bold">
              <div class="flex items-center space-x-2">
                 <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                 <span style="color: var(--text-secondary)">{{ $t('dashboard.idle') }} ({{ statusCounts.idle }})</span>
              </div>
              <div class="flex items-center space-x-2">
                 <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                 <span style="color: var(--text-secondary)">{{ $t('dashboard.running') }} ({{ statusCounts.running }})</span>
              </div>
              <div class="flex items-center space-x-2">
                 <div class="w-2 h-2 rounded-full bg-[#f43f5e]"></div>
                 <span style="color: var(--text-secondary)">{{ $t('dashboard.error') }} ({{ statusCounts.error }})</span>
              </div>
           </div>
        </div>
        
        <!-- 任务列表 -->
        <div v-if="tasks.length === 0" class="h-48 flex items-center justify-center">
           <div class="text-center" style="color: var(--text-muted)">
             <LayersIcon class="w-10 h-10 mx-auto mb-3 opacity-20" />
             <p class="text-sm font-medium">{{ $t('dashboard.no_tasks') }}</p>
           </div>
        </div>
        <div v-else class="space-y-3 max-h-56 overflow-y-auto custom-scrollbar pr-2">
           <div v-for="task in tasks" :key="task.id" 
                class="flex items-center justify-between p-4 rounded-2xl transition-colors group"
                :style="{ background: 'var(--bg-elevated)' }"
                @mouseenter="$event.target.style.background = 'var(--bg-card-hover)'"
                @mouseleave="$event.target.style.background = 'var(--bg-elevated)'">
              <div class="flex items-center space-x-4 min-w-0 flex-1">
                 <div class="relative flex-shrink-0">
                    <div :class="statusDotClass(task.status)" class="w-2.5 h-2.5 rounded-full"></div>
                    <div v-if="task.status === 'running'" :class="statusDotClass(task.status)" class="w-2.5 h-2.5 rounded-full absolute inset-0 animate-ping opacity-75"></div>
                 </div>
                 <div class="min-w-0">
                    <p class="text-sm font-bold truncate" style="color: var(--text-heading)">{{ task.name }}</p>
                    <p class="text-[10px] font-mono mt-0.5" style="color: var(--text-muted)">{{ Math.round(task.interval / 60) }} {{ $t('tasks.minutes') }}</p>
                 </div>
              </div>
              <div class="flex items-center space-x-3 flex-shrink-0 ml-4">
                 <span :class="statusBadgeClass(task.status)" class="px-3 py-1 rounded-lg text-[10px] font-bold tracking-wider">
                   {{ statusLabel(task.status) }}
                 </span>
                 <span v-if="task.last_run" class="text-[10px] font-mono hidden sm:inline" style="color: var(--text-subtle)">
                   {{ formatTime(task.last_run) }}
                 </span>
              </div>
           </div>
        </div>

        <!-- 状态比例条 -->
        <div v-if="tasks.length > 0" class="mt-6 pt-4" style="border-top: 1px solid var(--border-color)">
           <div class="flex h-3 rounded-full overflow-hidden" style="background: var(--bg-elevated)">
              <div v-if="statusCounts.idle > 0" class="bg-blue-500 transition-all duration-700" :style="{ width: barPct('idle') }"></div>
              <div v-if="statusCounts.running > 0" class="bg-emerald-500 transition-all duration-700" :style="{ width: barPct('running') }"></div>
              <div v-if="statusCounts.error > 0" class="bg-[#f43f5e] transition-all duration-700" :style="{ width: barPct('error') }"></div>
           </div>
           <div class="flex justify-between mt-2 text-[10px] font-bold" style="color: var(--text-muted)">
              <span>{{ $t('dashboard.idle') }} {{ barPct('idle') }}</span>
              <span>{{ $t('dashboard.running') }} {{ barPct('running') }}</span>
              <span>{{ $t('dashboard.error') }} {{ barPct('error') }}</span>
           </div>
        </div>
      </div>

      <!-- 账号类型饼图 -->
      <div class="glass-card p-8 rounded-[2rem] flex flex-col">
         <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold" style="color: var(--text-heading)">{{ $t('dashboard.account_type') }}</h3>
            <span class="text-xs font-bold uppercase" style="color: var(--text-muted)">{{ $t('dashboard.all') }}</span>
         </div>

         <div class="flex-1 flex items-center justify-center relative">
            <div class="w-40 h-40 rounded-full relative flex items-center justify-center" style="border: 16px solid var(--bg-elevated)">
               <div class="absolute inset-0 rounded-full" 
                    :style="{
                        background: stats.accounts > 0 
                          ? `conic-gradient(#6366f1 0% ${webdavPct}%, #10b981 ${webdavPct}% 100%)` 
                          : 'var(--bg-elevated)', 
                        mask: 'radial-gradient(transparent 58%, black 59%)',
                        WebkitMask: 'radial-gradient(transparent 58%, black 59%)'
                    }">
               </div>
               <div class="text-center z-10">
                  <span class="block text-3xl font-black" style="color: var(--text-heading)">{{ stats.accounts }}</span>
                  <span class="text-[10px] font-bold uppercase tracking-widest" style="color: var(--text-secondary)">{{ $t('dashboard.total') }}</span>
               </div>
            </div>
         </div>

         <div class="mt-4 space-y-3">
            <div class="flex justify-between text-xs font-bold">
               <div class="flex items-center" style="color: var(--text-secondary)">
                  <div class="w-2 h-2 rounded-full bg-indigo-500 mr-2"></div> WebDAV
               </div>
               <span style="color: var(--text-heading)">{{ stats.webdavCount }}</span>
            </div>
            <div class="flex justify-between text-xs font-bold">
               <div class="flex items-center" style="color: var(--text-secondary)">
                  <div class="w-2 h-2 rounded-full bg-emerald-500 mr-2"></div> Alist
               </div>
               <span style="color: var(--text-heading)">{{ stats.alistCount }}</span>
            </div>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LayersIcon, ZapIcon, UsersIcon } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  tasks: Array,
  accounts: Array
})

const stats = computed(() => {
    const webdavCount = props.accounts.filter(a => a.type === 'webdav').length
    const alistCount = props.accounts.filter(a => a.type === 'alist').length
    
    return {
        total: props.tasks.length,
        enabled: props.tasks.filter(t => t.enabled).length,
        disabled: props.tasks.filter(t => !t.enabled).length,
        running: props.tasks.filter(t => t.status === 'running').length,
        accounts: props.accounts.length,
        webdavCount,
        alistCount
    }
})

const statusCounts = computed(() => {
    let idle = 0, running = 0, error = 0
    props.tasks.forEach(task => {
        if (task.status === 'running') running++
        else if (task.status?.startsWith('error')) error++
        else idle++
    })
    return { idle, running, error }
})

const webdavPct = computed(() => {
    if (stats.value.accounts === 0) return 0
    return (stats.value.webdavCount / stats.value.accounts) * 100
})

const barPct = (type) => {
    const total = props.tasks.length
    if (total === 0) return '0%'
    return Math.round((statusCounts.value[type] / total) * 100) + '%'
}

const statusDotClass = (status) => {
    if (status === 'running') return 'bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]'
    if (status?.startsWith('error')) return 'bg-[#f43f5e]'
    return 'bg-blue-500'
}

const statusBadgeClass = (status) => {
    if (status === 'running') return 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
    if (status?.startsWith('error')) return 'bg-red-500/15 text-red-400 border border-red-500/20'
    return 'bg-blue-500/15 text-blue-400 border border-blue-500/20'
}

const statusLabel = (status) => {
    if (status === 'running') return t('dashboard.running')
    if (status === 'idle') return t('dashboard.idle')
    if (status?.startsWith('error')) return t('dashboard.error')
    return status
}

const formatTime = (isoStr) => {
    try {
        const d = new Date(isoStr)
        const pad = n => String(n).padStart(2, '0')
        return `${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    } catch {
        return isoStr
    }
}
</script>
