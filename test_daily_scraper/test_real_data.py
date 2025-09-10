"""Test script to validate real data fetching with stock 2330."""

import asyncio
import sys
sys.path.append('src')

from src.daily_data_service import DailyDataService


async def test_real_data_fetch():
    """Test fetching real data from brokers for stock 2330."""
    print("Testing real data fetch for stock 2330...")
    
    service = DailyDataService()
    
    # Test each broker URL
    for i, broker_url in enumerate(service.broker_urls):
        print(f"\nTesting broker {i+1}: {broker_url}")
        try:
            data = await service.fetch_daily_data_from_broker(broker_url, "2330")
            if data:
                print(f"SUCCESS! Got {len(data)} records")
                print(f"Sample record: {data[0] if data else 'None'}")
                return data  # Return first successful result
            else:
                print(f"No data returned")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nAll brokers failed")
    return []


async def main():
    """Main test function."""
    data = await test_real_data_fetch()
    
    if data:
        print(f"\nSUCCESS! Retrieved {len(data)} daily records for stock 2330")
        print("First record details:")
        print(f"  Stock ID: {data[0]['stock_id']}")
        print(f"  Date: {data[0]['trade_date']}")
        print(f"  Open: {data[0]['open_price']}")
        print(f"  Close: {data[0]['close_price']}")
        print(f"  Volume: {data[0]['volume']}")
        print(f"  Adjusted Close: {data[0]['adjusted_close']}")
    else:
        print("\nFailed to retrieve any data")


if __name__ == "__main__":
    asyncio.run(main())