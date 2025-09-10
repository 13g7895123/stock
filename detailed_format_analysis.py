"""Detailed analysis of broker data format"""

import asyncio
import httpx

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

def detailed_analysis(content):
    """Detailed analysis of the content structure"""
    
    parts = content.split(',')
    total_parts = len(parts)
    
    print(f"=== DETAILED FORMAT ANALYSIS ===")
    print(f"Total parts: {total_parts}")
    print()
    
    # Group parts by type
    dates = []
    numbers = []
    other = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        
        if '/' in part and len(part.split('/')) == 3:
            # Looks like a date
            dates.append((i, part))
        else:
            try:
                float(part)
                numbers.append((i, part))
            except:
                other.append((i, part))
    
    print(f"Dates found: {len(dates)}")
    print(f"Numbers found: {len(numbers)}")
    print(f"Other: {len(other)}")
    print()
    
    # Show sample dates
    print("Sample dates (first 10):")
    for i, (pos, date) in enumerate(dates[:10]):
        print(f"  Position {pos}: {date}")
    print()
    
    # Show sample numbers
    print("Sample numbers (first 20):")
    for i, (pos, num) in enumerate(numbers[:20]):
        print(f"  Position {pos}: {num}")
    print()
    
    # Show other data
    if other:
        print("Other data (first 10):")
        for i, (pos, data) in enumerate(other[:10]):
            print(f"  Position {pos}: '{data}'")
        print()
    
    # Try to identify pattern
    print("=== PATTERN IDENTIFICATION ===")
    
    # Check if dates are consecutive
    if len(dates) >= 2:
        first_date = dates[0][1]
        second_date = dates[1][1]
        print(f"First date: {first_date}")
        print(f"Second date: {second_date}")
        
        try:
            from datetime import datetime
            d1 = datetime.strptime(first_date, '%Y/%m/%d')
            d2 = datetime.strptime(second_date, '%Y/%m/%d')
            diff = (d2 - d1).days
            print(f"Days difference: {diff}")
        except:
            pass
    
    # Check structure around first few dates
    print("\nStructure analysis (first 50 parts):")
    for i in range(min(50, len(parts))):
        part = parts[i].strip()
        if '/' in part and len(part.split('/')) == 3:
            print(f"  {i:2}: DATE  {part}")
        else:
            try:
                float(part)
                print(f"  {i:2}: NUM   {part}")
            except:
                print(f"  {i:2}: TEXT  '{part}'")
    
    print()
    
    # Check for repeating patterns
    print("=== PATTERN REPETITION ANALYSIS ===")
    
    # Look for patterns in positions
    date_positions = [pos for pos, _ in dates[:20]]  # First 20 dates
    if len(date_positions) >= 2:
        print(f"Date positions: {date_positions}")
        
        # Check for regular intervals
        if len(date_positions) >= 3:
            intervals = [date_positions[i+1] - date_positions[i] for i in range(len(date_positions)-1)]
            print(f"Intervals between dates: {intervals[:10]}")
            
            # Check if intervals are consistent
            if len(set(intervals[:5])) == 1 and len(intervals) >= 5:
                interval = intervals[0]
                print(f"Regular interval detected: {interval} parts between dates")
                
                # This might mean each date is followed by N data points
                print(f"This suggests each date has {interval-1} data values")
                
                # Show what's between the first two dates
                if len(date_positions) >= 2:
                    start = date_positions[0] + 1
                    end = date_positions[1]
                    between_data = parts[start:end]
                    print(f"Data between first two dates: {between_data}")
    
    print("\n=== ANALYSIS COMPLETE ===")

async def main():
    print("Getting sample data for detailed analysis...")
    content = await get_sample_data()
    
    if content:
        detailed_analysis(content)
    else:
        print("Failed to get sample data")

if __name__ == "__main__":
    asyncio.run(main())