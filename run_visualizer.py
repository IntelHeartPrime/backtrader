#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit Visualizer - Launch backtrader visualization directly

This script bypasses Tushare API requirements and launches
the Streamlit visualization with sample data.
"""

import sys
import os
import subprocess
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))))

print('=' * 60)
print('🚀 Backtrader Streamlit Visualizer')
print('=' * 60)
print()

try:
    webbrowser.open('http://localhost:8501')
    print('✅ Opening browser at http://localhost:8501')
except:
    print('📋 Open http://localhost:8501 in your browser')

print()
print('💡 Press Ctrl+C to stop visualization server')
print()

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
