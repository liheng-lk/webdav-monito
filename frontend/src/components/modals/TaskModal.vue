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

         <div class="bg-indigo-500/10 p-4 rounded-xl flex items-center justify-between border border-indigo-500/20 mb-4">
             <div>
                 <h4 class="text-indigo-400 font-bold text-xs md:text-sm">智能扫描 (Smart Scan)</h4>
                 <p class="text-[10px] mt-1" style="color: var(--text-secondary)">跳过未变更目录 (Skip unchanged)</p>
             </div>
             <label class="relative inline-flex items-center cursor-pointer">
               <input type="checkbox" v-model="localTask.smart_scan" class="sr-only peer">
               <div class="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
             </label>
         </div>

         <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.interval') }} (sec)</label>
                <input v-model.number="localTask.interval" type="number" step="60" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle">
            </div>
            <div>
                <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">并发数 (Concurrency)</label>
                <input v-model.number="localTask.concurrency" type="number" min="1" max="50" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle" placeholder="10">
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

const save = () => {
  emit('save', localTask.value)
}
</script>
