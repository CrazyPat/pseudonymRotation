"""
Zuweisungs-Logik der Pseudonym-Rotation.
"""

import hashlib
import hmac
import secrets
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
        # Random Number
        self.rng = rng
        # Local Secret für HMAC SHA256
        self.local_secret = local_secret
        # Leeres Mapping von Domain --> Slot
        self.domain_to_slot_map: Dict[str, int] = {}
        # Leeres Mapping von Slot --> Pseudonyme = Baut die Zuordnung auf (z. B. 0: set())
        self.slot_to_pseudonym: Dict[int, Set[str]] = {i: set() for i in range(cfg.num_slots)}


    @staticmethod
    def gen_local_secret(user_id: str) -> bytes:
        """Erezugt ein Locales-Secret für HMAC basierend auf der User-ID"""
        return hashlib.sha256(f"pseudonym-rotation:{user_id}".encode("utf-8")).digest()


    def _hash_domain(self, domain: str) -> str:
        """Verschleiert eine Domain mit HMAC SHA256 und einem Localen-Secret"""
        # Startet HMAC
        return hmac.new(
            # Locales-Secret
            self.local_secret,
            # String in Bytes
            domain.encode("utf-8"),
            # Algorithmus
            hashlib.sha256,
        # Rückgabe als Hexadezimal-String
        ).hexdigest()

    def assign_domain(self, domain: str) -> int:
        """Hasht die Domain und weist einen Slot zu."""
        # Domainhashing
        pseudonym = self._hash_domain(domain)
        # Prüfung ob Domain bereits zugewiesen ist. Falls ja wird Slot zurückgegeben.
        if pseudonym in self.domain_to_slot_map:
            return self.domain_to_slot_map[pseudonym]
        # Falls keine Zuweisung existiert, wird ein zufälliger Slot zugewiesen.
        # Randomgenerator wählt zwischen 0 und in der Konfig angegebenen Slots. (numpy dann in py integer)
        assigned_slot = int(self.rng.integers(0, self.cfg.num_slots))
        # In Mapping eintragen für spätere Prüfung.
        self.domain_to_slot_map[pseudonym] = assigned_slot
        # Für Rotationen eintragen.
        self.slot_to_pseudonym[assigned_slot].add(pseudonym)
        return assigned_slot

    def release_slot(self, slot_id: int) -> None:
        """Rotation eines Slots"""
        # Alle Domains werden aus dem Slot entfernt. Nutzt die vorhin eingetragenen Domains.
        for pseudonym in self.slot_to_pseudonym[slot_id]:
            del self.domain_to_slot_map[pseudonym]
        # Slot wird restlos geleert.
        self.slot_to_pseudonym[slot_id].clear()