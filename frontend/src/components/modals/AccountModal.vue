<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-6 backdrop-blur-xl animate-in fade-in duration-300" :style="{ background: 'var(--modal-overlay)' }">
    <div class="w-full max-w-xl rounded-[2rem] p-8 md:p-12 relative overflow-hidden glass-card" style="box-shadow: 0 0 100px rgba(0,0,0,0.3)">
      <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500"></div>
      <h3 class="text-2xl md:text-3xl font-black mb-8" style="color: var(--text-heading)">
        {{ $t('accounts.add') }} 
        <span :class="localAcc.type === 'webdav' ? 'text-indigo-400' : 'text-emerald-400'">{{ localAcc.type.toUpperCase() }}</span>
      </h3>
      
      <div class="space-y-4 md:space-y-6">
        <div class="space-y-3 md:space-y-4">
           <input v-model="localAcc.name" type="text" :placeholder="$t('accounts.name')" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-indigo-500 font-bold transition-all" :style="inputStyle">
           <input v-model="localAcc.url" type="text" placeholder="URL (http://...)" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-indigo-500 font-mono transition-all text-sm" :style="inputStyle">
           <div class="grid grid-cols-2 gap-4">
              <input v-model="localAcc.username" type="text" :placeholder="$t('accounts.username')" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-indigo-500 font-bold transition-all" :style="inputStyle">
              <input v-model="localAcc.password" type="password" :placeholder="$t('accounts.password')" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-indigo-500 font-bold transition-all" :style="inputStyle">
           </div>
           <input v-if="localAcc.type === 'alist'" v-model="localAcc.token" type="text" :placeholder="$t('accounts.token')" class="w-full rounded-xl px-4 py-3 md:px-6 md:py-4 focus:ring-2 focus:ring-indigo-500 transition-all text-sm" :style="inputStyle">
        </div>
      </div>

      <div class="mt-8 md:mt-12 flex justify-between items-center">
         <button @click="$emit('test', localAcc)" :disabled="testing" class="text-indigo-400 hover:text-indigo-300 font-black text-[10px] md:text-xs uppercase tracking-[0.2em] transition-all disabled:opacity-30">
           {{ testing ? '...' : $t('accounts.test') }}
         </button>
         <div class="flex space-x-3 md:space-x-4">
           <button @click="$emit('close')" class="font-bold px-4 py-3 transition-colors text-sm" style="color: var(--text-muted)">{{ $t('common.cancel') }}</button>
           <button @click="$emit('save', localAcc)" class="bg-indigo-600 hover:bg-indigo-500 text-white font-black px-6 py-3 md:px-10 md:py-4 rounded-xl transition-all shadow-xl active:scale-[0.98] text-sm">{{ $t('common.save') }}</button>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  account: Object,
  testing: Boolean
})

defineEmits(['close', 'save', 'test'])

const localAcc = ref({ ...props.account })

watch(() => props.account, (newVal) => {
  localAcc.value = { ...newVal }
}, { deep: true })

const inputStyle = computed(() => ({
  background: 'var(--bg-input)',
  color: 'var(--text-heading)',
  border: '1px solid var(--border-color)'
}))
</script>
