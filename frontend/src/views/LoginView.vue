<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center">
    <!-- 壁纸背景 (登录页单独加载) -->
    <div v-if="wallpaper" class="wallpaper-bg" :style="{ backgroundImage: `url(${wallpaper})` }"></div>
    <div class="wallpaper-overlay"></div>

    <div class="w-full max-w-md p-8 glass-card rounded-[2.5rem] shadow-2xl relative overflow-hidden group z-10">
      <div class="absolute -top-24 -left-24 w-48 h-48 bg-indigo-600/20 rounded-full blur-3xl group-hover:bg-indigo-600/30 transition-all duration-700"></div>
      <div class="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-600/20 rounded-full blur-3xl group-hover:bg-purple-600/30 transition-all duration-700"></div>
      
      <div class="relative z-10 text-center">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiBmaWxsPSJub25lIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjM2NmYxIiAvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIgLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cGF0aCBkPSJNNTAgOTVDNTAgOTUgOTAgNzUgOTAgMzVWMTVMNTAgNUwxMCAxNVYzNUMxMCA3NSA1MCA5NSA1MCA5NVoiIGZpbGw9InVybCgjZzEpIiAvPjxwYXRoIGQ9Ik01MCAzNVY2NU0zNSA1MEg2NSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI2IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIC8+PC9zdmc+" alt="Logo" class="w-20 h-20 mx-auto mb-6 hover:scale-105 transition-transform" />
        <h1 class="text-3xl font-xingkai bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400 mb-2">{{ $t('auth.title') }}</h1>
        <p class="mb-8 font-medium" style="color: var(--text-secondary)">{{ $t('auth.subtitle') }}</p>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="text-left">
            <label class="block text-xs font-bold uppercase tracking-widest mb-1.5 ml-1" style="color: var(--text-muted)">{{ $t('auth.username') }}</label>
            <input v-model="form.username" type="text" class="w-full rounded-2xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-medium" style="background: var(--bg-input); color: var(--text-heading); border: 1px solid var(--border-color)" required>
          </div>
          <div class="text-left">
            <label class="block text-xs font-bold uppercase tracking-widest mb-1.5 ml-1" style="color: var(--text-muted)">{{ $t('auth.password') }}</label>
            <input v-model="form.password" type="password" class="w-full rounded-2xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-medium" style="background: var(--bg-input); color: var(--text-heading); border: 1px solid var(--border-color)" required>
          </div>
          <button type="submit" :disabled="loading" class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold py-4 rounded-2xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center active:scale-[0.98]">
            <span v-if="loading" class="animate-spin border-2 border-white/30 border-t-white rounded-full w-5 h-5 mr-4"></span>
            {{ loading ? $t('auth.logging_in') : $t('auth.login') }}
          </button>
          <p v-if="error" class="text-red-400 text-sm mt-4 font-bold bg-red-400/10 py-2 rounded-lg animate-pulse">{{ error }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ShieldCheckIcon } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme.js'

const { fetchWallpapers, currentWallpaper: wallpaper } = useTheme()

const props = defineProps({
  loading: Boolean,
  error: String
})

const emit = defineEmits(['login'])

const form = ref({ username: '', password: '' })

const handleSubmit = () => {
  emit('login', form.value)
}

onMounted(() => {
  fetchWallpapers()
})
</script>
