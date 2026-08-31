# -*- coding: utf-8 -*-
"""Parse technical annexes (decrees and drafts) and explicit Title B / AIS injections."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(r"E:\dev\NSR-10")

DOC_META = {
    "d092": {
        "file": "Modificaciones/2011-01-17-Decreto-092-2011-Anexo-Decreto-de-Modificaciones-Tecnicas-y-Cientificas-a-NSR-10.pdf",
        "title": "Decreto 092 de 2011",
    },
    "d340": {
        "file": "Modificaciones/2012-02-13-Decreto-340 02 13-2012_Anexo tecnico.pdf",
        "title": "Decreto 340 de 2012",
    },
    "d340draft": {
        "file": "Modificaciones/2012-01-24-Anexo-Final-al-Decreto-xxx-de-2012-Modificaciones-Tecnicas-y-Cientificas-a-NSR-10.pdf",
        "title": "Anexo tecnico (borrador) Decreto 340 de 2012",
    },
    "d945": {
        "file": "Modificaciones/2017-06-05-Decreto-945-del-05-de-junio-de-2017.pdf",
        "title": "Decreto 945 de 2017",
    },
    "d2113": {
        "file": "Modificaciones/2019-11-25-Decreto-2113-del-25-de-noviembre-de-2019.pdf",
        "title": "Decreto 2113 de 2019",
    },
    "d1711": {
        "file": "Modificaciones/2021-12-13-Decreto-1711-del-13-de-diciembre-de-2021.pdf",
        "title": "Decreto 1711 de 2021",
    },
    "borrador": {
        "file": "Modificaciones/2021-12-13-borrador decreto 2021-modificacion-nsr-10.pdf",
        "title": "Borrador tecnico 2021 (anexo Decreto 1711)",
    },
    "d1401": {
        "file": "Modificaciones/2023-08-25-DECRETO-1401-DEL-25-DE-AGOSTO-DE-2023.pdf",
        "title": "Decreto 1401 de 2023 (AIS 410-23)",
    },
    "d1580": {
        "file": "Modificaciones/2023-09-25-DECRETO 1580 DE 2023.pdf",
        "title": "Decreto 1580 de 2023",
    },
}

HEADING_NSR = re.compile(
    r"^([A-K])\.(\d+(?:\.\d+){0,8})\s*(?:[\u2014\u2013\-\u2212]+\s*|\s{2,})(.*)$"
)
HEADING_F4A = re.compile(
    r"^(F\.4\.A\.?\d+(?:\.\d+){0,8})\s*(?:[\u2014\u2013\-\u2212]+\s*|\s{2,})(.*)$",
    re.I,
)
PAGE_RE = re.compile(r"^-- PAGE (\d+) --$")
ART_ID_RE = re.compile(r"\b([A-K]\.\d+(?:\.\d+){0,6})\b")
CUE = re.compile(
    r"(quedar[a\u00e1]\s+as[i\u00ed]|debe quedar|se reemplaza|se substituye|se sustituye|"
    r"se modifica|se introduce|se suprime|se agrega|se adiciona)",
    re.I,
)


def clean_line(line: str) -> str:
    return line.replace("\u00a0", " ").strip()


def parse_pages(raw: str):
    page = 1
    out = []
    for line in raw.splitlines():
        m = PAGE_RE.match(line.strip())
        if m:
            page = int(m.group(1))
            continue
        out.append((page, line.rstrip()))
    return out


def parse_patches(text: str, source_id: str) -> dict:
    """article_id -> {source, text, page}."""
    replacements = {}
    lines = [(p, clean_line(s)) for p, s in parse_pages(text)]
    i = 0
    while i < len(lines):
        page, s = lines[i]
        if not CUE.search(s):
            i += 1
            continue
        window = " ".join(x[1] for x in lines[max(0, i - 2) : i + 1])
        ids = ART_ID_RE.findall(window)
        body = []
        j = i + 1
        start_page = page
        while j < len(lines) and j < i + 90:
            pj, t = lines[j]
            if CUE.search(t) and j > i + 1:
                break
            if re.match(r"^(REP[U\u00da]BLICA|MINISTERIO|COMISI[O\u00d3]N|DECRETO No)", t, re.I):
                j += 1
                continue
            if t:
                body.append(t)
            j += 1
        body_txt = "\n".join(body).strip()
        if ids and len(body_txt) > 40:
            art = ids[-1]
            start = body_txt.lstrip()
            if start.startswith(art) or re.match(rf"^{re.escape(art)}\b", start) or "introduce" in s.lower():
                replacements[art] = {
                    "source": source_id,
                    "text": body_txt,
                    "page": start_page,
                    "file": DOC_META.get(source_id, {}).get("file", ""),
                }
        i = j
    return replacements


def parse_f4a_articles(text: str):
    rows = parse_pages(text)
    articles = []
    current = None
    started = False
    for page, raw in rows:
        line = clean_line(raw)
        line_n = re.sub(r"F\.4\.A(\d)", r"F.4.A.\1", line, flags=re.I)
        hm = HEADING_F4A.match(line_n.replace("F.4.A", "F.4.A."))
        if not hm:
            hm = re.match(
                r"^(F\.4\.A\.?\d+(?:\.\d+)*)\s*(?:[\u2014\u2013\-]+\s*)?(.*)$",
                line_n,
                re.I,
            )
        if hm and page >= 6:
            started = True
            aid = re.sub(r"F\.4\.A(?!\.)", "F.4.A.", hm.group(1), flags=re.I)
            aid = re.sub(r"\.{2,}", ".", aid)
            title = (hm.group(2) or "").strip()
            if current:
                articles.append(current)
            current = {"id": aid, "title": title, "page": page, "lines": []}
            continue
        if not started or current is None:
            continue
        if line.startswith("NSR-10 Ap") or re.match(r"^\d+$", line):
            continue
        current["lines"].append((page, line))
    if current:
        articles.append(current)
    return articles


def _ok_ais_id(num: str) -> bool:
    parts = num.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return False
    first = int(parts[0])
    if first < 1 or first > 12:
        return False
    return all(int(p) < 80 for p in parts)


def _ok_ais_title(title: str) -> bool:
    t = re.sub(r"[\-\u2014\u2013\xad\s:.'\"]+", " ", title).strip()
    return sum(ch.isalpha() for ch in t) >= 5


def parse_ais410_articles(text: str):
    rows = parse_pages(text)
    articles = []
    current = None
    pending_id = None
    pending_page = 1
    for page, raw in rows:
        if page < 11:
            continue
        line = clean_line(raw)
        cm = re.match(r"^CAP[I\u00cd]TULO\s+(\d+)\.?\s*(.*)$", line, re.I)
        if cm:
            pending_id = None
            continue
        idm = re.match(r"^(\d+(?:\.\d+){0,5})\s*$", line)
        if idm:
            cand = idm.group(1)
            if cand.isdigit() and int(cand) == page:
                continue
            if _ok_ais_id(cand):
                pending_id = cand
                pending_page = page
            continue
        if pending_id:
            if re.match(r"^[\-\u2014\u2013]+\s*$", line):
                continue
            title = re.sub(r"^[\-\u2014\u2013]\s*", "", line).strip()
            if not _ok_ais_title(title):
                continue
            aid = "AIS410-" + pending_id
            if current:
                articles.append(current)
            current = {"id": aid, "title": title, "page": pending_page, "lines": []}
            pending_id = None
            continue
        hm = re.match(r"^(\d+(?:\.\d+){1,5})\s*[\-\u2014\u2013]\s*(.+)$", line)
        if hm and _ok_ais_id(hm.group(1)) and _ok_ais_title(hm.group(2)):
            aid = "AIS410-" + hm.group(1)
            if current:
                articles.append(current)
            current = {"id": aid, "title": hm.group(2).strip(), "page": page, "lines": []}
            pending_id = None
            continue
        if current is None:
            continue
        if line.startswith("AIS 410") or re.match(r"^\d+$", line):
            continue
        current["lines"].append((page, line))
    if current:
        articles.append(current)
    return articles


def wind_injection_html():
    href = DOC_META["d1711"]["file"]
    return (
        '<p class="mod-note">Decreto 1711 de 2021 &mdash; amenaza eolica y velocidades de viento '
        "para el Archipielago de San Andres, Providencia y Santa Catalina.</p>"
        f'<figure class="nsr-fig"><figcaption>'
        f'<a href="{html.escape(href)}#page=5" target="_blank" rel="noopener">Figura B.6.4-1</a> '
        "&mdash; Velocidad del viento basico, Zonas de amenaza eolica "
        "<span class='muted'>(mapa actualizado, Decreto 1711, pag. 5)</span>"
        "</figcaption></figure>"
        '<div class="nsr-table-wrap"><p class="table-cap">Velocidades basicas de viento adoptadas '
        "(Decreto 1711 de 2021)</p>"
        '<table class="nsr-table"><thead><tr><th>Lugar</th><th>Velocidad basica V (km/h)</th>'
        "<th>Fuente</th></tr></thead><tbody>"
        "<tr><td>San Andres</td><td>200</td><td>Decreto 1711 de 2021</td></tr>"
        "<tr><td>Providencia y Santa Catalina</td><td>220</td><td>Decreto 1711 de 2021</td></tr>"
        "</tbody></table></div>"
        "<p>La velocidad basica de viento V se toma de la Figura B.6.4-1 actualizada. "
        "Para el Departamento Archipielago se adoptan los valores tabulares anteriores, "
        "con fundamento en los estudios de amenaza eolica considerados por la Comision Asesora Permanente.</p>"
    )


def a109_html():
    h2113 = (
        "<p>A.10.9.2.6 &mdash; Edificaciones patrimoniales de uno y dos pisos de adobe y tapia pisada "
        "&mdash; Cuando se trate de edificaciones declaradas como patrimonio historico, de conservacion "
        "arquitectonica o sectores y bienes de interes cultural de caracter nacional, departamental, "
        "municipal o distrital, de uno y dos pisos construidas con adobe y tapia pisada, el diseno de su "
        "reforzamiento debera realizarse siguiendo los requisitos de la Norma AIS-610-EP-2017 "
        "&laquo;Evaluacion e intervencion de edificaciones patrimoniales de uno y dos pisos de adobe y "
        "tapia pisada&raquo; con el fin de garantizar un nivel de seguridad sismica equivalente al que el "
        "Reglamento exige a una edificacion nueva. Para el procedimiento de evaluacion de la intervencion "
        "se seguira lo establecido en la Seccion A.10.1.4 y una vez efectuado el reforzamiento bajo los "
        "requisitos de la Norma AIS-610-EP-2017, el supervisor tecnico independiente, de conformidad con "
        "lo previsto en la seccion A.10.1.6, al finalizar la intervencion debera indicar mediante concepto "
        "tecnico si la vulnerabilidad ha sido resuelta y definir si se puede autorizar el acceso al publico "
        "en general a la edificacion.</p>"
    )
    h1401 = (
        "<p>A.10.9.2.7 &mdash; Edificaciones de viviendas de mamposteria &mdash; Cuando se trate de "
        "edificaciones de viviendas de uno, dos y tres pisos construidas en mamposteria, la evaluacion, "
        "intervencion y reduccion de vulnerabilidad podra realizarse siguiendo los requisitos de la Norma "
        "AIS 410-23 &laquo;Evaluacion y Reduccion de la Vulnerabilidad Sismica en viviendas de mamposteria&raquo;. "
        "El Decreto 1580 de 2023 corrige el yerro formal del anexo respecto de las ecuaciones 7.8-2 y 7.8-3.</p>"
    )
    return h2113, h1401


def eq_pam():
    from eq_mathml import _n

    e2 = _n(
        "7.8-2",
        "<msub><mi>PAM</mi><mrow><mi>efectivo,x,i</mi></mrow></msub><mo>=</mo>"
        "<msub><mi>PAM</mi><mrow><mi>existente,x,i</mi></mrow></msub><mo>+</mo>"
        "<mfrac><mrow><mn>0.248</mn><mo>(</mo>"
        "<munder><mo>&#x2211;</mo><mi>m</mi></munder><msub><mi>K</mi><mi>m</mi></msub><msub><mi>L</mi><mi>m</mi></msub>"
        "<mo>+</mo><munder><mo>&#x2211;</mo><mi>p</mi></munder><msub><mi>K</mi><mi>p</mi></msub><msub><mi>L</mi><mi>p</mi></msub>"
        "<mo>+</mo><munder><mo>&#x2211;</mo><mi>e</mi></munder><msub><mi>K</mi><mi>e</mi></msub><msub><mi>L</mi><mi>e</mi></msub>"
        "<mo>)</mo></mrow><msub><mi>A</mi><mi>e</mi></msub></mfrac>",
    )
    e3 = _n(
        "7.8-3",
        "<msub><mi>PAM</mi><mrow><mi>efectivo,y,i</mi></mrow></msub><mo>=</mo>"
        "<msub><mi>PAM</mi><mrow><mi>existente,y,i</mi></mrow></msub><mo>+</mo>"
        "<mfrac><mrow><mn>0.248</mn><mo>(</mo>"
        "<munder><mo>&#x2211;</mo><mi>m</mi></munder><msub><mi>K</mi><mi>m</mi></msub><msub><mi>L</mi><mi>m</mi></msub>"
        "<mo>+</mo><munder><mo>&#x2211;</mo><mi>p</mi></munder><msub><mi>K</mi><mi>p</mi></msub><msub><mi>L</mi><mi>p</mi></msub>"
        "<mo>+</mo><munder><mo>&#x2211;</mo><mi>e</mi></munder><msub><mi>K</mi><mi>e</mi></msub><msub><mi>L</mi><mi>e</mi></msub>"
        "<mo>)</mo></mrow><msub><mi>A</mi><mi>e</mi></msub></mfrac>",
    )
    return e2, e3


def rec(aid, title, page, source, html_body, mod_page):
    meta = DOC_META.get(source, {})
    body = html_body or ""
    if "txt-modificado" not in body:
        body = '<div class="txt-modificado">' + body + "</div>"
    return {
        "id": aid,
        "title": title,
        "page": page,
        "source": source,
        "modified": True,
        "modFile": meta.get("file", ""),
        "modPage": mod_page,
        "html": body,
    }


def parse_a5_articles(text: str):
    heading = re.compile(
        r"^(A-5(?:\.\d+){1,8})\s*(?:[\u2014\u2013\-]+\s*)?(.*)$",
    )
    rows = parse_pages(text)
    articles = []
    current = None
    started = False
    for page, raw in rows:
        line = clean_line(raw)
        hm = heading.match(line)
        if hm:
            started = True
            if current:
                articles.append(current)
            current = {
                "id": hm.group(1),
                "title": (hm.group(2) or "").strip(),
                "page": page,
                "lines": [],
            }
            continue
        if not started or current is None:
            continue
        if re.match(r"^(REP[U\u00da]BLICA|MINISTERIO|COMISI[O\u00d3]N)", line, re.I):
            continue
        if re.match(r"^\d+/\d+$", line):
            continue
        current["lines"].append((page, line))
    if current:
        articles.append(current)
    return articles


def a4_xlsx_href():
    path = "Capitulos/APENDICE A-4-Tabla Municipios.xlsx"
    from urllib.parse import quote

    return path, quote(path, safe="/")


def a4_supia_html():
    href = DOC_META["d1711"]["file"]
    xlsx_path, xlsx_href = a4_xlsx_href()
    return (
        '<p class="mod-note">Decreto 1711 de 2021 &mdash; se modifica la amenaza s&iacute;smica del '
        "municipio de Sup&iacute;a (Caldas) en el Ap&eacute;ndice A-4.</p>"
        '<div class="nsr-table-wrap"><p class="table-cap">Ap&eacute;ndice A-4 &mdash; Municipio de Sup&iacute;a '
        "(valores vigentes)</p>"
        '<table class="nsr-table"><thead><tr>'
        "<th>Municipio</th><th>C&oacute;digo</th><th>Aa</th><th>Av</th>"
        "<th>Zona de amenaza s&iacute;smica</th><th>Ae</th><th>Ad</th>"
        "</tr></thead><tbody>"
        "<tr><td>Sup&iacute;a</td><td>17777</td><td>0.25</td><td>0.30</td>"
        "<td>Alta</td><td>0.20</td><td>0.10</td></tr>"
        "</tbody></table></div>"
        "<p>En el Decreto 926 de 2010 el valor de Aa para Sup&iacute;a era 0.15; el Decreto 1711 lo sustituye "
        "por 0.25. Los dem&aacute;s par&aacute;metros (Av, Ae, Ad y zona Alta) se mantienen.</p>"
        f'<p class="muted"><a href="{html.escape(href)}#page=4" target="_blank" rel="noopener">'
        "Ver fila adoptada en el Decreto 1711, p&aacute;g. 4</a></p>"
        f'<p class="download-xlsx"><a href="{html.escape(xlsx_href)}" download="'
        f'{html.escape(xlsx_path.split("/")[-1])}">Descargar tabla de municipios (Excel)</a> '
        '<span class="muted">Mismos datos del Ap&eacute;ndice A-4 (Aa, Av, Ae, Ad y zona de amenaza '
        "s&iacute;smica por municipio) en hoja de c&aacute;lculo, para consulta, programaci&oacute;n "
        "de una hoja propia o base de datos local.</span></p>"
    )


def a5_phrase_fix(text: str) -> str:
    return re.sub(
        r"para lo cual podr[a\u00e1]n consultar la Tabla A-5\.2[\s\u2013\u2014\-]*1\.?",
        "para lo cual deben consultar el t\u00edtulo VI de la Ley 400 de 1997 "
        "sobre calidades y requisitos de los profesionales.",
        text,
        flags=re.I,
    )


def chapter_of(art_id: str) -> str:
    if art_id.startswith("AIS410-"):
        rest = art_id.split("-", 1)[1]
        return "AIS410-" + rest.split(".")[0]
    if art_id.upper().startswith("F.4.A"):
        nums = re.findall(r"\d+", art_id)
        if len(nums) >= 2:
            return "F.4.A." + nums[1]
        return "F.4.A"
    parts = art_id.split(".")
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else art_id


def apply_injections(by_title):
    """Attach Title B wind update and A.10.9.2.6 / A.10.9.2.7."""
    wind = wind_injection_html()
    h2113, h1401 = a109_html()
    b6 = by_title.get("B", {}).get("B.6", [])
    wind_ids = {"B.6.4", "B.6.5.4", "B.6.5.4.1", "B.6.5.4.2", "B.6.5.4.3"}
    for art in b6:
        if art["id"] in wind_ids or art["id"].startswith("B.6.4."):
            extra = wind if art["id"] in {"B.6.4", "B.6.5.4"} else ""
            inner = art.get("html") or ""
            if "txt-modificado" in inner:
                inner = inner.replace('<div class="txt-modificado">', '<div class="txt-modificado">' + extra, 1)
            else:
                inner = '<div class="txt-modificado">' + extra + inner + "</div>"
            art["html"] = inner
            art["modified"] = True
            art["source"] = "d1711"
            art["modFile"] = DOC_META["d1711"]["file"]
            art["modPage"] = 5

    def add_or_replace(letter, chap, item):
        lst = by_title[letter][chap]
        for i, a in enumerate(lst):
            if a["id"] == item["id"]:
                lst[i] = item
                return
        lst.append(item)

    add_or_replace(
        "A",
        "A.10",
        rec(
            "A.10.9.2.6",
            "Edificaciones patrimoniales de uno y dos pisos de adobe y tapia pisada",
            140,
            "d2113",
            h2113,
            4,
        ),
    )
    add_or_replace(
        "A",
        "A-4",
        rec(
            "A-4-Supia",
            "Municipio de Supía, Caldas (Apéndice A-4)",
            203,
            "d1711",
            a4_supia_html(),
            4,
        ),
    )
    add_or_replace(
        "A",
        "A.10",
        rec(
            "A.10.9.2.7",
            "Edificaciones de viviendas de mamposteria",
            140,
            "d1401",
            h1401,
            4,
        ),
    )


def build_extra_titles(extracted_dir, lines_to_html, tables):
    extras = []
    p1711 = extracted_dir / "mod-d1711.txt"
    pborr = extracted_dir / "mod-borrador.txt"
    raw_f4 = ""
    if p1711.exists():
        raw_f4 = p1711.read_text(encoding="utf-8", errors="replace")
    if pborr.exists() and raw_f4.count("F.4.A") < 20:
        raw_f4 = pborr.read_text(encoding="utf-8", errors="replace")
    f4_arts = parse_f4a_articles(raw_f4) if raw_f4 else []
    if f4_arts:
        chmap = {}
        for a in f4_arts:
            body = lines_to_html(a["id"], a["lines"], {}, tables=tables)
            ch = chapter_of(a["id"])
            chmap.setdefault(ch, []).append(
                rec(a["id"], a["title"], a["page"], "d1711", body, a["page"])
            )
        chapters = []
        for cid in sorted(chmap.keys(), key=lambda x: [int(n) for n in re.findall(r"\d+", x)] or [0]):
            chapters.append(
                {
                    "id": cid,
                    "name": "Apéndice F.4-A — " + cid,
                    "page": chmap[cid][0]["page"],
                    "articles": chmap[cid],
                }
            )
        extras.append(
            {
                "letter": "F4A",
                "name": "Apéndice F.4-A — Sistemas de lámina formada en frío (Decreto 1711 / anexo 2021)",
                "chapters": chapters,
            }
        )

    p1401 = extracted_dir / "mod-d1401.txt"
    if p1401.exists():
        ais = parse_ais410_articles(p1401.read_text(encoding="utf-8", errors="replace"))
        e2, e3 = eq_pam()
        chmap = {}
        for a in ais:
            body = lines_to_html(a["id"], a["lines"], {}, tables=tables)
            aid_l = a["id"].lower()
            title_l = (a["title"] or "").lower()
            body_l = body.lower()
            if (
                aid_l.startswith("ais410-7.8.3")
                or aid_l.startswith("ais410-7.8.2")
                or ("pam" in title_l and "efectivo" in title_l)
                or "7.8-2" in body_l
                or "7.8 -2" in body_l
                or "7.8 - 2" in body_l
            ):
                body += (
                    '<p class="mod-note">Decreto 1580 de 2023: se adoptan las ecuaciones 7.8-2 y 7.8-3 '
                    "corregidas del anexo AIS 410-23.</p>"
                    + e2
                    + e3
                )
            ch = chapter_of(a["id"])
            chmap.setdefault(ch, []).append(
                rec(a["id"], a["title"], a["page"], "d1401", body, a["page"])
            )
        has_pam = any("PAM" in art["html"] and "msub" in art["html"] for arts in chmap.values() for art in arts)
        if not has_pam:
            chmap.setdefault("AIS410-7", []).append(
                rec(
                    "AIS410-7.8.3",
                    "Cálculo del PAM efectivo — ecuaciones 7.8-2 y 7.8-3",
                    71,
                    "d1580",
                    '<p class="mod-note">Decreto 1580 de 2023: se corrige el yerro formal del Decreto 1401 '
                    "respecto de las ecuaciones 7.8-2 y 7.8-3 del anexo AIS 410-23.</p>"
                    + e2
                    + e3,
                    1,
                )
            )
        chapters = []
        for cid in sorted(chmap.keys(), key=lambda x: [int(n) for n in re.findall(r"\d+", x)] or [0]):
            chapters.append(
                {
                    "id": cid,
                    "name": cid.replace("AIS410-", "Capítulo "),
                    "page": chmap[cid][0]["page"],
                    "articles": chmap[cid],
                }
            )
        if chapters:
            extras.append(
                {
                    "letter": "AIS410",
                    "name": "AIS 410-23 — Evaluación y reducción de vulnerabilidad en viviendas de mampostería (Decretos 1401 y 1580 de 2023)",
                    "chapters": chapters,
                }
            )

    extras.insert(
        0,
        {
            "letter": "A4APP",
            "name": "Apéndice A-4 — Valores de Aa, Av, Ae y Ad (modificación Decreto 1711, Supía)",
            "chapters": [
                {
                    "id": "A-4",
                    "name": "Municipios colombianos — fila modificada",
                    "page": 4,
                    "articles": [
                        rec(
                            "A-4-Supia",
                            "Municipio de Supía, Caldas",
                            4,
                            "d1711",
                            a4_supia_html(),
                            4,
                        )
                    ],
                }
            ],
        },
    )

    p945 = extracted_dir / "mod-d945.txt"
    if p945.exists():
        a5 = parse_a5_articles(p945.read_text(encoding="utf-8", errors="replace"))
        chmap = {}
        for a in a5:
            joined = (a["title"] or "") + " " + " ".join(ln for _, ln in a["lines"])
            if a["id"] in {"A-5.2.1.1", "A-5.2.1.2", "A-5.2.1.3", "A-5.2.1.4"}:
                fixed = a5_phrase_fix(joined)
                raw_lines = [(a["page"], fixed)]
                a["title"] = a5_phrase_fix(a["title"] or "")
            else:
                raw_lines = a["lines"]
            body = lines_to_html(a["id"], raw_lines, {}, tables=tables)
            body = a5_phrase_fix(body)
            if a["id"] in {"A-5.2.1.1", "A-5.2.1.2", "A-5.2.1.3", "A-5.2.1.4"}:
                src, mpg = "d1711", 4
            else:
                src, mpg = "d945", a["page"]
            if a["id"] == "A-5.2.2.4" or "Tabla A-5.2-1" in joined:
                body = (
                    '<p class="mod-note">Decreto 1711 de 2021: se suprime la Tabla A-5.2-1 del '
                    "Apéndice A-5. Las calidades profesionales se consultan en el Título VI de la Ley 400 "
                    "de 1997.</p>"
                    + body
                )
                src, mpg = "d1711", 4
            ch = chapter_of(a["id"])
            chmap.setdefault(ch, []).append(
                rec(a["id"], a["title"], a["page"], src, body, mpg)
            )
        chapters = []
        for cid in sorted(chmap.keys(), key=lambda x: [int(n) for n in re.findall(r"\d+", x)] or [0]):
            chapters.append(
                {
                    "id": cid,
                    "name": "Apéndice " + cid,
                    "page": chmap[cid][0]["page"],
                    "articles": chmap[cid],
                }
            )
        if chapters:
            extras.insert(
                1,
                {
                    "letter": "A5APP",
                    "name": "Apéndice A-5 — Profesiones y acreditación (Decreto 945, con ajustes del Decreto 1711)",
                    "chapters": chapters,
                },
            )
    return extras
