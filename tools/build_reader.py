#!/usr/bin/env python3
"""把 正文/ 與 01-大綱.md 組成單一 HTML 閱讀頁：site/index.html。"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CN = "〇一二三四五六七八九"

def inline(s):
    s = html.escape(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

def md_to_html(text):
    out, title = [], ""
    for block in re.split(r"\n\s*\n", text.strip()):
        b = block.strip()
        if b.startswith("## "):
            title = b[3:].strip()
            continue
        if b == "---":
            out.append('<hr class="sep">')
            continue
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) == 1 and re.fullmatch(r"\*\*.{1,3}\*\*", lines[0]):
            out.append('<p class="beat">' + inline(lines[0]) + "</p>")
            continue
        if all(re.fullmatch(r"\*\*.+\*\*", l) for l in lines):
            cls = "era" if any("年，" in l for l in lines) else "doc"
            out.append(f'<p class="{cls}">' + "<br>".join(inline(l)[8:-9] for l in lines) + "</p>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in lines) + "</p>")
    return title, "\n".join(out)

def volumes():
    outline = (ROOT / "01-大綱.md").read_text(encoding="utf-8")
    vols = []
    for m in re.finditer(r"^## (卷.)　(.+?)\n\n(.+?)\n\n(.+?)(?=\n## |\Z)", outline, re.S | re.M):
        chs = []
        for row in re.finditer(r"^\| (\d+) \| (.+?) \| (.+?) \|", m.group(4), re.M):
            chs.append({"n": int(row.group(1)), "name": row.group(2), "line": row.group(3)})
        vols.append({"vol": m.group(1), "name": m.group(2), "blurb": m.group(3).strip(), "chapters": chs})
    return vols

def main():
    chapters = {}
    for f in sorted((ROOT / "正文").glob("*.md")):
        n = int(f.name.split("-")[0])
        title, body = md_to_html(f.read_text(encoding="utf-8"))
        chars = len(re.sub(r"\s|<[^>]+>", "", body))
        chapters[n] = {"title": title, "html": body, "chars": chars}
    outline = (ROOT / "01-大綱.md").read_text(encoding="utf-8")
    core = re.search(r"## 故事核心\n\n(.+?)\n", outline).group(1)
    data = {"volumes": volumes(), "chapters": chapters, "core": core}
    tpl = (ROOT / "tools" / "reader_template.html").read_text(encoding="utf-8")
    out = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    dest = ROOT / "site" / "index.html"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"{dest}  {len(chapters)} 章")

if __name__ == "__main__":
    main()
