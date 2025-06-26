from typing import Sequence, TypeVar

from alcgen.generator import Generator, CAssertion, ABox
from alcgen.guide import Guide

_T = TypeVar('_T')


class MockGuide(Guide):
    def __init__(self, rules: list[int], n: int | None = None):
        super().__init__()
        self.rules = rules
        if n is None:
            self.n = len(self.rules)
        else:
            self.n = n

    def _select(self, items: list[_T]) -> _T:
        return min(items)

    def rule(self, n_rules: int) -> Sequence[int]:
        r = self.rules.pop(0)
        assert r < n_rules
        return [r]

    def steps(self) -> int:
        return self.n


def test_and():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    i2 = g._new_individual()
    aboxes = g._and([ABox({CAssertion(c0, i0)}, set(), set(), set()),
                     ABox({CAssertion(c1, i0)}, set(), set(), set()),
                     ABox({CAssertion(c0, i1), CAssertion(c0, i2), CAssertion(c1, i1)}, set(), set(), set()),
                     ])
    assert len(aboxes) == 3
    assert aboxes[0].c_assertions == {CAssertion(2, i0), CAssertion(3, i0)}
    assert aboxes[0].fresh == {CAssertion(2, i0), CAssertion(3, i0)}
    assert aboxes[1].c_assertions == {CAssertion(c1, i0)}
    assert len(aboxes[1].fresh) == 0
    assert aboxes[2].c_assertions == {CAssertion(2, i1), CAssertion(3, i1), CAssertion(2, i2), CAssertion(3, i2),
                                      CAssertion(c1, i1)}
    assert aboxes[2].fresh == {CAssertion(2, i1), CAssertion(3, i1), CAssertion(2, i2), CAssertion(3, i2)}


def test_or_impossible_lonely_assertion():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([ABox({CAssertion(c0, i0)}, set(), set(), set())])
    assert aboxes is None


def test_or_impossible_only_one_other_assertion():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([ABox({CAssertion(c0, i0), CAssertion(c1, i0)}, set(), set(), set())])
    assert aboxes is None


def test_or_possible():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([ABox({CAssertion(c0, i0), CAssertion(c1, i0), CAssertion(c2, i0)}, set(), set(), set())])
    assert len(aboxes) == 2
    assert aboxes[0].c_assertions == {CAssertion(3, i0), CAssertion(c1, i0), CAssertion(c2, i0)}
    assert aboxes[0].fresh == {CAssertion(3, i0)}
    assert aboxes[1].c_assertions == {CAssertion(4, i0), CAssertion(c1, i0), CAssertion(c2, i0)}
    assert aboxes[1].fresh == {CAssertion(4, i0)}
    assert g._blocked[c1]
    assert g._blocked[c2]


def test_or_impossible_wrong_individuals():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    aboxes = g._or([ABox({CAssertion(c0, i0), CAssertion(c1, i0), CAssertion(c2, i1)}, set(), set(), set())])
    assert aboxes is None


def test_or_impossible_no_common():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    c3 = g._new_class()
    c4 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([ABox({CAssertion(c0, i0), CAssertion(c1, i0), CAssertion(c2, i0)}, set(), set(), set()),
                    ABox({CAssertion(c0, i0), CAssertion(c3, i0), CAssertion(c4, i0)}, set(), set(), set()),
                    ABox({CAssertion(c3, i0), CAssertion(c1, i0), CAssertion(c2, i0)}, set(), set(), set()),
                    ABox({CAssertion(c4, i0), CAssertion(c1, i0), CAssertion(c2, i0)}, set(), set(), set()),
                    ])
    assert aboxes is None

# def test_nothing():
#     ce = Generator(MockGuide([], 3)).run(True)
#     assert ce == (AND, (AND, 1, 2), (AND, (NOT, 2), 3))
#
#
# def test_and():
#     ce = Generator(MockGuide([0], 4)).run(True)
#     assert ce == (AND, (AND, (AND, (3, 2), 1), 2), (AND, 3, 4))
#
#
# def test_or():
#     ce = Generator(MockGuide([1], 4)).run(True)
#     assert ce == (4, (4, (5, (3, 1), (3, 2)), 1), (4, 2, 3))
