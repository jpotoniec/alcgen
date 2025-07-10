from alcgen.aux import build_index, merge_constraints_into_symbols_for_test


def test_build_index():
    input = [{1, 2, 3}, {2, 3, 4}, {5, 6}]
    index = build_index(input)
    assert index == {1: {0}, 2: {0, 1}, 3: {0, 1}, 4: {1}, 5: {2}, 6: {2}}


def test_merge_constraint_into_symbols_partial():
    original = [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]
    symbols = merge_constraints_into_symbols_for_test(original, [({9, 10}, {17, 18})])
    assert len(original) == len(symbols)
    modified = [i for i in range(len(original)) if original[i] != symbols[i]]
    assert len(modified) == 1
    m = modified[0]
    d = symbols[m] - original[m]
    assert len(d) == 1
    assert d <= {9, 10, 17, 18}


def test_merge_constraint_into_symbols_full():
    original = [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]
    symbols = merge_constraints_into_symbols_for_test(original, [({5, 6}, {25, 26})])
    assert original == symbols


def test_merge_constraint_into_symbols_missing():
    original = [{1, 2}, {3, 19, 4, 20}, {5, 6, 9, 10, 25, 26}, {7, 8, 9, 10, 25, 26}, {11, 19, 12, 20},
                {13, 14, 17, 18, 25, 26}, {15, 16, 17, 18, 25, 26}, {25, 26, 21, 22}, {24, 25, 26, 23}]
    symbols = merge_constraints_into_symbols_for_test(original, [({30, 31}, {32, 33})])
    assert len(original) == len(symbols)
    assert original[1:] == symbols[1:]
    d = symbols[0] - original[0]
    assert len(d) == 2
    assert len(d & {30, 31}) == 1
    assert len(d & {32, 33}) == 1
