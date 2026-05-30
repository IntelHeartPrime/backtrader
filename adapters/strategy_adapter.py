import backtrader as bt
import importlib.util
import inspect
import re
import sys
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Type, List, Optional, Tuple
from datetime import datetime


@dataclass
class StrategyCatalogEntry:
    """Metadata for a discovered strategy."""
    key: str                          # "生产策略:SmaCrossStrategy"
    cls: Type                         # actual strategy class
    class_name: str                   # "SmaCrossStrategy"
    category: str                     # "生产策略"
    category_key: str                 # "examples"
    file_path: str                    # absolute path to .py file
    docstring: str                    # cleaned class docstring
    params_meta: Dict[str, Any] = field(default_factory=dict)
    complexity: str = "simple"        # "simple" | "moderate" | "complex"
    warnings: List[str] = field(default_factory=list)
    needs_multi_data: bool = False
    needs_specific_broker: Optional[str] = None
    external_dependencies: List[str] = field(default_factory=list)


class StrategyAutoDiscovery:
    """Scan configured directories for backtrader Strategy classes."""

    SCAN_DIRS = [
        ('examples', '生产策略'),
        ('samples', '示例策略'),
        ('contrib/samples', '贡献策略'),
        ('backtrader/strategies', '内置策略'),
    ]

    ABSTRACT_NAME_PATTERNS = ('Base', 'Abstract', 'Meta')

    _STRATEGY_BASES = None

    @staticmethod
    def _get_strategy_bases():
        if StrategyAutoDiscovery._STRATEGY_BASES is None:
            StrategyAutoDiscovery._STRATEGY_BASES = {
                bt.Strategy, bt.SignalStrategy, bt.Strategy.__base__
            }
        return StrategyAutoDiscovery._STRATEGY_BASES

    @staticmethod
    def discover(project_root: str) -> Dict[str, StrategyCatalogEntry]:
        """Main entry point: scan directories, return catalog keyed by 'category:class_name'."""
        catalog: Dict[str, StrategyCatalogEntry] = {}

        for rel_dir, category_display in StrategyAutoDiscovery.SCAN_DIRS:
            scan_path = os.path.join(project_root, rel_dir)
            if not os.path.isdir(scan_path):
                continue
            entries = StrategyAutoDiscovery._scan_directory(
                scan_path, rel_dir, category_display
            )
            for entry in entries:
                catalog[entry.key] = entry

        return catalog

    @staticmethod
    def _scan_directory(
        directory_path: str, category_key: str, category_display: str
    ) -> List[StrategyCatalogEntry]:
        """Recursively scan a directory for .py files containing strategy classes."""
        entries: List[StrategyCatalogEntry] = []

        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for filename in files:
                if not filename.endswith('.py') or filename.startswith('__init__'):
                    continue
                filepath = os.path.join(root, filename)
                rel = os.path.relpath(filepath, directory_path)
                module_name = f"_disc_{category_key}_{rel.replace(os.sep, '_')[:-3]}"

                module = StrategyAutoDiscovery._load_module(filepath, module_name)
                if module is None:
                    continue

                source_code = None
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                        source_code = fh.read()
                except Exception:
                    pass

                classes = StrategyAutoDiscovery._find_strategy_classes(module, filepath)
                for cls in classes:
                    source_analysis = (
                        StrategyAutoDiscovery._analyze_source(source_code)
                        if source_code else {}
                    )
                    # Check for class-level multi-data marker
                    if getattr(cls, '_needs_multi_data', False):
                        source_analysis['needs_multi_data'] = True
                    complexity, warnings_list = StrategyAutoDiscovery._estimate_complexity(
                        cls, source_analysis
                    )

                    docstring = inspect.getdoc(cls) or ""
                    params_meta = StrategyAdapter.get_parameters(cls)

                    # Build unique key: handle duplicate class names with sub-path
                    dir_part = os.path.dirname(rel).replace(os.sep, '/')
                    if dir_part and dir_part != '.':
                        key = f"{category_display}:{dir_part}/{cls.__name__}"
                    else:
                        key = f"{category_display}:{cls.__name__}"

                    entries.append(StrategyCatalogEntry(
                        key=key,
                        cls=cls,
                        class_name=cls.__name__,
                        category=category_display,
                        category_key=category_key,
                        file_path=filepath,
                        docstring=docstring,
                        params_meta=params_meta,
                        complexity=complexity,
                        warnings=warnings_list,
                        needs_multi_data=source_analysis.get('needs_multi_data', False),
                        needs_specific_broker=source_analysis.get('broker'),
                        external_dependencies=source_analysis.get('external_deps', []),
                    ))

        return entries

    @staticmethod
    def _load_module(filepath: str, module_name: str):
        """Dynamically import a .py file, return module or None on failure."""
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None

    @staticmethod
    def _find_strategy_classes(module, filepath: str) -> List[Type]:
        """Find concrete strategy classes in a loaded module."""
        bases = StrategyAutoDiscovery._get_strategy_bases()
        results = []

        for attr_name in dir(module):
            obj = getattr(module, attr_name, None)
            if obj is None or not isinstance(obj, type):
                continue
            if obj in bases:
                continue
            if any(p in attr_name for p in StrategyAutoDiscovery.ABSTRACT_NAME_PATTERNS):
                continue
            if getattr(obj, '__module__', '') != module.__name__:
                continue
            if not issubclass(obj, bt.Strategy):
                continue
            if not hasattr(obj, 'params'):
                continue

            results.append(obj)

        return results

    @staticmethod
    def _analyze_source(source_code: str) -> Dict[str, Any]:
        """Lightweight regex analysis of strategy source for complexity markers."""
        analysis: Dict[str, Any] = {
            'needs_multi_data': False,
            'broker': None,
            'external_deps': [],
            'needs_cheat': False,
        }

        if re.search(r'self\.data[12]|\b_mindatas\b', source_code):
            analysis['needs_multi_data'] = True

        if re.search(r'bt\.stores\.(IBStore|InteractiveBrokers)', source_code):
            analysis['broker'] = 'Interactive Brokers'
        elif re.search(r'bt\.stores\.OandaStore', source_code):
            analysis['broker'] = 'Oanda'

        if re.search(r'self\.cerebro\.p\.cheat_on_open', source_code):
            analysis['needs_cheat'] = True

        for lib in ('scipy', 'talib', 'statsmodels', 'pyfolio'):
            if re.search(rf'\bimport\s+{lib}\b|from\s+{lib}\b', source_code):
                analysis['external_deps'].append(lib)

        return analysis

    @staticmethod
    def _estimate_complexity(cls: Type, analysis: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Assign complexity level and human-readable warnings."""
        warnings: List[str] = []
        score = 0

        if analysis.get('needs_multi_data'):
            score += 2
            warnings.append('此策略需要多个数据源 (data0, data1)')

        if analysis.get('broker'):
            score += 2
            warnings.append(f'此策略依赖 {analysis["broker"]} broker，需要对应的 API')

        if analysis.get('needs_cheat'):
            score += 1
            warnings.append('此策略使用 cheat-on-open 模式，需要特殊配置')

        if analysis.get('external_deps'):
            deps = ', '.join(analysis['external_deps'])
            score += 1
            warnings.append(f'此策略需要额外依赖: {deps}')

        if score == 0:
            return ('simple', [])
        elif score <= 2:
            return ('moderate', warnings)
        else:
            return ('complex', warnings)


class StrategyAdapter:
    """Adapter for strategy parameter introspection, discovery, and UI generation."""

    @staticmethod
    def get_parameters(strategy_class: Type[bt.Strategy]) -> Dict[str, Dict[str, Any]]:
        """
        Extract strategy parameters with metadata for UI controls.

        Returns:
            Dict mapping param_name -> {'default': value, 'type': type, 'doc': str, 'widget_type': str}
        """
        params = {}
        if not hasattr(strategy_class, 'params'):
            return params

        param_names = strategy_class.params._getkeys()

        for name in param_names:
            if name.startswith('_'):
                continue

            param_obj = getattr(strategy_class.params, name)
            ptype = type(param_obj)
            widget_type = StrategyAdapter.get_parameter_input_type(ptype)

            doc = ''
            if hasattr(strategy_class.params, '_get'):
                try:
                    doc = strategy_class.params._get(name)[1] or ''
                except Exception:
                    pass

            params[name] = {
                'default': param_obj,
                'type': ptype,
                'doc': doc,
                'widget_type': widget_type,
            }

        return params

    @staticmethod
    def get_parameter_input_type(param_type: type) -> str:
        """Map Python type to Streamlit input widget type."""
        if param_type is type(None):
            return 'optional_number'
        if param_type in (list, tuple):
            return 'selectbox'
        type_map = {
            int: 'number_input',
            float: 'number_input',
            bool: 'checkbox',
            str: 'text_input',
            datetime: 'date_input',
        }
        return type_map.get(param_type, 'text_input')

    @staticmethod
    def generate_widget_configs(params_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate ordered list of Streamlit widget configurations from params_meta.

        Returns:
            List of {key, label, widget_type, default, doc, widget_kwargs} dicts
        """
        configs = []
        for param_name, meta in params_meta.items():
            label = param_name.replace('_', ' ').title()
            default = meta.get('default')
            widget_type = meta.get('widget_type', 'text_input')
            ptype = meta.get('type', str)
            doc = meta.get('doc', '')

            cfg = {
                'key': param_name,
                'label': label,
                'widget_type': widget_type,
                'default': default,
                'doc': doc,
                'widget_kwargs': {},
            }

            if widget_type == 'number_input':
                if isinstance(default, bool):
                    # bool is subclass of int — treat as checkbox
                    cfg['widget_type'] = 'checkbox'
                    cfg['widget_kwargs'] = {}
                elif isinstance(default, int):
                    cfg['widget_kwargs'] = {
                        'step': 1,
                        'min_value': min(default * 2, 0),
                        'max_value': max(default * 5, 500),
                    }
                elif isinstance(default, float):
                    cfg['widget_kwargs'] = {
                        'step': max(0.01, abs(default) * 0.1) if default != 0 else 0.01,
                        'format': '%.4f',
                    }
            elif widget_type == 'optional_number':
                cfg['widget_type'] = 'number_input'
                cfg['widget_kwargs'] = {'step': 1, 'value': None}
                cfg['optional'] = True
                if default is None:
                    cfg['default'] = None
            elif widget_type == 'selectbox':
                if isinstance(default, (list, tuple)):
                    cfg['widget_kwargs'] = {'options': list(default)}
                    cfg['default'] = default[0] if default else None

            configs.append(cfg)

        return configs
