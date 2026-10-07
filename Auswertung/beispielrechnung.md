# Beispielrechnung zur Verkettung

Vollständige Rechnung zum vereinfachten Beispiel aus Abschnitt 4.4 der Arbeit.

## Ausgangsdaten

| Segment | facebook.com | google.com | modellbahn.de |
|---|---|---|---|
| P1 (Nutzer A, vor Rotation) | 5 | 0 | 3 |
| P2 (Nutzer A, nach Rotation) | 4 | 0 | 2 |
| P3 (Nutzer B) | 6 | 2 | 0 |
| P4 (Nutzer C) | 3 | 4 | 0 |

## 1. Sublineare TF-Skalierung

Jede Häufigkeit $c > 0$ wird logarithmisch gedämpft, Nullen bleiben null:

$$tf = 1 + \ln(c)$$

Mit $\ln 2 = 0{,}6931$, $\ln 3 = 1{,}0986$, $\ln 4 = 1{,}3863$, $\ln 5 = 1{,}6094$ und $\ln 6 = 1{,}7918$ ergibt sich:

| Segment | facebook.com | google.com | modellbahn.de |
|---|---|---|---|
| P1 | $1 + \ln 5 = 2{,}6094$ | 0 | $1 + \ln 3 = 2{,}0986$ |
| P2 | $1 + \ln 4 = 2{,}3863$ | 0 | $1 + \ln 2 = 1{,}6931$ |
| P3 | $1 + \ln 6 = 2{,}7918$ | $1 + \ln 2 = 1{,}6931$ | 0 |
| P4 | $1 + \ln 3 = 2{,}0986$ | $1 + \ln 4 = 2{,}3863$ | 0 |

## 2. IDF-Gewicht nach der Gleichung 4.1

$$idf(t) = \ln\frac{1 + n}{1 + df(t)} + 1$$

Es gibt $n = 4$ Segmente. facebook.com kommt in allen vier vor, google.com und modellbahn.de jeweils in zwei:

$$idf(\text{facebook.com}) = \ln\frac{5}{5} + 1 = 0 + 1 = 1{,}0000$$

$$idf(\text{google.com}) = idf(\text{modellbahn.de}) = \ln\frac{5}{3} + 1 = 0{,}5108 + 1 = 1{,}5108$$

## 3. TF-IDF-Gewichtung

Jeder TF-Wert wird mit dem IDF-Gewicht seiner Domain multipliziert:

| Segment | facebook.com | google.com | modellbahn.de |
|---|---|---|---|
| P1 | $2{,}6094 \cdot 1 = 2{,}6094$ | 0 | $2{,}0986 \cdot 1{,}5108 = 3{,}1706$ |
| P2 | $2{,}3863 \cdot 1 = 2{,}3863$ | 0 | $1{,}6931 \cdot 1{,}5108 = 2{,}5581$ |
| P3 | $2{,}7918 \cdot 1 = 2{,}7918$ | $1{,}6931 \cdot 1{,}5108 = 2{,}5581$ | 0 |
| P4 | $2{,}0986 \cdot 1 = 2{,}0986$ | $2{,}3863 \cdot 1{,}5108 = 3{,}6053$ | 0 |

## 4. L2-Normalisierung

Jeder Vektor wird durch seine Länge $\lVert P \rVert = \sqrt{\sum_t w_t^2}$ geteilt:

$$\lVert P_1 \rVert = \sqrt{2{,}6094^2 + 3{,}1706^2} = \sqrt{6{,}8092 + 10{,}0529} = \sqrt{16{,}8621} = 4{,}1063$$

$$\lVert P_2 \rVert = \sqrt{2{,}3863^2 + 2{,}5581^2} = \sqrt{5{,}6944 + 6{,}5436} = \sqrt{12{,}2380} = 3{,}4983$$

$$\lVert P_3 \rVert = \sqrt{2{,}7918^2 + 2{,}5581^2} = \sqrt{7{,}7939 + 6{,}5436} = \sqrt{14{,}3375} = 3{,}7865$$

$$\lVert P_4 \rVert = \sqrt{2{,}0986^2 + 3{,}6053^2} = \sqrt{4{,}4042 + 12{,}9980} = \sqrt{17{,}4022} = 4{,}1716$$

Damit ergeben sich die normierten Vektoren (für Tabelle (4.5)):

| Segment | facebook.com | google.com | modellbahn.de |
|---|---|---|---|
| P1 | $2{,}6094 / 4{,}1063 = 0{,}6355$ | 0 | $3{,}1706 / 4{,}1063 = 0{,}7721$ |
| P2 | $2{,}3863 / 3{,}4983 = 0{,}6821$ | 0 | $2{,}5581 / 3{,}4983 = 0{,}7312$ |
| P3 | $2{,}7918 / 3{,}7865 = 0{,}7373$ | $2{,}5581 / 3{,}7865 = 0{,}6756$ | 0 |
| P4 | $2{,}0986 / 4{,}1716 = 0{,}5031$ | $3{,}6053 / 4{,}1716 = 0{,}8642$ | 0 |

## 5. Kosinus-Ähnlichkeit nach Gleichung 4.2

Vektoren sind normiert,  deshalb entspricht die Kosinus-Ähnlichkeit dem Skalarprodukt:

$$sim_{cos}(P_1, P_2) = 0{,}6355 \cdot 0{,}6821 + 0 \cdot 0 + 0{,}7721 \cdot 0{,}7312 = 0{,}4335 + 0{,}5646 = 0{,}9981$$

$$sim_{cos}(P_1, P_3) = 0{,}6355 \cdot 0{,}7373 + 0 \cdot 0{,}6756 + 0{,}7721 \cdot 0 = 0{,}4685$$

$$sim_{cos}(P_1, P_4) = 0{,}6355 \cdot 0{,}5031 + 0 \cdot 0{,}8642 + 0{,}7721 \cdot 0 = 0{,}3197$$

Zwischen P1 und den fremden Segmenten trägt nur facebook.com bei. Zwischen P1 und P2 kommt zusätzlich modellbahn.de mit dem höheren IDF-Gewicht hinzu.

## 6. Verkettungsentscheidung nach Gleichung 4.3

$$\max(sim_{own}(P_1)) = 0{,}9981 > \max(sim_{other}(P_1)) = \max(0{,}4685;\ 0{,}3197) = 0{,}4685$$

Da die höchste Ähnlichkeit zu einem eigenen Segment größer ist als zu jedem fremden und größer als 0, gilt der Verkettungsversuch für P1 als erfolgreich. P1 und P2 werden demselben Nutzer zugeordnet, obwohl zwischen beiden eine Rotation stattgefunden hat.
