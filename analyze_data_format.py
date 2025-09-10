"""Analyze the actual data format from working broker sites"""

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

def analyze_format(content):
    """Analyze the data format"""
    
    print(f"=== DATA FORMAT ANALYSIS ===")
    print(f"Total content length: {len(content)}")
    print()
    
    # Split into lines
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    print()
    
    # Show first 10 lines
    print("First 10 lines:")
    for i, line in enumerate(lines[:10], 1):
        if line.strip():
            print(f"  {i}: {line[:150]}")
            if i == 1:
                # Analyze first line format
                parts = line.split(',')
                print(f"    -> Split by comma: {len(parts)} parts")
                if len(parts) >= 5:
                    print(f"    -> Sample parts: {parts[:5]}")
    print()
    
    # Look for patterns
    print("=== PATTERN ANALYSIS ===")
    
    # Check if it's all dates first
    first_line = lines[0] if lines else ""
    if first_line:
        parts = first_line.split(',')
        print(f"First line parts (first 10): {parts[:10]}")
        
        # Check if these look like dates
        date_patterns = []
        for part in parts[:20]:  # Check first 20 parts
            if '/' in part and len(part.split('/')) == 3:
                date_patterns.append(part)
        
        if date_patterns:
            print(f"Found {len(date_patterns)} date patterns in first 20 parts: {date_patterns[:5]}")
    
    print()
    
    # Look for actual stock data lines
    print("=== LOOKING FOR STOCK DATA LINES ===")
    for i, line in enumerate(lines[:20], 1):
        if line.strip() and not all(c in '0123456789/,' for c in line.replace('.', '')):
            # This line contains non-date data
            print(f"Non-date line {i}: {line[:150]}")
            parts = line.split(',')
            print(f"  Parts count: {len(parts)}")
            if len(parts) >= 5:
                print(f"  Sample parts: {parts[:8]}")
        elif line.strip() and len(line.split(',')) >= 8:
            # This might be stock price data
            parts = line.split(',')
            try:
                # Try to parse as numeric data
                numeric_parts = []
                for part in parts[:8]:
                    try:
                        if '/' in part:  # Date
                            numeric_parts.append(f"DATE({part})")
                        else:
                            float(part)
                            numeric_parts.append(f"NUM({part})")
                    except:
                        numeric_parts.append(f"TEXT({part})")
                
                if len(numeric_parts) >= 6:
                    print(f"Potential stock data line {i}: {numeric_parts[:8]}")
            except:
                pass
    
    print()
    print("=== SAMPLE ANALYSIS COMPLETE ===")

async def main():
    print("Getting sample data from broker...")
    content = await get_sample_data()
    
    if content:
        analyze_format(content)
    else:
        print("Failed to get sample data")

if __name__ == "__main__":
    asyncio.run(main())