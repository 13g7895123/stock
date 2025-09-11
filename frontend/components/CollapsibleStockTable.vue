<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm">
    <!-- 可收折的標題列 -->
    <div 
      @click="toggleCollapse"
      class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <ChevronRightIcon 
            :class="[
              'h-5 w-5 transition-transform duration-200 text-gray-500',
              isExpanded ? 'transform rotate-90' : ''
            ]"
          />
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ title }}</h3>
            <p v-if="description" class="text-sm text-gray-600 dark:text-gray-400">{{ description }}</p>
          </div>
        </div>
        
        <div class="flex items-center space-x-4">
          <!-- 統計資訊 -->
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <span class="font-medium">{{ filteredData.length }}</span> / {{ totalCount }} 檔股票
          </div>
          
          <!-- 操作按鈕 -->
          <div class="flex items-center space-x-2" @click.stop>
            <slot name="header-actions"></slot>
          </div>
        </div>
      </div>
    </div>

    <!-- 可收折的內容區域 -->
    <div 
      v-show="isExpanded"
      class="transition-all duration-300 ease-in-out"
      :class="isExpanded ? 'opacity-100' : 'opacity-0'"
    >
      <!-- 控制面板 -->
      <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <!-- 搜尋和篩選 -->
          <div class="flex items-center space-x-4">
            <!-- 搜尋框 -->
            <div class="relative">
              <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜尋股票代號或名稱..."
                class="pl-10 pr-4 py-2 w-64 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <!-- 快速篩選 -->
            <select 
              v-model="quickFilter"
              class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">全部</option>
              <option value="high_volume">高成交量</option>
              <option value="recent_data">近期有資料</option>
              <option value="complete_data">資料完整</option>
            </select>
          </div>
          
          <!-- 排序和顯示選項 -->
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <label class="text-sm text-gray-600 dark:text-gray-400">排序：</label>
              <select 
                v-model="sortBy"
                class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="record_count">資料筆數</option>
                <option value="latest_date">最新日期</option>
                <option value="stock_code">股票代號</option>
                <option value="avg_close_price">平均收盤價</option>
                <option value="data_period_days">資料期間</option>
              </select>
              <select 
                v-model="sortOrder"
                class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="desc">遞減</option>
                <option value="asc">遞增</option>
              </select>
            </div>
            
            <div class="flex items-center space-x-2">
              <label class="text-sm text-gray-600 dark:text-gray-400">每頁：</label>
              <select 
                v-model="pageSize"
                class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- 載入狀態 -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="flex flex-col items-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">載入股票清單中...</p>
        </div>
      </div>

      <!-- 空狀態 -->
      <div v-else-if="filteredData.length === 0" class="flex items-center justify-center py-12">
        <div class="text-center">
          <BuildingOfficeIcon class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">{{ emptyMessage }}</h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ emptyDescription }}</p>
        </div>
      </div>

      <!-- 資料表格 -->
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                股票代號
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                股票名稱
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                資料筆數
              </th>
              <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                資料期間
              </th>
              <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                最新日期
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                平均價格
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                成交量
              </th>
              <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
            <tr
              v-for="stock in paginatedData"
              :key="stock.stock_code"
              class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <span class="text-sm font-medium font-mono text-gray-900 dark:text-white">
                    {{ stock.stock_code }}
                  </span>
                </div>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900 dark:text-white">
                  {{ stock.stock_name }}
                </div>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-right">
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ formatNumber(stock.record_count) }}
                </span>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <div class="flex flex-col">
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {{ stock.earliest_date || 'N/A' }}
                  </span>
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {{ stock.data_period_days }}天
                  </span>
                </div>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <span class="text-sm text-gray-900 dark:text-white">
                  {{ stock.latest_date || 'N/A' }}
                </span>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-right">
                <span class="text-sm text-gray-900 dark:text-white">
                  ${{ formatPrice(stock.avg_close_price) }}
                </span>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-right">
                <span class="text-sm text-gray-900 dark:text-white">
                  {{ formatNumber(stock.total_volume) }}
                </span>
              </td>
              
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <div class="flex items-center justify-center space-x-2">
                  <!-- 查看按鈕 -->
                  <button
                    @click="$emit('view-details', stock.stock_code)"
                    :title="`查看 ${stock.stock_code} 詳細資料`"
                    class="p-1.5 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                  >
                    <EyeIcon class="h-4 w-4" />
                  </button>
                  <!-- 更新按鈕 -->
                  <button
                    @click="$emit('update-data', stock.stock_code)"
                    :title="`更新 ${stock.stock_code} 歷史資料`"
                    class="p-1.5 text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-md transition-colors"
                  >
                    <ArrowPathIcon class="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分頁控制 -->
        <div v-if="totalPages > 1" class="bg-white dark:bg-gray-800 px-6 py-4 border-t border-gray-200 dark:border-gray-600">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-700 dark:text-gray-300">
              顯示 {{ (currentPage - 1) * pageSize + 1 }} 到 {{ Math.min(currentPage * pageSize, filteredData.length) }} 項，
              共 {{ filteredData.length }} 項
            </div>
            
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                @click="goToPage(currentPage - 1)"
                :disabled="currentPage === 1"
                :class="[
                  'relative inline-flex items-center px-2 py-2 rounded-l-md border text-sm font-medium',
                  currentPage === 1
                    ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-500'
                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                ]"
              >
                <ChevronLeftIcon class="h-5 w-5" />
              </button>

              <button
                v-for="page in visiblePages"
                :key="page"
                @click="goToPage(page)"
                :class="[
                  'relative inline-flex items-center px-4 py-2 border text-sm font-medium',
                  page === currentPage
                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600 dark:bg-blue-900 dark:border-blue-600 dark:text-blue-200'
                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                ]"
              >
                {{ page }}
              </button>

              <button
                @click="goToPage(currentPage + 1)"
                :disabled="currentPage === totalPages"
                :class="[
                  'relative inline-flex items-center px-2 py-2 rounded-r-md border text-sm font-medium',
                  currentPage === totalPages
                    ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:border-gray-600 dark:text-gray-500'
                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                ]"
              >
                <ChevronRightIcon class="h-5 w-5" />
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  ChevronRightIcon,
  ChevronLeftIcon,
  ChevronRightIcon as ChevronRightPaginationIcon,
  MagnifyingGlassIcon,
  BuildingOfficeIcon,
  EyeIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps({
  title: {
    type: String,
    default: '股票清單'
  },
  description: {
    type: String,
    default: ''
  },
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyMessage: {
    type: String,
    default: '暫無股票資料'
  },
  emptyDescription: {
    type: String,
    default: '目前沒有找到符合條件的股票資料'
  },
  initiallyExpanded: {
    type: Boolean,
    default: true
  }
})

// Emits
defineEmits(['view-details', 'update-data', 'refresh'])

// Reactive data
const isExpanded = ref(props.initiallyExpanded)
const searchQuery = ref('')
const quickFilter = ref('')
const sortBy = ref('stock_code')
const sortOrder = ref('asc')
const currentPage = ref(1)
const pageSize = ref(20)

// Computed
const totalCount = computed(() => props.data.length)

const filteredData = computed(() => {
  let filtered = props.data

  // 搜尋篩選
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(stock => 
      stock.stock_code.toLowerCase().includes(query) ||
      stock.stock_name.toLowerCase().includes(query)
    )
  }

  // 快速篩選
  if (quickFilter.value) {
    switch (quickFilter.value) {
      case 'high_volume':
        filtered = filtered.filter(stock => stock.total_volume > 50000)
        break
      case 'recent_data':
        const thirtyDaysAgo = new Date()
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
        filtered = filtered.filter(stock => {
          const latestDate = new Date(stock.latest_date)
          return latestDate >= thirtyDaysAgo
        })
        break
      case 'complete_data':
        filtered = filtered.filter(stock => stock.record_count > 100)
        break
    }
  }

  // 排序
  return filtered.sort((a, b) => {
    let valueA = a[sortBy.value]
    let valueB = b[sortBy.value]
    
    // 處理日期排序
    if (sortBy.value.includes('date')) {
      valueA = new Date(valueA).getTime()
      valueB = new Date(valueB).getTime()
    }
    
    // 處理數字排序
    if (typeof valueA === 'string' && !isNaN(Number(valueA))) {
      valueA = Number(valueA)
      valueB = Number(valueB)
    }
    
    let result = 0
    if (valueA < valueB) result = -1
    else if (valueA > valueB) result = 1
    
    return sortOrder.value === 'desc' ? -result : result
  })
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / pageSize.value))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value
  
  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)
  
  if (end - start < 4) {
    start = Math.max(1, end - 4)
  }
  if (end - start < 4) {
    end = Math.min(total, start + 4)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const toggleCollapse = () => {
  isExpanded.value = !isExpanded.value
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const formatNumber = (num) => {
  if (num == null) return 'N/A'
  return new Intl.NumberFormat('zh-TW').format(num)
}

const formatPrice = (price) => {
  if (price == null) return 'N/A'
  return Number(price).toFixed(2)
}

// Watch for search and filter changes
watch([searchQuery, quickFilter, sortBy, sortOrder], () => {
  currentPage.value = 1
})

watch(() => props.data, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = 1
  }
}, { deep: true })
</script>