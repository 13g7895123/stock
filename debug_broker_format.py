"""Debug the actual broker data format"""

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

def debug_format(content):
    """Debug the exact format"""
    
    parts = content.split(',')
    
    print(f"=== DEBUGGING BROKER DATA FORMAT ===")
    print(f"Total parts: {len(parts)}")
    print()
    
    # Look at specific positions where we saw problems
    problem_positions = [2878, 4317, 5756, 7195]  # From previous analysis
    
    print("Examining problematic positions:")
    for pos in problem_positions:
        if pos < len(parts):
            print(f"Position {pos}: '{parts[pos]}'")
    print()
    
    # Look around these positions
    for pos in problem_positions[:2]:  # Check first 2
        if pos < len(parts):
            print(f"Context around position {pos}:")
            start = max(0, pos - 5)
            end = min(len(parts), pos + 6)
            for i in range(start, end):
                marker = " <-- PROBLEM" if i == pos else ""
                print(f"  {i:4}: '{parts[i]}'{marker}")
            print()
    
    # Let's examine the transition from dates to numbers
    print("Examining transition from dates to numbers:")
    
    # Find where dates end
    date_end_pos = -1
    for i, part in enumerate(parts):
        if '/' in part and len(part.split('/')) == 3:
            try:
                # Try to parse as pure date
                date_parts = part.split('/')
                int(date_parts[0])  # year
                int(date_parts[1])  # month 
                int(date_parts[2])  # day
                date_end_pos = i
            except:
                # This is where dates transition to mixed format
                print(f"Date format changes at position {i}: '{part}'")
                break
    
    if date_end_pos >= 0:
        print(f"Pure dates end at position: {date_end_pos}")
        print(f"Total pure dates: {date_end_pos + 1}")
        
        # Show transition area
        print("Transition area:")
        start = max(0, date_end_pos - 2)
        end = min(len(parts), date_end_pos + 10)
        for i in range(start, end):
            print(f"  {i:4}: '{parts[i]}'")
    
    print()
    
    # Try to find actual data pattern
    print("=== LOOKING FOR ACTUAL STOCK DATA PATTERN ===")
    
    # Look at the actual end of the data
    print("Last 20 parts:")
    for i, part in enumerate(parts[-20:], len(parts) - 20):
        print(f"  {i:4}: '{part}'")
    
    print()
    
    # Try a different approach - maybe it's tab-separated within comma-separated?
    print("Checking for tab-separated data within parts:")
    tab_parts = []
    for i, part in enumerate(parts[:100]):  # Check first 100
        if '\t' in part:
            print(f"Position {i} contains tabs: '{part}'")
            tab_split = part.split('\t')
            print(f"  Tab-split: {tab_split}")
            tab_parts.append((i, tab_split))
    
    if not tab_parts:
        print("No tab-separated data found in first 100 parts")
    
    print("\n=== DEBUG COMPLETE ===")

async def main():
    print("Getting data for detailed debugging...")
    content = await get_sample_data()
    
    if content:
        debug_format(content)
    else:
        print("Failed to get sample data")

if __name__ == "__main__":
    asyncio.run(main())