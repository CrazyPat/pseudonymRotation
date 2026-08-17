"""
Läd beide Datensätze herunter, entpackt sie und speichert sie in Data/datensatz/
"""

from .load_dataset import browsing_data


__all__ = [
    "browsing_data",
]
