#!/usr/bin/env python3
"""把漫畫分鏡轉成「一頁一個 prompt」的 ChatGPT 版，輸出到 漫畫/ChatGPT版/。"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent / "漫畫"
OUT = ROOT / "ChatGPT版"
OUT.mkdir(exist_ok=True)

NAMES = {
    "ZHOU": "周遠", "SHEN-YAN": "沈言", "SHEN-YAN-SMILE": "（附身的笑：嘴角拉得過寬、眼睛半閉）",
    "LIN-YI": "林依", "XIAO-FANG": "小方", "A-KAI": "阿凱", "DRIVER-HUANG": "黃司機",
    "DR-HE-JING": "何靜", "GRANNY-BED-SEVEN": "七號床阿婆", "INNKEEPER": "福星旅社老闆娘",
    "OLD-WU": "老吳", "HAT-MAN": "戴帽的男人（臉永遠在陰影裡）", "CHEN-SHOUYI": "陳守一",
    "GE-QINGYA": "葛青崖", "SENIOR-APPRENTICE": "師兄", "XIAO-MAN": "小滿", "YUE-E": "月娥",
    "OLD-MASTER-SHEN": "沈家老太爺", "FERRYMAN-LIN": "撐船的漢子（小滿的阿爸）",
}

def norm(k):
    return re.sub(r"-+", "-", re.sub(r"[^A-Z0-9]", "-", k.upper())).strip("-")

def english(s):
    return len(re.findall(r"[A-Za-z]+", s)) >= 5 and not re.search(r"[一-鿿]", s)

def defs_from(text):
    d = {}
    for m in re.finditer(r"^([A-Z][A-Z0-9 .'\-]+):\s+(.+)$", text, re.M):
        if english(m.group(2)): d[norm(m.group(1))] = m.group(2).strip()
    for m in re.finditer(r"^\|\s*\{?([A-Z][A-Z0-9 .'\-]+)\}?\s*\|\s*(.+?)\s*\|\s*$", text, re.M):
        if english(m.group(2)): d[norm(m.group(1))] = m.group(2).strip().strip("`")
    return d

base = defs_from((ROOT / "00-企劃與風格.md").read_text(encoding="utf-8"))
TAIL = re.compile(r",?\s*no text, no letters.*$", re.I)

def clean_prompt(p, d):
    p = TAIL.sub("", p)
    def rep(m):
        inner = m.group(1)
        if inner.startswith("RED:"):
            return f"monochrome except for a single faded rose-red accent on {inner[4:].strip()}"
        k = norm(inner)
        if k.startswith("STYLE"): return ""
        if k in NAMES: return NAMES[k]
        return d.get(k, inner)
    p = re.sub(r"\{([^{}]+)\}", rep, p)
    return re.sub(r"\s*,\s*,", ",", p).strip(" ,")

for f in sorted(ROOT.glob("第0*.md")):
    text = f.read_text(encoding="utf-8")
    d = dict(base); d.update(defs_from(text))
    ep = re.match(r"第0(\d)話-(.+)\.md", f.name)
    pages = re.split(r"^### ", text, flags=re.M)[1:]
    out = [f"# 《霧川》漫畫　第{ep.group(1)}話〈{ep.group(2)}〉　ChatGPT 逐頁 prompt\n",
           "> 使用前先在同一個對話貼上 `00-ChatGPT開場設定.md` 的開場設定，並上傳角色設定圖。之後一次貼一頁。\n"]
    for pg in pages:
        head, _, body = pg.partition("\n")
        mp = re.match(r"(P\d+)", head)
        if not mp:
            continue
        pno = mp.group(1)
        layout = re.search(r"版型[:：]\s*([^）)]+)", head)
        style = "舊線 1931 風格（毛筆水墨、泛黃紙感）" if "STYLE-1931" in body else "今線 2026 風格（細鋼筆線、冷灰網點）"
        panels = re.split(r"^\*\*格\s*", body, flags=re.M)[1:]
        lines = []
        for pn in panels:
            num, _, rest = pn.partition("**")
            pos = re.match(r"\s*（([^）]*)）", rest)
            scene = re.search(r"^- 畫面：(.+)$", rest, re.M)
            prm = re.search(r"^- Prompt：(.+)$", rest, re.M)
            txt = re.search(r"^- 文字：(.+)$", rest, re.M)
            t = txt.group(1).strip() if txt else "（無）"
            t = "不要加任何字" if t.startswith("（無") else t
            lines.append(f"格{num.strip()}（{pos.group(1) if pos else ''}）：{scene.group(1).strip() if scene else ''}\n　細節：{clean_prompt(prm.group(1), d) if prm else ''}\n　文字：{t}")
        n = len(lines)
        out.append(f"## {head.strip()}\n\n```\n請畫《霧川》第{ep.group(1)}話第{int(pno[1:])}頁。直式 2:3，黑白漫畫，{style}，依開場設定。日式右翻，格子閱讀順序右上→左上→右下→左下。本頁共 {n} 格{('，版型：' + layout.group(1).strip()) if layout else ''}。\n\n" + "\n\n".join(lines) + "\n\n文字規則：〔〕裡標的是類別與位置。對白、旁白都用繁體中文，字要寫正確、清楚；台語台詞旁的〔〕是華語註解，用小字附在旁邊。沒有標文字的格子不要加任何字。\n```\n")
    (OUT / f.name).write_text("\n".join(out), encoding="utf-8")
    print(f.name, sum(1 for x in out if x.startswith("## P")), "頁")
