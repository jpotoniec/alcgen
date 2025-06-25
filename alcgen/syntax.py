from typing import Mapping

TOP, BOT = -1, -2
SUB, EQV, DIS, NOT, AND, OR, ALL, ANY = range(8)
FORALL = ALL
EXISTS = ANY

OP_PRECEDENCE = {NOT: 50, ANY: 40, ALL: 40, AND: 30, OR: 30, SUB: 10, EQV: 10, DIS: 10}
OP_PRETTY = {NOT: '¬', AND: ' ⊓ ', OR: ' ⊔ ', SUB: ' ⊑ ', EQV: ' = ', DIS: ' != ', ANY: '∃', ALL: '∀'}
OP_BINARY = {AND, OR, SUB, EQV, DIS}
OP_QUANTIFIER = {ANY, ALL}
OP_UNARY = {NOT}

CE = int | tuple[int, 'CE'] | tuple[int, 'CE', 'CE'] | tuple[int, int, 'CE']
Axiom = tuple[int, CE, CE]


def nnf(t: CE) -> CE:
    if isinstance(t, tuple) and t[0] == NOT:
        if isinstance(t[1], tuple):
            if t[1][0] == NOT:
                # double negation
                return nnf(t[1][1])
            elif t[1][0] == AND:
                return OR, nnf((NOT, t[1][1])), nnf((NOT, t[1][2]))
            elif t[1][0] == OR:
                return AND, nnf((NOT, t[1][1])), nnf((NOT, t[1][2]))
            elif t[1][0] == ALL:
                return ANY, t[1][1], nnf((NOT, t[1][2]))
            elif t[1][0] == ANY:
                return ALL, t[1][1], nnf((NOT, t[1][2]))
        elif t[1] == BOT:
            return TOP
        elif t[1] == TOP:
            return BOT
    return t


def eq(a: CE, b: CE) -> bool:
    def real_eq(a: CE, b: CE) -> bool:
        if isinstance(a, tuple) and isinstance(b, tuple):
            if a[0] != b[0] or len(a) != len(b):
                return False
            if a[0] == AND or a[0] == OR:
                return (real_eq(a[1], b[1]) and real_eq(a[2], b[2])) or (real_eq(a[1], b[2]) and real_eq(a[2], b[1]))
            return all(real_eq(c, d) for c, d in zip(a[1:], b[1:]))
        else:
            return a == b

    return real_eq(nnf(a), nnf(b))


def rename(ce: CE, mapping: Mapping[int, int]) -> CE:
    if isinstance(ce, tuple):
        if ce[0] == ANY or ce[0] == ALL:
            return ce[0], ce[1], rename(ce[2], mapping)
        else:
            return (ce[0],) + tuple(rename(child, mapping) for child in ce[1:])
    else:
        return mapping.get(ce, ce)


def to_pretty(expr, *, concept_names=None, role_names=None):
    """
    Returns a pretty representation of a given expression.
    """

    def rec(x, prec):
        if isinstance(x, tuple):
            head = x[0]
            head_prec = OP_PRECEDENCE[head]
            if head in OP_UNARY:
                result = OP_PRETTY[head] + rec(x[1], head_prec)
            elif head in OP_BINARY:
                result = OP_PRETTY[head].join(rec(xx, head_prec) for xx in x[1:])
            elif head in OP_QUANTIFIER:
                role = 'R' + str(x[1]) if role_names is None else role_names[x[1]]
                result = OP_PRETTY[head] + role + '.' + rec(x[2], head_prec)
            else:
                assert False, f'unknown operator {head}'
            if prec >= head_prec:
                result = '(' + result + ')'
            return result
        elif x == TOP:
            return '⊤'
        elif x == BOT:
            return '⊥'
        elif isinstance(x, int):
            return 'C' + str(x) if concept_names is None else concept_names[x]
        else:
            assert False, f'bad expression {x}'

    return rec(expr, 0)


def to_manchester(expr: CE, prefix: str, f):
    classes = set()
    roles = set()

    def r(i: int):
        n = f"r{i}"
        roles.add(n)
        return n

    def c(i: int):
        n = f"c{i}"
        classes.add(n)
        return n

    def serialize(ce: CE) -> str:
        if isinstance(ce, tuple):
            if ce[0] == NOT:
                return f"(not {serialize(ce[1])})"
            elif ce[0] == AND:
                return f"({serialize(ce[1])} and {serialize(ce[2])})"
            elif ce[0] == OR:
                return f"({serialize(ce[1])} or {serialize(ce[2])})"
            elif ce[0] == ANY:
                return f"({r(ce[1])} some {serialize(ce[2])})"
            elif ce[0] == ALL:
                return f"({r(ce[1])} only {serialize(ce[2])})"
        else:
            return c(ce)

    print(f"Prefix: : <{prefix}#>", file=f)
    print(f"Ontology: <{prefix}>", file=f)
    print(f"Class: D", file=f)
    print(f"EquivalentTo:", serialize(expr), file=f)
    for c in classes:
        print("Class:", c, file=f)
    for r in roles:
        print("ObjectProperty:", r, file=f)
