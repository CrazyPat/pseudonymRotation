from pathlib import Path
import pandas as pd
from Funktionen.data.load_dataset import browsing_data

def run_pipeline(input_file: str, clean_csv: str) -> None:
    """Führt die gesamte Pipeline aus: Laden der Daten und Bereinigung."""
    # Datensätze prüfen und automatisch herunterladen/bereitstellen
    browsing_data()

    # Browsing-Daten einlesen
    df = pd.read_csv(input_file)

    # Datenbereinigung.
    df["used_at"] = pd.to_datetime(df["used_at"], errors="coerce")
    df = df.dropna(subset=["panelist_id", "domain", "used_at"])
    df = df.sort_values(["panelist_id", "used_at"]).reset_index(drop=True)
    
    # Domains normalisieren
    df["domain"] = df["domain"].astype(str).str.lower().str.strip()
    
    # Ausgabeverzeichnis erstellen
    Path(clean_csv).parent.mkdir(parents=True, exist_ok=True)

    # Bereinigte CSV speichern mit nur benötigten Spalten
    df[["panelist_id", "domain", "used_at"]].to_csv(clean_csv, index=False, encoding="utf-8")
    print(f"Daten erfolgreich bereinigt und gespeichert unter: {clean_csv}")

# main
if __name__ == "__main__":
    run_pipeline(
        input_file="Data/datensatz/browsing.csv",
        clean_csv="Data/datensatz/browsing_clean.csv"
    )