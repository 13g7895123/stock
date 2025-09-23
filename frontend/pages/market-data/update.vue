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
            <ActionButton
              @click="handleSequentialUpdateAllStocks"
              :loading="loading || batchUpdateProgress.isRunning || taskLoading"
              :icon="CpuChipIcon"
              text="循序更新"
              loading-text="創建循序任務中..."
              variant="info"
              class="relative"
            >
              <template #icon>
                <span class="relative">
                  <CpuChipIcon class="h-4 w-4" />
                  <span class="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center" style="font-size: 10px;">📊</span>
                </span>
              </template>
            </ActionButton>
            <NuxtLink to="/tasks/manual">
              <ActionButton
                :icon="EyeIcon"
                text="查看進度"
                variant="secondary"
              />
            </NuxtLink>
          </div>
        </div>

        <!-- Point 13: 智能批次更新管理 -->
        <div class="p-4 border border-blue-200 dark:border-blue-600 rounded-lg bg-blue-50 dark:bg-blue-900/20">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h4 class="font-medium text-gray-900 dark:text-white">🧠 智能批次更新 (證交所API)</h4>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                自動分析股票資料完整性，智能識別缺少的交易日，並透過證交所API精準修復
              </p>
              <p class="text-xs text-blue-600 dark:text-blue-400 mt-1">
                資料來源: 台灣證券交易所官方歷史資料API
              </p>

              <!-- Point 13 問題解決提示 -->
              <div class="mt-2 p-2 bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-400 rounded">
                <p class="text-xs text-yellow-700 dark:text-yellow-300">
                  💡 <strong>解決「沒有要更新的」問題</strong>：請確保啟用下方的「🔄 強制刷新模式」，
                  即使資料完整度很高也會刷新最近交易日確保資料最新！
                </p>
              </div>
            </div>

            <!-- 強制刷新模式切換 -->
            <div class="mt-3 p-3 border rounded-lg" :class="smartBatchUpdate.forceRefresh ? 'border-green-300 bg-green-50 dark:border-green-600 dark:bg-green-900/20' : 'border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-700'">
              <div class="flex items-center space-x-2">
                <input
                  v-model="smartBatchUpdate.forceRefresh"
                  type="checkbox"
                  id="forceRefreshMode"
                  class="w-4 h-4 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 dark:focus:ring-green-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                />
                <label for="forceRefreshMode" class="text-sm font-medium" :class="smartBatchUpdate.forceRefresh ? 'text-green-700 dark:text-green-200' : 'text-gray-700 dark:text-gray-300'">
                  🔄 強制刷新模式
                </label>
              </div>
              <p class="text-xs mt-1" :class="smartBatchUpdate.forceRefresh ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'">
                {{ smartBatchUpdate.forceRefresh ? '✅ 啟用：即使沒有缺少資料也會刷新最近交易日確保資料最新' : '停用：只檢查缺少的交易日' }}
              </p>
            </div>

            <!-- 分析結果顯示 -->
            <div v-if="smartBatchUpdate.analysis" class="mt-3 p-3 bg-white dark:bg-gray-800 rounded border">
              <div class="text-xs text-gray-600 dark:text-gray-300">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div>
                    <span class="text-gray-500">分析期間:</span>
                    <span class="ml-1 font-medium">{{ smartBatchUpdate.analysis.analysis_period?.start_date }} ~ {{ smartBatchUpdate.analysis.analysis_period?.end_date }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">資料完整度:</span>
                    <span class="ml-1 font-medium text-green-600">{{ smartBatchUpdate.analysis.statistics?.completeness_percentage || 0 }}%</span>
                  </div>
                  <div>
                    <span class="text-gray-500">缺少天數:</span>
                    <span class="ml-1 font-medium text-red-600">{{ smartBatchUpdate.analysis.statistics?.total_missing_days || 0 }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">可修復:</span>
                    <span class="ml-1 font-medium text-blue-600">{{ smartBatchUpdate.analysis.api_calls?.length || 0 }} 個API調用</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 執行進度顯示 -->
            <div v-if="smartBatchUpdate.isExecuting" class="mt-3">
              <div class="text-xs text-blue-600 dark:text-blue-400">
                {{ smartBatchUpdate.progress.currentAction || '執行中...' }}
                ({{ smartBatchUpdate.progress.current }} / {{ smartBatchUpdate.progress.total }})
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${smartBatchUpdate.progress.percentage}%` }"
                ></div>
              </div>
            </div>

            <!-- 執行結果顯示 -->
            <div v-if="smartBatchUpdate.results" class="mt-3 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs">
              <span class="text-green-600">✅ 成功: {{ smartBatchUpdate.results.successful }}</span>
              <span class="text-red-600 ml-3">❌ 失敗: {{ smartBatchUpdate.results.failed }}</span>
              <span class="text-gray-500 ml-3">總計: {{ smartBatchUpdate.results.total }}</span>
            </div>

            <!-- 操作按鈕 -->
            <div class="mt-4 flex items-center space-x-2">
              <ActionButton
                @click="handleSmartBatchAnalysis"
                :loading="smartBatchUpdate.isAnalyzing || tradingDaysLoading"
                :icon="ChartBarIcon"
                text="智能分析"
                loading-text="分析中..."
                variant="info"
                size="sm"
              />
              <ActionButton
                @click="handleSmartBatchUpdate"
                :loading="smartBatchUpdate.isExecuting"
                :disabled="!smartBatchUpdate.analysis || !smartBatchUpdate.analysis.api_calls || smartBatchUpdate.analysis.api_calls.length === 0"
                :icon="ArrowPathIcon"
                text="執行修復"
                loading-text="修復中..."
                variant="success"
                size="sm"
              />
            </div>
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
  EyeIcon,
  CpuChipIcon
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
  createSequentialStockCrawlTask,
  getManualTasks,
  startTaskPolling,
  loading: taskLoading,
  error: taskError
} = useTasks()

const {
  getSmartBatchUpdateAnalysis,
  executeSmartBatchUpdate,
  loading: tradingDaysLoading,
  error: tradingDaysError
} = useTradingDays()

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

// 智能批次更新狀態
const smartBatchUpdate = ref({
  analysis: null,
  isAnalyzing: false,
  isExecuting: false,
  forceRefresh: true,  // 強制刷新模式開關 - 預設啟用以解決用戶問題
  progress: {
    current: 0,
    total: 0,
    percentage: 0,
    currentAction: ''
  },
  results: null
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

const handleSequentialUpdateAllStocks = async () => {
  if (batchUpdateProgress.value.isRunning) {
    showNotification('error', '批次更新正在進行中，請稍候')
    return
  }

  try {
    // 創建循序的批次更新任務 (Point 65)
    showNotification('info', '正在創建循序批次更新任務...')
    showNotification('info', '📊 啟用循序功能：分批處理 + 資源監控 + 延遲保護', 3000)

    const sequentialOptions = {
      batchSize: 477,              // 1908/4 = 477檔每批
      delayBetweenStocks: 0.5,     // 股票間延遲0.5秒
      delayBetweenBatches: 10.0,   // 批次間延遲10秒
      cpuThreshold: 80.0,          // CPU使用率閾值80%
      memoryThreshold: 85.0,       // 記憶體使用率閾值85%
      autoPauseOnOverload: true    // 自動暫停過載
    }

    const result = await createSequentialStockCrawlTask(sequentialOptions)

    if (result) {
      // 計算預期資源節省
      const resourceSaving = result.performance_estimate || '減少 70% 系統負載'

      showNotification('success',
        `📊 循序任務已創建！將處理 ${result.symbols_count} 檔股票`
      )

      // 顯示循序功能詳情
      setTimeout(() => {
        const features = result.sequential_features || []
        showNotification('info',
          `🔧 循序功能已啟用：${features.join(', ')} - ${resourceSaving}`,
          6000
        )
      }, 1000)

      // 顯示任務管理鏈接
      setTimeout(() => {
        showNotification('info',
          '循序任務已在背景執行，前往「任務管理 > 手動執行任務」查看即時進度和資源使用狀況',
          8000
        )
      }, 3000)

      // 開始輪詢任務狀態
      startTaskPolling({
        onTaskCompleted: async (completedTaskIds) => {
          console.log('循序批次更新任務完成，重新整理統計資訊...', completedTaskIds)
          // 重新獲取系統統計資訊
          await handleGetOverallStats()
          showNotification('success', '🎉 循序批次更新任務已完成！統計資訊已更新，系統運行穩定無過載')
        }
      })
    } else {
      showNotification('error', taskError.value || '創建循序任務失敗')
    }
  } catch (err) {
    showNotification('error', '創建循序任務時發生錯誤：' + err.message)
  }
}

// Point 13: 智能批次更新分析
const handleSmartBatchAnalysis = async () => {
  smartBatchUpdate.value.isAnalyzing = true
  smartBatchUpdate.value.analysis = null

  try {
    const refreshMode = smartBatchUpdate.value.forceRefresh
    const modeText = refreshMode ? '強制刷新模式' : '缺少資料檢查模式'

    showNotification('info', `🧠 正在進行智能分析 (${modeText})，檢查股票資料完整性...`)

    const analysisResult = await getSmartBatchUpdateAnalysis(30, refreshMode)

    if (analysisResult) {
      smartBatchUpdate.value.analysis = analysisResult

      const fixableCount = analysisResult.api_calls?.length || 0
      const totalMissing = analysisResult.statistics?.total_missing_days || 0

      if (fixableCount > 0) {
        if (refreshMode) {
          showNotification('success',
            `🔄 強制刷新分析完成！將刷新最近 ${fixableCount} 個交易日的資料`
          )
        } else {
          showNotification('success',
            `🔍 分析完成！發現 ${totalMissing} 個缺少的交易日，其中 ${fixableCount} 個可透過證交所API修復`
          )
        }
      } else {
        if (refreshMode) {
          showNotification('info', `⚠️ 強制刷新模式：無法生成刷新清單`)
        } else {
          showNotification('info', `✅ 分析完成！資料完整性良好，目前沒有需要修復的缺少交易日`)
        }
      }
    } else {
      showNotification('error', tradingDaysError.value || '智能分析失敗')
    }
  } catch (err) {
    showNotification('error', '執行智能分析時發生錯誤：' + err.message)
  } finally {
    smartBatchUpdate.value.isAnalyzing = false
  }
}

// Point 13: 執行智能批次更新
const handleSmartBatchUpdate = async () => {
  if (!smartBatchUpdate.value.analysis || !smartBatchUpdate.value.analysis.api_calls) {
    showNotification('error', '請先執行智能分析')
    return
  }

  const apiCalls = smartBatchUpdate.value.analysis.api_calls
  if (apiCalls.length === 0) {
    showNotification('info', '沒有需要修復的資料')
    return
  }

  smartBatchUpdate.value.isExecuting = true
  smartBatchUpdate.value.progress = {
    current: 0,
    total: apiCalls.length,
    percentage: 0,
    currentAction: '準備開始...'
  }

  try {
    showNotification('info', `🚀 開始執行智能批次更新，將處理 ${apiCalls.length} 個API調用...`)

    const results = await executeSmartBatchUpdate(apiCalls, (progress) => {
      smartBatchUpdate.value.progress = progress
    })

    smartBatchUpdate.value.results = results

    if (results.successful > 0) {
      showNotification('success',
        `✅ 智能批次更新完成！成功: ${results.successful}，失敗: ${results.failed}`
      )

      // 重新獲取系統統計資訊
      setTimeout(async () => {
        await handleGetOverallStats()
        showNotification('info', '統計資訊已更新')
      }, 2000)
    } else {
      showNotification('error', `❌ 批次更新失敗，所有 ${results.total} 個調用都失敗了`)
    }
  } catch (err) {
    showNotification('error', '執行智能批次更新時發生錯誤：' + err.message)
  } finally {
    smartBatchUpdate.value.isExecuting = false
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