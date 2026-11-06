"""Randfälle, an denen die Varianten erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1 und n = 2, große λ (alle Ersparnisse ≤ 0), negative ν, Nachfrage gleich Kapazität, Kapazität für alle,
Kunden am selben Ort, Kunde auf dem Depot, Gleichstände, Reglergrenzen, Abstände an der Null, keine oder eine einzige Paarvertauschung."""

import dataclasses
import math

import pytest

import svv_algorithm as A
import svv_constants as C
import svv_evaluation as ev
import svv_savings as S
from svv_scenario import Instance, make_instance


def test_one_customer_in_every_variant():
    inst = Instance(((0.0, 0.0), (3.0, 4.0)), (2,), 2)
    for p in (S.STANDARD, S.Params(2.4), S.Params(1.0, 2.0, -1.0)):
        assert S.savings(inst, p).routes == ((1,),) and S.savings(inst, p).steps == () and S.savings_sequential(inst, p) == ((1,),)
    assert S.noise_runs(inst, S.STANDARD, 0.1, 3, 5) == [((1,),)] * 3 and S.swap_sensitivity(inst) == []
    plans = ev.strategy_plans(inst, 0)
    assert all(p.cost == pytest.approx(10.0) for p in plans.values())


def test_exactly_two_customers():
    together = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0)), (1, 1), 2)
    assert S.savings(together).routes == ((1, 2),) and S.savings_sequential(together) == ((1, 2),)
    assert S.swap_sensitivity(together) == []                                         # ein Paar: nichts zu vertauschen
    apart = dataclasses.replace(together, capacity=1)
    assert S.savings(apart).routes == ((1,), (2,)) and S.savings_sequential(apart) == ((2,), (1,))


def test_a_huge_lambda_leaves_everyone_alone_and_all_savings_are_non_positive():
    inst = make_instance(10, 1, 0, 3, 5, 85)
    p = S.Params(50.0)
    assert S.savings_list(inst, p) == [] and S.savings(inst, p).routes == tuple((c,) for c in range(1, 11)) and S.savings(inst, p).steps == ()
    assert len(S.savings_sequential(inst, p)) == 10 and all(len(r) == 1 for r in S.savings_sequential(inst, p))
    assert A.plan_length(inst, S.savings(inst, p).routes) == pytest.approx(2 * sum(math.dist(inst.xy[0], inst.xy[c]) for c in range(1, 11)))


def test_a_negative_nu_prefers_small_demands_and_stays_valid():
    inst = make_instance(12, 1, 0, 3, 2, 85)
    for nu in (-1.0, 0.0, 1.0):
        r = S.savings(inst, S.Params(1.0, 0.0, nu))
        assert A.is_feasible_plan(inst, r.routes)


def test_demand_equal_to_capacity_means_one_customer_per_route():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0), (-3.0, 4.0)), (4, 4, 4), 4)
    for p in (S.STANDARD, S.Params(0.5), S.Params(1.0, 1.0, 1.0)):
        r = S.savings(inst, p)
        assert r.routes == ((1,), (2,), (3,)) and r.merges == 0 and S.savings_sequential(inst, p) == ((2,), (1,), (3,))          # fernster Kunde zuerst, Gleichstand: kleinere Nummer


def test_all_customers_on_one_point_fill_the_vehicles_pair_by_pair():
    same = Instance(((0.0, 0.0),) + ((3.0, 4.0),) * 4, (1, 1, 1, 1), 2)
    result = S.savings(same)
    assert all(s.saving == pytest.approx(10.0) for s in result.steps) and result.routes == ((1, 2), (3, 4)) and A.plan_length(same, result.routes) == pytest.approx(20.0)
    assert S.savings_sequential(same) == ((2, 1), (4, 3))


def test_a_customer_on_the_depot_has_no_positive_saving_at_lambda_one_and_below_ties():
    inst = Instance(((0.0, 0.0), (0.0, 0.0), (3.0, 4.0), (-3.0, 4.0)), (1, 1, 1), 2)
    assert all(1 not in (i, j) for _, i, j in S.savings_list(inst))
    assert A.plan_length(inst, S.savings(inst).routes) == pytest.approx(16.0)


def test_ties_in_the_saving_go_to_the_smaller_customer_numbers_for_every_lambda():
    inst = Instance(((0.0, 0.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0)), (1, 1, 1, 1), 2)
    for lam in (0.5, 1.0):
        listed = S.savings_list(inst, S.Params(lam))
        adjacent = [(i, j) for s, i, j in listed if math.isclose(s, listed[0][0])]
        assert adjacent == sorted(adjacent)
    assert sorted(tuple(sorted(r)) for r in S.savings(inst).routes) == [(1, 2), (3, 4)]


def test_the_largest_noise_and_all_runs_are_valid():
    inst = make_instance(12, 2, 1, 3, 9, 90)
    runs = S.noise_runs(inst, S.Params(1.0, 1.0, 1.0), C.EPS_MAX / 100, C.RUNS_MAX, 9)
    assert len(runs) == C.RUNS_MAX and all(A.is_feasible_plan(inst, r) for r in runs)
    study = ev.noise_study(ev.Settings(12, 2, 1, 3, 90, 9), S.STANDARD, C.EPS_MAX, C.RUNS_MAX)
    assert study["k"] == C.RUNS_MAX and 1 <= study["distinct"] <= C.RUNS_MAX and study["best"] == pytest.approx(min(study["costs"])) and study["mean"] == pytest.approx(sum(study["costs"]) / C.RUNS_MAX)


def test_every_control_limit_gives_a_valid_analysis():
    for n in (C.N_MIN, C.N_MAX):
        for fill in (C.FILL_MIN, C.FILL_MAX):
            for routes in (C.ROUTES_MIN, C.ROUTES_MAX):
                a = ev.analyse(ev.Settings(n, 2, 1, routes, fill, C.SEED_MAX))
                assert all(p.cost >= a.exact.cost - 1e-9 and A.is_feasible_plan(a.inst, p.routes) for p in a.strategies.values())
                assert set(a.curve_par) == set(C.LAM_CURVE) == set(a.curve_seq)
                assert ev.verdict_strategies(a)[1]
                for p in (S.Params(C.LAM_MIN), S.Params(C.LAM_MAX, C.MU_MAX, C.NU_MIN), S.Params(1.0, C.MU_MAX, C.NU_MAX)):
                    res, base = S.savings(a.inst, p), S.savings(a.inst)
                    assert ev.verdict_lambda(a, p, res, base)[1] and ev.verdict_sequential(a, p, res.routes, S.savings_sequential(a.inst, p))[1]
                assert ev.verdict_swaps(ev.swap_info(a.settings, S.STANDARD), 1.0)[1]


def test_helpers_at_their_edges():
    assert ev.gap_percent(10.0, 0.0) == 0.0 and ev.gap_percent(5.0 + 1e-12, 5.0) == 0.0 and ev.gap_percent(4.0, 5.0) == 0.0 and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.diff_percent(5.0, 5.0 + 1e-12) == 0.0 and ev.diff_percent(11.0, 10.0) == pytest.approx(10.0) and ev.diff_percent(9.0, 10.0) == pytest.approx(-10.0) and ev.diff_percent(1.0, 0.0) == 0.0
    assert ev.reduction_percent(100.0, 90.0) == pytest.approx(10.0) and ev.reduction_percent(100.0, 100.0 + 1e-12) == 0.0 and ev.reduction_percent(90.0, 100.0) == 0.0
    assert ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(0.5) == "+0,5 %" and ev.signed_pct(-1.3) == "−1,3 %"
    assert ev.de(3.14159) == "3,14" and ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz" and ev.runs_word(1) == "1 Lauf" and ev.runs_word(20) == "20 Läufe"
    assert ev.params_text(S.Params(1.0)) == "λ = 1,0" and ev.params_text(S.Params(0.8, 0.5, -1.0)) == "λ = 0,8, μ = 0,5, ν = -1,0"
    assert ev.pct(4.26) == "4,3 %" and ev.pct(4.24) == "4,2 %"


def test_the_lambda_grid_of_the_curve_and_of_the_strategies():
    assert C.LAM_CURVE[0] == C.LAM_MIN and C.LAM_CURVE[-1] == C.LAM_MAX and len(C.LAM_CURVE) == 23 and 1.0 in C.LAM_CURVE
    assert S.LAMS == (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0) and len(S.GRID) == 36 and all(lam in C.LAM_CURVE for lam in S.LAMS)
