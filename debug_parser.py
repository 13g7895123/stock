"""Debug the new parser logic."""

import sys
sys.path.append('backend/src')

from services.daily_data_service import DailyDataService
from datetime import datetime

# Test data from the broker
test_data = "2019/11/11,2019/11/25,2019/11/27,2020/05/18,2025/06/20 258.2756,1195 258.2756,245.44,254.36,236.51,240.53,227093,267.65,269.00,263.14,264.94,266744,287.47,293.33,282.06,284.77,285669,451.53,451.76,446.54,447.96,446540,25023.00,47252.00,21736.00,45678.00,54340"

def debug_parsing():
    service = DailyDataService()
    
    print("=== DEBUGGING PARSER ===")
    
    parts = test_data.split(',')
    print(f"Total parts: {len(parts)}")
    
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
                print(f"Mixed format: {date_part} -> {price_part}")
            except ValueError:
                pass
        elif '/' in part and len(part.split('/')) == 3:
            # Pure date
            dates.append(part)
            print(f"Pure date: {part}")
        elif ' ' in part:
            # Handle mixed volume-price format like "1195 258.2756"
            space_parts = part.split()
            print(f"Space separated: {space_parts}")
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
    print(f"Dates: {dates}")
    print(f"First 10 numbers: {all_numbers[:10]}")
    
    if len(dates) == 0 or len(all_numbers) == 0:
        print("ERROR: No valid dates or numbers found")
        return
    
    # Step 2: Try to match dates with data
    data_per_date = len(all_numbers) // len(dates)
    print(f"Data points per date: {data_per_date}")
    
    if data_per_date < 4:
        print("ERROR: Not enough data points per date")
        return
    
    # Step 3: Try to parse first date
    date_str = dates[0]
    try:
        trade_date = datetime.strptime(date_str, '%Y/%m/%d')
        print(f"Parsed date: {trade_date}")
        
        # Get first 5 data points
        data_points = all_numbers[0:5]
        print(f"Data points for first date: {data_points}")
        
        open_price = data_points[0]
        high_price = data_points[1] 
        low_price = data_points[2]
        close_price = data_points[3]
        volume = int(data_points[4]) if data_points[4] > 1000 else int(data_points[4] * 1000)
        
        data_item = {
            "stock_id": "2330",
            "trade_date": trade_date,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "volume": volume,
            "adjusted_close": close_price
        }
        
        print(f"Data item created: {data_item}")
        
        # Test validation
        is_valid = service.validate_daily_data(data_item)
        print(f"Validation result: {is_valid}")
        
        # Check validation conditions manually
        print("\nValidation checks:")
        print(f"All prices > 0: {all(p > 0 for p in [open_price, high_price, low_price, close_price])}")
        print(f"Volume >= 0: {volume >= 0}")
        print(f"Low <= Open <= High: {low_price <= open_price <= high_price}")
        print(f"Low <= Close <= High: {low_price <= close_price <= high_price}")
        print(f"High >= Low: {high_price >= low_price}")
        
    except Exception as e:
        print(f"ERROR parsing first date: {e}")

if __name__ == "__main__":
    debug_parsing()