"""Savings variieren - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 5 der Reihe „Tourenbildung“: Savings (Clarke und Wright, Stück 4) hat Stellschrauben: den Formparameter λ (mit μ und ν), die sequentielle statt der parallelen Fassung und die Reihenfolge der
Zusammenlegungen. Die Demo zeigt, was sie bringen, wie empfindlich der Plan gegen kleine Änderungen der Liste ist und ob sich Mehrfachrechnen lohnt, live bis 12 Kunden gegen das exakte Optimum und in
vorberechneten Bändern bis 100 Kunden.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import svv_algorithm as A
import svv_constants as C
import svv_savings as S
from svv_evaluation import (
    Settings,
    analyse,
    band_rows,
    band_stats,
    build_instance,
    de,
    diff_percent,
    first_difference,
    gap_percent,
    instances_word,
    noise_study,
    order_text,
    params_text,
    pct,
    routes_text,
    routes_word,
    signed_pct,
    swap_info,
    verdict_bands,
    verdict_lambda,
    verdict_noise,
    verdict_noise_bands,
    verdict_sequential,
    verdict_strategies,
    verdict_swaps,
)
from svv_layout import dunkles_design, kopf_css
from svv_pdf_export import build_pdf
from svv_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from svv_visualization import build_band_curve, build_bands, build_lambda_curve, build_map, build_noise_strip

st.set_page_config(page_title="Savings variieren – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _variant(settings, params):
    inst = build_instance(settings)
    return S.savings(inst, params), S.savings(inst, S.STANDARD), S.savings_sequential(inst, params)


@st.cache_data(show_spinner=False)
def _noise(settings, params, eps, k):
    return noise_study(settings, params, eps, k)


@st.cache_data(show_spinner=False)
def _swaps(settings, params):
    return swap_info(settings, params)


@st.cache_data(show_spinner=False)
def _band_stats(n, fill, routes):
    return band_stats(band_rows(n, fill, routes))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in svv_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎛️ Savings variieren")
st.markdown(
    """
**Was bringen die Stellschrauben von Savings?** Savings (Stück 4) legt Einzelrouten nach absteigender **Ersparnis** zusammen. Daran lässt sich drehen: ein **Formparameter λ** gewichtet die Strecke zwischen den Kunden
(dazu μ und ν), die **sequentielle Fassung** baut eine Route nach der anderen, und die **Reihenfolge der Zusammenlegungen** entscheidet den Plan an wenigen Stellen. Die Demo zeigt, wie empfindlich der Plan ist,
und fragt, ob es sich lohnt, Savings mehrfach zu rechnen: Es ist so billig, dass neun oder zwanzig Läufe weniger kosten als ein Lauf von Einfügen nach Split.

Weiter unten: **🔬 Ein Parameter: λ**, **🔬 Parallel gegen sequentiell**, **🔬 Wie empfindlich ist die Liste?**, **🔬 Mehrfach rechnen**, **🔬 Wie schlagen sich die Strategien?**,
**🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So lässt sich Savings variieren", expanded=True):
    st.markdown(
        """
1. **Ersparnis:** *s(i, j) = d(0,i) + d(0,j) − λ·d(i,j) + μ·|d(0,i) − d(0,j)| + ν·(q_i + q_j)/q̄*. Mit *λ = 1, μ = ν = 0* ist es die Ersparnis aus Stück 4. Größeres λ bestraft lange Strecken zwischen den Kunden stärker, μ bevorzugt Paare mit ungleicher Entfernung zum Depot, ν Paare mit großer Nachfrage.
2. **Parallel:** Alle Paare mit *s > 0*, größte zuerst; ein Paar legt zwei Routen zusammen, wenn beide Kunden am Rand ihrer Routen stehen und die Last passt (Stück 4). **Sequentiell:** eine Route nach der anderen, jeweils mit dem Kunden mit der größten Ersparnis am Rand fortsetzen.
3. **Rauschen:** Jede Ersparnis mit *1 + ε·U[−1, 1]* multiplizieren und mehrfach rechnen; das ändert die Reihenfolge der Paare in der Liste.
4. **Mehrfach rechnen:** das Beste von k Läufen, wobei k Läufe zusammen weniger kosten als ein Lauf von Einfügen nach Split.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.N_MAX} rechnet die App das exakte Optimum. Größere Instanzen stehen in den vorberechneten Bändern.")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt zusammen mit der Auslastung die Kapazität fest.")
    fill = st.slider("Auslastung (%)", *bounds("fill_slider"), step=C.FILL_STEP, key="fill_slider",
                     help="Kapazität = aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung). Bei hoher Auslastung ist die Kapazität knapp.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed bestimmt auch die Zufallszahlen der verrauschten Läufe.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "fill_slider": int(fill), "seed_input": int(seed)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(fill), int(seed))
a = _analysis(settings)
inst = a.inst
plans = a.strategies

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: ein Lauf, neun Läufe oder Einfügen nach Split")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Optimum (alle Tourenpläne)", de(a.exact.cost), delta="Referenz", delta_color="off")
m2.metric("Savings, λ = 1", de(plans["std"].cost), delta=f"{round(plans['std'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m3.metric("Bestes von 9 λ-Werten", de(plans["lam9"].cost), delta=f"{round(plans['lam9'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m4.metric("Einfügen nach Split", de(plans["es"].cost), delta=f"{round(plans['es'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
st.caption(f"Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}, Mindestroutenzahl {a.min_routes}. Das Optimum fährt {routes_word(len(a.exact.routes))}, Savings mit λ = 1 {routes_word(len(plans['std'].routes))}, "
           f"das Beste von 9 λ-Werten {routes_word(len(plans['lam9'].routes))}, Einfügen nach Split {routes_word(len(plans['es'].routes))}.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="savings-variieren.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Lohnt es, Savings zu variieren und mehrfach zu rechnen?")
kind, text = verdict_strategies(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Ein Parameter: λ")
st.caption("Der Regler setzt den Formparameter λ der Ersparnis; μ und ν stehen im Expander darunter. Die Karte zeigt den Plan, die Kurve die Kosten für alle λ des Rasters (μ = ν = 0, parallel und sequentiell).")
lam = st.slider("Formparameter λ", C.LAM_MIN, C.LAM_MAX, C.DEFAULT_LAM, C.LAM_STEP, key="lam_slider", format="%.1f")
with st.expander("Weitere Formparameter μ und ν"):
    mu = st.slider("μ (Paare mit ungleicher Entfernung zum Depot)", C.MU_MIN, C.MU_MAX, C.DEFAULT_MU, 0.1, key="mu_slider", format="%.1f")
    nu = st.slider("ν (Paare mit großer Nachfrage)", C.NU_MIN, C.NU_MAX, C.DEFAULT_NU, 0.1, key="nu_slider", format="%.1f")
params = S.Params(round(float(lam), 1), round(float(mu), 1), round(float(nu), 1))
result, base, sequential = _variant(settings, params)
t1, t2 = st.columns([1, 1])
with t1:
    st.markdown(f"**{params_text(params)}: {de(A.plan_length(inst, result.routes))}** ({routes_word(len(result.routes))})")
    st.plotly_chart(build_map(inst, result.routes), width="stretch", key="map_lambda")
with t2:
    st.plotly_chart(build_lambda_curve(a.curve_par, a.curve_seq, params.lam if params.mu == 0 and params.nu == 0 else None, a.exact.cost, plans["es"].cost), width="stretch", key="lambda_curve")
kind, text = verdict_lambda(a, params, result, base)
getattr(st, kind)(text)
diff = first_difference(base, result)
if params != S.STANDARD:
    if diff is None:
        st.caption("Die Zusammenlegungen sind dieselben wie bei λ = 1, μ = ν = 0 (gleiche Paare in gleicher Folge).")
    else:
        def _cell(step):
            return "–" if step is None else f"Paar {step.i}, {step.j} (Platz {step.rank}, s = {de(step.saving)})"
        st.markdown(f"**Die erste abweichende Zusammenlegung** (die {diff['merge_no']}. von {max(base.merges, result.merges)}):")
        st.markdown("\n".join(["| | Zusammenlegung |", "|---|---|", f"| **λ = 1, μ = ν = 0** | {_cell(diff['base'])} |", f"| **{params_text(params)}** | {_cell(diff['other'])} |"]))

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Parallel gegen sequentiell")
st.caption("Dieselbe Ersparnis (die Parameter von oben), zwei Wege: parallel arbeitet die ganze Liste der Paare ab, sequentiell baut eine Route nach der anderen und setzt sie am Rand mit dem besten Kunden fort.")
q1, q2 = st.columns(2)
for col, title, routes_, key in ((q1, "Parallel", result.routes, "map_par"), (q2, "Sequentiell", sequential, "map_seq")):
    with col:
        st.markdown(f"**{title}: {de(A.plan_length(inst, routes_))}** ({routes_word(len(routes_))}, {pct(gap_percent(A.plan_length(inst, routes_), a.exact.cost))} über dem Optimum)")
        st.plotly_chart(build_map(inst, routes_), width="stretch", key=key)
kind, text = verdict_sequential(a, params, result.routes, sequential)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie empfindlich ist die Liste?")
st.caption("Savings hängt an der Reihenfolge der Paare in der Liste. Hier wird jede Ersparnis mit 1 + ε·U[−1, 1] multipliziert (ε in Prozent, die Parameter von oben) und k-mal gerechnet; darunter die Kippstellen, an denen "
           "schon das Vertauschen zweier benachbarter Paare den Plan ändert.")
e1, e2 = st.columns(2)
with e1:
    eps = st.slider("Rauschen ε (%)", C.EPS_MIN, C.EPS_MAX, C.DEFAULT_EPS, C.EPS_STEP, key="eps_slider", format="%.1f")
with e2:
    k_runs = st.slider("Zahl der Läufe k", C.RUNS_MIN, C.RUNS_MAX, C.DEFAULT_RUNS, C.RUNS_STEP, key="runs_slider")
study = _noise(settings, params, round(float(eps), 1), int(k_runs))
n1, n2 = st.columns([1, 1])
with n1:
    st.plotly_chart(build_noise_strip(study["costs"], study["base_cost"], a.exact.cost, plans["es"].cost), width="stretch", key="noise_strip")
with n2:
    st.markdown(f"**Bester von {int(k_runs)}: {de(study['best'])}** ({pct(gap_percent(study['best'], a.exact.cost))} über dem Optimum)")
    st.plotly_chart(build_map(inst, study["best_routes"]), width="stretch", key="map_noise")
kind, text = verdict_noise(study)
getattr(st, kind)(text)
swaps = _swaps(settings, params)
kind, text = verdict_swaps(swaps, A.plan_length(inst, result.routes))
getattr(st, kind)(text)
if swaps["changed"]:
    rows = ["| Plätze | Paar vorn | Paar hinten | Kostenänderung |", "|---|---|---|---|"]
    for r in sorted(swaps["changed"], key=lambda r: -abs(r["change_pct"]))[:6]:
        rows.append(f"| {r['rank']} und {r['rank'] + 1} | {r['first'][1]}, {r['first'][2]} (s = {de(r['first'][0])}) | {r['second'][1]}, {r['second'][2]} (s = {de(r['second'][0])}) | {signed_pct(r['change_pct'])} |")
    st.markdown("**Kippstellen** (die sechs mit der größten Kostenänderung)")
    st.markdown("\n".join(rows))

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Mehrfach rechnen")
st.caption("Savings kostet Millisekunden: Neun λ-Werte, zwanzig verrauschte Läufe (1 %) oder bis zu 45 Läufe über λ, μ und ν zusammen rechnen schneller als ein Lauf von Einfügen nach Split; ob sie auch bessere Pläne liefern, zeigen die Bänder (ab n = 25 meist ja, bis n = 12 gleichauf). Je Strategie zählt der beste Plan.")
table = ["| Strategie | Läufe | Kosten | über Optimum | Routen | gegen Einfügen nach Split |", "|---|---|---|---|---|---|"]
for key in C.STRATEGY_KEYS:
    p = plans[key]
    vs = "–" if key == "es" else signed_pct(diff_percent(p.cost, plans["es"].cost))
    table.append(f"| **{C.STRATEGY_NAMES[key]}** | {p.runs} | {de(p.cost)} | {pct(gap_percent(p.cost, a.exact.cost))} | {len(p.routes)} | {vs} |")
st.markdown("\n".join(table))
pick = st.selectbox("Plan auf der Karte", list(C.STRATEGY_KEYS), index=1, key="strategy_pick", format_func=lambda k: C.STRATEGY_NAMES[k])
st.markdown(f"**{C.STRATEGY_NAMES[pick]}: {de(plans[pick].cost)}** ({routes_word(len(plans[pick].routes))}): {routes_text(plans[pick].routes)}")
st.plotly_chart(build_map(inst, plans[pick].routes), width="stretch", key="map_strategy")

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie schlagen sich die Strategien?")
st.caption("Feste Instanzen, vorberechnet (generate_precomputed.py): die Instanzen von Stück 4, vier Zellen (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), nur Zellen mit Referenz. "
           "Bis 12 Kunden gegen das exakte Optimum, darüber gegen die Referenz PyVRP.")
short = st.radio("Zielrouten", ["Drei Zielrouten", f"Kurze Routen ({C.SHORT_N} Kunden, {C.SHORT_ROUTES} Zielrouten)"], horizontal=True, key="band_kind") != "Drei Zielrouten"
if short:
    band_n, band_routes, band_fills = C.SHORT_N, C.SHORT_ROUTES, C.SHORT_FILLS
else:
    band_n = int(st.radio("Kunden n", list(C.BAND_SIZES), index=3, horizontal=True, key="band_n"))
    band_routes, band_fills = C.BAND_ROUTES, C.BAND_FILLS[band_n]
band_fill = int(st.radio("Auslastung (%)", list(band_fills), index=list(band_fills).index(90) if 90 in band_fills else 0, horizontal=True, key=f"band_fill_{band_n}_{band_routes}"))
stats = _band_stats(band_n, band_fill, band_routes)
if stats:
    st.caption(f"{instances_word(stats['count'])} (alle vier Zellen zusammen). Die Zahlen sind Spannen über Instanzen, kein Satz.")
    st.plotly_chart(build_bands(stats["gaps"], C.STRATEGY_NAMES, C.STRATEGY_COLORS), width="stretch", key="band_chart")
    ref_name = "Optimum" if band_n in C.EXACT_SIZES else "Referenz"
    table = [f"| Strategie | Läufe | Median | Minimum bis Maximum | Mittel | trifft {ref_name} | billiger / gleich / teurer als Einfügen nach Split |", "|---|---|---|---|---|---|---|"]
    for key in C.STRATEGY_KEYS:
        g = stats["gaps"][key]
        vs = "–" if key == "es" else (lambda p: f"{p['cheaper']} / {p['equal']} / {p['more']}")(stats["vs_es"][key])
        table.append(f"| **{C.STRATEGY_NAMES[key]}** | {C.STRATEGY_RUNS[key]} | {pct(g['median'])} | {pct(g['min'])} bis {pct(g['max'])} | {pct(g['mean'])} | {g['hit']} von {g['count']} | {vs} |")
    st.markdown("\n".join(table))
    st.markdown("**Der Median über λ** (parallel und sequentiell, μ = ν = 0)")
    st.plotly_chart(build_band_curve(stats["curve_par"], stats["curve_seq"], stats["gaps"]["es"]["median"]), width="stretch", key="band_curve")
    st.caption(f"Bestes festes λ nach dem Median: {de(stats['best_lam'], 1)} (Median {pct(stats['best_lam_median'])}); auf wie vielen Instanzen λ = 1 unter den neun Werten das beste ist: {stats['lam_is_best']} von {stats['count']}. "
               f"Ein Lauf (λ = 1) braucht im Median {stats['t_run_median'] * 1000:.0f} ms (Größenordnung, eine Messung). Bei den neun λ-Plänen verbessert der Split {stats['split_plans'] and stats['split_improves']} von {stats['split_plans']} Plänen.")
kind, text = verdict_bands(band_n, band_fill, band_routes, stats)
getattr(st, kind)(text)
kind, text = verdict_noise_bands(stats)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Fester Raster von Parametern** | Das beste λ hängt von der Instanz ab; hier stehen die Gitter fest (neun λ-Werte, 36 Tripel) und sind nicht an den Instanzen angepasst. Wer die Parameter lernt (genetischer Algorithmus), tunt auf Instanzen | – |
| **Savings bleibt Konstruktion** | Kein Verbesserungsschritt nach der Konstruktion: Nachbarschaftssuche über die Pläne rechnen die Demos zu VRP-Nachbarschaften und die Fall-Demo „Mini-Tourenplanung“ | – |
| **Rauschen ist ein eigener Ansatz** | Die verzerrte Zufallsauswahl (biased randomization) wählt die Paare aus der Liste mit abnehmender Wahrscheinlichkeit; hier wird nur die Ersparnis verrauscht | – |
| **Nur Kapazität, keine Zeitfenster** | Mit Zeitfenstern ist das Zusammenlegen nur zulässig, wenn die Zeiten halten | Stück 8 (Zeitfenster) |
| **Symmetrische Entfernungen** | Mit asymmetrischen Entfernungen ändert Umdrehen einer Route die Länge | – |
| **Referenz PyVRP ab 25 Kunden** | Eine gute Lösung, keine bewiesene Untergrenze | – |
| **Kein Vergleich mit Sweep und Cluster-first** | Beide gruppieren zuerst | Stück 6 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Wie in den Stücken 1 bis 4: Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen $d(\cdot,\cdot)$, $\bar q$ die mittlere Nachfrage.

| Symbol | Bedeutung |
|---|---|
| $s_{\lambda,\mu,\nu}(i, j)$ | Ersparnis mit Formparametern: $d(0,i) + d(0,j) - \lambda\, d(i,j) + \mu\,\lvert d(0,i) - d(0,j)\rvert + \nu\,(q_i + q_j)/\bar q$ |
| $L(R)$ | Länge einer Route $R$ (Depot, Kunden in Reihenfolge, Depot) |
| $\varepsilon$ | Stärke des Rauschens: $\tilde s = s\,(1 + \varepsilon u)$ mit $u$ gleichverteilt in $[-1, 1]$, je Paar unabhängig |

**Was λ = 1 besonders macht.** Endet die Route $A$ in $i$ und beginnt $B$ in $j$, dann ist $L(A \cdot B) = L(A) + L(B) - \big(d(0,i) + d(0,j) - d(i,j)\big)$: Mit $\lambda = 1$, $\mu = \nu = 0$ ist $s$ genau die Längenersparnis der Zusammenlegung (Stück 4). Für $\lambda \ne 1$ oder $\mu, \nu \ne 0$ ist $s$ nur noch eine **Priorität**: Die Liste ordnet die Paare anders, die tatsächliche Ersparnis bleibt $d(0,i) + d(0,j) - d(i,j)$.

**Positive Werte.** Es zählen nur Paare mit $s > 0$. Für $\lambda \le 1$ und $\mu = \nu = 0$ ist $s \ge 0$ nach der Dreiecksungleichung; für große $\lambda$ werden viele $s$ negativ, die Liste wird kurz, und Kunden bleiben allein (mehr Routen).

**Sequentielle Fassung.** Beginne mit dem am weitesten vom Depot entfernten freien Kunden; füge am Anfang oder Ende der Route den freien Kunden mit der größten Ersparnis zum jeweiligen Randkunden hinzu, solange er passt und $s > 0$ ist; dann die nächste Route. Die Fassung sieht die Paare nur an den Rändern der laufenden Route; die parallele sieht alle Paare. Mehr lässt sich ohne Messung nicht sagen.

**Mehrfach rechnen.** Das Beste von $k$ Läufen ist nie schlechter als jeder einzelne Lauf: $\min_t L(\mathrm{Plan}_t) \le L(\mathrm{Plan}_u)$. Wie viel es bringt, ist eine Messung (Experiment 5), kein Satz.

**Literatur.** Die Formparameter $\lambda$ stammen laut Sekundärquellen von Gaskell (1967) und Yellow (1970), $\mu$ und $\nu$ von Paessens (1988); die Formel ist nach Sekundärquellen übernommen. Parallel gegen sequentiell: laut Sekundärquellen liefert die parallele Fassung meist bessere Pläne. Savings mit verzerrter Zufallsauswahl als Mehrfachstart beschreiben Juan u. a. (2011), Parameter-Abstimmung durch einen genetischen Algorithmus Battarra, Golden und Vigo (2008); beides wurde nur als Name gesehen, die Demo übernimmt keine Zahl daraus. Clarke und Wright (1964) und die Zusammenlegungsregel stehen in Stück 4.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
