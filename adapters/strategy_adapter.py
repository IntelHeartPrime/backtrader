import backtrader as bt
from typing import Dict, Any, Type, List
from datetime import datetime


class StrategyAdapter:
    """
    Adapter for strategy parameter introspection and instantiation.
    Allows dynamic UI control over strategy parameters.
    """
    
    @staticmethod
    def get_parameters(strategy_class: Type[bt.Strategy]) -> Dict[str, Dict[str, Any]]:
        """
        Extract strategy parameters with metadata for UI controls.
        
        Returns:
            Dict mapping param_name -> {'default': value, 'type': type, 'doc': str}
        """
        params = {}
        if not hasattr(strategy_class, 'params'):
            return params
            
        param_names = strategy_class.params._getkeys()
        
        for name in param_names:
            if name.startswith('_'):
                continue
            
            param_obj = getattr(strategy_class.params, name)
            params[name] = {
                'default': param_obj,
                'type': type(param_obj),
                'doc': strategy_class.params._get(name)[1] if hasattr(strategy_class.params, '_get') else ''
            }
        
        return params
    
    @staticmethod
    def create_strategy(strategy_class: Type[bt.Strategy], **kwargs) -> Type[bt.Strategy]:
        """
        Create strategy instance with given parameters.
        
        Args:
            strategy_class: Strategy class to instantiate
            **kwargs: Strategy parameters
            
        Returns:
            Strategy class (will be instantiated by Cerebro)
        """
        return strategy_class
    
    @staticmethod
    def get_parameter_input_type(param_type: type) -> str:
        """
        Map Python type to Streamlit input widget type.
        
        Returns:
            Streamlit widget type name
        """
        type_map = {
            int: 'number_input',
            float: 'number_input',
            bool: 'checkbox',
            str: 'text_input',
            datetime: 'date_input'
        }
        return type_map.get(param_type, 'text_input')
