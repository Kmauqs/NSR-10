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


_SLIVER = 12.0
_EDGE_TOL = 2.2
_LINE_TOL = 3.6
_NUM_TOKEN = re.compile(r"^[+\-]?\d+(?:[.,]\d+)?$")
_GRID_TITLE = re.compile(
    r"espesor|espesores|\bmm\b|\bcm\b|ancho|diametro|di\u00e1metro",
    re.I,
)


def _cluster_vals(vals, tol=_EDGE_TOL):
    if not vals:
        return []
    vals = sorted(vals)
    groups = [[vals[0]]]
    for v in vals[1:]:
        if v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def _collapse_edges(vals, gap=_SLIVER, keep="right"):
    if not vals:
        return []
    out = [vals[0]]
    for x in vals[1:]:
        if x - out[-1] < gap:
            if keep == "right":
                out[-1] = x
        else:
            out.append(x)
    return out


def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _nearest(vals, v):
    return min(vals, key=lambda x: abs(x - v))


def _col_of(x, xs):
    for i in range(len(xs) - 1):
        if xs[i] - 1.0 <= x < xs[i + 1] - 0.4:
            return i
    return max(0, len(xs) - 2)


def _major_x_edges(tb):
    xs = []
    for row in tb.rows:
        for c in row.cells:
            if c is None:
                continue
            if c[2] - c[0] < _SLIVER:
                continue
            xs.append(c[0])
            xs.append(c[2])
    raw = [_mean(g) for g in _cluster_vals(xs)]
    return _collapse_edges(raw, _SLIVER, "right")


def _major_y_edges(tb, xs):
    bbox = tb.bbox
    y_hits = {}
    all_y = []
    wide = []
    for row in tb.rows:
        for c in row.cells:
            if c is None or c[2] - c[0] < _SLIVER:
                continue
            wide.append(c)
            all_y.append(c[1])
            all_y.append(c[3])
    reps = [_mean(g) for g in _cluster_vals(all_y, 2.0)]
    if not reps:
        return [bbox[1], bbox[3]]
    for c in wide:
        ci = _col_of((c[0] + c[2]) / 2.0, xs)
        for y in (c[1], c[3]):
            yrep = _nearest(reps, y)
            y_hits.setdefault(yrep, set()).add(ci)
    kept = [bbox[1], bbox[3]]
    for y in reps:
        hits = y_hits.get(y, set())
        if 0 in hits or len(hits) >= 2:
            kept.append(y)
    kept = _collapse_edges(sorted(kept), 5.5, "right")
    if kept[0] > bbox[1] + 1:
        kept.insert(0, bbox[1])
    if kept[-1] < bbox[3] - 1:
        kept.append(bbox[3])
    return kept


def _covering_cell(tb, x, y):
    best = None
    best_area = -1.0
    for row in tb.rows:
        for c in row.cells:
            if c is None or c[2] - c[0] < _SLIVER:
                continue
            if c[0] - 1.8 <= x <= c[2] + 1.8 and c[1] - 1.8 <= y <= c[3] + 1.8:
                area = (c[2] - c[0]) * (c[3] - c[1])
                if area > best_area:
                    best = c
                    best_area = area
    return best


def _in_cell(c, x, y):
    if c is None:
        return False
    return c[0] - 1.8 <= x <= c[2] + 1.8 and c[1] - 1.8 <= y <= c[3] + 1.8


def _words_in_rect(words, x0, y0, x1, y1, pad=1.2):
    out = []
    for w in words:
        cx = (w[0] + w[2]) / 2.0
        cy = (w[1] + w[3]) / 2.0
        if x0 - pad <= cx <= x1 + pad and y0 - pad <= cy <= y1 + pad:
            out.append(w)
    return out


def _cluster_word_lines(words, y_tol=_LINE_TOL):
    lines = []
    for w in sorted(words, key=lambda t: (t[1], t[0])):
        if not str(w[4]).strip():
            continue
        if not lines or abs(w[1] - lines[-1]["y"]) > y_tol:
            lines.append({"y": w[1], "words": [w]})
        else:
            lines[-1]["words"].append(w)
            n = len(lines[-1]["words"])
            lines[-1]["y"] = (lines[-1]["y"] * (n - 1) + w[1]) / n
    return lines


def _join_line(words):
    parts = []
    for w in sorted(words, key=lambda t: t[0]):
        t = str(w[4])
        if parts and parts[-1].endswith("-") and t and t[0].islower():
            parts[-1] = parts[-1][:-1] + t
        else:
            parts.append(t)
    return " ".join(parts)


def _tidy_text(text):
    text = re.sub(r"-\n\s*", "", text or "")
    text = re.sub(r"m2\b", "m\u00b2", text)
    text = re.sub(r"m3\b", "m\u00b3", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _words_to_text(words):
    if not words:
        return ""
    lines = [_join_line(ln["words"]) for ln in _cluster_word_lines(words)]
    return _tidy_text("\n".join(lines))


def _is_number(text):
    t = (text or "").strip()
    return bool(_NUM_TOKEN.match(t))


def _parse_numeric_grid(words):
    lines = _cluster_word_lines(words)
    if len(lines) < 3:
        return None
    title = ""
    start = 0
    for i, ln in enumerate(lines):
        txt = _join_line(ln["words"])
        nums = [w for w in ln["words"] if _NUM_TOKEN.match(str(w[4]))]
        if _GRID_TITLE.search(txt) and len(nums) < 3:
            title = txt
            start = i + 1
            break
    header_i = None
    for i in range(start, len(lines)):
        nums = [w for w in lines[i]["words"] if _NUM_TOKEN.match(str(w[4]))]
        others = [w for w in lines[i]["words"] if not _NUM_TOKEN.match(str(w[4]))]
        if len(nums) >= 3 and not others:
            header_i = i
            break
    if header_i is None:
        return None
    headers_w = sorted(
        [w for w in lines[header_i]["words"] if _NUM_TOKEN.match(str(w[4]))],
        key=lambda t: t[0],
    )
    col_xs = [(w[0] + w[2]) / 2.0 for w in headers_w]
    headers = [str(w[4]) for w in headers_w]
    if len(col_xs) >= 2:
        gaps = [col_xs[i + 1] - col_xs[i] for i in range(len(col_xs) - 1)]
        tol = max(8.0, 0.45 * sorted(gaps)[len(gaps) // 2])
    else:
        tol = 18.0
    data = []
    row_ys = []
    for i in range(header_i + 1, len(lines)):
        nums = [w for w in lines[i]["words"] if _NUM_TOKEN.match(str(w[4]))]
        if not nums:
            continue
        row = [""] * len(col_xs)
        for w in nums:
            cx = (w[0] + w[2]) / 2.0
            j = min(range(len(col_xs)), key=lambda k: abs(cx - col_xs[k]))
            if abs(cx - col_xs[j]) <= tol:
                row[j] = str(w[4])
        if any(row):
            data.append(row)
            row_ys.append(lines[i]["y"])
    if len(data) < 1:
        return None
    return {
        "title": _tidy_text(title),
        "headers": headers,
        "rows": data,
        "row_ys": row_ys,
        "col_xs": col_xs,
    }


def _parse_labels(words, row_ys):
    title_parts = []
    labels = [""] * len(row_ys)
    for ln in _cluster_word_lines(words):
        txt = _tidy_text(_join_line(ln["words"]))
        if not txt:
            continue
        if row_ys:
            j = min(range(len(row_ys)), key=lambda k: abs(ln["y"] - row_ys[k]))
            if abs(ln["y"] - row_ys[j]) <= 6.5:
                labels[j] = txt
                continue
        title_parts.append(txt)
    return _tidy_text(" ".join(title_parts)), labels


def _frag(text):
    text = _tidy_text(text)
    if not text:
        return ""
    return "<br>".join(html.escape(ln) for ln in text.split("\n") if ln.strip())


def _subtable_html(title, labels, grids, alt_flags):
    n_rows = len(grids[0]["rows"])
    head1 = []
    head2 = []
    if title or any(labels):
        rs = 2 if any(g.get("headers") for g in grids) else 1
        head1.append(f'<th class="lbl" rowspan="{rs}">{html.escape(title)}</th>')
    for g, alt in zip(grids, alt_flags):
        cls = ' class="unit-alt"' if alt else ""
        n = len(g["headers"])
        cap = html.escape(g.get("title") or "")
        head1.append(f"<th{cls} colspan='{n}'>{cap}</th>")
        for h in g["headers"]:
            head2.append(f"<th{cls}>{html.escape(h)}</th>")
    body = []
    for i in range(n_rows):
        tds = []
        if title or any(labels):
            tds.append(f'<td class="lbl">{html.escape(labels[i] if i < len(labels) else "")}</td>')
        for g, alt in zip(grids, alt_flags):
            cls = ' class="unit-alt"' if alt else ""
            row = g["rows"][i] if i < len(g["rows"]) else [""] * len(g["headers"])
            for val in row:
                tds.append(f"<td{cls}>{html.escape(val)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (
        f'<table class="nsr-subtable"><thead><tr>{"".join(head1)}</tr>'
        f"<tr>{''.join(head2)}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def _td(tag, text, rowspan=1, colspan=1, classes=None, inner=None):
    cls = " ".join(c for c in (classes or []) if c)
    attrs = ""
    if rowspan > 1:
        attrs += f' rowspan="{rowspan}"'
    if colspan > 1:
        attrs += f' colspan="{colspan}"'
    if cls:
        attrs += f' class="{cls}"'
    if inner is not None:
        return f"<{tag}{attrs}>{inner}</{tag}>"
    return f"<{tag}{attrs}>{_frag(text)}</{tag}>"


def _looks_like_occ(text, col, colspan):
    if col != 0 or colspan != 1:
        return False
    t = re.sub(r"\s+", " ", text or "").strip()
    if not t or _is_number(t) or ":" in t:
        return False
    words = t.split()
    if len(words) > 3 or len(t) > 28:
        return False
    if any(ch.isdigit() for ch in t):
        return False
    return True


def _table_is_junk(blob, ncols, nrows):
    if ncols <= 2 and nrows <= 2 and EQ_LABEL_RE.search(blob):
        return True
    if ncols <= 2 and nrows <= 2 and re.search(r"[=\u2211]", blob) and "Tabla" not in blob:
        return True
    return False


def pdf_table_to_html(tid, caption, page, tb, page_num, words=None):
    xs = _major_x_edges(tb)
    if len(xs) < 3:
        return ""
    ys = _major_y_edges(tb, xs)
    if len(ys) < 3:
        return ""
    ncols = len(xs) - 1
    nrows = len(ys) - 1
    if words is None:
        words = page.get_text("words") or []
    used = [[False] * ncols for _ in range(nrows)]
    grid = [[None] * ncols for _ in range(nrows)]

    def center(r, c):
        return ((xs[c] + xs[c + 1]) / 2.0, (ys[r] + ys[r + 1]) / 2.0)

    for r in range(nrows):
        for c in range(ncols):
            if used[r][c]:
                continue
            cx, cy = center(r, c)
            cell = _covering_cell(tb, cx, cy)
            rs, cs = 1, 1
            if cell is not None:
                while c + cs < ncols and _in_cell(cell, *center(r, c + cs)):
                    cs += 1
                while r + rs < nrows:
                    if any(used[r + rs][c + k] for k in range(cs)):
                        break
                    if not all(_in_cell(cell, *center(r + rs, c + k)) for k in range(cs)):
                        break
                    rs += 1
            for rr in range(r, r + rs):
                for cc in range(c, c + cs):
                    used[rr][cc] = True
            wds = _words_in_rect(words, xs[c], ys[r], xs[c + cs], ys[r + rs])
            grid[r][c] = {
                "r": r,
                "c": c,
                "rowspan": rs,
                "colspan": cs,
                "words": wds,
                "text": _words_to_text(wds),
                "html": None,
            }

    header_cells = [grid[0][c] for c in range(ncols) if grid[0][c]]
    kgf_cols = set()
    occ_header = False
    for info in header_cells:
        low = (info["text"] or "").lower()
        if "kgf" in low:
            for cc in range(info["c"], info["c"] + info["colspan"]):
                kgf_cols.add(cc)
        if "ocupaci" in low:
            occ_header = True

    body_rows = []
    for r in range(1, nrows):
        cells = [grid[r][c] for c in range(ncols) if grid[r][c]]
        if not cells:
            continue
        if all(not (info["text"] or "").strip() for info in cells):
            continue
        grids_found = []
        for info in cells:
            g = _parse_numeric_grid(info["words"])
            grids_found.append((info, g))
        nested = [(info, g) for info, g in grids_found if g]
        first = cells[0]
        if (
            nested
            and first is not nested[0][0]
            and all(len(g["rows"]) == len(nested[0][1]["rows"]) for _, g in nested)
        ):
            title, labels = _parse_labels(first["words"], nested[0][1]["row_ys"])
            alt_flags = [info["c"] in kgf_cols for info, _ in nested]
            inner = _subtable_html(title, labels, [g for _, g in nested], alt_flags)
            body_rows.append(
                [
                    {
                        "c": 0,
                        "rowspan": 1,
                        "colspan": ncols,
                        "text": "",
                        "html": inner,
                        "classes": ["nested-block"],
                    }
                ]
            )
            continue
        if (
            len(cells) == ncols
            and all(info["rowspan"] == 1 and info["colspan"] == 1 for info in cells)
            and first["text"].strip()
            and all(not info["text"].strip() for info in cells[1:])
            and not _is_number(first["text"])
        ):
            body_rows.append(
                [
                    {
                        "c": 0,
                        "rowspan": 1,
                        "colspan": ncols,
                        "text": first["text"],
                        "html": None,
                        "classes": ["sec"],
                    }
                ]
            )
            continue
        out = []
        for info in cells:
            classes = []
            if info["c"] in kgf_cols:
                classes.append("unit-alt")
            if occ_header and _looks_like_occ(info["text"], info["c"], info["colspan"]):
                classes.append("occ")
            if _is_number(info["text"]):
                classes.append("num")
            inner = None
            g = _parse_numeric_grid(info["words"])
            if g:
                inner = _subtable_html(g.get("title") or "", [], [g], [info["c"] in kgf_cols])
            out.append(
                {
                    "c": info["c"],
                    "rowspan": info["rowspan"],
                    "colspan": info["colspan"],
                    "text": info["text"],
                    "html": inner,
                    "classes": classes,
                }
            )
        body_rows.append(out)

    blob = " ".join(info["text"] for r in range(nrows) for info in (grid[r][c] for c in range(ncols) if grid[r][c]) if info)
    if _table_is_junk(blob, ncols, nrows):
        return ""

    head_html = []
    for info in header_cells:
        classes = []
        if info["c"] in kgf_cols:
            classes.append("unit-alt")
        head_html.append(
            _td("th", info["text"], info["rowspan"], info["colspan"], classes, info.get("html"))
        )
    body_html = []
    for row in body_rows:
        tds = []
        for info in row:
            tds.append(
                _td(
                    "td",
                    info["text"],
                    info["rowspan"],
                    info["colspan"],
                    info.get("classes"),
                    info.get("html"),
                )
            )
        body_html.append("<tr>" + "".join(tds) + "</tr>")
    if not head_html or not body_html:
        return ""
    cap = html.escape(caption or "")
    pdf = (
        f' <a href="{PDF_BASE}#page={page_num}" target="_blank" rel="noopener">PDF p\u00e1g. {page_num}</a>'
        if page_num
        else ""
    )
    return (
        f'<div class="nsr-table-wrap"><p class="table-cap">Tabla {html.escape(tid)}'
        f"{(' \u2014 ' + cap) if cap else ''}{pdf}</p>"
        f"<table class='nsr-table'><thead><tr>{''.join(head_html)}</tr></thead>"
        f"<tbody>{''.join(body_html)}</tbody></table></div>"
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
    blob = " ".join(c for r in rows for c in r)
    if _table_is_junk(blob, ncol, len(rows)):
        return ""
    def _h(c):
        return html.escape(_tidy_text(c)).replace("\n", "<br>") if c else ""
    head = "".join(f"<th>{_h(c)}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{_h(c)}</td>" for c in r) + "</tr>" for r in rows[1:]
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
            later = [c[1] for c in captions if c[1] > y0 + 8 and c[0] != tid]
            if later:
                clip_bot = min(clip_bot, min(later) - 4)
            chosen_tb = None
            best_key = None
            for tb in tables:
                top, bot = tb.bbox[1], tb.bbox[3]
                if top <= y1 <= bot:
                    key = (0, abs(top - y0))
                elif y1 - 8 <= top <= min(clip_bot, y1 + 170):
                    key = (1, top - y1)
                else:
                    continue
                if best_key is None or key < best_key:
                    best_key = key
                    chosen_tb = tb
            if chosen_tb is None:
                continue
            if tid in catalog:
                continue
            html_tbl = pdf_table_to_html(tid, "", page, chosen_tb, i, words)
            nscore = chosen_tb.row_count
            if not html_tbl:
                matrix = None
                try:
                    matrix = chosen_tb.extract()
                except Exception:
                    matrix = None
                if not matrix:
                    continue
                html_tbl = cells_to_html(tid, "", matrix, i)
                nscore = len(matrix)
            if not html_tbl:
                continue
            score = html_tbl.count("<td") + html_tbl.count("<th")
            catalog[tid] = {"html": html_tbl, "page": i, "rows": nscore, "score": score}
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
                if j - i > 250:
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
