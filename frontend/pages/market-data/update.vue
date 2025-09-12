<template>
  <div class="space-y-6">
    <!-- 通知區域 -->
    <div v-if="notification.show" :class="[
      'p-4 rounded-lg border-l-4 flex items-center justify-between',
      notification.type === 'success' ? 'bg-green-50 border-green-400 text-green-700 dark:bg-green-900 dark:text-green-200' :
      notification.type === 'error' ? 'bg-red-50 border-red-400 text-red-700 dark:bg-red-900 dark:text-red-200' :
      'bg-blue-50 border-blue-400 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
    ]">
      <div class="flex items-center">
        <span class="font-medium mr-2">
          {{ notification.type === 'success' ? '✅' : notification.type === 'error' ? '❌' : 'ℹ️' }}
        </span>
        <span>{{ notification.message }}</span>
      </div>
      <button @click="notification.show = false" class="text-lg font-bold opacity-70 hover:opacity-100">
        ×
      </button>
    </div>

    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">資料更新管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">管理股票歷史資料的爬取與更新作業</p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton 
            @click="handleGetOverallStats"
            :loading="loading"
            :icon="ChartBarIcon"
            text="系統統計"
            variant="secondary"
          />
        </div>
      </div>
    </div>

    <!-- 系統統計資訊 -->
    <div v-if="overallStats" class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">系統統計</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div class="text-sm text-gray-500 dark:text-gray-400">有資料股票數</div>
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ overallStats.total_stocks }}</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div class="text-sm text-gray-500 dark:text-gray-400">總資料筆數</div>
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatNumber(overallStats.total_records) }}</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div class="text-sm text-gray-500 dark:text-gray-400">最新資料日期</div>
          <div class="text-lg font-bold text-gray-900 dark:text-white">{{ overallStats.latest_date || 'N/A' }}</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div class="text-sm text-gray-500 dark:text-gray-400">資料完整度</div>
          <div class="text-lg font-bold text-green-600">{{ overallStats.completeness || 0 }}%</div>
        </div>
      </div>
    </div>

    <!-- 單一股票資料更新 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">單一股票資料更新</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 股票代碼 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">股票代碼</label>
          <input
            v-model="singleStockSymbol"
            type="text"
            placeholder="如: 2330"
            maxlength="4"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        
        <!-- 執行按鈕 -->
        <div class="flex items-end">
          <ActionButton 
            @click="handleUpdateSingleStock"
            :loading="loading"
            :disabled="!singleStockSymbol || singleStockSymbol.length !== 4"
            :icon="ArrowPathIcon"
            text="爬取資料"
            loading-text="爬取中..."
            variant="primary"
            class="w-full"
          />
        </div>

        <!-- 檢查最新日期按鈕 -->
        <div class="flex items-end">
          <ActionButton 
            @click="handleCheckLatestDate"
            :loading="loading"
            :disabled="!singleStockSymbol || singleStockSymbol.length !== 4"
            :icon="CalendarIcon"
            text="檢查最新日期"
            variant="secondary"
            class="w-full"
          />
        </div>

        <!-- 查看統計按鈕 -->
        <div class="flex items-end">
          <ActionButton 
            @click="handleGetSingleStats"
            :loading="loading"
            :disabled="!singleStockSymbol || singleStockSymbol.length !== 4"
            :icon="ChartBarIcon"
            text="查看統計"
            variant="info"
            class="w-full"
          />
        </div>
      </div>

      <!-- 單一股票統計資訊 -->
      <div v-if="singleStockStats" class="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <h4 class="font-medium text-gray-900 dark:text-white mb-3">{{ singleStockSymbol }} 統計資訊</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">總筆數:</span>
            <span class="ml-2 font-medium">{{ singleStockStats.total_records }}</span>
          </div>
          <div v-if="singleStockStats.date_range">
            <span class="text-gray-500 dark:text-gray-400">日期範圍:</span>
            <span class="ml-2 font-medium">{{ singleStockStats.date_range.start_date }} ~ {{ singleStockStats.date_range.end_date }}</span>
          </div>
          <div v-if="latestTradeDate">
            <span class="text-gray-500 dark:text-gray-400">最新交易日:</span>
            <span class="ml-2 font-medium">{{ latestTradeDate }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 批次更新管理 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        批次更新管理
        <TooltipButton
          text="增量更新"
          tooltip="只更新缺失的資料，不重複更新已存在的資料"
          :icon="InformationCircleIcon"
          variant="ghost"
          size="sm"
        />
      </h3>
      
      <div class="space-y-4">
        <!-- 更新所有股票 -->
        <div class="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white">更新所有股票歷史資料 (Broker爬蟲)</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              使用8個broker網站爬取系統中所有股票的還原日線資料
            </p>
            <p class="text-xs text-blue-600 dark:text-blue-400 mt-1">
              資料來源: fubon-ebrokerdj, justdata.moneydj, yuanta, emega等broker網站
            </p>
            <div v-if="batchUpdateProgress.isRunning" class="mt-2">
              <div class="text-xs text-blue-600 dark:text-blue-400">
                執行中... 已處理 {{ batchUpdateProgress.processed }} / {{ batchUpdateProgress.total }} 檔股票
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                <div 
                  class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${(batchUpdateProgress.processed / batchUpdateProgress.total) * 100}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-500 mt-1">
                預估剩餘時間: {{ estimatedTimeRemaining }}
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <ActionButton 
              @click="handleUpdateAllStocks"
              :loading="loading || batchUpdateProgress.isRunning || taskLoading"
              :icon="ArrowPathIcon"
              text="開始更新"
              loading-text="創建任務中..."
              variant="success"
            />
            <NuxtLink to="/tasks/manual">
              <ActionButton 
                :icon="EyeIcon"
                text="查看進度"
                variant="secondary"
              />
            </NuxtLink>
          </div>
        </div>

        <!-- 最近更新記錄 -->
        <div v-if="recentUpdates.length > 0" class="mt-6">
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">最近更新記錄</h4>
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden">
            <div class="max-h-40 overflow-y-auto">
              <div
                v-for="update in recentUpdates"
                :key="update.id"
                class="px-4 py-2 border-b border-gray-200 dark:border-gray-600 last:border-b-0"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium">{{ update.symbol }}</span>
                    <span 
                      :class="[
                        'text-xs px-2 py-1 rounded-full',
                        update.status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                        update.status === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      ]"
                    >
                      {{ update.status === 'success' ? '成功' : update.status === 'error' ? '失敗' : '處理中' }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{ update.timestamp }}
                  </div>
                </div>
                <div v-if="update.message" class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                  {{ update.message }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  ChartBarIcon,
  CalendarIcon,
  InformationCircleIcon,
  EyeIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '資料更新管理'
})

// 使用組合式函數
const { 
  loading, 
  error, 
  updateStockData, 
  updateAllStockData,
  batchUpdateWithBrokerCrawler,
  getStockStats,
  getLatestTradeDate,
  getOverallStats
} = useStocks()

const { 
  createStockCrawlTask,
  getManualTasks,
  startTaskPolling,
  loading: taskLoading,
  error: taskError
} = useTasks()

// 響應式資料
const singleStockSymbol = ref('')
const overallStats = ref(null)
const singleStockStats = ref(null)
const latestTradeDate = ref(null)
const recentUpdates = ref([])

// 批次更新進度
const batchUpdateProgress = ref({
  isRunning: false,
  processed: 0,
  total: 0,
  startTime: null
})

// 通知系統
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// 顯示通知
const showNotification = (type, message, duration = 5000) => {
  notification.value = {
    show: true,
    type,
    message
  }
  
  setTimeout(() => {
    notification.value.show = false
  }, duration)
}

// 格式化數字
const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num?.toString() || '0'
}

// 預估剩餘時間
const estimatedTimeRemaining = computed(() => {
  if (!batchUpdateProgress.value.isRunning || !batchUpdateProgress.value.startTime) {
    return '計算中...'
  }
  
  const elapsed = Date.now() - batchUpdateProgress.value.startTime
  const processedCount = batchUpdateProgress.value.processed
  const totalCount = batchUpdateProgress.value.total
  
  if (processedCount === 0) return '計算中...'
  
  const avgTimePerStock = elapsed / processedCount
  const remainingStocks = totalCount - processedCount
  const remainingTime = avgTimePerStock * remainingStocks
  
  const minutes = Math.floor(remainingTime / 60000)
  const seconds = Math.floor((remainingTime % 60000) / 1000)
  
  return `${minutes}分${seconds}秒`
})

// API處理函數
const handleGetOverallStats = async () => {
  const result = await getOverallStats()
  if (result) {
    overallStats.value = result
    showNotification('success', '成功取得系統統計資訊')
  } else {
    showNotification('error', error.value || '取得系統統計資訊失敗')
  }
}

const handleUpdateSingleStock = async () => {
  if (!singleStockSymbol.value || singleStockSymbol.value.length !== 4) {
    showNotification('error', '請輸入有效的4位數股票代碼')
    return
  }

  const startTime = Date.now()
  showNotification('info', `開始爬取 ${singleStockSymbol.value} 的歷史資料...`)
  
  // 添加到更新記錄
  const updateRecord = {
    id: Date.now(),
    symbol: singleStockSymbol.value,
    status: 'processing',
    timestamp: new Date().toLocaleTimeString(),
    message: '開始爬取資料...'
  }
  recentUpdates.value.unshift(updateRecord)

  const result = await updateStockData(singleStockSymbol.value)
  const endTime = Date.now()
  const duration = ((endTime - startTime) / 1000).toFixed(1)
  
  // 更新記錄狀態
  const record = recentUpdates.value.find(r => r.id === updateRecord.id)
  if (record) {
    record.status = result ? 'success' : 'error'
    record.message = result 
      ? `成功處理 ${result.records_processed || 0} 筆資料 (耗時 ${duration}秒)`
      : error.value || '更新失敗'
  }

  if (result) {
    showNotification('success', 
      `${singleStockSymbol.value} 資料更新完成！處理了 ${result.records_processed || 0} 筆資料 (耗時 ${duration}秒)`
    )
    // 重新獲取統計資訊
    await handleGetSingleStats()
  } else {
    showNotification('error', error.value || '更新歷史資料失敗')
  }
}

const handleCheckLatestDate = async () => {
  const result = await getLatestTradeDate(singleStockSymbol.value)
  
  if (result) {
    latestTradeDate.value = result.latest_trade_date
    showNotification('success', result.has_data ? `最新交易日: ${result.latest_trade_date}` : result.message)
  } else {
    showNotification('error', error.value || '檢查最新交易日失敗')
  }
}

const handleGetSingleStats = async () => {
  const result = await getStockStats(singleStockSymbol.value)
  
  if (result) {
    singleStockStats.value = result
    showNotification('success', '成功取得統計資訊')
  } else {
    showNotification('error', error.value || '取得統計資訊失敗')
  }
}

const handleUpdateAllStocks = async () => {
  if (batchUpdateProgress.value.isRunning) {
    showNotification('error', '批次更新正在進行中，請稍候')
    return
  }

  try {
    // 使用新的任務管理API創建任務
    showNotification('info', '正在創建broker爬蟲批次更新任務...')
    
    const result = await createStockCrawlTask()
    
    if (result) {
      showNotification('success', 
        `任務已創建！將處理 ${result.symbols_count} 檔股票，您可以在任務管理中查看執行進度`
      )
      
      // 顯示任務管理鏈接
      setTimeout(() => {
        showNotification('info', 
          '任務已在背景執行，前往「任務管理 > 手動執行任務」查看即時進度',
          8000
        )
      }, 2000)
      
      // 開始輪詢任務狀態，並在任務完成時重新整理統計資訊
      startTaskPolling({
        onTaskCompleted: async (completedTaskIds) => {
          console.log('批次更新任務完成，重新整理統計資訊...', completedTaskIds)
          // 重新獲取系統統計資訊
          await handleGetOverallStats()
          showNotification('success', '批次更新任務已完成，統計資訊已更新')
        }
      })
    } else {
      showNotification('error', taskError.value || '創建任務失敗')
    }
  } catch (err) {
    showNotification('error', '創建任務時發生錯誤：' + err.message)
  }
}

// 監聽股票代碼變化，清除相關資料
watch(singleStockSymbol, () => {
  singleStockStats.value = null
  latestTradeDate.value = null
})

// 組件掛載時獲取系統統計
onMounted(async () => {
  await handleGetOverallStats()
})
</script>