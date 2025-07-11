import copy
import os
from pathlib import Path

import numpy as np
from tqdm import trange

from alcgen.configuration import DatasetConfiguration
from alcgen.generator import Generator, do_minimize, do_close
from alcgen.node import Node
from alcgen.random_guide import RandomGuide
from alcgen.syntax import to_manchester


def compute_seed(configuration: DatasetConfiguration, depth: int, instance: int) -> int | None:
    if configuration.seed_depth is None and configuration.seed_instance is None:
        return None
    seed = 0
    if configuration.seed_depth is not None:
        seed += configuration.seed_depth * depth
    if configuration.seed_instance is not None:
        seed += configuration.seed_instance * instance
    return seed


def save(path: Path, configuration: DatasetConfiguration, node: Node):
    ce = node.to_ce()
    with open(path, "wt") as f:
        to_manchester(ce, configuration.prefix, f)


def create_dataset(configuration: DatasetConfiguration, target_dir: os.PathLike | Path):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for depth in trange(configuration.min_depth, configuration.max_depth + 1):
        for instance in trange(configuration.n_instances, position=1):
            seed = compute_seed(configuration, depth, instance)
            guide = RandomGuide(np.random.default_rng(seed), configuration.guide, configuration.universal_guide)
            instance_dir = target_dir / str(depth) / str(instance)
            instance_dir.mkdir(parents=True, exist_ok=True)
            open_fn = instance_dir / "open.owl"
            open_minimized_fn = instance_dir / "open_minimized.owl"
            closed_fn = instance_dir / "closed.owl"
            closed_minimized_fn = instance_dir / "closed_minimized.owl"
            save_open = configuration.save_open and not open_fn.exists()
            save_open_minimized = configuration.save_open_minimized and not open_minimized_fn.exists()
            save_closed = configuration.save_closed and not closed_fn.exists()
            save_closed_minimized = configuration.save_closed_minimized and not closed_minimized_fn.exists()
            if not (save_open or save_open_minimized or save_closed or save_closed_minimized):
                continue
            n = Generator().generate(depth, guide)
            if save_open:
                save(open_fn, configuration, n)
            if save_open_minimized:
                m = copy.deepcopy(n)
                do_minimize(m)
                save(open_minimized_fn, configuration, m)
            if save_closed or save_closed_minimized:
                do_close(n)
                if save_closed:
                    save(closed_fn, configuration, n)
                if save_closed_minimized:
                    do_minimize(n)
                    save(closed_minimized_fn, configuration, n)
