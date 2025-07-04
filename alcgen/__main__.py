import os
from pathlib import Path

import fire
import numpy as np
from tqdm import trange

from alcgen.generator import Generator
from alcgen.random_guide import RandomGuide
from alcgen.syntax import to_manchester


def main(target_dir: os.PathLike = "dataset", seed1: int = 0xbeef, seed2: int = 0xfeed, seed3: int = 0xc0ffee,
         min_steps: int = 10, max_steps=200, increment: int = 10, n: int = 1000,
         prefix: str = "http://example.com/foo"):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for steps in trange(min_steps, max_steps, increment):
        for i in trange(n, desc=f"Steps {steps}", position=1):
            guide = RandomGuide(np.random.default_rng(seed1 * steps + seed2 * i + seed3), min_steps, max_steps)
            gen = Generator(guide)
            fn = f"{steps}_{i}.owl"
            full_path = target_dir / fn
            if not full_path.exists():
                result = gen.run(steps)
                with open(full_path, "wt") as f:
                    to_manchester(result, prefix, f)


if __name__ == "__main__":
    fire.Fire(main)
