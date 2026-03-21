"""
Dark theme configuration for Plotly charts.
Professional quantitative trading color scheme.
"""

COLORS = {
    'primary': '#00E676',
    'danger': '#FF4B4B',
    'warning': '#FFA500',
    'info': '#00BFFF',
    'success': '#4CAF50',
    'background': '#1E1E1E',
    'card': '#2D2D2D',
    'text': '#E0E0E0',
    'text_secondary': '#A0A0A0'
}

LAYOUT_CONFIG = {
    'template': 'plotly_dark',
    'font': {
        'family': 'Arial, sans-serif',
        'size': 12,
        'color': COLORS['text']
    },
    'margin': {
        'l': 10,
        'r': 10,
        't': 10,
        'b': 10
    },
    'hovermode': 'x unified',
    'legend': {
        'orientation': 'h',
        'yanchor': 'bottom',
        'y': 1.02,
        'xanchor': 'right',
        'x': 1
    }
}
