from pathlib import Path
import json
import pandas as pd
from Funktionen import run_sweep

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "Data" / "datensatz" / "browsing_clean.csv"
TRACKER_MAP_PATH = BASE_DIR / "Data" / "datensatz" / "domain_tracker_mapping.json"
checkpoint_file = BASE_DIR / "Data" / "datensatz" / "sweep_checkpoint.csv"

if __name__ == "__main__":
    df_raw = pd.read_csv(DATA_PATH)
    with open(TRACKER_MAP_PATH, "r", encoding="utf-8") as f:
        tracker_mapping = json.load(f)
        
    # Vocab Size wird überschrieben --> sonst 500!
    all_unique_trackers = set()
    for trackers in tracker_mapping.values():
        all_unique_trackers.update(trackers)
    total_vocab_size = len(all_unique_trackers)

    # slot_configs = [10, 35, 50, 80, 100, 150] 
    # domain_configs = [10, 50, 100]
    # event_configs = [200, 450, 700]
    # day_configs = [7, 20]
    # timeout_configs = [30, 60] --> https://support.google.com/analytics/answer/2731565?hl=de#zippy=%2Cthemen-in-diesem-artikel
    # k_values = [1, 3, 5, 10, 20]

    # slot_configs = [50, 65, 80, 100, 125, 150, 200] 
    # domain_configs = [10]
    # event_configs = [450, 700, 900, 1200]
    # day_configs = [7, 20]
    # timeout_configs = [30, 60]
    # k_values = [1, 3, 5, 10, 20]

    slot_configs = [65, 150]
    domain_configs = [10]
    event_configs = [5000, 7500, 10000]
    day_configs = [7, 20]
    timeout_configs = [30, 60]
    k_values = [1, 3, 5, 10, 20]

    results_df = run_sweep(
        df_raw=df_raw,
        tracker_mapping=tracker_mapping,
        checkpoint_file=checkpoint_file,
        slot_configs=slot_configs,
        domain_configs=domain_configs,
        event_configs=event_configs,
        day_configs=day_configs,
        timeout_configs=timeout_configs,
        num_eval_users=2148,
        k_values=k_values,
        vocab_size=total_vocab_size,
        use_parallel=True,
        verbose=True,
    )

    # Speichern der Finalen Ergebnisse.
    if not results_df.empty:
        out_dir = BASE_DIR / "Data" / "ergebnisse"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Ranking nach kneepoint.
        df_knee = results_df.sort_values(
            by=["Plateau_Member", "Chord_Distance", "Anzahl_Slots", "Total_Resets"],
            ascending=[False, False, True, True]
        )
        df_knee.to_csv(out_dir / "kneepoint.csv", index=False)

        # Ranking nach Privatsphäre.
        df_priv = results_df.sort_values(
            by=["Privacy_Score_Avg_Rotation", "Anzahl_Slots", "Total_Resets"],
            ascending=[False, True, True]
        )
        df_priv.to_csv(out_dir / "privacy.csv", index=False)
        print("Sweep erfolgreich beendet.")