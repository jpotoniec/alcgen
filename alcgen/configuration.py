from typing import Literal

import pydantic


class RandomGuideConfiguration(pydantic.BaseModel):
    conjuncts_low: int = 1
    conjuncts_high: int = 3

    disjuncts_p: float = 1.0
    disjuncts_low: int = 2
    disjuncts_high: int = 2

    n_roles: int = 1
    existential_low: int = 0
    existential_high: int = 3
    existential_depth: Literal['max', 'uniform', 'ascending', 'descending'] = 'max'
    existential_force_depth: None | Literal['uniform', 'first', 'last'] = 'uniform'

    universal_threshold_low: int | None = 2
    universal_threshold_high: int | None = 2
    universal_depth: Literal['max', 'uniform'] = 'max'


class DatasetConfiguration(pydantic.BaseModel):
    min_depth: int = 0
    max_depth: int = 5
    n_instances: int = 10

    save_open: bool = True
    save_open_minimized: bool = True
    save_closed: bool = True
    save_closed_minimized: bool = True

    seed_depth: int | None = 0xfeed
    seed_instance: int | None = 0xc00ffee
    seed_const: int | None = None

    prefix: str = "http://example.com/foo"

    guide: RandomGuideConfiguration | None = None
    universal_guide: RandomGuideConfiguration | None = None
