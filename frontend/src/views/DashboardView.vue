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

      <!-- 成功率 -->
      <div class="glass-card p-6 rounded-[2rem] relative overflow-hidden group">
         <div class="flex justify-between items-start mb-4">
           <div>
             <p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--text-secondary)">{{ $t('dashboard.success_rate') }}</p>
             <h3 class="text-4xl font-black" style="color: var(--text-heading)">{{ successRate }}%</h3>
           </div>
           <div class="w-12 h-12 rounded-2xl flex items-center justify-center group-hover:bg-[#10b981]/20 transition-colors" style="background: var(--bg-elevated)">
             <ActivityIcon class="w-6 h-6 text-[#10b981]" />
           </div>
         </div>
         <div class="w-full bg-gray-700/30 rounded-full h-1.5 mt-2 overflow-hidden">
           <div class="bg-emerald-500 h-full rounded-full transition-all duration-1000" :style="{ width: successRate + '%' }"></div>
         </div>
       </div>
    </div>

    <!-- 运行趋势图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- 运行趋势 -->
      <div class="glass-card p-8 rounded-[2rem]">
        <h3 class="text-lg font-bold mb-6" style="color: var(--text-heading)">{{ $t('dashboard.run_trend') }} (7 Days)</h3>
        <div class="h-48 flex items-end justify-between space-x-2">
          <div v-for="(day, i) in runTrend" :key="i" class="flex flex-col items-center flex-1 group">
            <div class="w-full bg-indigo-500/10 rounded-t-lg relative overflow-hidden transition-all hover:bg-indigo-500/20" 
                 :style="{ height: (day.count / maxRunCount * 100) + '%' }">
              <div class="absolute bottom-0 left-0 right-0 bg-indigo-500 transition-all" :style="{ height: (day.success / day.count * 100) + '%' }"></div>
            </div>
            <span class="text-[10px] font-mono mt-2" style="color: var(--text-muted)">{{ day.date }}</span>
          </div>
        </div>
      </div>

      <!-- 变更统计 -->
      <div class="glass-card p-8 rounded-[2rem]">
        <h3 class="text-lg font-bold mb-6" style="color: var(--text-heading)">{{ $t('dashboard.change_stats') }} (7 Days)</h3>
        <div class="h-48 flex items-end justify-between space-x-2">
          <div v-for="(day, i) in changeTrend" :key="i" class="flex flex-col items-center flex-1 group">
             <div class="w-2 rounded-full bg-slate-700/30 h-full relative overflow-hidden">
                <!-- Stacked bar -->
                <div class="absolute bottom-0 w-full bg-emerald-500 transition-all" :style="{ height: (day.new / maxChangeCount * 100) + '%', bottom: '0%' }"></div>
                <div class="absolute w-full bg-yellow-500 transition-all" :style="{ height: (day.mod / maxChangeCount * 100) + '%', bottom: (day.new / maxChangeCount * 100) + '%' }"></div>
                <div class="absolute w-full bg-red-500 transition-all" :style="{ height: (day.del / maxChangeCount * 100) + '%', bottom: ((day.new + day.mod) / maxChangeCount * 100) + '%' }"></div>
             </div>
             <span class="text-[10px] font-mono mt-2" style="color: var(--text-muted)">{{ day.date }}</span>
          </div>
        </div>
        <div class="flex justify-center space-x-4 mt-2 text-[10px] font-bold">
          <div class="flex items-center"><div class="w-2 h-2 rounded-full bg-emerald-500 mr-1"></div>New</div>
          <div class="flex items-center"><div class="w-2 h-2 rounded-full bg-yellow-500 mr-1"></div>Mod</div>
          <div class="flex items-center"><div class="w-2 h-2 rounded-full bg-red-500 mr-1"></div>Del</div>
        </div>
      </div>

    </div>

    <!-- 下半区域 -->
    <div class="glass-card p-8 rounded-[2rem]">
      <div class="flex justify-between items-center mb-6">
         <h3 class="text-lg font-bold" style="color: var(--text-heading)">{{ $t('dashboard.tasks_by_status') }}</h3>
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
              :style="{ background: 'var(--bg-elevated)' }">
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
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LayersIcon, ZapIcon, ActivityIcon } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  tasks: Array,
  accounts: Array,
  taskHistory: Array
})

const stats = computed(() => {
    return {
        total: props.tasks.length,
        enabled: props.tasks.filter(t => t.enabled).length,
        disabled: props.tasks.filter(t => !t.enabled).length,
        running: props.tasks.filter(t => t.status === 'running').length,
    }
})

const successRate = computed(() => {
  if (!props.taskHistory || props.taskHistory.length === 0) return 0
  const success = props.taskHistory.filter(r => r.status === 'success').length
  return Math.round((success / props.taskHistory.length) * 100)
})

const runTrend = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = `${d.getMonth()+1}-${d.getDate()}`
    
    // Filter history for this day
    const dayRecords = props.taskHistory.filter(r => {
      const rd = new Date(r.start_time)
      return rd.getDate() === d.getDate() && rd.getMonth() === d.getMonth()
    })
    
    days.push({
      date: dateStr,
      count: dayRecords.length,
      success: dayRecords.filter(r => r.status === 'success').length
    })
  }
  return days
})

const maxRunCount = computed(() => Math.max(...runTrend.value.map(d => d.count), 5))

const changeTrend = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = `${d.getMonth()+1}-${d.getDate()}`
    
    const dayRecords = props.taskHistory.filter(r => {
      const rd = new Date(r.start_time)
      return rd.getDate() === d.getDate() && rd.getMonth() === d.getMonth()
    })
    
    days.push({
      date: dateStr,
      new: dayRecords.reduce((sum, r) => sum + (r.new_files || 0), 0),
      mod: dayRecords.reduce((sum, r) => sum + (r.modified_files || 0), 0),
      del: dayRecords.reduce((sum, r) => sum + (r.deleted_files || 0), 0)
    })
  }
  return days
})

const maxChangeCount = computed(() => {
  const max = Math.max(...changeTrend.value.map(d => d.new + d.mod + d.del), 5)
  return max
})

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
