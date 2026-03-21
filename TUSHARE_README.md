# Tushare Data Feed Integration for Backtrader

本项目为Backtrader添加了Tushare数据源支持，可以直接从Tushare API获取中国股票数据并进行回测。

---

## 安装依赖

```bash
pip install tushare backtrader[plotting] python-dotenv
```

`python-dotenv` 是可选的，用于从`.env`文件读取配置。

---

## 配置Tushare API Token

### 方式1：使用.env文件（推荐）

```bash
# 复制模板文件
cp .env.example .env

# 编辑.env文件，填入你的token
# TUSHARE_TOKEN=your_actual_token_here
```

### 方式2：使用环境变量

```bash
export TUSHARE_TOKEN='your_token_here'
```

### 方式3：直接传递token参数

```python
df = get_tushare_data(
    ts_code='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    token='your_token_here'  # 直接传入
)
```

**Token获取方式优先级：**
1. 函数参数中明确传递的`token`
2. 环境变量`TUSHARE_TOKEN`
3. `.env`文件中的`TUSHARE_TOKEN`（需要安装`python-dotenv`）

---

## 快速开始

### 运行示例

```bash
# 方式1：使用.env文件
cp .env.example .env
# 编辑.env文件填入token
python examples/tushare_backtest.py

# 方式2：使用环境变量
export TUSHARE_TOKEN='your_token'
python examples/tushare_backtest.py
```

---

## 使用方法

### 基本用法

```python
import backtrader as bt
from tushare_fetcher import get_tushare_data

# 获取数据（token会自动从env或.env读取）
df = get_tushare_data(
    ts_code='000001.SZ',
    start_date='20230101',
    end_date='20231231'
)

# 创建引擎
cerebro = bt.Cerebro()

# 添加数据
data = bt.feeds.TushareData(dataname=df)
cerebro.adddata(data)

# 运行回测
cerebro.run()
```

### 前复权数据

```python
# 获取前复权数据
df = get_tushare_data(
    ts_code='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    adj='qfq'  # 前复权
)
```

### 批量获取多只股票

```python
from tushare_fetcher import get_tushare_multiple_stocks

# 批量获取
data_dict = get_tushare_multiple_stocks(
    ts_codes=['000001.SZ', '600000.SH'],
    start_date='20230101',
    end_date='20231231'
)

# 为每只股票创建数据源
for code, df in data_dict.items():
    data = bt.feeds.TushareData(dataname=df, name=code)
    cerebro.adddata(data)
```

---

## 文件说明

### tushare_fetcher.py

数据获取模块，提供两个函数：

- `get_tushare_data()` - 获取单只股票数据
- `get_tushare_multiple_stocks()` - 批量获取多只股票数据

**自动获取Token**：
- 从函数参数、环境变量或`.env`文件自动读取token
- 无需在代码中硬编码token

**返回格式**:
```
DataFrame with:
- Index: datetime (pandas Timestamp)
- Columns: open, high, low, close, volume
```

### backtrader/feeds/tushare.py

自定义DataFeed类，继承自`PandasData`，支持Tushare格式的数据。

**使用方式**:
```python
data = bt.feeds.TushareData(dataname=df)
```

### examples/tushare_backtest.py

完整的使用示例，包含：
- SMA交叉策略
- 数据获取
- 回测执行
- 分析结果
- 绘图

### .env.example

配置文件模板，复制为`.env`后填入你的token即可。

---

## 参数说明

### get_tushare_data()

| 参数 | 类型 | 必需 | 说明 |
|------|------|--------|------|
| ts_code | str | 是 | 股票代码代码（如'000001.SZ'） |
| start_date | str | 是 | 开始日期日期（YYYYMMDD） |
| end_date | str | 是 | 结束日期日期（YYYYMMDD） |
| token | str | 否 | Tushare API token（可选，优先级最低） |
| adj | str | 否 | 复权类型类型：None(未复权), 'qfq'(前复权) |

### TushareData

继承自`PandasData`的所有参数，包括：

| 参数 | 默认值 | 说明 |
|------|----------|------|
| nocase | True | 列名名大小写不敏感 |
| datetime | None | 日期列列（None表示使用索引） |
| open | -1 | 开盘价列列（-1表示自动检测） |
| high | -1 | 最高价列列（-1表示自动检测） |
| low | -1 | 最低价列列（-1表示自动检测） |
| close | -1 | 收盘价列列（-1表示自动检测） |
| volume | -1 | 成交量列列（-1表示自动检测） |

---

## 股票代码格式

- **深交所**: `000001.SZ`
- **上交所**: `600000.SH`
- **北交所**: `9xxxxx.BJ`

---

## 注意事项

1. **Token配置**: 推荐使用`.env`文件管理token，避免硬编码在代码中

2. **成交量单位**: Tushare返回的成交量单位是"手"，已自动转换为股数（×100）

3. **数据日期**: 返回的数据已按日期升序排序，并设置为DataFrame索引

4. **API限制**: 单次请求最多返回6000条数据，相当于约23年的历史数据

5. **复权**: 默认返回未复权数据，需要复权时设置`adj='qfq'`

6. **python-dotenv**: 如需使用`.env`文件，需安装`python-dotenv`包（可选）

7. **tushare包**: 使用前需要安装`pip install tushare`

---

## 安全最佳实践

1. **不要提交.env文件到版本控制**
   ```bash
   # .gitignore
   .env
   ```

2. **使用环境变量在CI/CD环境中**
   ```yaml
   # GitLab CI example
   variables:
     TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
   ```

3. **生产环境使用密钥管理服务**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault

---

## 示例输出

```
Fetching data for 000001.SZ from 20230101 to 20231231...
Fetched 243 bars of data
                open   high    low  close    volume
trade_date
2023-01-03  11.25  11.45  11.20  11.42  12345600
2023-01-04  11.38  11.50  11.30  11.48  98765400
2023-01-05  11.50  11.65  11.40  11.60  87654300
...

Starting backtest...
Starting Portfolio Value: 100000.00

2023-02-16 BUY EXECUTED, Price: 11.85, Cost: 11850.00, Comm: 11.85
2023-03-10 SELL EXECUTED, Price: 11.25, Cost: 11250.00, Comm: 11.25

Final Portfolio Value: 99892.40
Total Return: -0.11%
Sharpe Ratio: -1.23
Max Drawdown: 1.15%
Average Return: -0.05%
```

---

## 许可证

本项目遵循Backtrader的GPLv3+许可证。

---

## 参考链接

- [Tushare Pro](https://tushare.pro/)
- [Tushare Daily接口文档](https://tushare.pro/document/2?doc_id=27)
- [Backtrader文档](http://www.backtrader.com/docu/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
