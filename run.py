from pathlib import Path
import json
import pandas as pd
from Funktionen import run_sweep

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "Data" / "browsing_clean.csv"
TRACKER_MAP_PATH = BASE_DIR / "Data" / "domain_tracker_mapping.json"
checkpoint_file = BASE_DIR / "Data" / "sweep_checkpoint.csv"

if __name__ == "__main__":
    df_raw = pd.read_csv(DATA_PATH)
    with open(TRACKER_MAP_PATH, "r", encoding="utf-8") as f:
        tracker_mapping = json.load(f)

    all_unique_trackers = set()
    for trackers in tracker_mapping.values():
        all_unique_trackers.update(trackers)
    total_vocab_size = len(all_unique_trackers)

    slot_configs = [5, 10, 15, 20, 25, 35, 40, 45, 50, 55, 60, 65]
    domain_configs = [5, 10, 15, 20, 30, 45, 50, 55, 60, 75, 90, 105, 125, 140, 200]
    event_configs = [50, 100, 150, 200, 300, 450, 700, 800]
    k_values = [1, 3, 5, 10, 20]

    results_df = run_sweep(
        df_raw=df_raw,
        tracker_mapping=tracker_mapping,
        checkpoint_file=checkpoint_file,
        slot_configs=slot_configs,
        domain_configs=domain_configs,
        event_configs=event_configs,
        num_eval_users=2148,
        k_values=k_values,
        vocab_size=total_vocab_size,
        use_parallel=True,
        verbose=True,
    )
    if not results_df.empty:
        results_df.to_csv(BASE_DIR / "Data" / "final_evaluated_sweep.csv", index=False)
        print("Sweep erfolgreich beendet")