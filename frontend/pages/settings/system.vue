<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        系統設定與狀態
      </h2>

      <!-- 系統健康狀態 -->
      <div class="mb-8">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <HeartIcon class="w-5 h-5 mr-2 text-red-500" />
          系統健康狀態
        </h3>
        
        <div v-if="loading" class="flex items-center space-x-2 text-gray-500">
          <ArrowPathIcon class="w-5 h-5 animate-spin" />
          <span>檢查中...</span>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="(status, component) in healthStatus.components" 
            :key="component"
            class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 flex items-center justify-between"
          >
            <span class="capitalize text-gray-700 dark:text-gray-300 font-medium">{{ component }}</span>
            <span 
              :class="[
                'px-2 py-1 text-xs rounded-full',
                status === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              ]"
            >
              {{ status }}
            </span>
          </div>
        </div>
        
        <div v-if="!loading && healthStatus.timestamp" class="mt-2 text-xs text-gray-500 text-right">
          最後檢查時間: {{ new Date(healthStatus.timestamp).toLocaleString() }}
        </div>
      </div>

      <!-- 系統資訊 -->
      <div class="mb-8">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <InformationCircleIcon class="w-5 h-5 mr-2 text-blue-500" />
          系統資訊
        </h3>
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">API 版本</span>
            <span class="font-mono text-gray-900 dark:text-white">v1.0.0</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">環境</span>
            <span class="font-mono text-gray-900 dark:text-white">Development</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600 dark:text-gray-400">資料庫連線</span>
            <span class="font-mono text-gray-900 dark:text-white">{{ healthStatus.components?.database === 'healthy' ? '已連線' : '未連線' }}</span>
          </div>
        </div>
      </div>

      <!-- 預設參數設定 (前端儲存) -->
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Cog6ToothIcon class="w-5 h-5 mr-2 text-gray-500" />
          任務預設參數
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              爬蟲並行數量 (Workers)
            </label>
            <input 
              type="number" 
              v-model="settings.maxWorkers"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              批次處理大小 (Batch Size)
            </label>
            <input 
              type="number" 
              v-model="settings.batchSize"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600"
            >
          </div>
        </div>
        <div class="mt-4 flex justify-end">
          <button 
            @click="saveSettings"
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            儲存設定
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { HeartIcon, InformationCircleIcon, Cog6ToothIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

definePageMeta({
  title: '系統設定'
})

const { get } = useApi()
const loading = ref(true)
const healthStatus = ref({
  status: 'unknown',
  components: {},
  timestamp: null
})

// 預設設定 (實際應用可存於 localStorage 或 Pinia)
const settings = ref({
  maxWorkers: 4,
  batchSize: 50
})

const checkHealth = async () => {
  loading.value = true
  try {
    const res = await get('/health/detailed')
    if (res.success) {
      healthStatus.value = res.data
    } else {
      console.error('Health check failed:', res.error)
    }
  } catch (e) {
    console.error('Health check failed:', e)
  } finally {
    loading.value = false
  }
}

const saveSettings = () => {
  // 這裡可以實作儲存到 localStorage
  localStorage.setItem('taskSettings', JSON.stringify(settings.value))
  alert('設定已儲存')
}

onMounted(() => {
  checkHealth()
  // 載入設定
  const saved = localStorage.getItem('taskSettings')
  if (saved) {
    settings.value = JSON.parse(saved)
  }
})
</script>
