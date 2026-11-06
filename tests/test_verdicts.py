"""Verdikte: jede Zahl im Text stammt aus der Rechnung (DEMO-PLAYBOOK §9). Die Verdikte sind reine Funktionen (Art, Text); hier wird jede Verzweigung einmal erreicht."""

import re

import svv_algorithm as A
import svv_constants as C
import svv_evaluation as ev
import svv_savings as S


def _analysis_of(inst):
    plans = ev.strategy_plans(inst, 0)
    curve_par = {lam: A.plan_length(inst, S.savings_routes(inst, S.Params(lam))) for lam in C.LAM_CURVE}
    curve_seq = {lam: A.plan_length(inst, S.savings_sequential(inst, S.Params(lam))) for lam in C.LAM_CURVE}
    return ev.Analysis(ev.Settings(), inst, A.exact_cvrp(inst), inst.min_routes, plans, curve_par, curve_seq)


def test_lambda_verdict_standard_cheaper_and_dearer_on_the_small_instance(small):
    a = _analysis_of(small)
    base = S.savings(small)
    kind, text = ev.verdict_lambda(a, S.STANDARD, base, base)
    assert kind == "warning" and "Mit λ = 1,0 kostet Savings 62,26 (2 Routen, 9,7 % über dem Optimum 56,73)" in text and "Das ist der Standard aus Stück 4" in text
    assert "Auf dem Raster von λ (μ = ν = 0) ist λ = 0,9 am billigsten (56,73, 0,0 % über dem Optimum)" in text
    kind, text = ev.verdict_lambda(a, S.Params(0.8), S.savings(small, S.Params(0.8)), base)
    assert kind == "success" and "Mit λ = 0,8 kostet Savings 56,73 (2 Routen, 0,0 %" in text and "λ = 1 kostet 62,26: Die Wahl ist 8,9 % billiger" in text
    kind, text = ev.verdict_lambda(a, S.Params(1.2), S.savings(small, S.Params(1.2)), base)
    assert kind == "warning" and "λ = 1 kostet 62,26: Die Wahl ist 3,6 % teurer" in text
    kind, text = ev.verdict_lambda(a, S.Params(1.0, 0.0, 0.0), S.savings(small), base)
    assert "Das ist der Standard" in text
    same = ev.verdict_lambda(a, S.Params(0.9), S.savings(small, S.Params(0.9)), S.savings(small, S.Params(0.9)))
    assert "λ = 1 liefert dasselbe" in same[1]


def test_lambda_verdict_prefers_lambda_one_on_ties():
    a = ev.analyse(ev.Settings())
    base = S.savings(a.inst)
    kind, text = ev.verdict_lambda(a, S.STANDARD, base, base)
    assert kind == "info" and "ist λ = 1,0 am billigsten (459,10, 3,3 % über dem Optimum)" in text


def test_sequential_verdict_cheaper_dearer_and_equal(small):
    a = _analysis_of(small)
    par, seq = S.savings(small).routes, S.savings_sequential(small)
    kind, text = ev.verdict_sequential(a, S.STANDARD, par, seq)
    assert kind == "info" and "parallel 62,26 (2 Routen), sequentiell 56,73 (2 Routen); Optimum 56,73" in text and "hier 8,9 % billiger" in text
    a0 = ev.analyse(ev.Settings())
    kind, text = ev.verdict_sequential(a0, S.STANDARD, S.savings_routes(a0.inst), S.savings_sequential(a0.inst))
    assert "parallel 459,10 (4 Routen), sequentiell 492,45 (3 Routen)" in text and "7,3 % teurer" in text
    assert "dasselbe" in ev.verdict_sequential(a0, S.STANDARD, par, par)[1]


def test_noise_verdict_both_branches():
    better = {"eps": 1.0, "k": 20, "base_cost": 330.58, "costs": [330.58] * 11 + [323.39] * 9, "mean": 327.34, "best": 323.39, "best_routes": (), "same": 11, "distinct": 2}
    kind, text = ev.verdict_noise(better)
    assert kind == "info" and "20 Läufe mit Rauschen 1,0 %: 11 von 20 liefern denselben Plan wie der Lauf ohne Rauschen (330,58), 2 verschiedene Pläne insgesamt" in text
    assert "Im Mittel kosten die Läufe 327,34, der beste 323,39 (2,2 % unter dem Lauf ohne Rauschen)" in text
    same = dict(better, best=330.58, mean=330.58, same=20, distinct=1, k=1)
    assert "1 Lauf mit Rauschen" in ev.verdict_noise(same)[1] and "Kein verrauschter Lauf ist besser" in ev.verdict_noise(same)[1]


def test_noise_study_on_a_real_instance_is_consistent_with_its_verdict():
    s = ev.Settings(8, 1, 0, 3, 90, 39)
    study = ev.noise_study(s, S.STANDARD, 1.0, 20)
    assert study["same"] <= 20 and 1 <= study["distinct"] <= 20 and len(study["costs"]) == 20
    text = ev.verdict_noise(study)[1]
    assert f"{study['same']} von 20" in text and f"{study['distinct']} verschiedene" in text and ev.de(study["best"]) in text


def test_swaps_verdict_three_cases():
    assert ev.verdict_swaps({"total": 0, "changed": [], "worst": None}, 1.0)[0] == "info"
    kind, text = ev.verdict_swaps({"total": 14, "changed": [], "worst": None}, 1.0)
    assert kind == "success" and "Keine der 14 Vertauschungen" in text
    info = ev.swap_info(ev.Settings(6, 0, 0, 2, 90, 7), S.STANDARD)
    kind, text = ev.verdict_swaps(info, 1.0)
    w = info["worst"]
    assert kind == "info" and f"Von {info['total']} Vertauschungen benachbarter Paare ändern {len(info['changed'])} den Plan" in text
    assert f"Plätze {w['rank']} und {w['rank'] + 1}" in text and ev.signed_pct(w["change_pct"]) in text and ev.de(w["first"][0]) in text and ev.de(w["second"][0]) in text
    assert w["rank"] == 2 and (w["first"][1:], w["second"][1:]) == ((1, 2), (1, 4)) and round(w["change_pct"], 1) == -8.9


def test_strategies_verdict_cases(small):
    kind, text = ev.verdict_strategies(_analysis_of(small))
    assert kind == "success" and "Das Optimum ist 56,73. Savings mit λ = 1 kostet 62,26" in text and "das Beste von 9 λ-Werten 56,73 (0,0 %)" in text and "Einfügen nach Split 58,37 (2,9 %)" in text
    assert "Die neun λ-Werte senken die Kosten um 8,9 %" in text and "Das Optimum treffen: Bestes von 9 λ-Werten" in text and "Sequentiell, λ = 1" in text
    kind, text = ev.verdict_strategies(ev.analyse(ev.Settings()))
    assert kind == "info" and "Kein anderes λ ist besser als λ = 1" in text and text.endswith("Das Optimum treffen: Einfügen nach Split.")


def test_strategies_verdict_without_any_hit_warns_or_informs():
    a = ev.analyse(ev.Settings(12, 1, 0, 3, 98, 300002))
    kind, text = ev.verdict_strategies(a)
    assert kind in ("info", "warning", "success") and text


def test_band_verdict_at_every_size_names_the_counts_of_the_stored_rows():
    stats = ev.band_stats(ev.band_rows(12, 90))
    kind, text = ev.verdict_bands(12, 90, 3, stats)
    vs = stats["vs_es"]["lam9"]
    assert kind == "info" and "Bei n = 12, 3 Routen, Auslastung 90 % (80 Instanzen)" in text and "Abstand zum exakten Optimum" in text
    assert f"{vs['cheaper']} / {vs['equal']} / {vs['more']} von 80" in text and "im Median gleichauf (Unterschied 0,0 %" in text and "λ = 1 Median 0,8 %" in text
    kind, text = ev.verdict_bands(50, 90, 3, ev.band_stats(ev.band_rows(50, 90)))
    assert "Abstand zur Referenz PyVRP (keine bewiesene Untergrenze)" in text and "(Unterschied −3,4 %" in text and "26 / 0 / 6 von 32" in text and kind == "info"
    kind, text = ev.verdict_bands(100, 90, 3, ev.band_stats(ev.band_rows(100, 90)))
    assert "30 / 0 / 2 von 32" in text and "sequentiell (λ = 1) Median 21,4 %" in text
    assert ev.verdict_bands(12, 90, 3, {})[0] == "warning"


def test_band_verdict_level_and_reverse_cases():
    base = {"count": 4, "gaps": {k: {"median": 1.0, "max": 2.0} for k in C.STRATEGY_KEYS}, "vs_es": {"lam9": {"cheaper": 1, "equal": 1, "more": 2, "median_diff": 0.4, "count": 4}}}
    assert "im Median gleichauf (Unterschied +0,4 %" in ev.verdict_bands(12, 90, 3, base)[1]
    base["vs_es"]["lam9"]["median_diff"] = 2.5
    assert "Einfügen nach Split liegt im Median vorn (Unterschied +2,5 %" in ev.verdict_bands(12, 90, 3, base)[1]
    base["gaps"]["lam9"]["median"] = 6.0
    assert ev.verdict_bands(25, 90, 3, base)[0] == "warning"


def test_noise_band_verdict_lists_every_level():
    stats = ev.band_stats(ev.band_rows(50, 90))
    kind, text = ev.verdict_noise_bands(stats)
    assert kind == "info" and all(f"{ev.de(eps * 100, 1)} %" in text for eps in C.BAND_NOISE)
    assert "Plan unverändert in 38 % der Läufe" in text and "Besten von 20 3,6 %" in text
    assert ev.verdict_noise_bands({})[0] == "warning"


def test_every_preset_produces_all_verdicts():
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        a = ev.analyse(s)
        res, base = S.savings(a.inst, S.Params(0.8)), S.savings(a.inst)
        for kind, text in (ev.verdict_strategies(a), ev.verdict_lambda(a, S.Params(0.8), res, base), ev.verdict_sequential(a, S.STANDARD, base.routes, S.savings_sequential(a.inst)),
                           ev.verdict_noise(ev.noise_study(s, S.STANDARD, 1.0, 5)), ev.verdict_swaps(ev.swap_info(s, S.STANDARD), 1.0)):
            assert kind in ("success", "info", "warning") and text and re.search(r"\bnan\b", text.lower()) is None
