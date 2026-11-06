"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import svv_algorithm as A
import svv_constants as C
import svv_construct as K
import svv_savings as S
from svv_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    fill: int = C.DEFAULT_FILL
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Plan:
    cost: float
    routes: tuple[tuple[int, ...], ...]
    runs: int = 1                             # Zahl der Savings-Läufe, aus denen der Plan der Strategie stammt


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    exact: A.ExactResult                 # Optimum über alle Tourenpläne
    min_routes: int                      # aufgerundet Gesamtnachfrage / Kapazität
    strategies: dict                     # Strategie-Schlüssel -> Plan (std, lam9, noise20, grid45, seq, es)
    curve_par: dict                      # λ -> Kosten der parallelen Fassung (μ = ν = 0) auf dem Raster LAM_CURVE
    curve_seq: dict                      # λ -> Kosten der sequentiellen Fassung


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    """Mit Vorzeichen (echtes Minus); -0,0 wird zu 0,0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def runs_word(k: int) -> str:
    return f"{k} Lauf" if k == 1 else f"{k} Läufe"


def gap_percent(cost: float, reference: float) -> float:
    """Mehrkosten gegenüber der Referenz in Prozent der Referenz; unter der Toleranz oder ohne Referenzkosten gibt es keinen Abstand, nie negativ."""
    if reference <= 0 or cost - reference <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def diff_percent(a: float, b: float) -> float:
    """Unterschied (a - b) in Prozent von b; innerhalb der Toleranz 0."""
    if abs(a - b) <= C.TOL or b <= 0:
        return 0.0
    return 100.0 * (a - b) / b


def reduction_percent(old: float, new: float) -> float:
    """Um wie viel Prozent von `old` ist `new` kürzer; innerhalb der Toleranz 0."""
    if old - new <= C.TOL or old <= 0:
        return 0.0
    return 100.0 * (old - new) / old


def order_text(order) -> str:
    return " ".join(str(c) for c in order)


def routes_text(routes) -> str:
    return " ‖ ".join("(" + order_text(r) + ")" for r in routes)


def params_text(p: S.Params) -> str:
    return f"λ = {de(p.lam, 1)}" + (f", μ = {de(p.mu, 1)}" if p.mu else "") + (f", ν = {de(p.nu, 1)}" if p.nu else "")


# ----------------------------------------------------------------------------------------------------------------------------------- Analyse

def build_instance(settings: Settings) -> Instance:
    return make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed, settings.fill)


def strategy_plans(inst: Instance, seed: int, es_routes=None) -> dict:
    """Die sechs Strategien auf einer Instanz: Savings mit λ = 1, Bestes von 9 λ-Werten, Bestes von 20 verrauschten Läufen, Bestes aus bis zu 45 Läufen (36 Tripel und 9 λ), sequentiell, Einfügen nach Split."""
    def par(p):
        return S.savings_routes(inst, p)

    std = par(S.STANDARD)
    lam9 = [par(S.Params(lam)) for lam in S.LAMS]
    grid = [par(S.Params(*t)) for t in S.GRID]
    noise = S.noise_runs(inst, S.STANDARD, S.NOISE_EPS, S.NOISE_RUNS, seed)
    es_routes = es_routes if es_routes is not None else A.split(inst, K.insert_split_order(inst)).routes
    out = {"std": ((std,), 1), "lam9": (lam9, 9), "noise20": (noise, S.NOISE_RUNS), "grid45": (lam9 + grid, 9 + len(S.GRID)), "seq": ((S.savings_sequential(inst),), 1), "es": ((es_routes,), 1)}
    plans = {}
    for key, (candidates, runs) in out.items():
        cost, routes = S.best_of(inst, candidates)
        plans[key] = Plan(cost, routes, runs)
    return plans


def analyse(settings: Settings) -> Analysis:
    inst = build_instance(settings)
    exact = A.exact_cvrp(inst)
    plans = strategy_plans(inst, settings.seed)
    curve_par = {lam: A.plan_length(inst, S.savings_routes(inst, S.Params(lam))) for lam in C.LAM_CURVE}
    curve_seq = {lam: A.plan_length(inst, S.savings_sequential(inst, S.Params(lam))) for lam in C.LAM_CURVE}
    return Analysis(settings, inst, exact, inst.min_routes, plans, curve_par, curve_seq)


def first_difference(base: S.SavingsResult, other: S.SavingsResult) -> dict | None:
    """Die erste Zusammenlegung, in der zwei Läufe sich unterscheiden (der k-te Zusammenlegungsschritt: anderes Paar oder einer der beiden Läufe ist schon fertig). None, wenn dieselben Paare in derselben Folge."""
    a = [s for s in base.steps if s.outcome == S.MERGED]
    b = [s for s in other.steps if s.outcome == S.MERGED]
    for k in range(max(len(a), len(b))):
        x = a[k] if k < len(a) else None
        y = b[k] if k < len(b) else None
        if x is None or y is None or (x.i, x.j) != (y.i, y.j):
            return {"merge_no": k + 1, "base": x, "other": y}
    return None


def noise_study(settings: Settings, params: S.Params, eps_pct: float, k: int) -> dict:
    """Experiment 3: k verrauschte Läufe (eps in Prozent) gegen den Lauf ohne Rauschen."""
    inst = build_instance(settings)
    base = S.savings_routes(inst, params)
    runs = S.noise_runs(inst, params, eps_pct / 100.0, k, settings.seed)
    costs = [A.plan_length(inst, r) for r in runs]
    best_cost, best_routes = S.best_of(inst, runs)
    base_key = S.canonical(base)
    return {"eps": eps_pct, "k": k, "base_cost": A.plan_length(inst, base), "costs": costs, "mean": mean(costs), "best": best_cost, "best_routes": best_routes,
            "same": sum(S.canonical(r) == base_key for r in runs), "distinct": len({S.canonical(r) for r in runs})}


def swap_info(settings: Settings, params: S.Params) -> dict:
    """Experiment 3: Kippstellen der Liste (Vertauschung benachbarter Paare)."""
    rows = S.swap_sensitivity(build_instance(settings), params)
    changed = [r for r in rows if r["changed"]]
    return {"total": len(rows), "changed": changed, "worst": max(changed, key=lambda r: abs(r["change_pct"])) if changed else None}


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def _canon_same(routes_a, routes_b) -> bool:
    return S.canonical(routes_a) == S.canonical(routes_b)


def instance_row(n: int, family: int, depot: int, routes: int, seed: int, fill: int, ref: float, es: float) -> dict:
    """Eine feste Instanz der Bänder: Referenz und Kosten von Einfügen nach Split (aus Stück 4 übernommen) und alle Savings-Läufe."""
    inst = make_instance(n, family, depot, routes, seed, fill)
    row = {"seed": seed, "m": inst.min_routes, "ref": ref, "es": es, "par": {}, "par_k": {}, "seq": {}, "grid": {}, "noise": {}}
    plans = {}
    for lam in S.LAMS:
        t = time.perf_counter()
        r = S.savings_routes(inst, S.Params(lam))
        if lam == 1.0:
            row["t_run"] = time.perf_counter() - t
        plans[lam] = r
        row["par"][str(lam)], row["par_k"][str(lam)] = A.plan_length(inst, r), len(r)
        row["seq"][str(lam)] = A.plan_length(inst, S.savings_sequential(inst, S.Params(lam)))
    row["split_improves"] = sum(S.savings_then_split(inst, plans[lam]).cost < A.plan_length(inst, plans[lam]) - C.TOL for lam in S.LAMS)
    for lam, mu, nu in S.GRID:
        row["grid"][f"{lam}|{mu}|{nu}"] = A.plan_length(inst, S.savings_routes(inst, S.Params(lam, mu, nu)))
    for eps in C.BAND_NOISE:
        runs = S.noise_runs(inst, S.STANDARD, eps, S.NOISE_RUNS, seed)
        costs = [A.plan_length(inst, r) for r in runs]
        row["noise"][str(eps)] = {"best": min(costs), "mean": mean(costs), "same": sum(_canon_same(r, plans[1.0]) for r in runs) / len(runs)}
    return row


@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_rows(n: int, fill: int, routes: int = C.BAND_ROUTES) -> list[dict]:
    """Alle gespeicherten Instanzzeilen einer Größe, Auslastung und Zielroutenzahl, Zellen in der Reihenfolge von BAND_CELLS."""
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    cells = sorted((c for c in load_bands().get("cells", []) if c["n"] == n and c["fill"] == fill and c["routes"] == routes), key=lambda c: order[(c["family"], c["depot"])])
    return [r for c in cells for r in c["rows"]]


def strategy_cost(row: dict, key: str) -> float:
    """Kosten der Strategie auf einer gespeicherten Zeile."""
    if key == "std":
        return row["par"]["1.0"]
    if key == "lam9":
        return min(row["par"].values())
    if key == "noise20":
        return row["noise"][str(S.NOISE_EPS)]["best"]
    if key == "grid45":
        return min(min(row["grid"].values()), min(row["par"].values()))
    if key == "seq":
        return row["seq"]["1.0"]
    if key == "es":
        return row["es"]
    raise KeyError(key)


def spread(values: list[float]) -> dict:
    return {"min": min(values), "median": median(values), "mean": mean(values), "max": max(values), "hit": sum(v == 0.0 for v in values), "count": len(values)}


def paired(a: list[float], b: list[float]) -> dict:
    """Gepaarter Vergleich: a billiger / gleich / teurer als b, dazu der Median des Unterschieds in Prozent von b."""
    cheaper = sum(x < y - C.TOL for x, y in zip(a, b))
    more = sum(x > y + C.TOL for x, y in zip(a, b))
    return {"count": len(a), "cheaper": cheaper, "equal": len(a) - cheaper - more, "more": more, "median_diff": median(diff_percent(x, y) for x, y in zip(a, b))}


def band_stats(rows: list[dict]) -> dict:
    """Alle Kennzahlen einer Größe, Auslastung und Zielroutenzahl aus den gespeicherten Zeilen."""
    if not rows:
        return {}
    ref = [r["ref"] for r in rows]
    costs = {k: [strategy_cost(r, k) for r in rows] for k in C.STRATEGY_KEYS}
    lam_gaps = {lam: [gap_percent(r["par"][str(lam)], r["ref"]) for r in rows] for lam in S.LAMS}
    best_lam = min(S.LAMS, key=lambda lam: (median(lam_gaps[lam]), lam))
    curve_par = {lam: median(v) for lam, v in lam_gaps.items()}
    curve_seq = {lam: median(gap_percent(r["seq"][str(lam)], r["ref"]) for r in rows) for lam in S.LAMS}
    noise = {}
    for eps in C.BAND_NOISE:
        e = str(eps)
        noise[eps] = {"best": median(gap_percent(r["noise"][e]["best"], r["ref"]) for r in rows), "mean": median(gap_percent(r["noise"][e]["mean"], r["ref"]) for r in rows),
                      "same": mean(r["noise"][e]["same"] for r in rows)}
    return {
        "count": len(rows),
        "gaps": {k: spread([gap_percent(c, r) for c, r in zip(costs[k], ref)]) for k in C.STRATEGY_KEYS},
        "vs_es": {k: paired(costs[k], costs["es"]) for k in C.STRATEGY_KEYS if k != "es"},
        "seq_vs_std": paired(costs["seq"], costs["std"]),
        "seq_best_gap": median(gap_percent(min(r["seq"].values()), r["ref"]) for r in rows),
        "curve_par": curve_par, "curve_seq": curve_seq, "best_lam": best_lam, "best_lam_median": curve_par[best_lam],
        "lam_is_best": sum(min(S.LAMS, key=lambda lam: (r["par"][str(lam)], lam)) == 1.0 for r in rows),
        "noise": noise,
        "split_improves": sum(r["split_improves"] for r in rows), "split_plans": 9 * len(rows),
        "t_run_median": median(r["t_run"] for r in rows),
    }


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_lambda(a: Analysis, params: S.Params, result: S.SavingsResult, base: S.SavingsResult) -> tuple[str, str]:
    """Experiment 1: Savings mit den gewählten Parametern gegen λ = 1 und gegen die beste Stelle des Rasters."""
    inst = a.inst
    cost, base_cost = A.plan_length(inst, result.routes), A.plan_length(inst, base.routes)
    gap = gap_percent(cost, a.exact.cost)
    text = f"Mit {params_text(params)} kostet Savings {de(cost)} ({routes_word(len(result.routes))}, {pct(gap)} über dem Optimum {de(a.exact.cost)}). "
    d = diff_percent(cost, base_cost)
    if params == S.STANDARD:
        text += "Das ist der Standard aus Stück 4. "
    elif d == 0.0:
        text += f"λ = 1 liefert dasselbe ({de(base_cost)}). "
    elif d < 0:
        text += f"λ = 1 kostet {de(base_cost)}: Die Wahl ist {pct(-d)} billiger. "
    else:
        text += f"λ = 1 kostet {de(base_cost)}: Die Wahl ist {pct(d)} teurer. "
    best_lam = min(a.curve_par, key=lambda lam: (round(a.curve_par[lam], 9), abs(lam - 1.0), lam))     # bei gleichen Kosten das λ nächst 1
    best = a.curve_par[best_lam]
    text += f"Auf dem Raster von λ (μ = ν = 0) ist λ = {de(best_lam, 1)} am billigsten ({de(best)}, {pct(gap_percent(best, a.exact.cost))} über dem Optimum)."
    return ("success" if cost <= a.exact.cost + C.TOL else ("warning" if gap >= C.GAP_WARN else "info")), text


def verdict_sequential(a: Analysis, params: S.Params, parallel_routes, sequential_routes) -> tuple[str, str]:
    """Experiment 2: parallel gegen sequentiell bei denselben Parametern."""
    inst = a.inst
    p, s = A.plan_length(inst, parallel_routes), A.plan_length(inst, sequential_routes)
    d = diff_percent(s, p)
    head = f"Bei {params_text(params)}: parallel {de(p)} ({routes_word(len(parallel_routes))}), sequentiell {de(s)} ({routes_word(len(sequential_routes))}); Optimum {de(a.exact.cost)}. "
    if d == 0.0:
        return "info", head + "Beide Fassungen kosten dasselbe."
    if d > 0:
        return "info", head + f"Die sequentielle Fassung ist {pct(d)} teurer."
    return "info", head + f"Die sequentielle Fassung ist hier {pct(-d)} billiger (im Mittel über feste Instanzen ist sie schwächer, siehe die Bänder)."


def verdict_noise(study: dict) -> tuple[str, str]:
    """Experiment 3: verrauschte Läufe."""
    k = study["k"]
    text = (f"{runs_word(k)} mit Rauschen {pct(study['eps'], 1)}: {study['same']} von {k} liefern denselben Plan wie der Lauf ohne Rauschen ({de(study['base_cost'])}), {study['distinct']} verschiedene Pläne insgesamt. "
            f"Im Mittel kosten die Läufe {de(study['mean'])}, der beste {de(study['best'])}")
    if study["best"] < study["base_cost"] - C.TOL:
        text += f" ({pct(reduction_percent(study['base_cost'], study['best']))} unter dem Lauf ohne Rauschen)."
    else:
        text += ": Kein verrauschter Lauf ist besser als der ohne Rauschen."
    return "info", text


def verdict_swaps(info: dict, base_cost: float) -> tuple[str, str]:
    """Experiment 3: Kippstellen der Liste."""
    total, changed = info["total"], info["changed"]
    if total == 0:
        return "info", "Die Liste hat weniger als zwei Paare: Es gibt nichts zu vertauschen."
    if not changed:
        return "success", f"Keine der {total} Vertauschungen benachbarter Paare ändert den Plan: Die Liste ist hier an keiner Stelle knapp."
    w = info["worst"]
    return "info", (f"Von {total} Vertauschungen benachbarter Paare ändern {len(changed)} den Plan. Die größte Kostenänderung ({signed_pct(w['change_pct'])}) hat die Vertauschung der Plätze {w['rank']} und {w['rank'] + 1}: "
                    f"Paar {w['first'][1]}, {w['first'][2]} (s = {de(w['first'][0])}) gegen Paar {w['second'][1]}, {w['second'][2]} (s = {de(w['second'][0])}).")


def verdict_strategies(a: Analysis) -> tuple[str, str]:
    """Experiment 4 und Kernfrage: die sechs Strategien auf der Instanz."""
    plans = a.strategies
    opt = a.exact.cost
    std, lam9, es = plans["std"].cost, plans["lam9"].cost, plans["es"].cost
    hits = [C.STRATEGY_NAMES[k] for k in C.STRATEGY_KEYS if plans[k].cost <= opt + C.TOL]
    text = (f"Das Optimum ist {de(opt)}. Savings mit λ = 1 kostet {de(std)} ({pct(gap_percent(std, opt))} darüber), das Beste von 9 λ-Werten {de(lam9)} ({pct(gap_percent(lam9, opt))}), "
            f"Einfügen nach Split {de(es)} ({pct(gap_percent(es, opt))}). ")
    if lam9 < std - C.TOL:
        text += f"Die neun λ-Werte senken die Kosten um {pct(reduction_percent(std, lam9))}. "
    else:
        text += "Kein anderes λ ist besser als λ = 1. "
    text += ("Das Optimum treffen: " + ", ".join(hits) + ".") if hits else "Keine Strategie trifft das Optimum."
    best_gap = gap_percent(min(plans[k].cost for k in ("std", "lam9", "noise20", "grid45")), opt)
    return ("success" if hits and C.STRATEGY_NAMES["lam9"] in hits else ("warning" if best_gap >= C.GAP_WARN else "info")), text


def _gap_part(name: str, s: dict) -> str:
    return f"{name} Median {pct(s['median'])} (Maximum {pct(s['max'])})"


def verdict_bands(n: int, fill: int, routes: int, stats: dict) -> tuple[str, str]:
    """Experiment 5: Bänder einer Größe, Auslastung und Zielroutenzahl (alle vier Zellen zusammen)."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    vs = stats["vs_es"]["lam9"]
    d = vs["median_diff"]
    g = stats["gaps"]
    if abs(d) < C.LEVEL_PP:
        lead = f"Das Beste von 9 λ-Werten und Einfügen nach Split liegen im Median gleichauf (Unterschied {signed_pct(d)}"
    elif d < 0:
        lead = f"Das Beste von 9 λ-Werten liegt im Median vorn (Unterschied {signed_pct(d)}"
    else:
        lead = f"Einfügen nach Split liegt im Median vorn (Unterschied {signed_pct(d)}"
    lead += f"; billiger / gleich / teurer: {vs['cheaper']} / {vs['equal']} / {vs['more']} von {vs['count']}). "
    ref = "zum exakten Optimum" if n in C.EXACT_SIZES else "zur Referenz PyVRP (keine bewiesene Untergrenze)"
    lead += (f"Abstand {ref}: {_gap_part('λ = 1', g['std'])}, {_gap_part('Bestes von 9 λ-Werten', g['lam9'])}, {_gap_part('Einfügen nach Split', g['es'])}; "
             f"sequentiell (λ = 1) Median {pct(g['seq']['median'])}.")
    return ("info" if g["lam9"]["median"] < C.GAP_WARN else "warning"), f"Bei n = {n}, {routes_word(routes)}, Auslastung {fill} % ({instances_word(stats['count'])}): " + lead


def verdict_noise_bands(stats: dict) -> tuple[str, str]:
    """Experiment 5: Rauschen in den Bändern."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    parts = [f"{de(eps * 100, 1)} %: Plan unverändert in {de(100 * v['same'], 0)} % der Läufe, Median des Mittels {pct(v['mean'])}, des Besten von 20 {pct(v['best'])}" for eps, v in stats["noise"].items()]
    return "info", "Verrauschte Läufe (je 20, Abstand zur Referenz) bei " + "; ".join(parts) + "."
