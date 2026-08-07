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

    all_unique_trackers = set()
    for trackers in tracker_mapping.values():
        all_unique_trackers.update(trackers)
    total_vocab_size = len(all_unique_trackers)

    slot_configs = [5, 10, 15, 20, 25, 35, 40, 45, 50, 55, 60, 65]
    domain_configs = [5, 10, 15, 20, 30, 45, 50, 55, 60, 75, 90, 105, 125, 140, 200]
    event_configs = [50, 100, 200, 450, 700, 800]
    k_values = [1, 3, 5, 10, 20]
    # slot_configs = [35, 40, 45, 50, 55, 60, 65]
    # domain_configs = [20, 30, 45, 50, 55, 60, 75, 90, 105, 125, 140, 200]
    # event_configs = [450, 700, 800]
    # k_values = [1, 3, 5, 10, 20]
    # slot_configs = [35]
    # domain_configs = [20]
    # event_configs = [450]
    # k_values = [1, 3, 5, 10, 20]

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
            by=["Privacy_Score_Avg", "Anzahl_Slots", "Total_Resets"],
            ascending=[False, True, True]
        )
        df_priv.to_csv(out_dir / "privacy.csv", index=False)
        print("Sweep erfolgreich beendet.")