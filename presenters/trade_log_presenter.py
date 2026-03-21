import pandas as pd
from typing import List, Dict, Any


class TradeLogPresenter:
    """
    Format trade records for table display.
    """
    
    @staticmethod
    def format_trade_log(transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Format transaction data for display table.
        
        Args:
            transactions_df: Raw transaction DataFrame
            
        Returns:
            Formatted DataFrame with readable columns
        """
        if transactions_df.empty:
            return pd.DataFrame(columns=['Date', 'Direction', 'Price', 'Amount', 'Value'])
        
        df = transactions_df.copy()
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
        df['direction'] = df['amount'].apply(lambda x: 'Buy' if x > 0 else 'Sell')
        df['price'] = df['price'].round(2)
        df['amount'] = df['amount'].abs().astype(int)
        df['value'] = df['value'].round(2)
        
        display_df = df[['date', 'direction', 'price', 'amount', 'value']]
        display_df.columns = ['Date', 'Direction', 'Price', 'Amount', 'Value']
        
        return display_df
    
    @staticmethod
    def calculate_trade_statistics(transactions_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate additional trade statistics.
        
        Args:
            transactions_df: Transaction DataFrame
            
        Returns:
            Dict with trade statistics
        """
        if transactions_df.empty:
            return {}
        
        df = transactions_df.copy()
        buys = df[df['amount'] > 0]
        sells = df[df['amount'] < 0]
        
        return {
            'buy_count': len(buys),
            'sell_count': len(sells),
            'avg_buy_price': buys['price'].mean() if not buys.empty else None,
            'avg_sell_price': sells['price'].mean() if not sells.empty else None,
            'total_volume': df['amount'].abs().sum()
        }
