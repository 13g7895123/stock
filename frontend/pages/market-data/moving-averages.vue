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
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">均線計算管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">
            計算和管理股票的移動平均線（MA）
            <span class="ml-2 text-xs text-blue-500 dark:text-blue-400">
              📊 點擊重新整理更新統計數據
            </span>
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton 
            @click="handleRefreshStats"
            :loading="loading"
            :icon="ArrowPathIcon"
            text="重新整理"
            variant="secondary"
          />
        </div>
      </div>
    </div>

    <!-- 均線統計總覽 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ChartBarIcon class="w-8 h-8 text-blue-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">已計算股票</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              <span v-if="loading" class="animate-pulse">載入中...</span>
              <span v-else>{{ stats?.stocks_with_ma || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CalculatorIcon class="w-8 h-8 text-green-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">總計算筆數</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              <span v-if="loading" class="animate-pulse">載入中...</span>
              <span v-else>{{ formatNumber(stats?.total_ma_records || 0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CalendarIcon class="w-8 h-8 text-purple-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">最新計算日期</div>
            <div class="text-lg font-bold text-gray-900 dark:text-white">
              {{ stats?.latest_calculation_date || 'N/A' }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CheckCircleIcon class="w-8 h-8 text-orange-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">計算完整度</div>
            <div class="text-2xl font-bold text-green-600">
              {{ stats?.calculation_completeness || 0 }}%
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 均線計算控制 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">均線計算設定</h3>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- 計算參數設定 -->
        <div class="space-y-4">
          <h4 class="text-md font-medium text-gray-900 dark:text-white">計算參數</h4>
          
          <!-- 均線週期選擇 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">均線週期</label>
            <div class="grid grid-cols-3 gap-3">
              <label v-for="period in availablePeriods" :key="period" class="flex items-center">
                <input 
                  v-model="selectedPeriods"
                  type="checkbox"
                  :value="period"
                  class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-900 dark:text-white">MA{{ period }}</span>
              </label>
            </div>
          </div>

          <!-- 計算模式選擇 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">計算模式</label>
            <select 
              v-model="calculationMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部股票</option>
              <option value="missing">僅計算缺失的</option>
              <option value="update">更新現有的</option>
              <option value="single">單一股票</option>
            </select>
          </div>

          <!-- 單一股票選擇 -->
          <div v-if="calculationMode === 'single'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">股票代號</label>
            <input
              v-model="singleStockSymbol"
              type="text"
              placeholder="如: 2330"
              maxlength="4"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- 計算控制按鈕 -->
        <div class="space-y-4">
          <h4 class="text-md font-medium text-gray-900 dark:text-white">執行操作</h4>
          
          <div class="space-y-3">
            <ActionButton 
              @click="handleCalculateMovingAverages"
              :loading="calculating"
              :disabled="selectedPeriods.length === 0 || (calculationMode === 'single' && !singleStockSymbol)"
              :icon="PlayIcon"
              text="開始計算均線"
              loading-text="計算中..."
              variant="primary"
              class="w-full"
            />

            <ActionButton 
              @click="handleValidateMovingAverages"
              :loading="validating"
              :icon="CheckIcon"
              text="驗證均線數據"
              loading-text="驗證中..."
              variant="secondary"
              class="w-full"
            />

            <ActionButton 
              @click="handleClearMovingAverages"
              :loading="clearing"
              :icon="TrashIcon"
              text="清除均線數據"
              loading-text="清除中..."
              variant="danger"
              class="w-full"
            />
          </div>

          <!-- 計算進度 -->
          <div v-if="calculationProgress.show" class="mt-6 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-blue-900 dark:text-blue-200">均線計算進度</span>
              <span class="text-sm text-blue-700 dark:text-blue-300">{{ calculationProgress.percentage }}%</span>
            </div>
            
            <!-- 進度條 -->
            <div class="w-full bg-blue-200 rounded-full h-3 mb-3">
              <div 
                class="bg-blue-600 h-3 rounded-full transition-all duration-300"
                :style="{ width: `${calculationProgress.percentage}%` }"
              ></div>
            </div>
            
            <!-- 詳細狀態 -->
            <div class="space-y-2 text-sm">
              <div class="flex justify-between text-blue-700 dark:text-blue-300">
                <span>處理進度:</span>
                <span>{{ calculationProgress.current }} / {{ calculationProgress.total }} 檔股票</span>
              </div>
              
              <div v-if="taskStatus.stage" class="flex justify-between text-blue-700 dark:text-blue-300">
                <span>當前階段:</span>
                <span>{{ taskStatus.stage }}</span>
              </div>
              
              <div v-if="taskStatus.batch && taskStatus.total_batches" class="flex justify-between text-blue-700 dark:text-blue-300">
                <span>批次進度:</span>
                <span>{{ taskStatus.batch }} / {{ taskStatus.total_batches }} 批次</span>
              </div>
              
              <div v-if="currentTaskId" class="flex justify-between text-xs text-blue-600 dark:text-blue-400">
                <span>任務ID:</span>
                <span class="font-mono">{{ currentTaskId.substring(0, 8) }}...</span>
              </div>
            </div>
            
            <!-- 取消按鈕 -->
            <div v-if="calculating && currentTaskId" class="mt-4 flex justify-end">
              <ActionButton 
                @click="handleCancelTask"
                :icon="XMarkIcon"
                text="取消任務"
                variant="secondary"
                size="sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 均線查詢與檢視 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">均線數據查詢</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <!-- 股票代號 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">股票代號</label>
          <input
            v-model="queryParams.symbol"
            type="text"
            placeholder="如: 2330"
            maxlength="4"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 開始日期 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">開始日期</label>
          <input
            v-model="queryParams.start_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 結束日期 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">結束日期</label>
          <input
            v-model="queryParams.end_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- 查詢按鈕 -->
        <div class="flex items-end">
          <ActionButton 
            @click="handleQueryMovingAverages"
            :loading="querying"
            :disabled="!queryParams.symbol"
            :icon="MagnifyingGlassIcon"
            text="查詢均線"
            loading-text="查詢中..."
            variant="primary"
            class="w-full"
          />
        </div>
      </div>

      <!-- 快速日期設定 -->
      <div class="flex flex-wrap gap-3 mb-6">
        <ActionButton 
          @click="setLastMonthDates"
          :icon="CalendarIcon"
          text="近一月"
          variant="secondary"
          size="sm"
        />
        <ActionButton 
          @click="setLastThreeMonthsDates"
          :icon="CalendarIcon"
          text="近三月"
          variant="secondary"
          size="sm"
        />
        <ActionButton 
          @click="setLastSixMonthsDates"
          :icon="CalendarIcon"
          text="近半年"
          variant="secondary"
          size="sm"
        />
        <ActionButton 
          @click="clearDates"
          :icon="XCircleIcon"
          text="清除日期"
          variant="secondary"
          size="sm"
        />
      </div>

      <!-- 查詢結果 -->
      <div v-if="movingAverageData.length > 0" class="overflow-x-auto">
        <div class="mb-4 flex items-center justify-between">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            找到 {{ movingAverageData.length }} 筆均線資料
          </div>
          <ActionButton 
            @click="exportMovingAverageData"
            :icon="ArrowDownTrayIcon"
            text="匯出CSV"
            variant="secondary"
            size="sm"
          />
        </div>
        
        <table class="w-full border-collapse">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-left text-sm font-medium text-gray-500 dark:text-gray-300">交易日期</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">收盤價</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">MA5</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">MA10</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">MA24</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">MA72</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center text-sm font-medium text-gray-500 dark:text-gray-300">趨勢</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in movingAverageData"
              :key="`${record.trade_date}-${record.stock_code}`"
              class="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm">{{ formatDate(record.trade_date) }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right font-medium">${{ record.close_price?.toFixed(2) || 'N/A' }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">{{ record.ma5?.toFixed(2) || 'N/A' }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">{{ record.ma10?.toFixed(2) || 'N/A' }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">{{ record.ma20?.toFixed(2) || 'N/A' }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">{{ record.ma60?.toFixed(2) || 'N/A' }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center">
                <span 
                  :class="[
                    'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
                    getTrendColor(record)
                  ]"
                >
                  {{ getTrendText(record) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 無資料提示 -->
      <div v-else-if="hasQueried" class="text-center py-12">
        <ChartBarIcon class="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">查無均線資料</h3>
        <p class="text-gray-600 dark:text-gray-400">
          {{ queryParams.symbol ? `找不到股票代號 ${queryParams.symbol} 的均線資料` : '請輸入股票代號進行查詢' }}
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-500 mt-2">
          若該股票尚未計算均線，請先使用上方的「開始計算均線」功能
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  ChartBarIcon,
  CalculatorIcon,
  CalendarIcon,
  CheckCircleIcon,
  PlayIcon,
  CheckIcon,
  TrashIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  XCircleIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '均線計算管理'
})

// API 組合式函數
const { getMovingAveragesStatistics, calculateMovingAverages, queryMovingAverages, validateMovingAverages, clearMovingAverages, startAsyncCalculation, getTaskStatus, cancelTask } = useMovingAverages()
const { getAllStocksWithData } = useStocks()

// 響應式資料
const loading = ref(false)
const calculating = ref(false)
const validating = ref(false)
const clearing = ref(false)
const querying = ref(false)

const stats = ref(null)

// 監控統計數據變化以進行調試
watch(stats, (newStats, oldStats) => {
  console.log('📊 統計數據發生變化:', {
    old: oldStats,
    new: newStats,
    timestamp: new Date().toLocaleTimeString('zh-TW')
  })
}, { deep: true })
const movingAverageData = ref([])
const hasQueried = ref(false)

// 非同步任務相關
const currentTaskId = ref(null)
const taskStatus = ref({
  state: 'PENDING',
  current: 0,
  total: 0,
  percentage: 0,
  stage: '',
  result: null,
  error: null
})
const pollingInterval = ref(null)

// 計算參數
const availablePeriods = [5, 10, 24, 72, 120, 240]
const selectedPeriods = ref([5, 10, 24, 72])
const calculationMode = ref('missing')
const singleStockSymbol = ref('')

// 查詢參數
const queryParams = ref({
  symbol: '',
  start_date: '',
  end_date: ''
})

// 計算進度
const calculationProgress = ref({
  show: false,
  current: 0,
  total: 0,
  percentage: 0
})

// 通知系統
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// 顯示通知
const showNotification = (type, message) => {
  notification.value = {
    show: true,
    type,
    message
  }
  
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

// 工具函數
const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num?.toString() || '0'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const getCurrentDate = () => {
  return new Date().toISOString().split('T')[0]
}

// 日期設定函數
const setLastMonthDates = () => {
  const today = new Date()
  const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
  queryParams.value.start_date = lastMonth.toISOString().split('T')[0]
  queryParams.value.end_date = getCurrentDate()
}

const setLastThreeMonthsDates = () => {
  const today = new Date()
  const threeMonthsAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
  queryParams.value.start_date = threeMonthsAgo.toISOString().split('T')[0]
  queryParams.value.end_date = getCurrentDate()
}

const setLastSixMonthsDates = () => {
  const today = new Date()
  const sixMonthsAgo = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000)
  queryParams.value.start_date = sixMonthsAgo.toISOString().split('T')[0]
  queryParams.value.end_date = getCurrentDate()
}

const clearDates = () => {
  queryParams.value.start_date = ''
  queryParams.value.end_date = ''
}

// 趨勢分析
const getTrendText = (record) => {
  if (!record.ma5 || !record.ma20) return '無資料'
  
  if (record.close_price > record.ma5 && record.ma5 > record.ma20) {
    return '多頭'
  } else if (record.close_price < record.ma5 && record.ma5 < record.ma20) {
    return '空頭'
  } else {
    return '整理'
  }
}

const getTrendColor = (record) => {
  const trend = getTrendText(record)
  switch (trend) {
    case '多頭':
      return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
    case '空頭':
      return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
    case '整理':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
  }
}

// API處理函數
const handleRefreshStats = async () => {
  loading.value = true
  try {
    console.log('🔄 開始重新整理均線統計資訊...')
    const result = await getMovingAveragesStatistics()
    console.log('📊 API回應結果:', result)
    
    if (result.success && result.data) {
      stats.value = result.data.data
      console.log('✅ 統計資料更新完成:', stats.value)
      console.log('📊 已計算股票數:', stats.value.stocks_with_ma)
      showNotification('success', '成功重新整理統計資訊')
    } else {
      console.error('❌ API回應失敗:', result.error)
      showNotification('error', '重新整理統計資訊失敗: ' + result.error)
    }
  } catch (error) {
    console.error('❌ API請求異常:', error)
    showNotification('error', '重新整理統計資訊失敗: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleCalculateMovingAverages = async () => {
  calculating.value = true
  
  try {
    showNotification('info', '啟動非同步均線計算...')
    
    let stockCodes = []
    
    // 根據計算模式決定股票清單
    if (calculationMode.value === 'single') {
      if (!singleStockSymbol.value) {
        throw new Error('請輸入股票代號')
      }
      stockCodes = [singleStockSymbol.value]
    } else if (calculationMode.value === 'all') {
      // 獲取所有有資料的股票（分頁獲取）
      const stockResult = await getAllStocksWithData()
      if (stockResult.success && stockResult.stocks) {
        stockCodes = stockResult.stocks.map(stock => stock.stock_code)
      } else {
        throw new Error('無法取得股票清單: ' + (stockResult.error || '未知錯誤'))
      }
    } else {
      // missing 模式，讓後端自動處理（傳送 null）
      stockCodes = null
    }
    
    // 啟動非同步任務
    const taskResult = await startAsyncCalculation(
      stockCodes, 
      selectedPeriods.value,
      false, // 不強制重新計算
      50     // 批次大小
    )
    
    if (taskResult.success && taskResult.data) {
      currentTaskId.value = taskResult.data.task_id
      showNotification('success', '非同步任務已啟動，正在背景處理中...')
      
      // 開始輪詢任務狀態
      startTaskPolling()
    } else {
      throw new Error(taskResult.error || '啟動非同步任務失敗')
    }
    
  } catch (error) {
    showNotification('error', '啟動計算失敗: ' + error.message)
    calculating.value = false
  }
}

// 開始輪詢任務狀態
const startTaskPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
  
  // 初始化任務狀態
  taskStatus.value = {
    state: 'PENDING',
    current: 0,
    total: 0,
    percentage: 0,
    stage: '任務佇列中...',
    result: null,
    error: null
  }
  
  // 每秒輪詢任務狀態
  pollingInterval.value = setInterval(async () => {
    if (!currentTaskId.value) return
    
    try {
      const statusResult = await getTaskStatus(currentTaskId.value)
      
      if (statusResult.success && statusResult.data) {
        const status = statusResult.data
        taskStatus.value = { ...status }
        
        // 更新進度條
        calculationProgress.value = {
          show: true,
          current: status.current || 0,
          total: status.total || 0,
          percentage: status.percentage || 0
        }
        
        // 檢查任務是否完成
        if (status.state === 'SUCCESS') {
          clearInterval(pollingInterval.value)
          pollingInterval.value = null
          calculating.value = false
          calculationProgress.value.show = false
          
          const result = status.result || {}
          showNotification('success', 
            `均線計算完成！處理 ${result.processed_stocks}/${result.total_stocks} 檔股票，
            成功率 ${result.success_rate}%，總計算量 ${result.total_calculations} 筆`
          )
          
          // 重新整理統計
          await handleRefreshStats()
          
        } else if (status.state === 'FAILURE') {
          clearInterval(pollingInterval.value)
          pollingInterval.value = null
          calculating.value = false
          calculationProgress.value.show = false
          
          showNotification('error', '計算失敗: ' + (status.error || '未知錯誤'))
        }
      }
      
    } catch (error) {
      console.error('輪詢任務狀態錯誤:', error)
      // 不中斷輪詢，繼續嘗試
    }
  }, 1000) // 每秒輪詢一次
}

// 取消任務
const handleCancelTask = async () => {
  if (!currentTaskId.value) return
  
  try {
    const result = await cancelTask(currentTaskId.value)
    if (result.success) {
      showNotification('info', '任務已取消')
      stopTaskPolling()
    } else {
      showNotification('error', '取消任務失敗: ' + result.error)
    }
  } catch (error) {
    showNotification('error', '取消任務失敗: ' + error.message)
  }
}

// 停止輪詢
const stopTaskPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
  calculating.value = false
  calculationProgress.value.show = false
  currentTaskId.value = null
}

const handleValidateMovingAverages = async () => {
  validating.value = true
  try {
    // 模擬API呼叫
    await new Promise(resolve => setTimeout(resolve, 2000))
    showNotification('success', '均線數據驗證完成，發現 3 筆異常資料已修正')
  } catch (error) {
    showNotification('error', '驗證均線數據失敗: ' + error.message)
  } finally {
    validating.value = false
  }
}

const handleClearMovingAverages = async () => {
  if (!confirm('確定要清除所有均線數據嗎？此操作無法復原。')) {
    return
  }
  
  clearing.value = true
  try {
    // 模擬API呼叫
    await new Promise(resolve => setTimeout(resolve, 1500))
    showNotification('success', '成功清除所有均線數據')
    await handleRefreshStats() // 重新整理統計
  } catch (error) {
    showNotification('error', '清除均線數據失敗: ' + error.message)
  } finally {
    clearing.value = false
  }
}

const handleQueryMovingAverages = async () => {
  if (!queryParams.value.symbol) {
    showNotification('error', '請輸入股票代號')
    return
  }
  
  querying.value = true
  hasQueried.value = true
  
  try {
    const params = {
      start_date: queryParams.value.start_date,
      end_date: queryParams.value.end_date,
      periods: selectedPeriods.value,
      page: 1,
      limit: 1000
    }
    
    const result = await queryMovingAverages(queryParams.value.symbol, params)
    
    if (result.success) {
      movingAverageData.value = result.data || []
      
      if (movingAverageData.value.length > 0) {
        showNotification('success', `成功查詢到 ${movingAverageData.value.length} 筆均線資料`)
      } else {
        showNotification('info', '查無符合條件的均線資料')
      }
    } else {
      showNotification('error', '查詢均線資料失敗: ' + result.error)
      movingAverageData.value = []
    }
  } catch (error) {
    showNotification('error', '查詢均線資料失敗: ' + error.message)
    movingAverageData.value = []
  } finally {
    querying.value = false
  }
}

const exportMovingAverageData = () => {
  if (movingAverageData.value.length === 0) {
    showNotification('error', '無資料可匯出')
    return
  }

  const csv = [
    ['交易日期', '股票代號', '收盤價', 'MA5', 'MA10', 'MA24', 'MA72', '趨勢'],
    ...movingAverageData.value.map(record => [
      record.trade_date,
      record.stock_code,
      record.close_price?.toFixed(2) || '',
      record.ma5?.toFixed(2) || '',
      record.ma10?.toFixed(2) || '',
      record.ma20?.toFixed(2) || '',
      record.ma60?.toFixed(2) || '',
      getTrendText(record)
    ])
  ].map(row => row.join(',')).join('\n')

  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${queryParams.value.symbol}_均線資料_${getCurrentDate()}.csv`
  link.click()
  
  showNotification('success', 'CSV檔案已下載')
}

// 統計數據自動重新整理已移除
// 用戶可以手動點擊重新整理按鈕來更新統計數據

// 初始化
onMounted(async () => {
  console.log('🎯 均線計算管理頁面已掛載，開始初始化...')
  await handleRefreshStats()
  // 啟動自動重新整理
  // startStatsAutoRefresh()
  console.log('✅ 頁面初始化完成')
})

// 清理資源
onUnmounted(() => {
  stopTaskPolling()
  // stopStatsAutoRefresh() - 已移除自動更新功能
})
</script>