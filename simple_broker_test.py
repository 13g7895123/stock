"""Simple broker URL test without Unicode characters"""

import asyncio
import httpx

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

def build_test_url(base_url, stock_id="2330"):
    base_url = base_url.rstrip('/')
    return f"{base_url}/z/BCD/czkc1.djbcd?a={stock_id}&b=A&c=2880&E=1&ver=5"

async def test_broker_url(session, base_url, stock_id="2330"):
    url = build_test_url(base_url, stock_id)
    
    print(f"Testing {base_url}...")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = await session.get(url, headers=headers, timeout=30.0)
        
        content_length = len(response.text)
        content_preview = response.text[:200]
        
        if response.status_code == 200:
            print(f"SUCCESS: {base_url} (content length: {content_length})")
            if content_length > 0:
                print(f"Content preview: {content_preview}")
            return True, response.text
        else:
            print(f"HTTP ERROR: {base_url} - Status {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except httpx.TimeoutException:
        print(f"TIMEOUT: {base_url}")
        return False, "Timeout"
        
    except httpx.ConnectError as e:
        print(f"CONNECTION ERROR: {base_url} - {str(e)}")
        return False, f"Connection error: {str(e)}"
        
    except Exception as e:
        print(f"ERROR: {base_url} - {str(e)}")
        return False, str(e)

async def test_yahoo_finance(session, stock_id="2330"):
    """Test Yahoo Finance as alternative source"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"
    
    print(f"\nTesting Yahoo Finance: {url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        response = await session.get(url, headers=headers, timeout=30.0)
        
        if response.status_code == 200:
            content_length = len(response.text)
            print(f"YAHOO SUCCESS: Content length {content_length}")
            print(f"Content preview: {response.text[:300]}")
            return True, response.text
        else:
            print(f"YAHOO HTTP ERROR: Status {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        print(f"YAHOO ERROR: {str(e)}")
        return False, str(e)

async def main():
    print("=== Broker Data Source Availability Test ===\n")
    
    success_count = 0
    total_count = len(BROKER_URLS)
    successful_sources = []
    
    async with httpx.AsyncClient() as session:
        # Test broker URLs
        for base_url in BROKER_URLS:
            success, content = await test_broker_url(session, base_url, "2330")
            if success:
                success_count += 1
                successful_sources.append((base_url, content))
            print("-" * 60)
            await asyncio.sleep(1)  # Avoid too frequent requests
        
        # Test Yahoo Finance
        yahoo_success, yahoo_content = await test_yahoo_finance(session, "2330")
        if yahoo_success:
            successful_sources.append(("Yahoo Finance", yahoo_content))
    
    print(f"\n=== SUMMARY ===")
    print(f"Broker sites: {success_count}/{total_count} successful")
    print(f"Yahoo Finance: {'SUCCESS' if yahoo_success else 'FAILED'}")
    print(f"Total successful sources: {len(successful_sources)}")
    
    # Show successful content for analysis
    if successful_sources:
        print("\n=== SUCCESSFUL SOURCES DATA ANALYSIS ===")
        for source_name, content in successful_sources:
            print(f"\n--- {source_name} ---")
            print(f"Content length: {len(content)}")
            # Try to identify data format
            if content.strip().startswith("{"):
                print("Format: JSON")
            elif "\t" in content:
                print("Format: TAB-separated")
            elif "," in content:
                print("Format: CSV/Comma-separated")
            else:
                print("Format: Unknown/Text")
            
            # Show first few lines
            lines = content.split('\n')[:5]
            print("First 5 lines:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"  {i}: {line[:100]}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())