from collections import defaultdict
from dataclasses import dataclass
from itertools import chain


@dataclass(frozen=True)
class CAssertion:
    c: int
    i: int

    def __repr__(self):
        return f"{self.c}({self.i})"

    def __str__(self):
        return self.__repr__()


@dataclass(frozen=True)
class RAssertion:
    r: int
    i: int
    f: int

    def __repr__(self):
        return f"{self.r}({self.i}, {self.f})"

    def __str__(self):
        return self.__repr__()


@dataclass(frozen=True)
class PartialRAssertion:
    r: int
    i: int


class ABox:
    c_assertions: frozenset[CAssertion]
    r_assertions: frozenset[RAssertion]
    fresh: frozenset[CAssertion]
    forbidden: frozenset[PartialRAssertion]
    _c2i: dict[int, set[int]]
    _i2c: dict[int, set[int]]

    def __init__(self, c_assertions: set[CAssertion], r_assertions: set[RAssertion], fresh: set[CAssertion],
                 forbidden: set[PartialRAssertion]):
        self.c_assertions = frozenset(c_assertions)
        self.r_assertions = frozenset(r_assertions)
        self.fresh = frozenset(fresh)
        self.forbidden = frozenset(forbidden)
        self._c2i = defaultdict(set)
        self._i2c = defaultdict(set)
        for ca in self.c_assertions:
            self._c2i[ca.c].add(ca.i)
            self._i2c[ca.i].add(ca.c)

    def __repr__(self):
        return "{" + ", ".join(
            [repr(a) + ("*" if a in self.fresh else "") for a in chain(self.c_assertions, self.r_assertions)]) + "}"

    def __str__(self):
        return repr(self)

    def individuals_of_class(self, class_: int) -> set[int]:
        return self._c2i[class_]

    def classes_of_individual(self, individual: int) -> set[int]:
        return self._i2c[individual]

    def has_class(self, class_: int) -> bool:
        return class_ in self._c2i

    def lfillers_of_role(self, role: int) -> set[int]:
        return {ra.i for ra in self.r_assertions if ra.r == role}

    def rfillers(self, role: int, lfiller: int | None) -> set[int]:
        if lfiller is not None:
            return {ra.f for ra in self.r_assertions if ra.r == role and ra.i == lfiller}
        else:
            return {ra.f for ra in self.r_assertions if ra.r == role}

    def __hash__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        return isinstance(other, ABox) and self.c_assertions == other.c_assertions and \
            self.r_assertions == other.r_assertions and self.fresh == other.fresh and self.forbidden == other.forbidden
