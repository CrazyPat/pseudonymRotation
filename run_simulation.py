import pandas as pd
import concurrent.futures
import itertools
import json
from pathlib import Path
from Funktionen.config import PipelineConfig
from Funktionen.pseudonym.simulation import UserSimulation
from Funktionen.utils import log_status
from datetime import datetime
from Funktionen.reason_analysis import reason_analysis, summarize_segments
from verkettung import linkage_metrics

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

def main(use_parallel: bool = True, verbose: bool = True, save_events: bool = True, save_segments: bool = True, direct_analysis: bool = False, keep_raw=None):
    if not (save_events or save_segments or direct_analysis):
        print("Nichts zu tun: save_events, save_segments oder direct_analysis muss True sein.")
        return
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
    
    # Alle 535 simulierten Parameterkombinationen.
    # Jeder Eintrag ist ein Block aus vier Listen in der Reihenfolge:
    # ([Slots], [Max_Domains], [Max_Events], [Max_Days])
    # Aus jedem Block wird jede Kombination der vier Listen simuliert.
    # Auch ein einzelner Wert muss in eckigen Klammern stehen.
    #
    # Beispiele:
    #   ([100], [10], [700], [7])          -> 1 Kombination, die Referenz
    #   ([25, 50], [3], [100], [7, 14])    -> 2 x 1 x 1 x 2 = 4 Kombinationen:
    #                                         (25, 3, 100, 7), (25, 3, 100, 14),
    #                                         (50, 3, 100, 7), (50, 3, 100, 14)
    sweep_blocks = [
        ([25, 50, 100], [3, 5], [25, 100, 250], [7]),
        ([25, 50, 100], [3, 5], [25], [14]),
        ([10, 50], [10], [700], [7, 14]),
        ([5], [3], [200, 500, 600, 700], [7, 14]),
        ([225], [30], [700], [7, 14]),
        ([200, 225, 250], [3, 10, 15], [700, 1000], [7]),
        ([100, 400], [10], [700, 1000], [7]),
        ([225], [10], [100, 250], [7, 14]),
        (list(range(200, 251, 5)), [10],
         [500, 600, 700, 800, 900, 1000], [14]),
        ([400, 600], [10],
         [500, 700, 1000, 1250, 1500, 1750, 2000], [14]),
        ([100], [10], [700, 1000, 1250, 1500, 1750, 2000], [14]),
        ([225], [10], [1250, 1500, 1750, 2000], [14]),
        ([200, 250], [3, 15], [700, 1000], [14]),
        ([225], [15], [700, 1000], [14]),
        ([225, 400, 600], [3, 20],
         [500, 700, 1000, 2000], [14]),
        ([100], [3], [700, 1000, 2000], [14]),
        ([100], [20], [500, 700, 1000, 2000], [14]),
        ([100, 225, 400], [10], [700, 1000], [21, 31]),
        ([3, 5, 10, 15, 25], [2, 3, 5, 7, 10], [25, 50], [31]),
        ([3, 5, 15, 25], [2, 3, 5, 7, 10], [100, 250, 500], [31]),
        ([10, 50], [2, 3, 5, 7, 10, 15, 20, 30, 50],
         [100, 250, 500, 750, 1000], [31]),
        ([100], [2, 3, 5, 7], [100, 250, 500, 750, 1000], [31]),
        ([100], [10], [100, 250, 500, 750], [31]),
        ([225], [5, 7], [700], [14]),
        ([25, 150], [10], [700], [14]),
        ([100], [5, 7, 15], [700], [14]),
        ([15, 35, 75], [10], [700], [14]),
        ([25, 50, 100], [3, 5, 7, 10], [100, 250, 500], [14, 21]),
        ([25, 50, 75], [10], [700], [21]),
        ([15, 25, 35, 75, 150, 600], [10], [700], [7]),
        ([100], [10], [100, 250, 500, 1250, 1500, 2000], [7]),
        ([100], [3, 5, 7, 15, 20], [700], [7]),
        ([150], [30], [250, 500], [31]),]

    param_combinations = []

    for slot_configs, domain_configs, event_configs, day_configs in sweep_blocks:
        param_combinations.extend(itertools.product(slot_configs, domain_configs, event_configs, day_configs,))

    total_combinations = len(param_combinations)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starte Grid Search mit {total_combinations} Kombinationen.\n")

    # Rohdaten der Referenz-Slotreihe werden immer gespeichert (sofern sie in sweep_blocks stehen), da das Notebook sie für Zeitverlauf, Domainverteilung, Kaltstart und Surfmenge braucht.
    if keep_raw is None:
        keep_raw = [(s, 10, 700, 7) for s in [10, 25, 50, 100, 225, 600]]

    # Bei direct_analysis werden Verkettung und Abschlussgründe direkt in die *_direkt.csv geschrieben, um Speicher zu sparen.
    linkage_path = Path("Data/ergebnisse/verkettungs_ranking_direkt.csv")
    trigger_path = Path("Data/ergebnisse/sweep_trigger_analyse_direkt.csv")
    linkage_rows = pd.read_csv(linkage_path).to_dict("records") if direct_analysis and linkage_path.exists() else []
    trigger_rows = pd.read_csv(trigger_path).to_dict("records") if direct_analysis and trigger_path.exists() else []
    linkage_done = {(r["Anzahl_Slots"], r["Max_Domains"], r["Max_Events"], r["Max_Days"]) for r in linkage_rows}
    trigger_done = {(r["Slots"], r["Max_Domains"], r["Max_Events"], r["Max_Days"]) for r in trigger_rows}

    for idx, (slots, domains, events, days) in enumerate(param_combinations, 1):
        file_prefix = f"{slots}_{domains}_{events}_{days}"
        events_out_path = out_dir / f"{file_prefix}_events.csv"
        segments_out_path = out_dir / f"{file_prefix}_segments.csv"

        # Berechnete Segmente überspringen
        key = (slots, domains, events, days)
        write_events = save_events or key in keep_raw
        write_segments = save_segments or key in keep_raw
        needed_files = []
        if write_events:
            needed_files.append(events_out_path)
        if write_segments:
            needed_files.append(segments_out_path)
        files_done = all(p.exists() for p in needed_files)
        direct_done = not direct_analysis or (key in linkage_done and key in trigger_done)
        if (needed_files or direct_analysis) and files_done and direct_done:
            print(f"[{idx}/{total_combinations}] Überspringe {file_prefix} Dateien existieren bereits.")
            continue

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [{idx}/{total_combinations}] Simuliere: Slots={slots}, Domains={domains}, Events={events}, Days={days}")
        
        cfg = PipelineConfig(num_slots=slots, max_domains=domains, max_events=events, max_days=days)
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
                    # events nur sammeln, wenn sie auch gespeichert werden
                    if write_events:
                        all_annotated_rows.append(annotated_df)
                    all_segment_records.extend(segment_records)
        else:
            for chunk in user_chunks:
                annotated_df, segment_records = simulate_user_chunk(chunk)
                if write_events:
                    all_annotated_rows.append(annotated_df)
                all_segment_records.extend(segment_records)

        # Events nur speichern, wenn gewünscht oder Referenz-Slotreihe
        if write_events:
            final_df = pd.concat(all_annotated_rows, ignore_index=True)
            final_df.to_csv(events_out_path, index=False)

        segments_df = pd.DataFrame(all_segment_records)
        if write_segments:
            segments_df.to_csv(segments_out_path, index=False)
        # Direkte auswertung
        if direct_analysis and not segments_df.empty:
            if key not in trigger_done:
                trigger_rows.append(summarize_segments(segments_df, slots, domains, events, days))
                pd.DataFrame(trigger_rows).to_csv(trigger_path, index=False)
                trigger_done.add(key)

            if key not in linkage_done:
                seg_df = segments_df.copy()
                seg_df["domain_counter"] = seg_df["domain_counter_json"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                seg_df = seg_df[seg_df["domain_counter"].astype(bool)].reset_index(drop=True)
                row = {"Anzahl_Slots": slots, "Max_Domains": domains, "Max_Events": events, "Max_Days": days}
                if len(seg_df) >= 2:
                    m_incl = linkage_metrics(seg_df)
                    m_excl = linkage_metrics(seg_df[seg_df["trigger"] != "end_of_stream"])
                    if m_incl: row.update({f"Incl_{k}": v for k, v in m_incl.items()})
                    if m_excl: row.update({f"Excl_{k}": v for k, v in m_excl.items()})
                linkage_rows.append(row)
                pd.DataFrame(linkage_rows).to_csv(linkage_path, index=False)
                linkage_done.add(key)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gespeichert: {file_prefix}")

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sweep vollständig abgeschlossen.")
    if save_segments:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starte Abschlussgrund-Analyse...")
        reason_analysis(sweep_dir=out_dir, output_file="Data/ergebnisse/sweep_trigger_analyse.csv")

if __name__ == "__main__":
    # Schalter für den Durchlauf:
    # save_events     -> speichert alle Events pro Kombination (sehr groß)
    # save_segments   -> speichert alle Segmente pro Kombination (für verkettung.py und reason_analysis)
    # direct_analysis -> berechnet Verkettung und Abschlussgründe direkt im Speicher, Ergebnisse landen in *_direkt.csv
    # keep_raw        -> Kombinationen, deren Rohdaten immer gespeichert werden (für die Auswertung!)
    
    # Alles speichern (ALLE Log-Dateien), danach separat verkettung.py ausführen:
    #   save_events=True,  save_segments=True,  direct_analysis=False
    # Wenig Speicherverbrauch, nur die Rohdaten der Referenz-Slotreihe werden gespeichert:
    #   save_events=False, save_segments=False, direct_analysis=True
    # Segmente behalten und gleichzeitig direkt auswerten:
    #   save_events=False, save_segments=True,  direct_analysis=True
    
    # Bricht der Lauf ab, werden fertige Kombinationen beim Neustart übersprungen. :)
    main(use_parallel=True, verbose=True, save_events=False, save_segments=True, direct_analysis=False)
