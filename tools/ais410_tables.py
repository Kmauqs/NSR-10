# -*- coding: utf-8 -*-
"""Curated tables from the OCR-only AIS 410-23 decree annex."""
from __future__ import annotations

import html


PDF = "Modificaciones/2023-08-25-DECRETO-1401-DEL-25-DE-AGOSTO-DE-2023.pdf"


def _cell(
    text: object = "",
    *,
    tag: str = "td",
    rowspan: int = 1,
    colspan: int = 1,
    cls: str = "",
    safe_html: str | None = None,
) -> str:
    attrs = ""
    if rowspan > 1:
        attrs += f' rowspan="{rowspan}"'
    if colspan > 1:
        attrs += f' colspan="{colspan}"'
    if cls:
        attrs += f' class="{html.escape(cls, quote=True)}"'
    content = safe_html if safe_html is not None else html.escape(str(text))
    return f"<{tag}{attrs}>{content}</{tag}>"


def _tr(*cells: str) -> str:
    return "<tr>" + "".join(cells) + "</tr>"


def _text_row(values: tuple[object, ...] | list[object], *, header: bool = False) -> str:
    tag = "th" if header else "td"
    return _tr(*(_cell(v, tag=tag) for v in values))


def _table(tid: str, title: str, page: int, head: list[str], body: list[str]) -> dict:
    caption = (
        f"Tabla {html.escape(tid)} — {html.escape(title)}"
        f' <a href="{html.escape(PDF, quote=True)}#page={page}" target="_blank" '
        f'rel="noopener">PDF pág. {page}</a>'
    )
    table_html = (
        f'<div class="nsr-table-wrap"><p class="table-cap">{caption}</p>'
        f'<table class="nsr-table"><thead>{"".join(head)}</thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )
    return {
        "html": table_html,
        "page": page,
        "rows": len(body),
        "score": 999,
        "pdf": PDF,
    }


def _math_prime(base: str, sub: str) -> str:
    return (
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<msubsup><mi>{html.escape(base)}</mi><mi>{html.escape(sub)}</mi>"
        "<mo>′</mo></msubsup></math>"
    )


def curated_ais410_tables() -> dict:
    """Return hand-curated HTML tables from Decreto 1401 de 2023."""
    out: dict[str, dict] = {}

    head = [
        _tr(
            _cell("Sistema de muros de carga", tag="th", rowspan=3),
            _cell("R", tag="th", rowspan=3),
            _cell("Sistema resistente a cargas verticales", tag="th", rowspan=3),
            _cell("Zonas de amenaza sísmica", tag="th", colspan=6),
        ),
        _tr(
            _cell("Alta", tag="th", colspan=2),
            _cell("Intermedia", tag="th", colspan=2),
            _cell("Baja", tag="th", colspan=2),
        ),
        _tr(
            *(
                _cell(label, tag="th")
                for label in ("Uso permitido", "Altura máxima") * 3
            )
        ),
    ]
    body = [
        _tr(_cell("I. Muros estructurales", colspan=9, cls="sec")),
        _tr(
            _cell(
                "a. Muros de mampostería no reforzada (MNR), con algunos muros "
                "confinados y/o intervenidos con revoques con malla electrosoldada (1)"
            ),
            _cell("1", cls="num"),
            _cell("El mismo"),
            *(_cell(v) for v in ("Grupo I (4)", "2 pisos máximo") * 3),
        ),
        _tr(
            _cell("b. Muros de mampostería confinada (MC) (2)"),
            _cell("2", cls="num"),
            _cell("El mismo"),
            *(
                _cell(v)
                for v in (
                    "Grupo I (4)",
                    "2 pisos máximo",
                    "Grupo I (4)",
                    "3 pisos máximo",
                    "Grupo I (4)",
                    "3 pisos máximo",
                )
            ),
        ),
        _tr(
            _cell(
                "(1) Incluye sistemas MNR que antes o después de la intervención "
                "cuenten con algunos muros confinados o revoques con malla "
                "electrosoldada. (2) Los muros MC están delimitados por elementos "
                "verticales y horizontales de concreto reforzado. (3) Las viviendas "
                "MNR de dos pisos pueden evaluarse en amenaza alta, pero la reducción "
                "de vulnerabilidad debe asegurar el confinamiento de los muros del "
                "sistema estructural. (4) Uso residencial Grupo I; se admite uso "
                "comercial en el piso contra tierra y residencial en el resto.",
                colspan=9,
                cls="note",
            )
        ),
    ]
    out["1.2-1"] = _table(
        "1.2-1", "Límites de Aplicabilidad del Documento AIS 410", 12, head, body
    )

    fcu = _math_prime("f", "cu")
    head = [
        _tr(
            _cell("Tipo de unidad", tag="th"),
            _cell(
                tag="th",
                safe_html=f"Resistencia a compresión (1) {fcu} (MPa)",
            ),
        )
    ]
    body = [
        _text_row(("Arcilla de perforación horizontal", "2.0")),
        _text_row(("Concreto de perforación vertical", "5.0")),
        _tr(
            _cell(
                "(1) Resistencias asumidas sobre el área bruta de la unidad.",
                colspan=2,
                cls="note",
            )
        ),
    ]
    out["4.2-1"] = _table(
        "4.2-1",
        "Resistencia a Compresión típica f′cu de las Unidades de Mampostería",
        28,
        head,
        body,
    )

    head = [
        _text_row(
            ("Tipo de unidad", "Resistencia a cortante (1), vn (MPa)"), header=True
        )
    ]
    body = [
        _text_row(("Arcilla de perforación horizontal", "0.21")),
        _text_row(("Concreto de perforación vertical", "0.21")),
        _tr(
            _cell(
                "(1) Resistencias asumidas sobre el área neta de la unidad.",
                colspan=2,
                cls="note",
            )
        ),
    ]
    out["4.2-2"] = _table(
        "4.2-2",
        "Resistencia a Cortante típica vn de las Unidades de Mampostería",
        29,
        head,
        body,
    )

    head = [
        _text_row(
            (
                "Elemento de intervención",
                "Resistencia mínima (MPa)",
                "Especificación mínima",
                "Observaciones",
            ),
            header=True,
        )
    ]
    body = [
        _text_row(("Concreto para cimentación", "21.0", "—", "")),
        _text_row(("Concreto para nuevos elementos estructurales", "17.5", "—", "")),
        _text_row(
            (
                "Revoque para muros",
                "10.0",
                "15 mm para revoque simple; 30 mm para revoque con refuerzo",
                "Mínimo 75% de arena de río lavada para la mezcla.",
            )
        ),
        _text_row(
            (
                "Mampostería — mortero de pega",
                "7.5",
                "10 mm para juntas verticales y horizontales",
                "Mortero tipo N",
            )
        ),
        _text_row(
            (
                "Mampostería — bloques en arcilla",
                "",
                "Secciones E.3.2 y D.3.6.2.2 del Reglamento NSR-10",
                "D.10.3.3 y tabla E.3.5-1 del Reglamento NSR-10",
            )
        ),
        _text_row(
            (
                "Mampostería — bloques en concreto",
                "",
                "Sección D.3.6.2.1 del Reglamento NSR-10",
                "—",
            )
        ),
        _tr(_cell("Elemento de intervención", tag="th"), _cell("Resistencia a tracción mínima (MPa)", tag="th"), _cell("Especificación mínima", tag="th"), _cell("Observaciones", tag="th")),
        _text_row(
            (
                "Acero de refuerzo",
                "420",
                'No. 3 (3/8") o 10M (10 mm), longitudinal; No. 2 (1/4") o 6M (6 mm), transversal',
                "Barras corrugadas",
            )
        ),
        _text_row(
            (
                "Malla electrosoldada",
                "485",
                "Espesor ≥ 4 mm; celdas ≤ 200 mm",
                "",
            )
        ),
    ]
    out["4.3-1"] = _table(
        "4.3-1",
        "Propiedades Mínimas Requeridas para los materiales de intervención",
        30,
        head,
        body,
    )

    head = [
        _text_row(
            (
                "Lugar",
                "Material del bloque",
                "Tipo de ladrillo (dimensiones en mm)",
                "eN = %As / 0.248",
            ),
            header=True,
        )
    ]
    city_rows = [
        ("Bogotá", "Arcilla — No. 5", "No. 5 (330 × 115 × 230)", "1.00"),
        ("Bogotá", "Arcilla — No. 5", "No. 5 (330 × 115 × 230) + revoque a una cara", "1.24"),
        ("Bogotá", "Arcilla — No. 5", "No. 5 (330 × 115 × 230) + revoque a dos caras", "1.45"),
        ("Bogotá", "Arcilla — No. 4", "No. 4 (330 × 90 × 230)", "1.28"),
        ("Bogotá", "Arcilla — No. 4", "No. 4 (330 × 90 × 230) + revoque a una cara", "1.55"),
        ("Bogotá", "Arcilla — No. 4", "No. 4 (330 × 90 × 230) + revoque a dos caras", "1.78"),
        ("Bogotá", "Arcilla — tolete", "Tolete sólido (255 × 120 × 55)", "4.03"),
        ("Bogotá", "Arcilla — LEPV", "LEPV (330 × 115 × 230)", "2.02"),
        ("Medellín", "Arcilla — 100 mm", "100 × 200 × 400, perforación horizontal", "1.13"),
        ("Medellín", "Arcilla — 100 mm", "100 × 200 × 400 + revoque a una cara", "1.39"),
        ("Medellín", "Arcilla — 100 mm", "100 × 200 × 400 + revoque a dos caras", "1.61"),
        ("Medellín", "Arcilla — 150 mm", "150 × 200 × 400, perforación horizontal", "1.24"),
        ("Medellín", "Arcilla — 150 mm", "150 × 200 × 400 + revoque a una cara", "1.41"),
        ("Medellín", "Arcilla — 150 mm", "150 × 200 × 400 + revoque a dos caras", "1.57"),
        ("Cali", "Arcilla — 100 mm", "100 × 200 × 300, perforación horizontal", "1.45"),
        ("Cali", "Arcilla — 100 mm", "100 × 200 × 300 + revoque a una cara", "1.69"),
        ("Cali", "Arcilla — 100 mm", "100 × 200 × 300 + revoque a dos caras", "1.88"),
        ("Cali", "Arcilla — 120 mm", "120 × 200 × 300, perforación horizontal", "1.41"),
        ("Cali", "Arcilla — 120 mm", "120 × 200 × 300 + revoque a una cara", "1.61"),
        ("Cali", "Arcilla — 120 mm", "120 × 200 × 300 + revoque a dos caras", "1.19"),
        ("Colombia", "Concreto — 140 mm", "140 × 190 × 390", "2.3"),
    ]
    body = []
    group_sizes = {"Bogotá": 8, "Medellín": 6, "Cali": 6, "Colombia": 1}
    seen: set[str] = set()
    for city, material, kind, factor in city_rows:
        cells = []
        if city not in seen:
            cells.append(_cell(city, rowspan=group_sizes[city]))
            seen.add(city)
        cells.extend((_cell(material), _cell(kind), _cell(factor, cls="num")))
        body.append(_tr(*cells))
    out["5.10-1"] = _table(
        "5.10-1", "Factores de área neta para diferentes tipos de bloques", 41, head, body
    )

    head = [
        _tr(
            _cell("Sistema constructivo", tag="th", rowspan=2),
            _cell("Espesor mínimo aceptable", tag="th", colspan=3),
        ),
        _text_row(("Piso 1", "Piso 2", "Piso 3"), header=True),
    ]
    body = [
        _text_row(("MNR", "110 mm", "110 mm", "N/A")),
        _text_row(("MC", "110 mm", "110 mm", "95 mm")),
    ]
    out["6.3-1"] = _table(
        "6.3-1", "Espesores mínimos para muros existentes", 46, head, body
    )

    head = [
        _tr(
            _cell("Zona de amenaza", tag="th", rowspan=2),
            _cell("Tipo de suelo", tag="th", rowspan=2),
            _cell("Relación h/t en mampostería no reforzada", tag="th", colspan=3),
        ),
        _text_row(
            ("Techo liviano", "Entrepiso pesado + losa", "Piso superior"),
            header=True,
        ),
    ]
    data = [
        ("Baja", "A", "25", "25", "25"),
        ("Baja", "B", "25", "25", "25"),
        ("Baja", "C", "25", "25", "25"),
        ("Baja", "D", "25", "25", "25"),
        ("Baja", "E", "21", "17", "22"),
        ("Intermedia", "A", "25", "25", "25"),
        ("Intermedia", "B", "22", "21", "25"),
        ("Intermedia", "C", "21", "17", "22"),
        ("Intermedia", "D", "20", "16 (1)", "20"),
        ("Intermedia", "E", "19", "16 (1)", "16"),
    ]
    body = []
    for i, row in enumerate(data):
        cells = []
        if i in (0, 5):
            cells.append(_cell(row[0], rowspan=5))
        cells.extend(_cell(v) for v in row[1:])
        body.append(_tr(*cells))
    body.append(
        _tr(
            _cell(
                "(1) El área tributaria del muro debe ser mayor a 0.7 m; si es "
                "menor, la relación h/t se limita a 12.",
                colspan=5,
                cls="note",
            )
        )
    )
    out["6.3-2"] = _table(
        "6.3-2",
        "Límites de altura/espesor de muros con base en la tipología de vivienda y la zona sísmica",
        47,
        head,
        body,
    )

    head = [
        _text_row(
            (
                "Nivel de daño en muros",
                "% máximo aceptable de muros con daño atribuible a problemas de cimentación",
                "Desempeño",
            ),
            header=True,
        )
    ]
    body = [
        _text_row(("Ninguno / muy leve", "50", "Cumple")),
        _text_row(("Leve", "30", "No cumple")),
        _text_row(("Moderado", "10", "No cumple")),
        _text_row(("Fuerte", "6", "No cumple")),
        _text_row(("Severo", "4", "No cumple")),
    ]
    out["6.4-1"] = _table(
        "6.4-1",
        "Límites de aceptación de muros con daños atribuibles a problemas de cimentación",
        48,
        head,
        body,
    )

    sa = ("0.20", "0.40", "0.60", "0.80", "1.00")
    head = [
        _tr(
            _cell("Vivienda", tag="th", rowspan=2),
            _cell("Tipo de cubierta", tag="th", rowspan=2),
            _cell("Nivel", tag="th", rowspan=2),
            _cell("Sa (g)", tag="th", colspan=5),
        ),
        _tr(*(_cell(v, tag="th") for v in sa)),
    ]
    body = [
        _tr(_cell("1 piso", rowspan=2), _cell("Liviana"), _cell("1"), *(_cell(v) for v in ("4.0%", "4.0%", "6.0%", "8.1%", "10.1%"))),
        _tr(_cell("Pesada"), _cell("1"), *(_cell(v) for v in ("4.1%", "8.1%", "12.2%", "16.3%", "20.4%"))),
        _tr(_cell("2 pisos", rowspan=4), _cell("Liviana", rowspan=2), _cell("1"), *(_cell(v) for v in ("6.1%", "12.2%", "18.3%", "24.4%", "30.4%"))),
        _tr(_cell("2"), *(_cell(v) for v in ("4.0%", "6.1%", "9.1%", "12.2%", "15.2%"))),
        _tr(_cell("Pesada", rowspan=2), _cell("1"), *(_cell(v) for v in ("8.1%", "16.3%", "24.4%", "32.6%", "40.7%"))),
        _tr(_cell("2"), *(_cell(v) for v in ("5.5%", "10.9%", "16.4%", "21.8%", "27.3%"))),
    ]
    out["6.8-1"] = _table(
        "6.8-1",
        "Porcentajes de Área de Muro Mínimos Requeridos — Viviendas de mampostería no reforzada",
        57,
        head,
        body,
    )

    sa2 = ("0.20", "0.40", "0.60", "0.80", "1.00", "1.20", "1.40")
    head = [
        _tr(
            _cell("Sa (g)", tag="th", rowspan=3),
            _cell("Viviendas de 1 piso", tag="th", colspan=2),
            _cell("Viviendas de 2 pisos", tag="th", colspan=4),
            _cell("Viviendas de 3 pisos", tag="th", colspan=6),
        ),
        _tr(
            _cell("Liviana", tag="th", rowspan=2),
            _cell("Pesada", tag="th", rowspan=2),
            _cell("Liviana", tag="th", colspan=2),
            _cell("Pesada", tag="th", colspan=2),
            _cell("Liviana", tag="th", colspan=3),
            _cell("Pesada", tag="th", colspan=3),
        ),
        _tr(
            *(
                _cell(v, tag="th")
                for v in (
                    "Piso 1",
                    "Piso 2",
                    "Piso 1",
                    "Piso 2",
                    "Piso 1",
                    "Piso 2",
                    "Piso 3",
                    "Piso 1",
                    "Piso 2",
                    "Piso 3",
                )
            )
        ),
    ]
    values = [
        ("4.0%", "4.0%", "4.0%", "4.0%", "4.1%", "4.0%", "5.1%", "4.0%", "4.0%", "6.1%", "5.1%", "4.0%"),
        ("4.0%", "4.1%", "6.1%", "4.0%", "8.1%", "5.5%", "10.2%", "7.9%", "4.0%", "12.2%", "10.1%", "6.1%"),
        ("4.0%", "6.1%", "9.1%", "4.6%", "12.2%", "8.2%", "15.2%", "11.9%", "5.0%", "18.3%", "15.2%", "9.2%"),
        ("4.0%", "8.1%", "12.2%", "6.1%", "16.3%", "10.9%", "20.3%", "15.9%", "6.7%", "24.4%", "20.3%", "12.2%"),
        ("5.0%", "10.2%", "15.2%", "7.6%", "20.4%", "13.6%", "25.4%", "19.8%", "8.4%", "30.5%", "25.4%", "15.3%"),
        ("6.0%", "12.2%", "18.3%", "9.1%", "24.4%", "16.4%", "30.5%", "23.8%", "10.1%", "36.7%", "30.4%", "18.3%"),
        ("7.1%", "14.3%", "21.3%", "10.7%", "28.5%", "19.1%", "35.6%", "27.7%", "11.7%", "42.8%", "35.5%", "21.4%"),
    ]
    body = [_tr(_cell(s), *(_cell(v) for v in row)) for s, row in zip(sa2, values)]
    out["6.8-2"] = _table(
        "6.8-2",
        "Porcentajes de Área de Muro Mínimos Requeridos — Viviendas de mampostería confinada",
        57,
        head,
        body,
    )

    head = [
        _tr(
            _cell("f′cu (MPa)", tag="th", rowspan=2),
            _cell("Tipo de unidad de mampostería", tag="th", colspan=3),
        ),
        _text_row(
            ("Bloque de arcilla PH", "Tolete sólido", "Bloque de concreto"),
            header=True,
        ),
    ]
    body = [
        _text_row(("1.5", "1.11", "1.00", "1.60")),
        _text_row(("2.0", "1.00", "0.95", "1.45")),
        _text_row(("3.0", "0.85", "0.86", "1.24")),
        _text_row(("8.0", "0.55", "0.63", "0.81")),
        _text_row(("12.0", "0.46", "0.54", "0.67")),
        _text_row(("> 15", "0.41", "0.49", "0.60")),
    ]
    out["6.8-4"] = _table(
        "6.8-4", "Valores de Cs por tipo de unidad de mampostería", 58, head, body
    )

    head = [
        _tr(
            _cell("Nivel", tag="th", rowspan=2),
            _cell("Número de pisos", tag="th", colspan=3),
        ),
        _text_row(("1 piso", "2 pisos", "3 pisos"), header=True),
    ]
    body = [
        _text_row(("3", "—", "—", "0.39")),
        _text_row(("2", "—", "0.57", "0.65")),
        _text_row(("1", "1.00", "0.86", "0.79")),
    ]
    out["6.8-5"] = _table(
        "6.8-5", "Cp para viviendas con pisos y sistemas de techo pesados", 59, head, body
    )

    body = [
        _text_row(("3", "—", "—", "0.14")),
        _text_row(("2", "—", "0.57", "0.46")),
        _text_row(("1", "1.00", "0.86", "0.61")),
    ]
    out["6.8-6"] = _table(
        "6.8-6", "Cp para viviendas con entrepisos pesados y techo liviano", 59, head, body
    )

    head = [
        _tr(_cell("Factor de Peso Sísmico, Cw = peso sísmico real distribuido a medio nivel / 5.05 kPa", tag="th", colspan=4)),
        _tr(
            _cell("Mampuesto", tag="th"),
            _cell("Revoques en los otros muros", tag="th"),
            _cell("Ninguno", tag="th"),
            _cell("1 capa de revoque (15 mm)", tag="th"),
        ),
    ]
    finish_rows = (
        ("Ninguno", "1.00 (1)", ""),
        ("1 capa de revoque (15 mm), < 50% de los muros", "1.06 (1)", ""),
        ("1 capa de revoque (15 mm), > 50% de los muros", "1.13 (1)", ""),
        ("2 capas de revoque (15 mm) o revoque con malla (30 mm), < 50% de los muros", "1.13 (1)", "1.19 (1)"),
        ("2 capas de revoque (15 mm) o revoque con malla (30 mm), > 50% de los muros", "1.26", "1.26 (1)"),
    )
    body = []
    for material, base in (("Arcilla de perforación horizontal", "arcilla"), ("Tolete sólido", "tolete")):
        for i, (finish, none, one) in enumerate(finish_rows):
            if base == "tolete":
                none, one = (
                    ("1.40", ""),
                    ("1.44", ""),
                    ("1.50", ""),
                    ("1.50", "1.57"),
                    ("1.63", "1.63"),
                )[i]
            cells = []
            if i == 0:
                cells.append(_cell(material, rowspan=5))
            cells.extend((_cell(finish), _cell(none), _cell(one)))
            body.append(_tr(*cells))
    body.append(
        _tr(
            _cell(
                "(1) Para el último piso de viviendas con techo liviano y muros "
                "de bloque de arcilla de perforación horizontal, se considera una "
                "reducción del 50% de los valores de Cw.",
                colspan=4,
                cls="note",
            )
        )
    )
    out["6.8-7"] = _table(
        "6.8-7", "Valores de Cw por tipo de acabado de muros", 60, head, body
    )

    head = [
        _text_row(
            ("Sistemas de entrepiso", "Anclajes no dúctiles", "Anclajes dúctiles (1)"),
            header=True,
        )
    ]
    body = [
        _text_row(("Losas macizas", "150 mm", "Sin límite")),
        _text_row(("Losas aligeradas", "50 mm", "Sin límite")),
        _text_row(("Losas prefabricadas (2)", "160 mm", "Sin límite")),
        _tr(
            _cell(
                "(1) Incluye pernos de expansión y anclajes superficiales con "
                "epóxicos, vaciados en sitio o colocados por medio de explosivos. "
                "(2) Aplicable a losas con bloquelón y perfiles metálicos.",
                colspan=3,
                cls="note",
            )
        ),
    ]
    out["7.4-1"] = _table(
        "7.4-1",
        "Excentricidades máximas admisibles para discontinuidades verticales de muros",
        65,
        head,
        body,
    )

    head = [
        _tr(
            _cell("Mampostería nueva", tag="th", rowspan=2),
            *(_cell(v, tag="th", rowspan=2) for v in ("H (mm)", "L (mm)", "t (mm)", "f′cu (MPa)", "AN/AB")),
            _cell("f′cu (MPa) de la mampostería existente (1)", tag="th", colspan=4),
        ),
        _text_row(("1.5", "2.0", "3.0", "5.0"), header=True),
    ]
    body = [
        _text_row(("Bloque de arcilla PH (> 3 MPa, 25% sólido)", "230", "330", "120", "2", "0.25", "1.4", "1.2", "1.0", "0.8")),
        _text_row(("Relleno de aberturas con el mismo material existente (> 2 MPa)", "60", "240", "120", "2", "1.0", "1.0", "1.0", "1.0", "1.0")),
        _tr(_cell("(1) Para justificar f′cu superior a 2.0 MPa en bloques existentes se requieren ensayos del bloque de la vivienda.", colspan=10, cls="note")),
    ]
    out["7.8-1"] = _table(
        "7.8-1", "Valores del Coeficiente Km para diferentes tipos de bloques", 71, head, body
    )

    head = [
        _text_row(
            ("Prioridad", "Condición por subsanar", "Ejemplos de obras por desarrollar"),
            header=True,
        )
    ]
    priority_rows = [
        (
            "1",
            "Condición estructural: elementos muy dañados o desgastados; muros "
            "significativamente agrietados o deteriorados; elementos de concreto "
            "reforzado agrietados, con acero expuesto o corroído.",
            "Demolición y reconstrucción de muros o elementos de concreto dañados; "
            "resane y reparación de concreto reforzado; en techos livianos, "
            "sustitución de correas, tejas, anclajes y demás elementos en mal estado.",
        ),
        (
            "2",
            "Transferencia de cargas: falta de muros transversales, muros esbeltos, "
            "falta de vigas de amarre o conexión al diafragma.",
            "Relleno o reconfiguración de aberturas; muros perimetrales independientes; "
            "muros perpendiculares a culatas; nuevas vigas, columnetas y amarres; "
            "aumento del espesor con revoque y refuerzo de estructuras de contención.",
        ),
        (
            "3",
            "Configuración: fachadas muy abiertas, falta de muros perimetrales, "
            "excentricidad torsional, culatas sin amarre, voladizos y configuraciones "
            "irregulares.",
            "Demolición y reconstrucción de culatas o fachadas; soporte de voladizos; "
            "refuerzo de escaleras; juntas sísmicas; demolición de pisos; nuevos "
            "muros, confinamiento de parapetos y sustitución de cimentaciones deficientes.",
        ),
        (
            "4",
            "Resistencia/ductilidad: mampostería de baja resistencia, falta de muros, "
            "muros sin confinar y aberturas sin confinamiento.",
            "Revoques con o sin malla electrosoldada; conversión a mampostería "
            "confinada; confinamiento de aberturas en los muros.",
        ),
    ]
    body = [_text_row(row) for row in priority_rows]
    out["7.9-1"] = _table(
        "7.9-1", "Priorización de condiciones a subsanar", 73, head, body
    )

    return out


if __name__ == "__main__":
    tables = curated_ais410_tables()
    print(f"{len(tables)} tables")
    print(", ".join(tables))
