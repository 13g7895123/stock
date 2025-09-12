<template>
  <div class="space-y-6">
    <!-- 通知區域 -->
    <div v-if="notification.show" :class="[
      'p-4 rounded-lg border-l-4 flex items-center justify-between',
      notification.type === 'success' ? 'bg-green-50 border-green-400 text-green-700 dark:bg-green-900 dark:text-green-200' :
      notification.type === 'error' ? 'bg-red-50 border-red-400 text-red-700 dark:bg-red-900 dark:text-red-200' :
      'bg-blue-50 border-blue-400 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
    ]">
      <div class="flex items-center">
        <span class="font-medium mr-2">
          {{ notification.type === 'success' ? '✅' : notification.type === 'error' ? '❌' : 'ℹ️' }}
        </span>
        <span>{{ notification.message }}</span>
      </div>
      <button @click="notification.show = false" class="text-lg font-bold opacity-70 hover:opacity-100">
        ×
      </button>
    </div>

    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">資料品質管理</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-1">監控和管理股票歷史資料的品質與完整性</p>
        </div>
        <div class="flex items-center space-x-3">
          <ActionButton 
            @click="handleRunQualityCheck"
            :loading="loading"
            :icon="MagnifyingGlassIcon"
            text="執行品質檢查"
            loading-text="檢查中..."
            variant="primary"
          />
        </div>
      </div>
    </div>

    <!-- 品質概覽 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CheckCircleIcon class="w-8 h-8 text-green-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">整體品質評分</div>
            <div class="text-2xl font-bold text-green-600">
              {{ qualityOverview.overall_score || 0 }}%
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ExclamationCircleIcon class="w-8 h-8 text-yellow-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">異常資料筆數</div>
            <div class="text-2xl font-bold text-yellow-600">
              {{ qualityOverview.anomaly_count || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <XCircleIcon class="w-8 h-8 text-red-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">缺失資料筆數</div>
            <div class="text-2xl font-bold text-red-600">
              {{ qualityOverview.missing_count || 0 }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CalendarIcon class="w-8 h-8 text-blue-500" />
          </div>
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">最後檢查時間</div>
            <div class="text-sm font-bold text-gray-900 dark:text-white">
              {{ qualityOverview.last_check_time || 'N/A' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 品質檢查規則 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">品質檢查規則</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 價格合理性檢查 -->
        <div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-900 dark:text-white">價格合理性檢查</h4>
            <div class="flex items-center">
              <input
                v-model="qualityRules.price_check.enabled"
                type="checkbox"
                class="rounded border-gray-300 dark:border-gray-600"
              />
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">檢查股價是否在合理範圍內，偵測異常波動</p>
          <div class="space-y-2">
            <div class="flex items-center space-x-2">
              <label class="text-xs text-gray-500 dark:text-gray-400 w-20">漲跌限制:</label>
              <input
                v-model="qualityRules.price_check.max_change_percent"
                type="number"
                min="1"
                max="50"
                class="w-16 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded"
              />
              <span class="text-xs text-gray-500">%</span>
            </div>
          </div>
        </div>

        <!-- 資料完整性檢查 -->
        <div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-900 dark:text-white">資料完整性檢查</h4>
            <div class="flex items-center">
              <input
                v-model="qualityRules.completeness_check.enabled"
                type="checkbox"
                class="rounded border-gray-300 dark:border-gray-600"
              />
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">檢查必要欄位是否存在，偵測缺失資料</p>
          <div class="space-y-2">
            <div class="flex items-center space-x-2">
              <label class="text-xs text-gray-500 dark:text-gray-400 w-20">必要欄位:</label>
              <span class="text-xs text-gray-600 dark:text-gray-300">開盤價、最高價、最低價、收盤價、成交量</span>
            </div>
          </div>
        </div>

        <!-- 日期連續性檢查 -->
        <div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-900 dark:text-white">日期連續性檢查</h4>
            <div class="flex items-center">
              <input
                v-model="qualityRules.date_continuity_check.enabled"
                type="checkbox"
                class="rounded border-gray-300 dark:border-gray-600"
              />
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">檢查交易日期是否連續，偵測缺失的交易日</p>
          <div class="space-y-2">
            <div class="flex items-center space-x-2">
              <label class="text-xs text-gray-500 dark:text-gray-400 w-20">最大間隔:</label>
              <input
                v-model="qualityRules.date_continuity_check.max_gap_days"
                type="number"
                min="1"
                max="30"
                class="w-16 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded"
              />
              <span class="text-xs text-gray-500">天</span>
            </div>
          </div>
        </div>

        <!-- 成交量合理性檢查 -->
        <div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-900 dark:text-white">成交量合理性檢查</h4>
            <div class="flex items-center">
              <input
                v-model="qualityRules.volume_check.enabled"
                type="checkbox"
                class="rounded border-gray-300 dark:border-gray-600"
              />
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">檢查成交量是否異常，偵測異常交易</p>
          <div class="space-y-2">
            <div class="flex items-center space-x-2">
              <label class="text-xs text-gray-500 dark:text-gray-400 w-20">異常倍數:</label>
              <input
                v-model="qualityRules.volume_check.anomaly_multiplier"
                type="number"
                min="2"
                max="20"
                step="0.5"
                class="w-16 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded"
              />
              <span class="text-xs text-gray-500">倍</span>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
        <ActionButton 
          @click="handleSaveRules"
          :loading="loading"
          :icon="CheckIcon"
          text="儲存規則"
          variant="success"
        />
      </div>
    </div>

    <!-- 品質問題清單 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            品質問題清單 ({{ qualityIssues.length }} 項)
          </h3>
          <div class="flex items-center space-x-2">
            <!-- 篩選器 -->
            <select
              v-model="selectedSeverity"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            >
              <option value="">所有嚴重度</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
            <ActionButton 
              @click="handleFixSelectedIssues"
              :loading="loading"
              :disabled="selectedIssues.length === 0"
              :icon="WrenchScrewdriverIcon"
              text="修復選中項目"
              variant="warning"
              size="sm"
            />
          </div>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  @change="toggleSelectAll"
                  :checked="selectedIssues.length === filteredIssues.length && filteredIssues.length > 0"
                  class="rounded border-gray-300 dark:border-gray-600"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">股票代碼</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">問題類型</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">嚴重度</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">描述</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">發現時間</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="issue in filteredIssues"
              :key="issue.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td class="px-6 py-4">
                <input
                  type="checkbox"
                  :value="issue.id"
                  v-model="selectedIssues"
                  class="rounded border-gray-300 dark:border-gray-600"
                />
              </td>
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ issue.symbol }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{ issue.type }}</span>
              </td>
              <td class="px-6 py-4">
                <span 
                  :class="[
                    'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                    issue.severity === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                    issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                    'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  ]"
                >
                  {{ issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低' }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{ issue.description }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ issue.discovered_at }}</span>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <ActionButton 
                    @click="handleFixSingleIssue(issue)"
                    :icon="WrenchScrewdriverIcon"
                    text="修復"
                    variant="warning"
                    size="sm"
                  />
                  <ActionButton 
                    @click="handleIgnoreIssue(issue)"
                    :icon="XMarkIcon"
                    text="忽略"
                    variant="secondary"
                    size="sm"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 空狀態 -->
      <div v-if="filteredIssues.length === 0" class="text-center py-12">
        <CheckCircleIcon class="w-16 h-16 mx-auto text-green-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">沒有發現品質問題</h3>
        <p class="text-gray-600 dark:text-gray-400">
          所有資料都通過品質檢查，資料品質良好！
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  XCircleIcon,
  CalendarIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  WrenchScrewdriverIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

// 設定頁面標題
definePageMeta({
  title: '資料品質管理'
})

// 使用組合式函數
const { loading, error } = useStocks()

// 響應式資料
const qualityOverview = ref({
  overall_score: 85,
  anomaly_count: 12,
  missing_count: 3,
  last_check_time: '2024-01-15 14:30'
})

const qualityRules = ref({
  price_check: {
    enabled: true,
    max_change_percent: 10
  },
  completeness_check: {
    enabled: true
  },
  date_continuity_check: {
    enabled: true,
    max_gap_days: 3
  },
  volume_check: {
    enabled: true,
    anomaly_multiplier: 5
  }
})

const qualityIssues = ref([
  {
    id: 1,
    symbol: '2330',
    type: '價格異常',
    severity: 'high',
    description: '2024-01-10 股價單日漲幅超過15%',
    discovered_at: '2024-01-15 10:30'
  },
  {
    id: 2,
    symbol: '2317',
    type: '資料缺失',
    severity: 'medium',
    description: '2024-01-08 成交量資料缺失',
    discovered_at: '2024-01-15 10:30'
  },
  {
    id: 3,
    symbol: '2454',
    type: '日期間隔',
    severity: 'low',
    description: '2024-01-05-2024-01-09 資料間隔過大',
    discovered_at: '2024-01-15 10:30'
  }
])

const selectedSeverity = ref('')
const selectedIssues = ref([])

// 通知系統
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// 顯示通知
const showNotification = (type, message) => {
  notification.value = {
    show: true,
    type,
    message
  }
  
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

// 計算屬性
const filteredIssues = computed(() => {
  if (!selectedSeverity.value) return qualityIssues.value
  return qualityIssues.value.filter(issue => issue.severity === selectedSeverity.value)
})

// 處理函數
const handleRunQualityCheck = async () => {
  showNotification('info', '開始執行品質檢查...')
  
  // 模擬品質檢查過程
  await new Promise(resolve => setTimeout(resolve, 3000))
  
  // 更新品質概覽
  qualityOverview.value = {
    ...qualityOverview.value,
    last_check_time: new Date().toLocaleString('zh-TW')
  }
  
  showNotification('success', '品質檢查完成！發現了一些需要注意的問題')
}

const handleSaveRules = async () => {
  showNotification('info', '正在儲存品質檢查規則...')
  
  // 模擬儲存過程
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  showNotification('success', '品質檢查規則已成功儲存')
}

const handleFixSingleIssue = async (issue) => {
  showNotification('info', `正在修復 ${issue.symbol} 的 ${issue.type} 問題...`)
  
  // 模擬修復過程
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  // 從清單中移除已修復的問題
  const index = qualityIssues.value.findIndex(i => i.id === issue.id)
  if (index > -1) {
    qualityIssues.value.splice(index, 1)
  }
  
  showNotification('success', `${issue.symbol} 的 ${issue.type} 問題已修復`)
}

const handleIgnoreIssue = (issue) => {
  const index = qualityIssues.value.findIndex(i => i.id === issue.id)
  if (index > -1) {
    qualityIssues.value.splice(index, 1)
  }
  showNotification('info', `已忽略 ${issue.symbol} 的 ${issue.type} 問題`)
}

const handleFixSelectedIssues = async () => {
  if (selectedIssues.value.length === 0) {
    showNotification('error', '請選擇要修復的問題')
    return
  }

  showNotification('info', `正在修復 ${selectedIssues.value.length} 個問題...`)
  
  // 模擬修復過程
  await new Promise(resolve => setTimeout(resolve, 3000))
  
  // 移除選中的問題
  qualityIssues.value = qualityIssues.value.filter(issue => !selectedIssues.value.includes(issue.id))
  selectedIssues.value = []
  
  showNotification('success', '選中的問題已全部修復完成')
}

const toggleSelectAll = () => {
  if (selectedIssues.value.length === filteredIssues.value.length) {
    selectedIssues.value = []
  } else {
    selectedIssues.value = filteredIssues.value.map(issue => issue.id)
  }
}
</script>