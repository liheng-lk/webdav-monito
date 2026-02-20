<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center space-x-4">
        <div class="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
          <FolderSyncIcon class="w-6 h-6 text-emerald-400" />
        </div>
        <div>
          <h3 class="text-xl font-black" style="color: var(--text-heading)">{{ $t('nav.local') }}</h3>
          <p class="text-xs font-bold mt-0.5" style="color: var(--text-muted)">{{ tasks.length }} {{ $t('tasks.task_count') }}</p>
        </div>
      </div>
      <button @click="$emit('add-task')" class="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 rounded-2xl font-bold shadow-lg shadow-emerald-600/20 transition-all active:scale-[0.98] text-sm">
        <PlusIcon class="w-4 h-4" />
        <span>{{ $t('tasks.add_task') }}</span>
      </button>
    </div>

    <!-- Info Banner -->
    <div class="bg-emerald-500/10 p-5 rounded-2xl border border-emerald-500/20">
      <div class="flex items-start space-x-3">
        <InfoIcon class="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
        <div>
          <div class="space-y-1">
            <h4 class="text-emerald-400 font-bold text-sm">Watchdog 实时监控</h4>
            <p class="text-xs" style="color: var(--text-secondary)">
              通过 Watchdog 实时监听本地挂载目录的文件变化，自动触发扫描。
            </p>
            <p class="text-[10px]" style="color: var(--text-muted)">
              注：Alist 刷新和扫描模式 (Native/Polling) 可在任务设置中配置。请确保目标目录已通过 Docker Volume 挂载。
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex items-center space-x-4 pt-4">
      <div class="flex-1 h-px" style="background: var(--border-color)"></div>
      <div class="flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest" style="color: var(--text-muted)">
        <LayersIcon class="w-3 h-3" />
        <span>{{ $t('tasks.sync_tasks') }}</span>
      </div>
      <div class="flex-1 h-px" style="background: var(--border-color)"></div>
    </div>

    <div class="space-y-4">
      <TaskList 
        :tasks="tasks" 
        @trigger="$emit('trigger-task', $event)"
        @edit="$emit('edit-task', $event)"
        @delete="$emit('delete-task', $event)"
        @history="$emit('history-task', $event)"
      />
      
      <div v-if="tasks.length === 0" class="glass-card border-dashed rounded-[2rem] py-16 flex flex-col items-center justify-center group hover:border-emerald-500/30 transition-all cursor-pointer" style="color: var(--text-muted)" @click="$emit('add-task')">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/10 transition-colors" style="background: var(--bg-elevated)">
          <FolderSyncIcon class="w-8 h-8 group-hover:text-emerald-400 transition-colors" style="color: var(--text-subtle)" />
        </div>
        <p class="font-bold text-sm">暂无本地监控任务</p>
        <p class="text-xs mt-1" style="color: var(--text-subtle)">点击创建第一个 Watchdog 任务</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { PlusIcon, LayersIcon, FolderSyncIcon, InfoIcon } from 'lucide-vue-next'
import TaskList from '../components/TaskList.vue'

defineProps({
  tasks: { type: Array, default: () => [] }
})

defineEmits(['add-task', 'trigger-task', 'edit-task', 'delete-task', 'history-task'])
</script>
