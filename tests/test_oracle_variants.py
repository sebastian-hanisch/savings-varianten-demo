"""Orakel-Tests savings-varianten-demo: Savings mit Formparametern, sequentielle Fassung und Mehrfachläufe gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §2).

- Parallel: eigene Fassung in reinem Python (math.hypot, Listen), die in jedem Schritt das beste noch zulässige Paar wählt (statt eine sortierte Liste einmal abzulaufen) und die allgemeine Ersparnis
  mit λ, μ und ν selbst berechnet. Nur Familien mit stetigen Koordinaten (1 und 2), weil bei ganzzahligen Koordinaten Gleichstände von Rundungsfehlern abhängen.
- Sequentiell: eigene rekursive Fassung (Route als Liste, Fortsetzung am Rand).
- Mehrfachläufe: Bestes von k Läufen gegen eine eigene Schleife; Rauschen gegen eine eigene Ziehung aus demselben Erzeuger.
- Split und exakter Löser: Aufzählung aller Schnittmengen beziehungsweise aller Zerlegungen (Kern unverändert, hier kurz gegengeprüft).
Mini-Instanzen mit festen Seeds (range), insgesamt wenige Sekunden."""

import itertools
import math

import numpy as np
import pytest

import svv_algorithm as A
import svv_savings as S
from svv_scenario import make_instance

CELLS = [(f, d, r) for f in (1, 2) for d in (0, 1) for r in (2, 3)]
PARAMS = [S.Params(1.0), S.Params(0.8), S.Params(1.4), S.Params(1.0, 0.5, 0.0), S.Params(1.2, 0.0, 1.0), S.Params(0.6, 1.0, -0.5)]


def _dist(inst, a, b):
    (xa, ya), (xb, yb) = inst.xy[a], inst.xy[b]
    return math.hypot(xa - xb, ya - yb)


def _route(inst, customers):
    path = (0, *customers, 0)
    return sum(_dist(inst, u, v) for u, v in zip(path, path[1:]))


def _saving(inst, p, i, j):
    qbar = sum(inst.demand) / inst.n
    return (_dist(inst, 0, i) + _dist(inst, 0, j) - p.lam * _dist(inst, i, j) + p.mu * abs(_dist(inst, 0, i) - _dist(inst, 0, j)) + p.nu * (inst.demand[i - 1] + inst.demand[j - 1]) / qbar)


def _oracle_parallel(inst, p):
    routes = [[c] for c in range(1, inst.n + 1)]
    while True:
        best = None
        for i in range(1, inst.n + 1):
            for j in range(i + 1, inst.n + 1):
                s = _saving(inst, p, i, j)
                if s <= 0:
                    continue
                ra = next(r for r in routes if i in r)
                rb = next(r for r in routes if j in r)
                if ra is rb or i not in (ra[0], ra[-1]) or j not in (rb[0], rb[-1]):
                    continue
                if sum(inst.demand[c - 1] for c in ra + rb) > inst.capacity:
                    continue
                if best is None or (s, -i, -j) > (best[0], -best[1], -best[2]):
                    best = (s, i, j, ra, rb)
        if best is None:
            return routes
        _, i, j, ra, rb = best
        left = ra if ra[-1] == i else ra[::-1]
        right = rb if rb[0] == j else rb[::-1]
        routes = [r for r in routes if r is not ra and r is not rb] + [left + right]


def _oracle_sequential(inst, p):
    free = list(range(1, inst.n + 1))
    plan = []
    while free:
        start = min(free, key=lambda c: (-_dist(inst, 0, c), c))
        free.remove(start)
        route = [start]
        load = inst.demand[start - 1]
        while True:
            options = []
            for c in sorted(free):
                if load + inst.demand[c - 1] > inst.capacity:
                    continue
                options.append((_saving(inst, p, route[0], c), c, "front"))
                options.append((_saving(inst, p, route[-1], c), c, "back"))
            if not options:
                break
            top = options[0]
            for o in options[1:]:
                if o[0] > top[0] + 1e-12:
                    top = o
            if top[0] <= 0:
                break
            _, c, side = top
            route = [c] + route if side == "front" else route + [c]
            load += inst.demand[c - 1]
            free.remove(c)
        plan.append(route)
    return plan


def _canon(routes):
    return sorted(tuple(r) if r[0] <= r[-1] else tuple(r[::-1]) for r in routes)


def _cuts(inst, order):
    n = len(order)
    for mask in range(1 << (n - 1)):
        routes, current = [], [order[0]]
        for t in range(1, n):
            if (mask >> (t - 1)) & 1:
                routes.append(current)
                current = []
            current.append(order[t])
        routes.append(current)
        if all(sum(inst.demand[c - 1] for c in r) <= inst.capacity for r in routes):
            yield routes


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_parallel_savings_with_parameters_matches_the_independent_best_pair_version(family, depot, routes):
    for seed in range(8):
        inst = make_instance(8 + seed % 5, family, depot, routes, seed, 60 + 4 * seed)
        for p in PARAMS:
            assert _canon(S.savings(inst, p).routes) == _canon(_oracle_parallel(inst, p)), (seed, p)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_parallel_savings_matches_the_oracle_at_25_customers(family, depot, routes):
    for seed in range(3):
        inst = make_instance(25, family, depot, routes, seed, 70 + 5 * seed)
        for p in (S.Params(1.0), S.Params(1.2, 0.5, 0.5)):
            assert _canon(S.savings(inst, p).routes) == _canon(_oracle_parallel(inst, p)), (seed, p)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_sequential_savings_matches_the_independent_version(family, depot, routes):
    for seed in range(8):
        inst = make_instance(8 + seed % 6, family, depot, routes, seed, 60 + 4 * seed)
        for p in PARAMS:
            ours = [list(r) for r in S.savings_sequential(inst, p)]
            assert _canon(ours) == _canon(_oracle_sequential(inst, p)), (seed, p)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_best_of_k_runs_matches_an_independent_loop(family, depot, routes):
    for seed in range(5):
        inst = make_instance(12, family, depot, routes, seed, 85)
        plans = [S.savings(inst, S.Params(lam)).routes for lam in S.LAMS]
        costs = [sum(_route(inst, r) for r in plan) for plan in plans]
        cost, best = S.best_of(inst, plans)
        assert cost == pytest.approx(min(costs)) and best == plans[costs.index(min(costs))]
        grid = [S.savings(inst, S.Params(*t)).routes for t in S.GRID]
        assert S.best_of(inst, plans + grid)[0] == pytest.approx(min(min(costs), min(sum(_route(inst, r) for r in g) for g in grid)))


def test_noise_runs_match_an_independent_draw_from_the_same_generator():
    """Der Test zieht selbst aus numpy.random.default_rng(seed + 11) und rechnet jedes Paar einzeln."""
    for seed in (0, 1, 2):
        inst = make_instance(10, 1, 0, 3, seed, 85)
        rng = np.random.default_rng(seed + 11)
        iu, ju = np.triu_indices(inst.n, 1)
        expected = []
        for _ in range(4):
            draws = rng.uniform(-1, 1, size=len(iu))
            pairs = sorted(((_saving(inst, S.STANDARD, int(i) + 1, int(j) + 1) * (1 + 0.05 * u), int(i) + 1, int(j) + 1) for i, j, u in zip(iu, ju, draws)), key=lambda t: (-t[0], t[1], t[2]))
            expected.append(_canon(S.run_pairs(inst, [p for p in pairs if p[0] > 0])))
        assert [_canon(r) for r in S.noise_runs(inst, S.STANDARD, 0.05, 4, seed)] == expected, seed


@pytest.mark.parametrize("family,depot,routes", CELLS[::2])
def test_split_and_exact_still_match_the_enumeration(family, depot, routes):
    for seed in range(3):
        inst = make_instance(7, family, depot, routes, seed, 80)
        order = tuple(int(c) + 1 for c in np.random.default_rng(seed).permutation(7))
        assert A.split(inst, order).cost == pytest.approx(min(sum(_route(inst, r) for r in cut) for cut in _cuts(inst, order)))
    inst = make_instance(6, family, depot, routes, 1, 80)
    best = min(A.split(inst, p).cost for p in itertools.permutations(range(1, 7)))
    assert best == pytest.approx(A.exact_cvrp(inst).cost)
