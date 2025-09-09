<template>
  <div class="space-y-6">
    <!-- 頁面標題與操作 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">定時任務管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">
            管理系統自動執行的定時任務，包括資料更新、分析計算等
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <button class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
            <PlayIcon class="w-4 h-4" />
            <span>啟動全部</span>
          </button>
          <button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2">
            <PlusIcon class="w-4 h-4" />
            <span>新增任務</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 任務狀態統計 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div
        v-for="stat in taskStats"
        :key="stat.name"
        class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6"
      >
        <div class="flex items-center">
          <div 
            class="p-3 rounded-lg"
            :class="stat.bgColor"
          >
            <component :is="getIcon(stat.icon)" :class="['w-6 h-6', stat.iconColor]" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ stat.name }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 任務列表 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <!-- 列表標題 -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            定時任務 ({{ tasks.length }})
          </h3>
          <div class="flex items-center space-x-2">
            <button class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700">
              篩選
            </button>
            <button class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700">
              匯出
            </button>
          </div>
        </div>
      </div>

      <!-- 任務卡片列表 -->
      <div class="p-6">
        <div class="space-y-4">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow duration-200"
          >
            <div class="flex items-start justify-between">
              <!-- 任務基本資訊 -->
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-3">
                  <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ task.name }}
                  </h4>
                  <span 
                    class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                    :class="{
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': task.status === 'active',
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': task.status === 'stopped',
                      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': task.status === 'running'
                    }"
                  >
                    {{ 
                      task.status === 'active' ? '啟用中' :
                      task.status === 'stopped' ? '已停止' : '執行中'
                    }}
                  </span>
                </div>
                
                <p class="text-gray-600 dark:text-gray-400 mb-4">{{ task.description }}</p>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  <!-- 執行週期 -->
                  <div class="flex items-center space-x-2">
                    <ClockIcon class="w-4 h-4 text-gray-400" />
                    <div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">執行週期</div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ task.schedule }}</div>
                    </div>
                  </div>

                  <!-- 下次執行 -->
                  <div class="flex items-center space-x-2">
                    <CalendarIcon class="w-4 h-4 text-gray-400" />
                    <div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">下次執行</div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ task.nextRun }}</div>
                    </div>
                  </div>

                  <!-- 上次執行 -->
                  <div class="flex items-center space-x-2">
                    <CheckCircleIcon class="w-4 h-4 text-gray-400" />
                    <div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">上次執行</div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ task.lastRun }}</div>
                    </div>
                  </div>

                  <!-- 執行時長 -->
                  <div class="flex items-center space-x-2">
                    <ClockIcon class="w-4 h-4 text-gray-400" />
                    <div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">平均時長</div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ task.avgDuration }}</div>
                    </div>
                  </div>
                </div>

                <!-- 執行統計 -->
                <div class="flex items-center space-x-6 text-sm">
                  <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-gray-600 dark:text-gray-400">成功: {{ task.successCount }}</span>
                  </div>
                  <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span class="text-gray-600 dark:text-gray-400">失敗: {{ task.failureCount }}</span>
                  </div>
                  <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span class="text-gray-600 dark:text-gray-400">總執行: {{ task.totalRuns }}</span>
                  </div>
                </div>
              </div>

              <!-- 任務操作按鈕 -->
              <div class="flex items-center space-x-2 ml-6">
                <button
                  v-if="task.status === 'active'"
                  @click="pauseTask(task.id)"
                  class="p-2 text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
                  title="暫停任務"
                >
                  <PauseIcon class="w-4 h-4" />
                </button>
                <button
                  v-else
                  @click="startTask(task.id)"
                  class="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                  title="啟動任務"
                >
                  <PlayIcon class="w-4 h-4" />
                </button>

                <button
                  @click="runTaskNow(task.id)"
                  class="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                  title="立即執行"
                >
                  <BoltIcon class="w-4 h-4" />
                </button>

                <button
                  class="p-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="查看日誌"
                >
                  <DocumentTextIcon class="w-4 h-4" />
                </button>

                <button
                  class="p-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="編輯任務"
                >
                  <PencilIcon class="w-4 h-4" />
                </button>

                <div class="relative">
                  <button
                    class="p-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title="更多操作"
                  >
                    <EllipsisVerticalIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <!-- 任務進度條 (僅在執行中顯示) -->
            <div v-if="task.status === 'running' && task.progress" class="mt-4">
              <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                <span>{{ task.progress.currentStep }}</span>
                <span>{{ task.progress.percent }}%</span>
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  class="bg-primary-500 h-2 rounded-full transition-all duration-300"
                  :style="{ width: task.progress.percent + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任務創建/編輯對話框 (可選實現) -->
    <!-- <TaskDialog v-if="showTaskDialog" @close="showTaskDialog = false" /> -->
  </div>
</template>

<script setup>
import {
  PlusIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  BoltIcon,
  ClockIcon,
  CalendarIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  PencilIcon,
  EllipsisVerticalIcon,
  ExclamationTriangleIcon,
  CheckIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '定時任務管理'
})

// 任務統計
const taskStats = ref([
  { 
    name: '運行中', 
    value: '3', 
    icon: 'PlayIcon',
    bgColor: 'bg-green-100 dark:bg-green-900',
    iconColor: 'text-green-600 dark:text-green-400'
  },
  { 
    name: '已停止', 
    value: '2', 
    icon: 'PauseIcon',
    bgColor: 'bg-red-100 dark:bg-red-900',
    iconColor: 'text-red-600 dark:text-red-400'
  },
  { 
    name: '成功率', 
    value: '98.5%', 
    icon: 'CheckIcon',
    bgColor: 'bg-blue-100 dark:bg-blue-900',
    iconColor: 'text-blue-600 dark:text-blue-400'
  },
  { 
    name: '異常任務', 
    value: '1', 
    icon: 'ExclamationTriangleIcon',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900',
    iconColor: 'text-yellow-600 dark:text-yellow-400'
  }
])

// 模擬任務資料
const tasks = ref([
  {
    id: 1,
    name: '每日股票清單更新',
    description: '從證交所API獲取最新的股票清單，包括新上市、下市、更名等變更',
    status: 'active',
    schedule: '每日 06:00',
    nextRun: '明日 06:00',
    lastRun: '今日 06:00 (成功)',
    avgDuration: '2分45秒',
    successCount: 127,
    failureCount: 2,
    totalRuns: 129
  },
  {
    id: 2,
    name: '歷史股價資料同步',
    description: '同步所有股票的日線資料，包括開盤、收盤、最高、最低價格及成交量',
    status: 'running',
    schedule: '每日 07:00',
    nextRun: '明日 07:00',
    lastRun: '今日 07:00 (執行中)',
    avgDuration: '45分12秒',
    successCount: 125,
    failureCount: 1,
    totalRuns: 126,
    progress: {
      currentStep: '正在處理第 1,250 / 1,847 檔股票',
      percent: 67
    }
  },
  {
    id: 3,
    name: '技術指標計算',
    description: '計算所有股票的均線、RSI、MACD等技術指標，為選股分析提供基礎資料',
    status: 'active',
    schedule: '每日 08:00',
    nextRun: '明日 08:00',
    lastRun: '今日 08:00 (成功)',
    avgDuration: '15分30秒',
    successCount: 98,
    failureCount: 0,
    totalRuns: 98
  },
  {
    id: 4,
    name: '股票篩選分析',
    description: '根據預設條件篩選出符合技術分析條件的推薦股票',
    status: 'active',
    schedule: '每日 09:00',
    nextRun: '明日 09:00',
    lastRun: '今日 09:00 (成功)',
    avgDuration: '8分20秒',
    successCount: 87,
    failureCount: 1,
    totalRuns: 88
  },
  {
    id: 5,
    name: '系統資料備份',
    description: '備份重要的股票資料和分析結果到外部儲存系統',
    status: 'stopped',
    schedule: '每日 23:00',
    nextRun: '已停止',
    lastRun: '3天前 (失敗)',
    avgDuration: '12分15秒',
    successCount: 45,
    failureCount: 3,
    totalRuns: 48
  }
])

// 任務操作方法
const startTask = (taskId) => {
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    task.status = 'active'
    // 實際應用中這裡會調用API
    console.log(`啟動任務: ${task.name}`)
  }
}

const pauseTask = (taskId) => {
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    task.status = 'stopped'
    // 實際應用中這裡會調用API
    console.log(`暫停任務: ${task.name}`)
  }
}

const runTaskNow = (taskId) => {
  const task = tasks.value.find(t => t.id === taskId)
  if (task) {
    task.status = 'running'
    // 實際應用中這裡會調用API
    console.log(`立即執行任務: ${task.name}`)
    
    // 模擬執行過程
    setTimeout(() => {
      if (task.status === 'running') {
        task.status = 'active'
        task.lastRun = '剛才 (成功)'
        task.successCount++
        task.totalRuns++
      }
    }, 5000)
  }
}

// 圖示組件映射
const iconComponents = {
  PlayIcon,
  PauseIcon,
  StopIcon,
  CheckIcon,
  ExclamationTriangleIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || PlayIcon
}
</script>