# -*- coding: utf-8 -*-
"""MathML catalog for Decreto 1711, Apendice F.4-A (HTML entities only)."""

SUM = "&#x2211;"
LAMBDA = "&#x3BB;"
ALPHA = "&#x3B1;"
BETA = "&#x3B2;"
RHO = "&#x3C1;"
DELTA = "&#x3B4;"
OMEGA = "&#x3C9;"
LE = "&#x2264;"
GE = "&#x2265;"
LT = "&#x3C;"
GT = "&#x3E;"
MINUS = "&#x2212;"


def _n(eq, inner):
    return (
        f'<div class="eq-block" id="eq-{eq}">'
        f'<math display="block" xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<mrow>{inner}</mrow></math><p class=\"eq-num\">({eq})</p></div>"
    )


def mi(value):
    return f"<mi>{value}</mi>"


def mn(value):
    return f"<mn>{value}</mn>"


def mo(value):
    return f"<mo>{value}</mo>"


def mtext(value):
    return f"<mtext>{value}</mtext>"


def sub(base, index):
    return f"<msub><mi>{base}</mi><mi>{index}</mi></msub>"


def sup(base, exponent):
    return f"<msup><mrow>{base}</mrow><mrow>{exponent}</mrow></msup>"


def frac(numerator, denominator):
    return f"<mfrac><mrow>{numerator}</mrow><mrow>{denominator}</mrow></mfrac>"


def parens(value):
    return f"<mrow><mo>(</mo>{value}<mo>)</mo></mrow>"


def root(value):
    return f"<msqrt><mrow>{value}</mrow></msqrt>"


def sigma(value, index="i", lower="1", upper="n"):
    return (
        f"<munderover><mo>{SUM}</mo>"
        f"<mrow><mi>{index}</mi><mo>=</mo><mn>{lower}</mn></mrow>"
        f"<mi>{upper}</mi></munderover>{value}"
    )


def condition(lhs, relation, rhs):
    return f"{lhs}<mo>{relation}</mo>{rhs}"


def cases(rows):
    body = "".join(
        f"<mtr><mtd>{expression}</mtd><mtd><mtext>Para&#xA0;</mtext>{test}</mtd></mtr>"
        for expression, test in rows
    )
    return f"<mrow><mo>{{</mo><mtable>{body}</mtable></mrow>"


EQ_F4A = {}

# F.4.A.1
eq = "F.4.A.1.3.2.3-1"
EQ_F4A[eq] = _n(
    eq,
    sub("R", "re")
    + mo("=")
    + cases(
        [
            (frac(sub("M", "no"), sub("M", "y")), condition(mi(LAMBDA), LT, mn("0.673"))),
            (mn("1"), condition(mi(LAMBDA), GE, mn("0.673"))),
        ]
    ),
)

eq = "F.4.A.1.3.2.3-2"
EQ_F4A[eq] = _n(eq, sub("M", "y") + mo("=") + sub("S", "f") + sub("F", "y"))

# Wood structural-panel shear walls
eq = "F.4.A.5.1.3.1.1-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("v", "n")
    + mi("w")
    + mo(",")
    + mtext("&#xA0;")
    + condition(frac(mi("h"), mi("w")), LE, mn("2")),
)

eq = "F.4.A.5.1.3.1.1-2"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("v", "n")
    + mi("w")
    + parens(frac(mn("2") + mi("w"), mi("h")))
    + mo(",")
    + mtext("&#xA0;")
    + condition(mn("2"), LT, frac(mi("h"), mi("w")))
    + mo(LE)
    + mn("4"),
)

eq = "F.4.A.5.1.3.1.2-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("C", "a")
    + sub("v", "n")
    + sigma(sub("L", "i")),
)


def deflection_equation(beta_term, rho_term):
    return (
        mi(DELTA)
        + mo("=")
        + frac(mn("2") + mi("v") + sup(mi("h"), mn("3")), mn("3") + mi("E") + sub("A", "c") + mi("b"))
        + mo("+")
        + sub(OMEGA, "1")
        + sub(OMEGA, "2")
        + frac(mi("v") + mi("h"), rho_term + mi("G") + sub("t", "revestimiento"))
        + mo("+")
        + sub(OMEGA, "1")
        + sub(OMEGA, "2")
        + sub(OMEGA, "3")
        + sub(OMEGA, "4")
        + sup(parens(frac(mi("v"), beta_term)), frac(mn("5"), mn("4")))
        + frac(sup(mi("h"), mn("2")), mi("b"))
        + mo("+")
        + frac(mi("h"), mi("b"))
        + sub(DELTA, "v")
    )


eq = "F.4.A.5.1.4.1.4-1"
EQ_F4A[eq] = _n(eq, deflection_equation(mi(BETA), mi(RHO)))

eq = "F.4.A.5.1.4.1.4-2"
EQ_F4A[eq] = _n(eq, mi("v") + mo("=") + frac(mi("V"), mi("b")))

eq = "F.4.A.5.1.4.1.4-3"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "1") + mo("=") + frac(mi("s"), mn("152.4")))

eq = "F.4.A.5.1.4.1.4-4"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "2") + mo("=") + mn("0.838") + sub("t", "paral"))

eq = "F.4.A.5.1.4.1.4-5"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "3") + mo("=") + sup(parens(frac(mi("h"), mi("b"))), mn("2")))

eq = "F.4.A.5.1.4.2.2-1"
EQ_F4A[eq] = _n(eq, mi("v") + mo("=") + frac(mi("V"), sub("C", "a") + sigma(sub("L", "i"))))

eq = "F.4.A.5.1.4.2.2-2"
EQ_F4A[eq] = _n(
    eq,
    mi("C") + mo("=") + frac(mi("V") + mi("h"), sub("C", "a") + sigma(sub("L", "i"))),
)

# Steel-sheet shear walls and effective-strip method
eq = "F.4.A.5.2.3.1.1-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("v", "n")
    + mi("w")
    + mo(",")
    + mtext("&#xA0;")
    + condition(frac(mi("h"), mi("w")), LE, mn("2")),
)

eq = "F.4.A.5.2.3.1.1-2"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("v", "n")
    + mi("w")
    + parens(frac(mn("2") + mi("w"), mi("h")))
    + mo(",")
    + mtext("&#xA0;")
    + condition(mn("2"), LT, frac(mi("h"), mi("w")))
    + mo(LE)
    + mn("4"),
)

eq = "F.4.A.5.2.3.1.1.1-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + mtext("min")
    + parens(
        mn("1.33")
        + sub("P", "n")
        + mtext("cos")
        + mi(ALPHA)
        + mo(",")
        + mn("1.33")
        + sub("w", "e")
        + mi("t")
        + sub("F", "y")
        + mtext("cos")
        + mi(ALPHA)
    ),
)

eq = "F.4.A.5.2.3.1.1.1-2"
EQ_F4A[eq] = _n(
    eq,
    mi(ALPHA) + mo("=") + mtext("arctan") + parens(frac(mi("h"), mi("w"))),
)

eq = "F.4.A.5.2.3.1.1.1-3"
EQ_F4A[eq] = _n(
    eq,
    sub("w", "e")
    + mo("=")
    + sub("w", "max")
    + mo(",")
    + mtext("&#xA0;")
    + condition(mi(LAMBDA), LE, mn("0.0819")),
)

eq = "F.4.A.5.2.3.1.1.1-4"
EQ_F4A[eq] = _n(
    eq,
    sub("w", "e")
    + mo("=")
    + mi(RHO)
    + sub("w", "max")
    + mo(",")
    + mtext("&#xA0;")
    + condition(mi(LAMBDA), GT, mn("0.0819")),
)

eq = "F.4.A.5.2.3.1.1.1-5"
EQ_F4A[eq] = _n(
    eq,
    sub("w", "max") + mo("=") + mi("w") + mtext("sin") + mi(ALPHA),
)

eq = "F.4.A.5.2.3.1.1.1-6"
EQ_F4A[eq] = _n(
    eq,
    mi(RHO)
    + mo("=")
    + frac(
        mn("1")
        + mo(MINUS)
        + mn("0.55")
        + sup(parens(mi(LAMBDA) + mo(MINUS) + mn("0.08")), mo(MINUS) + mn("0.12")),
        sup(mi(LAMBDA), mn("0.12")),
    ),
)

eq = "F.4.A.5.2.3.1.1.1-7"
EQ_F4A[eq] = _n(
    eq,
    mi(LAMBDA)
    + mo("=")
    + mn("1.736")
    + frac(
        root(frac(mi("a"), sub(ALPHA, "1") + sub(ALPHA, "2"))),
        sub(BETA, "1") + sub(BETA, "2") + sub(BETA, "3"),
    ),
)

for number, lhs, numerator, denominator in [
    ("9", sub(ALPHA, "1"), sub("F", "ush"), mn("310.3")),
    ("11", sub(ALPHA, "2"), sub("F", "uf"), mn("310.3")),
    ("13", sub(BETA, "1"), sub("t", "sh"), mn("0.457")),
    ("15", sub(BETA, "2"), sub("t", "f"), mn("0.457")),
    ("17", sub(BETA, "3"), mi("s"), mn("152.4")),
]:
    eq = f"F.4.A.5.2.3.1.1.1-{number}"
    EQ_F4A[eq] = _n(eq, lhs + mo("=") + frac(numerator, denominator))

eq = "F.4.A.5.2.3.1.1.1-18"
EQ_F4A[eq] = _n(eq, mi("a") + mo("=") + frac(mi("h"), mi("w")))

eq = "F.4.A.5.2.3.1.2-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("C", "a")
    + sub("v", "n")
    + sigma(sub("L", "i")),
)

# Steel-sheet wall deflection
eq = "F.4.A.5.2.4.1.4-1"
EQ_F4A[eq] = _n(eq, deflection_equation(mi(BETA), mi(RHO)))

eq = "F.4.A.5.2.4.1.4-2"
EQ_F4A[eq] = _n(eq, mi("v") + mo("=") + frac(mi("V"), mi("b")))

eq = "F.4.A.5.2.4.1.4-3"
EQ_F4A[eq] = _n(
    eq,
    mi(BETA) + mo("=") + frac(mn("1.01") + sub("t", "revestimiento"), mn("0.457")),
)

eq = "F.4.A.5.2.4.1.4-4"
EQ_F4A[eq] = _n(
    eq,
    mi(RHO) + mo("=") + frac(mn("0.075") + sub("t", "revestimiento"), mn("0.457")),
)

eq = "F.4.A.5.2.4.1.4-5"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "1") + mo("=") + frac(mi("s"), mn("152")))

eq = "F.4.A.5.2.4.1.4-6"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "2") + mo("=") + mn("0.838") + sub("t", "paral"))

eq = "F.4.A.5.2.4.1.4-7"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "3") + mo("=") + sup(parens(frac(mi("h"), mi("b"))), mn("2")))

eq = "F.4.A.5.2.4.1.4-8"
EQ_F4A[eq] = _n(eq, sub(OMEGA, "4") + mo("=") + frac(mn("227.5"), sub("F", "y")))

eq = "F.4.A.5.2.4.2.2-1"
EQ_F4A[eq] = _n(eq, mi("v") + mo("=") + frac(mi("V"), sub("C", "a") + sigma(sub("L", "i"))))

eq = "F.4.A.5.2.4.2.2-2"
EQ_F4A[eq] = _n(
    eq,
    mi("C") + mo("=") + frac(mi("V") + mi("h"), sub("C", "a") + sigma(sub("L", "i"))),
)

# Strap-braced walls
eq = "F.4.A.5.3.3.1-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + frac(sub("T", "n") + mi("w"), root(sup(mi("h"), mn("2")) + mo("+") + sup(mi("w"), mn("2")))),
)

eq = "F.4.A.5.3.3.1-2"
EQ_F4A[eq] = _n(eq, sub("T", "n") + mo("=") + sub("A", "g") + sub("F", "y"))

eq = "F.4.A.5.3.4.1-1"
EQ_F4A[eq] = _n(
    eq,
    frac(sub("R", "t") + sub("F", "u"), sub("R", "y") + sub("F", "y"))
    + mo(GE)
    + mn("1.2"),
)

eq = "F.4.A.5.3.4.1-2"
EQ_F4A[eq] = _n(
    eq,
    sub("R", "t")
    + sub("A", "n")
    + sub("F", "u")
    + mo(GT)
    + sub("R", "y")
    + sub("A", "g")
    + sub("F", "y"),
)

# Special bolted moment frames
eq = "F.4.A.5.4.3.1.2-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "bp")
    + mo("=")
    + frac(sub("t", "p") + sub("V", "e"), mi("N") + parens(sub("t", "w") + mo("+") + sub("t", "p"))),
)

eq = "F.4.A.5.4.3.3-1"
EQ_F4A[eq] = _n(eq, sub("V", "e") + mo("=") + sub("V", "S") + mo("+") + sub("V", "B"))

eq = "F.4.A.5.4.3.3-2"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "S")
    + mo("=")
    + frac(sub("C", "S") + mi("k") + mi("N") + mi("T"), mi("h")),
)

eq = "F.4.A.5.4.3.3-3"
EQ_F4A[eq] = _n(
    eq,
    frac(sub("V", "B"), sub("V", "B,max"))
    + mo("=")
    + mn("1")
    + mo(MINUS)
    + parens(mn("1") + mo(MINUS) + frac(sub(DELTA, "B"), sub(DELTA, "B,max"))),
)

eq = "F.4.A.5.4.3.3-4"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "B,max")
    + mo("=")
    + frac(sub("C", "B") + mi("N") + sub("R", "0"), mi("h")),
)

eq = "F.4.A.5.4.3.3-5"
EQ_F4A[eq] = _n(
    eq,
    mi(DELTA)
    + mo(MINUS)
    + sub(DELTA, "S")
    + mo(MINUS)
    + frac(
        sigma(frac(sub("M", "e,i"), sub("h", "i"))),
        mi("K"),
    )
    + mo(GE)
    + mn("0"),
)

eq = "F.4.A.5.4.3.3-6"
EQ_F4A[eq] = _n(
    eq,
    sub(DELTA, "B,max")
    + mo("=")
    + frac(sub("C", "DB"), sub("C", "B,0"))
    + mi("h"),
)

eq = "F.4.A.5.4.3.3-7"
EQ_F4A[eq] = _n(
    eq,
    sub(DELTA, "S")
    + mo("=")
    + frac(sub("C", "DS") + sub("h", "OS"), mi("h")),
)

# Gypsum/fiber-board walls and wood structural-panel diaphragms
eq = "F.4.A.5.5.3.1.1-1"
EQ_F4A[eq] = _n(
    eq,
    sub("V", "n")
    + mo("=")
    + sub("v", "n")
    + mi("w")
    + mo(",")
    + mtext("&#xA0;")
    + condition(frac(mi("h"), mi("w")), LE, mn("2")),
)

eq = "F.4.A.6.2.4.1-1"
EQ_F4A[eq] = _n(eq, sub("V", "n") + mo("=") + sub("v", "n") + mi("L"))
