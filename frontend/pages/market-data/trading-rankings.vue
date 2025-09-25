<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-7xl mx-auto px-4 py-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">三大法人買賣超排名</h1>
            <p class="text-gray-600 dark:text-gray-400 mt-2">
              <span v-if="rankingsData.latest_date">{{ rankingsData.latest_date }} - </span>
              {{ categoryNames[selectedCategory] }}買賣超排名
              <span v-if="rankingsData.sort_name" class="ml-2 text-sm px-2 py-1 bg-blue-100 text-blue-800 rounded-full dark:bg-blue-900 dark:text-blue-200">
                {{ rankingsData.sort_name }}
              </span>
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <!-- 排序方式選擇器 -->
            <div class="relative">
              <select
                v-model="selectedSortBy"
                @change="handleSortByChange"
                class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="amount">按金額排序</option>
                <option value="capital_ratio">按股本比排序</option>
              </select>
            </div>

            <button
              @click="refreshRankings"
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
              重新整理
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <!-- 類別選擇 -->
      <div class="mb-8">
        <div class="sm:hidden">
          <label for="category-tabs" class="sr-only">選擇類別</label>
          <select
            id="category-tabs"
            v-model="selectedCategory"
            @change="handleCategoryChange"
            class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="total">三大法人合計</option>
            <option value="foreign">外資</option>
            <option value="investment_trust">投信</option>
            <option value="dealer">自營商</option>
          </select>
        </div>
        <div class="hidden sm:block">
          <nav class="flex space-x-8" aria-label="類別">
            <button
              v-for="(name, category) in categoryNames"
              :key="category"
              @click="selectCategory(category)"
              :class="[
                'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm',
                selectedCategory === category
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ name }}
            </button>
          </nav>
        </div>
      </div>

      <!-- 載入狀態 -->
      <div v-if="isLoading && !rankingsData.buy_rankings" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600 dark:text-gray-400">載入排名資料中...</p>
      </div>

      <!-- 錯誤狀態 -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">
              載入排名資料失敗
            </h3>
            <div class="mt-2 text-sm text-red-700">
              <p>{{ error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 排名資料 -->
      <div v-else-if="rankingsData.buy_rankings || rankingsData.sell_rankings" class="grid lg:grid-cols-2 gap-8">
        <!-- 買超排名 -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
              </svg>
              買超排名 (前{{ rankingsData.buy_count }}名)
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">排名</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">買超金額</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股本比</th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  <tr
                    v-for="item in rankingsData.buy_rankings"
                    :key="item.stock_code"
                    class="hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <td class="px-3 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <span
                          :class="[
                            'inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-medium',
                            item.rank <= 3
                              ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                              : 'bg-gray-100 text-gray-800 border border-gray-200'
                          ]"
                        >
                          {{ item.rank }}
                        </span>
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap">
                      <div>
                        <div class="text-sm font-medium text-gray-900 dark:text-white">{{ item.stock_code }}</div>
                        <div class="text-sm text-gray-500 dark:text-gray-400">{{ item.stock_name }}</div>
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-medium text-green-600">
                        +{{ formatNumber(item.net_amount) }}
                      </div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        外: {{ formatNumber(item.foreign_net) }} |
                        投: {{ formatNumber(item.investment_trust_net) }} |
                        自: {{ formatNumber(item.dealer_net) }}
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-medium text-green-600">
                        {{ formatCapitalRatio(item.capital_ratio) }}
                      </div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        {{ formatCapitalStock(item.capital_stock) }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 賣超排名 -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
              </svg>
              賣超排名 (前{{ rankingsData.sell_count }}名)
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">排名</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股票</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">賣超金額</th>
                    <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">股本比</th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  <tr
                    v-for="item in rankingsData.sell_rankings"
                    :key="item.stock_code"
                    class="hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <td class="px-3 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <span
                          :class="[
                            'inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-medium',
                            item.rank <= 3
                              ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                              : 'bg-gray-100 text-gray-800 border border-gray-200'
                          ]"
                        >
                          {{ item.rank }}
                        </span>
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap">
                      <div>
                        <div class="text-sm font-medium text-gray-900 dark:text-white">{{ item.stock_code }}</div>
                        <div class="text-sm text-gray-500 dark:text-gray-400">{{ item.stock_name }}</div>
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-medium text-red-600">
                        {{ formatNumber(item.net_amount) }}
                      </div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        外: {{ formatNumber(item.foreign_net) }} |
                        投: {{ formatNumber(item.investment_trust_net) }} |
                        自: {{ formatNumber(item.dealer_net) }}
                      </div>
                    </td>
                    <td class="px-3 py-4 whitespace-nowrap text-right">
                      <div class="text-sm font-medium text-red-600">
                        {{ formatCapitalRatio(item.capital_ratio) }}
                      </div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        {{ formatCapitalStock(item.capital_stock) }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- 無資料狀態 -->
      <div v-else class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">目前沒有排名資料</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">請嘗試重新整理或檢查資料來源</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const { $api } = useNuxtApp()

// 響應式資料
const isLoading = ref(false)
const error = ref('')
const selectedCategory = ref('total')
const selectedSortBy = ref('amount')

const rankingsData = ref({
  latest_date: '',
  category: '',
  category_name: '',
  sort_by: '',
  sort_name: '',
  buy_rankings: [],
  sell_rankings: [],
  buy_count: 0,
  sell_count: 0
})

// 類別名稱映射
const categoryNames = {
  total: '三大法人合計',
  foreign: '外資',
  investment_trust: '投信',
  dealer: '自營商'
}

// 排序方式名稱映射
const sortNames = {
  amount: '按金額排序',
  capital_ratio: '按股本比排序'
}

// 方法
const formatNumber = (num) => {
  if (num === 0) return '0'
  if (num > 0) {
    if (num >= 100000000) { // 1億以上
      return (num / 100000000).toFixed(1) + '億'
    } else if (num >= 10000) { // 1萬以上
      return (num / 10000).toFixed(0) + '萬'
    }
  } else {
    const absNum = Math.abs(num)
    if (absNum >= 100000000) { // 1億以上
      return '-' + (absNum / 100000000).toFixed(1) + '億'
    } else if (absNum >= 10000) { // 1萬以上
      return '-' + (absNum / 10000).toFixed(0) + '萬'
    }
  }
  return num.toLocaleString()
}

const formatCapitalRatio = (ratio) => {
  if (ratio === null || ratio === undefined) {
    return '-'
  }
  if (Math.abs(ratio) < 0.001) {
    return '0.00%'
  }
  return ratio.toFixed(3) + '%'
}

const formatCapitalStock = (capitalStock) => {
  if (!capitalStock) {
    return '未知股本'
  }
  if (capitalStock >= 100000000000) { // 1000億以上
    return (capitalStock / 100000000000).toFixed(1) + '千億'
  } else if (capitalStock >= 100000000) { // 1億以上
    return (capitalStock / 100000000).toFixed(1) + '億'
  } else if (capitalStock >= 10000) { // 1萬以上
    return (capitalStock / 10000).toFixed(0) + '萬'
  }
  return capitalStock.toLocaleString()
}

const showNotification = (message, type = 'info') => {
  // 簡單的通知處理
  console.log(`[${type}] ${message}`)
}

const loadRankings = async (category = selectedCategory.value, sortBy = selectedSortBy.value) => {
  try {
    isLoading.value = true
    error.value = ''

    const response = await $api(`/institutional-trading/rankings/latest?category=${category}&limit=20&sort_by=${sortBy}`)

    if (response.success && response.data?.status === 'success') {
      rankingsData.value = response.data.data
      console.log('📊 買賣超排名載入完成:', {
        category: rankingsData.value.category_name,
        date: rankingsData.value.latest_date,
        buy_count: rankingsData.value.buy_count,
        sell_count: rankingsData.value.sell_count
      })
    } else {
      const errorMessage = response.error || response.data?.message || '載入排名資料失敗'
      error.value = errorMessage
      showNotification(errorMessage, 'error')
    }
  } catch (err) {
    console.error('載入買賣超排名失敗:', err)
    error.value = '載入排名資料時發生錯誤'
    showNotification('載入排名資料時發生錯誤', 'error')
  } finally {
    isLoading.value = false
  }
}

const selectCategory = (category) => {
  if (category !== selectedCategory.value) {
    selectedCategory.value = category
    loadRankings(category, selectedSortBy.value)
  }
}

const selectSortBy = (sortBy) => {
  if (sortBy !== selectedSortBy.value) {
    selectedSortBy.value = sortBy
    loadRankings(selectedCategory.value, sortBy)
  }
}

const handleCategoryChange = () => {
  loadRankings(selectedCategory.value, selectedSortBy.value)
}

const handleSortByChange = () => {
  loadRankings(selectedCategory.value, selectedSortBy.value)
}

const refreshRankings = () => {
  loadRankings(selectedCategory.value, selectedSortBy.value)
}

// 頁面初始化
onMounted(() => {
  loadRankings()
})

// SEO
useHead({
  title: '三大法人買賣超排名',
  meta: [
    { name: 'description', content: '台股三大法人(外資、投信、自營商)買賣超排名，即時顯示買超賣超前20名股票' }
  ]
})
</script>

<style scoped>
/* 自定義樣式 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>