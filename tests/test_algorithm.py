"""Savings mit Formparametern, sequentielle Fassung und Kern an Handinstanzen (PLAN-05): jede Zahl ist hier von Hand aus Wurzeln zusammengesetzt.

Kleine Karte (conftest.py `small`): Depot (8,8); Kunden 1 (16,10), 2 (11,15), 3 (9,13), 4 (14,3), 5 (0,5), 6 (4,14); Nachfragen 4, 1, 2, 4, 1, 4; Kapazität 9; Optimum 56,73."""

import math

import pytest

import svv_algorithm as A
import svv_construct as K
import svv_evaluation as ev
import svv_savings as S
from conftest import OPTIMUM, TOUR_LENGTH
from svv_scenario import make_instance

SQ68, SQ58, SQ26, SQ61, SQ73, SQ52 = (math.sqrt(v) for v in (68, 58, 26, 61, 73, 52))
D0 = {1: SQ68, 2: SQ58, 3: SQ26, 4: SQ61, 5: SQ73, 6: SQ52}
PAIRS = [(i, j) for i in range(1, 7) for j in range(i + 1, 7)]
ROUND2 = 0.005


def _d(small, i, j):
    return math.dist(small.xy[i], small.xy[j])


def _expected(small, lam, mu=0.0, nu=0.0):
    qbar = sum(small.demand) / 6
    return {(i, j): D0[i] + D0[j] - lam * _d(small, i, j) + mu * abs(D0[i] - D0[j]) + nu * (small.demand[i - 1] + small.demand[j - 1]) / qbar for i, j in PAIRS}


def test_the_small_instance_is_the_generator_instance(small):
    assert make_instance(6, 0, 0, 2, 7, 90) == small
    assert small.min_routes == 2 and A.exact_cvrp(small).cost == pytest.approx(56.73, abs=ROUND2)


def test_the_savings_at_lambda_one_by_hand_and_their_order(small):
    listed = S.savings_list(small)
    assert [(i, j) for _, i, j in listed] == [(2, 3), (1, 2), (1, 4), (2, 6), (3, 6), (5, 6), (1, 3), (2, 4), (1, 6), (4, 5), (3, 4), (3, 5), (2, 5), (4, 6), (1, 5)]
    expected = _expected(small, 1.0)
    for s, i, j in listed:
        assert s == pytest.approx(expected[(i, j)]), (i, j)
    assert [round(s, 2) for s, _, _ in listed[:4]] == [9.89, 8.79, 8.78, 7.76]
    assert S.savings_list(small, S.Params(1.0)) == listed and S.STANDARD == S.Params()


def test_the_close_pair_at_lambda_one_decides_the_plan(small):
    """(1,2) mit 8,79 steht vor (1,4) mit 8,78; nach (1,2) und (2,3) ist die Last 7, und (1,4) scheitert an der Kapazität (7 + 4 > 9)."""
    result = S.savings(small)
    assert [s.outcome for s in result.steps] == [S.MERGED, S.MERGED, S.CAPACITY, S.NO_END, S.CAPACITY, S.MERGED, S.SAME_ROUTE, S.NO_END, S.CAPACITY, S.MERGED, S.CAPACITY, S.NO_END, S.NO_END, S.SAME_ROUTE, S.NO_END]
    assert S.canonical(result.routes) == ((1, 2, 3), (4, 5, 6))
    assert A.plan_length(small, result.routes) == pytest.approx(62.26, abs=ROUND2)
    assert (result.merges, result.count(S.CAPACITY), result.count(S.SAME_ROUTE), result.count(S.NO_END)) == (4, 4, 2, 5)


def test_at_lambda_point_eight_the_order_flips_and_savings_hits_the_optimum(small):
    p = S.Params(0.8)
    listed = S.savings_list(small, p)
    assert [(i, j) for _, i, j in listed][:6] == [(2, 3), (1, 4), (1, 2), (2, 6), (3, 6), (5, 6)]
    expected = _expected(small, 0.8)
    assert [round(s, 2) for s, _, _ in listed[:3]] == [10.45, 10.23, 10.21] and all(s == pytest.approx(expected[(i, j)]) for s, i, j in listed)
    result = S.savings(small, p)
    assert [s.outcome for s in result.steps[:6]] == [S.MERGED, S.MERGED, S.CAPACITY, S.MERGED, S.SAME_ROUTE, S.MERGED]
    assert sorted(map(sorted, result.routes)) == [[1, 4], [2, 3, 5, 6]]
    assert A.plan_length(small, result.routes) == pytest.approx(56.73, abs=ROUND2) == pytest.approx(A.exact_cvrp(small).cost, abs=ROUND2)


def test_first_difference_between_lambda_one_and_point_eight(small):
    fd = ev.first_difference(S.savings(small), S.savings(small, S.Params(0.8)))
    assert fd["merge_no"] == 2 and (fd["base"].i, fd["base"].j, fd["base"].rank) == (1, 2, 2) and (fd["other"].i, fd["other"].j, fd["other"].rank) == (1, 4, 2)
    assert ev.first_difference(S.savings(small), S.savings(small)) is None


def test_costs_over_lambda_by_hand(small):
    costs = {lam: A.plan_length(small, S.savings(small, S.Params(lam)).routes) for lam in S.LAMS}
    assert {lam: round(c, 2) for lam, c in costs.items()} == {0.4: 58.37, 0.6: 58.37, 0.8: 56.73, 1.0: 62.26, 1.2: 64.47, 1.4: 64.47, 1.6: 70.38, 1.8: 70.38, 2.0: 63.18}


def test_sequential_by_hand(small):
    routes = S.savings_sequential(small)
    assert sorted(map(sorted, routes)) == [[1, 4], [2, 3, 5, 6]]
    assert 5 in (routes[0][0], routes[0][-1])                                          # die erste Route beginnt beim fernsten Kunden 5 (8,54)
    assert A.plan_length(small, routes) == pytest.approx(56.73, abs=ROUND2)


def test_insertion_after_split_on_the_small_instance(small):
    r = A.split(small, K.insert_split_order(small))
    assert r.cost == pytest.approx(58.37, abs=ROUND2) and r.routes == ((2, 1, 4), (3, 6, 5))


def test_mu_and_nu_by_hand(small):
    s = {(i, j): v for v, i, j in S.savings_list(small, S.Params(1.0, 0.5, 1.0))}
    qbar = 16 / 6
    base23 = SQ58 + SQ26 - math.sqrt(8)
    assert s[(2, 3)] == pytest.approx(base23 + 0.5 * (SQ58 - SQ26) + (1 + 2) / qbar)
    assert round(s[(2, 3)], 2) == 12.27
    neg = {(i, j): v for v, i, j in S.savings_list(small, S.Params(1.0, 0.0, -1.0))}
    assert neg[(2, 3)] == pytest.approx(base23 - 3 / qbar)


def test_the_plan_instance_of_stueck_1_to_4_over_lambda(hand):
    for lam in (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6):
        assert A.plan_length(hand, S.savings(hand, S.Params(lam)).routes) == pytest.approx(OPTIMUM), lam
    # ab λ = 1,7 bleiben (3) und (5) allein (README: „kostet ab λ = 1,7 52,28“); 1,6 ist noch das Optimum
    for lam in (1.7, 1.8, 1.9, 2.0):
        r = S.savings(hand, S.Params(lam))
        assert S.canonical(r.routes) == ((1, 4), (2, 6), (3,), (5,)) and A.plan_length(hand, r.routes) == pytest.approx(52.28, abs=ROUND2), lam
    assert len(S.savings_list(hand, S.Params(2.0))) < 15 == len(S.savings_list(hand))


def test_kernel_split_exact_and_tour_from_earlier_pieces(hand):
    assert A.exact_cvrp(hand).cost == pytest.approx(OPTIMUM)
    length, order = A.tsp_tour(hand)
    assert length == pytest.approx(TOUR_LENGTH) and order == (2, 6, 3, 4, 1, 5)
    assert A.split(hand, (1, 4, 2, 6, 3, 5)).routes == ((1, 4), (2, 6, 3, 5))


def test_best_of_takes_the_cheapest_and_the_first_on_ties(small):
    plans = [S.savings(small, S.Params(lam)).routes for lam in S.LAMS]
    cost, routes = S.best_of(small, plans)
    assert cost == pytest.approx(56.73, abs=ROUND2) and routes == plans[S.LAMS.index(0.8)]
    assert S.best_of(small, [plans[0], plans[0]])[1] == plans[0]


def test_the_split_of_a_savings_plan_is_never_worse(small):
    for lam in S.LAMS:
        routes = S.savings(small, S.Params(lam)).routes
        assert S.savings_then_split(small, routes).cost <= A.plan_length(small, routes) + 1e-9
    assert S.savings_then_split(small, S.savings(small).routes).cost == pytest.approx(62.26, abs=ROUND2)      # bei λ = 1 ist der Plan hier ein Fixpunkt
