<template>
  <div class="min-h-screen bg-slate-950 text-white font-sans antialiased">
    <!-- 動態背景 -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-0 -left-40 w-80 h-80 bg-blue-500/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
      <div class="absolute top-0 -right-40 w-80 h-80 bg-purple-500/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
      <div class="absolute -bottom-40 left-1/2 w-80 h-80 bg-pink-500/20 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000"></div>
    </div>

    <!-- 主容器 -->
    <div class="relative">
      <!-- 頂部導航列 -->
      <nav class="sticky top-0 z-50 border-b border-white/5 backdrop-blur-xl bg-slate-950/80">
        <div class="max-w-[1920px] mx-auto px-6 lg:px-12">
          <div class="flex items-center justify-between h-20">
            <!-- Logo 區域 -->
            <div class="flex items-center gap-4">
              <div class="relative group">
                <div class="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-75 group-hover:opacity-100 transition duration-300"></div>
                <div class="relative w-14 h-14 bg-slate-900 rounded-2xl flex items-center justify-center">
                  <svg class="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <div>
                <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  台股分析平台
                </h1>
                <p class="text-xs text-slate-400 font-medium tracking-wide">TAIWAN STOCK ANALYSIS</p>
              </div>
            </div>

            <!-- 右側功能區 -->
            <div class="flex items-center gap-4">
              <!-- 系統狀態 -->
              <div class="hidden md:flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                <div class="relative">
                  <div class="w-3 h-3 rounded-full" :class="status === '運行中' ? 'bg-emerald-400' : 'bg-red-400'"></div>
                  <div v-if="status === '運行中'" class="absolute inset-0 w-3 h-3 rounded-full bg-emerald-400 animate-ping"></div>
                </div>
                <div class="text-sm">
                  <div class="font-semibold text-white">{{ status }}</div>
                  <div class="text-xs text-slate-400">{{ lastUpdate }}</div>
                </div>
              </div>

              <!-- 主題切換 -->
              <button 
                @click="toggleTheme"
                aria-label="切換深色/淺色模式"
                class="p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 group"
              >
                <svg v-if="isDark" class="w-5 h-5 text-yellow-400 group-hover:rotate-180 transition-transform duration-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="w-5 h-5 text-blue-400 group-hover:-rotate-45 transition-transform duration-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              </button>

              <!-- 重新整理 -->
              <button
                @click="loadData"
                :disabled="loading"
                aria-label="重新整理資料"
                class="p-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <svg class="w-5 h-5 text-white" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <!-- 主要內容 -->
      <main class="max-w-[1920px] mx-auto px-6 lg:px-12 py-12 space-y-8">
        <!-- 數據卡片區 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- 總股票數 -->
          <article class="group relative">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div class="relative bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:border-blue-500/50 transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl">
                  <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <span class="text-xs font-semibold text-blue-400 bg-blue-500/10 px-2 py-1 rounded-lg">STOCKS</span>
              </div>
              <h3 class="text-sm font-medium text-slate-400 mb-2">總股票數量</h3>
              <p class="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-1">
                {{ stats.totalStocks.toLocaleString() }}
              </p>
              <p class="text-xs text-slate-500">上市上櫃股票</p>
            </div>
          </article>

          <!-- 總記錄數 -->
          <article class="group relative">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div class="relative bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:border-purple-500/50 transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
                  <svg class="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <span class="text-xs font-semibold text-purple-400 bg-purple-500/10 px-2 py-1 rounded-lg">RECORDS</span>
              </div>
              <h3 class="text-sm font-medium text-slate-400 mb-2">歷史資料筆數</h3>
              <p class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-1">
                {{ stats.totalRecords.toLocaleString() }}
              </p>
              <p class="text-xs text-slate-500">交易日資料</p>
            </div>
          </article>

          <!-- 平均記錄 -->
          <article class="group relative">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div class="relative bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:border-emerald-500/50 transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-xl">
                  <svg class="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <span class="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-lg">AVERAGE</span>
              </div>
              <h3 class="text-sm font-medium text-slate-400 mb-2">平均資料量</h3>
              <p class="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent mb-1">
                {{ Math.round(stats.avgRecords).toLocaleString() }}
              </p>
              <p class="text-xs text-slate-500">每檔股票</p>
            </div>
          </article>

          <!-- 爬取控制 -->
          <article class="group relative">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div class="relative bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:border-orange-500/50 transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="p-3 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-xl">
                  <svg class="w-6 h-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <span class="text-xs font-semibold text-orange-400 bg-orange-500/10 px-2 py-1 rounded-lg">ACTION</span>
              </div>
              <h3 class="text-sm font-medium text-slate-400 mb-2">資料爬取</h3>
              <button
                @click="triggerCrawl"
                :disabled="loading"
                class="w-full mt-2 px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 rounded-xl font-semibold text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95"
              >
                <span v-if="loading">處理中...</span>
                <span v-else>開始爬取</span>
              </button>
            </div>
          </article>
        </div>

        <!-- 控制面板 -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div class="flex flex-col sm:flex-row gap-3 flex-1">
            <!-- 搜尋框 -->
            <div class="relative flex-1 max-w-md">
              <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜尋股票代碼或名稱..."
                aria-label="搜尋股票"
                class="w-full pl-12 pr-4 py-3 bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>

            <!-- 排序選擇 -->
            <div class="relative">
              <select
                v-model="sortBy"
                aria-label="排序方式"
                class="appearance-none pl-4 pr-12 py-3 bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all cursor-pointer"
              >
                <option value="stock_code">依代碼排序</option>
                <option value="stock_name">依名稱排序</option>
                <option value="record_count">依資料量排序</option>
                <option value="latest_date">依日期排序</option>
              </select>
              <svg class="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <!-- 匯出按鈕 -->
          <button
            @click="exportCSV"
            class="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium transition-all duration-300 flex items-center justify-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span class="hidden sm:inline">匯出 CSV</span>
          </button>
        </div>

        <!-- 股票資料表 -->
        <div class="relative">
          <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-10"></div>
          <div class="relative bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
            <!-- 表頭 -->
            <div class="px-6 py-5 border-b border-white/10">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-xl font-bold text-white mb-1">股票資料列表</h2>
                  <p class="text-sm text-slate-400">
                    顯示 <span class="text-blue-400 font-semibold">{{ filteredStocks.length }}</span> / {{ stocks.length }} 筆資料
                  </p>
                </div>
                <div v-if="searchQuery" class="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <span class="text-xs font-medium text-blue-400">搜尋中</span>
                </div>
              </div>
            </div>

            <!-- 載入中狀態 -->
            <div v-if="loading" class="py-32 text-center">
              <div class="inline-flex flex-col items-center gap-4">
                <div class="relative">
                  <div class="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                  <div class="absolute inset-0 w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
                </div>
                <p class="text-slate-400 font-medium">正在載入資料...</p>
              </div>
            </div>

            <!-- 錯誤狀態 -->
            <div v-else-if="error" class="py-32 text-center">
              <div class="inline-flex flex-col items-center gap-4">
                <div class="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                  <svg class="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p class="text-red-400 font-semibold mb-1">載入失敗</p>
                  <p class="text-sm text-slate-500">{{ error }}</p>
                </div>
              </div>
            </div>

            <!-- 資料表格 -->
            <div v-else class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-white/5">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      股票代碼
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      股票名稱
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      資料筆數
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      起始日期
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      最新日期
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      資料來源
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider whitespace-nowrap">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/5">
                  <tr 
                    v-for="stock in filteredStocks" 
                    :key="stock.stock_code"
                    class="hover:bg-white/5 transition-colors duration-150"
                  >
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="text-sm font-bold text-blue-400 font-mono">
                        {{ stock.stock_code }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="text-sm font-semibold text-white">
                        {{ stock.stock_name }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="inline-flex items-center px-3 py-1 text-xs font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                        {{ (stock.record_count || 0).toLocaleString() }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-400 font-mono">
                      {{ stock.first_date || '-' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-400 font-mono">
                      {{ stock.latest_date || '-' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="inline-flex items-center px-3 py-1 text-xs font-bold text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                        {{ stock.data_source || '未知' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <button
                        @click="viewDetail(stock)"
                        class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 hover:from-blue-500/20 hover:to-purple-500/20 border border-blue-500/20 hover:border-blue-500/40 rounded-lg text-sm font-semibold text-blue-300 transition-all duration-200"
                      >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <span>查看詳情</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>

              <!-- 無資料狀態 -->
              <div v-if="filteredStocks.length === 0" class="py-20 text-center">
                <svg class="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="text-slate-400 font-medium">找不到符合條件的資料</p>
                <p class="text-sm text-slate-500 mt-1">請嘗試其他搜尋條件</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 頁尾 -->
        <footer class="mt-16 pt-8 border-t border-white/5 text-center">
          <p class="text-sm text-slate-500">
            © 2026 台股分析平台 · Powered by 
            <span class="text-blue-400 font-semibold">Nuxt 4</span> & 
            <span class="text-purple-400 font-semibold">Bun</span>
          </p>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const apiUrl = config.public.apiUrl || 'http://localhost:9627'

// 狀態管理
const loading = ref(false)
const error = ref('')
const status = ref('檢查中...')
const stocks = ref<any[]>([])
const stats = ref({
  totalStocks: 0,
  totalRecords: 0,
  avgRecords: 0
})

// UI 狀態
const isDark = ref(true)
const searchQuery = ref('')
const sortBy = ref('stock_code')
const lastUpdate = ref('剛剛')

// 主題切換
const toggleTheme = () => {
  isDark.value = !isDark.value
  // 目前設計為深色模式優先，可擴展淺色模式
}

// 過濾與排序
const filteredStocks = computed(() => {
  let result = [...stocks.value]
  
  // 搜尋過濾
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(stock =>
      stock.stock_code.toLowerCase().includes(query) ||
      stock.stock_name.toLowerCase().includes(query)
    )
  }
  
  // 排序
  result.sort((a, b) => {
    const aVal = a[sortBy.value]
    const bVal = b[sortBy.value]
    
    if (sortBy.value === 'record_count') {
      return (bVal || 0) - (aVal || 0)
    }
    
    return String(aVal || '').localeCompare(String(bVal || ''), 'zh-TW')
  })
  
  return result
})

// 載入資料
const loadData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await $fetch(`${apiUrl}/api/v1/stats/stocks-summary`)
    
    if (response.success && response.data) {
      stocks.value = response.data.stocks || []
      stats.value = {
        totalStocks: response.data.total_stocks || 0,
        totalRecords: response.data.total_records || 0,
        avgRecords: response.data.avg_records || 0
      }
      status.value = '運行中'
      
      const now = new Date()
      lastUpdate.value = now.toLocaleTimeString('zh-TW', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      })
    }
  } catch (err: any) {
    console.error('載入失敗:', err)
    error.value = err.message || '無法連接到伺服器'
    status.value = '離線'
  } finally {
    loading.value = false
  }
}

// 觸發爬蟲
const triggerCrawl = async () => {
  if (!confirm('確定要開始爬取所有股票資料嗎？\n此操作可能需要較長時間。')) {
    return
  }
  
  loading.value = true
  
  try {
    await $fetch(`${apiUrl}/api/v1/stocks/batch-update`, {
      method: 'POST'
    })
    
    alert('✅ 爬取任務已成功提交！\n\n系統將在背景處理，約 30 秒後自動刷新資料。')
    
    // 延遲刷新
    setTimeout(() => {
      loadData()
    }, 30000)
  } catch (err: any) {
    console.error('爬取失敗:', err)
    alert(`❌ 爬取失敗\n\n錯誤訊息：${err.message}`)
  } finally {
    loading.value = false
  }
}

// 查看詳情
const viewDetail = (stock: any) => {
  // TODO: 實作詳情 Modal
  const message = `
📊 ${stock.stock_code} - ${stock.stock_name}

📈 資料筆數：${(stock.record_count || 0).toLocaleString()}
📅 起始日期：${stock.first_date || '-'}
📅 最新日期：${stock.latest_date || '-'}
🔗 資料來源：${stock.data_source || '未知'}

（詳細圖表功能開發中...）
  `.trim()
  
  alert(message)
}

// 匯出 CSV
const exportCSV = () => {
  if (filteredStocks.value.length === 0) {
    alert('⚠️ 沒有資料可以匯出')
    return
  }
  
  const headers = ['股票代碼', '股票名稱', '資料筆數', '起始日期', '最新日期', '資料來源']
  const rows = filteredStocks.value.map(stock => [
    stock.stock_code,
    stock.stock_name,
    stock.record_count || 0,
    stock.first_date || '-',
    stock.latest_date || '-',
    stock.data_source || '未知'
  ])
  
  const csv = [headers, ...rows]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const date = new Date().toISOString().split('T')[0]
  
  link.href = URL.createObjectURL(blob)
  link.download = `台股資料_${date}.csv`
  link.click()
  
  URL.revokeObjectURL(link.href)
}

// 生命週期
onMounted(() => {
  // 初始載入
  loadData()
  
  // 定期刷新（每 30 秒）
  const refreshInterval = setInterval(() => {
    if (!loading.value) {
      loadData()
    }
  }, 30000)
  
  // 清理
  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* 自訂動畫 */
@keyframes blob {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(20px, -50px) scale(1.1);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.9);
  }
  75% {
    transform: translate(50px, 50px) scale(1.05);
  }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}

/* 捲軸樣式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.8);
}

/* 無障礙：聚焦樣式 */
button:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid rgb(59, 130, 246);
  outline-offset: 2px;
}

/* 減少動畫 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
