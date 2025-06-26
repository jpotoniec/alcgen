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

    def individuals_of_class(self, class_: int) -> set[int]:
        return {ca.i for ca in self.c_assertions if ca.c == class_}

    def classes_of_individual(self, individual: int) -> set[int]:
        return {ca.c for ca in self.c_assertions if ca.i == individual}

    def has_class(self, class_: int) -> bool:
        return any(ca.c == class_ for ca in self.c_assertions)

    def lfillers_of_role(self, role: int) -> set[int]:
        return {ra.i for ra in self.r_assertions if ra.r == role}

    def rfillers(self, role: int, lfiller: int | None) -> set[int]:
        if lfiller is not None:
            return {ra.f for ra in self.r_assertions if ra.r == role and ra.i == lfiller}
        else:
            return {ra.f for ra in self.r_assertions if ra.r == role}
