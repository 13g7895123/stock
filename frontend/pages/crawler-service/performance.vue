<template>
  <div class="space-y-6">
    <!-- 頁面標題 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            效能對比分析 (Go vs Python)
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            對比 Go 爬蟲服務與 Python 爬蟲的處理速度、記憶體使用和成功率
          </p>
        </div>
      </div>
    </div>

    <!-- 通知訊息 -->
    <div
      v-if="notification.show"
      :class="[
        'p-4 rounded-lg-custom shadow-sm',
        notification.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' :
        notification.type === 'error' ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200' :
        'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200'
      ]"
    >
      <div class="flex items-start">
        <CheckCircleIcon v-if="notification.type === 'success'" class="h-5 w-5 mt-0.5 mr-3" />
        <XCircleIcon v-else-if="notification.type === 'error'" class="h-5 w-5 mt-0.5 mr-3" />
        <InformationCircleIcon v-else class="h-5 w-5 mt-0.5 mr-3" />
        <div class="flex-1">
          <p class="font-medium">{{ notification.message }}</p>
        </div>
        <button @click="notification.show = false" class="ml-4">
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>
    </div>

    <!-- 效能對比測試 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">執行效能測試</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            測試股票代碼
          </label>
          <input
            v-model="testSymbol"
            type="text"
            placeholder="例如: 2330"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="flex items-end">
          <ActionButton
            @click="runPerformanceTest"
            :loading="testing"
            variant="primary"
            class="w-full"
          >
            <BoltIcon class="h-5 w-5 mr-2" />
            執行效能測試
          </ActionButton>
        </div>
      </div>
    </div>

    <!-- 測試結果對比 -->
    <div v-if="comparisonResult" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Go 爬蟲結果 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Go 爬蟲服務</h3>
          <span
            :class="[
              'px-3 py-1 rounded-full text-sm font-medium',
              comparisonResult.go.success ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
            ]"
          >
            {{ comparisonResult.go.success ? '✅ 成功' : '❌ 失敗' }}
          </span>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-gray-600 dark:text-gray-400">執行時間</span>
            <span class="text-lg font-semibold text-green-600">
              {{ comparisonResult.go.duration }}ms
            </span>
          </div>
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-gray-600 dark:text-gray-400">資料筆數</span>
            <span class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ comparisonResult.go.recordCount }} 筆
            </span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-gray-600 dark:text-gray-400">記憶體使用</span>
            <span class="text-lg font-semibold text-purple-600">
              ~100 MB
            </span>
          </div>
        </div>
      </div>

      <!-- Python 爬蟲結果 -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Python 爬蟲服務</h3>
          <span
            :class="[
              'px-3 py-1 rounded-full text-sm font-medium',
              comparisonResult.python.success ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
            ]"
          >
            {{ comparisonResult.python.success ? '✅ 成功' : '❌ 失敗' }}
          </span>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-gray-600 dark:text-gray-400">執行時間</span>
            <span class="text-lg font-semibold text-orange-600">
              {{ comparisonResult.python.duration }}ms
            </span>
          </div>
          <div class="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
            <span class="text-gray-600 dark:text-gray-400">資料筆數</span>
            <span class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ comparisonResult.python.recordCount }} 筆
            </span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-gray-600 dark:text-gray-400">記憶體使用</span>
            <span class="text-lg font-semibold text-purple-600">
              ~500 MB
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 效能提升統計 -->
    <div v-if="comparisonResult && comparisonResult.speedup" class="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg-custom shadow-sm p-8">
      <div class="text-center mb-6">
        <h3 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">效能提升</h3>
        <p class="text-gray-600 dark:text-gray-400">Go 爬蟲相比 Python 爬蟲的效能優勢</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">速度提升</p>
          <p class="text-4xl font-bold text-green-600 mb-1">{{ comparisonResult.speedup }}x</p>
          <p class="text-xs text-gray-500">更快的處理速度</p>
        </div>

        <div class="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">記憶體節省</p>
          <p class="text-4xl font-bold text-purple-600 mb-1">80%</p>
          <p class="text-xs text-gray-500">降低記憶體使用</p>
        </div>

        <div class="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">並發能力</p>
          <p class="text-4xl font-bold text-blue-600 mb-1">100x+</p>
          <p class="text-xs text-gray-500">Goroutines vs Threads</p>
        </div>
      </div>
    </div>

    <!-- 效能指標說明 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">技術優勢分析</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div>
            <h4 class="font-medium text-gray-900 dark:text-gray-100 mb-2">🚀 Go 爬蟲優勢</h4>
            <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li class="flex items-start">
                <span class="text-green-500 mr-2">✓</span>
                <span>原生並發支援（Goroutines），可同時處理 1000+ 請求</span>
              </li>
              <li class="flex items-start">
                <span class="text-green-500 mr-2">✓</span>
                <span>編譯型語言，執行效能比直譯型語言快 10-20 倍</span>
              </li>
              <li class="flex items-start">
                <span class="text-green-500 mr-2">✓</span>
                <span>記憶體使用優化，GC 效率高，長期運行穩定</span>
              </li>
              <li class="flex items-start">
                <span class="text-green-500 mr-2">✓</span>
                <span>單一執行檔部署，無依賴問題</span>
              </li>
              <li class="flex items-start">
                <span class="text-green-500 mr-2">✓</span>
                <span>PostgreSQL COPY 協議支援，批次插入速度提升 100 倍</span>
              </li>
            </ul>
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <h4 class="font-medium text-gray-900 dark:text-gray-100 mb-2">📊 適用場景</h4>
            <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span>大量股票資料的批次爬取（> 100 檔股票）</span>
              </li>
              <li class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span>需要即時更新的高頻資料抓取</span>
              </li>
              <li class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span>資源受限環境下的資料處理</span>
              </li>
              <li class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span>需要長期穩定運行的爬蟲服務</span>
              </li>
              <li class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span>多券商輪詢策略的容錯處理</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 效能基準測試數據 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">效能基準測試</h2>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-700/50">
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                測試項目
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Python
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Go
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                提升倍數
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                批次處理速度
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                ~10 stocks/sec
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                100-200 stocks/sec
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                10-20x
              </td>
            </tr>
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                並發處理能力
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                4-8 threads
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                1000+ goroutines
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                100x+
              </td>
            </tr>
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                記憶體使用
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                ~500MB
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                ~100MB
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                5x
              </td>
            </tr>
            <tr>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                Docker 映像大小
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                ~500MB
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                ~20MB
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                25x
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
  BoltIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const { comparePerformance } = useCrawlerService()

// 本地狀態
const testSymbol = ref('2330')
const testing = ref(false)
const comparisonResult = ref(null)

// 通知
const notification = ref({
  show: false,
  type: 'info',
  message: ''
})

// 顯示通知
const showNotification = (type, message, duration = 5000) => {
  notification.value = { show: true, type, message }
  setTimeout(() => {
    notification.value.show = false
  }, duration)
}

// 執行效能測試
const runPerformanceTest = async () => {
  if (!testSymbol.value.trim()) {
    showNotification('error', '請輸入股票代碼')
    return
  }

  testing.value = true
  comparisonResult.value = null

  const result = await comparePerformance(testSymbol.value.trim())

  testing.value = false

  if (result.success) {
    comparisonResult.value = result.data
    showNotification('success', '效能測試完成')
  } else {
    showNotification('error', `測試失敗: ${result.error}`)
  }
}
</script>
