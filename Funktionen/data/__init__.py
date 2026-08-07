"""
Läd beide Datensätze herunter, entpackt sie und speichert sie in Data/datensatz/
"""

from .load_dataset import browsing_data
from .load_whotracksme import whotracksme_data


__all__ = [
    "browsing_data",
    "whotracksme_data"
]
