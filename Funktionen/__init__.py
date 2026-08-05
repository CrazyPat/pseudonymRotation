"""
 Alle Funktionen, die für die Simulation und Auswertung benötigt werden.
"""

from .config import PipelineConfig
from .utils import log_status

from .pseudonym import (
    LifecycleState,
    SlotState,
    SlotAssigner,
    UserSimulation,
    simulate_user_chunk,
)

from .auswertung import (
    build_domain_vocabulary,
    build_baseline_matrix,
    evaluate_configuration,
    minmax,
    find_knee_point,
    add_plateau,
    add_scores,
    run_sweep,
)

__all__ = [
    "PipelineConfig",
    "log_status",
    "LifecycleState",
    "SlotState",
    "SlotAssigner",
    "UserSimulation",
    "simulate_user_chunk",
    "build_domain_vocabulary",
    "build_baseline_matrix",
    "evaluate_configuration",
    "minmax",
    "find_knee_point",
    "add_plateau",
    "add_scores",
    "run_sweep",
]