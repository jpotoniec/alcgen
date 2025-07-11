import pytest

from alcgen.aux import minimizing_mapping
from alcgen.generator import generate, compute_constraints, closing_mapping, Generator
from alcgen.guide import Guide


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
    symbols = n.symbols()
    assert len(symbols) == 1
    assert len(symbols[0]) == 6
    mapping = minimizing_mapping(symbols, list(compute_constraints(n)))
    assert len(mapping.keys()) == 6
    assert len(set(mapping.values())) == 6
