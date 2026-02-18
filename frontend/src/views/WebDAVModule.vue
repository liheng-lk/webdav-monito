<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center space-x-4">
        <div class="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center">
          <CloudIcon class="w-6 h-6 text-indigo-400" />
        </div>
        <div>
          <h3 class="text-xl font-black" style="color: var(--text-heading)">{{ $t('accounts.title_webdav') }}</h3>
          <p class="text-xs font-bold mt-0.5" style="color: var(--text-muted)">{{ accounts.length }} {{ $t('accounts.configured') }}</p>
        </div>
      </div>
      <button @click="$emit('add-account')" class="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3 rounded-2xl font-bold shadow-lg shadow-indigo-600/20 transition-all active:scale-[0.98] text-sm">
        <PlusIcon class="w-4 h-4" />
        <span>{{ $t('accounts.add_webdav') }}</span>
      </button>
    </div>

    <div v-if="accounts.length > 0" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <AccountCard 
        v-for="acc in accounts" 
        :key="acc.id" 
        :account="acc" 
        type="webdav"
        @test="$emit('test-account', $event)"
        @delete="$emit('delete-account', $event)"
      />
    </div>
    <div v-else class="glass-card border-dashed rounded-[2rem] py-16 flex flex-col items-center justify-center group hover:border-indigo-500/30 transition-all cursor-pointer" style="color: var(--text-muted)" @click="$emit('add-account')">
      <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-indigo-500/10 transition-colors" style="background: var(--bg-elevated)">
        <CloudIcon class="w-8 h-8 group-hover:text-indigo-400 transition-colors" style="color: var(--text-subtle)" />
      </div>
      <p class="font-bold text-sm">{{ $t('accounts.no_webdav') }}</p>
      <p class="text-xs mt-1" style="color: var(--text-subtle)">{{ $t('accounts.click_add') }}</p>
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
      <div class="flex justify-between items-center">
        <p class="text-xs font-black uppercase tracking-widest" style="color: var(--text-muted)">{{ tasks.length }} {{ $t('tasks.task_count') }}</p>
        <button @click="$emit('add-task')" class="flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 font-bold text-xs bg-indigo-500/10 hover:bg-indigo-500/20 px-4 py-2 rounded-xl transition-all">
          <PlusIcon class="w-3 h-3" />
          <span>{{ $t('tasks.add_task') }}</span>
        </button>
      </div>

      <TaskList 
        :tasks="tasks" 
        @trigger="$emit('trigger-task', $event)"
        @edit="$emit('edit-task', $event)"
        @delete="$emit('delete-task', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { PlusIcon, LayersIcon, CloudIcon } from 'lucide-vue-next'
import AccountCard from '../components/AccountCard.vue'
import TaskList from '../components/TaskList.vue'

defineProps({
  accounts: { type: Array, default: () => [] },
  tasks: { type: Array, default: () => [] }
})

defineEmits(['add-account', 'test-account', 'delete-account', 'add-task', 'trigger-task', 'edit-task', 'delete-task'])
</script>
