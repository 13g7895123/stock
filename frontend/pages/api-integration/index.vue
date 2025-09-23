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
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">API 整合測試中心</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">測試並驗證所有系統 API 端點功能</p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton
            @click="testAllAPIs"
            :loading="globalLoading"
            :icon="PlayIcon"
            text="測試所有 API"
            variant="success"
          />
        </div>
      </div>
    </div>

    <!-- API 分類選單 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="category in apiCategories"
          :key="category.key"
          @click="activeCategory = category.key"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeCategory === category.key
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          {{ category.name }} ({{ category.count }})
        </button>
      </div>
    </div>

    <!-- API 測試區域 -->
    <div class="space-y-4">
      <!-- 健康檢查 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'health'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <HeartIcon class="w-5 h-5 mr-2 text-red-500" />
          健康檢查 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ApiTestButton
            title="基本健康檢查"
            endpoint="GET /health/"
            @test="testHealthCheck"
            :loading="loading.health"
            :result="results.health"
          />
          <ApiTestButton
            title="詳細健康檢查"
            endpoint="GET /health/detailed"
            @test="testDetailedHealthCheck"
            :loading="loading.healthDetailed"
            :result="results.healthDetailed"
          />
          <ApiTestButton
            title="就緒檢查"
            endpoint="GET /health/readiness"
            @test="testReadinessCheck"
            :loading="loading.readiness"
            :result="results.readiness"
          />
          <ApiTestButton
            title="存活檢查"
            endpoint="GET /health/liveness"
            @test="testLivenessCheck"
            :loading="loading.liveness"
            :result="results.liveness"
          />
        </div>
      </div>

      <!-- 股票同步 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'sync'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <ArrowPathIcon class="w-5 h-5 mr-2 text-blue-500" />
          股票同步 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ApiTestButton
            title="股票數量統計"
            endpoint="GET /sync/stocks/count"
            @test="testStockCount"
            :loading="loading.stockCount"
            :result="results.stockCount"
          />
          <ApiTestButton
            title="同步股票列表"
            endpoint="POST /sync/stocks"
            @test="testSyncStocks"
            :loading="loading.syncStocks"
            :result="results.syncStocks"
          />
          <ApiTestButton
            title="爬取股票列表"
            endpoint="GET /sync/stocks/crawl"
            @test="testCrawlStocks"
            :loading="loading.crawlStocks"
            :result="results.crawlStocks"
          />
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="驗證代號"
              endpoint="GET /sync/stocks/validate/{symbol}"
              @test="testValidateSymbol"
              :loading="loading.validateSymbol"
              :result="results.validateSymbol"
              :disabled="!testStockSymbol"
            />
          </div>
        </div>
      </div>

      <!-- 股票資料 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'stocks'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <BuildingLibraryIcon class="w-5 h-5 mr-2 text-green-500" />
          股票資料 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ApiTestButton
            title="股票列表"
            endpoint="GET /stocks/list"
            @test="testStockList"
            :loading="loading.stockList"
            :result="results.stockList"
          />
          <ApiTestButton
            title="批次更新所有股票"
            endpoint="POST /stocks/update-all"
            @test="testUpdateAllStocks"
            :loading="loading.updateAllStocks"
            :result="results.updateAllStocks"
          />
        </div>
      </div>

      <!-- 歷史資料 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'data'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <ChartBarIcon class="w-5 h-5 mr-2 text-purple-500" />
          歷史資料 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ApiTestButton
            title="整體統計"
            endpoint="GET /data/history/overview"
            @test="testHistoryOverview"
            :loading="loading.historyOverview"
            :result="results.historyOverview"
          />
          <ApiTestButton
            title="有資料股票清單"
            endpoint="GET /data/history/stocks-with-data"
            @test="testStocksWithData"
            :loading="loading.stocksWithData"
            :result="results.stocksWithData"
          />
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="歷史資料"
              endpoint="GET /data/history/{symbol}"
              @test="testStockHistory"
              :loading="loading.stockHistory"
              :result="results.stockHistory"
              :disabled="!testStockSymbol"
            />
          </div>
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="股票統計"
              endpoint="GET /data/history/{symbol}/stats"
              @test="testStockStats"
              :loading="loading.stockStats"
              :result="results.stockStats"
              :disabled="!testStockSymbol"
            />
          </div>
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="最新交易日"
              endpoint="GET /data/history/{symbol}/latest-date"
              @test="testLatestTradeDate"
              :loading="loading.latestTradeDate"
              :result="results.latestTradeDate"
              :disabled="!testStockSymbol"
            />
          </div>
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="更新股票資料"
              endpoint="GET /data/daily/{symbol}"
              @test="testUpdateStockData"
              :loading="loading.updateStockData"
              :result="results.updateStockData"
              :disabled="!testStockSymbol"
            />
          </div>
        </div>
      </div>

      <!-- 任務管理 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'tasks'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Cog6ToothIcon class="w-5 h-5 mr-2 text-orange-500" />
          任務管理 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ApiTestButton
            title="執行中任務"
            endpoint="GET /task-execution/running"
            @test="testRunningTasks"
            :loading="loading.runningTasks"
            :result="results.runningTasks"
          />
          <ApiTestButton
            title="最近任務記錄"
            endpoint="GET /task-execution/recent"
            @test="testRecentTasks"
            :loading="loading.recentTasks"
            :result="results.recentTasks"
          />
          <ApiTestButton
            title="任務統計"
            endpoint="GET /task-execution/statistics"
            @test="testTaskStatistics"
            :loading="loading.taskStatistics"
            :result="results.taskStatistics"
          />
          <ApiTestButton
            title="創建爬蟲任務"
            endpoint="POST /tasks/manual/stock-crawl"
            @test="testCreateCrawlTask"
            :loading="loading.createCrawlTask"
            :result="results.createCrawlTask"
          />
          <ApiTestButton
            title="清除已完成任務"
            endpoint="POST /tasks/manual/clear-completed"
            @test="testClearCompletedTasks"
            :loading="loading.clearCompleted"
            :result="results.clearCompleted"
          />
        </div>
      </div>

      <!-- 均線計算 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'ma'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <ChartLineIcon class="w-5 h-5 mr-2 text-indigo-500" />
          均線計算 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ApiTestButton
            title="均線統計"
            endpoint="GET /moving-averages/statistics"
            @test="testMAStatistics"
            :loading="loading.maStatistics"
            :result="results.maStatistics"
          />
          <ApiTestButton
            title="驗證均線資料"
            endpoint="GET /moving-averages/validate"
            @test="testMAValidate"
            :loading="loading.maValidate"
            :result="results.maValidate"
          />
          <div class="flex items-center space-x-2">
            <input
              v-model="testStockSymbol"
              type="text"
              placeholder="股票代號"
              class="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <ApiTestButton
              title="查詢均線"
              endpoint="GET /moving-averages/query/{symbol}"
              @test="testMAQuery"
              :loading="loading.maQuery"
              :result="results.maQuery"
              :disabled="!testStockSymbol"
            />
          </div>
        </div>
      </div>

      <!-- 選股 API -->
      <div v-if="activeCategory === 'all' || activeCategory === 'selection'" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <StarIcon class="w-5 h-5 mr-2 text-yellow-500" />
          選股 API
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ApiTestButton
            title="短線多頭選股"
            endpoint="GET /stock-selection/bullish-short-term"
            @test="testBullishSelection"
            :loading="loading.bullishSelection"
            :result="results.bullishSelection"
          />
          <ApiTestButton
            title="短線空頭選股"
            endpoint="GET /stock-selection/bearish-short-term"
            @test="testBearishSelection"
            :loading="loading.bearishSelection"
            :result="results.bearishSelection"
          />
        </div>
      </div>
    </div>

    <!-- 測試結果總覽 -->
    <div v-if="Object.keys(results).length > 0" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">測試結果總覽</h3>
      <div class="space-y-2">
        <div
          v-for="(result, key) in results"
          :key="key"
          class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded"
        >
          <span class="text-sm">{{ key }}</span>
          <span :class="[
            'text-xs px-2 py-1 rounded',
            result.success ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          ]">
            {{ result.success ? '成功' : '失敗' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  PlayIcon,
  HeartIcon,
  ArrowPathIcon,
  BuildingLibraryIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ChartLineIcon,
  StarIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: 'API 整合測試中心'
})

// 使用組合式函數
const { get, post } = useApi()
const {
  getStockCount,
  syncStockList,
  crawlStockList,
  getStockList,
  updateAllStockData,
  getStockHistory,
  getStockStats,
  getLatestTradeDate,
  updateStockData,
  getOverallStats,
  getStocksWithData
} = useStocks()

const {
  getMovingAveragesStatistics,
  queryMovingAverages,
  validateMovingAverages
} = useMovingAverages()

const {
  getManualTasks,
  createStockCrawlTask,
  clearCompletedTasks
} = useTasks()

// 響應式資料
const activeCategory = ref('all')
const globalLoading = ref(false)
const testStockSymbol = ref('2330')

// 載入狀態
const loading = ref({})

// 測試結果
const results = ref({})

// 通知系統
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// API 分類
const apiCategories = computed(() => [
  { key: 'all', name: '全部', count: 30 },
  { key: 'health', name: '健康檢查', count: 4 },
  { key: 'sync', name: '股票同步', count: 4 },
  { key: 'stocks', name: '股票資料', count: 2 },
  { key: 'data', name: '歷史資料', count: 7 },
  { key: 'tasks', name: '任務管理', count: 5 },
  { key: 'ma', name: '均線計算', count: 3 },
  { key: 'selection', name: '選股', count: 2 }
])

// 顯示通知
const showNotification = (type, message, duration = 3000) => {
  notification.value = {
    show: true,
    type,
    message
  }

  setTimeout(() => {
    notification.value.show = false
  }, duration)
}

// API 測試函數
const testHealthCheck = async () => {
  loading.value.health = true
  try {
    const result = await get('/health/')
    results.value.health = { success: true, data: result }
    showNotification('success', '健康檢查 API 測試成功')
  } catch (error) {
    results.value.health = { success: false, error: error.message }
    showNotification('error', '健康檢查 API 測試失敗')
  } finally {
    loading.value.health = false
  }
}

const testDetailedHealthCheck = async () => {
  loading.value.healthDetailed = true
  try {
    const result = await get('/health/detailed')
    results.value.healthDetailed = { success: true, data: result }
    showNotification('success', '詳細健康檢查 API 測試成功')
  } catch (error) {
    results.value.healthDetailed = { success: false, error: error.message }
    showNotification('error', '詳細健康檢查 API 測試失敗')
  } finally {
    loading.value.healthDetailed = false
  }
}

const testReadinessCheck = async () => {
  loading.value.readiness = true
  try {
    const result = await get('/health/readiness')
    results.value.readiness = { success: true, data: result }
    showNotification('success', '就緒檢查 API 測試成功')
  } catch (error) {
    results.value.readiness = { success: false, error: error.message }
    showNotification('error', '就緒檢查 API 測試失敗')
  } finally {
    loading.value.readiness = false
  }
}

const testLivenessCheck = async () => {
  loading.value.liveness = true
  try {
    const result = await get('/health/liveness')
    results.value.liveness = { success: true, data: result }
    showNotification('success', '存活檢查 API 測試成功')
  } catch (error) {
    results.value.liveness = { success: false, error: error.message }
    showNotification('error', '存活檢查 API 測試失敗')
  } finally {
    loading.value.liveness = false
  }
}

const testStockCount = async () => {
  loading.value.stockCount = true
  try {
    const result = await getStockCount()
    results.value.stockCount = { success: !!result, data: result }
    showNotification('success', `股票數量統計: ${result?.total || 0} 檔`)
  } catch (error) {
    results.value.stockCount = { success: false, error: error.message }
    showNotification('error', '股票數量統計 API 測試失敗')
  } finally {
    loading.value.stockCount = false
  }
}

const testSyncStocks = async () => {
  loading.value.syncStocks = true
  try {
    const result = await syncStockList()
    results.value.syncStocks = { success: !!result, data: result }
    showNotification('success', '同步股票列表 API 測試成功')
  } catch (error) {
    results.value.syncStocks = { success: false, error: error.message }
    showNotification('error', '同步股票列表 API 測試失敗')
  } finally {
    loading.value.syncStocks = false
  }
}

const testCrawlStocks = async () => {
  loading.value.crawlStocks = true
  try {
    const result = await crawlStockList()
    results.value.crawlStocks = { success: !!result, data: result }
    showNotification('success', '爬取股票列表 API 測試成功')
  } catch (error) {
    results.value.crawlStocks = { success: false, error: error.message }
    showNotification('error', '爬取股票列表 API 測試失敗')
  } finally {
    loading.value.crawlStocks = false
  }
}

const testValidateSymbol = async () => {
  if (!testStockSymbol.value) return
  loading.value.validateSymbol = true
  try {
    const result = await get(`/sync/stocks/validate/${testStockSymbol.value}`)
    results.value.validateSymbol = { success: result.success, data: result.data }
    showNotification(result.data?.is_valid ? 'success' : 'error',
      result.data?.message || '驗證完成')
  } catch (error) {
    results.value.validateSymbol = { success: false, error: error.message }
    showNotification('error', '股票代號驗證 API 測試失敗')
  } finally {
    loading.value.validateSymbol = false
  }
}

const testStockList = async () => {
  loading.value.stockList = true
  try {
    const result = await getStockList({ limit: 10 })
    results.value.stockList = { success: !!result, data: result }
    showNotification('success', `取得股票列表: ${result?.stocks?.length || 0} 檔`)
  } catch (error) {
    results.value.stockList = { success: false, error: error.message }
    showNotification('error', '股票列表 API 測試失敗')
  } finally {
    loading.value.stockList = false
  }
}

const testUpdateAllStocks = async () => {
  loading.value.updateAllStocks = true
  try {
    const result = await updateAllStockData()
    results.value.updateAllStocks = { success: !!result, data: result }
    showNotification('success', '批次更新 API 測試成功')
  } catch (error) {
    results.value.updateAllStocks = { success: false, error: error.message }
    showNotification('error', '批次更新 API 測試失敗')
  } finally {
    loading.value.updateAllStocks = false
  }
}

const testHistoryOverview = async () => {
  loading.value.historyOverview = true
  try {
    const result = await getOverallStats()
    results.value.historyOverview = { success: !!result, data: result }
    showNotification('success', '歷史資料統計 API 測試成功')
  } catch (error) {
    results.value.historyOverview = { success: false, error: error.message }
    showNotification('error', '歷史資料統計 API 測試失敗')
  } finally {
    loading.value.historyOverview = false
  }
}

const testStocksWithData = async () => {
  loading.value.stocksWithData = true
  try {
    const result = await getStocksWithData({ limit: 10 })
    results.value.stocksWithData = { success: !!result, data: result }
    showNotification('success', `有資料股票: ${result?.stocks?.length || 0} 檔`)
  } catch (error) {
    results.value.stocksWithData = { success: false, error: error.message }
    showNotification('error', '有資料股票 API 測試失敗')
  } finally {
    loading.value.stocksWithData = false
  }
}

const testStockHistory = async () => {
  if (!testStockSymbol.value) return
  loading.value.stockHistory = true
  try {
    const result = await getStockHistory(testStockSymbol.value, { limit: 10 })
    results.value.stockHistory = { success: !!result, data: result }
    showNotification('success', `${testStockSymbol.value} 歷史資料: ${result?.data?.length || 0} 筆`)
  } catch (error) {
    results.value.stockHistory = { success: false, error: error.message }
    showNotification('error', '股票歷史資料 API 測試失敗')
  } finally {
    loading.value.stockHistory = false
  }
}

const testStockStats = async () => {
  if (!testStockSymbol.value) return
  loading.value.stockStats = true
  try {
    const result = await getStockStats(testStockSymbol.value)
    results.value.stockStats = { success: !!result, data: result }
    showNotification('success', `${testStockSymbol.value} 統計資料獲取成功`)
  } catch (error) {
    results.value.stockStats = { success: false, error: error.message }
    showNotification('error', '股票統計 API 測試失敗')
  } finally {
    loading.value.stockStats = false
  }
}

const testLatestTradeDate = async () => {
  if (!testStockSymbol.value) return
  loading.value.latestTradeDate = true
  try {
    const result = await getLatestTradeDate(testStockSymbol.value)
    results.value.latestTradeDate = { success: !!result, data: result }
    showNotification('success', `最新交易日: ${result?.latest_trade_date || '無資料'}`)
  } catch (error) {
    results.value.latestTradeDate = { success: false, error: error.message }
    showNotification('error', '最新交易日 API 測試失敗')
  } finally {
    loading.value.latestTradeDate = false
  }
}

const testUpdateStockData = async () => {
  if (!testStockSymbol.value) return
  loading.value.updateStockData = true
  try {
    const result = await updateStockData(testStockSymbol.value)
    results.value.updateStockData = { success: !!result, data: result }
    showNotification('success', `${testStockSymbol.value} 資料更新成功`)
  } catch (error) {
    results.value.updateStockData = { success: false, error: error.message }
    showNotification('error', '更新股票資料 API 測試失敗')
  } finally {
    loading.value.updateStockData = false
  }
}

const testRunningTasks = async () => {
  loading.value.runningTasks = true
  try {
    const result = await get('/task-execution/running')
    results.value.runningTasks = { success: result.success, data: result.data }
    showNotification('success', `執行中任務: ${result.data?.running_tasks?.length || 0} 個`)
  } catch (error) {
    results.value.runningTasks = { success: false, error: error.message }
    showNotification('error', '執行中任務 API 測試失敗')
  } finally {
    loading.value.runningTasks = false
  }
}

const testRecentTasks = async () => {
  loading.value.recentTasks = true
  try {
    const result = await get('/task-execution/recent')
    results.value.recentTasks = { success: result.success, data: result.data }
    showNotification('success', `最近任務: ${result.data?.tasks?.length || 0} 個`)
  } catch (error) {
    results.value.recentTasks = { success: false, error: error.message }
    showNotification('error', '最近任務 API 測試失敗')
  } finally {
    loading.value.recentTasks = false
  }
}

const testTaskStatistics = async () => {
  loading.value.taskStatistics = true
  try {
    const result = await get('/task-execution/statistics')
    results.value.taskStatistics = { success: result.success, data: result.data }
    showNotification('success', '任務統計 API 測試成功')
  } catch (error) {
    results.value.taskStatistics = { success: false, error: error.message }
    showNotification('error', '任務統計 API 測試失敗')
  } finally {
    loading.value.taskStatistics = false
  }
}

const testCreateCrawlTask = async () => {
  loading.value.createCrawlTask = true
  try {
    const result = await createStockCrawlTask(['2330', '2317'])
    results.value.createCrawlTask = { success: !!result, data: result }
    showNotification('success', '創建爬蟲任務成功')
  } catch (error) {
    results.value.createCrawlTask = { success: false, error: error.message }
    showNotification('error', '創建爬蟲任務 API 測試失敗')
  } finally {
    loading.value.createCrawlTask = false
  }
}

const testClearCompletedTasks = async () => {
  loading.value.clearCompleted = true
  try {
    const result = await clearCompletedTasks()
    results.value.clearCompleted = { success: !!result, data: result }
    showNotification('success', '清除已完成任務成功')
  } catch (error) {
    results.value.clearCompleted = { success: false, error: error.message }
    showNotification('error', '清除已完成任務 API 測試失敗')
  } finally {
    loading.value.clearCompleted = false
  }
}

const testMAStatistics = async () => {
  loading.value.maStatistics = true
  try {
    const result = await getMovingAveragesStatistics()
    results.value.maStatistics = { success: result.success, data: result.data }
    showNotification('success', '均線統計 API 測試成功')
  } catch (error) {
    results.value.maStatistics = { success: false, error: error.message }
    showNotification('error', '均線統計 API 測試失敗')
  } finally {
    loading.value.maStatistics = false
  }
}

const testMAValidate = async () => {
  loading.value.maValidate = true
  try {
    const result = await validateMovingAverages()
    results.value.maValidate = { success: result.success, data: result.data }
    showNotification('success', '均線驗證 API 測試成功')
  } catch (error) {
    results.value.maValidate = { success: false, error: error.message }
    showNotification('error', '均線驗證 API 測試失敗')
  } finally {
    loading.value.maValidate = false
  }
}

const testMAQuery = async () => {
  if (!testStockSymbol.value) return
  loading.value.maQuery = true
  try {
    const result = await queryMovingAverages(testStockSymbol.value, { limit: 10 })
    results.value.maQuery = { success: result.success, data: result.data }
    showNotification('success', `${testStockSymbol.value} 均線查詢成功`)
  } catch (error) {
    results.value.maQuery = { success: false, error: error.message }
    showNotification('error', '均線查詢 API 測試失敗')
  } finally {
    loading.value.maQuery = false
  }
}

const testBullishSelection = async () => {
  loading.value.bullishSelection = true
  try {
    const result = await get('/stock-selection/bullish-short-term')
    results.value.bullishSelection = { success: result.success, data: result.data }
    showNotification('success', `短線多頭選股: ${result.data?.stocks?.length || 0} 檔`)
  } catch (error) {
    results.value.bullishSelection = { success: false, error: error.message }
    showNotification('error', '短線多頭選股 API 測試失敗')
  } finally {
    loading.value.bullishSelection = false
  }
}

const testBearishSelection = async () => {
  loading.value.bearishSelection = true
  try {
    const result = await get('/stock-selection/bearish-short-term')
    results.value.bearishSelection = { success: result.success, data: result.data }
    showNotification('success', `短線空頭選股: ${result.data?.stocks?.length || 0} 檔`)
  } catch (error) {
    results.value.bearishSelection = { success: false, error: error.message }
    showNotification('error', '短線空頭選股 API 測試失敗')
  } finally {
    loading.value.bearishSelection = false
  }
}

// 測試所有 API
const testAllAPIs = async () => {
  globalLoading.value = true
  showNotification('info', '開始執行所有 API 測試，請稍候...', 5000)

  const tests = [
    testHealthCheck,
    testDetailedHealthCheck,
    testReadinessCheck,
    testLivenessCheck,
    testStockCount,
    testHistoryOverview,
    testStocksWithData,
    testRunningTasks,
    testRecentTasks,
    testTaskStatistics,
    testMAStatistics,
    testMAValidate,
    testBullishSelection,
    testBearishSelection
  ]

  let successCount = 0

  for (const test of tests) {
    try {
      await test()
      successCount++
      await new Promise(resolve => setTimeout(resolve, 100)) // 短暫延遲
    } catch (error) {
      console.error('Test failed:', error)
    }
  }

  globalLoading.value = false
  showNotification('success',
    `API 測試完成！成功: ${successCount}/${tests.length}`,
    5000
  )
}
</script>