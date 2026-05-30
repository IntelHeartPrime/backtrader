import streamlit as st

from presenters.equity_presenter import EquityPresenter
from presenters.trade_log_presenter import TradeLogPresenter


def render_result_area(equity_df, drawdown_df, trade_log_df):
    """
    Render the result area with equity curve, drawdown, and trade log.
    """
    tab1, tab2, tab3 = st.tabs(['Equity Curve', 'Drawdown', 'Trade Log'])

    with tab1:
        if equity_df is None or equity_df.empty:
            st.info('No equity data available.')
        else:
            fig = EquityPresenter.create_equity_curve_figure(equity_df)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if drawdown_df is None or drawdown_df.empty:
            st.info('No drawdown data available.')
        else:
            fig = EquityPresenter.create_drawdown_figure(drawdown_df)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        if trade_log_df is None or trade_log_df.empty:
            st.info('No trade records available.')
        else:
            stats = TradeLogPresenter.calculate_trade_statistics(trade_log_df)
            if stats:
                cols = st.columns(5)
                with cols[0]:
                    st.metric('Buy Count', stats.get('buy_count', 0))
                with cols[1]:
                    st.metric('Sell Count', stats.get('sell_count', 0))
                avg_buy = stats.get('avg_buy_price')
                with cols[2]:
                    st.metric('Avg Buy Price', f'{avg_buy:.2f}' if avg_buy else 'N/A')
                avg_sell = stats.get('avg_sell_price')
                with cols[3]:
                    st.metric('Avg Sell Price', f'{avg_sell:.2f}' if avg_sell else 'N/A')
                with cols[4]:
                    st.metric('Total Volume', int(stats.get('total_volume', 0)))

            formatted_df = TradeLogPresenter.format_trade_log(trade_log_df)
            st.dataframe(
                formatted_df,
                use_container_width=True,
                height=400,
            )
