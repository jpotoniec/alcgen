from alcgen.random_guide import policy_ascending


def test_policy_ascending1():
    assert policy_ascending(None, 5, 3) == [0, 1, 2, 2, 2]


def test_policy_ascending2():
    assert policy_ascending(None, 3, 5) == [2, 3, 4]
