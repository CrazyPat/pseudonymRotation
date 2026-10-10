"""
Zuweisungs-Logik der Pseudonym-Rotation.
"""

import hashlib
import hmac
from typing import Dict, Set

import numpy as np
from ..config import PipelineConfig


# Service-Object
class SlotAssigner:
    """Verwaltet die Zuordnung (Domain -> Slot) und (Slot -> Domains)."""


    def __init__(self, user_id: str, cfg: PipelineConfig, rng: np.random.Generator, local_secret: bytes,):
        # User_id
        self.user_id = user_id
        # Objekt der Konfiguration
        self.cfg = cfg
        # Zufallsgenerator des Nutzers
        self.rng = rng
        # Local Secret für HMAC SHA256
        self.local_secret = local_secret
        # Leeres Mapping von Domain --> Slot
        self.domain_to_slot_map: Dict[str, int] = {}
        # Leeres Mapping von Slot --> Domains = Baut die Zuordnung auf (z. B. 0: set())
        self.slot_to_domains: Dict[int, Set[str]] = {i: set() for i in range(cfg.num_slots)}


    @staticmethod
    def gen_local_secret(user_id: str) -> bytes:
        """Erzeugt ein lokales Secret für HMAC basierend auf der User-ID."""
        # Hier aus der User-ID abgeleitet, damit auch die Zuordnungstabelle reproduzierbar ist. Auf die Slotwahl hat das Secret keinen Einfluss, die kommt aus dem Zufallsgenerator. In einer Extension wäre das Secret zufällig und nur lokal bekannt.
        return hashlib.sha256(f"pseudonym-rotation:{user_id}".encode("utf-8")).digest()


    def _hash_domain(self, domain: str) -> str:
        """Verschleiert eine Domain mit HMAC-SHA256 und dem lokalen Secret."""
        # Startet HMAC
        return hmac.new(
            # Lokales Secret
            self.local_secret,
            # String in Bytes
            domain.encode("utf-8"),
            # Algorithmus
            hashlib.sha256,
        # Rückgabe als Hexadezimal-String
        ).hexdigest()


    def assign_domain(self, domain_key: str) -> int:
        """Gibt den Slot einer gehashten Domain zurück und weist neuen Domains zufällig einen Slot zu."""
        # Prüfung ob Domain bereits zugewiesen ist. Falls ja wird Slot zurückgegeben.
        if domain_key in self.domain_to_slot_map:
            return self.domain_to_slot_map[domain_key]
        # Falls keine Zuweisung existiert, wird ein zufälliger Slot zugewiesen.
        # Zufallsgenerator wählt einen Slot von 0 bis num_slots - 1 (numpy dann in py integer).
        assigned_slot = int(self.rng.integers(0, self.cfg.num_slots))
        # In Mapping eintragen. Domain wird dem Slot zugewiesen.
        self.domain_to_slot_map[domain_key] = assigned_slot
        # Für Rotationen eintragen. Wer gehört alles zu diesem Slot.
        self.slot_to_domains[assigned_slot].add(domain_key)
        return assigned_slot


    def release_slot(self, slot_id: int) -> None:
        """Rotation eines Slots"""
        # Alle Domains werden aus dem Slot entfernt. Nutzt die vorhin eingetragenen Domains.
        for domain_key in self.slot_to_domains[slot_id]:
            del self.domain_to_slot_map[domain_key]
        # Slot wird restlos geleert.
        self.slot_to_domains[slot_id].clear()
