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

def cnum(n):
    if n <= 10: return "十" if n == 10 else CN[n]
    if n < 20: return "十" + (CN[n % 10] if n % 10 else "")
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")

def volumes():
    outline = (ROOT / "01-大綱.md").read_text(encoding="utf-8")
    vols = []
    for m in re.finditer(r"^## (卷.)　(.+?)\n\n(.+?)\n\n(.+?)(?=\n## |\Z)", outline, re.S | re.M):
        chs = []
        for row in re.finditer(r"^\| (\d+) \| (.+?) \| (.+?) \|", m.group(4), re.M):
            chs.append({"n": int(row.group(1)), "name": row.group(2), "line": ""})
        vols.append({"vol": m.group(1), "name": m.group(2), "chapters": chs})  # 不放卷簡介，免得暴雷
    return vols

def main():
    chapters = {}
    for f in sorted((ROOT / "正文").glob("*.md")):
        n = int(f.name.split("-")[0])
        title, body = md_to_html(f.read_text(encoding="utf-8"))
        chars = len(re.sub(r"\s|<[^>]+>", "", body))
        chapters[n] = {"title": title, "html": body, "chars": chars}
    # 彩蛋：另成一區，編號 81 起，顯示用 label
    vols = volumes()
    outline = (ROOT / "01-大綱.md").read_text(encoding="utf-8")
    em = re.search(r"^## 彩蛋　(.+?)\n\n(.+?)\n\n(.+?)(?=\n## |\Z)", outline, re.S | re.M)
    if em:
        eggs = []
        for i, row in enumerate(re.finditer(r"^\| ([一二三四五六七八九十]) \| (.+?) \| (.+?) \|", em.group(3), re.M)):
            n = 81 + i
            eggs.append({"n": n, "name": row.group(2), "line": "", "label": "彩蛋" + row.group(1)})
            f = ROOT / "彩蛋" / f"{i + 1:02d}-{row.group(2)}.md"
            if f.exists():
                title, body = md_to_html(f.read_text(encoding="utf-8"))
                chapters[n] = {"title": title, "html": body, "chars": len(re.sub(r"\s|<[^>]+>", "", body))}
        vols.append({"vol": "彩蛋", "name": em.group(1), "chapters": eggs})
    # 第二部《日遊》：編號 1001 起，顯示用 label；只收已排到每章一句的卷
    ry = ROOT / "日遊" / "01-大綱.md"
    if ry.exists():
        yo = ry.read_text(encoding="utf-8")
        first = True
        for m in re.finditer(r"^## (卷.)　(.+?)\n\n(.+?)\n\n(.+?)(?=\n## |\Z)", yo, re.S | re.M):
            chs = []
            for row in re.finditer(r"^\| (\d+) \| (.+?) \| (.+?) \|", m.group(4), re.M):
                k = int(row.group(1)); n = 1000 + k
                chs.append({"n": n, "name": row.group(2), "line": "", "label": "第" + cnum(k) + "章", "short": k})
                for f in (ROOT / "日遊" / "正文").glob(f"{k:02d}-*.md"):
                    title, body = md_to_html(f.read_text(encoding="utf-8"))
                    chapters[n] = {"title": title, "html": body, "chars": len(re.sub(r"\s|<[^>]+>", "", body))}
            if chs:
                name = re.sub(r"（.*?）$", "", m.group(2))
                vols.append({"vol": m.group(1), "name": name, "chapters": chs, "book": "日遊" if first else ""})
                first = False
    core = re.search(r"## 故事核心\n\n(.+?)\n", outline).group(1)
    data = {"volumes": vols, "chapters": chapters, "core": core}
    tpl = (ROOT / "tools" / "reader_template.html").read_text(encoding="utf-8")
    body = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    # Vercel 版：完整的 HTML 文件，含手機用的 meta 與加到主畫面的圖示
    cut = body.index("</style>") + len("</style>")
    page = HEAD.replace("</head>", body[:cut] + "\n</head>") + body[cut:] + "\n</body>\n</html>\n"
    (site / "index.html").write_text(page, encoding="utf-8")
    # claude.ai Artifact 版：發布時會自動包上外殼，所以只放內容
    art = ROOT / "build"
    art.mkdir(exist_ok=True)
    (art / "artifact.html").write_text(body, encoding="utf-8")
    print(f"{site / 'index.html'}  {len(chapters)} 章")

HEAD = """<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="「陰陽帳」三部曲：《霧川》十卷八十章、彩蛋，與第二部《日遊》。">
<meta name="theme-color" content="#e7ebe9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1316" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="霧川">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
"""

if __name__ == "__main__":
    main()
