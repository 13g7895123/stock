/**
 * 交易日分析相關API組合式函數
 */

export const useTradingDays = () => {
  const { get, post } = useApi()

  // 響應式資料
  const loading = ref(false)
  const error = ref(null)

  /**
   * 獲取缺少的交易日摘要
   * @param {number} daysBack - 檢查過去幾天的資料，預設30天
   */
  const getMissingTradingDaysSummary = async (daysBack = 30) => {
    loading.value = true
    error.value = null

    try {
      const result = await get(`/trading-days/missing-summary?days_back=${daysBack}`)

      if (result.success) {
        const backendResponse = result.data
        if (backendResponse.status === 'success') {
          console.log('✅ 缺少交易日摘要API成功回應')
          return backendResponse.data
        } else {
          error.value = backendResponse.message || '獲取摘要失敗'
          console.error('獲取缺少交易日摘要失敗:', backendResponse.message)
          return null
        }
      } else {
        error.value = result.error
        console.error('獲取缺少交易日摘要失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('獲取缺少交易日摘要時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票資料完整性分析
   * @param {string|null} stockCode - 股票代號，留空則分析所有股票
   * @param {number} daysBack - 檢查過去幾天的資料，預設30天
   */
  const getStockCompleteness = async (stockCode = null, daysBack = 30) => {
    loading.value = true
    error.value = null

    try {
      let url = `/trading-days/stock-completeness?days_back=${daysBack}`
      if (stockCode) {
        url += `&stock_code=${stockCode}`
      }

      const result = await get(url)

      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        console.error('獲取股票完整性分析失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('獲取股票完整性分析時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取缺少資料的修復建議
   * @param {string[]} missingDates - 缺少的日期列表，格式為 YYYY-MM-DD
   */
  const getFixSuggestions = async (missingDates) => {
    loading.value = true
    error.value = null

    try {
      const result = await post('/trading-days/fix-suggestions', missingDates)

      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        console.error('獲取修復建議失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('獲取修復建議時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 使用證交所API更新缺少的交易日資料
   * @param {string} date - 要更新的日期，格式為 YYYY-MM-DD 或 YYYYMMDD
   * @param {boolean} saveToDb - 是否儲存到資料庫
   */
  const updateMissingDate = async (date, saveToDb = true) => {
    loading.value = true
    error.value = null

    try {
      // 將日期格式轉換為YYYYMMDD
      const twseDate = date.replace(/-/g, '')

      const result = await get(`/twse/historical-all/${twseDate}?save_to_db=${saveToDb}`)

      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        console.error('更新缺少日期資料失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('更新缺少日期資料時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 批次更新多個缺少的交易日
   * @param {string[]} dates - 要更新的日期列表
   * @param {function} onProgress - 進度回調函數
   */
  const batchUpdateMissingDates = async (dates, onProgress = null) => {
    const results = []
    const total = dates.length

    for (let i = 0; i < dates.length; i++) {
      const date = dates[i]

      if (onProgress) {
        onProgress({
          current: i + 1,
          total,
          date,
          percentage: Math.round(((i + 1) / total) * 100)
        })
      }

      const result = await updateMissingDate(date)
      results.push({
        date,
        success: result !== null,
        result,
        error: result === null ? error.value : null
      })

      // 在請求之間添加短暫延遲，避免過於頻繁的API調用
      if (i < dates.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    return {
      total,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    }
  }

  /**
   * 智能分析缺少的交易日（自動調整檢查範圍）
   */
  const getSmartMissingTradingDaysAnalysis = async () => {
    loading.value = true
    error.value = null

    try {
      const result = await get('/trading-days/smart-analysis')

      if (result.success) {
        // result.data 是後端的原始回應 {status: "success", data: {...}, ...}
        // 我們需要返回其中的 data 欄位，它包含實際的分析結果
        const backendResponse = result.data
        if (backendResponse.status === 'success') {
          console.log('✅ 智能分析API成功回應，缺少交易日:', backendResponse.data.statistics?.total_missing_days || 0)
          return backendResponse.data
        } else {
          error.value = backendResponse.message || '智能分析失敗'
          console.error('智能分析缺少交易日失敗:', backendResponse.message)
          return null
        }
      } else {
        error.value = result.error
        console.error('智能分析缺少交易日失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('智能分析缺少交易日時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取交易日檢查服務資訊
   */
  const getServiceInfo = async () => {
    try {
      const result = await get('/trading-days/info')
      return result.success ? result.data : null
    } catch (err) {
      console.error('獲取服務資訊時發生錯誤:', err)
      return null
    }
  }

  /**
   * 智能批次更新分析 - Point 13 功能
   * @param {number} daysBack - 檢查過去幾天的資料，預設30天
   * @param {boolean} forceRefresh - 強制刷新模式，即使沒有缺少資料也生成刷新清單
   */
  const getSmartBatchUpdateAnalysis = async (daysBack = 30, forceRefresh = false) => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        days_back: daysBack.toString(),
        force_refresh: forceRefresh.toString()
      })

      const result = await get(`/trading-days/smart-batch-update-analysis?${params}`)

      if (result.success) {
        console.log('✅ 智能批次更新分析完成', forceRefresh ? '(強制刷新模式)' : '')
        return result.data
      } else {
        error.value = result.error
        console.error('智能批次更新分析失敗:', result.error)
        return null
      }
    } catch (err) {
      error.value = err.message
      console.error('智能批次更新分析時發生錯誤:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 執行智能批次更新 - 根據分析結果執行證交所API調用
   * @param {Array} apiCalls - API調用清單
   * @param {function} onProgress - 進度回調函數
   */
  const executeSmartBatchUpdate = async (apiCalls, onProgress = null) => {
    const results = []
    const total = apiCalls.length

    for (let i = 0; i < apiCalls.length; i++) {
      const apiCall = apiCalls[i]

      if (onProgress) {
        onProgress({
          current: i + 1,
          total,
          date: apiCall.date,
          percentage: Math.round(((i + 1) / total) * 100),
          currentAction: `正在處理 ${apiCall.date}`
        })
      }

      try {
        // 提取日期部分，移除查詢參數
        const endpoint = apiCall.api_endpoint.split('?')[0]
        const queryParams = apiCall.api_endpoint.includes('?') ? '?' + apiCall.api_endpoint.split('?')[1] : ''

        const result = await get(endpoint.replace('/api/v1', '') + queryParams)

        results.push({
          date: apiCall.date,
          success: result.success || (result.status === 'success'),
          result,
          error: result.success ? null : (result.error || '執行失敗')
        })

        console.log(`✅ ${apiCall.date} 批次更新完成`)
      } catch (err) {
        results.push({
          date: apiCall.date,
          success: false,
          result: null,
          error: err.message
        })
        console.error(`❌ ${apiCall.date} 批次更新失敗:`, err.message)
      }

      // 在請求之間添加延遲，避免過於頻繁的API調用
      if (i < apiCalls.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1500))
      }
    }

    return {
      total,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    }
  }

  return {
    // 響應式資料
    loading: readonly(loading),
    error: readonly(error),

    // API方法
    getMissingTradingDaysSummary,
    getSmartMissingTradingDaysAnalysis,
    getStockCompleteness,
    getFixSuggestions,
    updateMissingDate,
    batchUpdateMissingDates,
    getServiceInfo,
    // Point 13 新增功能
    getSmartBatchUpdateAnalysis,
    executeSmartBatchUpdate
  }
}