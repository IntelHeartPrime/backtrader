import plotly.graph_objects as go

def custom_plotly_plot(strategy):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=strategy.data.datetime,
        open=strategy.data.open,
        high=strategy.data.high,
        low=strategy.data.low,
        close=strategy.data.close,
        name="Candlestick"
    ))

    fig.update_layout(title="Interactive Candlestick Chart", xaxis_title="Date", yaxis_title="Price")
    fig.show()

# 调用时使用自定义绘图函数
# custom_plotly_plot(strategy)z