# Backtrader Streamlit Visualization Layer

A non-intrusive visualization layer for backtrader using Streamlit and Plotly.

## Architecture

```
├── app/                      # Streamlit application
│   ├── main.py             # Main entry point
│   └── components/          # UI components
│       ├── sidebar.py      # Control panel
│       ├── main_chart.py   # Price chart
│       ├── result_area.py  # Results display
│       └── kpi_cards.py    # KPI cards
├── visualization/             # Plotly charts
│   ├── charts.py         # Chart builders
│   └── theme.py          # Dark theme config
├── adapters/                 # Backtrader integration
│   ├── cerebro_adapter.py    # Engine wrapper
│   ├── strategy_adapter.py   # Parameter introspection
│   ├── data_adapter.py       # Data source factory
│   └── results_adapter.py    # Result extraction
└── presenters/              # Data formatting
    ├── metrics_presenter.py    # KPI formatting
    ├── equity_presenter.py     # Equity curve builder
    └── trade_log_presenter.py  # Trade log formatting
```

## Design Principles

1. **Non-intrusive**: No changes to `backtrader/` core directory
2. **Read-only**: Visualization layer only reads backtrader results
3. **Adapter pattern**: Clean separation between framework and UI
4. **Presenters**: Format analyzer outputs for display

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app/main.py
```

## Features

- **Parameter panel**: Strategy configuration, data source selection
- **Interactive charts**: Plotly candlestick with buy/sell markers
- **KPI cards**: Sharpe, returns, drawdown, win rate
- **Equity curve**: Cumulative returns over time
- **Drawdown chart**: Visual risk analysis
- **Trade log**: Detailed transaction records

## Consistency Verification

To verify the visualization layer doesn't change backtest semantics:

```bash
python examples/tushare_backtest.py
streamlit run app/main.py
```

Compare Sharpe, total return, max drawdown between both runs.

## Extension Points

1. Add new strategies to `examples/` directory
2. Extend `DataAdapter` for custom data sources
3. Add new analyzers in `ResultsAdapter`
4. Create additional chart types in `visualization/charts.py`
