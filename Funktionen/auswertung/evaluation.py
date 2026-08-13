"""
Simuliert Nutzer Parallel.
Auswertung einer Konfiguration aus der Nuter Simulation.
Berechnet die Kosinus-Ähnlichkeit, k-NN-Accuracy Utility.
"""

import concurrent.futures
import json
from collections import Counter

import numpy as np
import scipy.sparse as sp
import pandas as pd

from ..config import PipelineConfig
from ..pseudonym.simulation import simulate_user_chunk
from ..utils import log_status


def _score_segments(segments_sorted, domain_to_idx, baseline_matrix, user_list, k_values, verbose=False):
    """Baut Sparse-Matrix und berechnet kNN-Accuracy für eine gegebene Segment-Liste."""
    # Dimensionen für Sparse Matrix definieren
    num_segments = len(segments_sorted)
    # Falls keine Segmente übergeben wurden --> leeres Ergebnis.
    if num_segments == 0:
        return {f"kNN_Accuracy_k{k}": 0.0 for k in k_values}, 0

    num_vocab = len(domain_to_idx)

    # Listen für COO-Format
    log_status(f"Sparse-Koordinaten ({num_segments} x {num_vocab})", verbose)
    rows = []
    cols = []
    data = []

    # Speichert JEDE Zeile der Matrix. Wichtig für spätere Berechnung der Kosinus-Ähnlichkeit zwischen aufeinanderfolgenden Segmenten.
    query_A = []

    # Über alle Segmente
    for i, seg in enumerate(segments_sorted):
        if i > 0 and i % 500000 == 0:
            log_status(f"Verarbeite Segmente: {i}/{num_segments}", verbose)

        # Speichert Nutzer_ID.
        query_A.append(seg["user_id"])
        # Domain-Counter aus dem JSON laden
        counter_data = json.loads(seg["tracker_counter_json"])

        # Befüllt die Listen für das COO-Format mit den aus dem Vokabular gezählten Trackern.
        for dom, count in counter_data.items():
            if dom in domain_to_idx:
                rows.append(i)
                cols.append(domain_to_idx[dom])
                data.append(float(count))

    # Erstelle direkt eine CSR-Matrix aus den COO-Arrays
    query_matrix = sp.coo_matrix((data, (rows, cols)), shape=(num_segments, num_vocab)).tocsr()
    # Berechnet die Norm der Matrix.
    row_norms = np.sqrt(query_matrix.multiply(query_matrix).sum(axis=1).A1)
    # Falls teilen durch 0
    row_norms[row_norms == 0] = 1.0
    inv_norms = sp.diags(1.0 / row_norms)
    # Normiert die Matrix auf einheitliche Länge 1.0.
    query_matrix = inv_norms.dot(query_matrix)

    log_status("k-NN Auswertung", verbose)
    correct_predictions = {k: 0 for k in k_values}

    # k-NN
    batch_size = 10000
    max_k = max(k_values)

    # Nutzer-IDs
    user_array = np.array(user_list)
    query_users = np.array(query_A)
    # Fortschrittsanzeige
    for start_idx in range(0, num_segments, batch_size):
        end_idx = min(start_idx + batch_size, num_segments)

        if start_idx > 0 and start_idx % 100000 == 0:
            log_status(f"Auswertung: {start_idx}/{num_segments} Segmente", verbose)

        # Matrixmultiplikation für den Batch
        query_batch = query_matrix[start_idx:end_idx]
        sims = query_batch.dot(baseline_matrix.T)
        # Sortiert alle Zeilen des Batches gleichzeitig und holt nur die Top-max_k Spalten
        top_indices = np.argsort(sims, axis=1)[:, ::-1][:, :max_k]
        # Mappt Indizes zu Nutzer-IDs
        top_users = user_array[top_indices]
        # Wahre Nutzer für diesen Batch als Spaltenvektor
        true_users = query_users[start_idx:end_idx, None]
        # Zählt die Treffer für alle k-Werte vektorisiert
        for k in k_values:
            # Ist der Nutzer in den ersten k Spalten des Bachtes?
            matches = (top_users[:, :k] == true_users).any(axis=1)
            correct_predictions[k] += int(matches.sum())

    # Accuracy pro k-Wert berechnen.
    acc = {f"kNN_Accuracy_k{k}": correct_predictions[k] / num_segments for k in k_values}
    return acc, num_segments


def evaluate_configuration(df_eval: pd.DataFrame, cfg: PipelineConfig, baseline_matrix: np.ndarray, user_list: list, domain_to_idx: dict,
    tracker_mapping: dict, k_values: list, use_parallel: bool = True, verbose: bool = False) -> dict:
    # Gruppiert die Nutzer nach der ID und erstellt eine Liste für die Simulation.
    grouped_users = list(df_eval.groupby("panelist_id", sort=False))
    # Anzahl an Nutzer
    total_users = len(grouped_users)
    # Nutzer werden in Chunks aufgeteil --> Für parallisierte Verarbeitung.
    user_chunks = [(uid, index, total_users, user_df, cfg, tracker_mapping, verbose) for index, (uid, user_df) in enumerate(grouped_users, start=1)]

    # Ausgabe der config.
    if verbose:
        log_status(f"Slots={cfg.num_slots}, Domains={cfg.max_domains}, Events={cfg.max_events}", True)
    
    all_segments = []
    total_resets = 0

    # Alle Nutzer werden parallel oder sequentiell simuliert.
    # Parallel auf allen Kernen.
    if use_parallel:
        # Auswahl der Kerne. Hierbei alle die verfügbar sind. Können reduziert werden falls nötig mit z.b. max_workers=4
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Alle Aufgaben werden an die Kerne verteilt.
            futures = [executor.submit(simulate_user_chunk, chunk) for chunk in user_chunks]
            # Ergebnisse werden direkt gesammelt, wenn sie fertig sind.
            for future in concurrent.futures.as_completed(futures):
                user_id, segments, resets = future.result()
                all_segments.extend(segments)
                total_resets += resets
    else:
        # Sequentielle Verarbeitung
        for chunk in user_chunks:
            user_id, segments, resets = simulate_user_chunk(chunk)
            all_segments.extend(segments)
            total_resets += resets
    
    # Falls nichts simuliert wurde --> NONE
    if not all_segments:
        return None
    
    # Segemente werden sortiert nach Nutzer,Slot und Segment_id damit die Reihenfolge für die Kosinus-Ähnlichkeit korrekt ist.
    log_status(f"Total Segmente: {len(all_segments)}.", verbose)
    # Zählt wie oft welcher Rotations-Grund vorkam zur prüfung wann max_domains greift.
    trigger_counts = Counter(s["trigger"] for s in all_segments)
    segments_sorted = sorted(all_segments, key=lambda x: (x["user_id"], x["slot_id"], x["segment_id"]))
    
    # Dimensionen für Sparse Matrix definieren
    num_segments = len(segments_sorted)
    num_vocab = len(domain_to_idx)

    # Listen für COO-Format
    log_status(f"Sparse-Koordinaten ({num_segments} x {num_vocab})", verbose)
    rows = []
    cols = []
    data = []
    
    # Speichert JEDE Zeile der Matrix. Wichtig für spätere Berechnung der Kosinus-Ähnlichkeit zwischen aufeinanderfolgenden Segmenten.
    query_A = []
    # Alle TP-Events pro Segment --> Für Utility.
    third_party_counts = []
    
    # Über alle Segmente
    for i, seg in enumerate(segments_sorted):
        if i > 0 and i % 500000 == 0:
            log_status(f"Verarbeite Segmente: {i}/{num_segments}", verbose)

        # Speichert Nutzer_ID.
        query_A.append(seg["user_id"])
        # Speichert die Anzahl an Third-Party-Events pro Segment.
        third_party_counts.append(seg["tracker_events"])
        # Domain-Counter aus dem JSON laden
        counter_data = json.loads(seg["tracker_counter_json"])


        # Befüllt die Listen für das COO-Format mit den aus dem Vokabular gezählten Trackern.
        for dom, count in counter_data.items():
            if dom in domain_to_idx:
                rows.append(i)
                cols.append(domain_to_idx[dom])
                data.append(float(count))
    
    # Erstelle direkt eine CSR-Matrix aus den COO-Arrays
    query_matrix = sp.coo_matrix((data, (rows, cols)), shape=(num_segments, num_vocab)).tocsr()
    # Berechnet die Norm der Matrix.
    row_norms = np.sqrt(query_matrix.multiply(query_matrix).sum(axis=1).A1)
    # Falls teilen durch 0
    row_norms[row_norms == 0] = 1.0
    inv_norms = sp.diags(1.0 / row_norms)
    # Normiert die Matrix auf einheitliche Länge 1.0.
    query_matrix = inv_norms.dot(query_matrix)

    log_status("Kosinus-Ähnlichkeit und k-NN Auswertung", verbose)
    cosine_sims = []

    # Kosinus-Ähnlichkeit aufeinanderfolgender Segmente
    if num_segments > 1:
        row_sims = query_matrix[1:].multiply(query_matrix[:-1]).sum(axis=1).A1
        
        for i in range(1, num_segments):
            prev = segments_sorted[i - 1]
            curr = segments_sorted[i]
            if prev["user_id"] == curr["user_id"] and prev["slot_id"] == curr["slot_id"] and prev["trigger"] == "rotation_threshold":
                cosine_sims.append(float(row_sims[i - 1]))

    log_status("Konfiguration abgeschlossen.", verbose)

    # Nur echte Rotationen
    segments_rotation_only = [s for s in segments_sorted if s["trigger"] == "rotation_threshold"]
    # Zwei Angreifer einmal alle Segmente und einmal nur nach abgeschlossener Rotation.
    acc_all, n_all = _score_segments(segments_sorted, domain_to_idx, baseline_matrix, user_list, k_values, verbose)
    acc_rot, n_rot = _score_segments(segments_rotation_only, domain_to_idx, baseline_matrix, user_list, k_values, verbose)
    # Durchschnitt zwischen den Segmenten. Fallback auf 0 falls keine Segmente.
    mean_cosine = float(np.mean(cosine_sims)) if cosine_sims else 0.0

    # Ergebnis Dict:
    result = {
        "Anzahl_Slots": cfg.num_slots,
        "Max_Domains": cfg.max_domains,
        "Max_Events": cfg.max_events,
        "Max_Days": cfg.max_days,
        "Session_Timeout": cfg.session_timeout_minutes,
        "Mean_Cosine_Prev_Pseudonym": mean_cosine,
        "Avg_Utility_ThirdParty": np.mean(third_party_counts),
        "Total_Resets": total_resets,
        "Total_Segments": n_all,
        "Total_Segments_Rotation": n_rot,
        "Rotation_Threshold": trigger_counts.get("rotation_threshold", 0) / len(all_segments),
        "Session_Gap": trigger_counts.get("session_gap", 0) / len(all_segments),
        "End_Of_Stream": trigger_counts.get("end_of_stream", 0) / len(all_segments),
    }

    # Die Accuracy für jeden k-Wert dynamisch berechnen und dem Dict hinzufügen, für beide Bedrohungsmodelle.
    for k in k_values:
        result[f"kNN_Accuracy_k{k}_Segments"] = acc_all[f"kNN_Accuracy_k{k}"]
        result[f"kNN_Accuracy_k{k}_Rotation"] = acc_rot[f"kNN_Accuracy_k{k}"]

    # Ausgabe zur Kontrolle
    if verbose:
        ref_k = k_values[0] 
        log_status(
            f"Config -> Acc (k={ref_k}, Rotation): {result[f'kNN_Accuracy_k{ref_k}_RotationOnly']:.4f} | "
            f"Acc (k={ref_k}, All): {result[f'kNN_Accuracy_k{ref_k}_AllSegments']:.4f} | "
            f"Cosine: {result['Mean_Cosine_Prev_Pseudonym']:.4f} | Util: {result['Avg_Utility_ThirdParty']:.2f}",
            True,
        )
        
    return result