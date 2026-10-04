import pandas as pd
import concurrent.futures
import itertools
from pathlib import Path
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from Funktionen.utils import log_status
from datetime import datetime
from reason_analysis import reason_analysis

def simulate_user_chunk(chunk_args):
    """Führt die Simulation für einen einzelnen Nutzer in einem separaten Prozess aus."""
    user_id, index, total_users, user_df, cfg, verbose, observation_end = chunk_args
    sim = UserSimulation(user_id=user_id, cfg=cfg)
    annotated_df = sim.run_user(user_df, observation_end)
    
    if verbose:
        progress_pct = (index / total_users) * 100
        if index % max(1, total_users // 10) == 0 or index == total_users:
            log_status(
                f"Fortschritt: {progress_pct:.1f}% | User {index}/{total_users} fertig ({user_id}) | "
                f"Segmente={len(sim.segment_records)} | Resets={sim.total_resets()}",
                True,
            )
    return annotated_df, sim.segment_records

def main(use_parallel: bool = True, verbose: bool = True):
    data_path = Path("Data/datensatz/browsing_clean.csv")
    out_dir = Path("Data/ergebnisse/raw_sweeps")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Lade Basis-Daten...")
    df = pd.read_csv(data_path)
    df["used_at"] = pd.to_datetime(df["used_at"])
    df = df.sort_values(by=["panelist_id", "used_at"])
    observation_end = df["used_at"].max()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Gruppiere Nutzer...")
    grouped_users = list(df.groupby("panelist_id", sort=False))
    total_users = len(grouped_users)
    # Kompletter block für eine leichte ausführung. Das sind alle Kombinationen
    sweep_blocks = [
        ([25, 50, 100], [3, 5], [25, 100, 250], [7, 14]),
        ([10, 50], [10], [700], [7, 14]),
        ([5], [3], [200, 500, 600, 700], [7, 14]),
        ([225], [30], [700], [7, 14]),
        ([200, 225, 250], [3, 10, 15], [700, 1000], [7]),
        ([100, 400], [10], [700, 1000], [7]),
        ([225], [10], [100, 250], [7, 14]),
        (list(range(200, 251, 5)), [10],
         [500, 600, 700, 800, 900, 1000], [14]),
        ([100, 400, 600], [10],
         [500, 700, 1000, 1250, 1500, 1750, 2000], [14]),
        ([225], [10], [1250, 1500, 1750, 2000], [14]),
        ([200, 250], [3, 15], [700, 1000], [14]),
        ([225], [15], [700, 1000], [14]),
        ([100, 225, 400, 600], [3, 20],
         [500, 700, 1000, 2000], [14]),
        ([100, 225, 400], [10], [700, 1000], [21, 31]),
        ([3, 5, 10, 15, 25], [2, 3, 5, 7, 10], [25, 50], [31]),
        ([3, 5, 15, 25], [2, 3, 5, 7, 10], [100, 250, 500], [31]),
        ([10, 50], [2, 3, 5, 7, 10, 15, 20, 30, 50],
         [100, 250, 500, 750, 1000], [31]),
        ([100], [2, 3, 5, 7], [100, 250, 500, 750, 1000], [31]),
        ([100], [10], [100, 250, 500, 750], [31]),
        ([225], [5, 7], [700], [14]),
        ([25, 150], [10], [700], [14]),
        ([100], [10], [100, 250], [14]),
        ([100], [5, 7, 15], [700], [14]),
        ([15, 35, 75], [10], [700], [14]),
        ([25, 50, 100], [3, 5, 7, 10], [100, 250, 500], [14, 21]),
        ([25, 50, 75, 100], [10], [700], [21]),
        ([15, 25, 35, 75, 150, 600], [10], [700], [7]),
        ([100], [10], [100, 250, 500, 1250, 1500, 2000], [7]),
        ([100], [3, 5, 7, 15, 20], [700], [7]),
        ([150], [30], [250, 500], [31]),]

    param_combinations = []

    for slot_configs, domain_configs, event_configs, day_configs in sweep_blocks:
        param_combinations.extend(itertools.product(slot_configs, domain_configs, event_configs, day_configs,))

    total_combinations = len(param_combinations)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starte Grid Search mit {total_combinations} Kombinationen.\n")

    for idx, (slots, domains, events, days) in enumerate(param_combinations, 1):
        file_prefix = f"{slots}_{domains}_{events}_{days}"
        events_out_path = out_dir / f"{file_prefix}_events.csv"
        segments_out_path = out_dir / f"{file_prefix}_segments.csv"

        # Resume-Logik: Bereits berechnete Kombinationen überspringen
        if events_out_path.exists() and segments_out_path.exists():
            print(f"[{idx}/{total_combinations}] Überspringe {file_prefix} - Dateien existieren bereits.")
            continue

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [{idx}/{total_combinations}] Simuliere: Slots={slots}, Domains={domains}, Events={events}, Days={days}")
        
        cfg = PipelineConfig(num_slots=slots, max_domains=domains, max_events=events, max_days=days, use_tracker_mapping=False)
        user_chunks = [
            (uid, index, total_users, user_df, cfg, verbose, observation_end)
            for index, (uid, user_df) in enumerate(grouped_users, start=1)
        ]
        
        all_annotated_rows = []
        all_segment_records = []

        if use_parallel:
            with concurrent.futures.ProcessPoolExecutor(max_workers=7) as executor:
                futures = [executor.submit(simulate_user_chunk, chunk) for chunk in user_chunks]
                for future in concurrent.futures.as_completed(futures):
                    annotated_df, segment_records = future.result()
                    all_annotated_rows.append(annotated_df)
                    all_segment_records.extend(segment_records)
        else:
            for chunk in user_chunks:
                annotated_df, segment_records = simulate_user_chunk(chunk)
                all_annotated_rows.append(annotated_df)
                all_segment_records.extend(segment_records)

        # Ergebnisse pro Parameter-Kombination in den Ordner speichern
        final_df = pd.concat(all_annotated_rows, ignore_index=True)
        final_df.to_csv(events_out_path, index=False)
        
        segments_df = pd.DataFrame(all_segment_records)
        segments_df.to_csv(segments_out_path, index=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gespeichert: {file_prefix}")

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sweep vollständig abgeschlossen.")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starte Abschlussgrund-Analyse...")
    reason_analysis()
if __name__ == "__main__":
    main(use_parallel=True, verbose=True)