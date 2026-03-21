#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug script to diagnose Tushare API connection issues
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print('=' * 60)
print('🔍 Tushare API Debug Tool')
print('=' * 60)
print()

# Check 1: Tushare package installation
print('1️⃣ Checking Tushare package installation...')
try:
    import tushare as ts
    print(f'✅ Tushare installed - version: {ts.__version__}')
except ImportError as e:
    print(f'❌ Tushare not installed: {e}')
    print('   Run: pip install tushare')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Error checking Tushare: {e}')

# Check 2: Token configuration
print()
print('2️⃣ Checking Tushare token configuration...')
token_sources = []

# Check environment variable
env_token = os.getenv('TUSHARE_TOKEN')
if env_token:
    masked_token = env_token[:8] + '...' if len(env_token) > 8 else env_token
    print(f'✅ TUSHARE_TOKEN env var found: {masked_token}')
    token_sources.append(('Environment Variable', env_token))

# Check .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        env_file_token = os.getenv('TUSHARE_TOKEN')
        if env_file_token:
            masked_token = env_file_token[:8] + '...' if len(env_file_token) > 8 else env_file_token
            print(f'✅ .env file token found: {masked_token}')
            token_sources.append(('.env File', env_file_token))
    else:
        print('⚠️  .env file not found')
except ImportError:
    print('⚠️  python-dotenv not installed (optional)')
except Exception as e:
    print(f'⚠️  Error reading .env: {e}')

# Check .env.example file
env_example_path = os.path.join(os.path.dirname(__file__), '.env.example')
if os.path.exists(env_example_path):
    print(f'ℹ️  .env.example file exists at: {env_example_path}')
else:
    print('⚠️  .env.example file not found')

if not token_sources:
    print()
    print('❌ No Tushare token found in any source!')
    print()
    print('How to set token:')
    print('  1. Set TUSHARE_TOKEN environment variable')
    print('  2. Create .env file: TUSHARE_TOKEN=your_token')
    print('  3. Copy .env.example to .env and fill in your token')
    sys.exit(1)

# Use first available token
token = token_sources[0][1]

# Check 3: Network connectivity
print()
print('3️⃣ Checking network connectivity...')
try:
    import socket
    host = 'api.tushare.pro'
    port = 80
    socket.setdefaulttimeout(3)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    if result == 0:
        print(f'✅ Can connect to {host}:{port}')
    else:
        print(f'❌ Cannot connect to {host}:{port}')
    sock.close()
except Exception as e:
    print(f'❌ Network check failed: {e}')

    # Check 4: Simple API test
print()
print('4️⃣ Testing Tushare API connection...')
try:
    import tushare as ts
    pro = ts.pro_api(token)
    
    # Test with a simple query
    print('   Testing pro.query() with stock basic info...')
    try:
        df = pro.query(
            ts_code='000001.SZ',
            api_name='stock_basic',
            fields='ts_code,name,area,industry',
            limit=1
        )
        if not df.empty:
            print(f'✅ API query successful!')
            print(f'   Stock: {df.iloc[0]["name"]} ({df.iloc[0]["ts_code"]})')
        else:
            print('⚠️  API query returned empty data')
    except Exception as e:
        print(f'❌ API query failed: {e}')
        print('   This might indicate:')
        print('   - Token expired')
        print('   - Network timeout')
        print('   - Rate limiting')
        print('   - API parameter version mismatch')
        print('   - Wrong API parameter name')
        
except Exception as e:
    print(f'❌ API initialization failed: {e}')

# Check 5: Try fetching actual data (same as tushare_backtest.py)
print()
print('5️⃣ Testing data fetch with same parameters as tushare_backtest.py...')
try:
    from tushare_fetcher import get_tushare_data
    
    stock_code = '000001.SZ'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    print(f'   Fetching: {stock_code} from {start_date} to {end_date}...')
    
    df = get_tushare_data(
        ts_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        token=token
    )
    
    if df is not None and not df.empty:
        print(f'✅ Data fetch successful!')
        print(f'   Records: {len(df)}')
        print('   Sample data:')
        print(df.head())
    else:
        print('❌ Data fetch returned empty or None')
        print()
        print('Possible reasons:')
        print('  1. Stock code is delisted or has no data in date range')
        print('  2. Date range might be outside trading days')
        print('  3. API rate limiting')
        print('  4. Network issues')
        
except Exception as e:
    print(f'❌ Data fetch failed: {e}')
    print()
    print('Error type:', type(e).__name__)

# Summary
print()
print('=' * 60)
print('📋 Debug Summary')
print('=' * 60)
print()
print('If all checks passed but data fetch still fails, try:')
print('  1. Use a different stock code (e.g., "600000.SH" for Shanghai)')
print('  2. Try a recent date range (e.g., 2024-01-01 to 2024-12-31)')
print('  3. Use the sample data instead: python run_visualizer.py')
print()
print('💡 Tip: For testing visualization without API issues, use:')
print('      python run_visualizer.py')
