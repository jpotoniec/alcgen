from alcgen.syntax import nnf, NOT, AND, OR, ALL, ANY, BOT, TOP, eq, rename


def test_nnf_straight():
    assert nnf(1) == 1


def test_nnf_neg():
    assert nnf((NOT, 1)) == (NOT, 1)


def test_nnf_double_neg():
    assert nnf((NOT, (NOT, 1))) == 1


def test_nnf_triple_neg():
    assert nnf((NOT, (NOT, (NOT, 1)))) == (NOT, 1)


def test_demorgan1():
    assert nnf((NOT, (AND, 1, 2))) == (OR, (NOT, 1), (NOT, 2))


def test_demorgan2():
    assert nnf((NOT, (OR, 1, 2))) == (AND, (NOT, 1), (NOT, 2))


def test_demorgan3():
    assert nnf((NOT, (ALL, 1, 2))) == (ANY, 1, (NOT, 2))


def test_demorgan4():
    assert nnf((NOT, (ANY, 1, 2))) == (ALL, 1, (NOT, 2))


def test_not_top():
    assert nnf((NOT, TOP)) == BOT


def test_not_bot():
    assert nnf((NOT, BOT)) == TOP


def test_eq_commutative_demorgan():
    assert eq((NOT, (AND, 1, 2)), (OR, (NOT, 2), (NOT, 1)))
    assert not eq((NOT, (AND, 1, 2)), (AND, (NOT, 2), (NOT, 1)))
    assert not eq((NOT, (AND, 1, 2)), (OR, 2, (NOT, 1)))


def test_rename():
    assert rename((AND, 1, 2), {1: 3}) == (AND, 3, 2)
    assert rename((ANY, 1, 1), {1: 2}) == (ANY, 1, 2)
    assert rename(1, {1: 2}) == 2
