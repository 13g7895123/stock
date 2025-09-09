<template>
  <div class="space-y-6">
    <!-- 頁面標題與操作 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">股票推薦</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">
            基於技術分析篩選出的優質股票，按推薦度排序
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
            <ClockIcon class="w-4 h-4" />
            <span>最後更新：{{ lastUpdateTime }}</span>
          </div>
          <button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2">
            <ArrowPathIcon class="w-4 h-4" />
            <span>重新篩選</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 篩選統計 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div
        v-for="stat in screeningStats"
        :key="stat.name"
        class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6"
      >
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-primary-100 dark:bg-primary-900">
            <component :is="getIcon(stat.icon)" class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ stat.name }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 篩選條件與排序 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div class="flex flex-wrap items-center gap-4">
          <!-- 評分範圍 -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">評分範圍：</label>
            <select
              v-model="scoreRange"
              class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">全部</option>
              <option value="excellent">優秀 (80+)</option>
              <option value="good">良好 (60-79)</option>
              <option value="average">普通 (<60)</option>
            </select>
          </div>

          <!-- 風險等級 -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">風險等級：</label>
            <select
              v-model="riskLevel"
              class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">全部</option>
              <option value="low">低風險</option>
              <option value="medium">中風險</option>
              <option value="high">高風險</option>
            </select>
          </div>
        </div>

        <div class="flex items-center space-x-4">
          <!-- 排序方式 -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">排序：</label>
            <select
              v-model="sortBy"
              class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="score">評分</option>
              <option value="price">股價</option>
              <option value="change">漲跌幅</option>
              <option value="volume">成交量</option>
            </select>
          </div>

          <!-- 檢視模式 -->
          <div class="flex items-center border border-gray-300 dark:border-gray-600 rounded">
            <button
              @click="viewMode = 'grid'"
              :class="[
                'px-3 py-1 text-sm',
                viewMode === 'grid' 
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              ]"
            >
              卡片
            </button>
            <button
              @click="viewMode = 'table'"
              :class="[
                'px-3 py-1 text-sm border-l border-gray-300 dark:border-gray-600',
                viewMode === 'table' 
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              ]"
            >
              列表
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 推薦股票 - 卡片視圖 -->
    <div v-if="viewMode === 'grid'" class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="stock in filteredStocks"
        :key="stock.code"
        class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden"
      >
        <!-- 卡片頭部 -->
        <div class="p-6 pb-4">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ stock.code }} {{ stock.name }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-400">{{ stock.industry }}</p>
            </div>
            <div class="text-right">
              <div class="flex items-center space-x-1 mb-1">
                <StarIcon class="w-4 h-4 text-yellow-500" />
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ stock.score }}</span>
              </div>
              <span 
                class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                :class="{
                  'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': stock.riskLevel === 'low',
                  'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': stock.riskLevel === 'medium',
                  'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': stock.riskLevel === 'high'
                }"
              >
                {{ 
                  stock.riskLevel === 'low' ? '低風險' :
                  stock.riskLevel === 'medium' ? '中風險' : '高風險'
                }}
              </span>
            </div>
          </div>

          <!-- 價格資訊 -->
          <div class="flex items-center justify-between mb-4">
            <div>
              <span class="text-2xl font-bold text-gray-900 dark:text-white">${{ stock.price }}</span>
              <span 
                :class="[
                  'ml-2 text-sm font-medium',
                  stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ stock.change >= 0 ? '+' : '' }}{{ stock.change }}%
              </span>
            </div>
            <div class="text-right text-sm text-gray-600 dark:text-gray-400">
              <div>成交量: {{ stock.volume }}</div>
              <div>市值: {{ stock.marketCap }}</div>
            </div>
          </div>
        </div>

        <!-- 技術指標 -->
        <div class="px-6 pb-4">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">技術指標</h4>
          <div class="grid grid-cols-2 gap-3">
            <div
              v-for="indicator in stock.technicalIndicators"
              :key="indicator.name"
              class="bg-gray-50 dark:bg-gray-700 rounded p-2"
            >
              <div class="text-xs text-gray-600 dark:text-gray-400">{{ indicator.name }}</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">{{ indicator.value }}</div>
              <div 
                :class="[
                  'text-xs',
                  indicator.signal === 'buy' ? 'text-green-600' :
                  indicator.signal === 'sell' ? 'text-red-600' : 'text-gray-600'
                ]"
              >
                {{ 
                  indicator.signal === 'buy' ? '買進' :
                  indicator.signal === 'sell' ? '賣出' : '持有'
                }}
              </div>
            </div>
          </div>
        </div>

        <!-- 推薦理由 -->
        <div class="px-6 pb-6">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">推薦理由</h4>
          <ul class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
            <li v-for="reason in stock.reasons" :key="reason">• {{ reason }}</li>
          </ul>
        </div>

        <!-- 操作按鈕 -->
        <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700 flex items-center justify-between">
          <button class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium">
            查看詳情
          </button>
          <div class="flex items-center space-x-2">
            <button class="p-2 text-gray-400 hover:text-yellow-500">
              <StarIcon class="w-4 h-4" />
            </button>
            <button class="p-2 text-gray-400 hover:text-gray-600">
              <ShareIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 推薦股票 - 表格視圖 -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                排名
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                股票
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                評分
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                價格
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                漲跌幅
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                風險等級
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                主要訊號
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="(stock, index) in filteredStocks"
              :key="stock.code"
              class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <td class="px-6 py-4">
                <div class="flex items-center space-x-2">
                  <span class="text-lg font-bold text-primary-600">{{ index + 1 }}</span>
                  <TrophyIcon 
                    v-if="index < 3"
                    :class="[
                      'w-4 h-4',
                      index === 0 ? 'text-yellow-500' :
                      index === 1 ? 'text-gray-400' : 'text-amber-600'
                    ]"
                  />
                </div>
              </td>
              <td class="px-6 py-4">
                <div>
                  <div class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ stock.code }} {{ stock.name }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">{{ stock.industry }}</div>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center space-x-1">
                  <StarIcon class="w-4 h-4 text-yellow-500" />
                  <span class="text-sm font-medium">{{ stock.score }}</span>
                </div>
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
                <span 
                  class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                  :class="{
                    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': stock.riskLevel === 'low',
                    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': stock.riskLevel === 'medium',
                    'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': stock.riskLevel === 'high'
                  }"
                >
                  {{ 
                    stock.riskLevel === 'low' ? '低風險' :
                    stock.riskLevel === 'medium' ? '中風險' : '高風險'
                  }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center space-x-2">
                  <span
                    v-for="signal in stock.mainSignals"
                    :key="signal"
                    class="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded"
                  >
                    {{ signal }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button class="p-1 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400">
                    <EyeIcon class="w-4 h-4" />
                  </button>
                  <button class="p-1 text-gray-400 hover:text-yellow-500">
                    <StarIcon class="w-4 h-4" />
                  </button>
                  <button class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    <ShareIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  ClockIcon,
  StarIcon,
  TrophyIcon,
  ShareIcon,
  EyeIcon,
  FunnelIcon,
  ChartBarIcon,
  BuildingOfficeIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '股票推薦'
})

// 響應式資料
const viewMode = ref('grid')
const scoreRange = ref('all')
const riskLevel = ref('all')
const sortBy = ref('score')
const lastUpdateTime = ref('30分鐘前')

// 篩選統計
const screeningStats = ref([
  { name: '總篩選股票', value: '156', icon: 'BuildingOfficeIcon' },
  { name: '優秀評分', value: '42', icon: 'StarIcon' },
  { name: '買進訊號', value: '89', icon: 'ArrowPathIcon' },
  { name: '低風險', value: '67', icon: 'ChartBarIcon' }
])

// 模擬推薦股票資料
const recommendedStocks = ref([
  {
    code: '2330',
    name: '台積電',
    industry: '半導體',
    price: 512.00,
    change: 2.1,
    score: 87,
    riskLevel: 'low',
    volume: '28,456K',
    marketCap: '13.2T',
    technicalIndicators: [
      { name: 'RSI', value: '65.2', signal: 'buy' },
      { name: 'MACD', value: '0.85', signal: 'buy' },
      { name: 'KD', value: '78.3', signal: 'hold' },
      { name: 'MA20', value: '508.5', signal: 'buy' }
    ],
    mainSignals: ['均線多頭', 'RSI強勢'],
    reasons: [
      '20日均線呈現多頭排列',
      'RSI指標顯示強勢但未超買',
      'MACD出現黃金交叉',
      '成交量溫和放大'
    ]
  },
  {
    code: '2454',
    name: '聯發科',
    industry: '半導體',
    price: 789.00,
    change: 3.8,
    score: 82,
    riskLevel: 'medium',
    volume: '15,234K',
    marketCap: '1.26T',
    technicalIndicators: [
      { name: 'RSI', value: '58.7', signal: 'hold' },
      { name: 'MACD', value: '1.23', signal: 'buy' },
      { name: 'KD', value: '82.1', signal: 'sell' },
      { name: 'MA20', value: '765.2', signal: 'buy' }
    ],
    mainSignals: ['MACD買進', '突破壓力'],
    reasons: [
      'MACD指標轉為正值',
      '成功突破前期壓力位',
      '法人連續買超',
      '獲利成長動能強勁'
    ]
  }
])

// 計算屬性
const filteredStocks = computed(() => {
  let result = [...recommendedStocks.value]

  // 評分篩選
  if (scoreRange.value !== 'all') {
    result = result.filter(stock => {
      if (scoreRange.value === 'excellent') return stock.score >= 80
      if (scoreRange.value === 'good') return stock.score >= 60 && stock.score < 80
      if (scoreRange.value === 'average') return stock.score < 60
    })
  }

  // 風險等級篩選
  if (riskLevel.value !== 'all') {
    result = result.filter(stock => stock.riskLevel === riskLevel.value)
  }

  // 排序
  result.sort((a, b) => {
    if (sortBy.value === 'score') return b.score - a.score
    if (sortBy.value === 'price') return b.price - a.price
    if (sortBy.value === 'change') return b.change - a.change
    return 0
  })

  return result
})

// 圖示組件映射
const iconComponents = {
  BuildingOfficeIcon,
  StarIcon,
  ArrowPathIcon,
  ChartBarIcon,
  FunnelIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || ChartBarIcon
}
</script>