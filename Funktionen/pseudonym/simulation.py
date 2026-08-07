"""
Simulation eines einzelnen Nutzers über alle Slots
"""

import hashlib
import json
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ..config import PipelineConfig
from ..utils import log_status
from .lifecycle import (
    LifecycleState,
    SlotState,
    clear_slot_for_new_segment,
    threshold_reached,
    update_lifecycle_on_event,
)
from .zuweisung import SlotAssigner


class UserSimulation:
    def __init__(self, user_id: str, cfg: PipelineConfig, tracker_mapping: Dict[str, List[str]], verbose: bool = False) -> None:
        self.user_id = user_id
        self.cfg = cfg
        # Slots aus Lifecycle werden initialisiert mit der Anzahl aus der config
        self.slots: Dict[int, SlotState] = {i: SlotState() for i in range(cfg.num_slots)}
        # Für spätere Auswertung speicherung der Segmente.
        self.segment_records: List[dict] = []
        self.tracker_mapping = tracker_mapping
        self.verbose = verbose
        self.processed_events = 0
        # Seedgenerator für die Slot-Zuweisung. Jeder Nutzer bekommt sein eigenes Secret.
        seed_str = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()
        self.rng = np.random.default_rng(int(seed_str[:8], 16))
        self.user_secret = seed_str[8:24]
        # Zuweisungslogik aus zuweisung.py
        self.assigner = SlotAssigner(user_id=user_id, cfg=cfg, rng=self.rng)


    def _close_slot_segment(self, slot_id: int, reason: str, close_time: pd.Timestamp) -> None:
        """Datensammlung nach Abschluss eines Segments."""
        slot = self.slots[slot_id]
        # Wird abgebrochen falls ein Segment keine Events hatte.
        if slot.events_count <= 0:
            return
        # Setzt das Pseudonym auf SATURATED.
        if reason == "rotation_threshold":
            slot.current_state = LifecycleState.SATURATED
        
        # Speichert den Datensatz ab für spätere Auswertungen.
        self.segment_records.append({
            "user_id": self.user_id,
            "slot_id": slot_id,
            "segment_id": slot.segment_index,
            "start_time": slot.first_event_time,
            "end_time": close_time,
            "events_count": slot.events_count,
            "third_party_events": slot.third_party_events_count,
            "unique_domains": len(slot.unique_domains),
            "trigger": reason,
            "domain_counter_json": json.dumps(slot.domain_counter, ensure_ascii=False),
            "final_state": slot.current_state.name
        })
        # Leert alle Zähler + Slot --> FRESH, weil neues Segment beginnt. Slots bleiben dabei gleich!
        clear_slot_for_new_segment(slot)

        # Löscht einen kompletten Slot. Dies aber nur wenn ein Schwellenwert erreicht wurde.
        if reason == "rotation_threshold":
            self.assigner.release_slot(slot_id)


    def process_event(self, domain: str, timestamp: pd.Timestamp) -> None:
        """Verarbeitet jede Domain und prüft ob Rotation notwendig ist."""
        # Speichert die Menge an verarbeiteten Events
        self.processed_events += 1
        # Prüft ob der Slot bereits existiert, wenn nicht wird ein neuer Slot zugewiesen aus zuweisung.py.
        slot_id = self.assigner.assign_domain(domain)
        # Slot wird geladen aus Dict (SlotState).
        slot = self.slots[slot_id]
        # Sitzungslogik, welche prüft ob ein Segment wegen Inaktivität geschlossen werden muss.
        if slot.last_event_time is not None:
            # Inaktivität in Minuten
            idle_minutes = (timestamp - slot.last_event_time).total_seconds() / 60.0
            # Wenn Inaktivität größer ist als in config dann wird das Segment geschlossen.
            if idle_minutes > self.cfg.session_timeout_minutes:
                self._close_slot_segment(slot_id, "session_gap", slot.last_event_time)
        # Zeitstempel setzen beim ersten Event.
        if slot.first_event_time is None:
            slot.first_event_time = timestamp
        # Zähler erhöhen für Events.
        slot.events_count += 1
        # Domain wird in Set gespeichert für eindeutige Domains.
        slot.unique_domains.add(domain)
        # Nimmt Tracker aus dem Mapping. Falls leer dann auch leere Liste.
        associated_trackers = self.tracker_mapping.get(domain, [])
        # Zählt TPT-Events und speichert sie in einem Set für Duplikatsvermeidung.
        for tp_domain in associated_trackers:
            slot.third_party_events_count += 1
            slot.domain_counter[tp_domain] += 1
        # Letzter Zeitstempel wird gesetzt, um Inaktivität zu prüfen.
        slot.last_event_time = timestamp
        # Lifecycle-Logik prüft den Zustand des Slots und ob eine Rotation notwendig ist.
        update_lifecycle_on_event(slot, self.cfg, timestamp)
        # Beim erreichen eines Schwellenwertes wird das Segment geschlossen und der Slot restlos gelöscht.
        if threshold_reached(slot, self.cfg, timestamp):
            self._close_slot_segment(slot_id, "rotation_threshold", timestamp)


    def finalize(self) -> None:
        """Schließt alle Slots ab, die noch offen sind (z. B. ein Segment leer war)."""
        for slot_id, slot in self.slots.items():
            # Setzt Endzeitstempel oder nimmt letzten Zeitstempel.
            end_ts = slot.last_event_time or pd.Timestamp.now()
            # Schließt Segment ab und speichert mit end of stream.
            self._close_slot_segment(slot_id, "end_of_stream", end_ts)

    def total_resets(self) -> int:
        """Summiert alle Resets über alle Slots."""
        return sum(slot.reset_count for slot in self.slots.values())


def simulate_user_chunk(args: Tuple[str, int, int, pd.DataFrame, PipelineConfig, Dict[str, List[str]], bool]) -> Tuple[str, List[dict], int]:
    """Simuliert einen einzelnen Nutzer und gibt die Segmentdaten zurück. Für parallele Verarbeitung in chunks notwendig."""
    # Entpackt die Argumente für die parallele Verarbeitung.
    user_id, user_index, total_users, df_user, cfg, tracker_mapping, verbose = args
    # Initialisiert die UserSimulation mit den gegebenen Parametern.
    sim = UserSimulation(user_id=user_id, cfg=cfg, tracker_mapping=tracker_mapping, verbose=verbose)
    # Dataframe wird für jedes Event verarbeitet.
    for row in df_user.itertuples(index=False):
        sim.process_event(row.domain, row.used_at)
    # Letzten offenen Segmente schließen.
    sim.finalize()
    # Fehlerfinden oder Fortschrittanzeige.
    if verbose:
        # Wie viele Nutzer verarbeitet wurden in %.
        progress_pct = (user_index / total_users) * 100
        #Ausgabe
        log_status(
            f"Fortschritt: {progress_pct:.1f}% | User {user_index}/{total_users} fertig ({user_id}) | "
            f"Segmente={len(sim.segment_records)} | Resets={sim.total_resets()}",
            True,
        )
    return user_id, sim.segment_records, sim.total_resets()
