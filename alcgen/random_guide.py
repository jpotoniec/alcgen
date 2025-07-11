import numpy as np

from alcgen.configuration import RandomGuideConfiguration
from alcgen.guide import Guide


def policy_max(rng: np.random.Generator, n: int, depth: int) -> list[int]:
    return [depth - 1] * n


def policy_uniform(rng: np.random.Generator, n: int, depth: int) -> list[int]:
    return rng.integers(0, depth, n)


def policy_ascending(rng: np.random.Generator, n: int, depth: int) -> list[int]:
    if n >= depth:
        return list(range(depth)) + [depth - 1] * (n - depth)
    else:
        return list(range(depth - n, depth))


def policy_descending(rng: np.random.Generator, n: int, depth: int) -> list[int]:
    return list(reversed(policy_ascending(rng, n, depth)))


existential_policies = {
    'max': policy_max,
    'uniform': policy_uniform,
    'ascending': policy_ascending,
    'descending': policy_descending,
}


class RandomGuide(Guide):
    def __init__(self, rng: np.random.Generator, cfg: RandomGuideConfiguration | None = None,
                 universal_cfg: RandomGuideConfiguration | None = None):
        self.rng = rng
        self.cfg = cfg or RandomGuideConfiguration()
        self.universal_cfg = universal_cfg or cfg
        if self.universal_cfg is None:
            self.universal_cfg = RandomGuideConfiguration()
            self.universal_cfg.disjuncts_p = 0.0

    def _cfg(self, universal: bool) -> RandomGuideConfiguration:
        if universal:
            return self.universal_cfg
        else:
            return self.cfg

    def n_conjuncts(self, depth: int, universal: bool) -> int:
        cfg = self._cfg(universal)
        return int(self.rng.integers(cfg.conjuncts_low, cfg.conjuncts_high + 1))

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        cfg = self._cfg(universal)
        if cfg.disjuncts_p < self.rng.random():
            return 0
        return int(self.rng.integers(cfg.disjuncts_low, cfg.disjuncts_high + 1))

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
        cfg = self._cfg(universal)
        n = int(self.rng.integers(cfg.existential_low, cfg.existential_high + 1))
        if n == 0:
            return []
        roles = self.rng.integers(0, cfg.n_roles, n) + 1
        depths = existential_policies[cfg.existential_depth](self.rng, n, depth)
        if cfg.existential_force_depth is not None and all(d < depth - 1 for d in depths):
            if cfg.existential_force_depth == 'first':
                i = 0
            elif cfg.existential_force_depth == 'last':
                i = -1
            elif cfg.existential_force_depth == 'uniform':
                i = self.rng.integers(0, n)
            else:
                raise ValueError(f"Illegal existential_force_depth: `{cfg.existential_force_depth}`")
            depths[i] = depth - 1
        return list(zip(roles, depths))

    def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
        def sample_max(v: list[int]) -> int:
            return max(v)

        def sample_uniform(v: list[int]) -> int:
            return self.rng.choice(v)

        cfg = self._cfg(universal)
        th = int(self.rng.integers(cfg.universal_threshold_low, cfg.universal_threshold_high + 1))
        if cfg.universal_depth == 'max':
            sample = sample_max
        else:
            assert cfg.universal_depth == 'uniform'
            sample = sample_uniform
        return [(r, sample(v)) for r, v in roles.items() if len(v) >= th]
