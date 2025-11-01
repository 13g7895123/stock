package middleware

import (
	"net/http"
	"strconv"
	"strings"
)

// CORSConfig CORS 配置
type CORSConfig struct {
	AllowedOrigins []string
	AllowedMethods []string
	AllowedHeaders []string
	MaxAge         int
}

// DefaultCORSConfig 預設 CORS 配置
func DefaultCORSConfig() *CORSConfig {
	return &CORSConfig{
		AllowedOrigins: []string{
			"http://localhost:3000",
			"http://localhost:3302",
			"http://localhost:5173",
		},
		AllowedMethods: []string{
			"GET",
			"POST",
			"PUT",
			"DELETE",
			"OPTIONS",
			"PATCH",
		},
		AllowedHeaders: []string{
			"Content-Type",
			"Authorization",
			"X-Requested-With",
			"Accept",
			"Origin",
		},
		MaxAge: 86400, // 24 小時
	}
}

// CORS 創建 CORS 中間件
func CORS(config *CORSConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCORSConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")

			// 檢查來源是否在允許列表中
			if isOriginAllowed(origin, config.AllowedOrigins) {
				// 設置 CORS 響應頭
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", strings.Join(config.AllowedMethods, ", "))
				w.Header().Set("Access-Control-Allow-Headers", strings.Join(config.AllowedHeaders, ", "))
				w.Header().Set("Access-Control-Max-Age", strconv.Itoa(config.MaxAge))
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			}

			// 處理 Preflight OPTIONS 請求
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusNoContent)
				return
			}

			// 繼續處理後續請求
			next.ServeHTTP(w, r)
		})
	}
}

// isOriginAllowed 檢查來源是否被允許
func isOriginAllowed(origin string, allowedOrigins []string) bool {
	// 空來源不允許
	if origin == "" {
		return false
	}

	// 檢查是否在允許列表中
	for _, allowed := range allowedOrigins {
		// 支持通配符 *
		if allowed == "*" {
			return true
		}

		// 精確匹配
		if origin == allowed {
			return true
		}

		// 支持子域名通配符（例如：*.example.com）
		if strings.HasPrefix(allowed, "*.") {
			domain := strings.TrimPrefix(allowed, "*")
			if strings.HasSuffix(origin, domain) {
				return true
			}
		}
	}

	return false
}
