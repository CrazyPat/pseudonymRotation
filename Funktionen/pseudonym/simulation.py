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
    close_segment,
    reset_pseudonym,
    threshold_reached,
    update_lifecycle_on_event,
)
from .zuweisung import SlotAssigner


class UserSimulation:
    def __init__(self, user_id: str, cfg: PipelineConfig, verbose: bool = False) -> None:
        self.user_id = user_id
        self.cfg = cfg
        # Slots aus Lifecycle werden initialisiert mit der Anzahl aus der config
        self.slots: Dict[int, SlotState] = {i: SlotState() for i in range(cfg.num_slots)}
        # Für spätere Auswertung speicherung der Segmente.
        self.segment_records: List[dict] = []
        self.verbose = verbose
        # Seedgenerator für die Slot-Zuweisung. Jeder Nutzer bekommt sein eigenes Secret.
        seed_str = hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()
        self.rng = np.random.default_rng(int(seed_str[:8], 16))
        local_secret = SlotAssigner.gen_local_secret(user_id)
        # Zuweisungslogik aus zuweisung.py
        self.assigner = SlotAssigner(user_id=user_id, cfg=cfg, rng=self.rng, local_secret=local_secret)
        self.global_last_domain: str | None = None


    def _close_slot_segment(self, slot_id: int, reason: str, close_time: pd.Timestamp, trigger_detail: str | None = None) -> None:
        """Datensammlung nach Abschluss eines Segments."""
        slot = self.slots[slot_id]
        # Wird abgebrochen falls ein Segment keine Events hatte.
        if slot.page_visits <= 0:
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
            "page_visits": slot.page_visits,
            "unique_domains": len(slot.unique_domains),
            "trigger": reason,
            "trigger_detail": trigger_detail,
            "domain_counter_json": json.dumps(slot.domain_counter, ensure_ascii=False),
            "final_state": slot.current_state.name
        })
        # Segment wird geschlossen.
        close_segment(slot)

        # Löscht einen kompletten Slot. Dies aber nur wenn ein Schwellenwert erreicht wurde.
        if reason == "rotation_threshold":
            slot.reset_count += 1
            reset_pseudonym(slot)
            self.assigner.release_slot(slot_id)


    def process_event(self, domain: str, timestamp: pd.Timestamp) -> tuple[int, int]:
        """Verarbeitet jede Domain und prüft ob Rotation notwendig ist."""
        # Checkt, in welchen Slot die Domain gehört
        pseudonym = self.assigner._hash_domain(domain)
        # Slot zuweisung basierend auf dem Pseudonym
        slot_id = self.assigner.assign_domain(pseudonym)
        # Holt sich das passende Slot-Objekt
        slot = self.slots[slot_id]
        # Speichert das aktuelle Segment für den Return
        current_segment = slot.segment_index
        if domain == self.global_last_domain:
            slot.last_event_time = timestamp
            return slot_id, current_segment
        self.global_last_domain = domain
        # Zeitstempel setzen beim ersten Event.
        if slot.first_event_time is None:
            slot.first_event_time = timestamp
        # Startzeit für Pseudonym.
        if slot.pseudonym_start_time is None:
            slot.pseudonym_start_time = timestamp
        # Zähler erhöhen für ALLE.
        slot.page_visits += 1
        # Domain wird in Set gespeichert für eindeutige Domains.
        slot.unique_domains.add(domain)
        # Kummulierte Domains auch zählen.
        slot.cum_unique_domains.add(domain)
        # Domain-Counter für Fingerprint erhöhen
        slot.domain_counter[domain] += 1
        # Letzter Zeitstempel wird gesetzt, um Inaktivität zu prüfen.
        slot.last_event_time = timestamp
        # Lifecycle-Logik prüft den Zustand des Slots und ob eine Rotation notwendig ist.
        update_lifecycle_on_event(slot, self.cfg, timestamp)
        # Prüfen ob Schwellenwert erreicht wurde
        reason_detail = threshold_reached(slot, self.cfg, timestamp)
        if reason_detail is not None:
            # reason = "rotation_threshold" und trigger_detail"Events", "Domains" oder "Days"
            self._close_slot_segment(slot_id, reason="rotation_threshold", close_time=timestamp, trigger_detail=reason_detail)
            
        return slot_id, current_segment


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


    def run_user(self, df_user: pd.DataFrame) -> pd.DataFrame:
            results = []
            for row in df_user.itertuples(index=False):
                slot_id, seg_id = self.process_event(row.domain, row.used_at)
                results.append({
                    "panelist_id": self.user_id,
                    "domain": row.domain,
                    "used_at": row.used_at,
                    "slot_id": slot_id,
                    "segment_id": seg_id
                })
            self.finalize()
            return pd.DataFrame(results)
