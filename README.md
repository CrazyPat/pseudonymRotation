# Pseudonym-Rotation im Real-Time-Bidding

Inhalt ist die Python-Simulations- und Evaluationspipeline für die Bachelorarbeit.

---

## Projektstruktur

```text
├── Auswertung/                              # Auswertungen
│   └── auswertung.ipynb                     # Alle Abbildungen und Tabellen der Arbeit
├── Data/                                    # Datensatz und Ergebnisse
│   ├── datensatz/                           # Datensätze
│   │   ├── browsing.csv                     # Roher Zenodo-Datensatz: https://zenodo.org/records/4757574
│   │   ├── browsing_clean.csv               # Bereinigter Zenodo-Datensatz
│   │   └── domain_tracker_mapping.json      # Verworfener Ansatz: Zuordnung der Domains zu Trackern über WhoTracks.Me
│   └── ergebnisse/                          # Ergebnisse
│       ├── raw_sweeps/                      # Rohdaten pro Konfiguration
│       │   ├── *_events.csv                 # Alle Events einer Konfiguration (save_events=True oder Referenz-Slotreihe)
│       │   └── *_segments.csv               # Alle Segmente einer Konfiguration (save_segments=True oder Referenz-Slotreihe)
│       ├── variance_check/                  # Segmente des Varianz-Checks (nur mit save_segments=True)
│       ├── auswertung/                      # Abbildungen und kaltstart.csv aus dem Notebook
│       ├── dataset_stats.json               # Kennzahlen des Datensatzes
│       ├── verkettungs_ranking.csv          # Verkettung aller Konfigurationen (über verkettung.py)
│       ├── verkettungs_ranking_direkt.csv   # Verkettung aller Konfigurationen (über direct_analysis)
│       ├── sweep_trigger_analyse.csv        # Abschlussgründe aller Konfigurationen (über reason_analysis)
│       ├── sweep_trigger_analyse_direkt.csv # Abschlussgründe aller Konfigurationen (über direct_analysis)
│       ├── variance_check_ranking.csv       # Ergebnis jedes Laufs des Varianz-Checks
│       └── variance_check_summary.csv       # Mittelwert und Standardabweichung pro Slotanzahl
├── Funktionen/                              # Python-Paket der Simulationspipeline
│   ├── data/                                # Download und Kennzahlen des Datensatzes
│   │   ├── __init__.py                      # init
│   │   ├── load_dataset.py                  # Download der rohen browsing.csv
│   │   └── dataset_check.py                 # Kennzahlen des bereinigten Datensatzes
│   ├── pseudonym/                           # Lifecycle, HMAC-Zuweisung und Nutzersimulation
│   │   ├── __init__.py                      # init
│   │   ├── lifecycle.py                     # SlotState-Container und Lifecycle
│   │   ├── simulation.py                    # UserSimulation
│   │   └── zuweisung.py                     # SlotAssigner
│   ├── config.py                            # Datencontainer
│   ├── utils.py                             # Logging-Funktion
│   └── reason_analysis.py                   # Abschlussgründe und Domain-Kennzahlen pro Konfiguration
├── preprocessing.py                         # Download, Bereinigung und Kennzahlen des Datensatzes
├── run_simulation.py                        # Hauptskript
├── verkettung.py                            # Berechnet die Verkettung aus den gespeicherten Segmenten
├── varianceCheck.py                         # Wiederholt die Simulation mit 20 Seeds
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

* **Clickstream-Daten:** Der Zenodo-Datensatz „A web tracking data set of online browsing behavior of 2,148 users“ (Kulshrestha et al., ICWSM 2021) bildet das reale Surfverhalten der Nutzer im Oktober 2018 ab. Er wird von `preprocessing.py` automatisch heruntergeladen.

---

## Ausführung der Pipeline

### Daten laden
Vor dem Ausführen der eigentlichen Simulation muss der Datensatz bereinigt und initialisiert werden:

```bash
python preprocessing.py
```
Das Ergebnis wird in `browsing_clean.csv` gespeichert, die Kennzahlen des Datensatzes in `dataset_stats.json`.

### Simulation starten
Die Parameterkombinationen werden in `sweep_blocks` in der `run_simulation.py` festgelegt. Über die Schalter im `main(...)`-Aufruf am Ende der Datei wird gewählt, was gespeichert und ausgewertet wird:

| Schalter | Bedeutung |
|---|---|
| `save_events` | Speichert alle Events pro Kombination in `Data/ergebnisse/raw_sweeps/` (sehr groß) |
| `save_segments` | Speichert alle Segmente pro Kombination, benötigt für `verkettung.py` und die Abschlussgrund-Analyse |
| `direct_analysis` | Berechnet Verkettung und Abschlussgründe direkt im Speicher und schreibt sie in `verkettungs_ranking_direkt.csv` und `sweep_trigger_analyse_direkt.csv` |

Es gibt zwei Wege, die zu denselben Ergebnissen führen:

```python
# Alle Rohdaten speichern, danach seperat verkettung.py ausführen (ca. 230 GB)
main(save_events=True, save_segments=True, direct_analysis=False)

# Wenig Speicherverbrauch, Auswertung direkt während des Laufs
main(save_events=False, save_segments=False, direct_analysis=True)
```

Unabhängig von den Schaltern werden die Rohdaten der Referenz-Slotreihe (10, 25, 50, 100, 225 und 600 Slots mit 10 Domains, 700 Events und 7 Tagen) IMMER in `Data/ergebnisse/raw_sweeps/` gespeichert, da das Notebook sie für Kaltstart, Domainverteilung und Zeitverlauf benötigt. Alle übrigen Rohdaten können bei Bedarf identisch neu erzeugt werden. Wichtig ist auch, dass wenn man die Simulationsergebnisse nicht speichert, der Durchlauf der Simulationspipeline von dem der Verkettung nicht getrennt werden kann. 

Ergebnisse werden nach jeder Kombination geschrieben. Bricht der Lauf ab, werden bereits fertige Kombinationen beim Neustart übersprungen.

```bash
python run_simulation.py
```

---
### Verkettung berechnen
Nach dem Sweep werden die Verkettungsmetriken (Kosinus-Ähnlichkeit, Chord-Distance, Identification-Rate) aus den Segment-Dateien berechnet:

\```bash
python verkettung.py
\```

Das Ergebnis wird in `verkettungs_ranking.csv` gespeichert.

### Abschlussgründe analysieren
Wird bei `save_segments=True` automatisch am Ende von `run_simulation.py` ausgeführt. Einzeln lässt sie sich aus dem Ordner `Funktionen` starten:

```bash
cd Funktionen
python reason_analysis.py
```

Das Ergebnis wird in `sweep_trigger_analyse.csv` gespeichert.

### Varianz-Check der Slot-Zuweisung
Die Zuweisung neuer Domains zu Slots erfolgt zufällig. Der Varianz-Check prüft deshalb, wie stark die Angriffsraten bei gleicher Slotanzahl allein durch diese Zuweisung schwanken. Dafür wird die Referenz mit 25, 50, 75, 100, 150 und 225 Slots jeweils mit den Seeds 0 bis 19 simuliert, wobei Seed 0 dem Hauptlauf entspricht. Die Verkettung wird direkt nach jedem Lauf berechnet:

```bash
python varianceCheck.py
```

Die Ergebnisse jedes Laufs werden in `variance_check_ranking.csv` gespeichert, Mittelwerte und Standardabweichungen pro Slotanzahl in `variance_check_summary.csv`. Bricht der Lauf ab, werden bereits fertige Seeds beim Neustart übersprungen. Mit `save_segments=True` im `main(...)`-Aufruf werden zusätzlich die Segmente jedes Laufs in `Data/ergebnisse/variance_check` gespeichert (ca. 50 MB pro Lauf).

### Auswertung
Die Abbildungen und Tabellen der Arbeit werden im Notebook `Auswertung/auswertung.ipynb` erzeugt und in `Data/ergebnisse/auswertung/` gespeichert. Die Ergebnis-CSVs liegen im Repository, die Rohdaten der Referenz-Slotreihe dagegen nicht. Sie entstehen bei jedem Lauf von `run_simulation.py`. Wurde die Simulation mit `direct_analysis=True` ausgeführt, wird oben im Notebook `direct = True` gesetzt.

## Architektur

### Die Simulation der Pseudonym-Rotation
Die Simulation bildet die Pseudonym-Rotation ab. Der Verkettungsangriff in `verkettung.py` nimmt einen Tracker an, der jeden Domain-Aufruf eines Nutzers erfasst.

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