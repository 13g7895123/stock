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
          <button 
            @click="refreshStatus"
            class="px-4 py-2 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center space-x-2"
          >
            <ArrowPathIcon class="w-4 h-4" :class="{ 'animate-spin': loading }" />
            <span>重新整理</span>
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
            系統任務 ({{ tasks.length }})
          </h3>
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
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200': task.status === 'active' || task.status === 'success',
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': task.status === 'failed',
                      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': task.status === 'running' || task.status === 'pending'
                    }"
                  >
                    {{ getStatusLabel(task.status) }}
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

                  <!-- 上次執行 -->
                  <div class="flex items-center space-x-2">
                    <CheckCircleIcon class="w-4 h-4 text-gray-400" />
                    <div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">上次執行</div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ task.lastRun || '無紀錄' }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 任務操作按鈕 -->
              <div class="flex items-center space-x-2 ml-6">
                <button
                  @click="runTaskNow(task)"
                  :disabled="task.status === 'running'"
                  class="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="立即執行"
                >
                  <BoltIcon class="w-4 h-4" :class="{ 'animate-pulse': task.status === 'running' }" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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
  CheckIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '定時任務管理'
})

const { get, post } = useApi()
const loading = ref(false)

// 任務統計
const taskStats = ref([
  { 
    name: '系統任務', 
    value: '4', 
    icon: 'PlayIcon',
    bgColor: 'bg-blue-100 dark:bg-blue-900',
    iconColor: 'text-blue-600 dark:text-blue-400'
  },
  { 
    name: '執行中', 
    value: '0', 
    icon: 'ArrowPathIcon',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900',
    iconColor: 'text-yellow-600 dark:text-yellow-400'
  },
  { 
    name: '最近失敗', 
    value: '0', 
    icon: 'ExclamationTriangleIcon',
    bgColor: 'bg-red-100 dark:bg-red-900',
    iconColor: 'text-red-600 dark:text-red-400'
  },
  { 
    name: '正常運作', 
    value: '100%', 
    icon: 'CheckIcon',
    bgColor: 'bg-green-100 dark:bg-green-900',
    iconColor: 'text-green-600 dark:text-green-400'
  }
])

// 定義系統任務
const tasks = ref([
  {
    id: 'stock_list_sync',
    name: '每日股票清單更新',
    description: '從證交所同步最新的股票清單',
    status: 'active',
    schedule: '每日 00:00',
    lastRun: '-',
    apiPath: '/sync/stocks/sync', // Note: This is sync, crawl is separate usually
    method: 'POST'
  },
  {
    id: 'daily_price_update',
    name: '每日股價資料更新',
    description: '更新所有股票的日線資料',
    status: 'active',
    schedule: '每日 14:00',
    lastRun: '-',
    apiPath: '/tasks/manual/optimized-stock-crawl',
    method: 'POST',
    body: { symbols: null, max_workers: 4 }
  },
  {
    id: 'ma_calculation',
    name: '技術指標計算',
    description: '計算所有股票的均線指標',
    status: 'active',
    schedule: '每日 16:00',
    lastRun: '-',
    apiPath: '/moving-averages/calculate-async',
    method: 'POST',
    body: { stock_codes: null, periods: [5, 10, 24, 72, 120, 240] }
  },
  {
    id: 'institutional_update',
    name: '法人買賣超更新',
    description: '更新投信外資買賣超資料',
    status: 'active',
    schedule: '每日 17:00',
    lastRun: '-',
    apiPath: '/institutional-trading/update/latest',
    method: 'POST'
  }
])

const getStatusLabel = (status) => {
  const map = {
    'active': '就緒',
    'running': '執行中',
    'stopped': '已停止',
    'success': '執行成功',
    'failed': '執行失敗',
    'pending': '等待中'
  }
  return map[status] || status
}

const refreshStatus = async () => {
  loading.value = true
  try {
    // 獲取最近的任務執行紀錄來更新狀態
    const res = await get('/task-execution/recent', { limit: 50 })
    if (res.success && res.data) {
      const recentTasks = res.data
      
      // 更新統計
      const runningCount = recentTasks.filter(t => t.status === 'running').length
      const failedCount = recentTasks.filter(t => t.status === 'failed').length
      
      taskStats.value[1].value = runningCount.toString()
      taskStats.value[2].value = failedCount.toString()
      
      // 簡單計算成功率
      const total = recentTasks.length
      const success = recentTasks.filter(t => t.status === 'success').length
      taskStats.value[3].value = total > 0 ? Math.round((success / total) * 100) + '%' : '-'

      // 更新任務狀態 (這裡做一個簡單的映射，實際可能需要根據 task_type 匹配)
      // 假設 task_type 對應 id 或者有某種關聯
      // 由於後端 task_type 可能不完全對應，這裡僅作示範，實際需根據後端定義調整
      
      // 嘗試從 recentTasks 中找到對應類型的最新執行
      // 這裡假設 task_type 包含關鍵字
      tasks.value.forEach(task => {
        const match = recentTasks.find(t => {
            if (task.id === 'stock_list_sync') return t.task_type?.includes('sync') || t.name?.includes('清單')
            if (task.id === 'daily_price_update') return t.task_type?.includes('crawl') || t.name?.includes('爬蟲')
            if (task.id === 'ma_calculation') return t.task_type?.includes('ma') || t.name?.includes('均線')
            if (task.id === 'institutional_update') return t.task_type?.includes('institutional') || t.name?.includes('法人')
            return false
        })
        
        if (match) {
            task.lastRun = new Date(match.created_at || match.start_time).toLocaleString()
            // 如果最近的任務正在執行，則更新狀態
            if (match.status === 'running') {
                task.status = 'running'
            } else {
                // 保持 active，但在 lastRun 顯示結果
                task.status = 'active' 
            }
        }
      })
    }
  } catch (e) {
    console.error('Failed to refresh tasks', e)
  } finally {
    loading.value = false
  }
}

const runTaskNow = async (task) => {
  if (task.status === 'running') return
  
  if (!confirm(`確定要立即執行「${task.name}」嗎？`)) return

  try {
    task.status = 'running'
    const res = await post(task.apiPath, task.body || {})
    
    if (res.success) {
      // 顯示成功訊息
      alert(`已觸發任務：${task.name}`)
      // 重新整理狀態
      setTimeout(refreshStatus, 1000)
    } else {
      task.status = 'failed'
      alert(`啟動失敗：${res.message || '未知錯誤'}`)
    }
  } catch (e) {
    console.error(e)
    task.status = 'failed'
    alert('執行發生錯誤')
  }
}

// 圖示組件映射
const iconComponents = {
  PlayIcon,
  PauseIcon,
  StopIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || PlayIcon
}

onMounted(() => {
  refreshStatus()
})
</script>