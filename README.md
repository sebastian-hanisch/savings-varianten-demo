# Savings variieren – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-savings-varianten-demo.streamlit.app/)** -->

Fünftes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt; Stück 2 ([riesentouren-erzeugen-demo](https://github.com/sebastian-hanisch/riesentouren-erzeugen-demo)) baut solche Reihenfolgen, Stück 3 ([split-gegen-fuellen-demo](https://github.com/sebastian-hanisch/split-gegen-fuellen-demo)) vergleicht den Split mit „Füllen bis voll“, Stück 4 ([savings-gegen-split-demo](https://github.com/sebastian-hanisch/savings-gegen-split-demo)) stellt Savings gegen den Split. Dieses Stück dreht an den **Stellschrauben von Savings**: Formparameter, sequentielle Fassung, Reihenfolge der Zusammenlegungen und Mehrfachrechnen.

## Kernfrage

Was bringen die Stellschrauben von Savings, und lohnt es, Savings mehrfach zu rechnen? Die Demo zeigt die Ersparnis mit den Formparametern λ, μ und ν auf einer Instanz (Karte, Kosten über dem λ-Raster, erste abweichende Zusammenlegung gegenüber λ = 1), stellt die parallele und die sequentielle Fassung nebeneinander, misst mit Rauschen und mit Vertauschungen benachbarter Paare, wie empfindlich der Plan gegen die Reihenfolge der Liste ist, rechnet sechs Strategien (ein Lauf, bestes von 9 λ-Werten, bestes von 20 verrauschten Läufen, bestes aus bis zu 45 Läufen, sequentiell, Einfügen nach Split) und fasst Vergleiche über feste Instanzen bis 100 Kunden in Bändern zusammen.

## Modell

Wie in den Stücken 1 bis 4: ein Depot, n Kunden mit ganzzahliger Nachfrage, gleiche Fahrzeuge der Kapazität Q, euklidische Entfernungen; die Kapazität folgt aus der **Auslastung** (aufgerundet Gesamtnachfrage geteilt durch Zielroutenzahl mal Auslastung, mindestens die größte Nachfrage). **Ersparnis:** s(i, j) = d(0,i) + d(0,j) − λ·d(i,j) + μ·|d(0,i) − d(0,j)| + ν·(q_i + q_j)/q̄; λ = 1, μ = ν = 0 ist die Fassung aus Stück 4 (parallel: Paare mit s > 0 in absteigender Ersparnis, Routen am Rand zusammenlegen, wenn die Last passt; Routen dürfen umgedreht werden). **Sequentiell:** eine Route nach der anderen, Start beim fernsten freien Kunden, am Rand der Kunde mit der größten Ersparnis. **Rauschen:** jede Ersparnis mit 1 + ε·U[−1, 1] multipliziert (je Paar unabhängig, Seed der Instanz plus 11). **Bestes von k Läufen:** der billigste Plan. Formeln und Lesehilfe stehen im 📐-Expander der App; die Formparameter sind nach Sekundärquellen übernommen.

## Methodik

- **Kern** (`svv_algorithm.py`): aus Stück 4 kopiert und umbenannt (Split, Hilfsgraph, exakter Löser mit Held–Karp, kürzeste Rundreise); Erzeuger Einfügen nach Split in `svv_construct.py`.
- **Savings** (`svv_savings.py`): aus Stück 4 erweitert um die Ersparnis mit λ, μ und ν, die sequentielle Fassung, Rauschläufe, Vertauschung benachbarter Paare („Kippstellen“) und die Mehrfachlauf-Gitter (neun λ-Werte, 36 Tripel).
- **Fünf Experimente:** ein Parameter (λ-Regler, μ und ν im Expander); parallel gegen sequentiell; wie empfindlich ist die Liste (Rauschen, Kippstellen); Mehrfach rechnen (sechs Strategien auf der Instanz); Bänder über feste Instanzen.
- **Bänder** (`svv_bands.json`, erzeugt von `generate_precomputed.py`): die Instanzen, Referenzen und Kosten von Einfügen nach Split aus Stück 4 (`sgs_bands.json`), nur Zellen mit Referenz: n = 10 und n = 12 (Auslastung 60, 75, 90, 98 %) mit je 80 Instanzen und exaktem Optimum, n = 25, 50, 100 (Auslastung 90 %) mit je 32 Instanzen und der Referenz PyVRP, dazu kurze Routen (n = 50, 8 Zielrouten, Auslastung 90 und 98 %); vier Zellen (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke). Je Instanz alle Läufe: neun λ-Werte parallel und sequentiell, 36 Tripel (λ, μ, ν), je 20 verrauschte Läufe bei vier Rauschstufen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Seeds (Abstand zum Optimum beziehungsweise zur PyVRP-Referenz in Prozent: Median / Mittel / Maximum; „gepaart“ heißt billiger / gleich / teurer auf denselben Instanzen; vier Zellen zusammen), nachgerechnet in `tests/test_claims.py`, `tests/test_bands.py`, `tests/test_algorithm.py` und `tests/test_oracle_variants.py`. Die Zahlen wurden in der Planung mit eigenen Skripten unabhängig vorgerechnet und stimmen überein. Ab 25 Kunden ist die Referenz PyVRP (keine bewiesene Untergrenze).

**Mehrfach rechnen: das Beste von 9 λ-Werten (λ = 0,4 bis 2,0 in Schritten von 0,2, μ = ν = 0) gegen einen Lauf mit λ = 1 und gegen Einfügen nach Split**

| Zelle (n, Auslastung, Zielrouten) | λ = 1 (Median / Mittel / Maximum) | Bestes von 9 λ | Referenz getroffen | gepaart gegen Einfügen nach Split | Einfügen nach Split |
|---|---|---|---|---|---|
| n = 10, 90 %, 3 | 0,2 / 1,8 / 15,0 | **0,0 / 1,0 / 11,1** | 39 von 80 | 20 / 40 / 20 | 0,0 / 1,1 / 10,0 |
| n = 12, 60 %, 3 | 0,7 / 2,0 / 12,0 | **0,2 / 1,1 / 7,4** | 32 von 80 | 36 / 22 / 22 | 0,7 / 1,8 / 15,8 |
| n = 12, 75 %, 3 | 1,0 / 2,3 / 15,6 | **0,0 / 1,3 / 13,1** | 34 von 80 | 35 / 26 / 19 | 0,5 / 1,8 / 11,0 |
| n = 12, 90 %, 3 | 0,8 / 1,7 / 9,9 | **0,0 / 0,9 / 7,9** | 37 von 80 | 32 / 31 / 17 | 0,6 / 1,8 / 15,3 |
| n = 12, 98 %, 3 | 2,0 / 4,8 / 26,6 | **0,5 / 2,1 / 15,9** | 27 von 80 | 36 / 24 / 20 | 1,0 / 2,7 / 15,7 |
| n = 25, 90 %, 3 | 2,4 / 3,1 / 10,7 | **1,4 / 1,9 / 8,0** | – | 24 / 1 / 7 | 3,3 / 5,1 / 18,8 |
| n = 50, 90 %, 3 | 7,7 / 7,7 / 19,7 | **4,8 / 5,2 / 14,5** | – | 26 / 0 / 6 | 8,3 / 9,1 / 17,4 |
| n = 100, 90 %, 3 | 9,2 / 9,7 / 18,2 | **6,7 / 6,8 / 12,5** | – | 30 / 0 / 2 | 11,7 / 13,2 / 24,9 |
| n = 50, 90 %, 8 | 3,3 / 3,6 / 8,4 | **2,9 / 2,9 / 5,7** | – | 28 / 0 / 4 | 5,6 / 6,8 / 17,1 |
| n = 50, 98 %, 8 | 3,4 / 4,2 / 11,7 | **2,3 / 3,0 / 8,5** | – | 30 / 0 / 2 | 6,6 / 7,3 / 15,9 |

| Frage | Befund |
|---|---|
| **λ als Einzelwert** (parallel, μ = ν = 0) | Das beste feste λ (kleinster Median) liegt in allen zehn Zellen zwischen 0,8 und 1,2: 1,0 / 1,0 / 1,2 / 1,0 / 0,8 bei n = 10 und n = 12 (60 / 75 / 90 / 98 %), 1,0 / 1,2 / 1,2 bei n = 25 / 50 / 100, 1,0 / 1,2 bei den kurzen Routen. Weit weg wird es schlechter: n = 12, 90 %: λ = 0,4 / 0,6 / 1,0 / 1,6 / 2,0 mit Median 5,1 / 2,7 / 0,8 / 3,1 / 6,5 % (Optimum getroffen in 1 / 5 / 31 / 4 / 2 von 80). Bei n = 50 liegt das Tal bei 1,2 (Median 7,0 gegen 7,7 % bei λ = 1), bei n = 100 bei 1,2 (8,5 gegen 9,2 %) |
| **Das beste λ ist je Instanz verschieden** | λ = 1 ist unter den neun Werten das beste in 34 von 80 (n = 12, 90 %), 16 von 32 (n = 25), 5 von 32 (n = 50) und 7 von 32 (n = 100); bei n = 100 verteilen sich die übrigen auf 0,8 / 1,2 / 1,4 / 1,6 / 1,8 / 2,0 mit 2 / 6 / 3 / 5 / 6 / 3 Instanzen |
| **Mehrfach rechnen schlägt Einfügen nach Split ab n = 25** | Das Beste von 9 λ-Werten ist billiger in 24 / 26 / 30 von 32 (n = 25 / 50 / 100), der Median des Unterschieds −2,0 / −3,4 / −5,5 %; bei den kurzen Routen 28 und 30 von 32 (−2,7 und −4,0 %). **Bis n = 12 gleichauf** (Median des Unterschieds 0,0 %): Das Beste von 9 ist dort in mehr Paaren billiger als teurer (zum Beispiel 36 / 24 / 20 bei 98 %), trifft aber nur wenig öfter das Optimum (37 gegen 32 von 80 bei 90 %). Savings läuft in Millisekunden, Einfügen nach Split bei n = 100 etwa 10 Sekunden |
| **Verrauschte Läufe, mehrfach gerechnet** (je 20, λ = 1, Rauschen 1 %) | Das Beste von 20 ist im Median **0,2 / 1,2 / 3,6 / 6,9 %** bei n = 12 / 25 / 50 / 100 (n = 12 mit 90 %); gepaart gegen Einfügen nach Split 32 / 32 / 16 (n = 12), 26 / 1 / 5, 27 / 0 / 5 und 30 / 0 / 2 (n = 100). Das ist bei n = 25 und n = 50 besser als das Beste von 9 λ-Werten (1,2 gegen 1,4 % und 3,6 gegen 4,8 %), bei n = 12 und n = 100 gleichauf oder knapp dahinter (0,2 gegen 0,0 % und 6,9 gegen 6,7 %) |
| **Bis zu 45 Läufe** (36 Tripel aus λ ∈ {0,8; 1; 1,2; 1,4}, μ ∈ {0; 0,5; 1}, ν ∈ {0; 0,5; 1} und die 9 λ-Werte) | Bestes im Median **0,0 / 1,2 / 3,3 / 5,2 %** bei n = 12 / 25 / 50 / 100; gepaart gegen Einfügen nach Split 35 / 32 / 13, 26 / 1 / 5, 28 / 0 / 4 und 31 / 0 / 1. Gegenüber dem Besten von 9 λ-Werten liegt das Ergebnis bei n = 50 und n = 100 je 1,5 Prozentpunkte niedriger (3,3 gegen 4,8 %, 5,2 gegen 6,7 %), bei n = 25 0,2 (1,2 gegen 1,4 %); es sind aber 45 statt 9 Läufe, und die Demo trennt nicht, ob μ und ν oder die größere Laufzahl den Unterschied macht |
| **Sequentielle Fassung ist viel schwächer** | Mit λ = 1: Median **4,8 / 4,9 / 12,1 / 17,0 / 21,4 %** bei n = 10 / 12 / 25 / 50 / 100 gegen 0,2 / 0,8 / 2,4 / 7,7 / 9,2 % parallel; gepaart sequentiell billiger / gleich / teurer als parallel: 7 / 19 / 54 (n = 10), 3 / 18 / 59 (n = 12, 90 %), 14 / 20 / 46 (n = 12, 98 %), 2 / 3 / 27 (n = 25), 2 / 0 / 30 (n = 50), 0 / 0 / 32 (n = 100 und kurze Routen bei 90 %). Auch das beste λ je Instanz rettet sie nicht (n = 50: 10,2 gegen 7,7 %; n = 100: 16,2 gegen 9,2 %) |
| **Die Liste ist empfindlich, aber an wenigen Stellen** | Vertauscht man zwei benachbarte Paare der Liste (λ = 1), ändert sich der Plan selten: bei n = 12 im Median in 2 von 65 Vertauschungen (Minimum 0, Maximum 6), bei n = 25 in 3 von 299 (0 bis 7); die größte Kostenänderung durch eine einzelne Vertauschung ist im Median 0,7 / 1,0 % (n = 12 / 25), im Maximum 13,8 / 9,5 %. Multiplikatives Rauschen auf allen Ersparnissen ändert den Plan dagegen fast immer: Anteil der Läufe mit demselben Plan wie ohne Rauschen bei 0,3 % Rauschen 85 / 69 / 38 / 13 %, bei 1 % 63 / 34 / 10 / 1 % (n = 12 / 25 / 50 / 100). Ein einzelner verrauschter Lauf ist bei 1 % im Mittel so gut wie der ohne Rauschen (Median des Mittels n = 50: 7,3 gegen 7,7 %), bei 10 % deutlich schlechter (19,8 %) |
| **Split auf den Plänen anderer λ** | Bei λ = 1 verbessert der Split in diesen Bändern fast nie (Stück 4); bei den neun λ-Werten verbessert er viele Pläne: 137 von 720 (n = 12, 90 %), 67 von 288 (n = 25), 47 von 288 (n = 50), 65 von 288 (n = 100). Savings mit λ ≠ 1 ist also kein Fixpunkt des Splits |
| **Rechenzeit je Lauf** (Größenordnung, eine Messung) | Ein Lauf (λ = 1, ohne Spur) braucht im Median etwa 0,4 ms (n = 12), 1 ms (n = 25), 3 ms (n = 50) und 10 ms (n = 100); neun Läufe also bei n = 100 etwa 0,1 s gegen etwa 10 s für Einfügen nach Split. Nicht festgeschrieben |
| **Kleine Handinstanz** (n = 6, Kapazität 9, Optimum 56,73) | λ = 1: das Paar (1, 2) mit 8,79 steht vor (1, 4) mit 8,78 und blockiert es (Last 7 + 4 > 9): Plan 62,26 (+9,7 %). λ = 0,8: (1, 4) mit 10,23 steht vor (1, 2) mit 10,21: Savings trifft das Optimum 56,73; ebenso die sequentielle Fassung; Einfügen nach Split 58,37. Kosten über λ = 0,4 / 0,6 / 0,8 / 1,0 / 1,2 / 1,4 / 1,6 / 1,8 / 2,0: 58,37 / 58,37 / 56,73 / 62,26 / 64,47 / 64,47 / 70,38 / 70,38 / 63,18. Die Planinstanz aus den Stücken 1 bis 4 (Optimum 44,36) bleibt für λ von 0,4 bis 1,6 beim Optimum und bricht erst bei λ = 2,0 (nur Paare mit s > 0: (3) und (5) bleiben allein, 52,28) |
| **Voreinstellung** (n = 8, zufällig verteilt, Depot in der Mitte, Auslastung 90 %, Seed 0) | Optimum 444,40; Einfügen nach Split trifft es; Savings 459,10 (+3,3 %), kein λ des Rasters ändert das, kein verrauschter Lauf ist besser; die sequentielle Fassung kostet 492,45 (+10,8 %) |

## Ehrliche Grenzen

- Die Aussagen gelten für die gemessenen Größen (10, 12, 25, 50, 100 Kunden), drei Zielrouten (und 8 bei n = 50) und die drei Kartenarten; sie sind keine Aussagen über echte Daten oder andere Zielroutenzahlen.
- Ab 25 Kunden ist die Referenz PyVRP (5 Sekunden, ein Seed), eine gute Lösung und keine bewiesene Untergrenze; nur Zellen mit Referenz sind in den Bändern.
- „Bestes von k Läufen“ nutzt feste Gitter (neun λ-Werte, 36 Tripel, 20 Läufe mit 1 % Rauschen), die nicht an den Instanzen angepasst sind. Das beste feste λ je Zelle ist ein Messwert und kein Verfahren; ein „bestes Tripel“ je Zelle wird nicht berichtet, weil es an denselben Instanzen ausgewählt wäre.
- „Gleichauf“ heißt hier: die Mediane des gepaarten Unterschieds liegen weniger als einen Prozentpunkt auseinander; bis n = 12 ist der Median des Unterschieds 0,0 %, weil viele Paare gleich teuer sind.
- Das Rauschen ist ein eigener einfacher Ansatz (multiplikatives Rauschen auf jeder Ersparnis), nicht die verzerrte Zufallsauswahl von Juan u. a.; μ und ν sowie die Rolle von λ sind nach Sekundärquellen übernommen und nicht an den Originalarbeiten geprüft. Keine Zahl aus der Literatur wird übernommen.
- Es gibt keine Verbesserungsphase nach der Konstruktion; Savings mit Nachbarschaftssuche rechnen die Demos zu VRP-Nachbarschaften und die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/).
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows bei paralleler Last, nicht festgeschrieben.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge, euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.
- „Savings“ meint die Fassung aus Stück 4 (parallel, Routen dürfen umgedreht werden, nur Paare mit positiver Ersparnis) mit der Ersparnis s = d(0,i) + d(0,j) − λ·d(i,j) + μ·|d(0,i) − d(0,j)| + ν·(q_i + q_j)/q̄. Die Formparameter λ (Gaskell, Yellow) sowie μ und ν (Paessens) sind nach Sekundärquellen übernommen, nicht an den Originalarbeiten geprüft.
- „Rauschen“ meint hier den eigenen Ansatz, jede Ersparnis mit 1 + ε·U[−1, 1] zu multiplizieren (je Paar unabhängig); es ist nicht die verzerrte Zufallsauswahl von Juan u. a.

**Grenzen**
- Live rechnet die App bis zu 12 Kunden mit exaktem Optimum. Die Bänder gelten für 10 und 12 Kunden (exaktes Optimum, je 80 feste Instanzen) und für 25, 50 und 100 Kunden (je 32 feste Instanzen, Referenz PyVRP, nicht bewiesen optimal) bei drei Zielrouten sowie für 50 Kunden mit 8 Zielrouten; nur Zellen mit Referenz.
- Die Referenz PyVRP (5 Sekunden, ein Seed) ist eine gute Lösung, keine Untergrenze: Abstände zur Referenz sind keine Abstände zum Optimum.
- „Bestes von k Läufen“ wählt je Instanz den billigsten Plan; das Gitter von λ-Werten, die Rauschstufe und die Zahl der Läufe stehen fest und sind nicht an den Instanzen angepasst. Das beste feste λ je Zelle ist ein Messwert, kein Verfahren.
- Einfügen nach Split rechnet bei 100 Kunden etwa 10 Sekunden je Instanz; seine Kosten stammen aus den Bändern von Stück 4.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über feste Instanzen, keine Trends und keine Aussagen über andere Kartenarten oder Zielroutenzahlen; zu n steht keine Trendaussage in der App.
- Bei großen λ bleiben viele Ersparnisse nicht positiv: Dann bleiben Kunden allein, und der Plan hat mehr Routen.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Prozentzahl der Handinstanz:** Der Plan nannte 62,26 als +9,8 % über dem Optimum; die Rechnung ergibt 9,7 % (62,257 gegen 56,728).
- **Auf dem 0,1-Raster treffen zwei λ das Optimum:** Die Planmessung benutzte das Raster 0,2 (λ = 0,8); die App rechnet die Kurve auf dem feineren Raster 0,2 bis 2,4 in Schritten von 0,1, und λ = 0,8 und 0,9 treffen das Optimum der kleinen Handinstanz.
- **Mehrfach rechnen bis n = 12 nur gleichauf:** Der Plan sprach von einem Gewinn gegen Einfügen nach Split in 26 bis 31 von 32 Instanzen; das gilt ab n = 25 (24, 26, 30 von 32). Bis n = 12 ist das Bild gemischt (36 / 24 / 20 bei 98 %, 20 / 40 / 20 bei n = 10) und der Median des Unterschieds 0,0 %.
- **Gewinner nicht in-sample:** Der Plan nannte das beste Tripel je Zelle; die Demo berichtet nur das beste feste λ (Messwert) und die festen Gitter, weil ein gewähltes Tripel an denselben Instanzen ausgesucht wäre.
- **Rauschen mit 1 % schlägt das λ-Gitter bei n = 25 und 50:** In der Planung stand das Beste von 20 Läufen (1 %) nur neben dem λ-Gitter; die Demo führt es als eigene Strategie, und es liegt bei n = 25 und 50 vor dem Besten von 9 λ-Werten (1,2 gegen 1,4 %, 3,6 gegen 4,8 %), bei n = 12 und 100 nicht.
- **Nicht in der Demo:** Die Planmessung „mehr Parameter bringen mehr als ein feineres λ-Gitter“ (41 statt 9 λ-Werte, n = 50: 4,5 statt 4,8 %) nutzte ein Gitter, das die Bänder nicht speichern; die Demo behauptet es deshalb nicht.
- **Rechenzeit ohne Spur:** Die Mehrfachläufe und die Bänder benutzen `savings_routes` ohne Spur; die Spur (Karte nach jedem Schritt) rechnet nur der λ-Regler.
- **Reihenfolge der Routen und Rauschen:** Das Rauschen wird für alle Paare gezogen, auch die mit s ≤ 0 (so hängt die Zufallsfolge nur von n und dem Seed ab, nicht von λ); die Messung der Planung benutzte dieselbe Ziehung.

## Verifikation

- **Kern:** Savings mit λ = 1 und λ = 0,8 an der kleinen Handinstanz (alle 15 Ersparnisse aus Wurzeln, Ausgang jedes Paares, Pläne, Kosten über das λ-Raster, erste abweichende Zusammenlegung), sequentielle Fassung, μ und ν an einem Paar von Hand, die Planinstanz der Stücke 1 bis 4 über λ, Split, exakter Löser und kürzeste Rundreise aus den Stücken 1 bis 4 (`tests/test_algorithm.py`).
- **Orakel:** Savings mit λ, μ und ν in reinem Python mit anderer Auswahlregel (in jedem Schritt das beste noch zulässige Paar) bei 8 bis 25 Kunden und sechs Parameterwerten; sequentielle Fassung rekursiv noch einmal; Bestes von k Läufen gegen eine eigene Schleife; Rauschläufe gegen eine eigene Ziehung aus demselben Erzeuger; Split und exakter Löser gegen die Aufzählung (`tests/test_oracle_variants.py`).
- **Eigenschaften:** Zulässigkeit aller Varianten, die Zusammenlegung verkürzt um die einfache Ersparnis (bei λ = 1 gleich s), Bestes von k nie schlechter als ein Lauf und nie besser als das Optimum, Rauschen 0 gleich dem Lauf ohne Rauschen, gleicher Seed gleiche Läufe, Rauschen ändert den Plan je stärker desto öfter, eine Route bei Platz für alle und λ ≤ 1, große λ lassen Kunden allein, λ = 0, Verschieben, Skalieren und Umnummerieren, Kippstellen gegen direkte Neurechnung, symmetrische erste Abweichung (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Kunden, sehr großes λ (keine positive Ersparnis), negatives ν, Nachfrage gleich Kapazität, alle Kunden am selben Ort, Kunde auf dem Depot, Gleichstände, größtes Rauschen mit 50 Läufen, Reglergrenzen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau, Stimmigkeit und gegen eine frische Rechnung je Zelle (`tests/test_bands.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), λ-, μ-, ν-, Rausch- und Laufzahl-Regler, Planauswahl, Bänder inklusive kurzer Routen, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

259 Tests. Laufzeit lokal etwa eine Minute.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `svv_bands.json` aus den Instanzen und Referenzen von Stück 4 (Teile lassen sich parallel rechnen) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `svv_algorithm.py` | Kern: Split, Hilfsgraph, exakter Löser, Held–Karp, kürzeste Rundreise |
| `svv_bands.json` | vorberechnete Bänder (Größen, Auslastungen, kurze Routen; je vier Zellen) |
| `svv_constants.py` | Regler-Grenzen, Strategien, Bänder, Farben, Presets, Annahmentext |
| `svv_construct.py` | Einfügen nach Split und fernstes Einfügen |
| `svv_evaluation.py` | Analyse, Strategien, Bänder, Kennzahlen, Verdikt-Logik |
| `svv_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `svv_pdf_export.py` | PDF-Export des Ergebnisses |
| `svv_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `svv_savings.py` | Savings mit Formparametern und Spur, sequentielle Fassung, Rauschläufe, Kippstellen |
| `svv_scenario.py` | Instanzen (aus Stück 1, mit Auslastung als Parameter) |
| `svv_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanzen, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Verbesserungsphase** (Nachbarschaftssuche, Split auf jedem Plan): Savings bleibt Konstruktion; der Split auf den Plänen steht nur als Zahl in den Bändern.
- **Parameter lernen** (genetischer Algorithmus, Battarra u. a.): hier nur feste Gitter.
- **Verzerrte Zufallsauswahl** (Juan u. a.): das Rauschen ist ein eigener einfacher Ansatz.
- **Sweep und Cluster-first** (Stück 6); die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet beide.
- **Zeitfenster** (Stück 8): Zusammenlegen braucht dann eine Zeitprüfung, die Ersparnis allein genügt nicht.
- **Suche über Reihenfolgen** (Stück 11): Mehrfachlauf ist ein Mehrfachstart ohne Lernen.
- **Asymmetrische Entfernungen und verschiedene Fahrzeugtypen:** nur symmetrische Entfernungen und gleiche Fahrzeuge.
- **Instanzen über 12 Kunden live:** größere Instanzen stehen nur in den vorberechneten Bändern.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
