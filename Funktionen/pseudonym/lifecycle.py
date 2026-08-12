"""
Lifecycle der Pseudonym-Rotation.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta
import pandas as pd
from ..config import PipelineConfig
from enum import Enum


class LifecycleState(Enum):
    """Zustände des Lifecycles inerhalb eines Slots"""
    FRESH = 1
    ACTIVE = 2
    WARM = 3
    SATURATED = 4
    RESET = 5


# Generiert automatisch __init__ und ist Datencontainer für Slot-Zustände.
@dataclass
class SlotState:
    # Meint alle Events, damit auch Domains.
    page_visits: int = 0
    # Alle Tracker auf einer Seite.
    tracker_events: int = 0
    # Eindeutige Domains als Set mit field.
    unique_domains: set = field(default_factory=set)
    # Eindeutige Tracker als Set mit field.
    tracker_counter: Counter = field(default_factory=Counter)
    #Zeitstempel speichern, damit das erste und letzte Event (Als pd Timestamp oder none).
    first_event_time: pd.Timestamp | None = None
    last_event_time: pd.Timestamp | None = None

    # Counter für Datenmenge in einem Pseudonym = Segment (Von Rotation zu Rotation).
    segment_index: int = 0
    # Count für Resets eines Slots.
    reset_count: int = 0
    # Status des Slots.
    warm_logged: bool = False
    warm_reached_at: pd.Timestamp | None = None
    # Initialzustand des Slots.
    current_state: LifecycleState = LifecycleState.FRESH
    # kummulierte tracker events.
    cum_tracker_events: int = 0
    # kummulierte domains.
    cum_unique_domains: set = field(default_factory=set)
    # startzeit des Pseudonyms.
    pseudonym_start_time: pd.Timestamp | None = None


def update_lifecycle_on_event(slot: SlotState, cfg: PipelineConfig, timestamp: pd.Timestamp) -> None:
    """Prüft nach einem Event ob eine Zustandänderung notwendig ist."""
    # FRESH -> ACTIVE
    if slot.current_state == LifecycleState.FRESH and len(slot.cum_unique_domains) > 0:
        # Slot auf Acitve setzen wenn Bedinung erfüllt ist und mindestens 1 Event vorhanden ist.
        slot.current_state = LifecycleState.ACTIVE

    # WARM-Threshold berechnen (Threshold wird in der ..config.py --> pipeline_config definiert)
    warm_tracker_threshold = cfg.max_events * cfg.warm_threshold_ratio
    warm_domain_threshold = cfg.max_domains * cfg.warm_threshold_ratio

    # ACTIVE -> WARM
    if slot.current_state == LifecycleState.ACTIVE and not slot.warm_logged:
        # Wenn der Theshold erreicht ist wird:
        if slot.cum_tracker_events >= warm_tracker_threshold or len(slot.cum_unique_domains) >= warm_domain_threshold:
            # der Slot auf WARM gesetzt.
            slot.current_state = LifecycleState.WARM
            # der Slot auf WARM gelogged.
            slot.warm_logged = True
            # der Zeitstempel gesetzt.
            slot.warm_reached_at = timestamp


def threshold_reached(slot: SlotState, cfg: PipelineConfig, current_time: pd.Timestamp) -> bool:
    """Rotations-Schwellenwert-Prüfung für einen Slot."""
    # Setzt die Schwellenwerte für Events und Domains aus der Config. Wenn erreicht dann True
    # Schwellenwert Tracker.
    if slot.cum_tracker_events >= cfg.max_events:
        return True
    # Schwellenwert Domains.
    if len(slot.cum_unique_domains) >= cfg.max_domains:
        return True
    # Schwellenwert Days.
    if slot.pseudonym_start_time is not None and (current_time - slot.pseudonym_start_time) >= timedelta(days=cfg.max_days):
        return True
    # Sonst noch kein Schwellenwert erreicht.
    return False


def close_segment(slot: SlotState) -> None:
    """Session-Grenze für die Auswertung."""
    slot.page_visits = 0
    slot.tracker_events = 0
    slot.unique_domains.clear()
    slot.tracker_counter = Counter()
    slot.first_event_time = None
    slot.last_event_time = None
    slot.segment_index += 1

def reset_pseudonym(slot: SlotState) -> None:
    """Löscht den Pseudonym-Zustand --> Kompletter Reset."""
    slot.cum_tracker_events = 0
    slot.cum_unique_domains = set()
    slot.pseudonym_start_time = None
    slot.warm_logged = False
    slot.warm_reached_at = None
    slot.current_state = LifecycleState.FRESH
