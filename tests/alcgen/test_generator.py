import copy
import json

import numpy as np
import pytest

from alcgen.configuration import DatasetConfiguration
from alcgen.cooccurrences import Cooccurrences
from alcgen.generator import generate, compute_constraints, merge_constraint_into_symbols, closing_mapping, \
    Generator, minimizing_mapping
from alcgen.guide import Guide
from alcgen.node import Node
from alcgen.random_guide import RandomGuide


class BaselineGuide(Guide):
    def n_conjuncts(self, depth: int, universal: bool) -> int:
        return 2

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        if universal:
            return 0
        else:
            return 2

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
        return [(1, depth - 1), (1, depth - 1)]

    def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
        return [(1, depth - 1)]


@pytest.mark.parametrize("d", range(0, 6))
def test_baseline(d: int):
    guide = BaselineGuide()
    ce = generate(d, guide, True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 6))
def test_disjuncts_in_universals(d: int):
    class MyGuide(BaselineGuide):
        def n_disjuncts(self, depth: int, universal: bool) -> int:
            return 2

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 5))
def test_no_disjuncts(d: int):
    class MyGuide(BaselineGuide):
        def n_disjuncts(self, depth: int, universal: bool) -> int:
            return 0

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 6))
def test_one_conjunct(d: int):
    class MyGuide(BaselineGuide):
        def n_conjuncts(self, depth: int, universal: bool) -> int:
            return 1

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 6))
def test_no_universals(d: int):
    class MyGuide(BaselineGuide):
        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return []

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 6))
def test_no_existential(d: int):
    class MyGuide(BaselineGuide):
        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            return []

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


@pytest.mark.parametrize("d", range(0, 4))
def test_many_existentials_no_universals(d: int):
    class MyGuide(BaselineGuide):
        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            return [(1, depth - 1)] * 10

        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return []

    ce = generate(d, MyGuide(), True, True)
    assert ce is not None


def test_constraints():
    class MyGuide(BaselineGuide):
        def n_disjuncts(self, depth: int, universal: bool) -> int:
            return 0

    node = generate(2, MyGuide(), False, False, ce=False)
    eager = list(compute_constraints(node, lazy=False))
    assert eager == [({9, 10}, {17, 18}), ({5, 6}, {8, 7}), ({13, 14}, {16, 15}), ({21, 22}, {23, 24})]
    lazy = list(compute_constraints(node, lazy=True))
    assert lazy == [({3, 4}, {11, 12}), ({5, 6}, {8, 7}), ({13, 14}, {16, 15}), ({21, 22}, {23, 24})]


def test_merge_constraint_into_symbols_partial():
    cooccurences = Cooccurrences()
    for item in [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                 {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]:
        cooccurences.add(item)
    merge_constraint_into_symbols(cooccurences, ({9, 10}, {17, 18}))
    assert cooccurences.has_nonempty_intersection({9}, {17, 18})


def test_merge_constraint_into_symbols_full():
    cooccurences = Cooccurrences()
    for item in [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                 {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]:
        cooccurences.add(item)
    original = copy.deepcopy(cooccurences)
    merge_constraint_into_symbols(cooccurences, ({5, 6}, {25, 26}))
    assert original.to_list() == cooccurences.to_list()


def test_merge_constraint_into_symbols_missing():
    cooccurences = Cooccurrences()
    for item in [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                 {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]:
        cooccurences.add(item)
    merge_constraint_into_symbols(cooccurences, ({30, 31}, {32, 33}))
    lists = [l for l in cooccurences.to_list() if 30 in l or 31 in l]
    assert len(lists) == 1
    x = lists[0]
    assert len(x) == 2
    assert len(x & {30, 31}) == 1
    assert len(x & {32, 33}) == 1


def test_closing_mapping_prefers_deeper():
    class MyGuide(BaselineGuide):
        def __init__(self):
            self.ctr = 0

        def n_disjuncts(self, depth: int, universal: bool) -> int:
            return 0

        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            if depth == 2:
                return [(1, depth - 1)] * 2
            elif depth == 1:
                self.ctr += 1
                if self.ctr == 2:
                    return [(1, depth - 1)]
                else:
                    return []

        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return []

    n = generate(2, MyGuide(), False, False, ce=False)
    mapping = closing_mapping(n.leafs())
    assert mapping == {7: -8} or mapping == {8: -7}


def test_minimize_not_closed():
    n = Generator().generate(0, BaselineGuide())
    cooccurrences = n.cooccurrences()
    assert cooccurrences.to_list() == [{1, 2, 3, 4, 5, 6}]
    for constraint in compute_constraints(n):
        merge_constraint_into_symbols(cooccurrences, constraint)
    mapping = minimizing_mapping(cooccurrences)
    assert len(mapping.keys()) == 6
    assert len(set(mapping.values())) == 6


def test_forall_not_included_in_closing_mapping():
    n = Node(1, (1, Node(2)))
    n.add_universal(1, Node(3))
    mapping = closing_mapping(n.leafs())
    assert mapping == {2: -3} or mapping == {3: -2}


def test_closing_forall_with_existential_inside():
    text = """{"min_depth":2,"max_depth":2,"n_instances":1,"save_open":false,"save_open_minimized":false,"save_closed":false,"save_closed_minimized":true,"seed_depth":0,"seed_instance":0,"seed_const":4227725670,"prefix":"http://example.com/foo","guide":{"conjuncts_low":1,"conjuncts_high":3,"disjuncts_p":0.0,"disjuncts_low":2,"disjuncts_high":2,"n_roles":1,"existential_low":0,"existential_high":3,"existential_depth":"max","existential_force_depth":"uniform","universal_threshold_low":2,"universal_threshold_high":2,"universal_depth":"max"},"universal_guide":null}"""
    cfg = DatasetConfiguration(**json.loads(text))
    n = generate(cfg.min_depth, RandomGuide(np.random.default_rng(cfg.seed_const), cfg.guide, cfg.universal_guide),
                 False, False, ce=False)
    assert len(closing_mapping(n.leafs())) > 0
