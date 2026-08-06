"""
Führt den vollständigen Parameter-Sweep über alle Konfigurationen aus
"""

import itertools
import os

import pandas as pd

from ..config import PipelineConfig
from ..utils import log_status
from .evaluation import evaluate_configuration
from .scoring import add_scores
from .vocabulary import build_baseline_matrix, build_domain_vocabulary


def run_sweep(
    df_raw: pd.DataFrame, tracker_mapping: dict,
    slot_configs: list, domain_configs: list, event_configs: list,
    num_eval_users: int = 2148, vocab_size: int = 500,
    use_parallel: bool = True, verbose: bool = False,
    k_values: list = [1, 3, 5, 10],
    checkpoint_file: str = "sweep_checkpoint.csv",
):

    # Bereinigt die Rohdaten und sortiert sie nach Nutzer und Zeit.
    df_clean = df_raw.copy()
    df_clean["used_at"] = pd.to_datetime(df_clean["used_at"], errors="coerce")
    df_clean = df_clean.dropna(subset=["used_at", "domain", "panelist_id"])
    df_clean = df_clean.sort_values(["panelist_id", "used_at"]).reset_index(drop=True)
    # Baut die Vokabular.
    domain_to_idx = build_domain_vocabulary(df_clean, tracker_mapping, vocab_size)
    # Baut Baseline-Matrix und Nutzerliste.
    baseline_matrix, user_list = build_baseline_matrix(df_clean, tracker_mapping, domain_to_idx)
    # Wählt nur die Top-Nutzer für die Evaluation basierend auf der Anzahl ihrer Events. Es wird aber ein Vollständiger durchlauf Simuliert (Also alle Nutzer werden genutzt)
    top_users = df_clean["panelist_id"].value_counts().head(num_eval_users).index
    df_eval = df_clean[df_clean["panelist_id"].isin(top_users)].copy()
    # Läd alle configs.
    configs = list(itertools.product(slot_configs, domain_configs, event_configs))
    # Berechnet alle configs für Fortschrittsanzeige.
    total_configs = len(configs)

    # Fertige configs
    completed_configs = set()
    # checkpoint file prüfen
    if os.path.exists(checkpoint_file):
        try:
            #Checkpoint file laden.
            df_checkpoint = pd.read_csv(checkpoint_file)
            # Geht durch alle configs.
            for _, row in df_checkpoint.iterrows():
                # Speichert fertige im Set, falls diese schon durchgelaufen sind.
                completed_configs.add((int(row["Anzahl_Slots"]), int(row["Max_Domains"]), int(row["Max_Events"])))
            # Fortschrittsanzeige.
            if verbose:
                log_status(f"Checkpoint: {len(completed_configs)}", True)
        except Exception as e:
            # Falls Fehler bei laden entstehen.
            if verbose:
                log_status(f"Fehler beim Laden des Checkpoints: {e}", True)

    # Start des Sweeps. Durchläuft alle configs. Damit slots, domains und events.
    for config_index, (s, d, e) in enumerate(configs, start=1):
        # Kontrolliert ob configs schon fertig sind --> Überspringt falls ja.
        if (s, d, e) in completed_configs:
            # Alle fertigen. Fortschrittsanzeige.
            if verbose:
                log_status(f"Überspringe {config_index}/{total_configs} (Slots={s}, Dom={d}, Ev={e})", True)
            continue
        # Erstellt pipeline für die config.
        cfg = PipelineConfig(num_slots=s, max_domains=d, max_events=e)
        # Kontrolle wie weit die config durchgelaufen ist.
        if verbose:
            log_status(f"Starte Konfiguration {config_index}/{total_configs} (Slots={s}, Dom={d}, Ev={e})...", True)
        # Evaluierung der config mit parametern. --> dict mit allen Werten (kNN-Accuracy, Cosine Similarity usw).
        res = evaluate_configuration(
            df_eval, cfg, baseline_matrix, user_list, domain_to_idx, tracker_mapping,
            k_values=k_values, 
            use_parallel=use_parallel, verbose=verbose
        )
        # Inhaltsprüfung der Ergebnisse
        if res:
            # Dict in Liste und dann in pd DF.
            res_df = pd.DataFrame([res])
            # Checker ob file exisitert.
            write_header = not os.path.exists(checkpoint_file)
            # Erzeugt oder hängt die Ergebnisse an die Datei an.
            res_df.to_csv(checkpoint_file, mode='a', header=write_header, index=False)

    # Ende des Sweeps. Exisitert chepoint file?
    if os.path.exists(checkpoint_file):
        # Löd die file
        final_df = pd.read_csv(checkpoint_file)
        # Fügt Scores hinzu.
        scored = add_scores(final_df)
        # Gibt diese zurück.
        return scored
    else:
        return pd.DataFrame()
