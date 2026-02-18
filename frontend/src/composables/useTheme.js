import { ref, watch } from 'vue'
import axios from 'axios'

const theme = ref(localStorage.getItem('theme') || 'dark')
const wallpapers = ref([])
const currentWallpaper = ref('')
const wallpaperIndex = ref(0)
let rotateTimer = null

export function useTheme() {
    const applyTheme = () => {
        document.documentElement.setAttribute('data-theme', theme.value)
    }

    const toggleTheme = () => {
        theme.value = theme.value === 'dark' ? 'light' : 'dark'
        localStorage.setItem('theme', theme.value)
        applyTheme()
    }

    const setTheme = (t) => {
        theme.value = t
        localStorage.setItem('theme', t)
        applyTheme()
    }

    const fetchWallpapers = async () => {
        try {
            const res = await axios.get('/api/wallpaper')
            if (res.data.images?.length > 0) {
                wallpapers.value = res.data.images
                currentWallpaper.value = res.data.images[0]
                wallpaperIndex.value = 0
                // 预加载所有壁纸
                res.data.images.forEach(url => {
                    const img = new Image()
                    img.src = url
                })
            }
        } catch (e) {
            console.error('Failed to fetch wallpapers:', e)
        }
    }

    const rotateWallpaper = () => {
        if (wallpapers.value.length <= 1) return
        wallpaperIndex.value = (wallpaperIndex.value + 1) % wallpapers.value.length
        currentWallpaper.value = wallpapers.value[wallpaperIndex.value]
    }

    const startRotation = (intervalMs = 30000) => {
        stopRotation()
        rotateTimer = setInterval(rotateWallpaper, intervalMs)
    }

    const stopRotation = () => {
        if (rotateTimer) {
            clearInterval(rotateTimer)
            rotateTimer = null
        }
    }

    // 初始化主题
    applyTheme()

    return {
        theme,
        currentWallpaper,
        wallpapers,
        toggleTheme,
        setTheme,
        fetchWallpapers,
        rotateWallpaper,
        startRotation,
        stopRotation
    }
}
