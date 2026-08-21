import pandas as pd
import concurrent.futures
import itertools
from pathlib import Path
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from Funktionen.utils import log_status
from datetime import datetime

def simulate_user_chunk(chunk_args):
    """Führt die Simulation für einen einzelnen Nutzer in einem separaten Prozess aus."""
    user_id, index, total_users, user_df, cfg, verbose = chunk_args
    sim = UserSimulation(user_id=user_id, cfg=cfg)
    annotated_df = sim.run_user(user_df)
    
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

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Gruppiere Nutzer...")
    grouped_users = list(df.groupby("panelist_id", sort=False))
    total_users = len(grouped_users)

    slot_configs = [20, 60, 150]
    domain_configs = [10, 20]
    event_configs = [20, 50, 100]
    day_configs = [7, 14]
    
    param_combinations = list(itertools.product(slot_configs, domain_configs, event_configs, day_configs))
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
        
        cfg = PipelineConfig(
            num_slots=slots, 
            max_domains=domains, 
            max_events=events, 
            max_days=days, 
            use_tracker_mapping=False
        )

        user_chunks = [
            (uid, index, total_users, user_df, cfg, verbose) 
            for index, (uid, user_df) in enumerate(grouped_users, start=1)
        ]
        
        all_annotated_rows = []
        all_segment_records = []

        if use_parallel:
            with concurrent.futures.ProcessPoolExecutor() as executor:
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

if __name__ == "__main__":
    main(use_parallel=True, verbose=True)