<template>
  <div class="space-y-6">
    <!-- 頁面標題與操作 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">手動執行任務</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">
            監控和管理手動觸發的任務，包括資料更新、爬蟲作業等
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton 
            @click="refreshTasks"
            :loading="loading"
            :icon="ArrowPathIcon"
            text="重新整理"
            variant="secondary"
          />
          <ActionButton 
            @click="handleClearCompleted"
            :icon="TrashIcon"
            text="清除完成"
            variant="danger"
            :disabled="!hasCompletedTasks"
          />
        </div>
      </div>
    </div>

    <!-- 任務統計 -->
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
            <component :is="stat.icon" :class="['w-6 h-6', stat.iconColor]" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ stat.name }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 執行中的任務 -->
    <div v-if="runningTasks.length > 0" class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        執行中的任務 ({{ runningTasks.length }})
      </h3>
      <div class="space-y-4">
        <div
          v-for="task in runningTasks"
          :key="task.id"
          class="border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-2">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ task.name }}
                </h4>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  執行中
                </span>
              </div>
              <p class="text-gray-600 dark:text-gray-400 mb-3">{{ task.description }}</p>
              
              <!-- 執行資訊 -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">開始時間:</span>
                  <span class="ml-2 font-medium">{{ task.startTime }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">執行時間:</span>
                  <span class="ml-2 font-medium">{{ task.executionTime }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">預估剩餘:</span>
                  <span class="ml-2 font-medium">{{ task.estimatedRemaining }}</span>
                </div>
              </div>
            </div>
            <ActionButton 
              @click="handleCancelTask(task.id)"
              :icon="XMarkIcon"
              text="取消"
              variant="danger"
              size="sm"
            />
          </div>

          <!-- 進度條 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">{{ task.currentStep }}</span>
              <span class="font-medium">{{ task.progress.current }}/{{ task.progress.total }} ({{ task.progress.percent }}%)</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                :style="{ width: task.progress.percent + '%' }"
              ></div>
            </div>
          </div>

          <!-- 最近處理的項目 -->
          <div v-if="task.recentItems && task.recentItems.length > 0" class="mt-4">
            <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">最近處理:</h5>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="item in task.recentItems"
                :key="item"
                class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
              >
                {{ item }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 執行記錄 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            執行記錄 ({{ taskHistory.length }})
          </h3>
          <div class="flex items-center space-x-2">
            <select 
              v-model="statusFilter"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
            >
              <option value="">全部狀態</option>
              <option value="completed">已完成</option>
              <option value="failed">失敗</option>
              <option value="cancelled">已取消</option>
            </select>
            <select 
              v-model="typeFilter"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
            >
              <option value="">全部類型</option>
              <option value="data_update">資料更新</option>
              <option value="stock_crawl">股票爬蟲</option>
              <option value="analysis">技術分析</option>
            </select>
          </div>
        </div>
      </div>

      <div class="divide-y divide-gray-200 dark:divide-gray-700">
        <div
          v-for="record in filteredHistory"
          :key="record.id"
          class="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-2">
                <h4 class="text-lg font-medium text-gray-900 dark:text-white">
                  {{ record.name }}
                </h4>
                <span 
                  class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                  :class="{
                    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': record.status === 'completed',
                    'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': record.status === 'failed',
                    'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200': record.status === 'cancelled'
                  }"
                >
                  {{ getStatusText(record.status) }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ record.taskType }}
                </span>
              </div>
              
              <p class="text-gray-600 dark:text-gray-400 mb-3">{{ record.description }}</p>
              
              <!-- 執行結果 -->
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm mb-3">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">執行時間:</span>
                  <span class="ml-2 font-medium">{{ record.executionTime }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">處理數量:</span>
                  <span class="ml-2 font-medium">{{ record.processedCount }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">成功/失敗:</span>
                  <span class="ml-2 font-medium text-green-600">{{ record.successCount }}</span>
                  <span class="mx-1">/</span>
                  <span class="font-medium text-red-600">{{ record.failureCount }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">開始時間:</span>
                  <span class="ml-2 font-medium">{{ record.startTime }}</span>
                </div>
              </div>

              <!-- 錯誤訊息 -->
              <div v-if="record.status === 'failed' && record.errorMessage" class="mt-2">
                <details class="text-sm">
                  <summary class="cursor-pointer text-red-600 dark:text-red-400">錯誤詳情</summary>
                  <div class="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-300">
                    {{ record.errorMessage }}
                  </div>
                </details>
              </div>
            </div>

            <div class="flex items-center space-x-2 ml-4">
              <ActionButton 
                @click="viewTaskDetails(record.id)"
                :icon="EyeIcon"
                text="詳情"
                variant="secondary"
                size="sm"
              />
              <ActionButton 
                v-if="record.status === 'failed'"
                @click="retryTask(record.id)"
                :icon="ArrowPathIcon"
                text="重試"
                variant="primary"
                size="sm"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 分頁 -->
      <div v-if="taskHistory.length === 0" class="p-12 text-center">
        <DocumentTextIcon class="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">暫無執行記錄</h3>
        <p class="text-gray-600 dark:text-gray-400">當您開始執行任務時，記錄會顯示在這裡</p>
      </div>
    </div>

    <!-- 任務詳情模態框 -->
    <div v-if="selectedTask" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 overflow-y-auto flex items-center justify-center p-4">
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <!-- 模態框標題 -->
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">任務執行詳情</h3>
          <button 
            @click="closeTaskDetails"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon class="w-6 h-6" />
          </button>
        </div>

        <!-- 模態框內容 -->
        <div class="px-6 py-4 space-y-6">
          <!-- 基本資訊 -->
          <div>
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">基本資訊</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">任務名稱:</span>
                  <span class="ml-2 font-medium">{{ selectedTask.name }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">任務類型:</span>
                  <span class="ml-2 font-medium">{{ selectedTask.type }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">執行狀態:</span>
                  <span 
                    class="ml-2 inline-flex px-2 py-1 text-xs font-medium rounded-full"
                    :class="{
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': selectedTask.status === 'completed',
                      'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200': selectedTask.status === 'running',
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': selectedTask.status === 'failed',
                      'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200': selectedTask.status === 'cancelled'
                    }"
                  >
                    {{ getStatusText(selectedTask.status) }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">任務ID:</span>
                  <span class="ml-2 font-mono text-sm">{{ selectedTask.id }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 執行時間資訊 -->
          <div>
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">執行時間</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">開始時間:</span>
                  <span class="ml-2 font-medium">{{ formatDateTime(selectedTask.startTime) }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">結束時間:</span>
                  <span class="ml-2 font-medium">{{ selectedTask.endTime ? formatDateTime(selectedTask.endTime) : '執行中' }}</span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">執行時長:</span>
                  <span class="ml-2 font-medium">{{ formatDuration(selectedTask.duration) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 執行進度 -->
          <div>
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">執行進度</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div class="space-y-3">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400">總進度</span>
                  <span class="font-medium">{{ selectedTask.processedCount }}/{{ selectedTask.totalCount }} ({{ selectedTask.progress }}%)</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                  <div 
                    class="bg-blue-500 h-3 rounded-full transition-all duration-300"
                    :style="{ width: selectedTask.progress + '%' }"
                  ></div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mt-4">
                  <div>
                    <span class="text-gray-500 dark:text-gray-400">處理總數:</span>
                    <span class="ml-2 font-medium">{{ selectedTask.processedCount }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500 dark:text-gray-400">成功數量:</span>
                    <span class="ml-2 font-medium text-green-600">{{ selectedTask.successCount }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500 dark:text-gray-400">錯誤數量:</span>
                    <span class="ml-2 font-medium text-red-600">{{ selectedTask.errorCount }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 執行結果 -->
          <div v-if="selectedTask.resultSummary">
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">執行結果</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p class="text-sm text-gray-700 dark:text-gray-300">{{ selectedTask.resultSummary }}</p>
            </div>
          </div>

          <!-- 執行參數 -->
          <div v-if="selectedTask.parameters">
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">執行參數</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <pre class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ formatParameters(selectedTask.parameters) }}</pre>
            </div>
          </div>

          <!-- 錯誤訊息 -->
          <div v-if="selectedTask.errorMessage">
            <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-3">錯誤訊息</h4>
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p class="text-sm text-red-700 dark:text-red-300">{{ selectedTask.errorMessage }}</p>
            </div>
          </div>
        </div>

        <!-- 模態框底部 -->
        <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end space-x-3">
          <ActionButton 
            @click="closeTaskDetails"
            text="關閉"
            variant="secondary"
          />
          <ActionButton 
            v-if="selectedTask.status === 'failed'"
            @click="retryTask(selectedTask.id)"
            :icon="ArrowPathIcon"
            text="重新執行"
            variant="primary"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowPathIcon,
  TrashIcon,
  XMarkIcon,
  EyeIcon,
  DocumentTextIcon,
  PlayIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '手動執行任務'
})

// 使用任務管理API
const {
  runningTasks,
  taskHistory,
  loading,
  error,
  getManualTasks,
  cancelTask,
  clearCompletedTasks,
  getTaskDetails,
  startTaskPolling
} = useTasks()

// 使用API組合式函數
const { get } = useApi()

// 任務統計資料
const taskStatistics = ref({
  total_tasks: 0,
  running_count: 0,
  completed_count: 0,
  failed_count: 0,
  cancelled_count: 0,
  success_rate: 0,
  average_duration: 0
})

// 響應式資料
const statusFilter = ref('')
const typeFilter = ref('')
const pollCleanup = ref(null)
const selectedTask = ref(null)

// 計算任務統計
const taskStats = computed(() => [
  { 
    name: '執行中', 
    value: taskStatistics.value.running_count || runningTasks.value.length, 
    icon: PlayIcon,
    bgColor: 'bg-blue-100 dark:bg-blue-900',
    iconColor: 'text-blue-600 dark:text-blue-400'
  },
  { 
    name: '已完成', 
    value: taskStatistics.value.completed_count || taskHistory.value.filter(t => t.status === 'completed').length, 
    icon: CheckCircleIcon,
    bgColor: 'bg-green-100 dark:bg-green-900',
    iconColor: 'text-green-600 dark:text-green-400'
  },
  { 
    name: '失敗任務', 
    value: taskStatistics.value.failed_count || taskHistory.value.filter(t => t.status === 'failed').length, 
    icon: ExclamationCircleIcon,
    bgColor: 'bg-red-100 dark:bg-red-900',
    iconColor: 'text-red-600 dark:text-red-400'
  },
  { 
    name: '平均時長', 
    value: formatDuration(taskStatistics.value.average_duration), 
    icon: ClockIcon,
    bgColor: 'bg-gray-100 dark:bg-gray-900',
    iconColor: 'text-gray-600 dark:text-gray-400'
  }
])

// 過濾後的歷史記錄
const filteredHistory = computed(() => {
  let filtered = taskHistory.value
  
  if (statusFilter.value) {
    filtered = filtered.filter(task => task.status === statusFilter.value)
  }
  
  if (typeFilter.value) {
    filtered = filtered.filter(task => task.taskType === typeFilter.value)
  }
  
  return filtered
})

// 是否有已完成的任務
const hasCompletedTasks = computed(() => 
  taskHistory.value.some(task => task.status === 'completed')
)

// 輔助函數
const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '0秒'
  
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分`
  } else {
    const hours = Math.floor(seconds / 3600)
    const remainingMinutes = Math.floor((seconds % 3600) / 60)
    return remainingMinutes > 0 ? `${hours}時${remainingMinutes}分` : `${hours}時`
  }
}

// 獲取統計資料
const getTaskStatistics = async () => {
  try {
    const result = await get('/task-execution/statistics')
    if (result.success && result.statistics) {
      taskStatistics.value = result.statistics
      console.log('✅ 任務統計資料更新完成:', taskStatistics.value)
    } else {
      console.error('❌ 獲取任務統計失敗:', result)
    }
  } catch (error) {
    console.error('獲取任務統計失敗:', error)
  }
}

// 方法
const refreshTasks = async () => {
  await Promise.all([
    getManualTasks(),
    getTaskStatistics()
  ])
}

const handleClearCompleted = async () => {
  await clearCompletedTasks()
}

const handleCancelTask = async (taskId) => {
  await cancelTask(taskId)
}

const viewTaskDetails = async (taskId) => {
  const details = await getTaskDetails(taskId)
  if (details) {
    selectedTask.value = details
  }
}

const closeTaskDetails = () => {
  selectedTask.value = null
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-TW')
}

const formatParameters = (parameters) => {
  if (!parameters) return ''
  try {
    return JSON.stringify(JSON.parse(parameters), null, 2)
  } catch {
    return parameters
  }
}

const retryTask = (taskId) => {
  console.log('重試任務:', taskId)
  // 實際應用中會重新執行任務
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'failed': '失敗',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 頁面掛載時初始化
onMounted(async () => {
  // 獲取任務資料和統計
  await refreshTasks()
  
  // 如果有執行中的任務，開始輪詢
  if (runningTasks.value.length > 0) {
    pollCleanup.value = startTaskPolling()
  }
})

// 頁面卸載時清理
onUnmounted(() => {
  if (pollCleanup.value) {
    pollCleanup.value()
  }
})
</script>