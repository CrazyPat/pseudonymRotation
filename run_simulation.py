import pandas as pd
from pathlib import Path
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from Funktionen.utils import log_status

def main(verbose = True):
    # Datensatz load
    data_path = Path("Data/datensatz/browsing_clean.csv")
    df = pd.read_csv(data_path)
    # Timestamps einlesen + sorty values
    df["used_at"] = pd.to_datetime(df["used_at"])
    df = df.sort_values(by=["panelist_id", "used_at"])

    cfg = PipelineConfig(num_slots=10, max_domains=10, max_events=100, max_days=7)
    
    all_annotated_rows = []
    user_groups = list(df.groupby("panelist_id"))
    total_users = len(user_groups)
    
    for user_index, (user_id, user_df) in enumerate(user_groups, start=1):
        sim = UserSimulation(user_id=user_id, cfg=cfg)
        annotated_df = sim.run_user(user_df)
        all_annotated_rows.append(annotated_df)
        if verbose:
            progress_pct = (user_index / total_users) * 100
            log_status(
                f"Fortschritt: {progress_pct:.1f}% | User {user_index}/{total_users} fertig ({user_id}) | "
                f"Segmente={len(sim.segment_records)} | Resets={sim.total_resets()}",
                True,
            )
    final_df = pd.concat(all_annotated_rows, ignore_index=True)
    
    out_path = Path("Data/ergebnisse/simulation_output.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(out_path, index=False)
if __name__ == "__main__":
    main(verbose = True)