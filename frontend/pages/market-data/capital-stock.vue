<template>
  <div class="space-y-6">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">股本資料管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">管理股票實收資本額資料</p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton
            @click="refreshStatistics"
            :loading="isLoading"
            :icon="ArrowPathIcon"
            text="重新整理"
            variant="secondary"
          />
          <ActionButton
            @click="updateCapitalStock"
            :loading="isUpdating"
            :icon="CloudArrowUpIcon"
            text="更新股本資料"
            variant="primary"
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
              {{ statistics.total_stocks || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CheckCircleIcon class="w-8 h-8 text-green-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">有股本資料</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ statistics.stocks_with_capital || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ExclamationTriangleIcon class="w-8 h-8 text-orange-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">缺少股本</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ statistics.stocks_without_capital || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ChartBarIcon class="w-8 h-8 text-purple-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">完整率</div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ statistics.completeness_rate || 0 }}%
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 股本分布統計 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">股本規模分布</h3>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ statistics.capital_distribution?.large_cap || 0 }}</div>
              <div class="text-sm text-red-700 dark:text-red-300">大型股 (≥100億)</div>
            </div>
            <div class="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ statistics.capital_distribution?.mid_cap || 0 }}</div>
              <div class="text-sm text-yellow-700 dark:text-yellow-300">中型股 (10-100億)</div>
            </div>
            <div class="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ statistics.capital_distribution?.small_cap || 0 }}</div>
              <div class="text-sm text-green-700 dark:text-green-300">小型股 (<10億)</div>
            </div>
          </div>
        </div>
    </div>

    <!-- 股本查詢 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">股本資料查詢</h3>
        </div>
        <div class="p-6">
          <div class="max-w-md">
            <label for="stock-search" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              請輸入股票代號
            </label>
            <div class="flex">
              <input
                id="stock-search"
                v-model="searchStockCode"
                type="text"
                placeholder="例：2330"
                maxlength="4"
                class="flex-1 min-w-0 block w-full px-3 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                @keyup.enter="searchStockCapital"
              >
              <button
                @click="searchStockCapital"
                :disabled="isSearching || !searchStockCode"
                class="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 dark:border-gray-600 text-sm font-medium rounded-r-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <svg v-if="isSearching" class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- 查詢結果 -->
          <div v-if="stockCapitalData" class="mt-6 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">股票代號</dt>
                <dd class="text-lg font-semibold text-gray-900 dark:text-white">{{ stockCapitalData.stock_code }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">公司名稱</dt>
                <dd class="text-lg font-semibold text-gray-900 dark:text-white">{{ stockCapitalData.stock_name }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">市場別</dt>
                <dd class="text-lg font-semibold text-gray-900 dark:text-white">{{ stockCapitalData.market }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">產業別</dt>
                <dd class="text-lg font-semibold text-gray-900 dark:text-white">{{ stockCapitalData.industry || 'N/A' }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">實收資本額</dt>
                <dd class="text-lg font-semibold text-green-600 dark:text-green-400">
                  NT$ {{ formatCurrency(stockCapitalData.capital_stock) }}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">股本規模</dt>
                <dd class="text-lg font-semibold">
                  <span
                    :class="{
                      'text-red-600 dark:text-red-400': stockCapitalData.capital_category === '大型股',
                      'text-yellow-600 dark:text-yellow-400': stockCapitalData.capital_category === '中型股',
                      'text-green-600 dark:text-green-400': stockCapitalData.capital_category === '小型股'
                    }"
                  >
                    {{ stockCapitalData.capital_category }}
                  </span>
                </dd>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">最後更新時間</dt>
              <dd class="text-sm text-gray-700 dark:text-gray-300">
                {{ formatDateTime(stockCapitalData.capital_updated_at) }}
              </dd>
            </div>
          </div>
        </div>

      <!-- 最後更新時間 -->
      <div v-if="statistics.last_update" class="text-center text-sm text-gray-500 dark:text-gray-400">
        最後更新：{{ formatDateTime(statistics.last_update) }}
      </div>
    </div>

    <!-- 通知 -->
    <div
      v-if="notification.show"
      :class="{
        'bg-green-50 border-green-200 text-green-800': notification.type === 'success',
        'bg-red-50 border-red-200 text-red-800': notification.type === 'error',
        'bg-blue-50 border-blue-200 text-blue-800': notification.type === 'info'
      }"
      class="fixed bottom-4 right-4 max-w-md w-full border rounded-md p-4 shadow-lg z-50"
    >
      <div class="flex">
        <div class="flex-shrink-0">
          <svg v-if="notification.type === 'success'" class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <svg v-else-if="notification.type === 'error'" class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
          <svg v-else class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm font-medium">{{ notification.message }}</p>
        </div>
        <div class="ml-auto pl-3">
          <div class="-mx-1.5 -my-1.5">
            <button
              @click="hideNotification"
              class="inline-flex rounded-md p-1.5 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  BuildingOfficeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ArrowPathIcon,
  CloudArrowUpIcon
} from '@heroicons/vue/24/outline'

// SEO 設定
useSeoMeta({
  title: '股本資料管理',
  description: '管理與查看股票實收資本額資料'
})

// 響應式狀態
const statistics = ref({})
const stockCapitalData = ref(null)
const searchStockCode = ref('')
const isLoading = ref(false)
const isUpdating = ref(false)
const isSearching = ref(false)

// 通知狀態
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// API 基本設定
const { $api } = useNuxtApp()

// 載入統計資料
const loadStatistics = async () => {
  try {
    isLoading.value = true
    const response = await $api('/capital-stock/statistics')

    if (response.success && response.data?.status === 'success') {
      statistics.value = response.data.data
    } else {
      console.error('載入統計資料失敗:', response.error || response.data?.message)
      showNotification('載入統計資料失敗', 'error')
    }
  } catch (error) {
    console.error('載入統計資料失敗:', error)
    showNotification('載入統計資料失敗', 'error')
  } finally {
    isLoading.value = false
  }
}

// 刷新統計資料
const refreshStatistics = async () => {
  await loadStatistics()
  showNotification('統計資料已更新', 'success')
}

// 更新股本資料
const updateCapitalStock = async () => {
  try {
    isUpdating.value = true
    const response = await $api('/capital-stock/update', {
      method: 'POST'
    })

    if (response.success && response.data?.status === 'success') {
      showNotification(response.data.message, 'success')
      await loadStatistics() // 重新載入統計資料
    } else {
      const errorMessage = response.error || response.data?.message || '更新失敗'
      showNotification(errorMessage, 'error')
    }
  } catch (error) {
    console.error('更新股本資料失敗:', error)
    showNotification('更新股本資料失敗', 'error')
  } finally {
    isUpdating.value = false
  }
}

// 搜尋股票股本資料
const searchStockCapital = async () => {
  if (!searchStockCode.value || searchStockCode.value.length !== 4) {
    showNotification('請輸入4位數股票代號', 'error')
    return
  }

  try {
    isSearching.value = true
    const response = await $api(`/capital-stock/${searchStockCode.value}`)

    if (response.status === 'success') {
      stockCapitalData.value = response.data
      showNotification('查詢成功', 'success')
    }
  } catch (error) {
    console.error('查詢股本資料失敗:', error)
    if (error.response?.status === 404) {
      showNotification('找不到該股票資料', 'error')
    } else {
      showNotification('查詢失敗', 'error')
    }
    stockCapitalData.value = null
  } finally {
    isSearching.value = false
  }
}

// 顯示通知
const showNotification = (message, type = 'info') => {
  notification.value = {
    show: true,
    type,
    message
  }

  // 3秒後自動隱藏
  setTimeout(() => {
    hideNotification()
  }, 3000)
}

// 隱藏通知
const hideNotification = () => {
  notification.value.show = false
}

// 格式化貨幣
const formatCurrency = (amount) => {
  if (!amount) return '0'
  return amount.toLocaleString('zh-TW')
}

// 格式化日期時間
const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 頁面載入時執行
onMounted(() => {
  loadStatistics()
})
</script>