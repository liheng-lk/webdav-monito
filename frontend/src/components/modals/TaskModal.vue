<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-6 backdrop-blur-xl animate-in fade-in duration-300" :style="{ background: 'var(--modal-overlay)' }">
    <div class="w-full max-w-xl rounded-[2rem] p-8 md:p-12 relative overflow-hidden flex flex-col max-h-full glass-card" style="box-shadow: 0 0 100px rgba(0,0,0,0.3)">
      <h3 class="text-2xl md:text-3xl font-black mb-6 md:mb-8" style="color: var(--text-heading)">{{ task.id ? $t('common.edit') : $t('tasks.add') }}</h3>
      
      <div class="space-y-4 md:space-y-6 overflow-y-auto custom-scrollbar flex-1 pr-2">
         <div>
           <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.name') }}</label>
           <input v-model="localTask.name" type="text" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle">
         </div>
         
         <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.src_acc') }}</label>
            <select v-model="localTask.src_account_id" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all appearance-none" :style="inputStyle">
              <option value="" disabled>-- {{ $t('tasks.src_acc') }} --</option>
              <option v-for="acc in srcAccounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
          </div>
          
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.dst_acc') }}</label>
            <select v-model="localTask.dst_account_id" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all appearance-none" :style="inputStyle">
              <option value="">-- None --</option>
              <option v-for="acc in dstAccounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
          </div>
        </div>

         <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
           <div class="space-y-2">
             <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.src_path') }}</label>
             <div class="relative">
               <input v-model="localTask.src_path" type="text" class="w-full rounded-xl pl-4 pr-20 py-3 md:pl-6 md:pr-24 md:py-4 focus:ring-2 focus:ring-purple-500 font-mono transition-all text-xs md:text-sm" :style="inputStyle">
               <button @click="$emit('browse', 'src_path', localTask.src_account_id)" class="absolute right-2 top-2 bottom-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 px-3 rounded-lg text-[10px] font-black transition-all">{{ $t('tasks.browse') }}</button>
             </div>
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

         <div>
           <label class="block text-[10px] font-black uppercase tracking-widest mb-2 ml-1" style="color: var(--text-muted)">{{ $t('tasks.interval') }}</label>
           <input v-model.number="localTask.interval" type="number" step="60" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-purple-500 font-bold transition-all" :style="inputStyle">
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
