# -*- coding: utf-8 -*-
"""Rebuild NSR-10 definition glossaries from PDF glyph positions."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import nomenclature as nom

DASH_RE = re.compile(r"[\u2014\u2013\u2212]")
LOOSE_HEAD = re.compile(
    r"^([A-K])\s*[.\-]\s*(\d+(?:\s*[.\-]\s*\d+){0,8})\s*[\u2014\u2013\-\u2212]+\s*(.*)$"
)
INTRO_TITLE = re.compile(
    r"^(LAS SIGUIENTES DEFINICIONES|LAS DEFINICIONES QUE SE DAN)\b",
    re.I,
)
GLOSSARY_TITLE = re.compile(
    r"^DEFINICIONES(\b|$|[\s\u2014\u2013\u2212\-]| Y )",
    re.I,
)
SKIP_GLOSSARY = re.compile(
    r"^DEFINICIONES DE LOS PAR[A\u00c1]METROS",
    re.I,
)


def is_definitions_title(title: str) -> bool:
    t = (title or "").strip()
    if not t:
        return False
    if SKIP_GLOSSARY.search(t):
        return False
    if INTRO_TITLE.search(t):
        return True
    return bool(GLOSSARY_TITLE.search(t))


def short_title(title: str) -> str:
    t = (title or "").strip()
    m = re.match(
        r"(DEFINICIONES(?:\s+Y\s+[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1]+)?)",
        t,
        re.I,
    )
    if m:
        return m.group(1)
    return t


def _heading_id(row):
    head = nom._heading_id(row)
    if head:
        return head
    if max((s["sz"] for s in row["spans"]), default=0) < 9.8:
        return None
    txt = re.sub(r"\s+", " ", nom._row_text(row)).strip()
    m = LOOSE_HEAD.match(txt)
    if not m:
        return None
    title = (m.group(3) or "").strip(" \u2014\u2013-")
    letters = re.sub(
        r"[^A-Za-z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]",
        "",
        title,
    )
    if len(letters) < 4:
        return None
    nums = re.sub(r"\s+", "", m.group(2)).replace("-", ".")
    return m.group(1) + "." + nums, title


def _is_term_font(font: str, flags: int) -> bool:
    f = (font or "").lower()
    if "bolditalic" in f or "bold-italic" in f:
        return True
    if "bold" in f and "italic" in f:
        return True
    return bool((flags & 16) and (flags & 2))
    f = (font or "").lower()
    if "bolditalic" in f or "bold-italic" in f:
        return True
    if "bold" in f and "italic" in f:
        return True
    return bool((flags & 16) and (flags & 2))


def _is_new_term(row) -> bool:
    spans = [s for s in row["spans"] if (s.get("t") or "").strip()]
    if not spans:
        return False
    first = min(spans, key=lambda s: s["x"])
    if first["x"] > 58:
        return False
    if first["sz"] > 10.8:
        return False
    txt = nom._row_text(row)
    if txt.startswith("NSR-10"):
        return False
    if _heading_id(row):
        return False
    if _is_term_font(first["font"], first["flags"]):
        return True
    font = (first["font"] or "").lower()
    if "bold" in font and first["sz"] <= 10.6 and DASH_RE.search(txt):
        return True
    return False


def _split_dash(spans):
    term = []
    body = []
    seen = False
    for sp in spans:
        t = sp["t"]
        if seen:
            body.append(sp)
            continue
        m = DASH_RE.search(t)
        if m:
            before = t[: m.start()]
            after = t[m.end() :]
            if before.strip():
                term.append(dict(sp, t=before))
            seen = True
            if after.strip():
                body.append(dict(sp, t=after.lstrip(" \t-")))
            continue
        term.append(sp)
    return term, body, seen


def _term_html(spans) -> str:
    parts = []
    i = 0
    n = len(spans)
    while i < n:
        sp = spans[i]
        if nom._is_math_font(sp["font"]) and "arial" not in (sp["font"] or "").lower():
            group = [sp]
            j = i + 1
            while (
                j < n
                and nom._is_math_font(spans[j]["font"])
                and "arial" not in (spans[j]["font"] or "").lower()
                and spans[j]["x"] - group[-1]["x1"] < 16
            ):
                group.append(spans[j])
                j += 1
            parts.append(nom._symbol_math(group))
            i = j
            continue
        parts.append(html.escape(sp["t"]))
        i += 1
    txt = re.sub(r"\s+", " ", "".join(parts)).strip(" ,;")
    txt = re.sub(r"([^\s>(])\(", r"\1 (", txt)
    return txt


def _body_html(spans) -> str:
    txt = nom._def_html(spans)
    txt = txt.lstrip(" \t-").strip()
    return txt


def extract_pdf_lists(pdf_path: Path) -> dict:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    articles = {}
    current_id = None
    current_title = ""
    collecting = False
    pending = None

    def rec_of(art_id, page_no=None):
        rec = articles.setdefault(
            art_id, {"title": current_title, "page": page_no, "intro": [], "entries": []}
        )
        if rec["page"] is None and page_no:
            rec["page"] = page_no
        if current_title and not rec.get("title"):
            rec["title"] = current_title
        return rec

    def flush():
        nonlocal pending
        if not pending or not current_id:
            pending = None
            return
        term = (pending.get("term") or "").strip()
        body = (pending.get("body") or "").strip()
        if term:
            rec = rec_of(current_id)
            rec["entries"].append({"term": term, "def": body})
        pending = None

    def start_article(art_id, title, page_no):
        nonlocal current_id, current_title, collecting, pending
        flush()
        current_id = art_id
        current_title = title
        collecting = is_definitions_title(title)
        pending = None
        if collecting:
            rec = rec_of(art_id, page_no)
            if INTRO_TITLE.search(title):
                rec["intro"].append(title.rstrip(":").strip())
            else:
                m = re.match(
                    r"DEFINICIONES(?:\s+Y\s+[^\u2014\u2013\u2212\-]+)?\s*[\u2014\u2013\u2212\-]+\s*(.*)$",
                    title,
                    re.I,
                )
                if m and m.group(1).strip():
                    rec["intro"].append(m.group(1).strip())

    for i, page in enumerate(doc, 1):
        rows = nom._rows(nom._iter_spans(page))
        for row in rows:
            txt = nom._row_text(row)
            head = _heading_id(row)
            if head:
                art_id, title = head
                if nom.FIG_OR_TAB.match(title or ""):
                    flush()
                    collecting = False
                    continue
                start_article(art_id, title, i)
                continue
            if not collecting or not current_id:
                continue
            if nom.FIG_OR_TAB.match(txt):
                flush()
                collecting = False
                continue
            if _is_new_term(row):
                term_spans, body_spans, seen = _split_dash(row["spans"])
                flush()
                pending = {
                    "term": _term_html(term_spans),
                    "body": _body_html(body_spans) if seen else "",
                    "open": not seen,
                }
                continue
            if pending is None:
                if txt and len(txt) > 20:
                    rec = rec_of(current_id, i)
                    if not rec["entries"]:
                        rec["intro"].append(txt)
                continue
            if pending.get("open"):
                term_spans, body_spans, seen = _split_dash(row["spans"])
                more_term = _term_html(term_spans)
                if more_term:
                    pending["term"] = (pending["term"] + " " + more_term).strip()
                if seen:
                    pending["body"] = _body_html(body_spans)
                    pending["open"] = False
                continue
            more = _body_html(row["spans"])
            if more:
                pending["body"] = (pending["body"] + " " + more).strip()
        if not collecting:
            flush()
            pending = None
    flush()
    return articles


def entries_html(rec: dict) -> str:
    parts = []
    intro = " ".join(
        re.sub(r"\s+", " ", x or "").strip() for x in (rec.get("intro") or [])
    ).strip()
    intro = re.sub(r"\s+", " ", intro)
    if intro:
        parts.append(f"<p>{html.escape(intro)}</p>")
    if not rec.get("entries"):
        return "\n".join(parts)
    parts.append('<div class="def-list">')
    for ent in rec["entries"]:
        term = ent.get("term") or ""
        body = ent.get("def") or ""
        if not term:
            continue
        line = f'<p class="def-item"><span class="def-term">{term}</span>'
        if body:
            line += f" \u2014 {body}"
        line += "</p>"
        parts.append(line)
    parts.append("</div>")
    return "\n".join(parts)


def load_or_extract(pdf_path: Path, cache_path: Path, force: bool = False) -> dict:
    if cache_path.exists() and cache_path.stat().st_size > 200 and not force:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    articles = extract_pdf_lists(pdf_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")
    return articles


def html_for(art_id: str, catalog: dict) -> str:
    rec = catalog.get(art_id)
    if not rec:
        return ""
    if not rec.get("entries") and not rec.get("intro"):
        return ""
    if not rec.get("entries"):
        return ""
    return entries_html(rec)
