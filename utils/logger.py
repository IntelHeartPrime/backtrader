"""
Centralized logging for data fetching and loading.
Provides timestamped, structured logs for debugging data pipeline issues.
"""

import logging
import sys
from datetime import datetime
from typing import List


class DataPipelineLogger:
    """Ring-buffer logger that captures recent entries for UI display."""

    _instance = None
    _ring: List[str] = []
    _max_entries = 200

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self):
        self.logger = logging.getLogger('backtrader.data')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Console handler — structured, compact
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)-5s %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(console)

    def _record(self, level: str, msg: str):
        getattr(self.logger, level)(msg)
        entry = f'[{datetime.now().strftime("%H:%M:%S")}] {level.upper():5} {msg}'
        self._ring.append(entry)
        if len(self._ring) > self._max_entries:
            self._ring.pop(0)

    def debug(self, msg): self._record('debug', msg)
    def info(self, msg): self._record('info', msg)
    def warning(self, msg): self._record('warning', msg)
    def error(self, msg): self._record('error', msg)

    @property
    def recent(self) -> str:
        return '\n'.join(self._ring[-80:])

    def clear(self):
        self._ring.clear()


# Singleton access
def get_logger() -> DataPipelineLogger:
    return DataPipelineLogger()
