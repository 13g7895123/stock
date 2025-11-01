#!/usr/bin/env python3
"""測試 Go 爬蟲服務的 parser 修正"""

import asyncio
import httpx

async def test_python_parser():
    """測試 Python 版本的解析器"""
    print("=" * 60)
    print("測試 Python 解析器")
    print("=" * 60)
    
    base_url = "http://fubon-ebrokerdj.fbs.com.tw/"
    url = f"{base_url.rstrip('/')}/z/BCD/czkc1.djbcd?a=2330&b=A&c=2880&E=1&ver=5"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                content = response.text
                print(f"✓ 成功獲取資料，長度: {len(content)} bytes")
                
                # 簡單解析
                parts = content.split(',')
                dates = [p.strip() for p in parts if '/' in p and len(p.split('/')) == 3]
                numbers = []
                for p in parts:
                    try:
                        numbers.append(float(p.strip()))
                    except:
                        pass
                
                print(f"✓ 找到 {len(dates)} 個日期")
                print(f"✓ 找到 {len(numbers)} 個數字")
                
                if len(dates) > 0 and len(numbers) > 0:
                    data_points_per_date = len(numbers) // len(dates)
                    print(f"✓ 每個日期對應 {data_points_per_date} 個數據點")
                    
                    # 顯示第一筆資料
                    if len(dates) > 0 and len(numbers) >= 5:
                        print(f"\n第一筆資料範例:")
                        print(f"  日期: {dates[0]}")
                        print(f"  開盤: {numbers[0]:.2f}")
                        print(f"  最高: {numbers[1]:.2f}")
                        print(f"  最低: {numbers[2]:.2f}")
                        print(f"  收盤: {numbers[3]:.2f}")
                        print(f"  成交量: {int(numbers[4])}")
                
                return True
            else:
                print(f"✗ HTTP 錯誤: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return False

async def test_go_api():
    """測試 Go API 端點"""
    print("\n" + "=" * 60)
    print("測試 Go API /api/v1/stocks/2330/daily")
    print("=" * 60)
    
    url = "http://localhost:8080/api/v1/stocks/2330/daily"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ API 調用成功")
                print(f"回應資料:")
                
                import json
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 檢查資料結構
                if 'success' in data and data['success']:
                    print(f"\n✓ 資料解析成功")
                    if 'data' in data and len(data['data']) > 0:
                        print(f"✓ 獲得 {len(data['data'])} 筆資料")
                        
                        # 顯示第一筆
                        first_record = data['data'][0]
                        print(f"\n第一筆資料:")
                        print(f"  股票代號: {first_record.get('stock_code')}")
                        print(f"  日期: {first_record.get('trade_date')}")
                        print(f"  開盤: {first_record.get('open_price')}")
                        print(f"  最高: {first_record.get('high_price')}")
                        print(f"  最低: {first_record.get('low_price')}")
                        print(f"  收盤: {first_record.get('close_price')}")
                        print(f"  成交量: {first_record.get('volume')}")
                        print(f"  來源: {first_record.get('data_source')}")
                    
                    return True
                else:
                    print(f"✗ 資料解析失敗")
                    return False
            else:
                print(f"✗ API 錯誤: {response.status_code}")
                print(f"錯誤內容: {response.text}")
                return False
                
    except httpx.ConnectError:
        print(f"✗ 無法連接到 Go 服務 (localhost:8080)")
        print(f"  請確認服務是否正在運行")
        return False
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主測試流程"""
    print("\n" + "=" * 60)
    print("Go 爬蟲服務 Parser 修正驗證")
    print("=" * 60 + "\n")
    
    # 測試 Python 解析器（驗證資料格式）
    python_ok = await test_python_parser()
    
    # 測試 Go API
    go_ok = await test_go_api()
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"Python 解析器: {'✓ 通過' if python_ok else '✗ 失敗'}")
    print(f"Go API 服務: {'✓ 通過' if go_ok else '✗ 失敗'}")
    print("=" * 60)
    
    if python_ok and go_ok:
        print("\n✓ 所有測試通過！修正成功！")
        return 0
    else:
        print("\n✗ 部分測試失敗，請檢查錯誤訊息")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
