#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit Visualizer - Launch enhanced backtrader visualization

Features:
- Single backtest mode
- Batch backtest with parameter grid search
- Equity curve comparison across strategies
- Performance rankings
"""

import sys
import os
import subprocess
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('=' * 70)
print('🚀 Backtrader Enhanced Visualization')
print('=' * 70)
print()
print('Features:')
print('  ✅ Single backtest with detailed metrics')
print('  ✅ Batch backtest with parameter grid search')
print('  ✅ Equity curve comparison across strategies')
print('  ✅ Performance rankings')
print()
print('=' * 70)

try:
    webbrowser.open('http://localhost:8501')
    print('✅ Opening browser at http://localhost:8501')
except:
    print('📋 Open http://localhost:8501 in your browser')

print()
print('💡 Press Ctrl+C to stop visualization server')
print()
print('Starting Streamlit server...')

try:
    subprocess.Popen([
        sys.executable,
        '-m', 'streamlit',
        'run', 'app/main.py'
    ])
    print('🎉 Streamlit server started!')
except KeyboardInterrupt:
    print('\n🛑 Visualization stopped.')
except Exception as e:
    print(f'❌ Error launching visualization: {e}')
    print('💡 You can manually run: streamlit run app/main.py')
