"""
Konfiguration der Simulationsparameter.
"""

from dataclasses import dataclass


@dataclass
class PipelineConfig:
    num_slots: int = 10
    max_domains: int = 15
    max_events: int = 100
    max_days: int = 7
    warm_threshold_ratio: float = 0.8
    use_tracker_mapping: bool = True