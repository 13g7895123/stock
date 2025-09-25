<template>
  <div class="space-y-6">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">投信外資買賣超管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">管理三大法人買賣超資料</p>
        </div>
        <div class="flex space-x-4">
            <button
              @click="refreshStatistics"
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
            <button
              @click="updateLatestData"
              :disabled="isUpdating"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              <svg v-if="isUpdating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
              </svg>
              更新最新資料
            </button>
            <button
              @click="checkCompleteness"
              :disabled="isChecking"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
            >
              <svg v-if="isChecking" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              檢查資料完整性
            </button>
            <button
              @click="batchUpdate"
              :disabled="isBatchUpdating"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
            >
              <svg v-if="isBatchUpdating" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4-4m0 0L8 8m4-4v12"></path>
              </svg>
              下載近30天資料
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <!-- 統計卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                </div>
              </div>
              <div class="ml-4">
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">總記錄數</dt>
                <dd class="text-2xl font-bold text-gray-900 dark:text-white">{{ statistics.total_records || 0 }}</dd>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                  <svg class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                  </svg>
                </div>
              </div>
              <div class="ml-4">
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">有資料股票</dt>
                <dd class="text-2xl font-bold text-green-600 dark:text-green-400">{{ statistics.total_stocks || 0 }}</dd>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-yellow-100 dark:bg-yellow-900 rounded-full flex items-center justify-center">
                  <svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                </div>
              </div>
              <div class="ml-4">
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">資料天數</dt>
                <dd class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ statistics.total_days || 0 }}</dd>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
          <div class="p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                  <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
              </div>
              <div class="ml-4">
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">最新日期</dt>
                <dd class="text-lg font-bold text-purple-600 dark:text-purple-400">
                  {{ statistics.latest_date ? formatDate(statistics.latest_date) : 'N/A' }}
                </dd>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最新日期統計 -->
      <div v-if="statistics.latest_summary" class="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 mb-8">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            最新交易日統計 ({{ formatDate(statistics.latest_summary.date) }})
          </h3>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div class="text-xl font-bold text-red-600 dark:text-red-400">
                {{ formatShares(statistics.latest_summary.foreign_net_total) }}
              </div>
              <div class="text-sm text-red-700 dark:text-red-300">外資買賣超 (股)</div>
            </div>
            <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div class="text-xl font-bold text-blue-600 dark:text-blue-400">
                {{ formatShares(statistics.latest_summary.investment_trust_net_total) }}
              </div>
              <div class="text-sm text-blue-700 dark:text-blue-300">投信買賣超 (股)</div>
            </div>
            <div class="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div class="text-xl font-bold text-green-600 dark:text-green-400">
                {{ formatShares(statistics.latest_summary.dealer_net_total) }}
              </div>
              <div class="text-sm text-green-700 dark:text-green-300">自營商買賣超 (股)</div>
            </div>
            <div class="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div class="text-xl font-bold text-purple-600 dark:text-purple-400">
                {{ formatShares(statistics.latest_summary.total_net) }}
              </div>
              <div class="text-sm text-purple-700 dark:text-purple-300">三大法人合計 (股)</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 資料完整性檢查結果 -->
      <div v-if="completenessData" class="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 mb-8">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">資料完整性檢查結果</h3>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="text-center">
              <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ completenessData.completeness_rate }}%</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">完整率</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-green-600 dark:text-green-400">{{ completenessData.stocks_with_data }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">有資料股票</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-red-600 dark:text-red-400">{{ completenessData.stocks_without_data }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">缺少資料股票</div>
            </div>
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            分析期間：{{ formatDate(completenessData.analysis_period.start_date) }} ~
            {{ formatDate(completenessData.analysis_period.end_date) }}
            ({{ completenessData.analysis_period.days }} 天)
          </div>
        </div>
      </div>

      <!-- 股票查詢 -->
      <div class="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 mb-8">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">股票買賣超查詢</h3>
        </div>
        <div class="p-6">
          <div class="max-w-md mb-6">
            <label for="stock-search" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              請輸入股票代號
            </label>
            <div class="flex">
              <input
                id="stock-search"
                v-model="searchStockCode"
                type="text"
                placeholder="例：2330"
                maxlength="6"
                class="flex-1 min-w-0 block w-full px-3 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                @keyup.enter="searchStockData"
              >
              <button
                @click="searchStockData"
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
          <div v-if="stockData && stockData.length > 0" class="overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      交易日期
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      外資買賣超
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      投信買賣超
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      自營商買賣超
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      三大法人合計
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  <tr v-for="record in stockData" :key="record.trade_date" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {{ formatDate(record.trade_date) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm" :class="getNetBuyColorClass(record.foreign_net)">
                      {{ formatShares(record.foreign_net) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm" :class="getNetBuyColorClass(record.investment_trust_net)">
                      {{ formatShares(record.investment_trust_net) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm" :class="getNetBuyColorClass(record.dealer_net)">
                      {{ formatShares(record.dealer_net) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-bold" :class="getNetBuyColorClass(record.total_institutional_net)">
                      {{ formatShares(record.total_institutional_net) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-else-if="searchStockCode && !isSearching" class="text-center py-8 text-gray-500 dark:text-gray-400">
            查無資料
          </div>
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

// SEO 設定
useSeoMeta({
  title: '投信外資買賣超管理',
  description: '管理與查看投信外資三大法人買賣超資料'
})

// 響應式狀態
const statistics = ref({})
const completenessData = ref(null)
const stockData = ref([])
const searchStockCode = ref('')
const isLoading = ref(false)
const isUpdating = ref(false)
const isChecking = ref(false)
const isSearching = ref(false)
const isBatchUpdating = ref(false)

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
    const response = await $api('/institutional-trading/statistics')

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

// 更新最新資料
const updateLatestData = async () => {
  try {
    isUpdating.value = true
    const response = await $api('/institutional-trading/update/latest', {
      method: 'POST'
    })

    if (response.success && response.data?.status === 'success') {
      const processedCount = response.data.data?.total_processed || 0
      showNotification(`成功更新 ${processedCount} 筆資料`, 'success')
      await loadStatistics() // 重新載入統計資料
    } else {
      const errorMessage = response.error || response.data?.message || '更新失敗'
      showNotification(errorMessage, 'error')
    }
  } catch (error) {
    console.error('更新資料失敗:', error)
    showNotification('更新資料失敗', 'error')
  } finally {
    isUpdating.value = false
  }
}

// 檢查資料完整性
const checkCompleteness = async () => {
  try {
    isChecking.value = true
    const response = await $api('/institutional-trading/check/completeness?days_back=30')

    if (response.status === 'success') {
      completenessData.value = response.data
      showNotification('完整性檢查完成', 'success')
    }
  } catch (error) {
    console.error('檢查完整性失敗:', error)
    showNotification('檢查完整性失敗', 'error')
  } finally {
    isChecking.value = false
  }
}

// 批次更新近30天資料
const batchUpdate = async () => {
  try {
    isBatchUpdating.value = true
    const response = await $api('/institutional-trading/update/batch?days_back=30', {
      method: 'POST'
    })

    if (response.success && response.data?.status === 'success') {
      const summary = response.data.data?.summary || {}
      const totalProcessed = summary.total_processed || 0
      const successCount = summary.success_count || 0
      showNotification(`批次更新完成！成功處理 ${successCount} 天，共 ${totalProcessed} 筆資料`, 'success')
      await loadStatistics() // 重新載入統計資料
    } else {
      const errorMessage = response.error || response.data?.message || '批次更新失敗'
      showNotification(errorMessage, 'error')
    }
  } catch (error) {
    console.error('批次更新失敗:', error)
    showNotification('批次更新失敗', 'error')
  } finally {
    isBatchUpdating.value = false
  }
}

// 搜尋股票資料
const searchStockData = async () => {
  if (!searchStockCode.value || searchStockCode.value.length < 4) {
    showNotification('請輸入正確的股票代號', 'error')
    return
  }

  try {
    isSearching.value = true
    const response = await $api(`/institutional-trading/stock/${searchStockCode.value}?limit=30`)

    if (response.status === 'success') {
      stockData.value = response.data
      showNotification(`查詢成功，找到 ${response.total_records} 筆資料`, 'success')
    }
  } catch (error) {
    console.error('查詢股票資料失敗:', error)
    if (error.response?.status === 404) {
      showNotification('找不到該股票的買賣超資料', 'error')
    } else {
      showNotification('查詢失敗', 'error')
    }
    stockData.value = []
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

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 格式化股數
const formatShares = (shares) => {
  if (!shares) return '0'

  const num = Math.abs(shares)
  const sign = shares >= 0 ? '+' : '-'

  if (num >= 100000000) { // 1億以上
    return `${sign}${(num / 100000000).toFixed(2)}億`
  } else if (num >= 10000) { // 1萬以上
    return `${sign}${(num / 10000).toFixed(0)}萬`
  } else {
    return `${sign}${num.toLocaleString()}`
  }
}

// 獲取買賣超顏色樣式
const getNetBuyColorClass = (value) => {
  if (!value || value === 0) return 'text-gray-500 dark:text-gray-400'
  return value > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
}

// 頁面載入時執行
onMounted(() => {
  loadStatistics()
})
</script>