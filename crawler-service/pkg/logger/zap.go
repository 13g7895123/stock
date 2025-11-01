package logger

import (
	"os"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var log *zap.Logger

// Init 初始化日誌系統
func Init(level string, format string, output string, filePath string) error {
	// 設定日誌等級
	logLevel := getLogLevel(level)

	// 設定編碼器
	var encoder zapcore.Encoder
	if format == "json" {
		encoder = zapcore.NewJSONEncoder(getEncoderConfig())
	} else {
		encoder = zapcore.NewConsoleEncoder(getEncoderConfig())
	}

	// 設定輸出
	var writeSyncer zapcore.WriteSyncer
	if output == "file" && filePath != "" {
		file, err := os.OpenFile(filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			return err
		}
		writeSyncer = zapcore.AddSync(file)
	} else {
		writeSyncer = zapcore.AddSync(os.Stdout)
	}

	// 建立 core
	core := zapcore.NewCore(encoder, writeSyncer, logLevel)

	// 建立 logger
	log = zap.New(core,
		zap.AddCaller(),
		zap.AddStacktrace(zapcore.ErrorLevel),
	)

	return nil
}

// getEncoderConfig 獲取編碼器配置
func getEncoderConfig() zapcore.EncoderConfig {
	return zapcore.EncoderConfig{
		TimeKey:        "ts",
		LevelKey:       "level",
		NameKey:        "logger",
		CallerKey:      "caller",
		FunctionKey:    zapcore.OmitKey,
		MessageKey:     "msg",
		StacktraceKey:  "stacktrace",
		LineEnding:     zapcore.DefaultLineEnding,
		EncodeLevel:    zapcore.LowercaseLevelEncoder,
		EncodeTime:     zapcore.ISO8601TimeEncoder,
		EncodeDuration: zapcore.SecondsDurationEncoder,
		EncodeCaller:   zapcore.ShortCallerEncoder,
	}
}

// getLogLevel 獲取日誌等級
func getLogLevel(level string) zapcore.Level {
	switch level {
	case "debug":
		return zapcore.DebugLevel
	case "info":
		return zapcore.InfoLevel
	case "warn":
		return zapcore.WarnLevel
	case "error":
		return zapcore.ErrorLevel
	default:
		return zapcore.InfoLevel
	}
}

// Debug 記錄 debug 等級日誌
func Debug(msg string, fields ...zap.Field) {
	log.Debug(msg, fields...)
}

// Info 記錄 info 等級日誌
func Info(msg string, fields ...zap.Field) {
	log.Info(msg, fields...)
}

// Warn 記錄 warn 等級日誌
func Warn(msg string, fields ...zap.Field) {
	log.Warn(msg, fields...)
}

// Error 記錄 error 等級日誌
func Error(msg string, fields ...zap.Field) {
	log.Error(msg, fields...)
}

// Fatal 記錄 fatal 等級日誌並退出程式
func Fatal(msg string, fields ...zap.Field) {
	log.Fatal(msg, fields...)
}

// Now 返回當前時間
func Now() time.Time {
	return time.Now()
}

// Since 返回從指定時間開始經過的時間
func Since(t time.Time) time.Duration {
	return time.Since(t)
}

// With 建立帶有額外欄位的 logger
func With(fields ...zap.Field) *zap.Logger {
	return log.With(fields...)
}

// Sync 刷新日誌緩衝區
func Sync() error {
	return log.Sync()
}

// GetLogger 獲取 zap logger 實例
func GetLogger() *zap.Logger {
	return log
}
