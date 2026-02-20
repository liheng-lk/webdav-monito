<template>
  <div class="min-h-screen bg-[#111111] text-slate-200 font-sans selection:bg-indigo-500/30">
    
    <LoginView 
      v-if="!isLoggedIn" 
      :loading="loading" 
      :error="loginError" 
      @login="handleLogin" 
    />

    
    <AppLayout 
      v-else 
      :current-view="currentView" 
      :locale="locale"
      :avatar="avatar"
      @update:currentView="currentView = $event"
      @change-lang="changeLang"
      @logout="logout"
      @update-avatar="uploadAvatar"
    >
      
      <component 
        :is="CurrentViewComponent" 
        v-bind="viewProps"
        @add-account="openAccountModal"
        @test-account="testAccount"
        @delete-account="deleteAccount"
        @add-task="openTaskModal"
        @trigger-task="triggerTask"
        @edit-task="openTaskModal"
        @delete-task="deleteTask"
        @history-task="openHistoryModal"
        @refresh="fetchLogs"
        @update="updateSettings"
        @update-avatar="uploadAvatar"
      />
    </AppLayout>

    
    <AccountModal 
      :is-open="showAccountModal"
      :account="newAcc"
      :testing="testing"
      @close="showAccountModal = false"
      @save="saveAccount"
      @test="testNewAccount"
    />

    <TaskModal 
      :is-open="showTaskModal"
      :task="newTask"
      :src-accounts="srcAccountsForModal"
      :dst-accounts="dstAccountsForModal"
      @close="showTaskModal = false"
      @save="saveTask"
      @browse="openPicker"
    />

    <FilePickerModal 
      :is-open="showDirPicker"
      :path="picker.path"
      :items="picker.items"
      :loading="picker.loading"
      @close="showDirPicker = false"
      @go-up="goUp"
      @select="selectItem"
      @confirm="confirmPicker"
    />

    <TaskHistoryModal
      :is-open="showHistoryModal"
      :task-id="historyTaskId"
      :task-name="historyTaskName"
      @close="showHistoryModal = false"
    />

    
    <Teleport to="body">
      <div v-if="notification" class="fixed top-8 left-1/2 -translate-x-1/2 z-[1000] animate-in fade-in slide-in-from-top-4 duration-500">
        <div :class="notification.type === 'success' ? 'bg-emerald-600 border-emerald-500' : 'bg-red-600 border-red-500'" class="px-8 py-3.5 rounded-2xl shadow-2xl border text-white font-black text-sm flex items-center space-x-3">
          <CheckCircle2Icon v-if="notification.type === 'success'" class="w-5 h-5" />
          <AlertCircleIcon v-else class="w-5 h-5" />
          <span>{{ notification.message }}</span>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { CheckCircle2Icon, AlertCircleIcon } from 'lucide-vue-next'

import AppLayout from './components/layout/AppLayout.vue'
import LoginView from './views/LoginView.vue'
import DashboardView from './views/DashboardView.vue'
import WebDAVModule from './views/WebDAVModule.vue'
import AlistModule from './views/AlistModule.vue'
import LocalModule from './views/LocalModule.vue'
import LogsView from './views/LogsView.vue'
import SettingsView from './views/SettingsView.vue'
import AccountModal from './components/modals/AccountModal.vue'
import TaskModal from './components/modals/TaskModal.vue'
import FilePickerModal from './components/modals/FilePickerModal.vue'
import TaskHistoryModal from './components/modals/TaskHistoryModal.vue'

const { t, locale } = useI18n()

const isLoggedIn = ref(!!localStorage.getItem('token'))
const loading = ref(false)
const loginError = ref('')
const currentView = ref('dashboard')
const accounts = ref([])
const tasks = ref([])
const logs = ref([])
const avatar = ref('')
const notification = ref(null)

const showAccountModal = ref(false)
const showTaskModal = ref(false)
const showDirPicker = ref(false)
const showHistoryModal = ref(false)
const historyTaskId = ref('')
const historyTaskName = ref('')
const testing = ref(false)
const taskHistory = ref([])

const newAcc = ref({ type: 'webdav', name: '', url: '', username: '', password: '', token: '' })
const newTask = ref({ name: '', src_account_id: '', dst_account_id: '', src_path: '/', dst_path: '/', interval: 600, enabled: true, refresh_source: false, src_type: 'webdav', concurrency: 10, smart_scan: true, schedule_type: 'interval', cron_expr: '', max_retries: 0, retry_delay: 60 })
const picker = ref({ loading: false, items: [], path: '/', accountId: '', targetField: '' })

const CurrentViewComponent = computed(() => {
  switch (currentView.value) {
    case 'dashboard': return DashboardView
    case 'webdav': return WebDAVModule
    case 'alist': return AlistModule
    case 'local': return LocalModule
    case 'logs': return LogsView
    case 'settings': return SettingsView
    default: return DashboardView
  }
})

const viewProps = computed(() => {
  switch (currentView.value) {
    case 'dashboard': return { tasks: tasks.value, accounts: accounts.value, taskHistory: taskHistory.value }
    case 'webdav': return { 
        accounts: accounts.value.filter(a => a.type === 'webdav'), 
        tasks: tasks.value.filter(t => {
            const acc = accounts.value.find(a => a.id === t.src_account_id)
            return acc && acc.type === 'webdav'
        }) 
    }
    case 'alist': return { 
        accounts: accounts.value.filter(a => a.type === 'alist'), 
        tasks: tasks.value.filter(t => {
            const acc = accounts.value.find(a => a.id === t.src_account_id)
            return acc && acc.type === 'alist'
        }) 
    }
    case 'local': return {
        tasks: tasks.value.filter(t => t.src_type === 'local')
    }
    case 'logs': return { logs: logs.value }
    case 'settings': return { locale: locale.value, avatar: avatar.value }
    default: return {}
  }
})

const srcAccountsForModal = computed(() => {
  if (currentView.value === 'webdav') return accounts.value.filter(a => a.type === 'webdav')
  if (currentView.value === 'alist') return accounts.value.filter(a => a.type === 'alist')
  return accounts.value
})

const dstAccountsForModal = computed(() => {
  return accounts.value.filter(a => a.type === 'alist')
})


axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

axios.interceptors.response.use(
  resp => resp,
  err => {
    if (err.response?.status === 401) logout()
    return Promise.reject(err)
  }
)

const handleLogin = async (creds) => {
  loading.value = true
  loginError.value = ''
  try {
    const formData = new FormData()
    formData.append('username', creds.username)
    formData.append('password', creds.password)
    const res = await axios.post('/api/auth/login', formData)
    localStorage.setItem('token', res.data.access_token)
    isLoggedIn.value = true
    fetchConfig()
  } catch (err) {
    loginError.value = t('auth.error')
  } finally {
    loading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  isLoggedIn.value = false
}

const fetchConfig = async () => {
  try {
    const res = await axios.get('/api/config')
    accounts.value = res.data.accounts
    tasks.value = res.data.tasks
    if (res.data.settings?.language) locale.value = res.data.settings.language
    if (res.data.settings?.avatar) avatar.value = res.data.settings.avatar
  } catch (err) {
    notify('Fetch failed', 'error')
  }
}

const fetchLogs = async () => {
  try {
    const res = await axios.get('/api/logs')
    logs.value = res.data.reverse()
  } catch (err) {
    console.error('Failed to fetch logs')
  }
}

const openAccountModal = () => {
  newAcc.value = { type: currentView.value === 'alist' ? 'alist' : 'webdav', name: '', url: '', username: '', password: '', token: '' }
  showAccountModal.value = true
}

const saveAccount = async (acc) => {
  await axios.post('/api/accounts', acc)
  showAccountModal.value = false
  notify(t('accounts.save'))
  fetchConfig()
}

const deleteAccount = async (id) => {
  if (!confirm(t('common.confirm_delete'))) return
  await axios.delete(`/api/accounts/${id}`)
  notify('Deleted')
  fetchConfig()
}

const testAccount = async (acc) => {
  try {
    const res = await axios.post('/api/accounts/test', acc)
    if (res.data.success) notify(t('accounts.test_success'))
    else notify(`${t('accounts.test_fail')}: ${res.data.message}`, 'error')
  } catch (err) {
    notify('Test error', 'error')
  }
}

const testNewAccount = async (acc) => {
  testing.value = true
  await testAccount(acc)
  testing.value = false
}

const openTaskModal = (task = null) => {
  if (task && task.id) {
    newTask.value = { ...task }
  } else {
    const isLocal = currentView.value === 'local'
    newTask.value = { 
        name: '', 
        src_account_id: isLocal ? '' : (srcAccountsForModal.value[0]?.id || ''), 
        dst_account_id: '', 
        src_path: '/', 
        dst_path: '/', 
        interval: 600, 
        enabled: true, 
        refresh_source: false,
        src_type: isLocal ? 'local' : 'webdav',
        concurrency: 10,
        smart_scan: true,
        schedule_type: 'interval',
        cron_expr: '',
        max_retries: 0,
        retry_delay: 60
    }
  }
  showTaskModal.value = true
}

const saveTask = async (task) => {
  if (task.id) {
    await axios.put(`/api/tasks/${task.id}`, task)
  } else {
    await axios.post('/api/tasks', task)
  }
  showTaskModal.value = false
  notify('Task Saved')
  fetchConfig()
}

const deleteTask = async (id) => {
  if (!confirm(t('common.confirm_delete'))) return
  await axios.delete(`/api/tasks/${id}`)
  fetchConfig()
}

let pollTimer = null

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(() => {
    if (isLoggedIn.value && document.visibilityState === 'visible') {
      fetchConfig()
      fetchTaskHistory()
      if (currentView.value === 'logs') fetchLogs()
    }
  }, 3000)
}

const stopPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
}

watch(isLoggedIn, (val) => {
  if (val) startPolling()
  else stopPolling()
})

watch(currentView, (val) => {
  if (val === 'logs') fetchLogs()
})

onMounted(() => {
  if (isLoggedIn.value) {
    fetchConfig()
    fetchTaskHistory()
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

const triggerTask = async (id) => {
  const task = tasks.value.find(t => t.id === id)
  if (task) task.status = 'running'

  try {
    await axios.post(`/api/tasks/${id}/run`)
    notify('Triggered')
    setTimeout(fetchConfig, 1000)
  } catch (err) {
    notify('Trigger failed', 'error')
    fetchConfig()
  }
}

const openHistoryModal = (task) => {
  historyTaskId.value = task.id
  historyTaskName.value = task.name
  showHistoryModal.value = true
}

const fetchTaskHistory = async () => {
  try {
    const res = await axios.get('/api/stats/history')
    taskHistory.value = res.data
  } catch { taskHistory.value = [] }
}

const openPicker = async (field, accId) => {
  const isLocal = newTask.value.src_type === 'local' && field === 'src_path'
  if (!isLocal && !accId) return notify('Please select an account first', 'error')
  picker.value.accountId = accId
  picker.value.targetField = field
  picker.value.isLocal = isLocal
  picker.value.path = field === 'src_path' ? newTask.value.src_path : newTask.value.dst_path
  if (!picker.value.path?.startsWith('/')) picker.value.path = '/'
  
  showDirPicker.value = true
  browseTo(picker.value.path)
}

const browseTo = async (path) => {
  picker.value.loading = true
  picker.value.path = path
  try {
    let res
    if (picker.value.isLocal) {
      res = await axios.post('/api/local/list', { path })
    } else {
      res = await axios.post(`/api/accounts/${picker.value.accountId}/ls`, { path })
    }
    picker.value.items = res.data.sort((a,b) => (b.is_dir - a.is_dir) || a.name.localeCompare(b.name))
  } catch (err) {
    notify('Failed to list directory', 'error')
  } finally {
    picker.value.loading = false
  }
}

const selectItem = (item) => {
  if (item.is_dir) browseTo(item.path)
}

const goUp = () => {
  const path = picker.value.path.replace(/\/$/, '')
  const parts = path.split('/')
  parts.pop()
  const parent = parts.join('/') || '/'
  browseTo(parent)
}

const confirmPicker = () => {
  if (picker.value.targetField === 'src_path') newTask.value.src_path = picker.value.path
  else newTask.value.dst_path = picker.value.path
  showDirPicker.value = false
}

const changeLang = (l) => updateSettings({ language: l })

const updateSettings = async (data) => {
  try {
    const res = await axios.put('/api/settings', data)
    if (data.language) locale.value = data.language
    if (data.password) notify(t('settings.success') + ' (Password Updated)')
    else notify(t('settings.success'))
  } catch (err) {
    notify('Update failed', 'error')
  }
}

const uploadAvatar = async (base64Data) => {
  try {
    const res = await axios.put('/api/avatar', { avatar: base64Data })
    avatar.value = res.data.avatar
    notify(t('settings.avatar_updated'))
  } catch (err) {
    notify(t('settings.avatar_error'), 'error')
  }
}

const notify = (message, type = 'success') => {
  notification.value = { message, type }
  setTimeout(() => notification.value = null, 3000)
}

</script>
