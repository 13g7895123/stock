"""測試券商網站URL的可用性和資料格式"""

import asyncio
import httpx
from typing import List, Dict, Any

# 測試用的券商URL
BROKER_URLS = [
    "http://fubon-ebrokerdj.fbs.com.tw/",
    "http://justdata.moneydj.com/",
    "http://jdata.yuanta.com.tw/",
    "http://moneydj.emega.com.tw/",
    "http://djfubonholdingfund.fbs.com.tw/",
    "https://sjmain.esunsec.com.tw/",
    "http://kgieworld.moneydj.com/",
    "http://newjust.masterlink.com.tw/"
]

def build_test_url(base_url: str, stock_id: str = "2330") -> str:
    """建立測試URL"""
    base_url = base_url.rstrip('/')
    return f"{base_url}/z/BCD/czkc1.djbcd?a={stock_id}&b=A&c=2880&E=1&ver=5"

async def test_broker_url(session: httpx.AsyncClient, base_url: str, stock_id: str = "2330") -> Dict[str, Any]:
    """測試單一券商URL"""
    url = build_test_url(base_url, stock_id)
    
    result = {
        "base_url": base_url,
        "test_url": url,
        "status": "unknown",
        "status_code": None,
        "content_length": 0,
        "content_preview": "",
        "error": None
    }
    
    try:
        print(f"測試 {base_url}...")
        
        # 添加適當的headers來模擬瀏覽器請求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        response = await session.get(url, headers=headers, timeout=30.0)
        
        result["status_code"] = response.status_code
        result["content_length"] = len(response.text)
        result["content_preview"] = response.text[:200]  # 前200字符
        
        if response.status_code == 200:
            result["status"] = "success"
            print(f"SUCCESS: {base_url} (content length: {result['content_length']})")
        else:
            result["status"] = "http_error"
            result["error"] = f"HTTP {response.status_code}"
            print(f"HTTP ERROR: {base_url} - {response.status_code}")
            
    except httpx.TimeoutException:
        result["status"] = "timeout"
        result["error"] = "Request timeout"
        print(f"TIMEOUT: {base_url}")
        
    except httpx.ConnectError as e:
        result["status"] = "connect_error"
        result["error"] = f"Connection error: {str(e)}"
        print(f"CONNECTION ERROR: {base_url} - {str(e)}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"ERROR: {base_url} - {str(e)}")
    
    return result

async def test_alternative_urls(session: httpx.AsyncClient, stock_id: str = "2330") -> List[Dict[str, Any]]:
    """測試替代的資料來源URL"""
    
    # Yahoo Finance 台股資料
    yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"
    
    # Goodinfo 資料
    goodinfo_url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
    
    alternative_urls = [yahoo_url, goodinfo_url]
    results = []
    
    for url in alternative_urls:
        result = {
            "source": "alternative",
            "test_url": url,
            "status": "unknown",
            "status_code": None,
            "content_length": 0,
            "content_preview": "",
            "error": None
        }
        
        try:
            print(f"測試替代來源: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
            
            response = await session.get(url, headers=headers, timeout=30.0)
            
            result["status_code"] = response.status_code
            result["content_length"] = len(response.text)
            result["content_preview"] = response.text[:300]
            
            if response.status_code == 200:
                result["status"] = "success"
                print(f"ALT SOURCE SUCCESS: {url} (content length: {result['content_length']})")
            else:
                result["status"] = "http_error"
                result["error"] = f"HTTP {response.status_code}"
                print(f"ALT SOURCE HTTP ERROR: {url} - {response.status_code}")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"ALT SOURCE ERROR: {url} - {str(e)}")
        
        results.append(result)
    
    return results

async def main():
    """主要測試函數"""
    print("=== 券商網站資料來源可用性測試 ===\n")
    
    async with httpx.AsyncClient() as session:
        # 測試原始券商URLs
        broker_results = []
        for base_url in BROKER_URLS:
            result = await test_broker_url(session, base_url, "2330")
            broker_results.append(result)
            await asyncio.sleep(1)  # 避免請求過於頻繁
        
        print("\n=== 替代資料來源測試 ===\n")
        
        # 測試替代資料來源
        alt_results = await test_alternative_urls(session, "2330")
        
        print("\n=== 測試結果摘要 ===\n")
        
        # 統計結果
        success_count = len([r for r in broker_results if r["status"] == "success"])
        total_count = len(broker_results)
        
        print(f"券商網站測試結果: {success_count}/{total_count} 成功")
        
        for result in broker_results:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"{status_emoji} {result['base_url']}: {result['status']} - {result.get('error', 'OK')}")
        
        print("\n替代來源測試結果:")
        for result in alt_results:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"{status_emoji} {result['test_url']}: {result['status']} - {result.get('error', 'OK')}")
        
        # 顯示成功的內容預覽
        print("\n=== 成功回應內容預覽 ===\n")
        for result in broker_results + alt_results:
            if result["status"] == "success" and result["content_preview"]:
                print(f"\n--- {result.get('base_url', result.get('test_url'))} ---")
                print(f"內容長度: {result['content_length']}")
                print(f"內容預覽:\n{result['content_preview']}")
                print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())