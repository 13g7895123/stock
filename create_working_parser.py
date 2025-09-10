"""Create a working parser for the broker data format"""

import asyncio
import httpx
from datetime import datetime
import re

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

def parse_mixed_format_data(content):
    """Parse the mixed format broker data"""
    
    parts = content.split(',')
    
    # Step 1: Extract all dates and separate all numeric values
    dates = []
    all_numbers = []
    
    for part in parts:
        part = part.strip()
        
        # Handle mixed date-price format like "2025/09/09 258.2756"
        if '/' in part and ' ' in part:
            # Split the mixed format
            date_part, price_part = part.split(' ', 1)
            dates.append(date_part)
            try:
                all_numbers.append(float(price_part))
            except ValueError:
                pass
        elif '/' in part and len(part.split('/')) == 3:
            # Pure date
            dates.append(part)
        elif ' ' in part:
            # Handle mixed volume-price format like "1195 258.2756"
            space_parts = part.split()
            for space_part in space_parts:
                try:
                    all_numbers.append(float(space_part))
                except ValueError:
                    pass
        else:
            # Single number
            try:
                all_numbers.append(float(part))
            except ValueError:
                pass
    
    print(f"Extracted {len(dates)} dates and {len(all_numbers)} numbers")
    
    if len(dates) == 0 or len(all_numbers) == 0:
        return []
    
    # Step 2: Try to match dates with data
    # Assuming each date has 5 data points: Open, High, Low, Close, Volume
    data_per_date = len(all_numbers) // len(dates)
    print(f"Data points per date: {data_per_date}")
    
    if data_per_date < 4:
        print("Not enough data points per date")
        return []
    
    # Step 3: Parse the data
    parsed_data = []
    
    for i, date_str in enumerate(dates):
        try:
            # Parse date
            trade_date = datetime.strptime(date_str, '%Y/%m/%d')
            
            # Get corresponding data points
            start_idx = i * data_per_date
            end_idx = start_idx + data_per_date
            
            if end_idx <= len(all_numbers):
                data_points = all_numbers[start_idx:end_idx]
                
                # Try different interpretations of the data
                if len(data_points) >= 5:
                    # Method 1: OHLCV format
                    open_price = data_points[0]
                    high_price = data_points[1] 
                    low_price = data_points[2]
                    close_price = data_points[3]
                    volume = int(data_points[4]) if data_points[4] > 1000 else int(data_points[4] * 1000)
                    
                    # Validate the data makes sense
                    if (all(p > 0 for p in [open_price, high_price, low_price, close_price]) and
                        volume > 0 and
                        low_price <= min(open_price, close_price) and
                        high_price >= max(open_price, close_price)):
                        
                        parsed_data.append({
                            'stock_id': '2330',
                            'trade_date': trade_date,
                            'open_price': open_price,
                            'high_price': high_price,
                            'low_price': low_price,
                            'close_price': close_price,
                            'volume': volume,
                            'adjusted_close': close_price
                        })
                
                elif len(data_points) >= 4:
                    # Method 2: OHLC format (no volume)
                    open_price = data_points[0]
                    high_price = data_points[1] 
                    low_price = data_points[2]
                    close_price = data_points[3]
                    
                    # Validate the data makes sense
                    if (all(p > 0 for p in [open_price, high_price, low_price, close_price]) and
                        low_price <= min(open_price, close_price) and
                        high_price >= max(open_price, close_price)):
                        
                        parsed_data.append({
                            'stock_id': '2330',
                            'trade_date': trade_date,
                            'open_price': open_price,
                            'high_price': high_price,
                            'low_price': low_price,
                            'close_price': close_price,
                            'volume': 0,  # Unknown volume
                            'adjusted_close': close_price
                        })
        
        except Exception as e:
            continue
    
    return parsed_data

def try_alternative_parsing(content):
    """Try alternative parsing method"""
    
    parts = content.split(',')
    
    # Maybe the data is structured differently
    # Let's try to find the actual OHLCV pattern by looking at recent dates
    
    print("Trying alternative parsing...")
    
    # Look for recent dates (last 10 trading days)
    recent_dates = []
    recent_data_start = -1
    
    for i, part in enumerate(parts):
        if '2025/' in part:
            recent_dates.append((i, part.strip()))
            if recent_data_start == -1:
                recent_data_start = i
    
    if len(recent_dates) >= 5:  # Need at least 5 recent dates
        print(f"Found {len(recent_dates)} recent dates starting at position {recent_data_start}")
        
        # Show recent dates and following data
        for pos, date in recent_dates[-5:]:  # Last 5 dates
            print(f"Date at {pos}: {date}")
            
            # Show next 10 values after this date
            next_values = []
            for j in range(pos + 1, min(pos + 11, len(parts))):
                try:
                    val = float(parts[j])
                    next_values.append(val)
                except:
                    next_values.append(f"'{parts[j]}'")
            
            print(f"  Next values: {next_values}")
    
    return []

async def main():
    print("Creating working parser for broker data...")
    content = await get_sample_data()
    
    if content:
        # Try main parsing method
        parsed_data = parse_mixed_format_data(content)
        
        if parsed_data:
            print(f"\nSuccessfully parsed {len(parsed_data)} records")
            
            # Show first few and last few records
            print("\nFirst 5 records:")
            for i, record in enumerate(parsed_data[:5]):
                date_str = record['trade_date'].strftime('%Y/%m/%d')
                print(f"{i+1:2}: {date_str} - "
                      f"O:{record['open_price']:7.2f} "
                      f"H:{record['high_price']:7.2f} "
                      f"L:{record['low_price']:7.2f} "
                      f"C:{record['close_price']:7.2f} "
                      f"V:{record['volume']:>8}")
            
            print("\nLast 5 records:")
            for record in parsed_data[-5:]:
                date_str = record['trade_date'].strftime('%Y/%m/%d')
                print(f"    {date_str} - "
                      f"O:{record['open_price']:7.2f} "
                      f"H:{record['high_price']:7.2f} "
                      f"L:{record['low_price']:7.2f} "
                      f"C:{record['close_price']:7.2f} "
                      f"V:{record['volume']:>8}")
            
        else:
            print("\nMain parsing failed, trying alternative method...")
            try_alternative_parsing(content)
        
    else:
        print("Failed to get sample data")

if __name__ == "__main__":
    asyncio.run(main())