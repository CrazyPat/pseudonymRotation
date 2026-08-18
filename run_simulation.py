import pandas as pd
import json
import concurrent.futures
from pathlib import Path
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from Funktionen.utils import log_status

def simulate_user_chunk(chunk_args):
    """Führt die Simulation für einen einzelnen Nutzer in einem separaten Prozess aus."""
    user_id, index, total_users, user_df, cfg, verbose = chunk_args
    sim = UserSimulation(user_id=user_id, cfg=cfg)
    annotated_df = sim.run_user(user_df)
    
    if verbose:
        progress_pct = (index / total_users) * 100
        log_status(
            f"Fortschritt: {progress_pct:.1f}% | User {index}/{total_users} fertig ({user_id}) | "
            f"Segmente={len(sim.segment_records)} | Resets={sim.total_resets()}",
            True,
        )
    return annotated_df, sim.segment_records

def main(use_parallel: bool = True, verbose: bool = True):
    data_path = Path("Data/datensatz/browsing_clean.csv")
    mapping_path = Path("Data/datensatz/domain_tracker_mapping.json")
    
    df = pd.read_csv(data_path)
    df["used_at"] = pd.to_datetime(df["used_at"])
    df = df.sort_values(by=["panelist_id", "used_at"])

    cfg = PipelineConfig(num_slots=10, max_domains=15, max_events=100, max_days=7, use_tracker_mapping=False)

    if cfg.use_tracker_mapping and mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            tracker_mapping = json.load(f)
        
        expanded_rows = []
        for row in df.itertuples(index=False):
            trackers = tracker_mapping.get(row.domain, [])
            if trackers:
                for tracker in trackers:
                    expanded_rows.append({
                        "panelist_id": row.panelist_id,
                        "domain": tracker,
                        "used_at": row.used_at
                    })
            else:
                expanded_rows.append({
                    "panelist_id": row.panelist_id,
                    "domain": row.domain,
                    "used_at": row.used_at
                })
        df = pd.DataFrame(expanded_rows)
    grouped_users = list(df.groupby("panelist_id", sort=False))
    total_users = len(grouped_users)
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


    final_df = pd.concat(all_annotated_rows, ignore_index=True)
    out_path = Path("Data/ergebnisse/simulation_output.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(out_path, index=False)
    segments_df = pd.DataFrame(all_segment_records)
    segments_out_path = Path("Data/ergebnisse/simulation_segments.csv")
    segments_df.to_csv(segments_out_path, index=False)

if __name__ == "__main__":
    main(use_parallel=False, verbose=True)