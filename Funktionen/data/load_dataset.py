from pathlib import Path
import tarfile
import requests

def browsing_data() -> None:
    # Ausgabeverzeichnis absolut festlegen
    output_dir = Path(__file__).resolve().parents[2] / "Data" / "datensatz"
    # Zielpfad für browsing.csv definieren
    target_file = output_dir / "browsing.csv"
    # Prüfen ob Browsing-Datei bereits existiert
    if target_file.exists():
        return
    # Verzeichnis erstellen falls nicht vorhanden
    output_dir.mkdir(parents=True, exist_ok=True)
    # Download-URL für den Web-Tracking-Datensatz definieren
    url = "https://zenodo.org/records/4757574/files/web_tracking_data.tar.gz?download=1"
    # Pfad für das temporäre Archiv definieren
    tar_path = output_dir / "web_tracking_data.tar.gz"
    # Statusmeldung für den Download ausgeben
    print("Lade Datensatz von Zenodo herunter...")
    # HTTP-Get-Request mit Datenstrom starten
    response = requests.get(url, stream=True)
    # HTTP-Fehler prüfen und ggf. Exception werfen
    response.raise_for_status()
    # Archiv im Binärmodus zum Schreiben öffnen
    with open(tar_path, "wb") as f:
        # Daten in Chunks durchlaufen und speichern
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    # Statusmeldung für den Entpackvorgang ausgeben
    print("Entpacke Archiv und suche nach browsing.csv...")
    # Tar-Archiv zum Lesen öffnen
    with tarfile.open(tar_path, "r:gz") as tar:
        # Zieldatei im Archiv suchen
        target = next((m for m in tar.getmembers() if m.name.endswith("browsing.csv")), None)
        # Prüfen ob browsing.csv gefunden wurde
        if not target:
            raise FileNotFoundError("Die Datei 'browsing.csv' wurde im Archiv nicht gefunden.")
        # Dateinamen im Archiv anpassen
        target.name = "browsing.csv"
        # Datei in den Zielordner extrahieren
        tar.extract(target, path=output_dir)
        # Erfolgsmeldung mit Pfad ausgeben
        print(f"Erfolgreich gespeichert unter: {target_file}")
    # Temporäres Archiv von der Festplatte löschen
    tar_path.unlink()
    # Abschlussmeldung ausgeben
    print("Fertig.")