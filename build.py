"""Build index.html from src/template.html + src/decks.json, and link every photo in img/.
Run: python3 build.py"""
import json, re, os
ROOT = os.path.dirname(os.path.abspath(__file__))
decks = json.load(open(os.path.join(ROOT, "src/decks.json")))
ids = [d["id"] for d in decks]
imgs = {}
for f in sorted(os.listdir(os.path.join(ROOT, "img"))):
    n, p = f.rsplit(".", 1)[0], "img/" + f
    m = re.fullmatch(r"use-(\d\d)", n)
    if m: imgs[f"use-it-for:{int(m[1])-1}"] = p; continue
    m = re.fullmatch(r"defend-(\d\d)", n)
    if m: imgs[f"defend-the-object:{int(m[1])-1}"] = p; continue
    m = re.fullmatch(r"swap-(\d\d)([ab])", n)
    if m: imgs[f"great-swap:{int(m[1])-1}{m[2]}"] = p; continue
    for i in sorted(ids, key=len, reverse=True):
        if n.startswith(i + "-"):
            r = n[len(i)+1:]
            if r == "cover": imgs[f"{i}:cover"] = p
            elif re.fullmatch(r"\d\d", r): imgs[f"{i}:{int(r)-1}"] = p
            elif re.fullmatch(r"\d\d[ab]", r): imgs[f"{i}:{int(r[:2])-1}{r[2]}"] = p
            elif re.fullmatch(r"\d\d-\d", r): imgs[f"{i}:{int(r[:2])-1}-{int(r[3])-1}"] = p
            break
t = open(os.path.join(ROOT, "src/template.html")).read()
t = re.sub(r"const IMAGES=\{.*?\};", "const IMAGES=" + json.dumps(imgs) + ";", t, count=1)
body = t.replace("/*DECKS*/[]", json.dumps(decks, ensure_ascii=False))
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + body.replace("</style>", "</style>\n</head>\n<body>", 1) + "\n</body>\n</html>\n")
open(os.path.join(ROOT, "index.html"), "w").write(page)
print(f"index.html built: {len(decks)} activities, {len(imgs)} photos")
