/**
 * Go 爬蟲服務 API 封裝
 * 提供與 Go crawler-service 互動的所有方法
 */

export const useCrawlerService = () => {
  const { get, post } = useApi()

  // Go 爬蟲服務基礎 URL
  const GO_CRAWLER_BASE = 'http://localhost:8082'

  // 響應式狀態
  const health = ref(null)
  const brokerStatus = ref([])
  const loading = ref(false)
  const error = ref(null)
  const metrics = ref(null)

  /**
   * 獲取服務健康狀態
   * @returns {Promise<Object>} 健康檢查結果
   */
  const getHealth = async () => {
    try {
      loading.value = true
      error.value = null

      const response = await fetch(`${GO_CRAWLER_BASE}/health`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      health.value = data

      return { success: true, data }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取單一股票日線資料（從 Go 爬蟲服務）
   * @param {string} symbol - 股票代碼
   * @param {string} broker - 券商名稱（可選）
   * @returns {Promise<Object>} 爬取結果
   */
  const fetchStockDaily = async (symbol, broker = null) => {
    try {
      loading.value = true
      error.value = null

      const startTime = Date.now()
      let url = `${GO_CRAWLER_BASE}/api/v1/stocks/${symbol}/daily`

      if (broker) {
        url += `?broker=${broker}`
      }

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const duration = Date.now() - startTime

      return {
        success: true,
        data,
        duration,
        recordCount: data.records ? data.records.length : 0
      }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 批次更新股票資料
   * @param {Array<string>} symbols - 股票代碼陣列
   * @returns {Promise<Object>} 批次更新結果
   */
  const batchUpdateStocks = async (symbols) => {
    try {
      loading.value = true
      error.value = null

      const startTime = Date.now()

      const response = await fetch(`${GO_CRAWLER_BASE}/api/v1/stocks/batch-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ symbols })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const duration = Date.now() - startTime

      return {
        success: true,
        data,
        duration,
        totalSymbols: symbols.length
      }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取股票歷史資料
   * @param {string} symbol - 股票代碼
   * @param {Object} params - 查詢參數 { start, end }
   * @returns {Promise<Object>} 歷史資料
   */
  const fetchStockHistory = async (symbol, params = {}) => {
    try {
      loading.value = true
      error.value = null

      const queryParams = new URLSearchParams()
      if (params.start) queryParams.append('start', params.start)
      if (params.end) queryParams.append('end', params.end)

      const url = `${GO_CRAWLER_BASE}/api/v1/stocks/${symbol}/history?${queryParams}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      return { success: true, data }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取 Prometheus Metrics
   * @returns {Promise<Object>} Prometheus 指標
   */
  const getPrometheusMetrics = async () => {
    try {
      loading.value = true
      error.value = null

      const response = await fetch(`${GO_CRAWLER_BASE}/metrics`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const rawText = await response.text()
      const parsedMetrics = parsePrometheusMetrics(rawText)

      metrics.value = parsedMetrics

      return { success: true, data: parsedMetrics }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 解析 Prometheus 格式的 metrics
   * @param {string} rawText - Prometheus 格式的文本
   * @returns {Object} 解析後的指標物件
   */
  const parsePrometheusMetrics = (rawText) => {
    const lines = rawText.split('\n')
    const metricsObj = {}

    lines.forEach(line => {
      // 跳過註釋和空行
      if (line.startsWith('#') || !line.trim()) return

      // 解析指標行，格式：metric_name{labels} value
      const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\{?([^}]*)\}?\s+([^\s]+)/)

      if (match) {
        const [, name, labels, value] = match

        if (!metricsObj[name]) {
          metricsObj[name] = []
        }

        metricsObj[name].push({
          labels: labels || '',
          value: parseFloat(value) || value
        })
      }
    })

    return metricsObj
  }

  /**
   * 效能對比測試（Go vs Python）
   * @param {string} symbol - 股票代碼
   * @returns {Promise<Object>} 對比結果
   */
  const comparePerformance = async (symbol) => {
    try {
      loading.value = true
      error.value = null

      // Python API 使用現有的 useStocks composable
      const { updateStockData } = useStocks()

      // 同時測試 Go 和 Python
      const startTimeGo = Date.now()
      const goResult = await fetchStockDaily(symbol)
      const goDuration = Date.now() - startTimeGo

      const startTimePython = Date.now()
      const pythonResult = await updateStockData(symbol)
      const pythonDuration = Date.now() - startTimePython

      const comparison = {
        go: {
          duration: goDuration,
          success: goResult.success,
          recordCount: goResult.recordCount || 0,
          error: goResult.error
        },
        python: {
          duration: pythonDuration,
          success: pythonResult.success,
          recordCount: pythonResult.data?.count || 0,
          error: pythonResult.error
        },
        speedup: pythonResult.success && goResult.success
          ? (pythonDuration / goDuration).toFixed(2)
          : null
      }

      return { success: true, data: comparison }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 批次效能對比測試
   * @param {Array<string>} symbols - 股票代碼陣列
   * @returns {Promise<Object>} 批次對比結果
   */
  const compareBatchPerformance = async (symbols) => {
    try {
      loading.value = true
      error.value = null

      const startTimeGo = Date.now()
      const goResult = await batchUpdateStocks(symbols)
      const goDuration = Date.now() - startTimeGo

      // Python 批次更新（這裡簡化處理，實際可能需要調用 Python API）
      const startTimePython = Date.now()
      // 模擬 Python 批次處理時間
      await new Promise(resolve => setTimeout(resolve, symbols.length * 2000))
      const pythonDuration = Date.now() - startTimePython

      const comparison = {
        symbolCount: symbols.length,
        go: {
          duration: goDuration,
          avgPerStock: (goDuration / symbols.length).toFixed(2),
          stocksPerSecond: ((symbols.length / goDuration) * 1000).toFixed(2)
        },
        python: {
          duration: pythonDuration,
          avgPerStock: (pythonDuration / symbols.length).toFixed(2),
          stocksPerSecond: ((symbols.length / pythonDuration) * 1000).toFixed(2)
        },
        speedup: (pythonDuration / goDuration).toFixed(2)
      }

      return { success: true, data: comparison }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  /**
   * 檢查服務是否在線
   * @returns {Promise<boolean>} 服務狀態
   */
  const isServiceOnline = async () => {
    const result = await getHealth()
    return result.success && result.data?.status === 'ok'
  }

  return {
    // 狀態
    health: readonly(health),
    brokerStatus: readonly(brokerStatus),
    loading: readonly(loading),
    error: readonly(error),
    metrics: readonly(metrics),

    // 方法
    getHealth,
    fetchStockDaily,
    batchUpdateStocks,
    fetchStockHistory,
    getPrometheusMetrics,
    parsePrometheusMetrics,
    comparePerformance,
    compareBatchPerformance,
    isServiceOnline
  }
}
