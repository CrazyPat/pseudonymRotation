from pathlib import Path
import pandas as pd
from whotracksme.data.loader import DataSource

def whotracksme_data() -> None:
    # Iteritems für Series patchen
    pd.Series.iteritems = getattr(pd.Series, 'iteritems', pd.Series.items)
    # Iteritems für DataFrame patchen
    pd.DataFrame.iteritems = getattr(pd.DataFrame, 'iteritems', pd.DataFrame.items)
    try:
        # DataSource initialisieren
        ds = DataSource()
    except Exception:
        # Fehler abfangen und abbrechen
        return
    # Ausgabeverzeichnis absolut festlegen
    output_dir = Path(__file__).resolve().parents[2] / "Data" / "datensatz" / "whotracksme"
    # Verzeichnis erstellen falls nicht vorhanden
    output_dir.mkdir(parents=True, exist_ok=True)
    # Schleife über benötigte Datasets
    for attr in ["sites_trackers", "trackers"]:
        # Wert aus DataSource abrufen
        val = getattr(ds, attr, None)
        # DataFrame aus .df oder direkt extrahieren
        df = getattr(val, "df", val) if val is not None else None
        # Prüfen ob DataFrame gültig und nicht leer ist
        if isinstance(df, pd.DataFrame) and not df.empty:
            # Dateipfad zusammensetzen
            file_path = output_dir / f"{attr}.csv"
            # Als CSV speichern
            df.to_csv(file_path, index=False)
            # Erfolgsmeldung ausgeben
            print(f"Exportiert: {attr} -> {file_path} (Zeilen: {len(df)}, Spalten: {list(df.columns)})")