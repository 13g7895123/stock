<template>
  <div class="space-y-6">
    <!-- 系統狀態概覽 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          系統概覽
        </h2>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-600 dark:text-gray-300">系統運行中</span>
        </div>
      </div>
    </div>

    <!-- 核心指標 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="metric in coreMetrics"
        :key="metric.name"
        class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6 hover:shadow-md transition-shadow duration-200"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ metric.name }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white mt-2">{{ metric.value }}</p>
            <div class="flex items-center mt-2">
              <component 
                :is="metric.trend === 'up' ? ArrowUpIcon : ArrowDownIcon" 
                :class="[
                  'w-4 h-4',
                  metric.trend === 'up' ? 'text-green-500' : 'text-red-500'
                ]" 
              />
              <span 
                :class="[
                  'text-xs ml-1',
                  metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ metric.change }}
              </span>
            </div>
          </div>
          <div class="p-3 rounded-lg bg-primary-100 dark:bg-primary-900">
            <component :is="getIcon(metric.icon)" class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 資料更新狀態與任務執行 -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <!-- 資料更新狀態 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            資料更新狀態
          </h3>
          <button class="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors">
            手動更新
          </button>
        </div>
        <div class="space-y-4">
          <div
            v-for="update in updateStatus"
            :key="update.name"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  update.status === 'completed' ? 'bg-green-500' : 
                  update.status === 'running' ? 'bg-yellow-500 animate-pulse' : 'bg-gray-400'
                ]"
              ></div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ update.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ update.lastUpdate }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ update.progress }}</p>
              <div class="w-20 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full mt-1">
                <div 
                  class="h-1.5 bg-primary-500 rounded-full transition-all duration-300"
                  :style="{ width: update.progressPercent + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 今日選股結果 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            今日推薦股票
          </h3>
          <NuxtLink 
            to="/screening/recommendations"
            class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            查看全部
          </NuxtLink>
        </div>
        <div class="space-y-3">
          <div
            v-for="stock in recommendedStocks"
            :key="stock.code"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors cursor-pointer"
          >
            <div>
              <p class="text-sm font-semibold text-gray-900 dark:text-white">
                {{ stock.code }} {{ stock.name }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                評分: {{ stock.score }}/100
              </p>
            </div>
            <div class="text-right">
              <p class="text-sm font-medium text-gray-900 dark:text-white">
                ${{ stock.price }}
              </p>
              <p 
                :class="[
                  'text-xs',
                  stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ stock.change >= 0 ? '+' : '' }}{{ stock.change }}%
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系統活動日誌與效能圖表 -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <!-- 效能監控圖表 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          系統效能監控
        </h3>
        <div class="h-64 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-700 dark:to-gray-600 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <PresentationChartLineIcon class="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p class="text-gray-500 dark:text-gray-400 text-sm">效能圖表區域</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">(可整合Chart.js或其他圖表庫)</p>
          </div>
        </div>
      </div>

      <!-- 系統活動日誌 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            系統活動
          </h3>
          <NuxtLink 
            to="/tasks/logs"
            class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            查看詳細日誌
          </NuxtLink>
        </div>
        <div class="space-y-4 max-h-64 overflow-y-auto">
          <div
            v-for="activity in systemActivities"
            :key="activity.id"
            class="flex items-start space-x-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <div 
              :class="[
                'w-2 h-2 mt-2 rounded-full flex-shrink-0',
                activity.type === 'success' ? 'bg-green-500' :
                activity.type === 'warning' ? 'bg-yellow-500' :
                activity.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
              ]"
            ></div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-900 dark:text-white">{{ activity.message }}</p>
              <div class="flex items-center mt-1 space-x-2">
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ activity.time }}</p>
                <span 
                  v-if="activity.duration"
                  class="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-full"
                >
                  {{ activity.duration }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作面板 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        快速操作
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <button
          v-for="action in quickActions"
          :key="action.name"
          class="flex flex-col items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
        >
          <component 
            :is="getIcon(action.icon)" 
            class="w-8 h-8 text-gray-600 dark:text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 mb-2" 
          />
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300 text-center">
            {{ action.name }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  BuildingOfficeIcon,
  CircleStackIcon,
  PresentationChartLineIcon,
  StarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '系統概覽'
})

// 核心指標數據
const coreMetrics = ref([
  { 
    name: '股票總數', 
    value: '1,847', 
    change: '+23',
    trend: 'up',
    icon: 'BuildingOfficeIcon' 
  },
  { 
    name: '資料完整度', 
    value: '98.7%', 
    change: '+1.2%',
    trend: 'up',
    icon: 'CircleStackIcon' 
  },
  { 
    name: '推薦股票', 
    value: '156', 
    change: '-5',
    trend: 'down',
    icon: 'StarIcon' 
  },
  { 
    name: '系統負載', 
    value: '23%', 
    change: '-8%',
    trend: 'down',
    icon: 'ChartBarIcon' 
  }
])

// 資料更新狀態
const updateStatus = ref([
  {
    name: '股票清單更新',
    status: 'completed',
    lastUpdate: '2小時前',
    progress: '完成',
    progressPercent: 100
  },
  {
    name: '歷史資料同步',
    status: 'running',
    lastUpdate: '進行中',
    progress: '67%',
    progressPercent: 67
  },
  {
    name: '均線計算',
    status: 'pending',
    lastUpdate: '等待中',
    progress: '待執行',
    progressPercent: 0
  }
])

// 推薦股票
const recommendedStocks = ref([
  { code: '2330', name: '台積電', price: '512.00', change: 2.1, score: 85 },
  { code: '2317', name: '鴻海', price: '106.50', change: -1.2, score: 78 },
  { code: '2454', name: '聯發科', price: '789.00', change: 3.8, score: 82 },
  { code: '1301', name: '台塑', price: '87.20', change: 1.5, score: 75 }
])

// 系統活動
const systemActivities = ref([
  {
    id: 1,
    message: '股票清單更新完成，新增23檔股票',
    time: '2分鐘前',
    type: 'success',
    duration: '45秒'
  },
  {
    id: 2,
    message: '技術分析計算完成，發現156檔推薦股票',
    time: '15分鐘前',
    type: 'success',
    duration: '3分鐘'
  },
  {
    id: 3,
    message: '資料源連接異常，正在重試',
    time: '1小時前',
    type: 'warning'
  },
  {
    id: 4,
    message: '定時任務啟動：每日資料更新',
    time: '2小時前',
    type: 'info',
    duration: '120分鐘'
  }
])

// 快速操作
const quickActions = ref([
  { name: '更新股票', icon: 'ArrowPathIcon' },
  { name: '執行分析', icon: 'PlayIcon' },
  { name: '停止任務', icon: 'StopIcon' },
  { name: '系統設定', icon: 'Cog6ToothIcon' },
  { name: '查看報告', icon: 'ChartBarIcon' },
  { name: '排程管理', icon: 'ClockIcon' }
])

// 圖示組件映射
const iconComponents = {
  BuildingOfficeIcon,
  CircleStackIcon,
  PresentationChartLineIcon,
  StarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  ClockIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || ChartBarIcon
}
</script>