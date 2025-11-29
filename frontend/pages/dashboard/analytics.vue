<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        數據分析報告
      </h2>
      <button 
        @click="refreshData"
        class="flex items-center px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
      >
        <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': loading }" />
        重新整理
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 產業分佈圖 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          股票產業分佈 (Top 10)
        </h3>
        <div class="relative h-64 w-full">
          <canvas id="industryChart"></canvas>
        </div>
      </div>

      <!-- 市場分佈 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場分佈 (上市 vs 上櫃)
        </h3>
        <div class="relative h-64 w-full flex justify-center">
          <canvas id="marketChart"></canvas>
        </div>
      </div>
    </div>

    <!-- 統計數據卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">總股票數</p>
        <p class="text-3xl font-bold text-gray-900 dark:text-white mt-2">{{ stats.total }}</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">上市股票</p>
        <p class="text-3xl font-bold text-blue-600 mt-2">{{ stats.tse }}</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">上櫃股票</p>
        <p class="text-3xl font-bold text-green-600 mt-2">{{ stats.otc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import Chart from 'chart.js/auto'

definePageMeta({
  title: '數據分析'
})

const { getStockList } = useStocks()
const loading = ref(false)
const stats = ref({
  total: 0,
  tse: 0,
  otc: 0
})

let industryChartInstance = null
let marketChartInstance = null

const refreshData = async () => {
  loading.value = true
  try {
    // 獲取所有股票 (limit 設大一點以獲取足夠樣本，或分頁獲取全部)
    // 這裡為了演示，先獲取前 2000 筆
    const res = await getStockList({ limit: 2000 })
    if (res && res.stocks) {
      processData(res.stocks)
    }
  } catch (e) {
    console.error('Failed to fetch analytics data:', e)
  } finally {
    loading.value = false
  }
}

const processData = (stocks) => {
  // 1. 計算基本統計
  stats.value.total = stocks.length
  stats.value.tse = stocks.filter(s => s.market === 'TSE' || s.market === '上市').length
  stats.value.otc = stocks.filter(s => s.market === 'OTC' || s.market === '上櫃' || s.market === 'TPEx').length

  // 2. 計算產業分佈
  const industryCounts = {}
  stocks.forEach(s => {
    const ind = s.industry || '其他'
    industryCounts[ind] = (industryCounts[ind] || 0) + 1
  })

  // 排序並取前 10
  const sortedIndustries = Object.entries(industryCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  renderCharts(sortedIndustries)
}

const renderCharts = (topIndustries) => {
  // 銷毀舊圖表
  if (industryChartInstance) industryChartInstance.destroy()
  if (marketChartInstance) marketChartInstance.destroy()

  // 產業長條圖
  const ctxIndustry = document.getElementById('industryChart')
  if (ctxIndustry) {
    industryChartInstance = new Chart(ctxIndustry, {
      type: 'bar',
      data: {
        labels: topIndustries.map(i => i[0]),
        datasets: [{
          label: '股票數量',
          data: topIndustries.map(i => i[1]),
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        }
      }
    })
  }

  // 市場圓餅圖
  const ctxMarket = document.getElementById('marketChart')
  if (ctxMarket) {
    marketChartInstance = new Chart(ctxMarket, {
      type: 'doughnut',
      data: {
        labels: ['上市', '上櫃'],
        datasets: [{
          data: [stats.value.tse, stats.value.otc],
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    })
  }
}

onMounted(() => {
  refreshData()
})
</script>