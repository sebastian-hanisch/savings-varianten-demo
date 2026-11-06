"""Eigenschaftstests (ORACLE-PLAYBOOK §5, Schicht „Eigenschaften“): Aussagen, die für jede Instanz gelten, an vielen festen Seeds geprüft.

Stetige Koordinaten (Familien 1 und 2) für alles, was von Gleichständen abhängt; die Aussagen ohne Gleichstände (Zulässigkeit, Ersparnis-Identität) laufen auch auf der kleinen Karte (Familie 0)."""

import dataclasses

import numpy as np
import pytest

import svv_algorithm as A
import svv_evaluation as ev
import svv_savings as S
from svv_scenario import Instance, distance_matrix, make_instance

ALL_CELLS = [(f, d, r) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3, 4)]
CONTINUOUS = [(f, d, r) for f in (1, 2) for d in (0, 1) for r in (2, 3)]
PARAMS = [S.Params(1.0), S.Params(0.6), S.Params(1.6), S.Params(1.0, 0.5, 0.0), S.Params(1.2, 0.0, 1.0), S.Params(0.8, 1.0, -0.5), S.Params(2.4)]


@pytest.mark.parametrize("family,depot,routes", ALL_CELLS)
def test_every_variant_gives_a_feasible_plan(family, depot, routes):
    for seed in range(4):
        inst = make_instance(8 + 4 * seed, family, depot, routes, seed, 60 + 8 * seed)
        for p in PARAMS:
            result = S.savings(inst, p)
            assert A.is_feasible_plan(inst, result.routes) and result.merges == inst.n - len(result.routes)
            assert A.is_feasible_plan(inst, S.savings_sequential(inst, p))
            assert result.routes == S.savings_routes(inst, p)


@pytest.mark.parametrize("family,depot,routes", ALL_CELLS)
def test_a_merge_shortens_by_the_plain_saving_for_every_parameter_and_by_s_only_at_lambda_one(family, depot, routes):
    for seed in range(3):
        inst = make_instance(12 + 3 * seed, family, depot, routes, seed, 62 + 7 * seed)
        D = distance_matrix(inst)
        for p in (S.Params(1.0), S.Params(0.7), S.Params(1.3, 0.5, 0.5)):
            result = S.savings(inst, p)
            before = A.plan_length(inst, S.routes_after(inst, result, 0))
            for step in result.steps:
                after = A.plan_length(inst, step.routes)
                plain = D[0][step.i] + D[0][step.j] - D[step.i][step.j]
                assert before - after == pytest.approx(plain if step.outcome == S.MERGED else 0.0, abs=1e-9), (seed, p, step.rank)
                if step.outcome == S.MERGED and p == S.STANDARD:
                    assert plain == pytest.approx(step.saving)
                before = after


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_best_of_k_runs_is_never_worse_than_one_run_and_never_better_than_the_optimum(family, depot, routes):
    for seed in range(4):
        inst = make_instance(10, family, depot, routes, seed, 80)
        optimum = A.exact_cvrp(inst).cost
        plans = ev.strategy_plans(inst, seed)
        assert plans["lam9"].cost <= plans["std"].cost + 1e-9 and plans["grid45"].cost <= plans["std"].cost + 1e-9
        assert plans["grid45"].cost <= plans["lam9"].cost + 1e-9                         # das Gitter enthält die neun λ-Werte
        assert plans["lam9"].cost <= plans["std"].cost + 1e-9                            # λ = 1 ist einer der neun Werte
        assert all(p.cost >= optimum - 1e-9 and A.is_feasible_plan(inst, p.routes) for p in plans.values())
        assert [plans[k].runs for k in ev.C.STRATEGY_KEYS] == [ev.C.STRATEGY_RUNS[k] for k in ev.C.STRATEGY_KEYS]


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_zero_noise_gives_the_plain_run_and_a_seed_gives_the_same_runs(family, depot, routes):
    for seed in range(3):
        inst = make_instance(12, family, depot, routes, seed, 80)
        plain = S.savings_routes(inst)
        assert all(r == plain for r in S.noise_runs(inst, S.STANDARD, 0.0, 3, seed))
        a = S.noise_runs(inst, S.STANDARD, 0.02, 5, seed)
        assert a == S.noise_runs(inst, S.STANDARD, 0.02, 5, seed)
        la = S.noisy_list(inst, S.STANDARD, 0.02, np.random.default_rng(seed + S.NOISE_SEED_OFFSET))
        lb = S.noisy_list(inst, S.STANDARD, 0.02, np.random.default_rng(seed + 1 + S.NOISE_SEED_OFFSET))
        assert [s for s, _, _ in la] != [s for s, _, _ in lb]                      # andere Seeds ziehen andere Zufallszahlen


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_noise_changes_plans_the_more_the_stronger_it_is(family, depot, routes):
    inst = make_instance(25, family, depot, routes, 3, 85)
    base = S.canonical(S.savings_routes(inst))
    same = {eps: np.mean([S.canonical(r) == base for r in S.noise_runs(inst, S.STANDARD, eps, 20, 3)]) for eps in (0.001, 0.01, 0.1)}
    assert same[0.001] >= same[0.1] and same[0.1] < 1.0


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_with_room_for_everyone_and_lambda_up_to_one_savings_builds_one_route(family, depot, routes):
    for seed in range(4):
        inst = dataclasses.replace(make_instance(12, family, depot, routes, seed), capacity=10 ** 6)
        for lam in (0.4, 1.0):
            result = S.savings(inst, S.Params(lam))
            assert len(result.routes) == 1 and result.count(S.CAPACITY) == 0


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_a_large_lambda_leaves_customers_alone_and_never_lowers_the_number_of_pairs_to_below_zero(family, depot, routes):
    inst = make_instance(15, family, depot, routes, 1, 85)
    counts = [len(S.savings_list(inst, S.Params(lam))) for lam in (0.2, 0.6, 1.0, 1.4, 2.0, 2.4)]
    assert counts == sorted(counts, reverse=True) and counts[-1] < counts[0]               # mit wachsendem λ bleiben weniger Paare mit s > 0
    assert len(S.savings(inst, S.Params(2.4)).routes) >= len(S.savings(inst, S.Params(0.6)).routes)


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_lambda_zero_orders_by_closeness_to_the_depot_only(family, depot, routes):
    inst = make_instance(12, family, depot, routes, 2, 85)
    D = distance_matrix(inst)
    listed = S.savings_list(inst, S.Params(0.0))
    assert len(listed) == inst.n * (inst.n - 1) // 2 and all(s == pytest.approx(D[0][i] + D[0][j]) for s, i, j in listed)


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_savings_ignores_moving_scaling_and_renumbering_for_every_parameter(family, depot, routes):
    for seed in range(3):
        inst = make_instance(12, family, depot, routes, seed, 75)
        moved = Instance(tuple((2 * x + 64, 2 * y + 128) for x, y in inst.xy), inst.demand, inst.capacity)
        rng = np.random.default_rng(seed)
        perm = [int(p) + 1 for p in rng.permutation(inst.n)]
        xy = [inst.xy[0]] + [None] * inst.n
        demand = [0] * inst.n
        for c in range(1, inst.n + 1):
            xy[perm[c - 1]] = inst.xy[c]
            demand[perm[c - 1] - 1] = inst.demand[c - 1]
        renamed = Instance(tuple(xy), tuple(demand), inst.capacity)
        for p in (S.Params(1.0), S.Params(0.8), S.Params(1.3, 0.0, 0.5)):
            base = S.canonical(S.savings(inst, p).routes)
            assert S.canonical(S.savings(moved, p).routes) == base, (seed, p)
            assert S.canonical(S.savings(renamed, p).routes) == S.canonical([tuple(perm[c - 1] for c in r) for r in S.savings(inst, p).routes]), (seed, p)


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_swap_sensitivity_matches_a_direct_recomputation(family, depot, routes):
    for seed in range(3):
        inst = make_instance(10, family, depot, routes, seed, 85)
        pairs = S.savings_list(inst)
        base = S.canonical(S.run_pairs(inst, pairs))
        rows = S.swap_sensitivity(inst)
        assert len(rows) == len(pairs) - 1 and [r["rank"] for r in rows] == list(range(1, len(pairs)))
        for r in rows:
            k = r["rank"] - 1
            swapped = pairs[:k] + [pairs[k + 1], pairs[k]] + pairs[k + 2:]
            assert r["changed"] == (S.canonical(S.run_pairs(inst, swapped)) != base)
            assert (r["change_pct"] != 0.0) <= r["changed"] and r["first"] == pairs[k] and r["second"] == pairs[k + 1]


def test_first_difference_is_symmetric_in_the_merge_number():
    for seed in range(6):
        inst = make_instance(10, 1, 0, 3, seed, 85)
        a, b = S.savings(inst, S.Params(0.7)), S.savings(inst, S.Params(1.4))
        fd, fd2 = ev.first_difference(a, b), ev.first_difference(b, a)
        assert (fd is None) == (fd2 is None)
        if fd:
            assert fd["merge_no"] == fd2["merge_no"] and fd["base"] == fd2["other"] and fd["other"] == fd2["base"]


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_sequential_plan_is_independent_of_the_reading_direction_of_the_routes(family, depot, routes):
    inst = make_instance(12, family, depot, routes, 4, 85)
    assert S.canonical(S.savings_sequential(inst)) == S.canonical([r[::-1] for r in S.savings_sequential(inst)])
