<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <!-- 頁面標題 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Prometheus Metrics 監控
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Go 爬蟲服務即時效能指標監控
      </p>
    </div>

    <!-- 控制面板 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <!-- 自動刷新開關 -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              自動刷新
            </label>
            <button
              @click="toggleAutoRefresh"
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                autoRefresh ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
              ]"
            >
              <span
                :class="[
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  autoRefresh ? 'translate-x-6' : 'translate-x-1'
                ]"
              />
            </button>
          </div>

          <!-- 刷新間隔選擇 -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              刷新間隔
            </label>
            <select
              v-model="refreshInterval"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              :disabled="!autoRefresh"
            >
              <option :value="5000">5 秒</option>
              <option :value="10000">10 秒</option>
              <option :value="30000">30 秒</option>
              <option :value="60000">1 分鐘</option>
            </select>
          </div>
        </div>

        <!-- 手動刷新按鈕 -->
        <div class="flex items-center space-x-4">
          <span v-if="lastUpdate" class="text-sm text-gray-500 dark:text-gray-400">
            最後更新: {{ formatTime(lastUpdate) }}
          </span>
          <button
            @click="refreshMetrics"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium transition-colors flex items-center space-x-2"
          >
            <svg
              :class="['w-4 h-4', loading && 'animate-spin']"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{{ loading ? '載入中...' : '立即刷新' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 載入錯誤提示 -->
    <div
      v-if="error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
    >
      <div class="flex items-start">
        <svg
          class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clip-rule="evenodd"
          />
        </svg>
        <div>
          <h3 class="text-sm font-medium text-red-800 dark:text-red-300">
            載入失敗
          </h3>
          <p class="text-sm text-red-700 dark:text-red-400 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Metrics 內容 -->
    <div v-if="metricsData" class="space-y-6">
      <!-- 概覽統計卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- 總請求數 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                總請求數
              </p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                {{ getTotalRequests() }}
              </p>
            </div>
            <div class="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <svg
                class="w-6 h-6 text-blue-600 dark:text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- 成功率 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                成功率
              </p>
              <p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
                {{ getSuccessRate() }}%
              </p>
            </div>
            <div class="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <svg
                class="w-6 h-6 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- 平均響應時間 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                平均響應時間
              </p>
              <p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                {{ getAvgDuration() }}ms
              </p>
            </div>
            <div class="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <svg
                class="w-6 h-6 text-purple-600 dark:text-purple-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- 資料庫連線池 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
                資料庫連線數
              </p>
              <p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-2">
                {{ getDBConnections() }}
              </p>
            </div>
            <div class="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <svg
                class="w-6 h-6 text-orange-600 dark:text-orange-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 圖表區域 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 請求狀態分佈 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            請求狀態分佈
          </h3>
          <canvas ref="statusChartRef" height="250"></canvas>
        </div>

        <!-- 券商效能對比 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            券商效能對比
          </h3>
          <canvas ref="brokerChartRef" height="250"></canvas>
        </div>
      </div>

      <!-- HTTP 請求統計 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          HTTP 請求統計
        </h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Metric 名稱
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  標籤
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  數值
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(metric, index) in getHTTPMetrics()"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                  {{ metric.name }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="(label, idx) in parseLabels(metric.labels)"
                      :key="idx"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
                    >
                      {{ label }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-white font-mono">
                  {{ formatMetricValue(metric.value) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 資料庫 Metrics -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          資料庫效能指標
        </h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Metric 名稱
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  標籤
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  數值
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(metric, index) in getDBMetrics()"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                  {{ metric.name }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="(label, idx) in parseLabels(metric.labels)"
                      :key="idx"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                    >
                      {{ label }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-white font-mono">
                  {{ formatMetricValue(metric.value) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Go Runtime Metrics -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Go Runtime 系統資源
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="(metric, index) in getGoMetrics()"
            :key="index"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
              {{ metric.name }}
            </p>
            <p class="text-xl font-bold text-gray-900 dark:text-white">
              {{ formatMetricValue(metric.value) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 原始 Metrics 數據（可摺疊） -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <button
          @click="showRawData = !showRawData"
          class="flex items-center justify-between w-full text-left"
        >
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            原始 Metrics 數據
          </h3>
          <svg
            :class="['w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform', showRawData && 'rotate-180']"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
        <div v-if="showRawData" class="mt-4">
          <pre class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto text-sm text-gray-900 dark:text-gray-100">{{ JSON.stringify(metricsData, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <!-- 載入中狀態 -->
    <div v-else-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <svg
          class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p class="text-gray-600 dark:text-gray-400">載入 Metrics 數據中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

// 註冊 Chart.js 組件
Chart.register(...registerables)

const { getPrometheusMetrics } = useCrawlerService()

// 響應式狀態
const metricsData = ref(null)
const loading = ref(false)
const error = ref(null)
const autoRefresh = ref(true)
const refreshInterval = ref(10000) // 預設 10 秒
const lastUpdate = ref(null)
const showRawData = ref(false)

// Chart 實例和引用
const statusChartRef = ref(null)
const brokerChartRef = ref(null)
let statusChart = null
let brokerChart = null
let refreshTimer = null

// 頁面 Meta
definePageMeta({
  layout: 'default',
  title: 'Metrics 監控'
})

// 載入 Metrics 數據
const refreshMetrics = async () => {
  loading.value = true
  error.value = null

  try {
    const result = await getPrometheusMetrics()

    if (result.success) {
      metricsData.value = result.data
      lastUpdate.value = new Date()

      // 更新圖表
      await nextTick()
      updateCharts()
    } else {
      error.value = result.error || '無法載入 Metrics 數據'
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// 切換自動刷新
const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
}

// 格式化時間
const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

// 格式化數值
const formatMetricValue = (value) => {
  if (typeof value === 'number') {
    if (value < 1 && value > 0) {
      return value.toFixed(6)
    }
    if (value > 1000000) {
      return (value / 1000000).toFixed(2) + 'M'
    }
    if (value > 1000) {
      return (value / 1000).toFixed(2) + 'K'
    }
    return value.toFixed(2)
  }
  return value
}

// 解析標籤字串
const parseLabels = (labelsStr) => {
  if (!labelsStr) return []
  return labelsStr.split(',').map(l => l.trim()).filter(l => l)
}

// 獲取總請求數
const getTotalRequests = () => {
  if (!metricsData.value?.crawler_requests_total) return 0

  const total = metricsData.value.crawler_requests_total.reduce(
    (sum, item) => sum + (parseFloat(item.value) || 0),
    0
  )
  return Math.round(total)
}

// 獲取成功率
const getSuccessRate = () => {
  if (!metricsData.value?.crawler_requests_total) return 0

  let success = 0
  let total = 0

  metricsData.value.crawler_requests_total.forEach(item => {
    const value = parseFloat(item.value) || 0
    total += value

    if (item.labels.includes('status="success"')) {
      success += value
    }
  })

  return total > 0 ? ((success / total) * 100).toFixed(2) : 0
}

// 獲取平均響應時間
const getAvgDuration = () => {
  if (!metricsData.value?.crawler_request_duration_seconds) return 0

  const durations = metricsData.value.crawler_request_duration_seconds
  if (!durations || durations.length === 0) return 0

  const sum = durations.reduce((acc, item) => acc + (parseFloat(item.value) || 0), 0)
  const avg = sum / durations.length

  return (avg * 1000).toFixed(2) // 轉換為毫秒
}

// 獲取資料庫連線數
const getDBConnections = () => {
  if (!metricsData.value?.db_connection_pool_size) return 0

  const poolMetrics = metricsData.value.db_connection_pool_size
  if (!poolMetrics || poolMetrics.length === 0) return 0

  return Math.round(parseFloat(poolMetrics[0].value) || 0)
}

// 獲取 HTTP 相關 Metrics
const getHTTPMetrics = () => {
  if (!metricsData.value) return []

  const httpMetrics = []
  const httpPrefixes = ['crawler_requests', 'crawler_fetch', 'http_']

  Object.keys(metricsData.value).forEach(key => {
    if (httpPrefixes.some(prefix => key.startsWith(prefix))) {
      metricsData.value[key].forEach(item => {
        httpMetrics.push({
          name: key,
          labels: item.labels,
          value: item.value
        })
      })
    }
  })

  return httpMetrics
}

// 獲取資料庫相關 Metrics
const getDBMetrics = () => {
  if (!metricsData.value) return []

  const dbMetrics = []
  const dbPrefixes = ['db_']

  Object.keys(metricsData.value).forEach(key => {
    if (dbPrefixes.some(prefix => key.startsWith(prefix))) {
      metricsData.value[key].forEach(item => {
        dbMetrics.push({
          name: key,
          labels: item.labels,
          value: item.value
        })
      })
    }
  })

  return dbMetrics
}

// 獲取 Go Runtime Metrics
const getGoMetrics = () => {
  if (!metricsData.value) return []

  const goMetrics = []
  const goPrefixes = ['go_', 'process_']

  Object.keys(metricsData.value).forEach(key => {
    if (goPrefixes.some(prefix => key.startsWith(prefix))) {
      const items = metricsData.value[key]
      if (items && items.length > 0) {
        goMetrics.push({
          name: key.replace(/_/g, ' '),
          value: items[0].value
        })
      }
    }
  })

  return goMetrics.slice(0, 12) // 限制顯示數量
}

// 更新圖表
const updateCharts = () => {
  if (!metricsData.value) return

  // 更新請求狀態分佈圖
  updateStatusChart()

  // 更新券商效能對比圖
  updateBrokerChart()
}

// 更新請求狀態分佈圖
const updateStatusChart = () => {
  if (!statusChartRef.value) return

  const ctx = statusChartRef.value.getContext('2d')

  // 銷毀舊圖表
  if (statusChart) {
    statusChart.destroy()
  }

  // 準備數據
  let successCount = 0
  let failureCount = 0

  if (metricsData.value?.crawler_requests_total) {
    metricsData.value.crawler_requests_total.forEach(item => {
      const value = parseFloat(item.value) || 0
      if (item.labels.includes('status="success"')) {
        successCount += value
      } else if (item.labels.includes('status="failure"')) {
        failureCount += value
      }
    })
  }

  // 創建新圖表
  statusChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['成功', '失敗'],
      datasets: [
        {
          data: [successCount, failureCount],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',  // green
            'rgba(239, 68, 68, 0.8)'   // red
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(239, 68, 68, 1)'
          ],
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
          }
        },
        title: {
          display: false
        }
      }
    }
  })
}

// 更新券商效能對比圖
const updateBrokerChart = () => {
  if (!brokerChartRef.value) return

  const ctx = brokerChartRef.value.getContext('2d')

  // 銷毀舊圖表
  if (brokerChart) {
    brokerChart.destroy()
  }

  // 準備數據
  const brokerData = {}

  if (metricsData.value?.crawler_fetch_requests_total) {
    metricsData.value.crawler_fetch_requests_total.forEach(item => {
      const brokerMatch = item.labels.match(/broker="([^"]+)"/)
      if (brokerMatch) {
        const broker = brokerMatch[1]
        const value = parseFloat(item.value) || 0

        if (!brokerData[broker]) {
          brokerData[broker] = 0
        }
        brokerData[broker] += value
      }
    })
  }

  const brokers = Object.keys(brokerData)
  const values = Object.values(brokerData)

  // 創建新圖表
  brokerChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: brokers,
      datasets: [
        {
          label: '請求次數',
          data: values,
          backgroundColor: 'rgba(59, 130, 246, 0.8)', // blue
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
          },
          grid: {
            color: document.documentElement.classList.contains('dark') ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 0.5)'
          }
        },
        x: {
          ticks: {
            color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
          },
          grid: {
            display: false
          }
        }
      }
    }
  })
}

// 監聽自動刷新設置
watch([autoRefresh, refreshInterval], () => {
  // 清除舊的定時器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }

  // 如果啟用自動刷新，設置新的定時器
  if (autoRefresh.value) {
    refreshTimer = setInterval(() => {
      refreshMetrics()
    }, refreshInterval.value)
  }
})

// 組件掛載時
onMounted(() => {
  // 初始載入
  refreshMetrics()
})

// 組件卸載時
onUnmounted(() => {
  // 清除定時器
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }

  // 銷毀圖表
  if (statusChart) {
    statusChart.destroy()
  }
  if (brokerChart) {
    brokerChart.destroy()
  }
})
</script>

<style scoped>
/* 自定義樣式可以在這裡添加 */
</style>
