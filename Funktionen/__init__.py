"""
Funktionen-Paket, aufgeteilt in zwei Bereiche:

- Funktionen.pseudonym   -> Pseudonym-Rotation (Lifecycle, Zuweisungslogik,
                             Preprocessing, UserSimulation)
- Funktionen.auswertung  -> Auswertung/Sweep (Vokabular, Baseline-Matrix,
                             Konfigurations-Evaluierung, Scoring, run_sweep)

Die wichtigsten Symbole werden hier zusätzlich re-exportiert, damit
z.B. `from Funktionen import run_sweep, PipelineConfig` weiterhin
funktioniert.
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