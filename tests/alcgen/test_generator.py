from typing import Sequence, TypeVar

from alcgen.abox import PartialRAssertion, RAssertion
from alcgen.generator import Generator, CAssertion, ABox
from alcgen.guide import Guide
from alcgen.syntax import ANY

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


def test_exists_candidates_no_roles():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    candidates = g._exists_candidates([ABox({CAssertion(c0, i0)}, set(), set(), set())])
    assert len(candidates) == 0


def test_exists_candidates1():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    candidates = g._exists_candidates([ABox({CAssertion(c0, i0), CAssertion(c0, i1)}, set(), set(), set())])
    assert candidates == [(c0, r0)]


def test_exists_candidates2():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    candidates = g._exists_candidates([ABox({CAssertion(c0, i0), CAssertion(c1, i1)}, set(), set(), set())])
    assert candidates == [(c0, r0), (c1, r0)]


def test_exists_candidates3():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    r1 = g._new_role()
    candidates = g._exists_candidates(
        [ABox({CAssertion(c0, i0), CAssertion(c1, i1)}, set(), set(), {PartialRAssertion(r1, i1)})])
    assert candidates == [(c0, r0), (c0, r1), (c1, r0)]


def test_exists_new_role():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._exists([ABox({CAssertion(c0, i0), CAssertion(c1, i0)}, set(), set(), set()),
                        ABox({CAssertion(c1, i0)}, set(), set(), set())]
                       )
    assert g.n_roles == 1
    assert len(aboxes) == 2
    assert aboxes[0].c_assertions == {CAssertion(2, 1), CAssertion(c1, i0)}
    assert aboxes[0].r_assertions == {RAssertion(0, 0, 1)}
    assert aboxes[0].fresh == {CAssertion(2, 1)}
    assert len(aboxes[0].forbidden) == 0
    assert aboxes[1].c_assertions == {CAssertion(c1, i0)}
    assert len(aboxes[1].r_assertions) == 0
    assert len(aboxes[1].fresh) == 0
    assert len(aboxes[1].forbidden) == 0
    assert g._definitions[0] == (ANY, 0, 2)


def test_exists_existing_role():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    aboxes = g._exists(
        [ABox({CAssertion(c0, i0), CAssertion(c1, i1)}, {RAssertion(r0, i0, i1)}, set(), {PartialRAssertion(r0, i0)})]
    )
    assert g.n_roles == 1
    assert len(aboxes) == 1
    assert aboxes[0].c_assertions == {CAssertion(2, 2), CAssertion(c0, i0)}
    assert aboxes[0].r_assertions == {RAssertion(r0, i0, i1), RAssertion(0, 1, 2)}
    assert aboxes[0].fresh == {CAssertion(2, 2)}
    assert g._definitions[1] == (ANY, r0, 2)

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
