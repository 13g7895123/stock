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
    <!-- 頁面標題與操作 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">股票清單管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">管理系統中的股票資料，包括新增、編輯和刪除股票</p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton 
            @click="handleCrawlStocks"
            :loading="loading"
            :icon="ArrowPathIcon"
            text="爬取股票清單"
            loading-text="爬取中..."
            variant="success"
          />
          <ActionButton 
            @click="handleSyncStocks"
            :loading="loading"
            :icon="ArrowPathIcon"
            text="同步股票列表"
            loading-text="同步中..."
            variant="info"
          />
          <ActionButton 
            @click="handleGetStockCount"
            :loading="loading"
            :icon="ChartBarIcon"
            text="檢查數量"
            variant="secondary"
          />
        </div>
      </div>
    </div>

    <!-- 篩選與搜尋 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 搜尋 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">搜尋股票</label>
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="股票代碼或名稱..."
              class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        <!-- 市場分類 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">市場</label>
          <select
            v-model="selectedMarket"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">全部市場</option>
            <option value="TSE">上市</option>
            <option value="OTC">上櫃</option>
            <option value="EMERGING">興櫃</option>
          </select>
        </div>

        <!-- 產業分類 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">產業</label>
          <select
            v-model="selectedIndustry"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">全部產業</option>
            <option value="semiconductor">半導體</option>
            <option value="electronics">電子零組件</option>
            <option value="finance">金融保險</option>
            <option value="steel">鋼鐵工業</option>
          </select>
        </div>

        <!-- 狀態篩選 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">狀態</label>
          <select
            v-model="selectedStatus"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">全部狀態</option>
            <option value="active">正常交易</option>
            <option value="suspended">暫停交易</option>
            <option value="delisted">已下市</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 股票列表 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <!-- 表格標題 -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            股票列表 ({{ filteredStocks.length }} 檔)
            <span v-if="stockCount !== null" class="text-sm text-gray-500 dark:text-gray-400 ml-2">
              (資料庫: {{ stockCount }} 檔)
            </span>
          </h3>
          <div class="flex items-center space-x-2">
            <ActionButton 
              @click="loadStockList"
              :loading="loading"
              :icon="ArrowPathIcon"
              text="重新載入"
              loading-text="載入中..."
              variant="primary"
              size="sm"
            />
            <button class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
              <FunnelIcon class="w-4 h-4" />
            </button>
            <button class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
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
                <input type="checkbox" class="rounded border-gray-300 dark:border-gray-600" />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                股票代碼
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                股票名稱
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                市場
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                產業
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                目前價格
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                漲跌幅
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                資料狀態
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                最後更新
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="stock in paginatedStocks"
              :key="stock.code"
              class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <td class="px-6 py-4">
                <input type="checkbox" class="rounded border-gray-300 dark:border-gray-600" />
              </td>
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ stock.code }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-900 dark:text-white">{{ stock.name }}</span>
              </td>
              <td class="px-6 py-4">
                <span 
                  class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                  :class="{
                    'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200': stock.market === 'TSE',
                    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': stock.market === 'OTC',
                    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': stock.market === 'EMERGING'
                  }"
                >
                  {{ stock.market }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{ stock.industry }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-gray-900 dark:text-white">${{ stock.price }}</span>
              </td>
              <td class="px-6 py-4">
                <span 
                  :class="[
                    'text-sm font-medium',
                    stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ stock.change >= 0 ? '+' : '' }}{{ stock.change }}%
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center space-x-2">
                  <div 
                    :class="[
                      'w-2 h-2 rounded-full',
                      stock.dataStatus === 'complete' ? 'bg-green-500' :
                      stock.dataStatus === 'partial' ? 'bg-yellow-500' : 'bg-red-500'
                    ]"
                  ></div>
                  <span class="text-xs text-gray-600 dark:text-gray-400">
                    {{ 
                      stock.dataStatus === 'complete' ? '完整' :
                      stock.dataStatus === 'partial' ? '部分' : '缺失'
                    }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ stock.lastUpdate }}</span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button class="p-1 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400">
                    <PencilIcon class="w-4 h-4" />
                  </button>
                  <button class="p-1 text-gray-400 hover:text-red-600">
                    <TrashIcon class="w-4 h-4" />
                  </button>
                  <button class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    <EllipsisVerticalIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分頁 -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-700 dark:text-gray-300">
            顯示第 {{ (currentPage - 1) * pageSize + 1 }} 至 {{ Math.min(currentPage * pageSize, filteredStocks.length) }} 筆，
            共 {{ filteredStocks.length }} 筆資料
          </div>
          <div class="flex items-center space-x-2">
            <button 
              @click="currentPage > 1 && currentPage--"
              :disabled="currentPage === 1"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一頁
            </button>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              第 {{ currentPage }} / {{ totalPages }} 頁
            </span>
            <button 
              @click="currentPage < totalPages && currentPage++"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一頁
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  PlusIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  TrashIcon,
  EllipsisVerticalIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '股票清單管理'
})

// 使用組合式函數
const { 
  loading, 
  error, 
  getStockCount, 
  crawlStockList, 
  syncStockList, 
  getStockList 
} = useStocks()

// 響應式資料
const searchQuery = ref('')
const selectedMarket = ref('')
const selectedIndustry = ref('')
const selectedStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const stockCount = ref(null)
const realStocks = ref([]) // 從API獲取的實際股票資料

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
  
  // 3秒後自動隱藏
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

// 模擬股票資料
const stocks = ref([
  {
    code: '2330',
    name: '台積電',
    market: 'TSE',
    industry: '半導體',
    price: 512.00,
    change: 2.1,
    dataStatus: 'complete',
    lastUpdate: '2分鐘前'
  },
  {
    code: '2317',
    name: '鴻海',
    market: 'TSE',
    industry: '電子零組件',
    price: 106.50,
    change: -1.2,
    dataStatus: 'complete',
    lastUpdate: '5分鐘前'
  },
  {
    code: '2454',
    name: '聯發科',
    market: 'TSE',
    industry: '半導體',
    price: 789.00,
    change: 3.8,
    dataStatus: 'partial',
    lastUpdate: '10分鐘前'
  }
])

// 計算屬性
const filteredStocks = computed(() => {
  let result = realStocks.value.length > 0 ? realStocks.value : stocks.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(stock => 
      stock.code.toLowerCase().includes(query) ||
      stock.name.toLowerCase().includes(query)
    )
  }

  if (selectedMarket.value) {
    result = result.filter(stock => stock.market === selectedMarket.value)
  }

  if (selectedIndustry.value) {
    result = result.filter(stock => stock.industry === selectedIndustry.value)
  }

  if (selectedStatus.value) {
    result = result.filter(stock => stock.status === selectedStatus.value)
  }

  return result
})

const totalPages = computed(() => Math.ceil(filteredStocks.value.length / pageSize.value))

const paginatedStocks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredStocks.value.slice(start, end)
})

// API處理函數
const handleGetStockCount = async () => {
  const result = await getStockCount()
  if (result) {
    stockCount.value = result.total
    showNotification('success', `資料庫中共有 ${result.total} 檔股票`)
  } else {
    showNotification('error', error.value || '獲取股票數量失敗')
  }
}

const loadStockList = async () => {
  try {
    const result = await getStockList({
      page: 1,
      limit: 2000, // 載入更多資料
      market: selectedMarket.value || undefined,
      search: searchQuery.value || undefined
    })
    
    console.log('API回傳資料:', result) // 除錯用
    
    if (result && result.stocks) {
      realStocks.value = result.stocks
      showNotification('success', `載入 ${result.stocks.length} 檔股票資料`)
      
      // 如果有分頁資訊，也顯示總數
      if (result.pagination && result.pagination.total) {
        console.log(`總共 ${result.pagination.total} 檔股票，目前載入 ${result.stocks.length} 檔`)
      }
    } else {
      console.error('API回傳格式錯誤:', result)
      showNotification('error', '無法取得股票資料，請檢查API回應格式')
    }
  } catch (err) {
    console.error('載入股票列表錯誤:', err)
    showNotification('error', `載入失敗: ${err.message || '未知錯誤'}`)
  }
}

const handleCrawlStocks = async () => {
  showNotification('info', '開始爬取股票清單...')
  const result = await crawlStockList()
  if (result) {
    await handleGetStockCount() // 重新獲取數量
    await loadStockList() // 重新載入股票列表
    showNotification('success', `爬取完成！成功處理 ${result.total_stocks || 0} 檔股票`)
  } else {
    showNotification('error', error.value || '爬取股票清單失敗')
  }
}

const handleSyncStocks = async () => {
  showNotification('info', '開始同步股票清單...')
  const result = await syncStockList()
  if (result) {
    await handleGetStockCount() // 重新獲取數量
    await loadStockList() // 重新載入股票列表
    showNotification('success', `同步完成！處理了 ${result.total_stocks || 0} 檔股票`)
  } else {
    showNotification('error', error.value || '同步股票清單失敗')
  }
}

// 監聽篩選條件變化，重置頁面
watch([searchQuery, selectedMarket, selectedIndustry, selectedStatus], () => {
  currentPage.value = 1
})

// 組件掛載時獲取股票數量和列表
onMounted(async () => {
  await handleGetStockCount()
  await loadStockList()
})
</script>