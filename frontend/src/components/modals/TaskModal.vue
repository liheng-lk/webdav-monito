<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-full max-w-2xl bg-[#0f172a] rounded-2xl border border-gray-800 shadow-2xl p-6 md:p-8 relative overflow-y-auto max-h-[90vh]" style="box-shadow: 0 0 50px rgba(124, 58, 237, 0.1)">
      
      <div class="flex justify-between items-center mb-6 md:mb-8">
        <div>
          <h2 class="text-2xl md:text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 tracking-tight">{{ task.id ? $t('tasks.edit') : $t('tasks.create') }}</h2>
          <p class="text-xs md:text-sm font-medium mt-1" style="color: var(--text-secondary)">{{ $t('tasks.create_desc') }}</p>
        </div>
        <button @click="$emit('close')" class="p-2 rounded-xl hover:bg-white/5 transition-colors group">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-slate-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="space-y-6">
          <div>
            <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.name') }}</label>
            <input v-model="localTask.name" type="text" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle">
          </div>
          
         <div class="mb-4 mt-4">
              <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">Source Type</label>
              <div class="flex space-x-2">
                  <button @click="localTask.src_type = 'webdav'" :class="['px-4 py-2 rounded-lg text-xs font-bold transition-all', (localTask.src_type || 'webdav') === 'webdav' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700']">
                      WebDAV / Alist
                  </button>
                  <button @click="localTask.src_type = 'local'" :class="['px-4 py-2 rounded-lg text-xs font-bold transition-all', localTask.src_type === 'local' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700']">
                      Local Folder (Watchdog)
                  </button>
              </div>
              
              <div v-if="localTask.src_type === 'local'" class="mt-4 bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div class="flex items-center justify-between">
                      <div>
                          <h4 class="text-slate-300 font-bold text-xs">Use Polling Mode</h4>
                          <p class="text-[10px] text-slate-500 mt-0.5">Slower, high CPU. Use only if native events fail (e.g. some Docker binds).</p>
                      </div>
                      <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" v-model="localTask.use_polling" class="sr-only peer">
                        <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-600"></div>
                      </label>
                  </div>
              </div>
          </div>

         <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
          <div class="space-y-2" v-if="(localTask.src_type || 'webdav') === 'webdav'">
            <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.src_acc') }}</label>
            <select v-model="localTask.src_account_id" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all appearance-none" :style="inputStyle">
              <option value="" disabled>-- {{ $t('tasks.src_acc') }} --</option>
              <option v-for="acc in srcAccounts" :key="acc.id" :value="acc.id">{{ acc.name }} ({{ acc.type }})</option>
            </select>
          </div>
          
           <div class="space-y-2">
             <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.src_path') }}</label>
             <div class="relative">
               <input v-model="localTask.src_path" type="text" class="w-full rounded-xl pl-4 pr-20 py-3 md:pl-6 md:pr-24 md:py-4 focus:ring-2 focus:ring-purple-500 font-mono transition-all text-xs md:text-sm" :style="inputStyle" :placeholder="localTask.src_type === 'local' ? '/data/downloads' : '/dav/movies'">
               <button @click="$emit('browse', 'src_path', localTask.src_account_id)" class="absolute right-2 top-2 bottom-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 px-3 rounded-lg text-[10px] font-black transition-all">{{ $t('tasks.browse') }}</button>
             </div>
           </div>
           
           <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.dst_acc') }}</label>
            <select v-model="localTask.dst_account_id" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all appearance-none" :style="inputStyle">
              <option value="" disabled>-- {{ $t('tasks.dst_acc') }} --</option>
              <option v-for="acc in dstAccounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
           </div>
           
           <div class="space-y-2">
             <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.dst_path') }}</label>
             <div class="relative">
               <input v-model="localTask.dst_path" type="text" class="w-full rounded-xl pl-4 pr-20 py-3 md:pl-6 md:pr-24 md:py-4 focus:ring-2 focus:ring-purple-500 font-mono transition-all text-xs md:text-sm" :style="inputStyle">
               <button @click="$emit('browse', 'dst_path', localTask.dst_account_id || localTask.src_account_id)" class="absolute right-2 top-2 bottom-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 px-3 rounded-lg text-[10px] font-black transition-all">{{ $t('tasks.browse') }}</button>
             </div>
           </div>
         </div>

         <div v-if="isSourceAlist" class="bg-indigo-500/10 p-4 rounded-xl flex items-center justify-between border border-indigo-500/20">
             <div>
                 <h4 class="text-indigo-400 font-bold text-xs md:text-sm">{{ $t('tasks.refresh_source') }}</h4>
                 <p class="text-[10px] mt-1" style="color: var(--text-secondary)">{{ $t('tasks.refresh_tips') }}</p>
             </div>
             <label class="relative inline-flex items-center cursor-pointer">
               <input type="checkbox" v-model="localTask.refresh_source" class="sr-only peer">
               <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
             </label>
         </div>

         <div v-if="localTask.dst_account_id" class="bg-indigo-500/10 p-4 rounded-xl flex items-center justify-between border border-indigo-500/20">
             <div>
                 <h4 class="text-indigo-400 font-bold text-xs md:text-sm">Refresh Destination (Alist)</h4>
                 <p class="text-[10px] mt-1" style="color: var(--text-secondary)">Refresh Alist directory after changes</p>
             </div>
             <label class="relative inline-flex items-center cursor-pointer">
               <input type="checkbox" v-model="localTask.refresh_destination" class="sr-only peer">
               <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
             </label>
         </div>

         <div class="bg-indigo-500/10 p-4 rounded-xl flex items-center justify-between border border-indigo-500/20">
             <div>
                 <h4 class="text-indigo-400 font-bold text-xs md:text-sm">{{ $t('tasks.smart_scan') }}</h4>
                 <p class="text-[10px] mt-1" style="color: var(--text-secondary)">{{ $t('tasks.smart_scan_desc') }}</p>
             </div>
             <label class="relative inline-flex items-center cursor-pointer">
               <input type="checkbox" v-model="localTask.smart_scan" class="sr-only peer">
               <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
             </label>
         </div>

         <!-- 调度类型 -->
         <div>
           <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.schedule_type') }}</label>
           <div class="flex space-x-2 mb-3">
             <button @click="localTask.schedule_type = 'interval'" :class="['px-4 py-2 rounded-lg text-xs font-bold transition-all', (localTask.schedule_type || 'interval') === 'interval' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700']">
               {{ $t('tasks.interval_mode') }}
             </button>
             <button @click="localTask.schedule_type = 'cron'" :class="['px-4 py-2 rounded-lg text-xs font-bold transition-all', localTask.schedule_type === 'cron' ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700']">
               Cron
             </button>
           </div>

           <div v-if="localTask.schedule_type === 'cron'" class="space-y-3">
             <input v-model="localTask.cron_expr" type="text" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-mono transition-all text-sm" :style="inputStyle" placeholder="0 3 * * *">
             <div class="flex flex-wrap gap-2">
               <button v-for="preset in cronPresets" :key="preset.expr" @click="localTask.cron_expr = preset.expr" class="px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white">
                 {{ preset.label }}
               </button>
             </div>
           </div>

           <div v-else class="grid grid-cols-2 gap-4">
             <div>
               <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.interval') }} (sec)</label>
               <input v-model.number="localTask.interval" type="number" step="60" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle">
             </div>
             <div>
               <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.concurrency') }}</label>
               <input v-model.number="localTask.concurrency" type="number" min="1" max="50" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle" placeholder="10">
             </div>
           </div>
         </div>

         <!-- 失败重试 -->
         <div class="bg-amber-500/10 p-4 rounded-xl border border-amber-500/20">
           <h4 class="text-amber-400 font-bold text-xs md:text-sm mb-3">{{ $t('tasks.retry_title') }}</h4>
           <div class="grid grid-cols-2 gap-4">
             <div>
               <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.max_retries') }}</label>
               <input v-model.number="localTask.max_retries" type="number" min="0" max="5" class="w-full rounded-xl px-4 py-3 focus:ring-2 focus:ring-amber-500 font-bold transition-all" :style="inputStyle" placeholder="0">
             </div>
             <div>
               <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.retry_delay') }} (sec)</label>
               <input v-model.number="localTask.retry_delay" type="number" min="10" step="10" class="w-full rounded-xl px-4 py-3 focus:ring-2 focus:ring-amber-500 font-bold transition-all" :style="inputStyle" placeholder="60">
             </div>
           </div>
         </div>
      </div>

      <div class="mt-8 flex justify-end space-x-4 pt-4" style="border-top: 1px solid var(--border-color)">
         <button @click="$emit('close')" class="font-bold px-4 py-3 transition-colors text-sm" style="color: var(--text-muted)">{{ $t('common.cancel') }}</button>
         <button @click="save" class="bg-purple-600 text-white hover:bg-purple-500 font-black px-8 py-3 rounded-xl transition-all shadow-xl active:scale-[0.98] text-sm">{{ $t('common.save') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  isOpen: Boolean,
  task: Object,
  srcAccounts: Array,
  dstAccounts: Array
})

const emit = defineEmits(['close', 'save', 'browse'])

const localTask = ref({ ...props.task })

watch(() => props.task, (newVal) => {
  localTask.value = { ...newVal }
}, { deep: true })

const isSourceAlist = computed(() => {
  const acc = props.srcAccounts.find(a => a.id === localTask.value.src_account_id)
  return acc?.type === 'alist'
})

const inputStyle = computed(() => ({
  background: 'var(--bg-input)',
  color: 'var(--text-heading)',
  border: '1px solid var(--border-color)'
}))

const cronPresets = [
  { label: t('tasks.cron_hourly'), expr: '0 * * * *' },
  { label: t('tasks.cron_daily_3am'), expr: '0 3 * * *' },
  { label: t('tasks.cron_every_6h'), expr: '0 */6 * * *' },
  { label: t('tasks.cron_every_12h'), expr: '0 */12 * * *' },
  { label: t('tasks.cron_weekly'), expr: '0 3 * * 1' },
]

const save = () => {
  emit('save', localTask.value)
}
</script>
