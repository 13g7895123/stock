<template>
  <div class="space-y-6">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">股本比分析</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">投信外資買賣超股本比累積排名與趨勢分析</p>
        </div>
        <div class="flex items-center space-x-3">
            <button
              @click="loadData"
              :disabled="isLoading"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              重新載入
            </button>
            <!-- 資料爬取按鈕 -->
            <button
              v-if="shouldShowCrawlButton"
              @click="executeCrawl"
              :disabled="isCrawling"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              <svg v-if="isCrawling" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
              </svg>
              執行資料爬取
            </button>
        </div>
      </div>
    </div>

    <!-- 資料不足提示 -->
    <div v-if="!isDataSufficient && !isLoading" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
            資料不足提示
          </h3>
          <div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
            <p>
              系統資料較少（共 {{ buyRankings.length + sellRankings.length }} 筆排名資料），建議執行資料爬取以獲取更完整的分析結果。
            </p>
          </div>
          <div class="mt-4">
            <div class="-mx-2 -my-1.5 flex">
              <button
                @click="executeCrawl"
                :disabled="isCrawling"
                class="bg-yellow-50 dark:bg-yellow-900/50 px-2 py-1.5 rounded-md text-sm font-medium text-yellow-800 dark:text-yellow-200 hover:bg-yellow-100 dark:hover:bg-yellow-900/70 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-yellow-50 focus:ring-yellow-600 disabled:opacity-50"
              >
                {{ isCrawling ? '爬取中...' : '立即爬取資料' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 時間範圍選擇 -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div class="flex space-x-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">分析期間</label>
          <select v-model="selectedPeriod" @change="loadData" class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
            <option value="7">近一週</option>
            <option value="30">近一個月</option>
            <option value="60">近兩個月</option>
            <option value="90">近三個月</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">顯示筆數</label>
          <select v-model="displayLimit" @change="loadData" class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
            <option value="20">前20名</option>
            <option value="50">前50名</option>
            <option value="100">前100名</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 買超股本比排名 -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
      <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          買超股本比排名 
          <span class="text-sm text-gray-500 dark:text-gray-400">({{ periodText }})</span>
        </h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          三大法人買超金額占股本比例排名（正值表示買超）
        </p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">排名</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票代號</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票名稱</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">累積買賣超</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">股本比 (%)</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">交易天數</th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="stock in buyRankings" :key="stock.stock_code" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {{ stock.rank }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                {{ stock.stock_code }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                {{ stock.stock_name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span class="text-green-600 font-medium">
                  +{{ formatNumber(stock.total_cumulative) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span class="text-green-600 font-medium">
                  +{{ stock.capital_ratio?.toFixed(4) || 'N/A' }}%
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                {{ stock.trading_days }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 賣超股本比排名 -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
      <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          賣超股本比排名 
          <span class="text-sm text-gray-500 dark:text-gray-400">({{ periodText }})</span>
        </h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          三大法人賣超金額占股本比例排名（負值表示賣超）
        </p>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">排名</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票代號</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票名稱</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">累積買賣超</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">股本比 (%)</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">交易天數</th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="stock in sellRankings" :key="stock.stock_code" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {{ stock.rank }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                {{ stock.stock_code }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                {{ stock.stock_name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span class="text-red-600 font-medium">
                  {{ formatNumber(stock.total_cumulative) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                <span class="text-red-600 font-medium">
                  {{ stock.capital_ratio?.toFixed(4) || 'N/A' }}%
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                {{ stock.trading_days }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 股本比趨勢圖表 -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
      <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          每日股本比累積趨勢
          <span class="text-sm text-gray-500 dark:text-gray-400">({{ periodText }})</span>
        </h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          顯示前{{ chartStockLimit }}檔股票的每日股本比累積變化
        </p>
      </div>
      <div class="p-6">
        <div v-if="trendsData.length > 0" class="h-96">
          <canvas ref="chartCanvas" width="800" height="400"></canvas>
        </div>
        <div v-else class="flex items-center justify-center h-96 text-gray-500">
          <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">暫無趨勢資料</h3>
            <p class="mt-1 text-sm text-gray-500">請確保已有足夠的歷史資料</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知 -->
    <div
      v-if="notification.show"
      class="fixed top-4 right-4 max-w-sm w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black dark:ring-gray-600 ring-opacity-5 overflow-hidden z-50"
      :class="{
        'border-l-4 border-green-400': notification.type === 'success',
        'border-l-4 border-red-400': notification.type === 'error',
        'border-l-4 border-blue-400': notification.type === 'info'
      }"
    >
      <div class="p-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <svg v-if="notification.type === 'success'" class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="notification.type === 'error'" class="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="ml-3 w-0 flex-1 pt-0.5">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ notification.title }}</p>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ notification.message }}</p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button @click="notification.show = false" class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'

// SEO 設定
useSeoMeta({
  title: '股本比分析 - 投信外資買賣超分析系統',
  description: '投信外資買賣超股本比累積排名與趨勢分析'
})

// 響應式狀態
const isLoading = ref(false)
const selectedPeriod = ref(30)
const displayLimit = ref(50)
const chartStockLimit = ref(10)

const buyRankings = ref([])
const sellRankings = ref([])
const trendsData = ref([])
const chartDates = ref([])

// 通知狀態
const notification = ref({
  show: false,
  type: 'info',
  title: '',
  message: ''
})

// 計算屬性
const periodText = computed(() => {
  const period = selectedPeriod.value
  if (period === 7) return '近一週'
  if (period === 30) return '近一個月'
  if (period === 60) return '近兩個月'
  if (period === 90) return '近三個月'
  return `近${period}天`
})

// Chart.js 相關
const chartCanvas = ref(null)
let chartInstance = null

// API 功能
const { $api } = useNuxtApp()

// 載入股本比排名資料
const loadRankings = async () => {
  try {
    const response = await $api(`/institutional-trading/capital-ratio/rankings?days_back=${selectedPeriod.value}&limit=${displayLimit.value}`)
    
    if (response.status === 'success') {
      buyRankings.value = response.data.buy_rankings || []
      sellRankings.value = response.data.sell_rankings || []
    }
  } catch (error) {
    console.error('載入排名資料失敗:', error)
    showNotification('載入排名資料失敗', 'error')
  }
}

// 載入趨勢資料
const loadTrends = async () => {
  try {
    const response = await $api(`/institutional-trading/capital-ratio/trends?days_back=${selectedPeriod.value}&top_stocks=${chartStockLimit.value}`)
    
    if (response.status === 'success') {
      trendsData.value = response.data.trends || []
      chartDates.value = response.data.dates || []
      
      // 更新圖表
      await nextTick()
      updateChart()
    }
  } catch (error) {
    console.error('載入趨勢資料失敗:', error)
    showNotification('載入趨勢資料失敗', 'error')
  }
}

// 資料不足檢查
const isDataSufficient = computed(() => {
  return (buyRankings.value.length + sellRankings.value.length) >= 10
})

const shouldShowCrawlButton = computed(() => {
  return !isLoading.value && !isDataSufficient.value
})

// 載入所有資料
const loadData = async () => {
  isLoading.value = true
  try {
    await Promise.all([
      loadRankings(),
      loadTrends()
    ])

    // 檢查資料是否充足
    if (isDataSufficient.value) {
      showNotification('資料載入完成', 'success')
    } else {
      showNotification('資料不足，建議執行資料爬取以獲取更多資料', 'info')
    }
  } catch (error) {
    console.error('載入資料失敗:', error)
    showNotification('載入資料失敗', 'error')
  } finally {
    isLoading.value = false
  }
}

// 執行資料爬取
const isCrawling = ref(false)
const executeCrawl = async () => {
  if (isCrawling.value) return

  isCrawling.value = true
  try {
    showNotification('開始爬取投信外資買賣超資料...', 'info')

    // 調用後端批次更新API
    const response = await $api(`/institutional-trading/update/batch?days_back=${selectedPeriod.value}`, {
      method: 'POST'
    })

    if (response.status === 'success') {
      showNotification(`爬取完成！新增 ${response.data.records_added || 0} 筆資料`, 'success')
      // 重新載入資料
      await loadData()
    } else {
      throw new Error(response.message || '爬取失敗')
    }
  } catch (error) {
    console.error('爬取資料失敗:', error)
    showNotification('爬取資料失敗: ' + error.message, 'error')
  } finally {
    isCrawling.value = false
  }
}

// 更新圖表
const updateChart = async () => {
  if (!chartCanvas.value || trendsData.value.length === 0) return

  try {
    // 動態導入 Chart.js
    const { Chart, registerables } = await import('chart.js')
    Chart.register(...registerables)

    // 銷毀舊圖表
    if (chartInstance) {
      try {
        chartInstance.destroy()
      } catch (error) {
        console.warn('銷毀舊圖表時發生錯誤:', error)
      }
    }

    // 驗證必要的資料
    if (!trendsData.value || trendsData.value.length === 0) {
      console.warn('趨勢資料為空，無法建立圖表')
      return
    }

    if (!chartDates.value || chartDates.value.length === 0) {
      console.warn('圖表日期為空，無法建立圖表')
      return
    }

    // 準備圖表資料
    const datasets = trendsData.value.map((stockData, index) => {
      const colors = [
        '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
        '#F97316', '#06B6D4', '#84CC16', '#EC4899', '#6366F1'
      ]
      const color = colors[index % colors.length]

      return {
        label: `${stockData.stock_code || 'N/A'} ${stockData.stock_name || ''}`,
        data: chartDates.value.map(date => {
          try {
            const cumulativeData = stockData.cumulative_data?.[date]
            return cumulativeData ? (cumulativeData.cumulative_ratio || 0) : null
          } catch (error) {
            console.warn(`處理日期 ${date} 的資料時發生錯誤:`, error)
            return null
          }
        }),
        borderColor: color,
        backgroundColor: color + '20',
        fill: false,
        tension: 0.1
      }
    })

    // 建立圖表
    chartInstance = new Chart(chartCanvas.value, {
      type: 'line',
      data: {
        labels: chartDates.value.map(date => {
          try {
            return date ? date.slice(5) : '' // 只顯示月-日
          } catch (error) {
            console.warn(`處理日期標籤時發生錯誤:`, error)
            return ''
          }
        }),
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: '股本比累積趨勢 (%)'
          },
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '日期'
            }
          },
          y: {
            title: {
              display: true,
              text: '股本比 (%)'
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    })

    console.log('圖表建立成功')
  } catch (error) {
    console.error('建立圖表時發生錯誤:', error)
    showNotification('圖表載入失敗，但不影響其他功能使用', 'error')
    // 不重新拋出錯誤，避免中斷整個頁面載入
  }
}

// 格式化數字
const formatNumber = (num) => {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 顯示通知
const showNotification = (message, type = 'info', title = '') => {
  notification.value = {
    show: true,
    type,
    title: title || (type === 'success' ? '成功' : type === 'error' ? '錯誤' : '提示'),
    message
  }
  
  // 自動隱藏通知
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

// 組件掛載
onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* 表格樣式 */
.table-container {
  max-height: 600px;
  overflow-y: auto;
}

/* 響應式表格 */
@media (max-width: 768px) {
  .table-container {
    font-size: 0.875rem;
  }
}
</style>
