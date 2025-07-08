import pytest

from alcgen.generator import generate
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


@pytest.mark.parametrize("d", range(0, 6))
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
