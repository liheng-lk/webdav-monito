<template>
  <div class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div class="glass-card rounded-[2rem] p-6 md:p-8">
      <h3 class="text-xl md:text-2xl font-black mb-8" style="color: var(--text-heading)">{{ $t('settings.title') }}</h3>

      <div class="space-y-8">
        <!-- 头像设置 -->
        <div class="flex items-center justify-between p-4 rounded-2xl" style="background: var(--bg-elevated)">
          <div class="flex items-center space-x-4">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-[2px] cursor-pointer hover:scale-105 transition-transform group/avatar relative"
                 @click="$refs.settingsAvatarInput.click()">
              <div class="w-full h-full rounded-2xl flex items-center justify-center overflow-hidden" style="background: var(--bg-page)">
                <img v-if="avatar" :src="avatar" alt="Profile" class="w-full h-full object-cover">
                <span v-else class="text-2xl font-black text-indigo-400">A</span>
              </div>
              <div class="absolute inset-0 rounded-2xl bg-black/40 flex items-center justify-center opacity-0 group-hover/avatar:opacity-100 transition-opacity">
                <CameraIcon class="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <label class="text-sm font-bold" style="color: var(--text-heading)">{{ $t('settings.avatar') }}</label>
              <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ $t('settings.avatar_desc') }}</p>
            </div>
          </div>
          <button @click="$refs.settingsAvatarInput.click()" class="px-4 py-2 rounded-xl font-bold text-sm bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 transition-all">
            {{ $t('settings.change_avatar') }}
          </button>
          <input ref="settingsAvatarInput" type="file" accept="image/*" class="hidden" @change="handleAvatarUpload" />
        </div>

        <!-- 主题设置 -->
        <div class="flex items-center justify-between p-4 rounded-2xl" style="background: var(--bg-elevated)">
          <div>
            <label class="text-sm font-bold" style="color: var(--text-heading)">{{ $t('settings.theme') }}</label>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ $t('settings.theme_desc') }}</p>
          </div>
          <button @click="toggleTheme" class="flex items-center space-x-2 px-4 py-2 rounded-xl font-bold text-sm transition-all"
                  :class="theme === 'dark' ? 'bg-slate-700 text-white' : 'bg-amber-100 text-amber-700'">
            <SunIcon v-if="theme === 'dark'" class="w-4 h-4" />
            <MoonIcon v-else class="w-4 h-4" />
            <span>{{ theme === 'dark' ? $t('settings.dark') : $t('settings.light') }}</span>
          </button>
        </div>

        <!-- 语言 -->
        <div class="flex items-center justify-between p-4 rounded-2xl" style="background: var(--bg-elevated)">
          <label class="text-sm font-bold" style="color: var(--text-heading)">{{ $t('settings.language') }}</label>
          <select v-model="lang" @change="$emit('change-lang', lang)" class="rounded-xl px-4 py-2 font-bold text-sm border transition-all" style="background: var(--bg-input); color: var(--text-heading); border-color: var(--border-color)">
            <option value="zh">中文</option>
            <option value="en">English</option>
          </select>
        </div>
        
        <!-- 改密码 -->
        <div class="space-y-4 p-4 rounded-2xl" style="background: var(--bg-elevated)">
          <label class="text-sm font-bold" style="color: var(--text-heading)">{{ $t('settings.password') }}</label>
          <input v-model="newPassword" type="password" :placeholder="$t('settings.new_password')" class="w-full rounded-xl px-4 py-3 font-bold text-sm border transition-all" style="background: var(--bg-input); color: var(--text-heading); border-color: var(--border-color)">
        </div>
        
        <button @click="saveSettings" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-3 rounded-xl shadow-lg shadow-indigo-600/20 transition-all active:scale-[0.98] text-sm">
          {{ $t('settings.update') }}
        </button>
      </div>
    </div>
    
    <p class="text-[10px] uppercase tracking-widest font-bold text-center" style="color: var(--text-subtle)">WebDAV Monitor v3.0</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { SunIcon, MoonIcon, CameraIcon } from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme.js'

const { theme, toggleTheme } = useTheme()

const props = defineProps({
  settings: Object,
  avatar: String
})

const emit = defineEmits(['save', 'change-lang', 'update-avatar'])

const lang = ref(props.settings?.language || 'zh')
const newPassword = ref('')

const handleAvatarUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (file.size > 500 * 1024) {
    alert('图片不能超过 500KB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    emit('update-avatar', reader.result)
  }
  reader.readAsDataURL(file)
}

const saveSettings = () => {
  const payload = { language: lang.value }
  if (newPassword.value) payload.password = newPassword.value
  emit('save', payload)
}
</script>
