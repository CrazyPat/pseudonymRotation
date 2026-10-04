# Pseudonym-Rotation im Real-Time-Bidding

Inhalt ist die Python-Simulations- und Evaluationspipeline für die Bachelorarbeit.

---

## Projektstruktur

```text
├── Auswertung/                              # Alle Auswertungen
│   └── auswertung.ipynb                     # Alle Abbilungen und Tabellen
├── Data/                                    # Datensatz und Ergebnisse
│   ├── datensatz                            # Alle relevanten Datensätze
│   │   ├── browsing.csv                     # Raw Zenodo-Datensatz: https://zenodo.org/records/4757574
│   │   ├── browsing_clean.csv               # Aufgeräumter Zenodo-Datensatz
│   │   └── domain_tracker_mapping.json      # Verworfener Ansatz: Zurodnung aller Domains zu Trackern basierend auf dem WhoTracks.Me-Datensatz
│   ├── ergebnisse/                          # Ergebnisse
│   │   └── raw_sweeps/                      # Speichert Simulationsergebnisse von jeder Konfiguration (LOGS)
│   │   │   ├── parameter_events.csv         # Jedes Event einer Konfiguration
│   │   │   └── parameter_segments.csv       # Jedes Segment einer Konfiguration
│   │   └── variance_check/                  # Speichert die Varianzergebnisse von jeder Konfiguration (Logs)
│   │   │   └── parameter_segments.csv       # Jedes Segment einer Konfiguration
│   │   ├── verkettungs_ranking.csv          # Ergebnisse der Verkettung für den kompletten Sweep
│   │   ├── sweep_trigger_analyse.csv        # Abschlussgründe für eine Konfiguration
│   │   ├── variance_check_ranking.csv       # Ergebnis des Variance_Checks
│   │   └── variance_check_summary.csv       # Zusammenfassung des Variance_Checks
├── Funktionen/                              # Python-Paket der Simulationspipeline
│   ├── daten/                               # Browsing.csv und WhoTracks.Me Datensatz Download
│   │   ├── __init__.py                      # init
│   │   └── load_dataset.py                  # Download des raw browsing.csv
│   ├── pseudonym/                           # Lifecycle, HMAC-Zuweisung und Nutzersimulation
│   │   ├── __init__.py                      # init
│   │   ├── lifecycle.py                     # SlotState-Container und Lifecycle
│   │   ├── simulation.py                    # UserSimulation
│   │   └── zuweisung.py                     # SlotAssigner
│   ├── config.py                            # Datencontainer
│   ├── utils.py                             # Logging-Funktion
│   └── reason_analysis.py                   # Erstellt die Abschlussgründe aus allen Konfigurationen
├── preprocessing.py                         # Download und Vorverarbeitung des Datensatzes
├── run_simulation.py                        # Hauptskript
├── verkettung.py                            # Berechnet Verkettungsmetriken
├── varianceCheckSimulation.py               # Variiert Slotzuweisung für die Gesamte Simulation 20 mal durch
├── varianceCheckVerkettung.py               # Rechnet Verkettung für die Variierte Simulation aus
├── requirements.txt                         # Projekt-Abhängigkeiten
└── README.md                                # Projektdokumentation
```

---

## Einrichtung

### Abhängigkeiten installieren
Installiere die benötigten Abhängigkeiten im Root-Verzeichnis des Projekts:

```bash
pip install -r requirements.txt
```

## Datensatz

* **Clickstream-Daten:** Der Zenodo-Datensatz „A web tracking data set of online browsing behavior of 2,148 users“ bildet das reale Surfverhalten der Nutzer ab.

---

## Ausführung der Pipeline

### Daten laden
Vor dem Ausführen der eigentlichen Simulation muss der Datensatz bereinigt und initialisiert werden:

```bash
python preprocessing.py
```
Das Ergebnis wird in `browsing_clean.csv` gespeichert.

### Simulation starten
Damit der Simulationsdurchlauf starten kann muss ein Parameter-Sweep in der run_simulation.py angegeben werden, sonst wird die empfohlene Konfiguration durchlaufen.

```bash
python run_simulation.py
```

Die vollständig durchlaufenden Segmente und Events werden in `Data/ergebnisse/raw_sweeps/` gespeichert.
---
### Verkettung berechnen
Nach dem Sweep werden die Verkettungsmetriken (Kosinus-Ähnlichkeit, Chord-Distance, Identification-Rate) aus den Segment-Dateien berechnet:

\```bash
python verkettung.py
\```

Das Ergebnis wird in `verkettungs_ranking.csv` gespeichert.

### Abschlussgründe analysieren
Fasst die Trigger-Verteilung für jede Konfiguration zusammen:

\```bash
python reason_analysis.py
\```

Das Ergebnis wird in `sweep_trigger_analyse.csv` gespeichert.

### Varianz-Check der Slot-Zuweisung
Die Erstzuweisung der Domains zu Slots passiert zufällig, deshalb prüft der Varianz-Check, wie stark die Angriffsraten von der gewählten Slotanzahl schwanken. Dafür wird dieselbe Konfiguration mit mehreren Seeds wiederholt simuliert:

\```bash
python varianceCheckSimulation.py
python varianceCheckVerkettung.py
\```

Die vollständig durchlaufenden Segmente und Events werden in `Data/ergebnisse/variance_check` gespeichert.
Das vollständige Ergebnis wird in `variance_check_ranking.csv` gespeichert.
Das zusammenfassende Ergebnis wird in `variance_check_summary.csv` gespeichert.

## Architektur

### Die Simulation der Pseudonym-Rotation
Die Simulation bildet einen Angriff eines globalen Trackers ab, der jeden Domain-Aufruf eines Nutzers erfasst.

**Slot-Zuweisung und Reproduzierbarkeit**

Jeder Nutzer verfügt über $N$ parallele Slots. Eine Domain wird vor der Speicherung mit einem lokalen Secret per HMAC-SHA256 auf einen Schlüssel der Zuordnungstabelle abgebildet:

$$k = \text{HMAC}(\text{LocalSecret}, \text{Domain})$$

Der HMAC dient nur dazu, die Domains in der Tabelle nicht im Klartext zu speichern. Eine noch unbekannte Domain wird zufällig einem der $N$ Slots zugewiesen. Danach landen alle weiteren Aufrufe dieser Domain im selben Slot, bis dieser rotiert wird.

Die Zuweisung ist derzeit deterministisch, damit jede Konfiguration exakt reproduziert werden kann. Das lokale Secret wird aus der Nutzer-ID abgeleitet und der Zufallsgenerator jedes Nutzers mit `SHA-256("{user_id}_{run_seed}")` initialisiert. Die Hauptauswertung verwendet `run_seed = 0`. Der Varianz-Check wiederholt die Simulation mit den Seeds 0 bis 19, wobei Seed 0 dem Hauptlauf entspricht. In einer realen Umsetzung wären Secret und Slotwahl echt zufällig.

**Lifecycle und Rotation**

Jeder Slot durchläuft die Zustände FRESH → ACTIVE → WARM → SATURATED → RESET → FRESH. WARM wird gesetzt, sobald ein Wert 80 % seiner Schwelle erreicht. Ein Pseudonym rotiert, wenn bei einer Prüfung einer der folgenden Schwellenwerte erreicht ist:

* **max_domains:** Maximale Anzahl an unterschiedlichen Domains.
* **max_events:** Maximale Anzahl an Seitenaufrufen.
* **max_days:** Maximales Alter des Pseudonyms in Tagen.

Geprüft wird nur beim Wechsel auf eine andere Domain (Rotation-Lock), und zwar der Slot der verlassenen und der Slot der neuen Domain. Bei einer Rotation werden alle Zähler, Zeitstempel und Domain-Historien des Slots gelöscht und die Zuweisungen der betroffenen Domains aus der `domain_to_slot_map` entfernt. Beim nächsten Aufruf erhält die Domain eine neue Zuweisung.
---

## KI-Nutzung
Zur Unterstützung der Implementierung, Strukturierung und Syntax-Optimierung der Simulationspipeline wurden KI-gestützte Programmierassistenten eingesetzt.