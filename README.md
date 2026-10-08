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

Die Skripte werden in dieser Reihenfolge ausgeführt: `preprocessing.py`, `run_simulation.py`, `verkettung.py`, `varianceCheck.py`, danach das Notebook. Alle Skripte mit langer Laufzeit speichern ihre Ergebnisse nach jeder Kombination und überspringen beim nächsten Start alles, was bereits berechnet wurde. Ein abgebrochener Lauf kann so einfach fortgesetzt werden. Soll dagegen etwas neu berechnet werden, müssen die alten Ergebnisse vorher verschoben werden (siehe [Neustart von vorne](#neustart-von-vorne)).

### Daten laden
Vor dem Ausführen der eigentlichen Simulation muss der Datensatz bereinigt und initialisiert werden:

```bash
python preprocessing.py
```
Das Ergebnis wird in `browsing_clean.csv` gespeichert, die Kennzahlen des Datensatzes in `dataset_stats.json`. Der Download wird übersprungen, wenn `Data/datensatz/browsing.csv` bereits existiert. Bereinigung und Kennzahlen werden bei jedem Start neu geschrieben.

### Simulation starten
Die Parameterkombinationen werden in `sweep_blocks` in der `run_simulation.py` festgelegt. Über die Schalter im `main(...)`-Aufruf am Ende der Datei wird gewählt, was gespeichert und ausgewertet wird:

| Schalter | Bedeutung |
|---|---|
| `save_events` | Speichert alle Events pro Kombination in `Data/ergebnisse/raw_sweeps/` (sehr groß) |
| `save_segments` | Speichert alle Segmente pro Kombination, benötigt für `verkettung.py` und die Abschlussgrund-Analyse |
| `direct_analysis` | Berechnet Verkettung und Abschlussgründe direkt im Speicher und schreibt sie in `verkettungs_ranking_direkt.csv` und `sweep_trigger_analyse_direkt.csv` |

Es gibt drei Wege, die zu denselben Ergebnissen führen:

```python
# Alle Rohdaten speichern, danach verkettung.py ausführen (ca. 225 GB)
main(save_events=True, save_segments=True, direct_analysis=False)

# Nur Segmente speichern, danach verkettung.py ausführen (ca. 18,6 GB)
main(save_events=False, save_segments=True, direct_analysis=False)

# Wenig Speicherverbrauch, Auswertung direkt während des Laufs
main(save_events=False, save_segments=False, direct_analysis=True)
```

Unabhängig von den Schaltern werden die Rohdaten der Referenz-Slotreihe (10, 25, 50, 100, 225 und 600 Slots mit 10 Domains, 700 Events und 7 Tagen) IMMER in `Data/ergebnisse/raw_sweeps/` gespeichert, da das Notebook sie für Kaltstart, Domainverteilung und Zeitverlauf benötigt. Alle übrigen Rohdaten können bei Bedarf identisch neu erzeugt werden. Werden die Segmente nicht gespeichert, lässt sich die Verkettung nicht getrennt von der Simulation berechnen. Sie muss dann mit `direct_analysis=True` im selben Lauf erfolgen.

```bash
python run_simulation.py
```

Eine Kombination wird übersprungen, wenn ihre Dateien in `raw_sweeps/` bereits existieren und bei `direct_analysis=True` ihre Ergebnisse bereits in den `*_direkt.csv` stehen.

---
### Verkettung berechnen
Nach dem Sweep werden die Verkettungsmetriken (Kosinus-Ähnlichkeit, Chord-Distance, Identification-Rate) aus den Segment-Dateien berechnet:

```bash
python verkettung.py
```

Das Ergebnis wird in `verkettungs_ranking.csv` gespeichert. Die genauen Spalten-Namen werden unten noch mal genauer erklärt. Konfigurationen, die bereits in `verkettungs_ranking.csv` stehen, werden übersprungen. Das gilt auch, wenn `linkage_metrics` geändert wurde und neue Spalten berechnet werden sollen. In diesem Fall muss die Datei vorher verschoben werden. Die Simulation muss dafür nicht wiederholt werden, solange die Segment-Dateien in `raw_sweeps/` vorhanden sind.

### Abschlussgründe analysieren
Wird bei `save_segments=True` automatisch am Ende von `run_simulation.py` ausgeführt. Einzeln lässt sie sich aus dem Ordner `Funktionen` starten:

```bash
cd Funktionen
python reason_analysis.py
```

Das Ergebnis wird in `sweep_trigger_analyse.csv` gespeichert. Die Datei wird bei jedem Lauf komplett aus den Segment-Dateien neu erzeugt, hier wird also nichts übersprungen.

### Varianz-Check der Slot-Zuweisung
Die Zuweisung neuer Domains zu Slots erfolgt zufällig. Der Varianz-Check prüft deshalb, wie stark die Angriffsraten bei gleicher Slotanzahl allein durch diese Zuweisung schwanken. Dafür wird die Referenz mit 25, 50, 75, 100, 150 und 225 Slots jeweils mit den Seeds 0 bis 19 simuliert, wobei Seed 0 dem Hauptlauf entspricht. Die Verkettung wird direkt nach jedem Lauf berechnet:

```bash
python varianceCheck.py
```

Die Ergebnisse jedes Laufs werden in `variance_check_ranking.csv` gespeichert, Mittelwerte und Standardabweichungen pro Slotanzahl in `variance_check_summary.csv`. Bricht der Lauf ab, werden bereits fertige Seeds beim Neustart übersprungen. Mit `save_segments=True` im `main(...)`-Aufruf werden zusätzlich die Segmente jedes Laufs in `Data/ergebnisse/variance_check` gespeichert (ca. 50 MB pro Lauf).

### Auswertung
Die Abbildungen und Tabellen der Arbeit werden im Notebook `Auswertung/auswertung.ipynb` erzeugt. Die Ergebnis-CSVs liegen im Repository, die Rohdaten der Referenz-Slotreihe dagegen nicht. Sie entstehen bei jedem Lauf von `run_simulation.py`. Wurde die Simulation mit `direct_analysis=True` ausgeführt, wird oben im Notebook `direct = True` gesetzt.

### Neustart von vorne
Für einen vollständig neuen Lauf wird der komplette Ergebnisordner in einen Sicherungsordner verschoben. Danach die Pipeline wie oben beschrieben von vorne ausführen:

```bash
mv Data/ergebnisse Data/ergebnisse_alt
```

Soll nur ein Teil neu berechnet werden, reicht es, die Dateien des jeweiligen Schritts zu verschieben:

| Neu berechnen | Verschieben |
|---|---|
| Simulation | `Data/ergebnisse/raw_sweeps/`, bei `direct_analysis=True` zusätzlich `verkettungs_ranking_direkt.csv` und `sweep_trigger_analyse_direkt.csv` |
| Verkettung | `verkettungs_ranking.csv` |
| Varianz-Check | `variance_check_ranking.csv` und, falls vorhanden, `Data/ergebnisse/variance_check/` |

Verschieben ist besser als Löschen, da die alten Ergebnisse so zum Vergleich erhalten bleiben. Liegt der Sicherungsordner im Projekt, sollte er in die `.gitignore` eingetragen werden.

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
Dafür wurde Claude mit Sonnet 5.5 und Opus 5.5 verwendet.
Um Feedback einzuholen wurde Astra 6 von ChatGPT verwendet.

---

#### Spalten in `sweep_trigger_analyse.csv`

Jede Zeile ist eine Konfiguration. Ein Segment entspricht einem Pseudonym von seiner Vergabe bis zu seinem Abschluss. Prozentwerte sind hier, anders als in `verkettungs_ranking.csv`, bereits mit 100 multipliziert.

| Spalte | Bedeutung |
|---|---|
| `Slots`, `Max_Domains`, `Max_Events`, `Max_Days` | Parameter der Konfiguration |
| `Segments` | Anzahl aller Segmente über alle Nutzer |
| `Median_Age_Days` | Median Alter eines Pseudonyms bei Rotation in Tagen, das aber nur für durch eine Schwelle rotierte Segmente |
| `Avg_Overshoot` | Durchschnittliche Überschreitung der Schwelle durch den Rotation-Lock. Ist in der Einheit der jeweiligen Schwelle. |
| `Max_Overshoot` | Größte Überschreitung einer Schwelle |
| `Avg_Domains_Per_Segment` | Durchschnittliche Anzahl unterschiedlicher Domains pro Segment |
| `Domain_Limit_Fill_Pct` | Durchschnittliche Ausschöpfung der Domaingrenze. Bzw. Domains pro Segment geteilt durch `Max_Domains` |
| `Used_Slots_Pct` | Durchschnittlicher Anteil der Slots, die ein Nutzer überhaupt belegt |
| `Single_Domain_Segments_Pct` | Anteil der Segmente mit genau einer Domain |
| `Single_Domain_Visits_Pct` | Anteil der Aufrufe, die in Segmenten mit genau einer Domain liegen |
| `Trigger_Distribution` | Anteil der Segmente je Abschlussgrund: `Days`, `Events`, `Domains` = Rotation durch die jeweilige Schwelle, `expired` = Schwelle am Datenende bereits erreicht, `end_of_stream` = am Datenende noch offen |

---

#### Spalten in `verkettungs_ranking.csv`

Jede Zeile ist eine Konfiguration. Alle Kennzahlen gibt es zweimal: mit `Incl_` für alle Segmente und mit `Excl_` ohne die am Datenende offenen Segmente (`end_of_stream`). Anteile sind als Werte zwischen 0 und 1 gespeichert.

| Spalte | Bedeutung |
|---|---|
| `Anzahl_Slots`, `Max_Domains`, `Max_Events`, `Max_Days` | Parameter der Konfiguration |
| `Identification_Rate` | Anteil der Segmente, deren ähnlichstes Segment vom selben Nutzer stammt |
| `Avg_Max_Cosine_Own` | Durchschnittlich höchste Kosinus-Ähnlichkeit zu einem eigenen Segment |
| `Avg_Max_Cosine_Other` | Durchschnittlich höchste Kosinus-Ähnlichkeit zu einem fremden Segment |
| `Avg_Chord_Distance` | Durchschnittliche Chord Distance zum ähnlichsten eigenen Segment, wird berechnet, aber nicht ausgewertet |
| `Valid_Segments` | Anzahl der ausgewerteten Segmente |
| `Share_Single_Segment_Users` | Anteil der Nutzer mit nur einem Segment, die nicht verkettet werden können |
| `Tie_Share` | Anteil der Segmente mit Gleichstand zwischen eigenem und fremdem Segment, zählt als Fehlschlag |
| `No_Own_Share` | Anteil der Segmente ohne gemeinsame Domain mit einem eigenen Segment |
| `Tie_Single_Domain_Share` | Anteil der Gleichstände, bei denen das Segment nur eine Domain enthält |
| `Random_Baseline` | Erwartete Rate, wenn der Angreifer zufällig ein anderes Segment wählt |
| `Users_Linked_Share` | Anteil der Nutzer mit mindestens einem korrekt verketteten Segment |
| `Visit_Weighted_Rate` | Identification-Rate, gewichtet nach der Anzahl der Aufrufe im Segment |

### Achtung!
Bei Konfigurationen mit sehr vielen Gleichständen, vor allem bei niedriger Domaingrenze und wenigen Slots, können sich die Identification-Rates zwischen Läufen auf verschiedenen Rechnern oder Paketversionen um wenige Hundertstel Prozentpunkte unterscheiden, da exakte Gleichstände von der Rundung der Gleitkommazahlen abhängen.