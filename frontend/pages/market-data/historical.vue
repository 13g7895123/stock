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
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">歷史資料管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">查看和管理系統中的股票歷史資料</p>
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

    <!-- 資料統計總覽 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <BuildingOfficeIcon class="w-8 h-8 text-blue-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">總股票數</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ overallStats?.total_stocks || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ChartBarIcon class="w-8 h-8 text-green-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">總資料筆數</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ formatNumber(overallStats?.total_records || 0) }}
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
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">最新資料日期</div>
            <div class="text-lg font-bold text-gray-900 dark:text-white">
              {{ overallStats?.latest_date || 'N/A' }}
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
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">資料完整度</div>
            <div class="text-2xl font-bold text-green-600">
              {{ overallStats?.completeness || 0 }}%
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 有資料的股票清單 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm">
      <!-- 標題區 -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">有資料的股票清單</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">系統中有歷史資料的股票清單及統計資訊</p>
          </div>
          
          <div class="flex items-center space-x-4">
            <!-- 統計資訊 -->
            <div class="text-sm text-gray-600 dark:text-gray-400">
              <span class="font-medium">共 {{ stocksWithData.length }} 檔有資料股票</span>
              （支援前端分頁與搜尋）
            </div>
            
            <!-- 操作按鈕 -->
            <ActionButton 
              @click="handleRefreshStocksList"
              :loading="stocksListLoading"
              :icon="ArrowPathIcon"
              text="重新整理"
              variant="secondary"
              size="sm"
            />
          </div>
        </div>
      </div>


      <!-- 股票清單內容 -->
      <CollapsibleStockTable
        title=""
        description=""
        :data="stocksWithData"
        :loading="stocksListLoading"
        :initially-expanded="true"
        :show-header="false"
        @view-details="viewStockHistory"
        @update-data="updateStockData"
        @refresh="() => handleRefreshStocksList(false)"
      />
    </div>

    <!-- 資料查詢區域 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">資料查詢</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
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

        <!-- 筆數限制 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">顯示筆數</label>
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

        <!-- 查詢按鈕 -->
        <div class="flex items-end">
          <ActionButton 
            @click="handleQueryData"
            :loading="loading"
            :disabled="!queryParams.symbol"
            :icon="MagnifyingGlassIcon"
            text="查詢資料"
            loading-text="查詢中..."
            variant="primary"
            class="w-full"
          />
        </div>
      </div>

      <!-- 快速操作按鈕 -->
      <div class="flex flex-wrap gap-3 mb-6">
        <ActionButton 
          @click="setTodayDates"
          :icon="CalendarIcon"
          text="今日資料"
          variant="secondary"
          size="sm"
        />
        <ActionButton 
          @click="setLastWeekDates"
          :icon="CalendarIcon"
          text="近一週"
          variant="secondary"
          size="sm"
        />
        <ActionButton 
          @click="setLastMonthDates"
          :icon="CalendarIcon"
          text="近一月"
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
      <div v-if="historyData.length > 0" class="overflow-x-auto">
        <div class="mb-4 flex items-center justify-between">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            找到 {{ pagination.total_records }} 筆資料，顯示第 {{ pagination.current_page }} 頁
          </div>
          <ActionButton 
            @click="exportData"
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
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">開盤價</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">最高價</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">最低價</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">收盤價</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">成交量</th>
              <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-right text-sm font-medium text-gray-500 dark:text-gray-300">漲跌幅</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="record in historyData"
              :key="record.trade_date"
              class="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm">{{ formatDate(record.trade_date) }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">${{ record.open_price }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">${{ record.high_price }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">${{ record.low_price }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right font-medium">${{ record.close_price }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">{{ formatVolume(record.volume) }}</td>
              <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-right">
                <span 
                  v-if="record.price_change"
                  :class="[
                    'font-medium',
                    record.price_change >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ record.price_change >= 0 ? '+' : '' }}{{ record.price_change }}%
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分頁 -->
        <div v-if="pagination.total_pages > 1" class="mt-4 flex items-center justify-between">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            第 {{ pagination.current_page }} / {{ pagination.total_pages }} 頁
          </div>
          <div class="flex items-center space-x-2">
            <ActionButton 
              @click="handlePrevPage"
              :disabled="pagination.current_page <= 1 || loading"
              :icon="ChevronLeftIcon"
              text="上一頁"
              variant="secondary"
              size="sm"
            />
            <ActionButton 
              @click="handleNextPage"
              :disabled="pagination.current_page >= pagination.total_pages || loading"
              :icon="ChevronRightIcon"
              text="下一頁"
              variant="secondary"
              size="sm"
            />
          </div>
        </div>
      </div>

      <!-- 無資料提示 -->
      <div v-else-if="hasSearched" class="text-center py-12">
        <ChartBarIcon class="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">查無資料</h3>
        <p class="text-gray-600 dark:text-gray-400">
          {{ queryParams.symbol ? `找不到股票代碼 ${queryParams.symbol} 的歷史資料` : '請輸入股票代碼進行查詢' }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  CalendarIcon,
  CheckCircleIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  XCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline'
import CollapsibleStockTable from '@/components/CollapsibleStockTable.vue'

// 設定頁面標題
definePageMeta({
  title: '歷史資料管理'
})

// 使用組合式函數
const { 
  loading, 
  error, 
  getStockHistory,
  getOverallStats,
  getStocksWithData
} = useStocks()

// 響應式資料
const overallStats = ref(null)
const historyData = ref([])
const hasSearched = ref(false)
const pagination = ref({
  current_page: 1,
  total_pages: 1,
  total_records: 0
})

// 股票清單相關資料
const stocksWithData = ref([])
const stocksListLoading = ref(false)
const stocksPagination = ref({
  page: 1,
  limit: 50,
  total_pages: 1,
  total_stocks: 0,
  has_next: false,
  has_previous: false
})
const stocksQueryParams = ref({
  page: 1,
  limit: 50,  // 預設載入更多資料
  sort_by: 'stock_code',  // 預設按股票代號排序
  sort_order: 'asc'
})

const queryParams = ref({
  symbol: '',
  start_date: '',
  end_date: '',
  limit: 20,
  page: 1
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

// 計算可見的分頁按鈕
const visibleStockPages = computed(() => {
  const pages = []
  const total = stocksPagination.value.total_pages
  const current = stocksPagination.value.page
  
  if (total <= 7) {
    // 如果總頁數少於等於7頁，顯示所有頁面
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // 顯示當前頁面前後各2頁
    let start = Math.max(1, current - 2)
    let end = Math.min(total, current + 2)
    
    // 確保至少顯示5頁
    if (end - start < 4) {
      if (start === 1) {
        end = Math.min(total, start + 4)
      } else {
        start = Math.max(1, end - 4)
      }
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
  }
  
  return pages
})

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

const formatVolume = (volume) => {
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(1) + 'M'
  } else if (volume >= 1000) {
    return (volume / 1000).toFixed(1) + 'K'
  }
  return volume?.toString() || '0'
}

const getCurrentDate = () => {
  return new Date().toISOString().split('T')[0]
}

// 日期設定函數
const setTodayDates = () => {
  const today = getCurrentDate()
  queryParams.value.start_date = today
  queryParams.value.end_date = today
}

const setLastWeekDates = () => {
  const today = new Date()
  const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
  queryParams.value.start_date = lastWeek.toISOString().split('T')[0]
  queryParams.value.end_date = getCurrentDate()
}

const setLastMonthDates = () => {
  const today = new Date()
  const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
  queryParams.value.start_date = lastMonth.toISOString().split('T')[0]
  queryParams.value.end_date = getCurrentDate()
}

const clearDates = () => {
  queryParams.value.start_date = ''
  queryParams.value.end_date = ''
}

// API處理函數
const handleRefreshStats = async () => {
  const result = await getOverallStats()
  if (result) {
    overallStats.value = result
    showNotification('success', '成功重新整理統計資訊')
  } else {
    showNotification('error', error.value || '重新整理統計資訊失敗')
  }
}

const handleQueryData = async () => {
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

const handlePrevPage = () => {
  if (queryParams.value.page > 1) {
    queryParams.value.page--
    handleQueryData()
  }
}

const handleNextPage = () => {
  if (queryParams.value.page < pagination.value.total_pages) {
    queryParams.value.page++
    handleQueryData()
  }
}

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
  link.download = `${queryParams.value.symbol}_歷史資料_${getCurrentDate()}.csv`
  link.click()
  
  showNotification('success', 'CSV檔案已下載')
}

// 股票清單處理函數
const handleRefreshStocksList = async (showMessage = true) => {
  stocksListLoading.value = true
  // 移除分頁參數，一次性載入所有資料
  const params = { limit: 9999 } // 設置一個大的限制來獲取所有資料
  const result = await getStocksWithData(params)
  
  if (result) {
    stocksWithData.value = result.stocks || []
    
    if (showMessage && stocksWithData.value.length > 0) {
      showNotification('success', `載入 ${stocksWithData.value.length} 檔有資料股票`)
    } else if (showMessage) {
      showNotification('info', '系統中目前沒有任何股票的歷史資料')
    }
  } else {
    if (showMessage) {
      showNotification('error', error.value || '載入股票清單失敗')
    }
  }
  
  stocksListLoading.value = false
}


const viewStockHistory = (stockCode) => {
  // 將選中的股票代號填入查詢表單並自動查詢
  queryParams.value.symbol = stockCode
  handleQueryData()
  
  // 滾動到查詢結果區域
  nextTick(() => {
    const querySection = document.querySelector('.bg-white.dark\\:bg-gray-800:nth-child(4)')
    if (querySection) {
      querySection.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

const updateStockData = async (stockCode) => {
  try {
    showNotification('info', `正在更新股票 ${stockCode} 的資料...`)
    
    // 調用資料更新API (使用GET方法)
    const response = await $fetch(`http://localhost:9127/api/v1/data/daily/${stockCode}`)
    
    if (response.status === 'success') {
      const message = `股票 ${stockCode} 資料更新成功 (處理 ${response.records_processed} 筆，新增 ${response.records_created} 筆，更新 ${response.records_updated} 筆)`
      showNotification('success', message)
      // 重新整理股票清單和統計資訊
      await handleRefreshStocksList()
      await handleRefreshStats()
    } else if (response.status === 'skipped') {
      const message = `股票 ${stockCode} 資料已是最新 (最新日期: ${response.latest_date})`
      showNotification('info', message)
    } else {
      throw new Error(response.message || '更新失敗')
    }
  } catch (error) {
    console.error('更新股票資料錯誤:', error)
    const errorMessage = error.data?.detail || error.message || '更新失敗'
    showNotification('error', `更新股票 ${stockCode} 資料失敗: ${errorMessage}`)
  }
}

// 監聽查詢參數變化
watch(() => queryParams.value.symbol, (newSymbol) => {
  // 清除之前的資料
  historyData.value = []
  hasSearched.value = false
  queryParams.value.page = 1
})

// 初始化
onMounted(async () => {
  // 設定預設日期為今天
  setTodayDates()
  // 獲取系統統計
  await handleRefreshStats()
  // 載入有資料的股票清單
  await handleRefreshStocksList()
})
</script>