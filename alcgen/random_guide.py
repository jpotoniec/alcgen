import copy
import itertools
from collections import defaultdict, Counter
from typing import Collection

import numpy as np

from alcgen.guide import Guide
from alcgen.syntax import CE, AND, ANY, OR, TOP, to_pretty, ALL, NOT, to_manchester


class RandomGuide(Guide):
    def __init__(self, rng: np.random.Generator):
        self.rng = rng

    def n_conjuncts(self, depth: int, universal: bool) -> int:
        return int(self.rng.integers(1, 3))

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        if universal:
            return 0
        else:
            return 2

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[int]:
        return [1] * int(self.rng.integers(0, 4))

    def universal_roles(self, depth: int, roles: dict[int, int], universal: bool) -> list[int]:
        candidates = [r for r, v in roles.items() if v >= 2]
        return candidates