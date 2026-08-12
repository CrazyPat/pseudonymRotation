"""
Auswertung des Sweeps: Vokabular/Baseline, Konfigurations-Evaluierung,
Scoring und der übergeordnete Sweep-Runner.
"""

from .evaluation import evaluate_configuration
from .scoring import add_scores, find_knee_point, add_plateau, minmax
from .sweep import run_sweep
from .vocabulary import build_baseline_matrix, build_tracker_vocabulary

__all__ = [
    "evaluate_configuration",
    "add_scores",
    "minmax",
    "find_knee_point",
    "add_plateau",
    "run_sweep",
    "build_tracker_vocabulary",
    "build_baseline_matrix",
]
