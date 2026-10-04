#!/usr/bin/env python3
"""把漫畫分鏡裡的 {代號} 展開成完整英文，輸出到 漫畫/展開版/，方便直接複製給生圖 AI。"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "漫畫"

def norm(k):
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]", "-", k.upper())).strip("-")

def english(s):
    return len(re.findall(r"[A-Za-z]+", s)) >= 5 and not re.search(r"[一-鿿]", s)

def defs_from(text):
    d = {}
    for m in re.finditer(r"^([A-Z][A-Z0-9 .'\-]+):\s+(.+)$", text, re.M):
        if english(m.group(2)):
            d[norm(m.group(1))] = m.group(2).strip()
    for m in re.finditer(r"^\|\s*\{?([A-Z][A-Z0-9 .'\-]+)\}?\s*\|\s*(.+?)\s*\|\s*$", text, re.M):
        if english(m.group(2)):
            d[norm(m.group(1))] = m.group(2).strip().strip("`")
    return d

bible = (ROOT / "00-企劃與風格.md").read_text(encoding="utf-8")
base = defs_from(bible)
m = re.search(r"附身時加：`(.+?)`", bible)
if m:
    base["SHEN-YAN-SMILE"] = m.group(1)

missing_all = {}
for f in sorted(ROOT.glob("第0*.md")):
    text = f.read_text(encoding="utf-8")
    d = dict(base); d.update(defs_from(text))
    missing = set()
    def rep(m):
        inner = m.group(1)
        if inner.startswith("RED:"):
            return f"monochrome except for a single faded rose-red accent on {inner[4:].strip()}"
        k = norm(inner)
        if k in d:
            return d[k]
        missing.add(inner)
        return m.group(0)
    out = []
    for line in text.splitlines():
        if line.startswith("- Prompt："):
            line = "- Prompt：" + re.sub(r"\{([^{}]+)\}", rep, line[len("- Prompt："):])
        out.append(line)
    (ROOT / "展開版" / f.name).write_text(
        "> 本檔由 tools/expand_manga.py 自動產生：每一格的 Prompt 已把 {代號} 換成完整英文，可直接複製。要修改請改原始分鏡檔或 00-企劃與風格.md，再重新執行。\n\n" + "\n".join(out) + "\n",
        encoding="utf-8")
    if missing:
        missing_all[f.name] = sorted(missing)

print("未定義的代號：", missing_all or "無")
