from typing import TypeVar, Sequence

import numpy as np

from alcgen.guide import Guide

_T = TypeVar('_T')


class RandomGuide(Guide):
    def __init__(self, gen: np.random.Generator, min_steps: int, max_steps: int):
        super().__init__()
        self._gen = gen
        self._min_steps = min_steps
        self._max_steps = max_steps

    def _select(self, items: list[_T]) -> _T:
        return self._gen.choice(items)

    def rule(self, n_rules: int) -> Sequence[int]:
        return self._gen.permutation(n_rules)

    def steps(self) -> int:
        return int(self._gen.integers(self._min_steps, self._max_steps))
