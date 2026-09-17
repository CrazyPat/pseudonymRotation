import os
# Umgebungsvars damit jeder Prozess nur 1 Thread nutzt.
# Multi-Processing
os.environ["OMP_NUM_THREADS"] = "1"
# Intel Math Kernel lib für lineare algebra
os.environ["MKL_NUM_THREADS"] = "1"
# Für Kosinus-Ähnlichkeit
os.environ["OPENBLAS_NUM_THREADS"] = "1"
# Für Mac!
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
# FÜr numpy und große dfs
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import pandas as pd
import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ProcessPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfTransformer

    
def linkage_metrics(df_segments) -> dict: 
    """Berechnet die Verkettungs-Metriken für ein df."""
    # Indexierung fixen. Später für incl und excl wichtig, weil sonst Lücken bleiben.
    df_segments = df_segments.reset_index(drop=True)
    n_segments = len(df_segments)
    # Nur wenn du min. 2 Segmente hast, sonst kann man Nutzer nicht vergleichen.
    if n_segments < 2:
        return None

    # Geht alle Segmente durch und speichert domain to index alphabetisch. Dh. als bsp. zuerst a domain index 0 dann b domain index 1 usw.
    # Speichert als sparse damit nicht zu groß wird.
    vectorizer = DictVectorizer(sparse=True)
    # Alle 
    x_counts = vectorizer.fit_transform(df_segments['domain_counter'].tolist())
    tfidf = TfidfTransformer(sublinear_tf=True)
    X = tfidf.fit_transform(x_counts)
    user_ids = df_segments['user_id'].values

    # Nutzer, die in Config nur 1 Segment haben
    segments_per_user = pd.Series(user_ids).value_counts()
    # Für Auswertung wie viele Nutzer nur 1 Segment haben.
    share_single_segment_users = float((segments_per_user < 2).mean())

    own_sims = np.zeros(n_segments)
    other_sims = np.zeros(n_segments)
    attacker_success_count = 0
    
    # Chunk-Größe dynamisch anpassen, damit es nicht zu groß wird und crasht.
    target_bytes = 1_000_000_000
    chunk_size = max(1, min(10000, target_bytes // (n_segments * 8)))

    # Durchläuft alle Segmente in Chunks.
    for start_idx in range(0, n_segments, chunk_size):
        # min für schluss damit kein index out of bounds.
        end_idx = min(start_idx + chunk_size, n_segments)
        # Kosinus-Ähnlichkeit von chunks wird verglichen mit allen Segementen (NUR domain_counter). Gibt aus ob gleich oder nicht.
        sim_chunk = cosine_similarity(X[start_idx:end_idx], X)

        chunk_users = user_ids[start_idx:end_idx]
        
        # Numpy Broadcasting: Matrix-Masken für den ganzen Chunk aufbauen
        own_mask = (chunk_users[:, None] == user_ids)
        other_mask = (chunk_users[:, None] != user_ids)
        
        # Sich selbst ausschließen (Diagonale der Chunk-Sicht auf False setzen)
        local_idx = np.arange(end_idx - start_idx)
        global_idx = np.arange(start_idx, end_idx)
        own_mask[local_idx, global_idx] = False
        
        # Eigener und fremder Höchster Wert vektoriell für jedes einzelne Segment im Chunk berechnen.
        max_own = np.max(sim_chunk, axis=1, where=own_mask, initial=0.0)
        max_other = np.max(sim_chunk, axis=1, where=other_mask, initial=0.0)
        
        # Werte für spätere Distanzauswertung in Arrays schreiben.
        own_sims[start_idx:end_idx] = max_own
        other_sims[start_idx:end_idx] = max_other
        
        # Wenn eigener Wert größer dann ist der Angriff erfolgreich.
        success_mask = (max_own > max_other) & (max_own > 0)
        attacker_success_count += np.sum(success_mask)
        
        # Damit Arbeitsspeicher nicht zu groß wird.
        del sim_chunk, own_mask, other_mask

    # Chord-Distanz berechnen. Wie weit die Segmente auseinander liegen.
    chord = np.sqrt(np.maximum(0, 2 - 2 * own_sims))
    return {
        "Avg_Chord_Distance": np.mean(chord),
        "Avg_Max_Cosine_Own": np.mean(own_sims),
        "Avg_Max_Cosine_Other": np.mean(other_sims),
        "Identification_Rate": attacker_success_count / n_segments,
        "Valid_Segments": n_segments,
        "Share_Single_Segment_Users": share_single_segment_users,
    }


def process_single_file(seg_file):
    """Verarbeitet eine einzelne Sweep-Datei für eine parallele Verarbeitung."""
    # Nimmt Dateinamen der Segmente und baut daraus Konfigurationen. Bsp. 20_10_100_7_segments.csv --> Slots=20, Domains=10, Events=100, Days=7
    filename_clean = seg_file.stem.replace("_segments", "")
    parts = filename_clean.split("_")
    if len(parts) != 4:
        return None
    slots, domains, events, days = map(int, parts)
    print(f"Datei: Slots={slots}, Domains={domains}, Events={events}, Days={days}")
    # csv prüfen und laden.
    df_segments = pd.read_csv(seg_file)
    if df_segments.empty:
        return None
    # domain_counter aus json laden und als Spalte in domain_counter speichern
    df_segments['domain_counter'] = df_segments['domain_counter_json'].apply(json.loads)
    # Pseudonyme entfernen die KEINE Domains aufgerufen haben
    df_segments = df_segments[df_segments['domain_counter'].astype(bool)]
    # Indexierung fixen.
    df_segments = df_segments.reset_index(drop=True)
    n_segments = len(df_segments)
    
    if n_segments < 2:
        return None
    # Verkettungsmetrik für alle Segmente
    metrics_incl = linkage_metrics(df_segments)
    # Verkettungsmetrik für alle Segmente außer end_of_stream
    metrics_excl = linkage_metrics(df_segments[df_segments['trigger'] != 'end_of_stream'])
    # Werte anhängen und zurückgeben.
    result = {"Anzahl_Slots": slots, "Max_Domains": domains, "Max_Events": events, "Max_Days": days}
    if metrics_incl: result.update({f"Incl_{k}": v for k, v in metrics_incl.items()})
    if metrics_excl: result.update({f"Excl_{k}": v for k, v in metrics_excl.items()})
    return result if (metrics_incl or metrics_excl) else None


def verkettung():
    sweep_dir = Path("Data/ergebnisse/raw_sweeps_mit_days")
    out_dir = Path("Data/ergebnisse")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / "verkettungs_ranking_mit_days.csv"
    # Schon fertige confs
    results = []
    # Bereits verarbeitete Konfigs
    processed_set = set()
    
    # Checkpoint laden, falls vorhanden
    if output_file.exists():
        df_existing = pd.read_csv(output_file)
        if not df_existing.empty:
            # Ergebnisse aus der bestehenden Datei laden und in eigenes Dict speichern.
            results = df_existing.to_dict('records')
            for _, row in df_existing.iterrows():
                # Erfasst bereits berechnete Konfigurationen
                processed_set.add((int(row["Anzahl_Slots"]), int(row["Max_Domains"]), int(row["Max_Events"]), int(row["Max_Days"])))
            print(f"Checkpoint geladen: {len(processed_set)} werden übersprungen.")
    # Alle Sweep-Dateien aus der Simulation.
    segment_files = list(sweep_dir.glob("*_segments.csv"))
    files_to_process = []
    
    # Filtere bereits verarbeitete Dateien aus
    for seg_file in segment_files:
        # Prüfen ob auch korrekte Dateien im raw_sweep sind:
        filename_clean = seg_file.stem.replace("_segments", "")
        parts = filename_clean.split("_")
        if len(parts) == 4:
            # Ganzzahlen.
            identifier = tuple(map(int, parts))
            # Schauen ob sie schon berechnet wurden wenn nicht dann speichern in liste.
            if identifier not in processed_set:
                files_to_process.append(seg_file)
    print(f"Auswertung für {len(files_to_process)} (von {len(segment_files)}) Sweep-Dateien\n")
    # Alle configs die noch verarbeitet werden müssen.
    if files_to_process:
        # Auf 4 Kerne gesetz kann aber variert werden.
        with ProcessPoolExecutor(max_workers=4) as executor:
            # Parallelisiert die Verarbeitung und führt process_single_file für jede Datei aus. Speichert die Futures in einem Dict.
            future_to_file = {executor.submit(process_single_file, seg_file): seg_file for seg_file in files_to_process}
            # Wenn ein Kern fertig ist --> Ergebnis zurückgeben.
            for future in as_completed(future_to_file):
                seg_file = future_to_file[future]
                try:
                    res = future.result()
                except Exception as e:
                    print(f"FEHLER bei {seg_file.name}: {e}")
                    continue
                if res is not None:
                    # Zwischenspeichern.
                    results.append(res)
                    pd.DataFrame(results).to_csv(output_file, index=False)
    # Finales speichern
    df_final = pd.DataFrame(results)
    if not df_final.empty:
        df_final.to_csv(output_file, index=False)
        print(f"\nErfolgreich gespeichert unter: {output_file}")
    else:
        print("Keine Ergebnisse zum Auswerten gefunden.")

# main
if __name__ == "__main__":
    verkettung()