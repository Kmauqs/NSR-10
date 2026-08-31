# -*- coding: utf-8 -*-
"""HTML rendering: tables from PDF layout, equations without OCR junk, modified-text flags."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from eq_mathml import fallback_eq, mathml_for

PDF_BASE = "NSR10-Completa.pdf"
HEADING_RE = re.compile(
    r"^([A-K])\.(\d+(?:\.\d+){0,8})\s*(?:[\u2014\u2013\-\u2212]+\s*|\s{2,})(.*)$"
)
EQ_LABEL_RE = re.compile(r"\(([A-K]\.\d+(?:\.\d+)?-\d+)\)")
FIG_RE = re.compile(
    r"^(?:Figura|FIGURA)\s+([A-K]\.[\d.\-]+)\s*[\u2014\u2013\-\u2212]*\s*(.*)$",
    re.I,
)
TAB_RE = re.compile(
    r"^(?:Tabla|TABLA)\s+([A-K]\.[\d.\-]+\s*-?\s*\d+)\s*(?:\((?:continuaci[\u00f3o]n)\))?\s*[\u2014\u2013\-\u2212]*\s*(.*)$",
    re.I,
)
CHAP_RE = re.compile(r"^CAP[I\u00cd]TULO\s+([A-K])\.(\d+(?:\.\d+)?)\b", re.I)
SPANISH = re.compile(
    r"\b(para|donde|cuando|debe|deben|segun|seg\u00fan|el|la|los|las|en|se|con|por|"
    r"del|que|una|unos|como|este|esta|estos|estas|calculado|obtiene|define)\b",
    re.I,
)
ART_ID_RE = re.compile(r"\b([A-K]\.\d+(?:\.\d+){1,6})\b")
STOP_WORDS = {
    "tabla",
    "figura",
    "capitulo",
    "cap\u00edtulo",
    "titulo",
    "t\u00edtulo",
    "nsr-10",
}


def norm_table_id(raw: str) -> str:
    s = re.sub(r"\s+", "", raw)
    s = s.replace("--", "-").replace("\u2013", "-").replace("\u2014", "-")
    return s


def is_eq_junk(s: str) -> bool:
    t = s.strip()
    if not t:
        return False
    if FIG_RE.match(t) or TAB_RE.match(t) or HEADING_RE.match(t):
        return False
    if SPANISH.search(t) and not EQ_LABEL_RE.search(t):
        return False
    tokens = t.split()
    if EQ_LABEL_RE.search(t):
        # line is the formula + number
        if len(t) < 120 and not SPANISH.search(t):
            return True
    if 1 <= len(tokens) <= 28:
        short = 0
        for tok in tokens:
            core = re.sub(r"[^A-Za-z0-9.]", "", tok)
            if len(core) <= 4:
                short += 1
        if short / max(len(tokens), 1) >= 0.72 and not SPANISH.search(t):
            return True
    # stacked OCR fragments
    if re.fullmatch(r"[A-Za-z0-9()=+\-.,/\s]{1,40}", t) and not SPANISH.search(t):
        if len(tokens) <= 8 and any(ch in t for ch in "=+"):
            return True
        if len(t) <= 12 and t.isascii():
            return True
    return False


def figure_html(fig_id, caption, page):
    cap = html.escape((caption or "").strip(" -\u2014\u2013"))
    href = f"{PDF_BASE}#page={page}"
    extra = f" \u2014 {cap}" if cap and not cap.lower().startswith("y el") else ""
    if extra and SPANISH.match(cap.split()[0] if cap else ""):
        # wrapped sentence, not a caption
        extra = ""
    return (
        f'<figure class="nsr-fig"><figcaption>'
        f'<a href="{href}" target="_blank" rel="noopener">Figura {html.escape(fig_id)}</a>'
        f"{extra}"
        f" <span class='muted'>(PDF p\u00e1g. {page})</span>"
        f"</figcaption></figure>"
    )


def cells_to_html(tid, caption, matrix, page=None):
    rows = []
    for row in matrix:
        cleaned = [("" if c is None else re.sub(r"\s+", " ", str(c)).strip()) for c in row]
        if any(cleaned):
            rows.append(cleaned)
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    for r in rows:
        while len(r) < ncol:
            r.append("")
    # drop equation-shaped "tables"
    blob = " ".join(c for r in rows for c in r)
    if ncol <= 2 and len(rows) <= 2 and EQ_LABEL_RE.search(blob):
        return ""
    if ncol <= 2 and len(rows) <= 2 and re.search(r"[=\u2211]", blob) and "Tabla" not in blob:
        return ""
    head = "".join(f"<th>{html.escape(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:]
    )
    cap = html.escape(caption or "")
    pdf = (
        f' <a href="{PDF_BASE}#page={page}" target="_blank" rel="noopener">PDF p\u00e1g. {page}</a>'
        if page
        else ""
    )
    return (
        f'<div class="nsr-table-wrap"><p class="table-cap">Tabla {html.escape(tid)}'
        f"{(' \u2014 ' + cap) if cap else ''}{pdf}</p>"
        f"<table class='nsr-table'><thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )


def extract_pdf_tables(pdf_path: Path, cache_path: Path | None = None) -> dict:
    if cache_path and cache_path.exists() and cache_path.stat().st_size > 100:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    import pymupdf

    doc = pymupdf.open(pdf_path)
    catalog = {}
    id_re = re.compile(r"^[A-K]\.[\d.\-]+\d$|^[A-K]\.\d")
    for i, page in enumerate(doc, 1):
        words = page.get_text("words") or []
        captions = []
        for wi, w in enumerate(words):
            if w[4].lower() not in ("tabla", "table"):
                continue
            nxt = words[wi + 1][4] if wi + 1 < len(words) else ""
            nxt2 = words[wi + 2][4] if wi + 2 < len(words) else ""
            cand = nxt
            if nxt2.startswith("-") or re.match(r"^\d+$", nxt2):
                cand = nxt + nxt2
            tid = norm_table_id(cand)
            if not re.match(r"^[A-K]\.", tid):
                continue
            captions.append((tid, w[1], w[3]))
        try:
            found = page.find_tables()
            tables = list(found.tables) if found and found.tables else []
        except Exception:
            tables = []
        assigned = set()
        for tid, y0, y1 in captions:
            clip_top = y0 - 2
            clip_bot = y0 + 420
            # next caption limits the clip
            later = [c[1] for c in captions if c[1] > y0 + 8]
            if later:
                clip_bot = min(clip_bot, min(later) - 4)
            matrix = None
            for tb in tables:
                bb = tb.bbox
                mid_y = (bb[1] + bb[3]) / 2
                if clip_top - 20 <= bb[1] <= clip_bot and mid_y <= clip_bot + 40:
                    try:
                        matrix = tb.extract()
                    except Exception:
                        matrix = None
                    if matrix and len(matrix) >= 2:
                        break
                    matrix = None
            if matrix is None:
                matrix = cluster_words_table(page, clip=(0, clip_top, page.rect.width, clip_bot))
            if not matrix:
                continue
            html_tbl = cells_to_html(tid, "", matrix, i)
            if not html_tbl:
                continue
            prev = catalog.get(tid)
            if prev and prev.get("html", "").count("<tr>") >= html_tbl.count("<tr>"):
                continue
            catalog[tid] = {"html": html_tbl, "page": i, "rows": len(matrix)}
            assigned.add(tid)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return catalog


def cluster_words_table(page, y_tol=5.0, clip=None):
    words = page.get_text("words") or []
    if clip:
        x0c, y0c, x1c, y1c = clip
        words = [w for w in words if y0c <= w[1] <= y1c and x0c <= w[0] <= x1c]
    # drop running header fragments
    skip = re.compile(r"^(NSR-10|Cap[i\u00ed]tulo|T[i\u00cd]tulo|A-\d+|B-\d+|C-\d+)$", re.I)
    words = [w for w in words if not skip.match(w[4].strip())]
    if len(words) < 6:
        return None
    rows_map = []
    for x0, y0, x1, y1, w, *_ in sorted(words, key=lambda t: (round(t[1], 1), t[0])):
        if not w.strip():
            continue
        placed = False
        for row in rows_map:
            if abs(row["y"] - y0) <= y_tol:
                row["cells"].append((x0, w))
                placed = True
                break
        if not placed:
            rows_map.append({"y": y0, "cells": [(x0, w)]})
    if len(rows_map) < 2:
        return None
    xs = sorted({round(x / 8.0) * 8 for row in rows_map for x, _ in row["cells"]})
    if len(xs) < 2:
        return None
    cols = []
    for x in xs:
        if not cols or x - cols[-1] > 36:
            cols.append(x)
    if len(cols) < 2:
        return None
    matrix = []
    for row in rows_map:
        cells = [""] * len(cols)
        for x, w in row["cells"]:
            idx = min(range(len(cols)), key=lambda k: abs(x - cols[k]))
            cells[idx] = (cells[idx] + " " + w).strip()
        matrix.append(cells)
    if not any(sum(1 for c in r if c) >= 2 for r in matrix):
        return None
    # drop title row that is only "Tabla ..."
    if matrix and re.match(r"^Tabla\b", matrix[0][0] or "", re.I):
        matrix = matrix[1:]
    return matrix


def collect_touched_ids(extracted_dir: Path) -> dict:
    """article_id -> latest source id, only when the decree actually amends that unit."""
    touched = {}
    order = ["d092", "d340draft", "d340", "d945", "d2113", "borrador", "d1711", "d1401", "d1580"]
    cue = re.compile(
        r"quedar|modific|substit|sustitu|reemplaz|agreg|adicion|correg|anex|"
        r"debe quedar|se cambia|en vez de|en lugar de",
        re.I,
    )
    for mid in order:
        p = extracted_dir / f"mod-{mid}.txt"
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if not cue.search(line):
                continue
            window = " ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])
            for m in ART_ID_RE.finditer(window):
                touched[m.group(1)] = mid
    return touched


def article_is_modified(art_id: str, replacements: dict, touched: dict) -> str | None:
    if art_id in replacements:
        return replacements[art_id]["source"]
    if art_id in touched:
        return touched[art_id]
    parent = art_id
    while "." in parent:
        parent = parent.rsplit(".", 1)[0]
        if parent in replacements:
            return replacements[parent]["source"]
    return None


def lines_to_html(art_id, lines, replacements, tables=None):
    tables = tables or {}
    used_eq = set()
    html_parts = []
    i = 0
    n = len(lines)

    def flush_para(buf):
        if not buf:
            return
        kept = [x for x in buf if not is_eq_junk(x)]
        buf.clear()
        if not kept:
            return
        txt = " ".join(kept)
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            return
        html_parts.append(f"<p>{format_inline(txt, used_eq)}</p>")

    paras = []
    while i < n:
        page, line = lines[i]
        s = (line or "").strip()
        fm = FIG_RE.match(s)
        tm = TAB_RE.match(s)
        if fm:
            flush_para(paras)
            cap = fm.group(2) or ""
            html_parts.append(figure_html(fm.group(1), cap, page))
            i += 1
            continue
        if tm:
            flush_para(paras)
            cap_id = norm_table_id(tm.group(1))
            caption = (tm.group(2) or "").strip()
            j = i + 1
            while j < n:
                pl = (lines[j][1] or "").strip()
                if HEADING_RE.match(pl) or FIG_RE.match(pl) or TAB_RE.match(pl) or CHAP_RE.match(pl):
                    break
                if j - i > 60:
                    break
                j += 1
            rec = tables.get(cap_id)
            if rec:
                html_parts.append(rec["html"])
            else:
                html_parts.append(
                    f'<div class="nsr-table-wrap"><p class="table-cap">Tabla {html.escape(cap_id)}'
                    f"{(' \u2014 ' + html.escape(caption)) if caption else ''}"
                    f' \u2014 <a href="{PDF_BASE}#page={page}" target="_blank" rel="noopener">'
                    f"ver tabla en PDF p\u00e1g. {page}</a></p></div>"
                )
            i = j
            continue
        if is_eq_junk(s):
            eqm = EQ_LABEL_RE.search(s)
            if eqm:
                flush_para(paras)
                eid = eqm.group(1)
                if eid not in used_eq:
                    used_eq.add(eid)
                    html_parts.append(mathml_for(eid) or fallback_eq(eid))
            i += 1
            continue
        eqm = EQ_LABEL_RE.search(s)
        if eqm and not SPANISH.search(s):
            flush_para(paras)
            eid = eqm.group(1)
            if eid not in used_eq:
                used_eq.add(eid)
                html_parts.append(mathml_for(eid) or fallback_eq(eid))
            i += 1
            continue
        if not s:
            flush_para(paras)
            i += 1
            continue
        paras.append(s)
        i += 1
    flush_para(paras)
    return "\n".join(html_parts)


def format_inline(txt, used_eq):
    txt = html.escape(txt)
    txt = re.sub(r"\(([a-z])\)\s", r"<br><strong>(\1)</strong> ", txt)

    def eq_sub(m):
        eid = m.group(1)
        return f'(<a href="#eq-{html.escape(eid)}">{html.escape(eid)}</a>)'

    return EQ_LABEL_RE.sub(eq_sub, txt)


def overlay_replacement(article, repl, tables=None):
    raw = repl["text"]
    lines = [(article["page"], ln) for ln in raw.splitlines()]
    body = lines_to_html(article["id"], lines, {}, tables=tables)
    src = repl["source"]
    note = (
        f'<p class="mod-note">Texto vigente seg\u00fan modificatorio <strong>{html.escape(src)}</strong> '
        f"(se aplica el acto m\u00e1s reciente sobre esta unidad).</p>"
    )
    return note + body, src
