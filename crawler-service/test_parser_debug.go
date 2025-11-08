package main

import (
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

func main() {
	// 測試獲取券商資料
	url := "http://fubon-ebrokerdj.fbs.com.tw/z/BCD/czkc1.djbcd?a=2330&b=A&c=2880&E=1&ver=5"
	
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("User-Agent", "Mozilla/5.0")
	
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	content := string(body)
	
	fmt.Printf("Status: %d\n", resp.StatusCode)
	fmt.Printf("Content length: %d\n", len(content))
	fmt.Printf("First 500 chars:\n%s\n", content[:min(500, len(content))])
	
	// 解析資料
	parts := strings.Split(content, ",")
	fmt.Printf("\nTotal parts: %d\n", len(parts))
	
	var dates []string
	var numbers []float64
	
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		
		if strings.Contains(part, "/") && len(strings.Split(part, "/")) == 3 {
			dates = append(dates, part)
		} else {
			var num float64
			if _, err := fmt.Sscanf(part, "%f", &num); err == nil {
				numbers = append(numbers, num)
			}
		}
	}
	
	fmt.Printf("Found %d dates\n", len(dates))
	fmt.Printf("Found %d numbers\n", len(numbers))
	
	if len(dates) > 0 {
		fmt.Printf("\nFirst 3 dates: %v\n", dates[:min(3, len(dates))])
		fmt.Printf("Last 3 dates: %v\n", dates[max(0, len(dates)-3):])
	}
	
	if len(numbers) > 0 && len(dates) > 0 {
		dataPointsPerDate := len(numbers) / len(dates)
		fmt.Printf("\nData points per date: %d\n", dataPointsPerDate)
		
		if dataPointsPerDate > 0 {
			fmt.Printf("\nFirst date data points: %v\n", numbers[:min(dataPointsPerDate, len(numbers))])
		}
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
