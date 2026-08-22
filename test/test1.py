import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import pandas as pd
import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ProcessPoolExecutor, as_completed


def compute_linkage_metrics(df_segments):
    df_segments = df_segments.reset_index(drop=True)
    n_segments = len(df_segments)
    if n_segments < 2:
        return None

    vectorizer = DictVectorizer(sparse=True)
    X = vectorizer.fit_transform(df_segments['domain_counter'].tolist())
    user_ids = df_segments['user_id'].values

    own_sims, other_sims, attacker_success_count = [], [], 0

    # Chunk-Größe dynamisch an n_segments koppeln, damit jeder Chunk
    # (chunk_size x n_segments, float64) auf ~300 MB begrenzt bleibt,
    # statt bei großen Dateien auf mehrere GB pro Chunk zu wachsen.
    target_bytes = 300_000_000
    chunk_size = max(1, min(2000, target_bytes // (n_segments * 8)))

    for start_idx in range(0, n_segments, chunk_size):
        end_idx = min(start_idx + chunk_size, n_segments)
        sim_chunk = cosine_similarity(X[start_idx:end_idx], X)
        for i, row_idx in enumerate(range(start_idx, end_idx)):
            current_user = user_ids[row_idx]
            sims = sim_chunk[i]
            own_mask = (user_ids == current_user); own_mask[row_idx] = False
            other_mask = (user_ids != current_user)
            max_own = np.max(sims[own_mask]) if np.any(own_mask) else 0.0
            max_other = np.max(sims[other_mask]) if np.any(other_mask) else 0.0
            own_sims.append(max_own); other_sims.append(max_other)
            if max_own > max_other and max_own > 0:
                attacker_success_count += 1
        del sim_chunk

    own_sims = np.array(own_sims)
    chord = np.sqrt(np.maximum(0, 2 - 2 * own_sims))
    return {
        "Avg_Chord_Distance": np.mean(chord),
        "Avg_Max_Cosine_Own": np.mean(own_sims),
        "Avg_Max_Cosine_Other": np.mean(np.array(other_sims)),
        "Identification_Rate": attacker_success_count / n_segments,
        "Valid_Segments": n_segments,
    }


def process_single_file(seg_file):
    """Verarbeitet eine einzelne Sweep-Datei (wird parallel ausgeführt)."""
    filename_clean = seg_file.stem.replace("_segments", "")
    parts = filename_clean.split("_")
    if len(parts) != 4:
        return None
        
    slots, domains, events, days = map(int, parts)
    print(f"Starte Datei: Slots={slots}, Domains={domains}, Events={events}, Days={days}")
    
    df_segments = pd.read_csv(seg_file)
    if df_segments.empty:
        return None
        
    
    if df_segments.empty:
        return None
        
    df_segments['domain_counter'] = df_segments['domain_counter_json'].apply(json.loads)
    df_segments = df_segments[df_segments['domain_counter'].astype(bool)]
    
    df_segments = df_segments.reset_index(drop=True)
    n_segments = len(df_segments)
    
    if n_segments < 2:
        return None

    metrics_incl = compute_linkage_metrics(df_segments)
    metrics_excl = compute_linkage_metrics(df_segments[df_segments['trigger'] != 'end_of_stream'])

    result = {"Anzahl_Slots": slots, "Max_Domains": domains, "Max_Events": events, "Max_Days": days}
    if metrics_incl: result.update({f"Incl_{k}": v for k, v in metrics_incl.items()})
    if metrics_excl: result.update({f"Excl_{k}": v for k, v in metrics_excl.items()})
    return result if (metrics_incl or metrics_excl) else None


def main():
    sweep_dir = Path("Data/ergebnisse/raw_sweeps")
    out_dir = Path("Data/ergebnisse")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / "verkettungs_ranking.csv"
    
    results = []
    processed_set = set()
    
    # Checkpoint laden, falls vorhanden
    if output_file.exists():
        df_existing = pd.read_csv(output_file)
        if not df_existing.empty:
            results = df_existing.to_dict('records')
            for _, row in df_existing.iterrows():
                # Erfasst bereits berechnete Konfigurationen
                processed_set.add((int(row["Anzahl_Slots"]), int(row["Max_Domains"]), int(row["Max_Events"]), int(row["Max_Days"])))
            print(f"Checkpoint geladen: {len(processed_set)} Dateien wurden bereits berechnet und werden übersprungen.")

    segment_files = list(sweep_dir.glob("*_segments.csv"))
    files_to_process = []
    
    # Filtere bereits verarbeitete Dateien aus
    for seg_file in segment_files:
        filename_clean = seg_file.stem.replace("_segments", "")
        parts = filename_clean.split("_")
        if len(parts) == 4:
            identifier = tuple(map(int, parts))
            if identifier not in processed_set:
                files_to_process.append(seg_file)

    print(f"Starte parallele globale Verkettungs-Auswertung für {len(files_to_process)} (von {len(segment_files)}) Sweep-Dateien...\n")

    if files_to_process:
        # Nutzt automatisch alle verfügbaren CPU-Kerne parallel
        with ProcessPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(process_single_file, seg_file): seg_file for seg_file in files_to_process}
            
            for future in as_completed(future_to_file):
                res = future.result()
                if res is not None:
                    results.append(res)
                    # Optional: Hier könnte man nach jedem Ergebnis auch zwischenspeichern (pd.DataFrame(results).to_csv...) 
                    # um auch bei harten Abbrüchen während des Laufs nicht nochmal bei Null zu starten.
                    pd.DataFrame(results).to_csv(output_file, index=False)

    df_final = pd.DataFrame(results)
    
    if not df_final.empty:
        # Falls die Spalte 'Avg_Chord_Distance' existiert (wird nur gesetzt wenn compute_linkage_metrics erfolgreich war), sortieren
        if "Incl_Avg_Chord_Distance" in df_final.columns:
            df_final = df_final.sort_values(by="Incl_Avg_Chord_Distance", ascending=False)
            
        df_final.to_csv(output_file, index=False)
        
        print("\n=== RANKING: VERKETTUNGSRISIKO ===")
        print(df_final.to_string(index=False))
        print(f"\nErfolgreich gespeichert unter: {output_file}")
    else:
        print("Keine Ergebnisse zum Auswerten gefunden.")

if __name__ == "__main__":
    main()