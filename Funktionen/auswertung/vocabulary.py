"""
Aufbau des Tracker-Vokabulars und der Baseline
"""

from collections import Counter
import numpy as np
import pandas as pd


def build_domain_vocabulary(df: pd.DataFrame, tracker_mapping: dict, vocab_size: int) -> dict[str, int]:
    """Erstellt ein Vokabular der Top-Domains basierend auf der Häufigkeit der Tracker in den Daten."""
    # Es werden alle Tracker aus dem Mapping geladen.
    all_trackers = [tracker for trackers in tracker_mapping.values() for tracker in trackers]
    # Top-Domains werden nach Häufigkeit der Tracker ausgewählt.
    top_domains = Counter(all_trackers).most_common(vocab_size)
    # Umwandlung in ein Dict.
    return {d[0]: i for i, d in enumerate(top_domains)}


def build_baseline_matrix(df: pd.DataFrame, tracker_mapping: dict, domain_to_idx: dict) -> tuple[np.ndarray, list]:
    """Erstellt die Baseline für jeden Nutzer, basierend auf der Häufigkeit der Tracker in den Daten."""
    # Einzigartige Nutzer werden gewählt
    unique_users = df["panelist_id"].unique()
    # Matrixaufbau = Nutzer x Tracker
    matrix = np.zeros((len(unique_users), len(domain_to_idx)), dtype=float)
    user_list = []
    # Befüllen der Matrix.
    for i, user_id in enumerate(unique_users):
        # Nutzer hinzufügen
        user_list.append(user_id)
        # Domains des Nutzer auslesen, welche er besucht hat.
        user_rows = df[df["panelist_id"] == user_id]["domain"].tolist()
        # Alle Tracker
        user_trackers = []
        # Tracker für jede Domain werden gesammelt --> Damit ein Mapping über alle Tracker welche ein User ausgesetzt war
        for dom in user_rows:
            user_trackers.extend(tracker_mapping.get(dom, []))
        # Tracker zählen
        counts = Counter(user_trackers)
        # Befüllt Matrix mit den gezählten Trackern.
        for dom, count in counts.items():
            if dom in domain_to_idx:
                matrix[i, domain_to_idx[dom]] = float(count)
        
    # Normierung der Matrix --> Um Vergleichbarkeit der Nutzer zu schaffen.
    norm = np.linalg.norm(matrix, axis=1, keepdims=True)
    # Falls ein Nutzer keine Tracker hatte wird es auf 1 gesetzt um Division durch 0 zu verhindern.
    norm[norm == 0] = 1.0
    # Normalisiert die Matrix auf einheitliche Länge.
    return matrix / norm, user_list
