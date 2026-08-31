# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"E:\dev\NSR-10")


def load_title(letter):
    p = ROOT / "lector" / f"titulo-{letter}.js"
    txt = p.read_text(encoding="utf-8")
    key = f'window.NSR_TITLES[{json.dumps(letter)}]'
    i = txt.find(key + "=")
    payload = txt[i + len(key) + 1 :].strip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


obj = load_title("F4A")
print("F4A chapters", [c["id"] for c in obj["chapters"]], "narts", sum(len(c["articles"]) for c in obj["chapters"]))
print("sample ids", [a["id"] for a in obj["chapters"][0]["articles"][:8]])
print("modFile", obj["chapters"][0]["articles"][0].get("modFile"), obj["chapters"][0]["articles"][0].get("modPage"))

obj = load_title("AIS410")
print("AIS ch", [(c["id"], len(c["articles"])) for c in obj["chapters"]])
arts = [a for c in obj["chapters"] for a in c["articles"]]
print("AIS n", len(arts), "sample", [(a["id"], a["title"][:40]) for a in arts[:6]])
pam = [a for a in arts if "7.8" in a["id"] or "PAM" in (a["title"] or "").upper()]
print("PAM-ish", [(a["id"], a["title"][:50], "7.8-2" in a["html"]) for a in pam[:8]])

obj = load_title("B")
b6 = [c for c in obj["chapters"] if c["id"] == "B.6"][0]
for a in b6["articles"]:
    if a["id"].startswith("B.6.5.4") or "B.6.4-1" in (a.get("html") or ""):
        print(
            a["id"],
            a["modified"],
            a.get("modPage"),
            "wind" in (a["html"] or ""),
            "txt-modificado" in (a["html"] or ""),
        )

obj = load_title("A")
hits = []
for c in obj["chapters"]:
    for a in c["articles"]:
        if a["id"] in {"A.10.9.2.6", "A.10.9.2.7"} or "17777" in (a.get("html") or ""):
            hits.append((a["id"], a["modified"], a.get("source"), a.get("modPage"), a.get("modFile", "")[-35:]))
print("A hits", hits)

obj = load_title("A5APP")
print("A5", [(c["id"], len(c["articles"])) for c in obj["chapters"]])
a5211 = [a for c in obj["chapters"] for a in c["articles"] if a["id"] == "A-5.2.1.1"]
if a5211:
    print("A-5.2.1.1 src", a5211[0]["source"], "titulo VI" in a5211[0]["html"], "podran consultar" in a5211[0]["html"].lower())
