"""
Lädt den Zenodo-Datensatz herunter, entpackt ihn und speichert ihn in Data/datensatz/
"""

from .load_dataset import browsing_data


__all__ = [
    "browsing_data",
]
