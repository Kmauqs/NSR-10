# -*- coding: utf-8 -*-

"""Build NSR-10 HTML reader data: articles, MathML, tables, figure links, modifications."""

from __future__ import annotations

import html

import json

import os

import re

import sys

import unicodedata

from collections import defaultdict

from pathlib import Path

ROOT = Path(r"E:\dev\NSR-10")

sys.path.insert(0, str(ROOT / "tools"))

from eq_mathml import fallback_eq, mathml_for  # noqa: E402
import nsr_render  # noqa: E402
import annexes  # noqa: E402
import nomenclature  # noqa: E402
import definitions  # noqa: E402

OUT_DIR = ROOT / "lector"

EXTRACTED = ROOT / "extracted"

PDF_BASE = "NSR10-Completa.pdf"

CHAPTER_NAMES = {

    "A": [

        "Introducción",

        "Zonas de amenaza sísmica y movimientos sísmicos de diseño",

        "Requisitos generales de diseño sismo resistente",

        "Método de la fuerza horizontal equivalente",

        "Método del análisis dinámico",

        "Requisitos de la deriva",

        "Interacción suelo-estructura",

        "Efectos sísmicos sobre elementos estructurales no pertenecientes al sistema de resistencia sísmica",

        "Elementos no estructurales",

        "Evaluación e intervención de edificaciones construidas antes de la vigencia del Reglamento",

        "Instrumentación sísmica",

        "Requisitos especiales para edificaciones indispensables de los grupos III y IV",

        "Definiciones y nomenclatura del Título A",

    ],

    "B": [

        "Requisitos generales",

        "Combinaciones de carga",

        "Cargas muertas",

        "Cargas vivas",

        "Empuje de tierra y presión hidrostática",

        "Fuerzas de viento",

    ],

    "C": [

        "Requisitos generales",

        "Notación y definiciones",

        "Materiales",

        "Requisitos de durabilidad",

        "Calidad del concreto, mezclado y colocación",

        "Cimbras y encofrados, embebidos y juntas de construcción",

        "Detalles del refuerzo",

        "Análisis y diseño  consideraciones generales",

        "Requisitos de resistencia y funcionamiento",

        "Flexión y cargas axiales",

        "Cortante y torsión",

        "Longitudes de desarrollo y empalmes del refuerzo",

        "Sistemas de losa en una y dos direcciones",

        "Muros",

        "Cimentaciones",

        "Concreto prefabricado",

        "Elementos compuestos concreto-concreto sometidos a flexión",

        "Concreto preesforzado",

        "Cáscaras y losas plegadas",

        "Evaluación de la resistencia de estructuras existentes",

        "Requisitos de diseño sismo resistente",

        "Concreto estructural simple",

        "Tanques y estructuras de ingeniería ambiental de concreto",

    ],

    "D": [

        "Requisitos generales",

        "Clasificación, usos, normas, nomenclatura y definiciones",

        "Calidad de los materiales en la mampostería estructural",

        "Requisitos constructivos para mampostería estructural",

        "Requisitos generales de análisis y diseño",

        "Mampostería de cavidad reforzada",

        "Muros de mampostería reforzada con unidades de perforación vertical",

        "Muros de mampostería parcialmente reforzada con unidades de perforación vertical",

        "Muros de mampostería no reforzada",

        "Mampostería de muros confinados",

        "Muros diafragma",

        "Mampostería reforzada externamente",

    ],

    "E": [

        "Introducción",

        "Cimentaciones",

        "Mampostería confinada",

        "Elementos de confinamiento en mampostería confinada",

        "Losas de entrepiso, cubiertas, muros divisorios y parapetos",

        "Recomendaciones adicionales de construcción en mampostería confinada",

        "Bahareque encementado",

        "Entrepisos y uniones en bahareque encementado",

        "Cubiertas para construcción en bahareque encementado",

    ],

    "F": [

        "Requisitos generales",

        "Estructuras de acero con perfiles laminados, armados y tubulares estructurales  parte 1",

        "Estructuras de acero con perfiles laminados, armados y tubulares estructurales  parte 2",

        "Provisiones sísmicas para estructuras de acero con perfiles laminados, armados y tubulares",

        "Estructuras de acero con perfiles de lámina formada en frío  parte 1",

        "Estructuras de acero con perfiles de lámina formada en frío  parte 2",

        "Estructuras de acero con perfiles de lámina formada en frío  parte 3",

        "Estructuras de aluminio",

    ],

    "G": [

        "Requisitos generales",

        "Bases para el diseño estructural",

        "Diseño de elementos solicitados a flexión",

        "Diseño de elementos solicitados por fuerza axial",

        "Diseño de elementos solicitados por flexión y carga axial",

        "Uniones",

        "Diafragmas horizontales y muros de corte",

        "Armaduras",

        "Sistemas estructurales",

        "Aserrado",

        "Preparación, fabricación, construcción, montaje y mantenimiento",

        "Estructuras de guadua",

    ],

    "H": [

        "Introducción",

        "Definiciones",

        "Caracterización geotécnica del subsuelo",

        "Cimentaciones",

        "Excavaciones y estabilidad de taludes",

        "Estructuras de contención",

        "Evaluación geotécnica de efectos sísmicos",

        "Sistema constructivo de cimentaciones, excavaciones y muros de contención",

        "Condiciones geotécnicas especiales",

        "Rehabilitación sísmica de edificios: amenazas de origen sismo-geotécnico y reforzamiento de cimentaciones",

    ],

    "I": [

        "Generalidades",

        "Alcance de la supervisión técnica",

        "Idoneidad del supervisor técnico y su personal auxiliar",

        "Recomendaciones para el ejercicio de la supervisión técnica",

    ],

    "J": [

        "Generalidades",

        "Requisitos generales para protección contra incendios en edificaciones",

        "Requisitos de resistencia contra incendios en edificaciones",

        "Detección y extinción de incendios",

    ],

    "K": [

        "Generalidades, propósito y alcance",

        "Clasificación de las edificaciones por grupos de ocupación",

        "Requisitos para zonas comunes",

        "Requisitos especiales para vidrios",

    ],

}

MOD_SPECS = [
    ("d092", "2011", ROOT / "Modificaciones" / "2011-01-17-Decreto-092-2011-Anexo-Decreto-de-Modificaciones-Tecnicas-y-Cientificas-a-NSR-10.pdf"),
    ("d340draft", "2012", ROOT / "Modificaciones" / "2012-01-24-Anexo-Final-al-Decreto-xxx-de-2012-Modificaciones-Tecnicas-y-Cientificas-a-NSR-10.pdf"),
    ("d340", "2012", ROOT / "Modificaciones" / "2012-02-13-Decreto-340 02 13-2012_Anexo tecnico.pdf"),
    ("d945", "2017", ROOT / "Modificaciones" / "2017-06-05-Decreto-945-del-05-de-junio-de-2017.pdf"),
    ("d2113", "2019", ROOT / "Modificaciones" / "2019-11-25-Decreto-2113-del-25-de-noviembre-de-2019.pdf"),
    ("borrador", "2021", ROOT / "Modificaciones" / "2021-12-13-borrador decreto 2021-modificacion-nsr-10.pdf"),
    ("d1711", "2021", ROOT / "Modificaciones" / "2021-12-13-Decreto-1711-del-13-de-diciembre-de-2021.pdf"),
    ("d1401", "2023", ROOT / "Modificaciones" / "2023-08-25-DECRETO-1401-DEL-25-DE-AGOSTO-DE-2023.pdf"),
    ("d1580", "2023", ROOT / "Modificaciones" / "2023-09-25-DECRETO 1580 DE 2023.pdf"),
]

PAGE_RE = re.compile(r"^-- PAGE (\d+) --$")

HEADING_RE = re.compile(r"^([A-K])\.(\d+(?:\.\d+){0,8})\s*(?:[\u2014\u2013\-\u2212]+\s*|\s{2,})(.*)$")

EQ_LABEL_RE = re.compile(r"\(([A-K]\.\d+(?:\.\d+)?-\d+)\)")

FIG_RE = re.compile(r"^(?:Figura|FIGURA)\s+([A-K]\.[\d.\-]+)\s*[\u2014\u2013\-\u2212]*\s*(.*)$", re.I)

TAB_RE = re.compile(r"^(?:Tabla|TABLA)\s+([A-K]\.[\d.\-]+\s*-?\s*\d+)\s*(?:\((?:continuaci[\u00f3o]n)\))?\s*[\u2014\u2013\-\u2212]*\s*(.*)$", re.I)

CHAP_RE = re.compile(r"^CAP[ÍI]TULO\s+([A-K])\.(\d+(?:\.\d+)?)\b", re.I)

HEADER_RE = re.compile(r"^NSR-10", re.I)

PAGE_NUM_RE = re.compile(r"^[A-K]-?\d+$")

FOOTER_RE = re.compile(r"Secretar[íi]a de la Comisi", re.I)

ART_ID_RE = re.compile(r"^[A-K]\.\d")

def extract_pdf(path: Path) -> str:

    import pymupdf

    doc = pymupdf.open(path)

    parts = []

    for i, page in enumerate(doc, 1):

        parts.append(f"-- PAGE {i} --\n")

        parts.append(page.get_text("text") or "")

        parts.append("\n")

    return "".join(parts)

def extract_all():

    EXTRACTED.mkdir(exist_ok=True)

    nsr_path = EXTRACTED / "NSR10-pages.txt"

    if not nsr_path.exists() or nsr_path.stat().st_size < 1000:

        print("Extracting NSR10-Completa.pdf ")

        nsr_path.write_text(extract_pdf(ROOT / "NSR10-Completa.pdf"), encoding="utf-8")

    else:

        print("Using cached", nsr_path)

    for mid, year, pdf in MOD_SPECS:

        out = EXTRACTED / f"mod-{mid}.txt"

        if pdf.exists() and (not out.exists() or out.stat().st_size < 50):

            print("Extracting", pdf.name)

            try:

                out.write_text(extract_pdf(pdf), encoding="utf-8")

            except Exception as e:

                print("  fail", e)

    return nsr_path.read_text(encoding="utf-8", errors="replace")

def clean_line(line: str) -> str:

    return line.replace("\u00a0", " ").replace("\uf0b7", "").strip()

def is_noise(line: str) -> bool:

    if not line:

        return True

    if HEADER_RE.match(line):

        return True

    if PAGE_NUM_RE.match(line.replace(" ", "")):

        return True

    if FOOTER_RE.search(line):

        return True

    if line.startswith("Carrera 20"):

        return True

    if "Asociación Colombiana de Ingeniería Sísmica" in line and len(line) < 80:

        return True

    return False

def parse_pages(raw: str):

    page = 1

    lines = []

    for line in raw.splitlines():

        m = PAGE_RE.match(line.strip())

        if m:

            page = int(m.group(1))

            continue

        lines.append((page, line.rstrip()))

    return lines

def chapter_of(art_id: str) -> str:

    """A.1.3.4 -> A.1 ; F.2.1.3 -> F.2.1 if that is a chapter key."""

    parts = art_id.split(".")

    letter = parts[0]

    if letter == "F" and len(parts) >= 3 and parts[1] in {"2", "4"}:

        # F.2.1 / F.2.2 / F.4.1 / F.4.2 / F.4.3 are chapter-like

        if parts[2] in {"1", "2", "3"} and (parts[1] != "2" or parts[2] in {"1", "2"}):

            if parts[1] == "2" or (parts[1] == "4" and parts[2] in {"1", "2", "3"}):

                return f"{letter}.{parts[1]}.{parts[2]}"

    return f"{letter}.{parts[1]}" if len(parts) >= 2 else art_id

def parse_articles(raw: str):

    """Return list of {id, title, page, lines: [(page, text)]}."""

    rows = parse_pages(raw)

    articles = []

    current = None

    started = False

    for page, raw_line in rows:

        line = clean_line(raw_line)

        if page >= 44:

            started = True

        if not started:

            continue

        if CHAP_RE.match(line) and current:

            # chapter banners are not articles

            continue

        hm = HEADING_RE.match(line)

        if hm and page >= 44:

            letter, nums, title = hm.group(1), hm.group(2), hm.group(3).strip()

            art_id = f"{letter}.{nums}"

            # skip equation-like A.2.6-1 as heading

            if re.search(r"-\d+$", nums) and not title:

                if current:

                    current["lines"].append((page, line))

                continue

            if current:

                articles.append(current)

            current = {"id": art_id, "title": title, "page": page, "lines": []}

            continue

        if current is None:

            continue

        if is_noise(line):

            continue

        current["lines"].append((page, line if line else ""))

    if current:

        articles.append(current)

    return articles

def parse_mod_replacements(text: str, source_id: str):

    """Find blocks 'La sección X quedará así:' followed by article text."""

    replacements = {}

    # Normalize

    t = text.replace("\u00a0", " ")

    t = re.sub(r"[ \t]+", " ", t)

    pattern = re.compile(

        r"(?:La secci[oó]n|El (?:literal|numeral|art[íi]culo)|En el (?:numeral|art[íi]culo))\s+"

        r"([A-K]\.[\d.]+)\s+(?:quedar[aá]\s+as[ií]|debe quedar as[ií]|debe substituirse|se modifica)"

        r".{0,220}?(?:as[ií]\s*[:.]|siguiente[s]?:)\s*",

        re.I | re.S,

    )

    # Simpler sequential scan

    lines = [clean_line(x) for x in t.splitlines()]

    i = 0

    cue = re.compile(

        r"(quedar[aá]\s+as[ií]|debe quedar|se reemplaza|se substituye|se sustituye|se modifica[rá]?)",

        re.I,

    )

    id_in = re.compile(r"([A-K]\.\d+(?:\.\d+){0,6})")

    while i < len(lines):

        if cue.search(lines[i]):

            window = " ".join(lines[max(0, i - 2) : i + 1])

            ids = id_in.findall(window)

            # collect following body until next cue or long gap of headers

            body = []

            j = i + 1

            while j < len(lines) and j < i + 80:

                if lines[j].startswith("-- PAGE"):

                    j += 1

                    continue

                if cue.search(lines[j]) and j > i + 1:

                    break

                if re.match(r"^(REP[UÚ]BLICA|MINISTERIO|COMISI[OÓ]N|DECRETO No)", lines[j], re.I):

                    j += 1

                    continue

                body.append(lines[j])

                j += 1

            body_txt = "\n".join(x for x in body if x).strip()

            if ids and len(body_txt) > 40:
                art = ids[-1]
                start = body_txt.lstrip()
                if start.startswith(art):
                    replacements[art] = {"source": source_id, "text": body_txt}

            i = j

            continue

        i += 1

    return replacements

def figure_html(fig_id, caption, page):

    cap = html.escape(caption.strip(" -"))

    href = f"{PDF_BASE}#page={page}"

    return (

        f'<figure class="nsr-fig"><figcaption>'

        f'<a href="{href}" target="_blank" rel="noopener">Figura {html.escape(fig_id)}</a>'

        f"{'  ' + cap if cap else ''}"

        f" <span class='muted'>(PDF pág. {page})</span>"

        f"</figcaption></figure>"

    )

def try_table(caption_id, caption, rows):

    """Build HTML table from loosely columnar text rows."""

    cells = []

    for r in rows:

        r = r.strip()

        if not r:

            continue

        parts = re.split(r"\s{2,}", r)

        if len(parts) == 1:

            parts = re.split(r"\t+", r)

        cells.append(parts)

    if len(cells) < 2:

        body = "<p>" + "<br>".join(html.escape(r.strip()) for r in rows if r.strip()) + "</p>"

        return f'<div class="nsr-table-wrap"><p class="table-cap">Tabla {html.escape(caption_id)}  {html.escape(caption)}</p>{body}</div>'

    ncol = max(len(c) for c in cells)

    thead = cells[0]

    while len(thead) < ncol:

        thead.append("")

    head = "".join(f"<th>{html.escape(c)}</th>" for c in thead)

    body_rows = []

    for row in cells[1:]:

        while len(row) < ncol:

            row.append("")

        body_rows.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row[:ncol]) + "</tr>")

    return (

        f'<div class="nsr-table-wrap"><p class="table-cap">Tabla {html.escape(caption_id)}'

        f"{'  ' + html.escape(caption) if caption else ''}</p>"

        f"<table class='nsr-table'><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>"

    )

def lines_to_html(art_id, lines, replacements):

    """Convert article lines to HTML with figures, tables, MathML."""

    used_eq = set()

    html_parts = []

    i = 0

    n = len(lines)

    table_buf = None

    def flush_table():

        nonlocal table_buf

        if table_buf:

            html_parts.append(try_table(*table_buf))

            table_buf = None

    paras = []

    def flush_para():

        if paras:

            txt = " ".join(paras)

            html_parts.append(f"<p>{format_inline(txt, used_eq)}</p>")

            paras.clear()

    while i < n:

        page, line = lines[i]

        s = line.strip()

        fm = FIG_RE.match(s)

        tm = TAB_RE.match(s)

        if fm:

            flush_para()

            flush_table()

            html_parts.append(figure_html(fm.group(1), fm.group(2), page))

            i += 1

            continue

        if tm:

            flush_para()

            flush_table()

            cap_id = re.sub(r"\s+", "", tm.group(1).replace(" ", ""))

            cap_id = cap_id.replace("--", "-")

            caption = (tm.group(2) or "").strip()

            buf = []

            j = i + 1

            while j < n:

                ps, pl = lines[j]

                if HEADING_RE.match(pl.strip()) or FIG_RE.match(pl.strip()) or TAB_RE.match(pl.strip()):

                    break

                if CHAP_RE.match(pl.strip()):

                    break

                buf.append(pl)

                if j - i > 40:

                    break

                j += 1

            html_parts.append(try_table(cap_id, caption, buf))

            i = j

            continue

        eqm = EQ_LABEL_RE.search(s)

        if eqm:

            flush_para()

            flush_table()

            eid = eqm.group(1)

            if eid not in used_eq:

                used_eq.add(eid)

                m = mathml_for(eid)

                html_parts.append(m if m else fallback_eq(eid, s))

            i += 1

            continue

        if not s:

            flush_para()

            i += 1

            continue

        paras.append(s)

        i += 1

    flush_para()

    flush_table()

    return "\n".join(html_parts)

def format_inline(txt, used_eq):

    txt = html.escape(txt)

    txt = re.sub(r"\(([a-z])\)\s", r"<br><strong>(\1)</strong> ", txt)

    # article cross-refs stay as text

    def eq_sub(m):

        eid = m.group(1)

        if eid in used_eq:

            return f'(<a href="#eq-{html.escape(eid)}">{html.escape(eid)}</a>)'

        return m.group(0)

    txt = EQ_LABEL_RE.sub(eq_sub, txt)

    return txt

def apply_global_fixes(text: str) -> str:

    text = text.replace(

        "Instituto de Investigaciones en Geociencia, Minería y Química  Ingeominas",

        "Instituto Colombiano de Geología y Minería - INGEOMINAS",

    )

    text = text.replace(

        "Instituto de Investigaciones en Geociencia, Minería y Química - Ingeominas",

        "Instituto Colombiano de Geología y Minería - INGEOMINAS",

    )

    return text

def overlay_replacement(article, repl):

    """Replace article HTML body with later decree text, preserving figures already in HTML if any."""

    raw = repl["text"]

    lines = [(article["page"], ln) for ln in raw.splitlines()]

    body = lines_to_html(article["id"], lines, {})

    src = repl["source"]

    note = (

        f'<p class="mod-note">Texto vigente según modificatorio <strong>{html.escape(src)}</strong> '

        f"(se aplica el acto más reciente sobre esta unidad).</p>"

    )

    return note + body, src

def chapter_name(letter, chap_id):

    if chap_id == "A-4" or str(chap_id).startswith("A-4"):
        return "Apéndice A-4 — Valores de Aa, Av, Ae y Ad (Supía)"

    names = CHAPTER_NAMES.get(letter, [])

    # chap_id like A.1 or F.2.1

    bits = chap_id.split(".", 1)
    if len(bits) < 2:
        return chap_id
    rest = bits[1]

    # map F.2.1 -> special index

    if letter == "F":

        fmap = {"1": 0, "2.1": 1, "2.2": 2, "3": 3, "4.1": 4, "4.2": 5, "4.3": 6, "5": 7}

        idx = fmap.get(rest)

        if idx is not None and idx < len(names):

            return names[idx]

    try:

        n = int(rest.split(".")[0])

        if 1 <= n <= len(names):

            return names[n - 1]

    except ValueError:

        pass

    return ""

def dump_js(obj, path: Path):

    path.parent.mkdir(parents=True, exist_ok=True)

    # compact json as JS assignment

    letter = obj["letter"]

    payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    path.write_text(f"window.NSR_TITLES=window.NSR_TITLES||{{}};\nwindow.NSR_TITLES[{json.dumps(letter)}]={payload};\n", encoding="utf-8")


def fold_search(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").casefold())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def html_to_search_text(raw: str) -> str:
    t = re.sub(r"<[^>]+>", " ", raw or "")
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def search_record(art: dict, letter: str, chap: str) -> dict:
    blob = " ".join(
        [
            art.get("id") or "",
            art.get("title") or "",
            html_to_search_text(art.get("html") or ""),
        ]
    )
    folded = fold_search(blob)
    if len(folded) > 2800:
        folded = folded[:2800]
    return {
        "id": art["id"],
        "title": art.get("title") or "",
        "letter": letter,
        "chap": chap,
        "page": art.get("page") or 1,
        "t": folded,
    }

def main():

    raw = extract_all()

    raw = apply_global_fixes(raw)

    print("Parsing articles")

    articles = parse_articles(raw)

    print("  articles", len(articles))

    replacements = {}

    for mid, year, pdf in MOD_SPECS:

        p = EXTRACTED / f"mod-{mid}.txt"

        if not p.exists():

            continue

        print("Parsing replacements", mid)

        found = annexes.parse_patches(p.read_text(encoding="utf-8", errors="replace"), mid)

        print("  ", len(found), "units")

        replacements.update(found)  # later decrees override

    TABLES = nsr_render.extract_pdf_tables(
        ROOT / "NSR10-Completa.pdf",
        EXTRACTED / "tables.json",
    )
    print("  tables", len(TABLES))
    print("Extracting nomenclature / notation lists\u2026")
    NOM = nomenclature.load_or_extract(
        ROOT / "NSR10-Completa.pdf",
        EXTRACTED / "nomenclature.json",
    )
    print("  notation articles", sum(1 for v in NOM.values() if v.get("entries")), "entries", sum(len(v.get("entries") or []) for v in NOM.values()))
    print("Extracting definition glossaries\u2026")
    DEFS = definitions.load_or_extract(
        ROOT / "NSR10-Completa.pdf",
        EXTRACTED / "definitions.json",
    )
    print(
        "  glossary articles",
        sum(1 for v in DEFS.values() if v.get("entries")),
        "entries",
        sum(len(v.get("entries") or []) for v in DEFS.values()),
    )
    TOUCHED = nsr_render.collect_touched_ids(EXTRACTED)
    print("  touched", len(TOUCHED))
    by_title = defaultdict(lambda: defaultdict(list))

    index = []

    for art in articles:

        letter = art["id"][0]

        chap = chapter_of(art["id"])

        src = "nsrbase"
        body = nsr_render.lines_to_html(art["id"], art["lines"], replacements, tables=TABLES)
        if art["id"] in replacements:
            body, src = nsr_render.overlay_replacement(art, replacements[art["id"]], tables=TABLES)
        nom_html = nomenclature.html_for(art["id"], NOM)
        if nom_html and nomenclature.is_notation_title(art.get("title") or ""):
            body = nom_html
        def_html = definitions.html_for(art["id"], DEFS)
        if def_html and definitions.is_definitions_title(art.get("title") or ""):
            body = def_html
            art["title"] = definitions.short_title(art.get("title") or "")
        mod_src = nsr_render.article_is_modified(art["id"], replacements, TOUCHED)
        if mod_src:
            if src == "nsrbase":
                src = mod_src
            body = '<div class="txt-modificado">' + body + "</div>"
        meta = replacements.get(art["id"], {})
        rec = {
            "id": art["id"],
            "title": art["title"],
            "page": art["page"],
            "source": src,
            "modified": bool(mod_src),
            "modFile": meta.get("file") or (annexes.DOC_META.get(src) or {}).get("file", ""),
            "modPage": meta.get("page", 1),
            "html": body,
        }

        by_title[letter][chap].append(rec)

        index.append({"id": art["id"], "title": art["title"], "page": art["page"], "chap": chap, "letter": letter})

    annexes.apply_injections(by_title)
    extras = annexes.build_extra_titles(EXTRACTED, nsr_render.lines_to_html, TABLES)
    print("  extras", [e["letter"] for e in extras], "arts", sum(len(c["articles"]) for e in extras for c in e["chapters"]))
    OUT_DIR.mkdir(exist_ok=True)

    titles_meta = []
    search_recs = []

    for letter in "ABCDEFGHIJK":

        chmap = by_title[letter]

        chapters = []

        # stable order

        def chap_key(c):

            parts = c.split(".")

            nums = []

            for p in parts[1:]:

                try:

                    nums.append(int(p))

                except ValueError:

                    nums.append(0)

            return tuple(nums)

        for chap_id in sorted(chmap.keys(), key=chap_key):

            arts = chmap[chap_id]

            page = arts[0]["page"] if arts else 1

            chapters.append(

                {

                    "id": chap_id,

                    "name": chapter_name(letter, chap_id),

                    "page": page,

                    "articles": arts,

                }

            )

        obj = {

            "letter": letter,

            "name": {

                "A": "Requisitos generales de diseño y construcción sismo resistente",

                "B": "Cargas",

                "C": "Concreto estructural",

                "D": "Mampostería estructural",

                "E": "Casas de uno y dos pisos",

                "F": "Estructuras metálicas",

                "G": "Estructuras de madera y estructuras de guadua",

                "H": "Estudios geotécnicos",

                "I": "Supervisión técnica",

                "J": "Requisitos de protección contra incendios en edificaciones",

                "K": "Requisitos complementarios",

            }[letter],

            "chapters": chapters,

        }

        dump_js(obj, OUT_DIR / f"titulo-{letter}.js")
        titles_meta.append(
            {
                "letter": letter,
                "name": obj["name"],
                "chapters": [{"id": c["id"], "name": c["name"], "page": c["page"], "n": len(c["articles"])} for c in chapters],
            }
        )
        for c in chapters:
            for art in c["articles"]:
                search_recs.append(search_record(art, letter, c["id"]))
        print("Wrote", letter, "chapters", len(chapters), "articles", sum(len(c["articles"]) for c in chapters))

    for extra in extras:
        dump_js(extra, OUT_DIR / f"titulo-{extra['letter']}.js")
        titles_meta.append(
            {
                "letter": extra["letter"],
                "name": extra["name"],
                "chapters": [
                    {"id": c["id"], "name": c["name"], "page": c["page"], "n": len(c["articles"])}
                    for c in extra["chapters"]
                ],
            }
        )
        for c in extra["chapters"]:
            for art in c["articles"]:
                search_recs.append(search_record(art, extra["letter"], c["id"]))
        print(
            "Wrote",
            extra["letter"],
            "chapters",
            len(extra["chapters"]),
            "articles",
            sum(len(c["articles"]) for c in extra["chapters"]),
        )

    (OUT_DIR / "indice.js").write_text(

        "window.NSR_INDEX=" + json.dumps(titles_meta, ensure_ascii=False, separators=(",", ":")) + ";\n",

        encoding="utf-8",

    )
    (OUT_DIR / "busqueda.js").write_text(
        "window.NSR_SEARCH=" + json.dumps(search_recs, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print("  search index", len(search_recs))

    print("Done. replacements applied", len(replacements))

if __name__ == "__main__":

    main()

