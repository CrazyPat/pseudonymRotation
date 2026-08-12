import json
import os
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from Funktionen.data.load_dataset import browsing_data
from Funktionen.data.load_whotracksme import whotracksme_data
from Funktionen.data.dataset_check import dataset_check


def load_wtm_data(sites_path: str, trackers_path: str) -> Dict[str, List[str]]:
    """Lädt die WhoTracks.Me csvs und erstellt ein Mapping von Domains zu Trackern."""
    # Prüfen ob WTM-Dateien existieren
    if not os.path.exists(sites_path) or not os.path.exists(trackers_path):
        raise FileNotFoundError("WhoTracks.Me Dateien nicht gefunden.")
    
    # Relationstabelle laden
    st_df = pd.read_csv(sites_path, usecols=["site", "tracker"])
    # Site Spalte normalisieren
    st_df["site"] = st_df["site"].astype(str).str.lower().str.strip()
    # Tracker Spalte normalisieren
    st_df["tracker"] = st_df["tracker"].astype(str).str.strip()

    # Metadatentabelle laden
    t_df = pd.read_csv(trackers_path, usecols=["tracker", "category"])
    # Tracker normalisieren
    t_df["tracker"] = t_df["tracker"].astype(str).str.strip()
    # Kategorie normalisieren
    t_df["category"] = t_df["category"].astype(str).str.strip()
    # Duplikate entfernen
    t_df = t_df.drop_duplicates(subset=["tracker"], keep="last")
    # Alle Dienste die Ausgeschlossen werden, weil sie nicht relevant sind (v)
    ausgeschlossene_kategorien = {"cdn", "hosting", "customer_interaction", "audio_video_player", "extensions"}

    # Tabellen per Left-Join verknüpfen
    merged = pd.merge(st_df, t_df, on="tracker", how="left")
    merged = merged[~merged["category"].isin(ausgeschlossene_kategorien)]

    # Mapping-Dictionary vorbereiten
    mapping = {}
    # Nach Site gruppieren
    for site, group in merged.groupby("site"):
        # Eindeutige Tracker filtern
        trackers = sorted(list(set(t for t in group["tracker"] if pd.notna(t))))
        # Werte ins Mapping schreiben
        mapping[site] = trackers
        
    return mapping


def run_pipeline(input_file: str, wtm_sites: str, wtm_trackers: str, clean_csv: str, json_path: str, report_path: str, drop_unmapped: bool = False) -> None:
    """Führt die gesamte Pipeline aus: Laden der Daten, Mapping, Bereinigung und Evaluierung."""
    # Datensätze prüfen und automatisch herunterladen/bereitstellen
    browsing_data()
    whotracksme_data()

    # Browsing-Daten einlesen
    df = pd.read_csv(input_file)

    # Datenbereinigung.
    df["used_at"] = pd.to_datetime(df["used_at"], errors="coerce")
    df = df.dropna(subset=["panelist_id", "domain", "used_at"])
    df = df.sort_values(["panelist_id", "used_at"]).reset_index(drop=True)
    
    # WTM-Mapping generieren
    wtm_map = load_wtm_data(wtm_sites, wtm_trackers)
    
    # Domains normalisieren
    domains = df["domain"].astype(str).str.lower().str.strip()
    df["domain"] = domains
    
    # Tracker mappen
    df["trackers"] = domains.map(lambda d: wtm_map.get(d, []))
    
    # Tracker-Anzahl bestimmen
    df["tracker_count"] = df["trackers"].apply(len)

    # Unmapped filtern falls aktiv
    if drop_unmapped:
        df = df[df["tracker_count"] > 0].copy()

    # Ausgabeverzeichnisse erstellen
    for p in [clean_csv, json_path, report_path]:
        Path(p).parent.mkdir(parents=True, exist_ok=True)

    # Bereinigte CSV speichern mit nur benötigten Spalten
    df[["panelist_id", "domain", "used_at"]].to_csv(clean_csv, index=False, encoding="utf-8")

    # JSON-Mapping speichern
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dict(zip(df["domain"], df["trackers"])), f, indent=2, ensure_ascii=False)

    dataset_check(df, dict(zip(df["domain"], df["trackers"])), report_path)

# main
if __name__ == "__main__":
    run_pipeline(
        input_file="Data/datensatz/browsing.csv",
        wtm_sites="Data/datensatz/whotracksme/sites_trackers.csv",
        wtm_trackers="Data/datensatz/whotracksme/trackers.csv",
        clean_csv="Data/datensatz/browsing_clean.csv",
        json_path="Data/datensatz/domain_tracker_mapping.json",
        report_path="Data/datensatz/dataset_check.json",
        drop_unmapped=False
    )