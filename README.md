# Pseudonym-Rotation im Real-Time-Bidding

Inhalt ist die Python-Simulations- und Evaluationspipeline für die Bachelorarbeit.

---

## Projektstruktur

```text
├── Data/                        # Datensatz und generierte Mapping-Dateien
├── Funktionen/                  # Python-Paket der Simulationspipeline
│   ├── auswertung/              # Vokabular, Baseline-Matrix, k-NN-Evaluation und Scoring
│   ├── pseudonym/               # Lifecycle, HMAC-Zuweisung und Nutzersimulation
│   │   ├── __init__.py          # init
│   │   ├── evaluation.py        # Kosinus-Ähnlichkeit, k-NN-Accuracy und Utility-Berechnung
│   │   ├── scoring.py           # Min-Max-Normalisierung, Kniepunkt und Epsilon-Plateau
│   │   ├── sweep.py             # Parameter-Sweep
│   │   └── vocabulary.py        # Aufbau des Tracker-Vokabulars und der Baseline-Matrix
│   │   ├── __init__.py          # init
│   │   ├── lifecycle.py         # SlotState-Container und Lifecycle
│   │   ├── simulation.py        # UserSimulation
│   │   └── zuweisung.py         # SlotAssigner
│   ├── config.py                # Datencontainer
│   └── utils.py                 # Logging-Funktion
├── tracker.py                   # Vorverarbeitung des Datensatzes
├── run.py                       # Hauptskript
├── requirements.txt             # Projekt-Abhängigkeiten
└── README.md                    # Projektdokumentation
```

---

## Einrichtung

### Abhängigkeiten installieren
Installiere die benötigten Abhängigkeiten im Root-Verzeichnis des Projekts:

```bash
pip install -r requirements.txt
```

### Datensatz herunterladen
Als empirische Grundlage dient der Zenodo-Datensatz *„A web tracking data set of online browsing behavior of 2,148 users“*.

1. Lade den Datensatz von Zenodo herunter. 
LINK: https://zenodo.org/records/4757574/files/web_tracking_data.tar.gz?download=1
2. Navigiere zu `raw` und Platziere die Datei `browsing.csv` direkt in den Ordner `Data/`:
   ```text
   Data/browsing.csv
   ```

---

## Ausführung der Pipeline

### Vorverarbeitung der Daten und Erstellung des Tracker-Mappings
Bevor die Simulation startet, müssen die Clickstream-Daten bereinigt und über die *WhoTracks.Me*-Datenbank den jeweiligen Trackern zugeordnet werden. Dies ist notwendig, da der Datensatz keine Domain --> Tracker Zuordnung hat:

```bash
python tracker.py
```

*Dieser Schritt generiert automatisch die Dateien `Data/browsing_clean.csv` und `Data/domain_tracker_mapping.json`.* 


### Evaluation starten
Nun kann die Simulation gestartet werden:

```bash
python run.py
```

* Das Skript verarbeitet die Nutzer parallel über alle CPU-Kerne (`use_parallel=True`). Falls dies nicht passieren soll im run.py bitte auf False setzen.
* Der Fortschritt wird in `Data/sweep_checkpoint.csv` gespeichert um nach Fehlern oder einem Crash wieder erneut einsteigen zu können.
* Finales Ergebnis wird unter gespeichert unter: `Data/kneepoint.csv` (Komplette Pareto-Optimum Evaluation Nutzen + Privacy) `Data/privacy.csv` (Privacy sortiertes Ergebnis mit den sichersten Kombinationen).

---

## Funktionsweise und Architektur

### Deterministische Slot-Zuweisung & Lifecycle
Die Zuweisung der First-Party-Domänen $D_{\text{FP}}$ erfolgt deterministisch in N verschiedene parallele Slots mittels eines clientseitigen HMAC-SHA256-Verfahrens:

$$k = \text{HMAC}(\text{LocalSecret}, D_{\text{FP}})$$

Jeder Slot durchläuft einen finiten Zustandsautomaten mit Folgenden Zuständen: `FRESH`, `ACTIVE`, `WARM`, `SATURATED`
Zur realistischen Abbildung des Surfverhaltens unterscheidet der Algorithmus zwischen zwei Arten des Zurücksetzens:
* **Inaktivität als `session_gap`:** Nach 30 Minuten Inaktivität werden die Zähler für zeitlich isolierte Segmente zurückgesetzt.
* **Pseudonym-Rotation als `rotation_threshold`:** Bei Erreichen der Schwellenwerte erfolgt zusätzlich die Löschung des internen Speicherzustands sowie die Freigabe des Slots mit `release_slot`.

### Angreifermodell & Pareto-Optimierung (Trade-off-Scoring)
Die Evaluierung zwischen Privatsphäre-Schutz und Systemnutzen erfolgt über einen Parameter-Sweep bezüglich der Slot-Anzahl ($N$), der Domänen `max_domains` und der Events `max_events`. Jede Konfiguration wird über Einzelmetriken bewertet:

* **Re-Identifikationsrisiko ($k$-NN-Angreifer):** Jedes Segment wird als $L_2$-normierter Vektor abgebildet und über eine vektorisierte $k$-NN-Klassifikation ($k \in \{1, 3, 5, 10, 20\}$) gegen die ungeschützte Baseline-Matrix aller 2.148 Nutzer getestet. Daraus wird der durchschnittliche Privacy-Score (`Privacy_Score_Avg`) gebildet.
* **Utility-Score:** Kombiniert den normalen Retargeting-Nutzen (`Avg_Utility_ThirdParty`) und die Minimierung der Browser-Resets (`Total_Resets`) zu je 50 %.
* **Pareto-Front und Kniepunkt-Analyse:** Über eine Sekanten-Gerade zwischen den extremsten Punkten wird die Chord_Distance berechnet, um den optimalen Kniepunkt zu bestimmen.
* **Epsilon-Plateau:** Um zu verhindern, dass praktisch gleichwertige Konfigurationen durch minimale Nachkommastellen-Differenzen verloren gehen, markiert ein Toleranzschwellenwert ($\varepsilon = 0.005 = 0{,}5\,\%$) naheliegende Konfigurationen als Plateau-Mitglieder.


## KI-Nutzung
Zur Unterstützung der Implementierung, Strukturierung und Syntax-Optimierung der Simulationspipeline wurden KI-gestützte Programmierassistenten eingesetzt.