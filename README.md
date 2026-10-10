# Pseudonym-Rotation im Real-Time-Bidding

Inhalt ist die Python-Simulations- und Evaluationspipeline für die Bachelorarbeit „Pseudonym-Rotation im Real-Time-Bidding: Design und Evaluierung schwellenwertbasierter Slot-Partitionierung mittels Clickstream-basierten Re-Identifikationsangriffs“ (Patrick Wazny, Universität Regensburg, Lehrstuhl für Wirtschaftsinformatik IV, 2026).

Alle Ergebnisdateien und das ausgeführte Notebook liegen im Repository. Die Auswertung lässt sich also auch ohne eigene Simulation nachvollziehen (siehe [Auswertung](#auswertung)).

---

## Projektstruktur

```text
├── Auswertung/                                  # Auswertungen
│   ├── auswertung.ipynb                         # Alle Abbildungen und Tabellen aus Kapitel 5 und Anhang B
│   ├── trackerMapping.py                        # Verworfener Ansatz: WhoTracks.Me-Mapping und Kennzahlen aus Abschnitt 4.1.2
│   ├── beispielrechnung.md                      # Ausgeschriebene Rechnung zum Beispiel aus Abschnitt 4.4
│   └── statsCounterAuswertung.py                # Marktanteil der Chromium-basierten Browser (Anhang A)
├── Data/                                        # Datensatz und Ergebnisse
│   ├── datensatz/                               # Datensätze
│   │   ├── browsing.csv                         # Roher Zenodo-Datensatz (nicht im Repo, lädt preprocessing.py)
│   │   ├── browsing_clean.csv                   # Bereinigter Zenodo-Datensatz (nicht im Repo, erzeugt preprocessing.py)
│   │   ├── statsCounterData.csv                 # Statcounter-Export der Browser-Marktanteile (Anhang A)
│   │   ├── domain_tracker_mapping.json          # Verworfener Ansatz: Zuordnung der Domains zu Trackern über WhoTracks.Me
│   │   └── tranco_2019-02-18.txt                # Verworfener Ansatz: Tranco-Liste
│   └── ergebnisse/                              # Ergebnisse, die Spalten sind in Data/ergebnisse/README.md erklärt
│       ├── raw_sweeps/                          # Events und Segmente pro Konfiguration (nicht im Repo, zu groß)
│       ├── variance_check/                      # Segmente des Varianz-Checks (nur mit save_segments=True, nicht im Repo)
│       ├── auswertung/                          # Abbildungen 5.2 bis 5.10 sowie Tabellen 5.1 und 5.3 aus dem Notebook
│       ├── dataset_stats.json                   # Kennzahlen des Datensatzes
│       ├── tracker_mapping_stats.json           # Kennzahlen des verworfenen Tracker-Mappings
│       ├── verkettungs_ranking.csv              # Verkettung aller Konfigurationen (über verkettung.py)
│       ├── sweep_trigger_analyse.csv            # Abschlussgründe aller Konfigurationen (über reason_analysis.py)
│       ├── variance_check_ranking.csv           # Ergebnis jedes Laufs des Varianz-Checks
│       └── variance_check_summary.csv           # Mittelwert und Standardabweichung pro Konfiguration (Tabelle B.3)
├── Funktionen/                                  # Python-Paket der Simulationspipeline
│   ├── data/                                    # Download und Kennzahlen des Datensatzes
│   │   ├── load_dataset.py                      # Download der rohen browsing.csv
│   │   └── dataset_check.py                     # Kennzahlen des bereinigten Datensatzes
│   ├── pseudonym/                               # Lifecycle, HMAC-Zuweisung und Nutzersimulation
│   │   ├── lifecycle.py                         # SlotState-Container und Lifecycle
│   │   ├── simulation.py                        # UserSimulation
│   │   └── zuweisung.py                         # SlotAssigner
│   ├── config.py                                # Datencontainer
│   ├── utils.py                                 # Logging-Funktion
│   └── reason_analysis.py                       # Abschlussgründe und Domain-Kennzahlen pro Konfiguration
├── preprocessing.py                             # Download, Bereinigung und Kennzahlen des Datensatzes
├── run_simulation.py                            # Hauptskript
├── verkettung.py                                # Berechnet die Verkettung aus den gespeicherten Segmenten
└── varianceCheck.py                             # Wiederholt die Simulation mit 20 Seeds
```

---

## Einrichtung
Getestet mit Python 3.11 (mindestens 3.10). Die Abhängigkeiten werden im Hauptordner des Projekts installiert, aus dem auch alle Skripte gestartet werden:

```bash
pip install -r requirements.txt
```

---

## Ausführung der Pipeline

Die Skripte werden in dieser Reihenfolge ausgeführt: `preprocessing.py`, `run_simulation.py`, `verkettung.py`, `varianceCheck.py`, danach das Notebook. Alle Skripte mit langer Laufzeit speichern ihre Ergebnisse nach jeder Kombination und überspringen beim nächsten Start alles, was bereits berechnet wurde. Ein abgebrochener Lauf kann so einfach fortgesetzt werden. Soll dagegen etwas neu berechnet werden, müssen die alten Ergebnisse vorher verschoben werden (siehe [Neustart von vorne](#neustart-von-vorne)).

### Daten laden
Grundlage ist der Zenodo-Datensatz „A web tracking data set of online browsing behavior of 2,148 users“ (Kulshrestha et al., ICWSM 2021) mit dem realen Surfverhalten der Nutzer im Oktober 2018. `preprocessing.py` lädt ihn herunter, bereinigt ihn und speichert das Ergebnis in `browsing_clean.csv`, die Kennzahlen in `dataset_stats.json`. Der Download wird übersprungen, wenn `Data/datensatz/browsing.csv` bereits existiert.

```bash
python preprocessing.py
```

### Simulation starten
Die Parameterkombinationen stehen in `sweep_blocks` in der `run_simulation.py`. Jeder Eintrag besteht aus vier Listen in der Reihenfolge `([Slots], [Max_Domains], [Max_Events], [Max_Days])`, simuliert wird jede Kombination daraus. `([25, 50], [3], [100], [7, 14])` ergibt zum Beispiel vier Kombinationen, auch ein einzelner Wert steht in eckigen Klammern. Über die Schalter im `main(...)`-Aufruf am Ende der Datei wird gewählt, was gespeichert und ausgewertet wird. Es gibt drei Wege, die zu denselben Ergebnissen führen:

```python
# Alle Events und Segmente speichern, danach verkettung.py ausführen (ca. 225 GB)
main(save_events=True, save_segments=True, direct_analysis=False)

# Nur Segmente speichern, danach verkettung.py ausführen (ca. 18,6 GB, Standard)
main(save_events=False, save_segments=True, direct_analysis=False)

# Nichts speichern, Verkettung und Abschlussgründe direkt im Lauf in die *_direkt.csv schreiben
main(save_events=False, save_segments=False, direct_analysis=True)
```

Unabhängig von den Schaltern werden die Rohdaten der Referenz-Slotreihe (10, 25, 50, 100, 225 und 600 Slots mit 10 Domains, 700 Events und 7 Tagen) immer in `raw_sweeps/` gespeichert, sofern sie in `sweep_blocks` stehen, da das Notebook sie braucht. Eine Kombination wird übersprungen, wenn ihre Dateien in `raw_sweeps/` bereits existieren und bei `direct_analysis=True` ihre Ergebnisse schon in den `*_direkt.csv` stehen.

```bash
python run_simulation.py
```

Die Simulation aller 535 Konfigurationen dauerte auf einem MacBook Pro (M3 Pro, 18 GB) mit 7 parallelen Prozessen rund 4 Stunden und 40 Minuten.

### Erster Test
Für einen ersten Test empfiehlt sich nur die Referenz mit direkter Auswertung. Die mitgelieferten Ergebnisse bleiben dabei unverändert, die Werte landen in den `*_direkt.csv` und lassen sich mit der Referenzzeile in `verkettungs_ranking.csv` vergleichen:

```python
sweep_blocks = [([100], [10], [700], [7]),]
main(save_events=False, save_segments=False, direct_analysis=True)
```

Mit `sweep_blocks = [([10, 25, 50, 100, 225, 600], [10], [700], [7]),]` entstehen auf dieselbe Weise die Rohdaten der Referenz-Slotreihe, die das Notebook zusätzlich braucht.

Achtung: Mit `save_segments=True` wird am Ende `sweep_trigger_analyse.csv` aus allen Segment-Dateien in `raw_sweeps/` neu geschrieben. Bei einem Testlauf mit wenigen Konfigurationen würden so die mitgelieferten Ergebnisse überschrieben. Deshalb vorher `Data/ergebnisse` sichern (siehe [Neustart von vorne](#neustart-von-vorne)).

### Verkettung berechnen

```bash
python verkettung.py
```

Berechnet Kosinus-Ähnlichkeit, Chord Distance und Identification-Rate aus den Segment-Dateien und speichert sie in `verkettungs_ranking.csv`. Wurde `linkage_metrics` geändert, muss die Datei vorher verschoben werden, sonst werden die vorhandenen Konfigurationen übersprungen. Die Simulation muss dafür nicht wiederholt werden. Da jedes Segment mit allen anderen derselben Konfiguration verglichen wird, wächst die Rechenzeit quadratisch mit der Anzahl der Segmente, am längsten dauern daher wenige Slots und niedrige Grenzen. Alle 535 Konfigurationen dauerten bei 4 parallelen Prozessen etwa anderthalb Tage.

### Abschlussgründe analysieren
Läuft bei `save_segments=True` automatisch am Ende von `run_simulation.py`. Einzeln lässt es sich aus dem Ordner `Funktionen` starten:

```bash
cd Funktionen
python reason_analysis.py
```

`sweep_trigger_analyse.csv` wird dabei jedes Mal komplett aus den Segment-Dateien in `raw_sweeps/` neu erzeugt. Liegen dort keine Segment-Dateien, bleibt die vorhandene Datei unverändert.

### Varianz-Check der Slot-Zuweisung
Die Zuweisung neuer Domains zu Slots erfolgt zufällig. Der Varianz-Check prüft deshalb, wie stark die Angriffsraten allein durch diese Zuweisung schwanken. Dafür werden die Slotreihe um die Referenz (25, 50, 75, 100, 150 und 225 Slots) sowie die Konfigurationen mit 100 Slots, die die Referenz in Abschnitt 5.5 übertreffen (500, 1.000, 1.250, 1.500 und 2.000 Events sowie 15 und 20 Domains), jeweils mit den Seeds 0 bis 19 simuliert, wobei Seed 0 dem Hauptlauf entspricht. Die Verkettung wird direkt nach jedem Lauf berechnet:

```bash
python varianceCheck.py
```

Die Ergebnisse jedes Laufs stehen in `variance_check_ranking.csv`, Mittelwerte und Standardabweichungen in `variance_check_summary.csv` und die Tests dazu in Abschnitt 7 des Notebooks. Die 260 Läufe dauern zusammen etwa 9 bis 10 Stunden. Mit `save_segments=True` im `main(...)`-Aufruf werden zusätzlich die Segmente jedes Laufs in `Data/ergebnisse/variance_check` gespeichert (ca. 3,28 GB insgesamt).

### Auswertung
Die Abbildungen und Tabellen der Arbeit werden im Notebook `Auswertung/auswertung.ipynb` erzeugt, bei jedem Abschnitt steht die zugehörige Abbildung oder Tabelle. Alle Ausgaben sind im Notebook gespeichert. Die Rohdaten der Referenz-Slotreihe liegen nicht im Repository und entstehen bei jedem Lauf von `run_simulation.py` (siehe [Erster Test](#erster-test)). Ohne sie laufen alle Abschnitte außer 2.1, 3 (Abbildungen 5.7 und 5.8), 3.1 und 8. Wurden alle Konfigurationen mit `direct_analysis=True` berechnet, wird oben im Notebook `direct = True` gesetzt.

### Weitere Skripte
Die Kennzahlen zum verworfenen Domain-Tracker-Mapping aus Abschnitt 4.1.2 berechnet `Auswertung/trackerMapping.py`, die Marktanteile der Chromium-Browser aus Anhang A `Auswertung/statsCounterAuswertung.py`. Das Paket `whotracksme==2018.5.17` mit den WhoTracks.Me-Daten wird nur für das erste Skript gebraucht und setzt eine ältere Version von `setuptools` voraus. Es steht deshalb nicht in der `requirements.txt` und wird bei Bedarf separat installiert. Voraussetzung ist außerdem die `browsing_clean.csv` aus `preprocessing.py`.

```bash
pip install whotracksme==2018.5.17 "setuptools<70"
python Auswertung/trackerMapping.py            # erzeugt domain_tracker_mapping.json und tracker_mapping_stats.json
python Auswertung/statsCounterAuswertung.py    # summiert die Marktanteile aus statsCounterData.csv
```

### Neustart von vorne
Für einen vollständig neuen Lauf wird der komplette Ergebnisordner verschoben und die Pipeline danach von vorne ausgeführt:

```bash
mv Data/ergebnisse Data/ergebnisse_alt
```

Soll nur ein Teil neu berechnet werden, reicht es, die Dateien des jeweiligen Schritts zu verschieben:

| Neu berechnen | Verschieben |
|---|---|
| Simulation | `Data/ergebnisse/raw_sweeps/`, bei `direct_analysis=True` zusätzlich `verkettungs_ranking_direkt.csv` und `sweep_trigger_analyse_direkt.csv` |
| Verkettung | `verkettungs_ranking.csv` |
| Varianz-Check | `variance_check_ranking.csv` und, falls vorhanden, `Data/ergebnisse/variance_check/` |

---

## Funktionsweise und Reproduzierbarkeit
Der Verkettungsangriff in `verkettung.py` nimmt einen Tracker an, der jeden Domain-Aufruf eines Nutzers erfasst. Jeder Nutzer verfügt über $N$ parallele Slots. Eine noch unbekannte Domain wird zufällig einem Slot zugewiesen und in der Zuordnungstabelle nur als Schlüssel $k = \text{HMAC-SHA256}(\text{LocalSecret}, \text{Domain})$ gespeichert, damit die Domains dort nicht im Klartext stehen. Alle weiteren Aufrufe dieser Domain landen im selben Slot, bis dieser rotiert wird.

Jeder Slot durchläuft die Zustände FRESH → ACTIVE → WARM → SATURATED → RESET → FRESH, WARM wird bei 80 % einer Schwelle gesetzt. Ein Pseudonym rotiert, sobald bei einer Prüfung `max_domains` (unterschiedliche Domains), `max_events` (Seitenaufrufe) oder `max_days` (Alter in Tagen) erreicht ist. Geprüft wird nur beim Wechsel auf eine andere Domain (Rotation-Lock), und zwar der Slot der verlassenen und der Slot der neuen Domain. Bei einer Rotation werden alle Zähler, Zeitstempel und Domain-Historien des Slots gelöscht und die Zuweisungen seiner Domains aus der `domain_to_slot_map` entfernt.

Die Zuweisung ist derzeit deterministisch, damit jede Konfiguration exakt reproduziert werden kann. Das lokale Secret wird aus der Nutzer-ID abgeleitet und der Zufallsgenerator jedes Nutzers mit den ersten 32 Bit von `SHA-256("{user_id}_{run_seed}")` initialisiert. Die Slotwahl hängt dabei nur vom Zufallsgenerator ab, nicht vom Secret. Die Hauptauswertung verwendet `run_seed = 0`, der Varianz-Check die Seeds 0 bis 19. In einer realen Umsetzung wären Secret und Slotwahl echt zufällig.

Bei Konfigurationen mit sehr vielen Gleichständen, vor allem bei niedriger Domaingrenze und wenigen Slots, können sich die Identification-Rates zwischen Rechnern oder Paketversionen trotzdem um wenige Hundertstel Prozentpunkte unterscheiden, da exakte Gleichstände von der Rundung der Gleitkommazahlen abhängen.

---

## KI-Nutzung
Bei der Implementierung, Strukturierung und Syntax-Optimierung der Simulationspipeline und der Auswertungen sowie beim Verfassen dieser README wurden Claude Opus 5.5 und Claude Sonnet 5.5 als Programmierassistenten eingesetzt. Die Beispielrechnung in `Auswertung/beispielrechnung.md` wurde mit Claude Opus 5.5 ausformuliert und selbständig nachgerechnet. ChatGPT 6 Astra wurde für Feedback verwendet. Alle Ergebnisse wurden eigenständig geprüft. Eine vollständige Übersicht enthält das Hilfsmittelverzeichnis der Arbeit.

## Lizenz
Der Code steht unter der MIT-Lizenz (siehe `LICENSE`). Die Dateien in `Data/datensatz` stammen aus externen Quellen (Zenodo, Tranco, Statcounter, WhoTracks.Me) und unterliegen deren Nutzungsbedingungen.
