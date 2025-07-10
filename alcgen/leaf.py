from dataclasses import dataclass


@dataclass
class Leaf:
    atoms: set[int]
    shared: set[int]
    linked: set[int]


@dataclass
class Leafs:
    op: int | None
    leafs: list["Leafs"] | Leaf
    depth: int
