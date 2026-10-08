"""Prüft, wie stark die Angriffsraten allein durch die zufällige Slot-Zuweisung schwanken.
Läuft nach dem gleichen Prinzip wie run_simulation, nur mit verschiedenen Seeds für die Zuweisung.
Die Verkettung wird direkt nach jedem Lauf berechnet, die Segmente werden nur mit save_segments=True gespeichert.
"""

import pandas as pd
import concurrent.futures
import itertools
import json
from pathlib import Path
from datetime import datetime
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from verkettung import linkage_metrics

def simulate_user_chunk(chunk_args):
    user_id, user_df, cfg, run_seed, observation_end = chunk_args
    sim = UserSimulation(user_id=user_id, cfg=cfg, run_seed=run_seed)
    sim.run_user(user_df, observation_end)
    return sim.segment_records

def linkage_row(segments, slots, domains, events, days, run_seed):
    """Berechnet INCL und EXCL für einen Lauf."""
    df = pd.DataFrame(segments)
    if df.empty:
        return None
    df["domain_counter"] = df["domain_counter_json"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    df = df[df["domain_counter"].astype(bool)].reset_index(drop=True)
    if len(df) < 2:
        return None

    m_incl = linkage_metrics(df)
    m_excl = linkage_metrics(df[df["trigger"] != "end_of_stream"])

    row = {"Anzahl_Slots": slots, "Max_Domains": domains, "Max_Events": events,
           "Max_Days": days, "Run_Seed": run_seed}
    if m_incl: row.update({f"Incl_{k}": v for k, v in m_incl.items()})
    if m_excl: row.update({f"Excl_{k}": v for k, v in m_excl.items()})
    row["INCL (%)"] = row["Incl_Identification_Rate"] * 100
    row["EXCL (%)"] = row["Excl_Identification_Rate"] * 100
    return row

def main(use_parallel: bool = True, save_segments: bool = False):
    # paths für usersim
    data_path = Path("Data/datensatz/browsing_clean.csv")
    out_dir = Path("Data/ergebnisse/variance_check")
    ranking_path = Path("Data/ergebnisse/variance_check_ranking.csv")
    summary_path = Path("Data/ergebnisse/variance_check_summary.csv")
    if save_segments:
        out_dir.mkdir(parents=True, exist_ok=True)
    # einlesen
    df = pd.read_csv(data_path)
    # zeitstempel konvertieren
    df["used_at"] = pd.to_datetime(df["used_at"])
    df = df.sort_values(by=["panelist_id", "used_at"])
    # Ende des Beobachtungszeitraums, gleich wie in run_simulation
    observation_end = df["used_at"].max()
    grouped_users = list(df.groupby("panelist_id", sort=False))
    
    # grid sweep um die Referenz
    # Jeder Block besteht aus ([Slots], [Max_Domains], [Max_Events], [Max_Days]) und wird mit allen Seeds simuliert
    sweep_blocks = [
        ([25, 50, 75, 100, 150, 225], [10], [700], [7]),
        ([100], [10], [500, 1000, 1250, 1500, 2000], [7]),
        ([100], [15, 20], [700], [7]),
    ]
    # wie oft variiert werden soll
    run_seeds = list(range(20))
    # wird hier durchgezählt
    combos = [c for block in sweep_blocks for c in itertools.product(*block, run_seeds)]

    # bereits fertige läufe aus der csv lesen, damit nach einem abbruch weitergemacht werden kann
    rows = pd.read_csv(ranking_path).to_dict("records") if ranking_path.exists() else []
    done = {(r["Anzahl_Slots"], r["Max_Domains"], r["Max_Events"], r["Max_Days"], r["Run_Seed"]) for r in rows}
    
    for idx, (slots, domains, events, days, run_seed) in enumerate(combos, 1):
        file_prefix = f"{slots}_{domains}_{events}_{days}_seed{run_seed}"
        segments_out_path = out_dir / f"{file_prefix}_segments.csv"
        key = (slots, domains, events, days, run_seed)
        if key in done and (not save_segments or segments_out_path.exists()):
            print(f"[{idx}/{len(combos)}] Überspringe {file_prefix}")
            continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{idx}/{len(combos)}] {file_prefix}")
        cfg = PipelineConfig(num_slots=slots, max_domains=domains, max_events=events, max_days=days, use_tracker_mapping=False)
        chunks = [(uid, user_df, cfg, run_seed, observation_end) for uid, user_df in grouped_users]

        all_segments = []
        if use_parallel:
            with concurrent.futures.ProcessPoolExecutor(max_workers=7) as executor:
                futures = [executor.submit(simulate_user_chunk, c) for c in chunks]
                for future in concurrent.futures.as_completed(futures):
                    all_segments.extend(future.result())
        else:
            for c in chunks:
                all_segments.extend(simulate_user_chunk(c))

        if save_segments:
            pd.DataFrame(all_segments).to_csv(segments_out_path, index=False)

        # verkettung direkt berechnen und nach jedem lauf in die csv schreiben
        if key not in done:
            row = linkage_row(all_segments, slots, domains, events, days, run_seed)
            if row:
                rows.append(row)
                done.add(key)
                pd.DataFrame(rows).to_csv(ranking_path, index=False)

    # zusammenfassung pro slotanzahl
    df_all = pd.DataFrame(rows)
    summary = df_all.groupby(["Anzahl_Slots", "Max_Domains", "Max_Events", "Max_Days"]).agg(
        INCL_mean=("INCL (%)", "mean"), INCL_std=("INCL (%)", "std"),
        EXCL_mean=("EXCL (%)", "mean"), EXCL_std=("EXCL (%)", "std"),
        n_seeds=("Run_Seed", "count"),
    ).reset_index().sort_values("Anzahl_Slots")

    print(summary.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    summary.to_csv(summary_path, index=False)

if __name__ == "__main__":
    # save_segments=True speichert zusätzlich die Segmente jedes Laufs in Data/ergebnisse/variance_check (ca. 50 MB pro Lauf)
    main(use_parallel=True, save_segments=False)