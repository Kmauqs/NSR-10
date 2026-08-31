# -*- coding: utf-8 -*-
"""Labeled NSR-10 equations as MathML (HTML entities only)."""

SUM = "&#x2211;"
MINUS = "&#x2212;"
PHI = "&#x3C6;"
OMEGA = "&#x3A9;"
ALPHA = "&#x3B1;"
PI = "&#x3C0;"
NBSP = "&#xA0;"
OVER = "<mo>&#xAF;</mo>"


def _n(eq, inner):
    return (
        f'<div class="eq-block" id="eq-{eq}">'
        f'<math display="block" xmlns="http://www.w3.org/1998/Math/MathML"><mrow>{inner}</mrow></math>'
        f'<p class="eq-num">({eq})</p></div>'
    )


def msub(base, s):
    return f"<msub><mi>{base}</mi><mi>{s}</mi></msub>"


def msum(inner, lo, hi):
    return (
        f"<munderover><mo>{SUM}</mo><mrow>{lo}</mrow><mi>{hi}</mi></munderover>{inner}"
    )


def frac(a, b):
    return f"<mfrac><mrow>{a}</mrow><mrow>{b}</mrow></mfrac>"


EQ = {}

EQ["A.2.4-1"] = _n(
    "A.2.4-1",
    f"{msub('v', 's')}<mo>=</mo>"
    + frac(
        msum(msub("d", "i"), "<mi>i</mi><mo>=</mo><mn>1</mn>", "n"),
        msum(frac(msub("d", "i"), msub("v", "si")), "<mi>i</mi><mo>=</mo><mn>1</mn>", "n"),
    ),
)
EQ["A.2.4-2"] = _n(
    "A.2.4-2",
    f"<mover><mi>N</mi>{OVER}</mover><mo>=</mo>"
    + frac(
        msum(msub("d", "i"), "<mi>i</mi><mo>=</mo><mn>1</mn>", "n"),
        msum(frac(msub("d", "i"), msub("N", "i")), "<mi>i</mi><mo>=</mo><mn>1</mn>", "n"),
    ),
)
EQ["A.2.4-3"] = _n(
    "A.2.4-3",
    f"{msub('N', 'ch')}<mo>=</mo>"
    + frac(
        msub("d", "s"),
        msum(frac(msub("d", "i"), msub("N", "i")), "<mi>i</mi><mo>=</mo><mn>1</mn>", "m"),
    ),
)
EQ["A.2.4-4"] = _n(
    "A.2.4-4",
    f"{msub('s', 'u')}<mo>=</mo>"
    + frac(
        msub("d", "c"),
        msum(frac(msub("d", "i"), msub("s", "ui")), "<mi>i</mi><mo>=</mo><mn>1</mn>", "k"),
    ),
)
EQ["A.2.6-1"] = _n(
    "A.2.6-1",
    f"{msub('S', 'a')}<mo>=</mo>{frac('<mn>1.2</mn>' + msub('A', 'v') + msub('F', 'v') + '<mi>I</mi>', '<mi>T</mi>')}",
)
EQ["A.2.6-2"] = _n(
    "A.2.6-2",
    f"{msub('T', 'C')}<mo>=</mo><mn>0.48</mn>"
    + frac(msub("A", "v") + msub("F", "v"), msub("A", "a") + msub("F", "a")),
)
EQ["A.2.6-3"] = _n(
    "A.2.6-3",
    f"{msub('S', 'a')}<mo>=</mo><mn>2.5</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>I</mi>",
)
EQ["A.2.6-4"] = _n("A.2.6-4", f"{msub('T', 'L')}<mo>=</mo><mn>2.4</mn>{msub('F', 'v')}")
EQ["A.2.6-5"] = _n(
    "A.2.6-5",
    f"{msub('S', 'a')}<mo>=</mo>"
    + frac(
        f"<mn>1.2</mn>{msub('A', 'v')}{msub('F', 'v')}{msub('T', 'L')}<mi>I</mi>",
        "<msup><mi>T</mi><mn>2</mn></msup>",
    ),
)
EQ["A.2.6-6"] = _n(
    "A.2.6-6",
    f"{msub('T', '0')}<mo>=</mo><mn>0.1</mn>"
    + frac(msub("A", "v") + msub("F", "v"), msub("A", "a") + msub("F", "a")),
)
EQ["A.2.6-7"] = _n(
    "A.2.6-7",
    f"{msub('S', 'a')}<mo>=</mo><mn>2.5</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>I</mi>"
    f"<mrow><mo>(</mo><mn>0.4</mn><mo>+</mo><mn>0.6</mn>"
    f"{frac('<mi>T</mi>', msub('T', '0'))}<mo>)</mo></mrow>",
)
EQ["A.2.6-8"] = _n(
    "A.2.6-8",
    f"{msub('S', 'v')}<mo>=</mo><mn>1.87</mn>{msub('A', 'v')}{msub('F', 'v')}<mi>I</mi>"
    f"<mtext>{NBSP}(m/s)</mtext>",
)
EQ["A.2.6-9"] = _n(
    "A.2.6-9",
    f"{msub('S', 'v')}<mo>=</mo><mn>3.9</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>T</mi><mi>I</mi>"
    f"<mtext>{NBSP}(m/s)</mtext>",
)
EQ["A.2.6-10"] = _n(
    "A.2.6-10",
    f"{msub('S', 'v')}<mo>=</mo>"
    + frac(
        f"<mn>1.87</mn>{msub('A', 'v')}{msub('F', 'v')}<mi>I</mi>{msub('T', 'L')}",
        "<mi>T</mi>",
    )
    + f"<mtext>{NBSP}(m/s)</mtext>",
)
EQ["A.2.6-11"] = _n(
    "A.2.6-11",
    f"{msub('S', 'v')}<mo>=</mo><mn>3.9</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>I</mi><mi>T</mi>"
    f"<mrow><mo>(</mo><mn>0.4</mn><mo>+</mo><mn>0.6</mn>"
    f"{frac('<mi>T</mi>', msub('T', '0'))}<mo>)</mo></mrow>"
    f"<mtext>{NBSP}(m/s)</mtext>",
)
EQ["A.2.6-12"] = _n(
    "A.2.6-12",
    f"{msub('S', 'd')}<mo>=</mo><mn>0.3</mn>{msub('A', 'v')}{msub('F', 'v')}<mi>I</mi><mi>T</mi>"
    f"<mtext>{NBSP}(m)</mtext>",
)
EQ["A.2.6-13"] = _n(
    "A.2.6-13",
    f"{msub('S', 'd')}<mo>=</mo><mn>0.62</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>I</mi>"
    f"<msup><mi>T</mi><mn>2</mn></msup><mtext>{NBSP}(m)</mtext>",
)
EQ["A.2.6-14"] = _n(
    "A.2.6-14",
    f"{msub('S', 'd')}<mo>=</mo><mn>0.3</mn>{msub('A', 'v')}{msub('F', 'v')}<mi>I</mi>{msub('T', 'L')}"
    f"<mtext>{NBSP}(m)</mtext>",
)
EQ["A.2.6-15"] = _n(
    "A.2.6-15",
    f"{msub('S', 'd')}<mo>=</mo><mn>0.62</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>I</mi>"
    f"<msup><mi>T</mi><mn>2</mn></msup>"
    f"<mrow><mo>(</mo><mn>0.4</mn><mo>+</mo><mn>0.6</mn>"
    f"{frac('<mi>T</mi>', msub('T', '0'))}<mo>)</mo></mrow>"
    f"<mtext>{NBSP}(m)</mtext>",
)
EQ["A.2.9-1"] = _n(
    "A.2.9-1",
    f"{msub('R', 'C')}<mo>=</mo><mo>(</mo><mi>R</mi><mo>{MINUS}</mo><mn>1</mn><mo>)</mo>"
    f"{frac('<mi>T</mi>', msub('T', 'C'))}<mo>+</mo><mn>1</mn>",
)
EQ["A.3.3-1"] = _n(
    "A.3.3-1",
    f"<mi>R</mi><mo>=</mo>{msub(PHI, 'a')}{msub(PHI, 'p')}{msub(PHI, 'r')}{msub('R', '0')}",
)
EQ["A.3.3-2"] = _n(
    "A.3.3-2",
    f"<mi>E</mi><mo>=</mo>{msub(OMEGA, '0')}{msub('F', 's')}"
    f"<mo>&#x2213;</mo><mn>0.5</mn>{msub('A', 'a')}{msub('F', 'a')}<mi>D</mi>",
)
EQ["A.4.2-2"] = _n(
    "A.4.2-2",
    f"{msub('C', 'u')}<mo>=</mo><mn>1.75</mn><mo>{MINUS}</mo><mn>1.2</mn>{msub('A', 'v')}{msub('F', 'v')}",
)
EQ["A.4.2-3"] = _n(
    "A.4.2-3",
    f"{msub('T', 'a')}<mo>=</mo>{msub('C', 't')}<msup><mi>h</mi><mi>{ALPHA}</mi></msup>",
)
EQ["A.4.2-5"] = _n("A.4.2-5", f"{msub('T', 'a')}<mo>=</mo><mn>0.1</mn><mi>N</mi>")
EQ["A.4.3-1"] = _n(
    "A.4.3-1",
    f"{msub('V', 's')}<mo>=</mo>{msub('S', 'a')}<mi>g</mi><mi>M</mi>",
)
EQ["A.4.3-2"] = _n(
    "A.4.3-2",
    f"{msub('F', 'x')}<mo>=</mo>{msub('C', 'vx')}{msub('V', 's')}",
)
EQ["A.4.3-3"] = _n(
    "A.4.3-3",
    f"{msub('C', 'vx')}<mo>=</mo>"
    + frac(
        f"{msub('w', 'x')}{msub('h', 'x')}<msup><mi></mi><mi>k</mi></msup>",
        msum(
            f"{msub('w', 'i')}{msub('h', 'i')}<msup><mi></mi><mi>k</mi></msup>",
            "<mi>i</mi><mo>=</mo><mn>1</mn>",
            "n",
        ),
    ),
)
EQ["A.5.4-3"] = _n(
    "A.5.4-3",
    f"{msub('V', 'mj')}<mo>=</mo>{msub('S', 'am')}<mi>g</mi>{msub('M', 'mj')}",
)
EQ["A.8.2-2"] = _n(
    "A.8.2-2",
    f"{msub('F', 'p')}<mo>=</mo>{msub('a', 'x')}<mi>g</mi>{msub('M', 'p')}",
)
EQ["A.9.4-1"] = _n(
    "A.9.4-1",
    f"{msub('F', 'p')}<mo>=</mo>{msub('a', 'x')}{msub('a', 'p')}<mi>g</mi>{msub('M', 'p')}",
)
EQ["A.12.3-1"] = _n(
    "A.12.3-1",
    f"{msub('S', 'ad')}<mo>=</mo><mn>1.5</mn>{msub('A', 'd')}<mi>S</mi>",
)
EQ["A.12.4-1"] = _n(
    "A.12.4-1",
    f"{msub('V', 'sd')}<mo>=</mo>{msub('S', 'ad')}<mi>g</mi><mi>M</mi>",
)
EQ["B.6.4-1"] = _n(
    "B.6.4-1",
    f"{msub('p', 's')}<mo>=</mo>{msub('K', 'zt')}<mi>I</mi>{msub('p', 's10')}",
)
EQ["B.6.4-2"] = _n(
    "B.6.4-2",
    f"{msub('p', 'net')}<mo>=</mo>{msub('K', 'zt')}<mi>I</mi>{msub('p', 'net10')}",
)
EQ["B.6.5-1"] = _n(
    "B.6.5-1",
    f"{msub('K', 'zt')}<mo>=</mo><msup><mrow><mo>(</mo><mn>1</mn><mo>+</mo>"
    f"{msub('K', '1')}{msub('K', '2')}{msub('K', '3')}<mo>)</mo></mrow><mn>2</mn></msup>",
)

# Load combinations as MathML text rows (B.2.3 / B.2.4)
for i, expr in enumerate(
    [
        "D + F",
        "D + H + F + L + T",
        "D + H + F + (L_r o G o L_e)",
        "D + H + F + 0.75(L + T) + 0.75(L_r o G o L_e)",
        "D + H + F + W",
        "D + H + F + 0.7E",
        "D + H + F + 0.75W + 0.75L + 0.75(L_r o G o L_e)",
        "D + H + F + 0.75(0.7E) + 0.75L + 0.75(L_r o G o L_e)",
        "0.6D + W + H",
        "0.6D + 0.7E + H",
    ],
    1,
):
    EQ[f"B.2.3-{i}"] = _n(f"B.2.3-{i}", f"<mtext>{expr}</mtext>")

for i, expr in enumerate(
    [
        "1.4(D + F)",
        "1.2(D + F + T) + 1.6(L + H) + 0.5(L_r o G o L_e)",
        "1.2D + 1.6(L_r o G o L_e) + (L o 0.8W)",
        "1.2D + 1.6W + 1.0L + 0.5(L_r o G o L_e)",
        "1.2D + 1.0E + 1.0L",
        "0.9D + 1.6W + 1.6H",
        "0.9D + 1.0E + 1.6H",
    ],
    1,
):
    EQ[f"B.2.4-{i}"] = _n(f"B.2.4-{i}", f"<mtext>{expr}</mtext>")


def mathml_for(eq_id):
    return EQ.get(eq_id)


def fallback_eq(eq_id, raw=None):
    """Never dump OCR. Show only the official number and a PDF hint."""
    return (
        f'<div class="eq-block" id="eq-{eq_id}">'
        f'<p class="eq-num">Ecuacion ({eq_id})</p>'
        f'<p class="muted">Formula reconstruida no catalogada; consultela en el PDF oficial.</p>'
        f"</div>"
    )
