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
   * 獲取股票列表（從資料庫）
   */
  const getStockList = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/stocks/list', params)
      
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

  /**
   * 更新單一股票歷史資料（爬取日線資料）
   */
  const updateStockData = async (symbol) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get(`/data/daily/${symbol}`)
      
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
   * 更新所有股票歷史資料（使用TWSE API）
   * @deprecated 使用 batchUpdateWithBrokerCrawler 代替
   */
  const updateAllStockData = async (symbols = null) => {
    loading.value = true
    error.value = null
    
    try {
      // 修正：直接發送 symbols 陣列，而不是包裝在對象中
      const result = await post('/stocks/update-all', symbols)
      
      if (result.success || result.message) {
        return result
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 使用broker爬蟲批次更新股票歷史資料（使用8個broker網站）
   */
  const batchUpdateWithBrokerCrawler = async (symbols = null) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await post('/data/daily/batch-update', symbols)
      
      if (result.success || result.status === 'completed') {
        return result.data || result
      } else {
        error.value = result.error || result.detail
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取整體歷史資料統計
   */
  const getOverallStats = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/data/history/overview')
      
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
   * 獲取有歷史資料的股票清單
   */
  const getStocksWithData = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get('/data/history/stocks-with-data', params)
      
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
   * 獲取所有有資料的股票（分頁獲取）
   */
  const getAllStocksWithData = async () => {
    loading.value = true
    error.value = null
    
    try {
      let allStocks = []
      let page = 1
      const limit = 1000 // 使用最大允許的限制
      
      while (true) {
        const result = await get('/data/history/stocks-with-data', { 
          page, 
          limit,
          sort_by: 'stock_code',
          sort_order: 'asc'
        })
        
        if (!result.success) {
          error.value = result.error
          return { success: false, error: result.error, stocks: [] }
        }
        
        const pageStocks = result.data?.stocks || []
        allStocks = allStocks.concat(pageStocks)
        
        // 如果這頁的股票數量少於limit，表示已經是最後一頁
        if (pageStocks.length < limit) {
          break
        }
        
        page++
      }
      
      return { 
        success: true, 
        stocks: allStocks,
        total: allStocks.length
      }
    } catch (error) {
      error.value = error.message
      return { success: false, error: error.message, stocks: [] }
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
    getLatestTradeDate,
    updateStockData,
    updateAllStockData, // 保留舊的API以相容性
    batchUpdateWithBrokerCrawler, // 新的broker爬蟲API
    getOverallStats,
    getStocksWithData, // 新的有資料股票清單API
    getAllStocksWithData // 獲取所有有資料股票（分頁）
  }
}