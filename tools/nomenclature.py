# -*- coding: utf-8 -*-
"""Rebuild NSR-10 nomenclature / notation lists from PDF glyph positions."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ART_HEAD = re.compile(
    r"^([A-K])([.\-])(\d+(?:[.\-]\d+){0,8})\s*[\u2014\u2013\-\u2212]+\s*(.*)$"
)
NOTATION_LINE = re.compile(r"^Notaci[o\u00f3]n\s*:?\s*$", re.I)
SKIP_TITLE = re.compile(
    r"TEMPLE|CONVENCI[O\u00d3]N DE SIGNOS|PARA CONEXIONES|SECCI[O\u00d3]N MONOSIM|"
    r"SIMETR[I\u00cd]A OBLICUA|SECCI[O\u00d3]N ASIM[E\u00c9]TRICA",
    re.I,
)
FIG_OR_TAB = re.compile(r"^(?:Figura|FIGURA|Tabla|TABLA)\b", re.I)

# MT Extra "A" is the script ell used for wall length l_wi.
EXTRA_MAP = {"A": "\u2113", "a": "\u2113"}


def is_notation_title(title: str) -> bool:
    t = (title or "").strip()
    if not t or SKIP_TITLE.search(t):
        return False
    u = t.upper()
    if "NOMENCLATURA" in u:
        if "DEFINICIONES" in u:
            return False
        return True
    if u.startswith("NOTACI") or "NOTACI\u00d3N" in u or "NOTACION" in u:
        if "DEFINICIONES" in u and "NOTACI" in u:
            return False
        return True
    return False


def _font_kind(font: str) -> str:
    f = (font or "").lower()
    if "extra" in f:
        return "extra"
    if "symbol" in f:
        return "symbol"
    if "times" in f or "cambria" in f or "stix" in f:
        return "times"
    return "text"


def _is_math_font(font: str) -> bool:
    return _font_kind(font) in ("extra", "symbol", "times")


def _map_text(font: str, text: str) -> str:
    kind = _font_kind(font)
    if kind == "extra":
        return "".join(EXTRA_MAP.get(ch, ch) for ch in text)
    return text


def _iter_spans(page):
    data = page.get_text("dict") or {}
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                raw = sp.get("text") or ""
                if not raw.strip():
                    continue
                x0, y0, x1, y1 = sp["bbox"]
                if y0 < 36 or y0 > 748:
                    continue
                yield {
                    "t": raw,
                    "x": x0,
                    "y": y0,
                    "x1": x1,
                    "y1": y1,
                    "sz": float(sp.get("size") or 10),
                    "font": sp.get("font") or "",
                    "flags": int(sp.get("flags") or 0),
                }


def _rows(spans, tol=4.8):
    rows = []
    for sp in sorted(spans, key=lambda s: (round(s["y1"], 1), s["x"])):
        placed = False
        for row in rows:
            if abs(row["base"] - sp["y1"]) <= tol:
                row["spans"].append(sp)
                row["base"] = min(row["base"], sp["y1"])
                row["y"] = min(row["y"], sp["y"])
                placed = True
                break
        if not placed:
            rows.append({"y": sp["y"], "base": sp["y1"], "spans": [sp]})
    rows.sort(key=lambda r: r["y"])
    for row in rows:
        row["spans"].sort(key=lambda s: s["x"])
    return rows


def _row_text(row):
    return " ".join(s["t"].strip() for s in row["spans"] if (s["t"] or "").strip())


def _heading_id(row):
    if max((s["sz"] for s in row["spans"]), default=0) < 9.8:
        return None
    txt = re.sub(r"\s+", " ", _row_text(row))
    m = ART_HEAD.match(txt)
    if not m:
        return None
    title = (m.group(4) or "").strip(" \u2014\u2013-")
    letters = re.sub(r"[^A-Za-z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]", "", title)
    if len(letters) < 4:
        return None
    art_id = m.group(1) + "." + m.group(3).replace("-", ".")
    return art_id, title


def _find_sep(row):
    """Return (index, span) of a nomenclature '=' or ':' separator."""
    for i, sp in enumerate(row["spans"]):
        t = sp["t"].strip()
        if t not in ("=", ":") and not t.startswith("="):
            continue
        if sp["x"] < 52 or sp["x"] > 210:
            continue
        left = [s for s in row["spans"][:i] if s["x"] < sp["x"] - 1]
        if not left:
            continue
        if not any(_is_math_font(s["font"]) or len(s["t"].strip()) <= 4 for s in left):
            continue
        if min(s["x"] for s in left) > 110:
            continue
        return i, sp
    return None


def _mi(text, italic=True):
    esc = html.escape(text)
    var = "bold-italic" if italic else "bold"
    return f'<mi mathvariant="{var}">{esc}</mi>'


def _symbol_math(spans):
    parts = []
    buf = []
    for sp in spans:
        t = _map_text(sp["font"], sp["t"]).strip()
        if not t:
            continue
        if t in (",", ";", "/"):
            if buf:
                parts.append(_one_symbol(buf))
                buf = []
            parts.append(f"<mo>{html.escape(t)}</mo>")
            continue
        buf.append(sp)
    if buf:
        parts.append(_one_symbol(buf))
    if not parts:
        return ""
    inner = "".join(parts)
    if len(parts) > 1:
        inner = f"<mrow>{inner}</mrow>"
    return (
        f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">{inner}</math>'
    )


def _one_symbol(spans):
    spans = sorted(spans, key=lambda s: s["x"])
    base = spans[0]
    base_txt = _map_text(base["font"], base["t"]).strip()
    subs = []
    supers = []
    primes = 0
    for sp in spans[1:]:
        t = _map_text(sp["font"], sp["t"]).strip()
        if t in ("\u2032", "'", "\u00b4"):
            primes += max(t.count("\u2032"), 1)
            continue
        is_super = bool(sp["flags"] & 1) or (
            sp["y"] + 0.8 < base["y"] and sp["sz"] <= base["sz"]
        )
        is_sub = (sp["sz"] <= base["sz"] - 0.35) or (sp["y"] > base["y"] + 1.2)
        if is_super and not is_sub:
            supers.append(t)
        else:
            subs.append(t)
    node = _mi(base_txt, italic=True)
    if subs:
        node = f"<msub>{node}<mrow>{_mi(''.join(subs))}</mrow></msub>"
    if supers:
        node = f"<msup>{node}<mrow>{_mi(''.join(supers), italic=False)}</mrow></msup>"
    if primes:
        prime = "\u2032" * primes
        node = f"<msup>{node}<mo>{prime}</mo></msup>"
    return node


def _symbol_key(spans):
    bits = []
    buf = []
    for sp in spans:
        t = _map_text(sp["font"], sp["t"]).strip()
        if t in (",", ";"):
            if buf:
                bits.append(_key_one(buf))
                buf = []
            continue
        buf.append(sp)
    if buf:
        bits.append(_key_one(buf))
    return ",".join(bits)


def _key_one(spans):
    spans = sorted(spans, key=lambda s: s["x"])
    base = _map_text(spans[0]["font"], spans[0]["t"]).strip()
    sub = "".join(_map_text(s["font"], s["t"]).strip() for s in spans[1:] if s["t"].strip() not in ("\u2032", "'"))
    return f"{base}_{sub}" if sub else base


def _def_html(spans):
    out = []
    i = 0
    n = len(spans)
    while i < n:
        sp = spans[i]
        t = _map_text(sp["font"], sp["t"])
        if t.strip() in ("=", ":"):
            t = t.lstrip("=:").lstrip()
            if not t:
                i += 1
                continue
        if _is_math_font(sp["font"]) and t.strip():
            group = [sp]
            j = i + 1
            while j < n and _is_math_font(spans[j]["font"]) and spans[j]["x"] - group[-1]["x1"] < 14:
                if spans[j]["t"].strip() in (".", ",", ";", ":"):
                    break
                group.append(spans[j])
                j += 1
            out.append(_symbol_math(group))
            i = j
            continue
        nxt = spans[i + 1] if i + 1 < n else None
        if nxt and ((nxt["flags"] & 1) or nxt["sz"] <= 7.2) and not _is_math_font(nxt["font"]):
            base = html.escape(t.rstrip())
            sup = html.escape(_map_text(nxt["font"], nxt["t"]).strip())
            out.append(f"{base}<sup>{sup}</sup>")
            rest = ""
            i += 2
            continue
        out.append(html.escape(t))
        i += 1
    txt = "".join(out)
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = txt.lstrip("= ").strip()
    return txt


def _entry_from_row(row, sep_i, sep):
    left = [s for s in row["spans"][:sep_i] if s["x"] < sep["x"] - 0.5]
    right = row["spans"][sep_i:]
    if not left:
        return None
    return {
        "key": _symbol_key(left),
        "sym": _symbol_math(left),
        "def_spans": right,
        "y": row["y"],
    }


def extract_pdf_lists(pdf_path: Path) -> dict:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    articles = {}
    current_id = None
    current_title = ""
    collecting = False
    pending = None
    symbol_buf = []

    def rec_of(art_id, page_no=None):
        rec = articles.setdefault(
            art_id, {"title": current_title, "page": page_no, "intro": [], "entries": []}
        )
        if rec["page"] is None and page_no:
            rec["page"] = page_no
        return rec

    def flush_pending(into_id):
        nonlocal pending, symbol_buf
        if pending and into_id:
            defn = _def_html(pending["def_spans"])
            if defn:
                rec_of(into_id)["entries"].append(
                    {"key": pending["key"], "sym": pending["sym"], "def": defn}
                )
        pending = None

    def begin_entry(left_spans, right_spans, art_id, page_no):
        nonlocal pending
        flush_pending(art_id)
        if not left_spans or not art_id:
            return
        pending = {
            "key": _symbol_key(left_spans),
            "sym": _symbol_math(left_spans),
            "def_spans": list(right_spans),
            "y": left_spans[0]["y"],
        }
        rec_of(art_id, page_no)

    def start_article(art_id, title, page_no):
        nonlocal current_id, current_title, collecting, symbol_buf
        flush_pending(current_id)
        symbol_buf = []
        current_id = art_id
        current_title = title
        collecting = is_notation_title(title)
        if collecting:
            rec_of(art_id, page_no)

    for i, page in enumerate(doc, 1):
        rows = _rows(_iter_spans(page))
        for row in rows:
            txt = _row_text(row)
            head = _heading_id(row)
            if head:
                art_id, title = head
                if FIG_OR_TAB.match(title or ""):
                    flush_pending(current_id)
                    collecting = False
                    symbol_buf = []
                    continue
                start_article(art_id, title, i)
                continue
            if NOTATION_LINE.match(txt) and collecting:
                flush_pending(current_id)
                symbol_buf = []
                continue
            active = collecting
            sep = _find_sep(row) if active else None
            if sep:
                sep_i, sep_sp = sep
                left = [s for s in row["spans"][:sep_i] if s["x"] < sep_sp["x"] - 0.5]
                right = row["spans"][sep_i:]
                if not left and symbol_buf:
                    left = symbol_buf
                    symbol_buf = []
                begin_entry(left, right, current_id, i)
                continue
            if not active:
                continue
            math_left = [s for s in row["spans"] if _is_math_font(s["font"]) and s["x"] < 88]
            text_right = [
                s
                for s in row["spans"]
                if (not _is_math_font(s["font"])) and s["x"] >= 70 and s["t"].strip()
            ]
            long_text = "".join(s["t"] for s in text_right).strip()
            if math_left and len(long_text) < 12:
                if pending:
                    flush_pending(current_id)
                symbol_buf.extend(math_left)
                continue
            if pending:
                pending["def_spans"].extend(row["spans"])
                continue
            if symbol_buf and long_text:
                begin_entry(symbol_buf, row["spans"], current_id, i)
                symbol_buf = []
                continue
            if txt and not FIG_OR_TAB.match(txt) and len(txt) > 40 and current_id:
                rec = rec_of(current_id, i)
                if not rec["entries"] and not is_notation_title(txt):
                    rec["intro"].append(txt)
        flush_pending(current_id)
        if not collecting:
            symbol_buf = []
    flush_pending(current_id)
    return articles


def apply_known_patches(articles: dict) -> None:
    n_def = "n\u00famero de pisos de la edificaci\u00f3n por encima de la base."
    for art_id in ("A.4.0", "A.13.2"):
        rec = articles.get(art_id)
        if not rec:
            continue
        for ent in rec["entries"]:
            if ent.get("key") in ("N", "N_"):
                ent["def"] = n_def
    drop = {"A_B", "A_wi", "\u2113_wi", "h_n", "h_wi", "n_w"}
    rec = articles.get("A.4.0")
    if rec:
        rec["entries"] = [e for e in rec["entries"] if e.get("key") not in drop]


def entries_html(rec: dict) -> str:
    parts = []
    for intro in rec.get("intro") or []:
        if intro == "Notaci\u00f3n":
            parts.append('<p class="nom-kicker">Notaci\u00f3n</p>')
        else:
            parts.append(f"<p>{html.escape(intro)}</p>")
    if not rec.get("entries"):
        return "\n".join(parts)
    parts.append('<table class="nom-list">')
    for ent in rec["entries"]:
        parts.append(
            "<tr>"
            f'<td class="nom-sym">{ent["sym"]}</td>'
            '<td class="nom-eq">=</td>'
            f'<td class="nom-def">{ent["def"]}</td>'
            "</tr>"
        )
    parts.append("</table>")
    return "\n".join(parts)


def load_or_extract(pdf_path: Path, cache_path: Path, force: bool = False) -> dict:
    if cache_path.exists() and cache_path.stat().st_size > 200 and not force:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    articles = extract_pdf_lists(pdf_path)
    apply_known_patches(articles)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(articles, ensure_ascii=False), encoding="utf-8")
    return articles


def html_for(art_id: str, catalog: dict) -> str:
    rec = catalog.get(art_id)
    if not rec or not rec.get("entries"):
        return ""
    return entries_html(rec)
