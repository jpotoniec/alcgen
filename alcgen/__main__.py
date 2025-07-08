import fire
import numpy as np

from alcgen.generator import generate
from alcgen.random_guide import RandomGuide


def main():
    for depth in range(1, 10):
        for i in range(100):
            print(depth, i)
            guide = RandomGuide(np.random.default_rng(0xfeed * i + 0xbad * depth))
            generate(depth, guide, True, True)
    # guide = RandomGuide(np.random.default_rng(0xfeed))
    # n = Generator().generate(2, guide)
    # print(n.debug())
    # print("========")
    # leafs = n.leafs()
    # print(*leafs, sep='\n')
    # mapping = closing_mapping(leafs)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(n.debug())
    # print("========")
    # symbols = n.symbols()
    # print(symbols)
    # print("========")
    # mapping = minimizing_mapping(symbols)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(*n.leafs(), sep='\n')
    # print("========")
    # ce = n.to_ce()
    # print(to_pretty(ce))
    # with open("/tmp/a.owl", "wt") as f:
    #     to_manchester(ce, "http://example.com/foo", f)


if __name__ == "__main__":
    fire.Fire(main)
