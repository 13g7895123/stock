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
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">股票歷史資料查詢</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">查詢特定股票的歷史價格和交易資料</p>
        </div>
      </div>
    </div>

    <!-- 查詢條件 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">查詢條件</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 股票代碼 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">股票代碼</label>
          <input
            v-model="queryParams.symbol"
            type="text"
            placeholder="如: 2330"
            maxlength="4"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <!-- 開始日期 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">開始日期</label>
          <input
            v-model="queryParams.start_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <!-- 結束日期 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">結束日期</label>
          <input
            v-model="queryParams.end_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <!-- 查詢按鈕 -->
        <div class="flex items-end">
          <button 
            @click="handleQueryHistory"
            :disabled="!queryParams.symbol || loading"
            class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
          >
            <MagnifyingGlassIcon :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
            <span>{{ loading ? '查詢中...' : '查詢歷史資料' }}</span>
          </button>
        </div>
      </div>

      <!-- 其他查詢選項 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <!-- 排序方式 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">排序方式</label>
          <select
            v-model="queryParams.sort_by"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="trade_date">交易日期</option>
            <option value="close_price">收盤價</option>
            <option value="volume">成交量</option>
          </select>
        </div>

        <!-- 排序順序 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">排序順序</label>
          <select
            v-model="queryParams.sort_order"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="desc">由新到舊</option>
            <option value="asc">由舊到新</option>
          </select>
        </div>

        <!-- 每頁筆數 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">每頁筆數</label>
          <select
            v-model="queryParams.limit"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="10">10 筆</option>
            <option value="20">20 筆</option>
            <option value="50">50 筆</option>
            <option value="100">100 筆</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">快速操作</h3>
      <div class="flex flex-wrap gap-3">
        <button 
          @click="handleGetStats"
          :disabled="!queryParams.symbol || loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
        >
          <ChartBarIcon class="w-4 h-4" />
          <span>查看統計資訊</span>
        </button>
        <button 
          @click="handleGetLatestDate"
          :disabled="!queryParams.symbol || loading"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
        >
          <CalendarIcon class="w-4 h-4" />
          <span>最新交易日</span>
        </button>
      </div>
    </div>

    <!-- 統計資訊區域 -->
    <div v-if="stats" class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">統計資訊</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div class="text-sm text-gray-500 dark:text-gray-400">總筆數</div>
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_records }}</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg" v-if="stats.date_range">
          <div class="text-sm text-gray-500 dark:text-gray-400">日期範圍</div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            {{ stats.date_range.start_date }} ~ {{ stats.date_range.end_date }}
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg" v-if="stats.price_range">
          <div class="text-sm text-gray-500 dark:text-gray-400">價格範圍</div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            ${{ stats.price_range.min_price }} ~ ${{ stats.price_range.max_price }}
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg" v-if="latestDate">
          <div class="text-sm text-gray-500 dark:text-gray-400">最新交易日</div>
          <div class="text-lg font-bold text-gray-900 dark:text-white">{{ latestDate }}</div>
        </div>
      </div>
    </div>

    <!-- 歷史資料表格 -->
    <div v-if="historyData.length > 0" class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <!-- 表格標題 -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ queryParams.symbol }} 歷史資料 ({{ pagination.total_records }} 筆)
          </h3>
          <div class="flex items-center space-x-2">
            <button 
              @click="exportData"
              class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="匯出資料"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- 表格內容 -->
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                交易日期
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                開盤價
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                最高價
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                最低價
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                收盤價
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                成交量
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                漲跌幅
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="record in historyData"
              :key="record.trade_date"
              class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatDate(record.trade_date) }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-900 dark:text-white">${{ record.open_price }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-900 dark:text-white">${{ record.high_price }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-900 dark:text-white">${{ record.low_price }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-gray-900 dark:text-white">${{ record.close_price }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{ formatVolume(record.volume) }}</span>
              </td>
              <td class="px-6 py-4">
                <span 
                  v-if="record.price_change"
                  :class="[
                    'text-sm font-medium',
                    record.price_change >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ record.price_change >= 0 ? '+' : '' }}{{ record.price_change }}%
                </span>
                <span v-else class="text-sm text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分頁 -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-700 dark:text-gray-300">
            顯示第 {{ pagination.current_page }} 頁，共 {{ pagination.total_pages }} 頁
            (總計 {{ pagination.total_records }} 筆資料)
          </div>
          <div class="flex items-center space-x-2">
            <button 
              @click="handlePrevPage"
              :disabled="pagination.current_page <= 1 || loading"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一頁
            </button>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              第 {{ pagination.current_page }} / {{ pagination.total_pages }} 頁
            </span>
            <button 
              @click="handleNextPage"
              :disabled="pagination.current_page >= pagination.total_pages || loading"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一頁
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 無資料提示 -->
    <div v-else-if="hasSearched" class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-12 text-center">
      <div class="text-gray-400 mb-4">
        <ChartBarIcon class="w-16 h-16 mx-auto" />
      </div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">查無資料</h3>
      <p class="text-gray-600 dark:text-gray-400">
        找不到股票代碼 {{ queryParams.symbol }} 的歷史資料，請確認股票代碼是否正確。
      </p>
    </div>
  </div>
</template>

<script setup>
import {
  MagnifyingGlassIcon,
  ChartBarIcon,
  CalendarIcon,
  ArrowDownTrayIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '股票歷史資料查詢'
})

// 使用組合式函數
const { 
  loading, 
  error, 
  getStockHistory, 
  getStockStats, 
  getLatestTradeDate 
} = useStocks()

// 響應式資料
const queryParams = ref({
  symbol: '',
  start_date: '',
  end_date: '',
  sort_by: 'trade_date',
  sort_order: 'desc',
  limit: 20,
  page: 1
})

const historyData = ref([])
const stats = ref(null)
const latestDate = ref(null)
const hasSearched = ref(false)
const pagination = ref({
  current_page: 1,
  total_pages: 1,
  total_records: 0
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

// API處理函數
const handleQueryHistory = async () => {
  if (!queryParams.value.symbol) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  hasSearched.value = true
  const params = { ...queryParams.value }
  
  // 移除空值
  Object.keys(params).forEach(key => {
    if (params[key] === '') {
      delete params[key]
    }
  })

  const result = await getStockHistory(params.symbol, params)
  
  if (result) {
    historyData.value = result.data || []
    pagination.value = result.pagination || {
      current_page: 1,
      total_pages: 1,
      total_records: 0
    }
    
    if (historyData.value.length > 0) {
      showNotification('success', `成功取得 ${pagination.value.total_records} 筆歷史資料`)
    } else {
      showNotification('info', '查無符合條件的資料')
    }
  } else {
    showNotification('error', error.value || '查詢歷史資料失敗')
  }
}

const handleGetStats = async () => {
  if (!queryParams.value.symbol) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  const result = await getStockStats(queryParams.value.symbol)
  
  if (result) {
    stats.value = result
    showNotification('success', '成功取得統計資訊')
  } else {
    showNotification('error', error.value || '取得統計資訊失敗')
  }
}

const handleGetLatestDate = async () => {
  if (!queryParams.value.symbol) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  const result = await getLatestTradeDate(queryParams.value.symbol)
  
  if (result) {
    latestDate.value = result.latest_trade_date
    showNotification('success', result.has_data ? `最新交易日: ${result.latest_trade_date}` : result.message)
  } else {
    showNotification('error', error.value || '取得最新交易日失敗')
  }
}

// 分頁處理
const handlePrevPage = () => {
  if (queryParams.value.page > 1) {
    queryParams.value.page--
    handleQueryHistory()
  }
}

const handleNextPage = () => {
  if (queryParams.value.page < pagination.value.total_pages) {
    queryParams.value.page++
    handleQueryHistory()
  }
}

// 匯出資料
const exportData = () => {
  if (historyData.value.length === 0) {
    showNotification('error', '無資料可匯出')
    return
  }

  const csv = [
    ['交易日期', '開盤價', '最高價', '最低價', '收盤價', '成交量', '漲跌幅'],
    ...historyData.value.map(record => [
      record.trade_date,
      record.open_price,
      record.high_price,
      record.low_price,
      record.close_price,
      record.volume,
      record.price_change || ''
    ])
  ].map(row => row.join(',')).join('\n')

  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${queryParams.value.symbol}_歷史資料_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  showNotification('success', 'CSV檔案已下載')
}

// 工具函數
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

const formatVolume = (volume) => {
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(1) + 'M'
  } else if (volume >= 1000) {
    return (volume / 1000).toFixed(1) + 'K'
  }
  return volume.toString()
}

// 監聽查詢參數變化
watch(() => queryParams.value.symbol, (newSymbol) => {
  // 清除之前的資料
  historyData.value = []
  stats.value = null
  latestDate.value = null
  hasSearched.value = false
  queryParams.value.page = 1
})
</script>