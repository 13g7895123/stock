"""Parse broker data format and extract OHLCV data"""

import asyncio
import httpx
from datetime import datetime

async def get_sample_data():
    """Get sample data from a working broker site"""
    
    base_url = "http://fubon-ebrokerdj.fbs.com.tw/"
    url = f"{base_url.rstrip('/')}/z/BCD/czkc1.djbcd?a=2330&b=A&c=2880&E=1&ver=5"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    async with httpx.AsyncClient() as session:
        response = await session.get(url, headers=headers, timeout=30.0)
        
        if response.status_code == 200:
            return response.text
        else:
            return None

def parse_broker_data(content):
    """Parse the broker data format"""
    
    parts = content.split(',')
    
    # Separate dates and numbers
    dates = []
    numbers = []
    
    for part in parts:
        part = part.strip()
        if '/' in part and len(part.split('/')) == 3:
            dates.append(part)
        else:
            try:
                num = float(part)
                numbers.append(num)
            except:
                # Skip non-numeric parts
                pass
    
    print(f"Found {len(dates)} dates and {len(numbers)} numbers")
    
    if len(dates) == 0:
        return []
    
    # Calculate how many data points per date
    data_points_per_date = len(numbers) // len(dates)
    print(f"Data points per date: {data_points_per_date}")
    
    if data_points_per_date < 4:  # Need at least OHLC
        print("Not enough data points per date")
        return []
    
    # Parse the data
    parsed_data = []
    
    for i, date_str in enumerate(dates):
        try:
            # Parse date
            trade_date = datetime.strptime(date_str, '%Y/%m/%d')
            
            # Get corresponding data points
            start_idx = i * data_points_per_date
            end_idx = start_idx + data_points_per_date
            
            if end_idx <= len(numbers):
                data_points = numbers[start_idx:end_idx]
                
                if len(data_points) >= 5:
                    # Assuming OHLCV format
                    open_price = data_points[0]
                    high_price = data_points[1]
                    low_price = data_points[2]
                    close_price = data_points[3]
                    volume = int(data_points[4])
                    
                    # Basic validation
                    if (open_price > 0 and high_price > 0 and low_price > 0 and 
                        close_price > 0 and volume >= 0 and
                        low_price <= open_price <= high_price and
                        low_price <= close_price <= high_price):
                        
                        parsed_data.append({
                            'date': date_str,
                            'trade_date': trade_date,
                            'open_price': open_price,
                            'high_price': high_price,
                            'low_price': low_price,
                            'close_price': close_price,
                            'volume': volume,
                            'adjusted_close': close_price  # Assuming close price is already adjusted
                        })
        
        except Exception as e:
            print(f"Error parsing data for date {date_str}: {e}")
            continue
    
    return parsed_data

async def main():
    print("Getting and parsing broker data...")
    content = await get_sample_data()
    
    if content:
        parsed_data = parse_broker_data(content)
        
        print(f"\nSuccessfully parsed {len(parsed_data)} records")
        
        if parsed_data:
            print("\nFirst 10 records:")
            for i, record in enumerate(parsed_data[:10]):
                print(f"{i+1:2}: {record['date']} - "
                      f"O:{record['open_price']:7.2f} "
                      f"H:{record['high_price']:7.2f} "
                      f"L:{record['low_price']:7.2f} "
                      f"C:{record['close_price']:7.2f} "
                      f"V:{record['volume']:>8}")
            
            print("\nLast 10 records:")
            for i, record in enumerate(parsed_data[-10:], len(parsed_data)-9):
                print(f"{i:2}: {record['date']} - "
                      f"O:{record['open_price']:7.2f} "
                      f"H:{record['high_price']:7.2f} "
                      f"L:{record['low_price']:7.2f} "
                      f"C:{record['close_price']:7.2f} "
                      f"V:{record['volume']:>8}")
            
            # Show date range
            first_date = parsed_data[0]['trade_date']
            last_date = parsed_data[-1]['trade_date']
            print(f"\nDate range: {first_date.date()} to {last_date.date()}")
            print(f"Total trading days: {len(parsed_data)}")
        
    else:
        print("Failed to get sample data")

if __name__ == "__main__":
    asyncio.run(main())