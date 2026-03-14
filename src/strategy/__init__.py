"""
Strategy module for resource optimization.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List

# Export all strategy classes (explicit re-exports to satisfy linters)
from .base_strategy import BaseStrategy as BaseStrategy
from .basic_strategy import BasicStrategy as BasicStrategy
from .time_aware_strategy import TimeAwareStrategy as TimeAwareStrategy
from .trend_aware_strategy import TrendAwareStrategy as TrendAwareStrategy
from .workload_aware_strategy import WorkloadAwareStrategy as WorkloadAwareStrategy
from .adaptive_strategy import AdaptiveStrategy as AdaptiveStrategy
from .quantile_regression_strategy import (
    QuantileRegressionStrategy as QuantileRegressionStrategy,
)
from .moving_average_strategy import MovingAverageStrategy as MovingAverageStrategy
from .pmdarima_strategy import PMDARIMAStrategy as PMDARIMAStrategy
from .prophet_strategy import ProphetStrategy as ProphetStrategy
from .ensemble_strategy import EnsembleStrategy as EnsembleStrategy
from .strategy_factory import StrategyFactory as StrategyFactory

__all__ = [
    "BaseStrategy",
    "BasicStrategy",
    "TimeAwareStrategy",
    "TrendAwareStrategy",
    "WorkloadAwareStrategy",
    "AdaptiveStrategy",
    "QuantileRegressionStrategy",
    "MovingAverageStrategy",
    "PMDARIMAStrategy",
    "ProphetStrategy",
    "EnsembleStrategy",
    "StrategyFactory",
]


class RecommendationStrategy(Enum):
    BASIC = "basic"
    PERCENTILE = "percentile"
    TIME_AWARE = "time_aware"
    TREND_AWARE = "trend_aware"
    WORKLOAD_AWARE = "workload_aware"
    ADAPTIVE = "adaptive"
    QUANTILE_REGRESSION = "quantile_regression"
    MOVING_AVERAGE = "moving_average"
    PMDARIMA = "pmdarima"
    PROPHET = "prophet"
    ENSEMBLE = "ensemble"


@dataclass
class RecommendationConfig:
    strategy: RecommendationStrategy
    cpu_percentile: float = 95.0
    memory_buffer: float = 1.15
    min_cpu_cores: float = 0.01
    min_memory_bytes: float = 100 * 1024 * 1024  # 100Mi
    business_hours_start: int = 9
    business_hours_end: int = 17
    business_days: List[int] = (0, 1, 2, 3, 4)  # Monday = 0
    trend_threshold: float = 0.1
    high_variance_threshold: float = 0.5
    history_window_hours: int = 24  # Default to 24 hours of historical data
