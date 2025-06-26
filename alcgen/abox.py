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


@dataclass(frozen=True)
class ABox:
    c_assertions: frozenset[CAssertion]
    r_assertions: frozenset[RAssertion]
    fresh: frozenset[CAssertion]
    forbidden: frozenset[PartialRAssertion]

    def __repr__(self):
        return "{" + ", ".join(
            [repr(a) + ("*" if a in self.fresh else "") for a in chain(self.c_assertions, self.r_assertions)]) + "}"

    def __str__(self):
        return repr(self)
