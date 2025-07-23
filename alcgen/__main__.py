import json
import os
from pathlib import Path

import fire

from alcgen.configuration import DatasetConfiguration
from alcgen.create_dataset import create_dataset


def main(config_file: os.PathLike, target_dir: os.PathLike | None = None):
    with open(config_file) as f:
        configuration = DatasetConfiguration(**json.load(f))
    print("Using configuration:")
    print(configuration)
    if target_dir is None:
        target_dir = Path(config_file).with_suffix('')
    create_dataset(configuration, target_dir)


if __name__ == "__main__":
    fire.Fire(main)
