from dataclasses import dataclass
from enum import Enum
from typing import List


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
