import copy
import itertools
from collections import defaultdict, Counter
from typing import Collection

import numpy as np

from alcgen.syntax import CE, AND, ANY, OR, TOP, to_pretty, ALL, NOT, to_manchester




class Guide:
    def n_conjuncts(self, depth: int, universal: bool) -> int:
        ...

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        ...

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[int]:
        ...

    def universal_roles(self, depth: int, roles: Collection[int], universal: bool) -> list[int]:
        ...