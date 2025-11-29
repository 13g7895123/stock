/**
 * 均線計算相關API組合式函數
 */

export const useMovingAverages = () => {
  const { get, post } = useApi()

  /**
   * 獲取均線統計資訊
   */
  const getMovingAveragesStatistics = async () => {
    try {
      const result = await get('/moving-averages/statistics')
      return result
    } catch (error) {
      console.error('取得均線統計資訊失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '取得統計資訊失敗'
      }
    }
  }

  /**
   * 計算均線數據
   * @param {Array} stockCodes - 股票代號清單 
   * @param {Array} periods - 均線週期 [5, 10, 24, 72, 120, 240]
   * @param {Boolean} forceRecalculate - 是否強制重新計算
   */
  const calculateMovingAverages = async (stockCodes, periods = [5, 10, 24, 72, 120, 240], forceRecalculate = false) => {
    try {
      const requestData = {
        stock_codes: stockCodes,
        periods: periods,
        force_recalculate: forceRecalculate
      }
      
      const result = await post('/moving-averages/calculate', requestData)
      return result
    } catch (error) {
      console.error('計算均線失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '計算均線失敗'
      }
    }
  }

  /**
   * 查詢股票均線數據
   * @param {String} stockCode - 股票代號
   * @param {Object} params - 查詢參數 { start_date, end_date, periods, page, limit }
   */
  const queryMovingAverages = async (stockCode, params = {}) => {
    try {
      const result = await get(`/moving-averages/query/${stockCode}`, params)
      return result
    } catch (error) {
      console.error('查詢均線數據失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '查詢均線數據失敗'
      }
    }
  }

  /**
   * 驗證均線數據
   */
  const validateMovingAverages = async () => {
    try {
      const result = await get('/moving-averages/validate')
      return result
    } catch (error) {
      console.error('驗證均線數據失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '驗證均線數據失敗'
      }
    }
  }

  /**
   * 清除均線數據
   */
  const clearMovingAverages = async () => {
    try {
      const result = await post('/moving-averages/clear', {})
      return result
    } catch (error) {
      console.error('清除均線數據失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '清除均線數據失敗'
      }
    }
  }

  /**
   * 啟動非同步均線計算任務
   * @param {Array} stockCodes - 股票代號清單（可選，為空則處理所有股票）
   * @param {Array} periods - 均線週期 [5, 10, 24, 72, 120, 240]
   * @param {Boolean} forceRecalculate - 是否強制重新計算
   * @param {Number} batchSize - 批次處理大小
   */
  const startAsyncCalculation = async (stockCodes = null, periods = [5, 10, 24, 72, 120, 240], forceRecalculate = false, batchSize = 50) => {
    try {
      const requestData = {
        stock_codes: stockCodes,
        periods: periods,
        force_recalculate: forceRecalculate,
        batch_size: batchSize
      }
      
      const result = await post('/moving-averages/calculate-async', requestData)
      return result
    } catch (error) {
      console.error('啟動非同步均線計算失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '啟動非同步計算失敗'
      }
    }
  }

  /**
   * 啟動單一股票非同步均線計算任務
   * @param {String} stockCode - 股票代號
   * @param {Array} periods - 均線週期 [5, 10, 24, 72, 120, 240]
   * @param {Boolean} forceRecalculate - 是否強制重新計算
   */
  const startSingleStockAsyncCalculation = async (stockCode, periods = [5, 10, 24, 72, 120, 240], forceRecalculate = false) => {
    return await startAsyncCalculation([stockCode], periods, forceRecalculate)
  }

  /**
   * 取得非同步任務狀態
   * @param {String} taskId - 任務ID
   */
  const getTaskStatus = async (taskId) => {
    try {
      const result = await get(`/moving-averages/task-status/${taskId}`)
      return result
    } catch (error) {
      console.error('取得任務狀態失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '取得任務狀態失敗'
      }
    }
  }

  /**
   * 取消非同步任務
   * @param {String} taskId - 任務ID
   */
  const cancelTask = async (taskId) => {
    try {
      // 使用DELETE方法取消任務
      const { delete: deleteMethod } = useApi()
      const result = await deleteMethod(`/moving-averages/task/${taskId}`)
      return result
    } catch (error) {
      console.error('取消任務失敗:', error)
      return {
        success: false,
        data: null,
        error: error.message || '取消任務失敗'
      }
    }
  }

  return {
    getMovingAveragesStatistics,
    calculateMovingAverages,
    queryMovingAverages,
    validateMovingAverages,
    clearMovingAverages,
    // 新增非同步任務方法
    startAsyncCalculation,
    startSingleStockAsyncCalculation,
    getTaskStatus,
    cancelTask
  }
}