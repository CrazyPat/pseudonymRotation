import os
import json
import pandas as pd

# MONKEY PATCH
# Methode 'iteritems' fehlt?
if not hasattr(pd.Series, 'iteritems'):
    # 'iteritems' auf die neuere Methode 'items' setzen.
    pd.Series.iteritems = pd.Series.items
# Methode 'iteritems' fehlt?
if not hasattr(pd.DataFrame, 'iteritems'):
    # 'iteritems' auf 'items' im df setzen.
    pd.DataFrame.iteritems = pd.DataFrame.items

# WhoTracks.Me-Mappings als df laden.
def load_whotracksme_mapping() -> pd.DataFrame:
    """Lädt das Publisher-to-Tracker Mapping direkt aus dem whotracksme-Paket."""
    try:
        # Datenquelle.
        from whotracksme.data.loader import DataSource
        data = DataSource()
        mapping_rows = []
        
        # Webseiten auslesen ohne das es crashed falls tabelle nicht existiert.
        df_sites = getattr(data.sites, "df", None)
        # Existensprüfung.
        if df_sites is not None and len(df_sites) > 0:
            # Sucht Spalte für den Domain oder Seitennamen.
            d_col = next((c for c in df_sites.columns if "domain" in c.lower() or "site" in c.lower()), None)
            if d_col:
                # jede Zeile der Tabelle.
                for _, row in df_sites.iterrows():
                    # Leerzeichen entfernen und in Kleinbuchstaben.
                    domain = str(row.get(d_col, "")).strip().lower()
                    # Leere Einträge oder nan überspringen.
                    if not domain or domain == "nan":
                        continue
                    # Spaltennamen für Tracker.
                    for col in ["trackers", "top_trackers"]:
                        # Existenzprüfung.
                        if col in row and pd.notna(row[col]):
                            # Tracker-Spalte.
                            val = row[col]
                            # Liste oder Tuple
                            if isinstance(val, (list, tuple)):
                                for t in val:
                                    # Trackernamen aus dem String oder Dictionary.
                                    t_name = t if isinstance(t, str) else t.get("name") or t.get("tracker")
                                    if t_name:
                                        # Fügt Domain und Tracker zur Liste hinzu ohne Leerzeichen.
                                        mapping_rows.append({"domain": domain, "tracker": str(t_name).strip()})
                            # Prüfen ob einzelner Textstring
                            elif isinstance(val, str):
                                # Domain und einzelnem Tracker zur Liste hinzufügen ohne Leerzeichen.
                                mapping_rows.append({"domain": domain, "tracker": val.strip()})


        # Existieren Daten in der Liste?
        if mapping_rows:
            # Df und dduplication.
            df_mapping = pd.DataFrame(mapping_rows).drop_duplicates()
        # Falls keine Daten geladen sind.
        else:
            # Leere df mit korrekten Spaltennamen.
            df_mapping = pd.DataFrame(columns=["domain", "tracker"])
        return df_mapping

    # Fehlerbehandlung.
    except ImportError:
        raise ImportError("'whotracksme' ist nicht installiert.")


def run_full_pipeline(
    input_filepath: str = "Data/browsing.csv",
    output_clean_csv: str = "Data/browsing_clean.csv",
    output_json_path: str = "Data/domain_tracker_mapping.json",
    # Entfernt ungemappted Domains aus dem Datensatz!
    drop_unmapped: bool = True
):
    # Prüft, ob die angegebene Eingabedatei im Pfad existiert.
    if not os.path.exists(input_filepath):
        # Wirft einen Fehler, wenn die Datei nicht gefunden wird.
        raise FileNotFoundError(f"Eingabedatei nicht gefunden: {input_filepath}")

    print(f"Lese Rohdaten ein: {input_filepath}")
    # Alle Relevanten Spalten.
    usecols = ["panelist_id", "domain", "used_at"]
    # browsing.csv einlesen und nur relevante Spalten verwenden.
    df_zenodo = pd.read_csv(input_filepath, usecols=usecols, dtype={"panelist_id": str, "domain": str})
    # Bereinigung.
    df_zenodo["domain"] = df_zenodo["domain"].astype(str).str.strip().str.lower()
    # whoTracks.Me Mapping laden.
    df_mapping = load_whotracksme_mapping()
    # Leftjoin der beiden dfs.
    df_merged = pd.merge(df_zenodo, df_mapping, on="domain", how="left")

    # Maske zur Filterung der nicht zugeordnenten Tracker.
    missing_mask = df_merged["tracker"].isna()
    # Gemappte Einträge
    mapped_ratio = (1.0 - (missing_mask.sum() / len(df_merged))) * 100
    # Ausgabe
    print(f"Mapping: {mapped_ratio:.2f}% der Einträge gemappt.")

    # Ungemapptes Entfernen?
    if drop_unmapped:
        # Nur Trackerzeilen behalten.
        df_merged = df_merged[~missing_mask].copy()
    # nan entfernen, sollte aber eigentlich keine mehr geben.
    df_merged = df_merged.dropna(subset=["panelist_id", "used_at", "domain"])

    # Letzte Bereinigung der Daten.
    # Dduplication.
    df_clean = df_merged[["panelist_id", "domain", "used_at"]].drop_duplicates().copy()
    # Zeitstempel in pd.datetime.
    df_clean["used_at"] = pd.to_datetime(df_clean["used_at"], errors="coerce")
    # nan droppen.
    df_clean = df_clean.dropna(subset=["used_at", "domain", "panelist_id"])
    # Sortieren aufsteigend nach Nutzer-ID und Zeitstempel.
    df_clean = df_clean.sort_values(["panelist_id", "used_at"]).reset_index(drop=True)
    
    # Zielordner falls er nicht existiert erstellen.
    os.makedirs(os.path.dirname(output_clean_csv), exist_ok=True)
    # Speichern.
    df_clean.to_csv(output_clean_csv, index=False)

    # Json-Datei:
    tracker_mapping = (
        # Gruppieren nach Domain und Tracker-Spalte wählen.
        df_merged.groupby("domain")["tracker"]
        # Eindeutigen Tracker pro Domain.
        .unique()
        # nparray in Liste.
        .apply(list)
        # dict umwandeln.
        .to_dict()
    )

    # JSON-Datei öffnen.
    with open(output_json_path, "w", encoding="utf-8") as f:
        # Dict in die JSON schreiben.
        json.dump(tracker_mapping, f, indent=2, ensure_ascii=False)


# main
if __name__ == "__main__":
    run_full_pipeline(
        input_filepath="Data/browsing.csv",
        output_clean_csv="Data/browsing_clean.csv",
        output_json_path="Data/domain_tracker_mapping.json",
        drop_unmapped=True
    )