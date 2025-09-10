/**
 * 股票相關API組合式函數
 */

export const useStocks = () => {
  const { get, post } = useApi()

  // 響應式資料
  const stocks = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  /**
   * 獲取股票列表數量
   */
  const getStockCount = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/sync/stocks/count')
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 同步股票列表
   */
  const syncStockList = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await post('/sync/stocks')
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 爬取並同步股票列表
   */
  const crawlStockList = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/sync/stocks/crawl')
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票列表
   */
  const getStockList = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/data/stocks', params)
      
      if (result.success) {
        stocks.value = result.data.stocks || result.data
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票歷史資料
   */
  const getStockHistory = async (symbol, params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get(`/data/history/${symbol}`, params)
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票統計資訊
   */
  const getStockStats = async (symbol) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get(`/data/history/${symbol}/stats`)
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票最新交易日期
   */
  const getLatestTradeDate = async (symbol) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get(`/data/history/${symbol}/latest-date`)
      
      if (result.success) {
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  return {
    // 響應式資料
    stocks: readonly(stocks),
    loading: readonly(loading),
    error: readonly(error),
    
    // 方法
    getStockCount,
    syncStockList,
    crawlStockList,
    getStockList,
    getStockHistory,
    getStockStats,
    getLatestTradeDate
  }
}