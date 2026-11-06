"""Vorberechnete Bänder (svv_bands.json): Aufbau, Vollständigkeit, Stimmigkeit der Zeilen und frische Nachrechnung einzelner Zeilen (Stichprobe)."""

import json
from pathlib import Path

import pytest

import svv_constants as C
import svv_evaluation as ev
import svv_savings as S

DATA = json.loads((Path(__file__).resolve().parent.parent / C.BAND_FILE).read_text(encoding="utf-8"))
KEYS = {"seed", "m", "ref", "es", "par", "par_k", "seq", "grid", "noise", "split_improves", "t_run"}
EXPECTED = ({(3, n, f) for n in C.BAND_SIZES for f in C.BAND_FILLS[n]}) | {(C.SHORT_ROUTES, C.SHORT_N, f) for f in C.SHORT_FILLS}


def _cells():
    return DATA["cells"]


def test_every_expected_cell_is_there_exactly_once():
    seen = [(c["routes"], c["n"], c["fill"]) for c in _cells() if (c["family"], c["depot"]) == C.BAND_CELLS[0]]
    assert sorted(seen) == sorted(EXPECTED) and len(seen) == len(set(seen))
    assert len(_cells()) == len(EXPECTED) * len(C.BAND_CELLS) == 40
    for c in _cells():
        assert [r["seed"] for r in c["rows"]] == list(C.BAND_SEEDS[c["n"]]) and (c["family"], c["depot"]) in C.BAND_CELLS


def test_every_row_has_all_fields_and_all_runs():
    for c in _cells():
        for r in c["rows"]:
            assert set(r) == KEYS, (c["n"], c["fill"], r["seed"])
            assert list(r["par"]) == [str(lam) for lam in S.LAMS] == list(r["seq"]) == list(r["par_k"])
            assert list(r["grid"]) == [f"{lam}|{mu}|{nu}" for lam, mu, nu in S.GRID]
            assert list(r["noise"]) == [str(e) for e in C.BAND_NOISE] and all(set(v) == {"best", "mean", "same"} for v in r["noise"].values())


def test_rows_are_consistent():
    for c in _cells():
        for r in c["rows"]:
            costs = list(r["par"].values()) + list(r["seq"].values()) + list(r["grid"].values())
            assert min(costs) >= r["ref"] - 1e-9 if c["n"] in C.EXACT_SIZES else min(costs) > 0          # bis 12 Kunden liegt kein Plan unter dem exakten Optimum
            assert r["es"] >= r["ref"] - 1e-9 or c["n"] not in C.EXACT_SIZES
            assert 0 <= r["split_improves"] <= 9 and r["m"] <= min(r["par_k"].values()) and max(r["par_k"].values()) <= c["n"]
            for v in r["noise"].values():
                assert v["best"] <= v["mean"] + 1e-9 and 0.0 <= v["same"] <= 1.0
                assert c["n"] not in C.EXACT_SIZES or v["best"] >= r["ref"] - 1e-9
            assert r["ref"] > 0 and r["t_run"] > 0


def test_the_references_are_plausible_for_larger_instances():
    """PyVRP ist eine gute Lösung, aber keine Untergrenze: höchstens 1 % über dem besten aller Savings-Läufe, bei den meisten Instanzen darunter."""
    below = total = 0
    for c in _cells():
        if c["n"] not in C.EXACT_SIZES:
            for r in c["rows"]:
                best = min(list(r["par"].values()) + list(r["grid"].values()))
                assert r["ref"] <= best * 1.01, (c["n"], c["fill"], r["seed"])
                below += r["ref"] <= best + 1e-9
                total += 1
    assert below / total > 0.9


@pytest.mark.parametrize("n,fill,routes", [(10, 90, 3), (12, 98, 3), (25, 90, 3), (50, 90, 8)])
def test_a_fresh_recomputation_of_one_row_per_cell_matches(n, fill, routes):
    for c in (x for x in _cells() if x["n"] == n and x["fill"] == fill and x["routes"] == routes):
        row = c["rows"][0]
        fresh = ev.instance_row(n, c["family"], c["depot"], routes, row["seed"], fill, row["ref"], row["es"])
        for key in KEYS - {"t_run"}:
            assert _same(fresh[key], row[key]), (n, fill, c["family"], c["depot"], key)


def _same(a, b):
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, float) or isinstance(b, float):
        return a == pytest.approx(b)
    return a == b


def test_n100_rows_agree_with_a_fresh_plain_run():
    import svv_algorithm as A
    from svv_scenario import make_instance

    for c in (x for x in _cells() if x["n"] == 100):
        row = c["rows"][-1]
        inst = make_instance(100, c["family"], c["depot"], 3, row["seed"], 90)
        assert A.plan_length(inst, S.savings_routes(inst)) == pytest.approx(row["par"]["1.0"]) and A.plan_length(inst, S.savings_sequential(inst)) == pytest.approx(row["seq"]["1.0"])


def test_strategy_cost_and_statistics_on_small_data():
    row = {"par": {str(lam): 10.0 + abs(lam - 1.0) for lam in S.LAMS}, "seq": {str(lam): 15.0 for lam in S.LAMS}, "grid": {f"{lam}|{mu}|{nu}": 10.5 for lam, mu, nu in S.GRID},
           "noise": {str(e): {"best": 9.5, "mean": 11.0, "same": 0.5} for e in C.BAND_NOISE}, "es": 10.4, "ref": 9.0, "split_improves": 2, "t_run": 0.001}
    assert [ev.strategy_cost(row, k) for k in C.STRATEGY_KEYS] == [10.0, 10.0, 9.5, 10.0, 15.0, 10.4]
    other = {**row, "par": {str(lam): 11.0 for lam in S.LAMS}, "ref": 10.0, "es": 10.0}
    stats = ev.band_stats([row, other])
    assert stats["count"] == 2 and stats["split_plans"] == 18 and stats["split_improves"] == 4
    assert stats["vs_es"]["std"] == {"count": 2, "cheaper": 1, "equal": 0, "more": 1, "median_diff": stats["vs_es"]["std"]["median_diff"]}
    assert stats["gaps"]["std"]["hit"] == 0 and stats["gaps"]["lam9"]["max"] == pytest.approx(100 / 9) and stats["best_lam"] == 1.0
    assert stats["lam_is_best"] == 1 and ev.band_stats([]) == {}
    assert ev.paired([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]) == {"count": 3, "cheaper": 1, "equal": 1, "more": 1, "median_diff": 0.0}
