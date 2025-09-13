<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
    <div class="container mx-auto px-4 py-8">
      <!-- 標題區域 with Gradient Background -->
      <div class="mb-8 relative">
        <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl blur-3xl opacity-20"></div>
        <div class="relative bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-gray-200 dark:border-gray-700">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                智能選股中心
              </h1>
              <p class="text-gray-600 dark:text-gray-400 text-lg">
                基於均線排列的智能選股策略分析
              </p>
            </div>
            <div class="flex items-center gap-3">
              <div class="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full text-white text-sm font-semibold shadow-lg">
                <Icon name="mdi:lightning-bolt" class="mr-1" />
                即時分析
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 日期選擇區域 with Modern Design -->
      <div class="mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all duration-300">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-6">
              <!-- 日期選擇器 -->
              <div class="flex items-center gap-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl px-4 py-3">
                <div class="p-2 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg">
                  <Icon name="mdi:calendar" class="text-xl text-white" />
                </div>
                <div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">選股日期</div>
                  <input
                    v-model="selectedDate"
                    type="date"
                    :max="maxDate"
                    class="bg-transparent text-gray-900 dark:text-white font-semibold focus:outline-none cursor-pointer"
                    @change="handleDateChange"
                  />
                </div>
              </div>

              <!-- 最新交易日顯示 -->
              <div class="flex items-center gap-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl px-4 py-3">
                <div class="p-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg">
                  <Icon name="mdi:trending-up" class="text-xl text-white" />
                </div>
                <div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">最新交易日</div>
                  <div class="text-gray-900 dark:text-white font-semibold">
                    {{ latestTradingDate || '載入中...' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 重新整理按鈕 -->
            <button
              @click="refreshResults"
              class="group relative px-6 py-3 font-semibold text-white rounded-xl overflow-hidden transition-all duration-300 hover:scale-105"
              :disabled="loading"
            >
              <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 group-hover:from-blue-600 group-hover:to-purple-700 transition-all duration-300"></div>
              <div class="relative flex items-center gap-2">
                <Icon name="mdi:refresh" class="text-xl" :class="{ 'animate-spin': loading }" />
                <span>重新整理</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading 狀態 with Modern Animation -->
      <div v-if="loading" class="flex flex-col justify-center items-center h-64">
        <div class="relative">
          <div class="w-24 h-24 rounded-full border-4 border-gray-200 dark:border-gray-700"></div>
          <div class="absolute top-0 w-24 h-24 rounded-full border-4 border-transparent border-t-blue-500 animate-spin"></div>
        </div>
        <p class="mt-4 text-gray-600 dark:text-gray-400 font-semibold">載入選股資料中...</p>
      </div>

      <!-- 錯誤訊息 with Modern Style -->
      <div v-else-if="error" class="mb-6">
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 shadow-lg">
          <div class="flex items-center gap-3">
            <div class="p-3 bg-red-100 dark:bg-red-900/50 rounded-full">
              <Icon name="mdi:alert-circle" class="text-2xl text-red-600 dark:text-red-400" />
            </div>
            <span class="text-red-700 dark:text-red-300 font-medium">{{ error }}</span>
          </div>
        </div>
      </div>

      <!-- 選股結果 -->
      <div v-else-if="selectionResults">
        <!-- 統計總覽 with Modern Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- 完美多頭卡片 -->
          <div class="group relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-400 to-green-600 rounded-2xl transform rotate-1 group-hover:rotate-2 transition-transform duration-300"></div>
            <div class="relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-emerald-400 to-green-600 rounded-xl shadow-lg">
                  <Icon name="mdi:rocket-launch" class="text-2xl text-white" />
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ selectionResults.strategies?.perfect_bull?.count || 0 }}
                </div>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">完美多頭</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">MA5>MA10>MA20>MA60>MA120>MA240</p>
            </div>
          </div>

          <!-- 短線多頭卡片 -->
          <div class="group relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-blue-400 to-cyan-600 rounded-2xl transform rotate-1 group-hover:rotate-2 transition-transform duration-300"></div>
            <div class="relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-blue-400 to-cyan-600 rounded-xl shadow-lg">
                  <Icon name="mdi:trending-up" class="text-2xl text-white" />
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ selectionResults.strategies?.short_bull?.count || 0 }}
                </div>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">短線多頭</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">MA5>MA10>MA20</p>
            </div>
          </div>

          <!-- 空頭趨勢卡片 -->
          <div class="group relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-red-400 to-pink-600 rounded-2xl transform rotate-1 group-hover:rotate-2 transition-transform duration-300"></div>
            <div class="relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-red-400 to-pink-600 rounded-xl shadow-lg">
                  <Icon name="mdi:trending-down" class="text-2xl text-white" />
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ selectionResults.strategies?.bear?.count || 0 }}
                </div>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">空頭趨勢</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">MA5&lt;MA10&lt;MA20&lt;MA60</p>
            </div>
          </div>

          <!-- 選中比例卡片 -->
          <div class="group relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-purple-400 to-indigo-600 rounded-2xl transform rotate-1 group-hover:rotate-2 transition-transform duration-300"></div>
            <div class="relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-purple-400 to-indigo-600 rounded-xl shadow-lg">
                  <Icon name="mdi:percent" class="text-2xl text-white" />
                </div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ selectionResults.summary?.selection_rate || 0 }}%
                </div>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">選中比例</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                共 {{ selectionResults.summary?.total_stocks_with_ma || 0 }} 檔股票
              </p>
            </div>
          </div>
        </div>

        <!-- Tab 切換 with Modern Design -->
        <div class="mb-8">
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-2 shadow-xl border border-gray-200 dark:border-gray-700">
            <div class="flex gap-2">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                @click="activeTab = tab.key"
                :class="[
                  'flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all duration-300',
                  activeTab === tab.key
                    ? 'bg-gradient-to-r text-white shadow-lg transform scale-105'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                ]"
                :style="activeTab === tab.key ? getTabGradient(tab.key) : ''"
              >
                <Icon :name="tab.icon" class="text-xl" />
                <span>{{ tab.label }}</span>
                <span
                  :class="[
                    'px-2 py-1 rounded-lg text-xs font-bold',
                    activeTab === tab.key
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                  ]"
                >
                  {{ getTabCount(tab.key) }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- 股票列表 with Modern Table -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <!-- 策略說明 -->
          <div v-if="getCurrentStrategy()" class="p-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3 mb-3">
              <div class="p-2 rounded-lg" :style="getStrategyIconBg(activeTab)">
                <Icon :name="getStrategyIcon(activeTab)" class="text-xl text-white" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ getCurrentStrategy().name }}
              </h3>
            </div>
            <p class="text-gray-600 dark:text-gray-400 mb-2">
              {{ getCurrentStrategy().description }}
            </p>
            <div class="inline-flex items-center gap-2 px-3 py-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
              <Icon name="mdi:information" class="text-blue-500" />
              <span class="text-sm text-gray-600 dark:text-gray-400 font-mono">
                {{ getCurrentStrategy().condition }}
              </span>
            </div>
          </div>

          <!-- 股票表格 -->
          <div v-if="getCurrentStocks().length > 0" class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">排名</th>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">股票代號</th>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">股票名稱</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">收盤價</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">漲跌幅%</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">成交量</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA5</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA10</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA20</th>
                  <th v-if="activeTab !== 'short_bull'" class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA60</th>
                  <th v-if="activeTab === 'perfect_bull'" class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA120</th>
                  <th v-if="activeTab === 'perfect_bull'" class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">MA240</th>
                  <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">5日乖離率</th>
                  <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 dark:text-gray-300">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="(stock, index) in getCurrentStocks()"
                  :key="stock.stock_code"
                  class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-200"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-bold">
                      {{ index + 1 }}
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <span class="font-mono font-bold text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {{ stock.stock_code }}
                    </span>
                  </td>
                  <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{{ stock.stock_name }}</td>
                  <td class="px-4 py-3 text-right font-semibold text-gray-900 dark:text-white">
                    {{ formatNumber(stock.close_price) }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <span
                      :class="[
                        'inline-flex items-center px-2 py-1 rounded-lg font-bold text-sm',
                        stock.price_change > 0
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                          : stock.price_change < 0
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      ]"
                    >
                      <Icon
                        :name="stock.price_change > 0 ? 'mdi:arrow-up' : stock.price_change < 0 ? 'mdi:arrow-down' : 'mdi:minus'"
                        class="mr-1"
                      />
                      {{ formatPercent(stock.price_change) }}%
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatVolume(stock.volume) }}</td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatNumber(stock.ma_5) }}</td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatNumber(stock.ma_10) }}</td>
                  <td class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{{ formatNumber(stock.ma_20) }}</td>
                  <td v-if="activeTab !== 'short_bull'" class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                    {{ formatNumber(stock.ma_60) }}
                  </td>
                  <td v-if="activeTab === 'perfect_bull'" class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                    {{ formatNumber(stock.ma_120) }}
                  </td>
                  <td v-if="activeTab === 'perfect_bull'" class="px-4 py-3 text-right text-gray-700 dark:text-gray-300">
                    {{ formatNumber(stock.ma_240) }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <span
                      :class="[
                        'font-semibold',
                        stock.ma_bias > 5
                          ? 'text-red-600 dark:text-red-400'
                          : stock.ma_bias < -5
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-gray-600 dark:text-gray-400'
                      ]"
                    >
                      {{ stock.ma_bias }}%
                    </span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <button
                      @click="viewStockDetail(stock.stock_code)"
                      class="group p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300 hover:scale-110 shadow-lg"
                      title="查看詳情"
                    >
                      <Icon name="mdi:chart-line" class="text-lg text-white" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 無資料提示 -->
          <div v-else class="p-16 text-center">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-700 mb-4">
              <Icon name="mdi:database-off" class="text-4xl text-gray-400" />
            </div>
            <p class="text-gray-500 dark:text-gray-400 text-lg font-medium">
              目前沒有符合{{ getCurrentStrategy()?.name }}條件的股票
            </p>
            <p class="text-gray-400 dark:text-gray-500 text-sm mt-2">
              請嘗試選擇其他日期或策略
            </p>
          </div>
        </div>
      </div>

      <!-- 初始載入提示 with Modern Design -->
      <div v-else class="flex flex-col items-center justify-center py-20">
        <div class="relative mb-8">
          <div class="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full blur-2xl opacity-30 animate-pulse"></div>
          <div class="relative bg-white dark:bg-gray-800 p-8 rounded-full shadow-2xl">
            <Icon name="mdi:database-search" class="text-6xl text-gray-400" />
          </div>
        </div>
        <h3 class="text-2xl font-bold text-gray-700 dark:text-gray-300 mb-2">選股系統就緒</h3>
        <p class="text-gray-500 dark:text-gray-400">請選擇日期開始智能選股分析</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

// 狀態管理
const loading = ref(false)
const error = ref(null)
const selectedDate = ref('')
const latestTradingDate = ref('')
const selectionResults = ref(null)
const activeTab = ref('perfect_bull')

// Tab 配置
const tabs = [
  {
    key: 'perfect_bull',
    label: '完美多頭',
    icon: 'mdi:rocket-launch',
    badgeClass: 'badge-primary'
  },
  {
    key: 'short_bull',
    label: '短線多頭',
    icon: 'mdi:trending-up',
    badgeClass: 'badge-info'
  },
  {
    key: 'bear',
    label: '空頭趨勢',
    icon: 'mdi:trending-down',
    badgeClass: 'badge-error'
  }
]

// 計算屬性
const maxDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

// 獲取Tab漸變色
const getTabGradient = (tabKey) => {
  const gradients = {
    perfect_bull: 'background: linear-gradient(135deg, #10b981, #059669)',
    short_bull: 'background: linear-gradient(135deg, #3b82f6, #06b6d4)',
    bear: 'background: linear-gradient(135deg, #ef4444, #ec4899)'
  }
  return gradients[tabKey]
}

// 獲取策略圖標背景
const getStrategyIconBg = (tabKey) => {
  const backgrounds = {
    perfect_bull: 'background: linear-gradient(135deg, #10b981, #059669)',
    short_bull: 'background: linear-gradient(135deg, #3b82f6, #06b6d4)',
    bear: 'background: linear-gradient(135deg, #ef4444, #ec4899)'
  }
  return backgrounds[tabKey]
}

// 獲取策略圖標
const getStrategyIcon = (tabKey) => {
  const icons = {
    perfect_bull: 'mdi:rocket-launch',
    short_bull: 'mdi:trending-up',
    bear: 'mdi:trending-down'
  }
  return icons[tabKey]
}

// 獲取最新交易日期
const fetchLatestTradingDate = async () => {
  try {
    const response = await $fetch('/api/v1/stock-selection/latest-date', {
      baseURL: 'http://localhost:9127'
    })

    if (response.status === 'success' && response.data?.latest_date) {
      latestTradingDate.value = response.data.latest_date
      selectedDate.value = response.data.latest_date
      return response.data.latest_date
    }
  } catch (err) {
    console.error('獲取最新交易日期失敗:', err)
    error.value = '無法獲取最新交易日期'
  }
  return null
}

// 獲取選股結果
const fetchSelectionResults = async (date = null) => {
  loading.value = true
  error.value = null

  try {
    const params = {}
    if (date) {
      params.selection_date = date
    }

    const response = await $fetch('/api/v1/stock-selection/results', {
      baseURL: 'http://localhost:9127',
      params
    })

    if (response.status === 'success') {
      selectionResults.value = response.data
      console.log('選股結果:', selectionResults.value)
    } else {
      throw new Error(response.message || '獲取選股結果失敗')
    }
  } catch (err) {
    console.error('獲取選股結果失敗:', err)
    error.value = err.message || '無法獲取選股結果'
    selectionResults.value = null
  } finally {
    loading.value = false
  }
}

// 處理日期變更
const handleDateChange = () => {
  if (selectedDate.value) {
    fetchSelectionResults(selectedDate.value)
  }
}

// 重新整理結果
const refreshResults = async () => {
  await fetchSelectionResults(selectedDate.value || null)
}

// 獲取當前策略
const getCurrentStrategy = () => {
  if (!selectionResults.value?.strategies) return null
  return selectionResults.value.strategies[activeTab.value]
}

// 獲取當前股票列表
const getCurrentStocks = () => {
  const strategy = getCurrentStrategy()
  return strategy?.stocks || []
}

// 獲取 Tab 計數
const getTabCount = (tabKey) => {
  if (!selectionResults.value?.strategies) return 0
  return selectionResults.value.strategies[tabKey]?.count || 0
}

// 查看股票詳情
const viewStockDetail = (stockCode) => {
  window.open(`/market-data/historical?stock_code=${stockCode}`, '_blank')
}

// 格式化函數
const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toFixed(2)
}

const formatPercent = (num) => {
  if (num === null || num === undefined) return '0.00'
  return Math.abs(num).toFixed(2)
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '億'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(0) + '萬'
  }
  return volume.toLocaleString()
}

// 生命週期
onMounted(async () => {
  const date = await fetchLatestTradingDate()
  if (date) {
    await fetchSelectionResults(date)
  }
})
</script>

<style scoped>
/* 自定義滾動條 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-800 rounded-full;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-400 dark:bg-gray-600 rounded-full hover:bg-gray-500 dark:hover:bg-gray-500;
}

/* 動畫效果 */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

/* 表格行懸停效果 */
tbody tr {
  position: relative;
  transition: all 0.3s ease;
}

tbody tr::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.05), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

tbody tr:hover::before {
  opacity: 1;
}
</style>