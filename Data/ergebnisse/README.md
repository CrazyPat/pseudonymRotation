# Ergebnisdateien

Erklärt die Spalten der Ergebnis-CSVs. Wie die Dateien entstehen, steht im [README des Projekts](../../README.md).

## Spalten in `sweep_trigger_analyse.csv`

Jede Zeile ist eine Konfiguration. Ein Segment entspricht einem Pseudonym von seiner Vergabe bis zu seinem Abschluss. Die Spalten mit `_Pct` sind hier, anders als in `verkettungs_ranking.csv`, bereits mit 100 multipliziert.

| Spalte | Bedeutung |
|---|---|
| `Slots`, `Max_Domains`, `Max_Events`, `Max_Days` | Parameter der Konfiguration |
| `Segments` | Anzahl aller Segmente über alle Nutzer |
| `Median_Age_Days` | Medianes Alter eines Pseudonyms bei der Rotation in Tagen, nur für Segmente, die durch eine Schwelle rotiert wurden |
| `Avg_Overshoot` | Durchschnittliche Überschreitung der Schwelle bei der Rotation. Events werden durch den Rotation-Lock überschritten, Tage zählen in ganzen Tagen (abgerundet), die Domaingrenze wird nie überschritten. Da der Mittelwert über alle rotierten Segmente gebildet wird, mischt er diese Einheiten. |
| `Max_Overshoot` | Größte Überschreitung einer Schwelle |
| `Avg_Domains_Per_Segment` | Durchschnittliche Anzahl unterschiedlicher Domains pro Segment |
| `Domain_Limit_Fill_Pct` | Durchschnittliche Ausschöpfung der Domaingrenze, also Domains pro Segment geteilt durch `Max_Domains` |
| `Used_Slots_Pct` | Durchschnittlicher Anteil der Slots, die ein Nutzer überhaupt belegt |
| `Single_Domain_Segments_Pct` | Anteil der Segmente mit genau einer Domain |
| `Single_Domain_Visits_Pct` | Anteil der Aufrufe, die in Segmenten mit genau einer Domain liegen |
| `Trigger_Distribution` | Anteil der Segmente je Abschlussgrund als Wert zwischen 0 und 1: `Days`, `Events`, `Domains` = Rotation durch die jeweilige Schwelle, `expired` = Schwelle am Datenende bereits erreicht, `end_of_stream` = am Datenende noch offen |

## Spalten in `verkettungs_ranking.csv`

Jede Zeile ist eine Konfiguration. Alle Kennzahlen gibt es zweimal: mit `Incl_` für alle Segmente und mit `Excl_` ohne die am Datenende offenen Segmente (`end_of_stream`). Anteile sind als Werte zwischen 0 und 1 gespeichert. `variance_check_ranking.csv` hat dieselben Spalten, zusätzlich `Run_Seed` sowie `INCL (%)` und `EXCL (%)`.

| Spalte | Bedeutung |
|---|---|
| `Anzahl_Slots`, `Max_Domains`, `Max_Events`, `Max_Days` | Parameter der Konfiguration |
| `Identification_Rate` | Anteil der Segmente, deren ähnlichstes Segment vom selben Nutzer stammt. Die höchste Ähnlichkeit zu einem eigenen Segment muss größer als 0 und echt größer als zu jedem fremden Segment sein, ein Gleichstand zählt als Fehlschlag. |
| `Avg_Max_Cosine_Own` | Durchschnittlich höchste Kosinus-Ähnlichkeit zu einem eigenen Segment |
| `Avg_Max_Cosine_Other` | Durchschnittlich höchste Kosinus-Ähnlichkeit zu einem fremden Segment |
| `Avg_Chord_Distance` | Durchschnittliche Chord Distance zum ähnlichsten eigenen Segment, wird berechnet, aber nicht ausgewertet |
| `Valid_Segments` | Anzahl der ausgewerteten Segmente |
| `Share_Single_Segment_Users` | Anteil der Nutzer mit nur einem Segment, die nicht verkettet werden können |
| `Tie_Share` | Anteil der Segmente mit Gleichstand zwischen eigenem und fremdem Segment, zählt als Fehlschlag |
| `No_Own_Share` | Anteil der Segmente ohne gemeinsame Domain mit einem eigenen Segment (auch Segmente von Nutzern mit nur einem Segment) |
| `Tie_Single_Domain_Share` | Anteil der Gleichstände, bei denen das Segment nur eine Domain enthält |
| `Random_Baseline` | Erwartete Rate, wenn der Angreifer zufällig ein anderes Segment wählt |
| `Users_Linked_Share` | Anteil der Nutzer mit mindestens einem korrekt verketteten Segment |
| `Visit_Weighted_Rate` | Identification-Rate, gewichtet nach der Anzahl der Aufrufe im Segment |
