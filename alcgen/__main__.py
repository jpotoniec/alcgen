import json
import os
from pathlib import Path

import fire

from alcgen.configuration import DatasetConfiguration
from alcgen.create_dataset import create_dataset
from alcgen.generator import generate
from alcgen.guide import Guide


def simple_benchmark():
    class BaselineGuide(Guide):
        def n_conjuncts(self, depth: int, universal: bool) -> int:
            return 2

        def n_disjuncts(self, depth: int, universal: bool) -> int:
            if universal:
                return 0
            else:
                return 2

        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            return [(1, depth - 1), (1, depth - 1)]

        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return [(1, depth - 1)]

    class MyGuide(BaselineGuide):
        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            return [(1, depth - 1)] * 5

        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return []

    ce = generate(5, MyGuide(), True, True)
    assert ce is not None


def main(config_file: os.PathLike, target_dir: os.PathLike | None = None):
    with open(config_file) as f:
        configuration = DatasetConfiguration(**json.load(f))
    if target_dir is None:
        target_dir = Path(config_file).with_suffix('')
    create_dataset(configuration, target_dir)


if __name__ == "__main__":
    fire.Fire(main)
