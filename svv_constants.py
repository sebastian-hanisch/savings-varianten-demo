"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 12, 8
SEED_MAX, DEFAULT_SEED = 999999, 0
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL_MIN, FILL_MAX, FILL_STEP, DEFAULT_FILL = 60, 100, 2, 90   # Auslastung in Prozent: Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl · Auslastung)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)")
FAMILY_KEYS = ("small", "random", "clustered")
DEFAULT_FAMILY = 1
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0

# Strategien der Mehrfachrechnung (Experiment 4 und Bänder): Schlüssel, Namen, Zahl der Läufe
STRATEGY_KEYS = ("std", "lam9", "noise20", "grid45", "seq", "es")
STRATEGY_NAMES = {
    "std": "Savings, λ = 1 (ein Lauf)",
    "lam9": "Bestes von 9 λ-Werten",
    "noise20": "Bestes von 20 verrauschten Läufen (1 %)",
    "grid45": "Bestes aus bis zu 45 Läufen (λ, μ, ν)",
    "seq": "Sequentiell, λ = 1",
    "es": "Einfügen nach Split",
}
STRATEGY_RUNS = {"std": 1, "lam9": 9, "noise20": 20, "grid45": 45, "seq": 1, "es": 1}
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
TIE = 1e-12                                   # Beim Einfügen zählt ein Kandidat nur als besser, wenn er um mehr als TIE besser ist
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt
LEVEL_PP = 1.0                                # „gleichauf“: Unterschied der Mediane unter einem Prozentpunkt

# Regler der Experimente (im Hauptbereich)
LAM_MIN, LAM_MAX, LAM_STEP, DEFAULT_LAM = 0.2, 2.4, 0.1, 1.0
MU_MIN, MU_MAX, DEFAULT_MU = 0.0, 2.0, 0.0
NU_MIN, NU_MAX, DEFAULT_NU = -1.0, 1.0, 0.0
EPS_MIN, EPS_MAX, EPS_STEP, DEFAULT_EPS = 0.0, 10.0, 0.1, 1.0       # Rauschen in Prozent
RUNS_MIN, RUNS_MAX, RUNS_STEP, DEFAULT_RUNS = 5, 50, 5, 20
LAM_CURVE = tuple(round(LAM_MIN + LAM_STEP * k, 1) for k in range(int(round((LAM_MAX - LAM_MIN) / LAM_STEP)) + 1))   # Raster der Kostenkurve in Experiment 1

# Bänder (vorberechnet, svv_bands.json): feste Instanzen der Stück-4-Demo, vier Zellen (Kunden zufällig/Gruppen mal Depot Mitte/Ecke), nur Zellen mit Referenz
BAND_FILE = "svv_bands.json"
BAND_SIZES = (10, 12, 25, 50, 100)
BAND_FILLS = {10: (90,), 12: (60, 75, 90, 98), 25: (90,), 50: (90,), 100: (90,)}
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))
BAND_ROUTES = 3
SHORT_N, SHORT_ROUTES, SHORT_FILLS = 50, 8, (90, 98)     # kurze Routen: 50 Kunden, 8 Zielrouten
EXACT_SIZES = (10, 12)                        # Referenz = exaktes Optimum; sonst PyVRP (5 s, ein Seed)
BAND_SEEDS = {10: tuple(range(300000, 300020)), 12: tuple(range(300000, 300020)), 25: tuple(range(300000, 300008)), 50: tuple(range(300000, 300008)), 100: tuple(range(300000, 300008))}
BAND_NOISE = (0.003, 0.01, 0.03, 0.1)         # Rauschstufen in den Bändern (je 20 Läufe)
SOURCE_BANDS_FILE = "sgs_bands.json"          # Quelle der Referenzen und der Kosten von Einfügen nach Split (savings-gegen-split-demo, Stück 4)

COLOR_SAVINGS = "#2F6B65"
COLOR_SPLIT = "#d8a13a"
COLOR_OPT = "#c0504d"
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")
STRATEGY_COLORS = {"std": "#2F6B65", "lam9": "#4c78a8", "noise20": "#7b5ea7", "grid45": "#17becf", "seq": "#999999", "es": "#d8a13a"}

# Presets (Instanzen aus der Suche; die Zahlen in den Hilfetexten prüft tests/test_claims.py)
PRESETS = {
    "Einfügen nach Split gewinnt (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 0},
    "Ein kleineres λ trifft das Optimum (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 42},
    "λ oder Rauschen finden das Optimum (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 39},
    "Sequentiell trifft, parallel nicht (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 21},
    "Savings trifft das Optimum bei vielen λ (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 47},
    "Zwei Paare vertauschen die Plätze (n = 6)": {"n": 6, "family": 0, "depot": 0, "routes": 2, "fill": 90, "seed": 7},
}
PRESET_HELP = {
    "Einfügen nach Split gewinnt (n = 8)": "Einfügen nach Split trifft das Optimum 444,40; Savings liegt 3,3 % darüber, und kein λ des Rasters (0,2 bis 2,4) trifft das Optimum. Die sequentielle Fassung kostet 492,45 (+10,8 %).",
    "Ein kleineres λ trifft das Optimum (n = 8)": "Savings mit λ = 1 liegt 5,0 % über dem Optimum 413,58; die Raster-Werte λ = 0,4 und 0,5 treffen es, ebenso Einfügen nach Split.",
    "λ oder Rauschen finden das Optimum (n = 8)": "Savings mit λ = 1 liegt 2,2 % über dem Optimum 323,39; λ = 1,1 und 1,2 treffen es, und das Beste von 20 verrauschten Läufen (1 %) auch.",
    "Sequentiell trifft, parallel nicht (n = 8)": "Die sequentielle Fassung trifft das Optimum 392,33; die parallele mit λ = 1 liegt 10,0 % darüber, und kein λ des Rasters ändert das.",
    "Savings trifft das Optimum bei vielen λ (n = 8)": "Savings trifft das Optimum 338,50 bei jedem λ von 0,3 bis 1,0; Einfügen nach Split liegt 10,4 % darüber, die sequentielle Fassung 18,5 %.",
    "Zwei Paare vertauschen die Plätze (n = 6)": "Optimum 56,73. Bei λ = 1 steht das Paar (1, 2) mit 8,79 vor (1, 4) mit 8,78 und blockiert es: 62,26 (+9,7 %). Bei λ = 0,8 steht (1, 4) mit 10,23 vor (1, 2) mit 10,21: Savings trifft das Optimum.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
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
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft."""
