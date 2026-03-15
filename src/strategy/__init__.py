"""
Strategy module for resource optimization.
"""

from .adaptive_strategy import AdaptiveStrategy as AdaptiveStrategy
from .base_strategy import BaseStrategy as BaseStrategy
from .basic_strategy import BasicStrategy as BasicStrategy
from .ensemble_strategy import EnsembleStrategy as EnsembleStrategy
from .moving_average_strategy import MovingAverageStrategy as MovingAverageStrategy
from .pmdarima_strategy import PMDARIMAStrategy as PMDARIMAStrategy
from .prophet_strategy import ProphetStrategy as ProphetStrategy
from .quantile_regression_strategy import (
    QuantileRegressionStrategy as QuantileRegressionStrategy,
)
from .strategy_factory import StrategyFactory as StrategyFactory
from .time_aware_strategy import TimeAwareStrategy as TimeAwareStrategy
from .trend_aware_strategy import TrendAwareStrategy as TrendAwareStrategy
from .types import RecommendationConfig as RecommendationConfig
from .types import RecommendationStrategy as RecommendationStrategy
from .workload_aware_strategy import WorkloadAwareStrategy as WorkloadAwareStrategy

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
    "RecommendationConfig",
    "RecommendationStrategy",
]
