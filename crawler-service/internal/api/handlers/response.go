package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// Response 標準響應格式
type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   *ErrorInfo  `json:"error,omitempty"`
}

// ErrorInfo 錯誤資訊
type ErrorInfo struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// WriteJSON 寫入 JSON 響應
func WriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	response := Response{
		Success: status < 400,
		Data:    data,
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Error("Failed to encode JSON response", zap.Error(err))
	}
}

// WriteError 寫入錯誤響應
func WriteError(w http.ResponseWriter, status int, code, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	response := Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    code,
			Message: message,
		},
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		logger.Error("Failed to encode error response", zap.Error(err))
	}
}

// WriteSuccess 寫入成功響應
func WriteSuccess(w http.ResponseWriter, data interface{}) {
	WriteJSON(w, http.StatusOK, data)
}

// WriteBadRequest 寫入錯誤請求響應
func WriteBadRequest(w http.ResponseWriter, message string) {
	WriteError(w, http.StatusBadRequest, "BAD_REQUEST", message)
}

// WriteNotFound 寫入未找到響應
func WriteNotFound(w http.ResponseWriter, message string) {
	WriteError(w, http.StatusNotFound, "NOT_FOUND", message)
}

// WriteInternalError 寫入內部錯誤響應
func WriteInternalError(w http.ResponseWriter, message string) {
	WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", message)
}
