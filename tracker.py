import json
import os
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from Funktionen.data.load_dataset import browsing_data
from Funktionen.data.load_whotracksme import whotracksme_data


def load_wtm_data(sites_path: str, trackers_path: str) -> Dict[str, Dict[str, List[str]]]:
    """Lädt die WhoTracks.Me csvs und erstellt ein Mapping von Domains zu Trackern, Kategorien und Unternehmen."""
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
    t_df = pd.read_csv(trackers_path, usecols=["tracker", "category", "company_id"])
    # Tracker normalisieren
    t_df["tracker"] = t_df["tracker"].astype(str).str.strip()
    # Kategorie normalisieren
    t_df["category"] = t_df["category"].astype(str).str.strip()
    # Company normalisieren
    t_df["company_id"] = t_df["company_id"].astype(str).str.strip()
    # Duplikate entfernen
    t_df = t_df.drop_duplicates(subset=["tracker"], keep="last")

    # Tabellen per Left-Join verknüpfen
    merged = pd.merge(st_df, t_df, on="tracker", how="left")

    # Mapping-Dictionary vorbereiten
    mapping = {}
    # Nach Site gruppieren
    for site, group in merged.groupby("site"):
        # Eindeutige Tracker filtern
        trackers = sorted(list(set(t for t in group["tracker"] if pd.notna(t))))
        # Eindeutige Kategorien filtern
        categories = sorted(list(set(c for c in group["category"] if pd.notna(c) and c != "nan")))
        # Eindeutige Companies filtern
        companies = sorted(list(set(comp for comp in group["company_id"] if pd.notna(comp) and comp != "nan")))
        # Werte ins Mapping schreiben
        mapping[site] = {"trackers": trackers, "categories": categories, "companies": companies}
        
    return mapping

def calc_stats(counts: np.ndarray) -> Dict[str, float]:
    # Leere Arrays abfangen
    if len(counts) == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "q25": 0.0, "median": 0.0, "q75": 0.0, "iqr": 0.0, "max": 0.0}
    
    # Quartile berechnen
    q25, median, q75 = np.percentile(counts, [25, 50, 75])
    
    # Statistik-Dictionary zurückgeben
    return {
        "mean": round(float(np.mean(counts)), 4),
        "std": round(float(np.std(counts, ddof=1)) if len(counts) > 1 else 0.0, 4),
        "min": round(float(np.min(counts)), 4),
        "q25": round(float(q25), 4),
        "median": round(float(median), 4),
        "q75": round(float(q75), 4),
        "iqr": round(float(q75 - q25), 4),
        "max": round(float(np.max(counts)), 4)
    }

def evaluate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    # Zähler als Array extrahieren
    counts = df["tracker_count"].to_numpy()
    total = len(counts)
    
    # Maske für getrackte Domains
    mask = counts > 0
    mapped = counts[mask]
    
    # Anzahl getrackter Domains
    n_mapped = int(np.sum(mask))
    # Anzahl ungetrackter Domains
    n_unmapped = int(total - n_mapped)
    
    # Prävalenz berechnen
    prevalence = (n_mapped / total) if total > 0 else 0.0
    
    # Report-Struktur bauen
    return {
        "sample_overview": {
            "total_domains_analyzed": int(total),
            "tracked_domains_count": n_mapped,
            "untracked_domains_count": n_unmapped,
            "tracking_prevalence_ratio": round(float(prevalence), 4),
            "tracking_prevalence_percentage": f"{round(prevalence * 100, 2)}%"
        },
        "intensity_all_domains": {
            "description": "Gesamtverteilung inkl. unmapped (0 Tracker)",
            "metrics": calc_stats(counts)
        },
        "intensity_tracked_only": {
            "description": "Bedingte Verteilung nur getrackte Domains (> 0)",
            "metrics": calc_stats(mapped)
        }
    }

def run_pipeline(input_file: str, wtm_sites: str, wtm_trackers: str, clean_csv: str, json_path: str, report_path: str, drop_unmapped: bool = False) -> None:
    """Führt die gesamte Pipeline aus: Laden der Daten, Mapping, Bereinigung und Evaluierung."""
    # Datensätze prüfen und ggf. automatisch herunterladen/bereitstellen
    browsing_data()
    whotracksme_data()

    # Browsing-Daten einlesen
    df = pd.read_csv(input_file)
    
    # WTM-Mapping generieren
    wtm_map = load_wtm_data(wtm_sites, wtm_trackers)
    
    # Domains normalisieren
    domains = df["domain"].astype(str).str.lower().str.strip()
    
    # Tracker mappen
    df["trackers"] = domains.map(lambda d: wtm_map.get(d, {}).get("trackers", []))
    # Kategorien mappen
    df["categories"] = domains.map(lambda d: wtm_map.get(d, {}).get("categories", []))
    # Companies mappen
    df["companies"] = domains.map(lambda d: wtm_map.get(d, {}).get("companies", []))
    
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

    # Event-Level Report generieren
    event_report = evaluate_metrics(df)
    
    # Metadaten für Event-Level hinzufügen
    event_report["metadata"] = {
        # Eingabedatei übergeben
        "input_file": input_file,
        # Drop-Parameter speichern
        "drop_unmapped_applied": drop_unmapped,
        # Level auf event setzen
        "level": "event",
        # Beschreibung hinzufügen
        "description": "Gewichtet nach tatsächlicher Aufrufhäufigkeit"
    }
    
    # Dateipfad für Event-Report anpassen
    event_report_path = report_path.replace(".json", "_event_level.json")
    
    # Event-Report als JSON speichern
    with open(event_report_path, "w", encoding="utf-8") as f:
        json.dump(event_report, f, indent=2, ensure_ascii=False)

    # DataFrame auf eindeutige Domains reduzieren für Domain-Level
    df_domain_level = df[["domain", "tracker_count"]].drop_duplicates(subset=["domain"])
    
    # Domain-Level Report generieren
    domain_report = evaluate_metrics(df_domain_level)
    
    # Metadaten für Domain-Level hinzufügen
    domain_report["metadata"] = {
        # Eingabedatei übergeben
        "input_file": input_file,
        # Drop-Parameter speichern
        "drop_unmapped_applied": drop_unmapped,
        # Level auf domain setzen
        "level": "domain",
        # Beschreibung hinzufügen
        "description": "Ungewichtet auf Basis eindeutiger Domains"
    }
    # Dateipfad für Domain-Report anpassen
    domain_report_path = report_path.replace(".json", "_domain_level.json") 
    # Domain-Report als JSON speichern
    with open(domain_report_path, "w", encoding="utf-8") as f:
        json.dump(domain_report, f, indent=2, ensure_ascii=False)

# main
if __name__ == "__main__":
    run_pipeline(
        input_file="Data/datensatz/browsing.csv",
        wtm_sites="Data/datensatz/whotracksme/sites_trackers.csv",
        wtm_trackers="Data/datensatz/whotracksme/trackers.csv",
        clean_csv="Data/datensatz/browsing_clean.csv",
        json_path="Data/datensatz/domain_tracker_mapping.json",
        report_path="Data/datensatz/trackerset_report.json",
        drop_unmapped=False
    )