# CLAUDE.md

## 项目概述

基于 Backtrader 的回测框架。数据源使用 Tushare，前端弃用 Backtrader 原生图表，采用 Streamlit + Plotly 自建前端显示系统。

## 环境

- **Python 环境**: `conda activate BackTrader`（路径: `/Users/intelheartprime/opt/anaconda3/envs/BackTrader`）
- **Python 版本**: 3.9
- **启动命令**: `streamlit run app/main.py` 或 `python -m streamlit run app/main.py`
- **依赖管理**: `requirements.txt`

## 架构约束：前后端分离

```
Tushare → DataAdapter → Cerebro → ResultsAdapter → Presenters → Frontend (Streamlit)
```

### 后端层（不可修改 backtrader 核心）

- **`backtrader/`** — Backtrader 核心引擎。**不要修改此目录下的任何文件**
- **`adapters/`** — 适配器层，封装回测引擎，对外提供统一接口
  - `cerebro_adapter.py` — Cerebro 引擎适配
  - `data_adapter.py` — 数据源工厂（Sample Data / CSV / Yahoo Finance / Tushare）
  - `results_adapter.py` — 回测结果提取（metrics、equity、drawdown、trade log、OHLCV、signals）
  - `strategy_adapter.py` — 策略自动发现、参数内省、UI 控件配置生成
- **`tushare_fetcher.py`** — Tushare API 数据获取
- **`utils/logger.py`** — 数据管道日志系统（`DataPipelineLogger`），终端 + UI 双输出

### 前端层（Streamlit + Plotly）

- **`app/main.py`** — 应用入口，回测执行协调，`@st.cache_resource` 缓存策略发现
- **`app/components/`** — UI 组件
  - `sidebar.py` — 侧边栏（策略选择、数据源配置、日期范围、批量回测参数）
  - `main_chart.py` — 主图表（净值折线图 + 买卖信号标记）
  - `kpi_cards.py` — 绩效指标卡片
  - `result_area.py` — 权益/回撤/交易日志标签页
  - `batch_results.py` — 批量回测结果展示
- **`presenters/`** — 展示层，数据格式转换
  - `equity_presenter.py` — Plotly 图表构建（权益曲线、回撤曲线）
  - `metrics_presenter.py` — 指标格式化（`format_metrics()` + `format_value()`）
  - `trade_log_presenter.py` — 交易日志格式化 + 交易统计

### 策略系统

- 策略自动发现：`StrategyAutoDiscovery.discover()` 扫描 `examples/`、`samples/`、`contrib/`、`backtrader/strategies/`
- 4 个分类：生产策略、示例策略、贡献策略、内置策略（共 65 个策略类）
- 动态参数 UI：`StrategyAdapter.generate_widget_configs()` 根据策略 params 自动生成 Streamlit 控件
- 自定义策略放在 `examples/` 目录

## 关键约定

1. **前后端通过适配器层解耦** — 前端不直接调用 Backtrader API，所有回测操作通过 `adapters/` 层
2. **不修改 backtrader 核心** — `backtrader/` 目录下所有文件只读
3. **前端不依赖 Backtrader 原生绘图** — 所有图表使用 Plotly 自建
4. **数据流**: Tushare → DataAdapter → Cerebro → ResultsAdapter → Presenters → Frontend

## 日志

- 数据管道日志通过 `utils/logger.py` 的 `DataPipelineLogger` 统一管理
- 获取日志实例：`from utils.logger import get_logger; log = get_logger()`
- 日志级别：`log.debug()` / `log.info()` / `log.warning()` / `log.error()`
- 侧边栏底部 **📋 Data Pipeline Logs** 面板显示最近 80 条日志
- 所有关键步骤和改动记录固化到 `Logs_agents/` 文件夹，使用 `20xx-x-x.md` 命名
