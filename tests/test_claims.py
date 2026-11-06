"""Jede Zahl der README („Befunde“) und der Preset-Hilfen, nachgerechnet mit denselben Funktionen wie die App (DEMO-PLAYBOOK §4).

Die Bänder kommen aus svv_bands.json (tests/test_bands.py rechnet Stichproben davon frisch nach); Werte werden auf eine Stelle verglichen. Die Zahlen wurden in der Planung
(vormessung/messreihe_tb19 bis tb24) mit eigenen Skripten unabhängig bestimmt und stimmen überein. Zeiten werden nicht festgeschrieben."""

from pathlib import Path

import numpy as np
import pytest

import svv_algorithm as A
import svv_constants as C
import svv_evaluation as ev
import svv_savings as S
from svv_scenario import make_instance

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def r1(x):
    return round(x, 1)


def _stats(n, fill, routes=3):
    return ev.band_stats(ev.band_rows(n, fill, routes))


def _triple(p):
    return (p["cheaper"], p["equal"], p["more"])


# Zelle (n, Auslastung, Zielrouten) -> je Strategie (Median, Mittel, Maximum, getroffen); gepaart gegen Einfügen nach Split; sequentiell gegen λ = 1; bestes festes λ (Wert, Median);
# auf wie vielen Instanzen λ = 1 unter den neun Werten das beste ist; Split verbessert so viele der neun Pläne (von allen)
CELLS = {
    (10, 90, 3): dict(gaps={'std': (0.2, 1.8, 15.0, 35), 'lam9': (0.0, 1.0, 11.1, 39), 'noise20': (0.0, 1.3, 11.1, 44), 'grid45': (0.0, 0.7, 6.7, 47), 'seq': (4.8, 6.8, 29.7, 10), 'es': (0.0, 1.1, 10.0, 40)}, vs_es={'lam9': (20, 40, 20), 'noise20': (21, 40, 19), 'grid45': (27, 39, 14)}, seq_vs_std=(7, 19, 54),
          best_lam=(1.0, 0.2), lam_is_best=32, split=(133, 720)),
    (12, 60, 3): dict(gaps={'std': (0.7, 2.0, 12.0, 23), 'lam9': (0.2, 1.1, 7.4, 32), 'noise20': (0.2, 1.4, 12.0, 36), 'grid45': (0.0, 0.9, 6.7, 38), 'seq': (4.3, 6.8, 26.7, 7), 'es': (0.7, 1.8, 15.8, 19)}, vs_es={'lam9': (36, 22, 22), 'noise20': (34, 24, 22), 'grid45': (41, 25, 14)}, seq_vs_std=(5, 25, 50),
          best_lam=(1.0, 0.7), lam_is_best=33, split=(125, 720)),
    (12, 75, 3): dict(gaps={'std': (1.0, 2.3, 15.6, 29), 'lam9': (0.0, 1.3, 13.1, 34), 'noise20': (0.0, 1.9, 15.6, 40), 'grid45': (0.0, 1.2, 13.1, 38), 'seq': (4.1, 7.3, 33.7, 7), 'es': (0.5, 1.8, 11.0, 30)}, vs_es={'lam9': (35, 26, 19), 'noise20': (30, 28, 22), 'grid45': (37, 26, 17)}, seq_vs_std=(5, 21, 54),
          best_lam=(1.2, 0.9), lam_is_best=27, split=(132, 720)),
    (12, 90, 3): dict(gaps={'std': (0.8, 1.7, 9.9, 31), 'lam9': (0.0, 0.9, 7.9, 37), 'noise20': (0.2, 1.3, 9.9, 35), 'grid45': (0.0, 0.6, 7.9, 43), 'seq': (4.9, 7.1, 27.4, 7), 'es': (0.6, 1.8, 15.3, 32)}, vs_es={'lam9': (32, 31, 17), 'noise20': (32, 32, 16), 'grid45': (35, 32, 13)}, seq_vs_std=(3, 18, 59),
          best_lam=(1.0, 0.8), lam_is_best=34, split=(137, 720)),
    (12, 98, 3): dict(gaps={'std': (2.0, 4.8, 26.6, 23), 'lam9': (0.5, 2.1, 15.9, 27), 'noise20': (0.9, 3.2, 21.8, 29), 'grid45': (0.3, 1.7, 15.9, 29), 'seq': (4.5, 7.6, 30.8, 8), 'es': (1.0, 2.7, 15.7, 22)}, vs_es={'lam9': (36, 24, 20), 'noise20': (29, 29, 22), 'grid45': (38, 23, 19)}, seq_vs_std=(14, 20, 46),
          best_lam=(0.8, 1.7), lam_is_best=22, split=(137, 720)),
    (25, 90, 3): dict(gaps={'std': (2.4, 3.1, 10.7, 0), 'lam9': (1.4, 1.9, 8.0, 0), 'noise20': (1.2, 1.7, 6.6, 0), 'grid45': (1.2, 1.5, 5.3, 0), 'seq': (12.1, 12.1, 37.3, 0), 'es': (3.3, 5.1, 18.8, 0)}, vs_es={'lam9': (24, 1, 7), 'noise20': (26, 1, 5), 'grid45': (26, 1, 5)}, seq_vs_std=(2, 3, 27),
          best_lam=(1.0, 2.4), lam_is_best=16, split=(67, 288)),
    (50, 90, 3): dict(gaps={'std': (7.7, 7.7, 19.7, 0), 'lam9': (4.8, 5.2, 14.5, 0), 'noise20': (3.6, 4.2, 7.8, 0), 'grid45': (3.3, 3.6, 8.1, 1), 'seq': (17.0, 17.4, 31.2, 0), 'es': (8.3, 9.1, 17.4, 0)}, vs_es={'lam9': (26, 0, 6), 'noise20': (27, 0, 5), 'grid45': (28, 0, 4)}, seq_vs_std=(2, 0, 30),
          best_lam=(1.2, 7.0), lam_is_best=5, split=(47, 288)),
    (100, 90, 3): dict(gaps={'std': (9.2, 9.7, 18.2, 0), 'lam9': (6.7, 6.8, 12.5, 0), 'noise20': (6.9, 6.9, 13.8, 0), 'grid45': (5.2, 5.5, 10.2, 0), 'seq': (21.4, 20.7, 29.7, 0), 'es': (11.7, 13.2, 24.9, 0)}, vs_es={'lam9': (30, 0, 2), 'noise20': (30, 0, 2), 'grid45': (31, 0, 1)}, seq_vs_std=(0, 0, 32),
          best_lam=(1.2, 8.5), lam_is_best=7, split=(65, 288)),
    (50, 90, 8): dict(gaps={'std': (3.3, 3.6, 8.4, 0), 'lam9': (2.9, 2.9, 5.7, 0), 'noise20': (2.3, 2.5, 5.7, 0), 'grid45': (2.3, 2.5, 5.7, 0), 'seq': (11.3, 12.9, 28.0, 0), 'es': (5.6, 6.8, 17.1, 0)}, vs_es={'lam9': (28, 0, 4), 'noise20': (29, 0, 3), 'grid45': (29, 0, 3)}, seq_vs_std=(0, 0, 32),
          best_lam=(1.0, 3.3), lam_is_best=16, split=(63, 288)),
    (50, 98, 8): dict(gaps={'std': (3.4, 4.2, 11.7, 0), 'lam9': (2.3, 3.0, 8.5, 0), 'noise20': (1.9, 2.6, 11.7, 0), 'grid45': (2.1, 2.7, 8.5, 0), 'seq': (11.6, 11.8, 29.1, 0), 'es': (6.6, 7.3, 15.9, 0)}, vs_es={'lam9': (30, 0, 2), 'noise20': (30, 0, 2), 'grid45': (30, 0, 2)}, seq_vs_std=(1, 0, 31),
          best_lam=(1.2, 3.4), lam_is_best=13, split=(64, 288)),
}
NOISE = {(12, 90, 3): {0.003: (0.6, 0.9, 85), 0.01: (0.2, 0.9, 63), 0.03: (0.0, 1.5, 38), 0.1: (0.1, 3.6, 14)}, (25, 90, 3): {0.003: (1.5, 2.4, 69), 0.01: (1.2, 2.2, 34), 0.03: (0.9, 3.3, 8), 0.1: (3.4, 9.8, 0)}, (50, 90, 3): {0.003: (5.6, 7.6, 38), 0.01: (3.6, 7.3, 10), 0.03: (4.5, 9.0, 1), 0.1: (12.7, 19.8, 0)}, (100, 90, 3): {0.003: (6.4, 9.4, 13), 0.01: (6.9, 10.7, 1), 0.03: (8.8, 14.7, 0), 0.1: (23.0, 31.3, 0)}}                 # (n, 90, 3) -> Rauschstufe -> (Median des Besten von 20, Median des Mittels, Anteil der Läufe mit demselben Plan in Prozent)
CURVE_12_90 = {0.4: 5.1, 0.6: 2.7, 0.8: 1.1, 1.0: 0.8, 1.2: 1.3, 1.4: 1.6, 1.6: 3.1, 1.8: 4.2, 2.0: 6.5}
HITS_12_90 = {0.4: 1, 0.6: 5, 1.0: 31, 1.6: 4, 2.0: 2}


@pytest.mark.parametrize("cell", list(CELLS))
def test_strategies_in_every_cell(cell):
    expected = CELLS[cell]
    s = _stats(*cell)
    assert s["count"] == (80 if cell[0] in C.EXACT_SIZES else 32)
    for key, value in expected["gaps"].items():
        g = s["gaps"][key]
        assert (r1(g["median"]), r1(g["mean"]), r1(g["max"]), g["hit"]) == value, key
    for key, value in expected["vs_es"].items():
        assert _triple(s["vs_es"][key]) == value, key
    assert _triple(s["seq_vs_std"]) == expected["seq_vs_std"]
    assert (s["best_lam"], r1(s["best_lam_median"])) == expected["best_lam"] and s["lam_is_best"] == expected["lam_is_best"] and (s["split_improves"], s["split_plans"]) == expected["split"]


def test_the_readme_names_the_numbers_of_the_strategy_table():
    for cell, e in CELLS.items():
        for key in ("std", "lam9"):
            median, mean, mx, _ = e["gaps"][key]
            assert f"{median:.1f} / {mean:.1f} / {mx:.1f}".replace(".", ",") in README, (cell, key)
        assert " / ".join(map(str, e["vs_es"]["lam9"])) in README, cell


def test_the_best_fixed_lambda_lies_between_point_eight_and_one_point_two_in_every_cell():
    assert all(0.8 <= e["best_lam"][0] <= 1.2 for e in CELLS.values()) and len(CELLS) == 10


def test_the_lambda_curve_has_a_valley_at_one_for_n12():
    stats = _stats(12, 90)
    assert {lam: r1(v) for lam, v in stats["curve_par"].items()} == CURVE_12_90
    rows = ev.band_rows(12, 90)
    assert {lam: sum(r["par"][str(lam)] <= r["ref"] + 1e-9 for r in rows) for lam in HITS_12_90} == HITS_12_90
    assert min(CURVE_12_90, key=CURVE_12_90.get) == 1.0 and CURVE_12_90[0.4] > CURVE_12_90[0.6] > CURVE_12_90[0.8] > CURVE_12_90[1.0] < CURVE_12_90[1.4] < CURVE_12_90[2.0]


def test_larger_instances_have_their_valley_at_one_point_two():
    for n in (50, 100):
        stats = _stats(n, 90)
        assert stats["best_lam"] == 1.2 and stats["curve_par"][1.2] < stats["curve_par"][1.0]
    assert (r1(_stats(50, 90)["curve_par"][1.2]), r1(_stats(100, 90)["curve_par"][1.2])) == (7.0, 8.5)


def test_lambda_one_is_the_best_of_nine_on_few_instances_at_larger_sizes():
    assert [CELLS[(n, 90, 3)]["lam_is_best"] for n in (12, 25, 50, 100)] == [34, 16, 5, 7]
    best = {}
    for r in ev.band_rows(100, 90):
        b = min(S.LAMS, key=lambda lam: (r["par"][str(lam)], lam))
        best[b] = best.get(b, 0) + 1
    assert dict(sorted(best.items())) == {0.8: 2, 1.0: 7, 1.2: 6, 1.4: 3, 1.6: 5, 1.8: 6, 2.0: 3}


@pytest.mark.parametrize("n", [12, 25, 50, 100])
def test_noise_levels(n):
    stats = _stats(n, 90)
    got = {eps: (r1(v["best"]), r1(v["mean"]), round(100 * v["same"])) for eps, v in stats["noise"].items()}
    assert got == NOISE[(n, 90, 3)]


def test_the_sequential_version_is_clearly_weaker_than_the_parallel_one():
    medians = {n: r1(_stats(n, 90)["gaps"]["seq"]["median"]) for n in (10, 12, 25, 50, 100)}
    assert medians == {10: 4.8, 12: 4.9, 25: 12.1, 50: 17.0, 100: 21.4}
    assert r1(_stats(50, 90)["seq_best_gap"]) == 10.2 and r1(_stats(100, 90)["seq_best_gap"]) == 16.2
    assert all(_stats(n, 90)["gaps"]["seq"]["median"] > _stats(n, 90)["gaps"]["std"]["median"] for n in (10, 12, 25, 50, 100))


def test_times_are_only_compared_in_order_of_magnitude():
    for n in C.BAND_SIZES:
        assert _stats(n, 90)["t_run_median"] < 0.5


# ----------------------------------------------------------------------------------------------------------------------------------- Kippstellen (live)

def _swap_numbers(n, fill):
    changed, totals, worst = [], [], []
    for cell in ev.load_bands()["cells"]:
        if (cell["n"], cell["fill"], cell["routes"]) != (n, fill, 3):
            continue
        for r in cell["rows"]:
            rows = S.swap_sensitivity(make_instance(n, cell["family"], cell["depot"], 3, r["seed"], fill))
            ch = [x for x in rows if x["changed"]]
            changed.append(len(ch))
            totals.append(len(rows))
            worst.append(max((abs(x["change_pct"]) for x in ch), default=0.0))
    return float(np.median(totals)), float(np.median(changed)), min(changed), max(changed), r1(float(np.median(worst))), r1(max(worst))


def test_swap_sensitivity_at_n12_and_n25():
    assert _swap_numbers(12, 90) == (65.0, 2.0, 0, 6, 0.7, 13.8)
    assert _swap_numbers(25, 90) == (299.0, 3.0, 0, 7, 1.0, 9.5)


# ----------------------------------------------------------------------------------------------------------------------------------- Handinstanz, Voreinstellung, Presets

def test_small_hand_instance_numbers_of_the_readme(small):
    assert round(A.plan_length(small, S.savings(small).routes), 2) == 62.26 and round(A.exact_cvrp(small).cost, 2) == 56.73
    assert round(A.plan_length(small, S.savings(small, S.Params(0.8)).routes), 2) == 56.73 and round(A.plan_length(small, S.savings_sequential(small)), 2) == 56.73
    assert ev.pct(ev.gap_percent(A.plan_length(small, S.savings(small).routes), A.exact_cvrp(small).cost)) == "9,7 %"
    for text in ("62,26", "56,73", "58,37", "10,23", "10,21", "8,79", "8,78"):
        assert text in README


def test_default_setting_numbers_of_the_readme():
    a = ev.analyse(ev.Settings())
    assert {k: ev.de(p.cost) for k, p in a.strategies.items()} == {"std": "459,10", "lam9": "459,10", "noise20": "459,10", "grid45": "459,10", "seq": "492,45", "es": "444,40"}
    assert ev.de(a.exact.cost) == "444,40" and all(t in README for t in ("444,40", "459,10", "492,45"))
    assert [k for k, v in a.curve_par.items() if v <= a.exact.cost + 1e-9] == []


def test_preset_help_numbers():
    expected = {
        "Einfügen nach Split gewinnt (n = 8)": ("444,40", "3,3 %", "492,45", "10,8 %"),
        "Ein kleineres λ trifft das Optimum (n = 8)": ("413,58", "5,0 %", "λ = 0,4 und 0,5"),
        "λ oder Rauschen finden das Optimum (n = 8)": ("323,39", "2,2 %", "λ = 1,1 und 1,2"),
        "Sequentiell trifft, parallel nicht (n = 8)": ("392,33", "10,0 %"),
        "Savings trifft das Optimum bei vielen λ (n = 8)": ("338,50", "λ von 0,3 bis 1,0", "10,4 %", "18,5 %"),
        "Zwei Paare vertauschen die Plätze (n = 6)": ("56,73", "8,79", "8,78", "62,26", "9,7 %", "10,23", "10,21"),
    }
    assert set(expected) == set(C.PRESETS)
    for name, words in expected.items():
        for w in words:
            assert w in C.PRESET_HELP[name], (name, w)
    facts = {}
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(p["n"], p["family"], p["depot"], p["routes"], p["fill"], p["seed"]))
        hit = [lam for lam, v in a.curve_par.items() if v <= a.exact.cost + 1e-9]
        facts[name] = (ev.de(a.exact.cost), {k: ev.pct(ev.gap_percent(pl.cost, a.exact.cost)) for k, pl in a.strategies.items()}, hit, {k: ev.de(pl.cost) for k, pl in a.strategies.items()})
    f = facts["Einfügen nach Split gewinnt (n = 8)"]
    assert f[0] == "444,40" and (f[1]["std"], f[1]["es"], f[1]["seq"]) == ("3,3 %", "0,0 %", "10,8 %") and f[2] == [] and f[3]["seq"] == "492,45"
    f = facts["Ein kleineres λ trifft das Optimum (n = 8)"]
    assert f[0] == "413,58" and f[1]["std"] == "5,0 %" and f[1]["es"] == "0,0 %" and f[2] == [0.4, 0.5]
    f = facts["λ oder Rauschen finden das Optimum (n = 8)"]
    assert f[0] == "323,39" and f[1]["std"] == "2,2 %" and f[2] == [1.1, 1.2] and f[1]["noise20"] == "0,0 %"
    f = facts["Sequentiell trifft, parallel nicht (n = 8)"]
    assert f[0] == "392,33" and f[1]["seq"] == "0,0 %" and f[1]["std"] == "10,0 %" and f[2] == []
    f = facts["Savings trifft das Optimum bei vielen λ (n = 8)"]
    assert f[0] == "338,50" and f[2] == [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] and (f[1]["es"], f[1]["seq"]) == ("10,4 %", "18,5 %")
    f = facts["Zwei Paare vertauschen die Plätze (n = 6)"]
    assert f[0] == "56,73" and f[1]["std"] == "9,7 %" and f[1]["lam9"] == "0,0 %" and f[3]["std"] == "62,26"
