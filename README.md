# Pseudonym-Rotation im Real-Time-Bidding

Inhalt ist die Python-Simulations- und Evaluationspipeline für die Bachelorarbeit.

---

## Projektstruktur

```text
├── Data/                                    # Datensatz und generierte Mapping-Dateien
│   ├──datensatz                             # Alle relevanten Datensätze
│   │   ├──whotracksme                       # Join-Datensatz mit allen passenden Trackern
│   │   │   ├──site_trackers.csv             # Mapping zum Joinen
│   │   │   ├──trackers.csv                  # Alle Tracker, die verwendet werden
│   │   ├──browsing.csv                      # Raw Zonedo-Datensatz: https://zenodo.org/records/4757574
│   │   ├──browsing_clean.csv                # Aufgeräumter Zonedo-Datensatz
│   │   ├──domain_tracker_mapping.json       # Zurodnung aller Domains zu Trackern basierend auf dem WhoTracks.Me-Datensatz
│   │   ├──single_tracker_mapping.json       # Zurodnung aller Domains zu einem globalen Tracker
│   │   ├──sweep_checkpoint.csv              # Checkpoint falls die Simulation abstürtzt (Ergebnis geladen mit einem globalen Tracker)
│   │   ├──sweep_checkpoint_tracker.csv      # Checkpoint falls die Simulation abstürtzt (Ergebnis geladen mit den gejointen Trackern)
│   ├──ergebnisse_global_tracker             # Ergebnisse mit einem globalen Tracker
│   │   ├──kneepoint.csv                     # Ergebnis der Simulation geordnet nach dem Pareto-Optimum (Platz 1 = Utility + Privacy)
│   │   ├──privacy.csv                       # Ergebnis der Simulation geordnet nach dem Pareto-Optimum (Platz 1 = Utility + Privacy)
│   ├──ergebnisse_tracker                    # Ergebnisse der gejointen Tracker mit dem WhoTracks.Me-Datensatz
│   │   ├──kneepoint.csv                     # Ergebnis der Simulation geordnet nach dem Pareto-Optimum (Platz 1 = Utility + Privacy)
│   │   ├──privacy.csv                       # Ergebnis der Simulation geordnet nach dem Durchschnitt aller k-NN-Werte (Platz 1 = sicherste Kombination)
├── Funktionen/                              # Python-Paket der Simulationspipeline
│   ├── daten/                               # Browsing.csv und WhoTracks.Me Datensatz Download
│   │   ├── __init__.py                      # init
│   │   ├── load_dataset.py                  # Download des raw browsing.csv 
│   │   ├── load_whotracksme.py              # Download des WhoTracks.Me Datensatzes
│   ├── auswertung/                          # Vokabular, Baseline-Matrix, k-NN-Evaluation und Scoring
│   │   ├── __init__.py                      # init
│   │   ├── evaluation.py                    # Kosinus-Ähnlichkeit, k-NN-Accuracy und Utility-Berechnung
│   │   ├── scoring.py                       # Min-Max-Normalisierung, Kniepunkt und Epsilon-Plateau
│   │   ├── sweep.py                         # Parameter-Sweep
│   │   └── vocabulary.py                    # Aufbau des Tracker-Vokabulars und der Baseline-Matrix
│   ├── pseudonym/                           # Lifecycle, HMAC-Zuweisung und Nutzersimulation
│   │   ├── __init__.py                      # init
│   │   ├── lifecycle.py                     # SlotState-Container und Lifecycle
│   │   ├── simulation.py                    # UserSimulation
│   │   └── zuweisung.py                     # SlotAssigner
│   ├── config.py                            # Datencontainer
│   └── utils.py                             # Logging-Funktion
├── tracker.py                               # Download, Vorverarbeitung und Auswertung beider Datensätze
├── run.py                                   # Hauptskript
├── load_whotracksme.py                      # Läd den WhoTracks.Me-Datensatz in den Ordern Data/datensatz/whotracksme
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

## Datensätze

* **Clickstream-Daten:** Der Zenodo-Datensatz „A web tracking data set of online browsing behavior of 2,148 users“ bildet das reale Surfverhalten der Nutzer ab.

* **Tracker-Datenbank:** Die **WhoTracks.Me**-Datenbank dient dem Mapping von Domain auf Tracker.

---

## Vorverarbeitung

Die rohen Clickstream-Daten habeb keine Zuordnung zwischen den aufgerufenen Domains und benötigt deshalb eine Vorverarbeitung.

* **Filterung technischer Dienste:** WhoTracks.Me erfasst neben Tracking-Diensten auch allgemeine Web-Infrastruktur. Um dies zu zu filtern, werden folgende Dienste entfernt:
  * `cdn`, `hosting`, `customer_interaction`, `audio_video_player`, `extensions`
* **Bereinigung ungemappter Domains:** Es besteht die Möglichkeit ungemappte Domains zu entfernen, dies wird aber für die Simulation NICHt gemacht. Die Folge ist dass diese Domains keine Tracker-Zurodnung haben.
* **Daten-Download:** Fehlende Rohdaten wie die browsing.csv oder WhoTracks.Me-Tabellen werden beim Skriptaufruf automatisch geladen und bereitgestellt. Falls diese schon exisiteren werden die nicht erneut geladen.

---

## Ausführung der Pipeline

### Daten laden und Mapping erstellen
Vor dem Ausführen der eigentlichen Simulation muss das Tracker-Mapping erstellt und der Datensatz bereinigt werden:

```bash
python tracker.py
```

### Evaluation starten


```bash
python run.py
```

* Das Skript verarbeitet die Nutzer parallel über alle CPU-Kerne mit use_parallel=True. Falls dies nicht passieren soll im run.py auf False setzen.
* Der Fortschritt wird in Data/datensatz/sweep_checkpoint.csv gespeichert um nach Fehlern oder einem Crash wieder erneut einsteigen zu können. Dort werden dann Erstmalige Ergebnisse und druchläufe gespeichert.
* Finales Ergebnis wird gespeichert unter: Data/ergebnisse/kneepoint.csv (Komplette Pareto-Optimum Evaluation Nutzen + Privacy) Data/ergebnisse/privacy.csv (Privacy sortiertes Ergebnis mit den sichersten Kombinationen).

---

## Architektur

### Slot-Zuweisung und Lifecycle
Die Zuweisung der First-Party-Domänen $D_{\text{FP}}$ erfolgt deterministisch in N verschiedene parallele Slots mittels eines HMAC-SHA256-Verfahrens:

$$k = \text{HMAC}(\text{LocalSecret}, D_{\text{FP}})$$

Jeder Slot durchläuft einen Zustandsautomaten mit Folgenden Zuständen: FRESH, ACTIVE, WARM, SATURATED
Zur realistischen Abbildung des Surfverhaltens unterscheidet der Algorithmus zwischen zwei Arten des Zurücksetzens:
* **Inaktivität als session_gap:** Nach 30 Minuten Inaktivität werden die Zähler für zeitlich isolierte Segmente zurückgesetzt.
* **Pseudonym-Rotation als rotation_threshold:** Bei Erreichen der Schwellenwerte erfolgt zusätzlich die Löschung des internen Speicherzustands sowie die Freigabe des Slots mit release_slot.

### Angreifermodell und Pareto-Optimierung
Die Evaluierung zwischen Privatsphäre-Schutz und Systemnutzen erfolgt über einen Parameter-Sweep bezüglich der Slot-Anzahl ($N$), der Domänen max_domains und der Events max_events. Jede Konfiguration durchläuft die Pseudonym-Rotation und wird über Einzelmetriken bewertet:

**Re-Identifikationsrisiko ($k$-NN-Angreifer):** Jedes Segment wird als $L_2$-normierter Vektor abgebildet und über eine vektorisierte k-NN-Klassifikation ($k \in \{1, 3, 5, 10, 20\}$) gegen die ungeschützte Baseline-Matrix aller 2.148 Nutzer getestet. Daraus wird der durchschnittliche `Privacy_Score_Avg` gebildet:

**Kosinus-Ähnlichkeit:**

Misst die Verhaltensähnlichkeit zwischen aufeinanderfolgenden Segmenten desselben Nutzers.

$$\cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\|_2 \cdot \|\mathbf{B}\|_2}$$

**k-NN Accuracy:**

Berechnet ob ein Angreifer ein rotiertes Pseudonym dem ursprünglichen Langzeitprofil zu einem der 2.148 Nutzern zuzuordnen kann.

$$\text{Accuracy}_k = \frac{\text{Korrekt zugeordnete Segmente in Top-}k}{\text{Gesamtzahl aller evaluierten Segmente}}$$

$$\text{Accuracy}_{\text{Avg}} = \frac{1}{5} \sum_{k \in \{1,3,5,10,20\}} \text{Accuracy}_k$$

**Min-Max-Normalisierung:**

$$X_{\text{norm}} = \frac{X - X_{\min}}{X_{\max} - X_{\min}}$$

**Privacy Score:**

Kombiniert den Schutz vor Re-Identifikation und den Schutz vor Verkettung zu jeweils 50 %.

$$\text{PrivacyScore}_k = 0.5 \cdot (1 - X_{\text{norm}}(\text{Accuracy}_k)) + 0.5 \cdot (1 - X_{\text{norm}}(\text{MeanCosine}))$$

$$\text{PrivacyScore}_{\text{Avg}} = \frac{1}{5} \sum_{k \in \{1,3,5,10,20\}} \text{PrivacyScore}_k$$


### Utility, Pareto-Optimierung und Knepoint-Analyse

Der Utility_Score sowie die Bestimmung des optimalen Kompromisses zwischen Datenschutz und Nutzen als Pareto-Kniepunkt erfolgen über folgende Formeln:


**Avg_Utility_ThirdParty:**

Misst die Anzahl an beobachteten Tracker-Interaktionen pro Segment. Hier ist $M$ die Gesamtzahl aller Segmente und $E_{\text{TP}, m}$ die Anzahl der Third-Party-Events im Segment $m$:

$$\text{AvgUtility} = \frac{1}{M} \sum_{m=1}^{M} E_{\text{TP}, m}$$

**Total_Resets:**

$$\text{TotalResets} = \sum_{n=1}^{N} R_n$$

**Utility-Score als scoring.py**

$$\text{UtilityScore} = 0.5 \cdot X_{\text{norm}}(\text{AvgUtility}) + 0.5 \cdot (1 - X_{\text{norm}}(\text{TotalResets}))$$

**Chord Distance:**

Das Pareto-Optimum wird die Sekante gesucht zwischen den beiden Extrempunkten ($P_1$ für max.Utility, $P_2$ für max. Datenschutz). Der senkrechte Abstand zu Geraden berchnet sich wie folgt:

$$d_{\text{chord}}(P) = \frac{(p_2 - p_1)u_0 - (u_2 - u_1)p_0 + u_2 p_1 - p_2 u_1}{\sqrt{(p_2 - p_1)^2 + (u_2 - u_1)^2}}$$

Der Kneepoint ($P_{\text{knee}}$) ist die Konfiguration, die diesen Abstand maximiert:

$$P_{\text{knee}} = \arg\max_{P \in \mathcal{P}} d_{\text{chord}}(P)$$

**Epsilon-Plateau**

Minimale Abweichunen sorgen zu keiner Verschlechterung des Systems, deshalb wird ein Toleranz-Plateu mit $\varepsilon = 0{,}005$ Abweichung definiert. Eine Konfiguration gehört zu Plateu wenn der Wert nicht mehr als diese Toleranz abweicht.

---

## KI-Nutzung
Zur Unterstützung der Implementierung, Strukturierung und Syntax-Optimierung der Simulationspipeline wurden KI-gestützte Programmierassistenten eingesetzt.
