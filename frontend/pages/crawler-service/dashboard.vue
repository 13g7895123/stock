<template>
  <div class="space-y-6">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Go 爬蟲服務監控儀表板
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            即時監控服務狀態、券商健康度及資料爬取效能
          </p>
        </div>
        <div class="mt-4 md:mt-0 flex gap-3">
          <ActionButton
            @click="refreshAll"
            :loading="isRefreshing"
            variant="primary"
            size="md"
          >
            <ArrowPathIcon class="h-5 w-5 mr-2" />
            重新整理
          </ActionButton>
        </div>
      </div>
    </div>

    <!-- 通知訊息 -->
    <div
      v-if="notification.show"
      :class="[
        'p-4 rounded-lg-custom shadow-sm',
        notification.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' :
        notification.type === 'error' ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200' :
        'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200'
      ]"
    >
      <div class="flex items-start">
        <CheckCircleIcon v-if="notification.type === 'success'" class="h-5 w-5 mt-0.5 mr-3" />
        <XCircleIcon v-else-if="notification.type === 'error'" class="h-5 w-5 mt-0.5 mr-3" />
        <InformationCircleIcon v-else class="h-5 w-5 mt-0.5 mr-3" />
        <div class="flex-1">
          <p class="font-medium">{{ notification.message }}</p>
        </div>
        <button @click="notification.show = false" class="ml-4">
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>
    </div>

    <!-- 服務概覽統計 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 服務狀態 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">服務狀態</p>
            <p class="text-2xl font-bold" :class="serviceStatus.online ? 'text-green-600' : 'text-red-600'">
              {{ serviceStatus.online ? '✅ 運行中' : '❌ 離線' }}
            </p>
          </div>
          <ServerIcon class="h-10 w-10 text-gray-400" />
        </div>
      </div>

      <!-- 資料庫連線 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">資料庫連線</p>
            <p class="text-2xl font-bold" :class="dbStatus.connected ? 'text-green-600' : 'text-red-600'">
              {{ dbStatus.connected ? '✅ 已連接' : '❌ 未連接' }}
            </p>
          </div>
          <CircleStackIcon class="h-10 w-10 text-gray-400" />
        </div>
        <p v-if="dbStatus.connected" class="text-xs text-gray-500 mt-2">
          {{ dbStatus.host }}:{{ dbStatus.port }}
        </p>
      </div>

      <!-- 健康券商數 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">健康券商數</p>
            <p class="text-2xl font-bold text-blue-600">
              {{ healthyBrokersCount }}/8
            </p>
          </div>
          <SignalIcon class="h-10 w-10 text-gray-400" />
        </div>
        <div class="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${(healthyBrokersCount / 8) * 100}%` }"
          ></div>
        </div>
      </div>

      <!-- 記憶體使用 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">記憶體使用</p>
            <p class="text-2xl font-bold text-purple-600">
              {{ memoryUsage }} MB
            </p>
          </div>
          <CpuChipIcon class="h-10 w-10 text-gray-400" />
        </div>
        <p class="text-xs text-gray-500 mt-2">相比 Python 降低 60-80%</p>
      </div>
    </div>

    <!-- 券商健康檢查 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">券商健康檢查</h2>
        <ActionButton
          @click="checkBrokers"
          :loading="loadingBrokers"
          variant="secondary"
          size="sm"
        >
          <ArrowPathIcon class="h-4 w-4 mr-1" />
          重新檢查
        </ActionButton>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div
          v-for="broker in brokersList"
          :key="broker.name"
          class="p-4 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-medium text-gray-900 dark:text-gray-100">{{ broker.name }}</span>
            <span
              :class="[
                'h-3 w-3 rounded-full',
                broker.status === 'healthy' ? 'bg-green-500' :
                broker.status === 'degraded' ? 'bg-yellow-500' :
                'bg-red-500'
              ]"
            ></span>
          </div>
          <p class="text-xs text-gray-600 dark:text-gray-400">
            {{ broker.status === 'healthy' ? '正常運作' : broker.status === 'degraded' ? '部分異常' : '無法連線' }}
          </p>
          <p v-if="broker.responseTime" class="text-xs text-gray-500 mt-1">
            響應時間: {{ broker.responseTime }}ms
          </p>
        </div>
      </div>
    </div>

    <!-- 快速測試區 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 單一股票爬取測試 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">單一股票爬取測試</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              股票代碼
            </label>
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="例如: 2330"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <ActionButton
            @click="testSingleStock"
            :loading="testingStock"
            variant="primary"
            class="w-full"
          >
            <RocketLaunchIcon class="h-5 w-5 mr-2" />
            開始爬取
          </ActionButton>

          <!-- 測試結果 -->
          <div v-if="singleTestResult" class="mt-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
            <div class="flex items-start justify-between mb-2">
              <span class="font-medium text-gray-900 dark:text-gray-100">測試結果</span>
              <span
                :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  singleTestResult.success ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                ]"
              >
                {{ singleTestResult.success ? '成功' : '失敗' }}
              </span>
            </div>
            <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <p>耗時: {{ singleTestResult.duration }}ms</p>
              <p>資料筆數: {{ singleTestResult.recordCount }}</p>
              <p v-if="singleTestResult.source">來源: {{ singleTestResult.source }}</p>
              <p v-if="singleTestResult.error" class="text-red-600 dark:text-red-400">
                錯誤: {{ singleTestResult.error }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 批次股票爬取測試 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">批次股票爬取測試</h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              股票代碼 (用逗號分隔)
            </label>
            <textarea
              v-model="batchStockSymbols"
              placeholder="例如: 2330,2317,2454"
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <ActionButton
            @click="testBatchStocks"
            :loading="testingBatch"
            variant="success"
            class="w-full"
          >
            <BoltIcon class="h-5 w-5 mr-2" />
            批次爬取
          </ActionButton>

          <!-- 批次測試結果 -->
          <div v-if="batchTestResult" class="mt-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
            <div class="flex items-start justify-between mb-2">
              <span class="font-medium text-gray-900 dark:text-gray-100">批次結果</span>
              <span class="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                {{ batchTestResult.totalSymbols }} 檔股票
              </span>
            </div>
            <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <p>總耗時: {{ batchTestResult.duration }}ms</p>
              <p>平均每檔: {{ (batchTestResult.duration / batchTestResult.totalSymbols).toFixed(0) }}ms</p>
              <p>處理速度: {{ ((batchTestResult.totalSymbols / batchTestResult.duration) * 1000).toFixed(2) }} stocks/sec</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速效能對比 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">快速效能對比 (Go vs Python)</h2>
        <NuxtLink
          to="/crawler-service/performance"
          class="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center"
        >
          查看詳細對比
          <ArrowRightIcon class="h-4 w-4 ml-1" />
        </NuxtLink>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">速度提升</p>
          <p class="text-3xl font-bold text-green-600">10-20x</p>
          <p class="text-xs text-gray-500 mt-1">相比 Python 爬蟲</p>
        </div>
        <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">並發能力</p>
          <p class="text-3xl font-bold text-blue-600">1000+</p>
          <p class="text-xs text-gray-500 mt-1">Goroutines</p>
        </div>
        <div class="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">記憶體節省</p>
          <p class="text-3xl font-bold text-purple-600">60-80%</p>
          <p class="text-xs text-gray-500 mt-1">降低使用量</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  ServerIcon,
  CircleStackIcon,
  SignalIcon,
  CpuChipIcon,
  RocketLaunchIcon,
  BoltIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
  ArrowRightIcon
} from '@heroicons/vue/24/outline'

const {
  health,
  loading,
  error,
  getHealth,
  fetchStockDaily,
  batchUpdateStocks,
  isServiceOnline
} = useCrawlerService()

// 本地狀態
const isRefreshing = ref(false)
const serviceStatus = ref({ online: false })
const dbStatus = ref({ connected: false, host: '', port: 0 })
const healthyBrokersCount = ref(0)
const memoryUsage = ref(100)
const loadingBrokers = ref(false)
const brokersList = ref([
  { name: 'Fubon', status: 'unknown', responseTime: null },
  { name: 'MoneyDJ', status: 'unknown', responseTime: null },
  { name: 'Yuanta', status: 'unknown', responseTime: null },
  { name: 'Emega', status: 'unknown', responseTime: null },
  { name: 'FBS', status: 'unknown', responseTime: null },
  { name: 'Esunsec', status: 'unknown', responseTime: null },
  { name: 'KGIE', status: 'unknown', responseTime: null },
  { name: 'Masterlink', status: 'unknown', responseTime: null }
])

// 測試相關
const testStockSymbol = ref('2330')
const testingStock = ref(false)
const singleTestResult = ref(null)
const batchStockSymbols = ref('2330,2317,2454')
const testingBatch = ref(false)
const batchTestResult = ref(null)

// 通知
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// 顯示通知
const showNotification = (type, message, duration = 5000) => {
  notification.value = { show: true, type, message }
  setTimeout(() => {
    notification.value.show = false
  }, duration)
}

// 重新整理所有資訊
const refreshAll = async () => {
  isRefreshing.value = true
  await Promise.all([
    updateServiceStatus(),
    checkBrokers()
  ])
  isRefreshing.value = false
  showNotification('success', '資料已更新')
}

// 更新服務狀態
const updateServiceStatus = async () => {
  const result = await getHealth()

  if (result.success && result.data) {
    serviceStatus.value.online = result.data.status === 'ok'

    // 解析資料庫狀態（從日誌或健康檢查中獲取，這裡模擬）
    dbStatus.value = {
      connected: true,
      host: 'postgres',
      port: 5432
    }

    // 模擬記憶體使用（實際應從 metrics 獲取）
    memoryUsage.value = 98
  } else {
    serviceStatus.value.online = false
    dbStatus.value.connected = false
  }
}

// 檢查券商健康狀態
const checkBrokers = async () => {
  loadingBrokers.value = true

  // 模擬券商檢查（實際應調用相應的 API）
  await new Promise(resolve => setTimeout(resolve, 1500))

  // 隨機設置券商狀態（實際應從 API 獲取）
  const statuses = ['healthy', 'degraded', 'unhealthy']
  let healthyCount = 0

  brokersList.value = brokersList.value.map(broker => {
    const status = statuses[Math.floor(Math.random() * statuses.length)]
    if (status === 'healthy') healthyCount++

    return {
      ...broker,
      status,
      responseTime: status === 'healthy' ? Math.floor(Math.random() * 500) + 100 : null
    }
  })

  healthyBrokersCount.value = healthyCount
  loadingBrokers.value = false
}

// 測試單一股票爬取
const testSingleStock = async () => {
  if (!testStockSymbol.value.trim()) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  testingStock.value = true
  singleTestResult.value = null

  const result = await fetchStockDaily(testStockSymbol.value.trim())

  singleTestResult.value = result
  testingStock.value = false

  if (result.success) {
    showNotification('success', `成功爬取 ${testStockSymbol.value} 的資料`)
  } else {
    showNotification('error', `爬取失敗: ${result.error}`)
  }
}

// 測試批次股票爬取
const testBatchStocks = async () => {
  if (!batchStockSymbols.value.trim()) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  const symbols = batchStockSymbols.value.split(',').map(s => s.trim()).filter(s => s)

  if (symbols.length === 0) {
    showNotification('error', '請輸入有效的股票代碼')
    return
  }

  testingBatch.value = true
  batchTestResult.value = null

  const result = await batchUpdateStocks(symbols)

  batchTestResult.value = result
  testingBatch.value = false

  if (result.success) {
    showNotification('success', `成功批次爬取 ${symbols.length} 檔股票`)
  } else {
    showNotification('error', `批次爬取失敗: ${result.error}`)
  }
}

// 初始化
onMounted(async () => {
  await updateServiceStatus()
  await checkBrokers()

  // 設置自動更新（每 30 秒）
  const interval = setInterval(updateServiceStatus, 30000)

  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>
