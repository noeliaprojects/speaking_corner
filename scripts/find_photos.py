"""Find free, openly licensed real photos for the slides (no API key needed).
Searches Openverse (CC0 / public domain / CC BY / CC BY-SA photographs) and falls back to Wikimedia Commons.
Saves img/<name>.jpg cropped to 4:3 and records the author and licence in src/credits.json.
Usage: python3 scripts/find_photos.py --max 60 [--only deck-id] [--redo name1,name2]"""
import argparse, io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_photos import photo_list, ROOT

UA = {"User-Agent": "SpeakingCorner/1.0 (classroom slides; github.com/noeliaprojects/speaking_corner)"}
STOP = r"^(a|an|the|your|you|my|some|several)\s+"

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else json.load(r)

QUERIES = json.load(open(os.path.join(ROOT, "src/photo_queries.json"))) if os.path.exists(os.path.join(ROOT, "src/photo_queries.json")) else {}
BAD = re.compile(r"engraving|illustration|drawing|painting|caricature|diagram|map of|poster|logo|screenshot|stereograph|lithograph|print|cartoon|sketch|stereo|obama|trump|biden|president|white house|vintage|black and white|\b1[89]\d\d\b", re.I)

def query_for(deck, card, name):
    if name in QUERIES:
        return QUERIES[name]
    if deck.get("qP"):
        base = deck["qP"]
    else:
        base = "{x}"
    if name.endswith("-cover"):
        return deck.get("coverQ") or deck["name"]
    if isinstance(card, dict):
        x = card.get("q") or (re.sub(r"^(He|She)'s (a|an) ", "", card["ans"]).rstrip(".") + " at work" if "ans" in card and deck["id"] == "guess-the-job" else card.get("t", ""))
    else:
        x = card
    x = re.sub(r"[\"'…?!.]", " ", x)
    x = re.sub(STOP, "", x.strip(), flags=re.I)
    return base.replace("{x}", x).strip()

def openverse(q, used):
    p = urllib.parse.urlencode({"q": q, "license": "cc0,pdm,by,by-sa", "category": "photograph",
                                "aspect_ratio": "wide", "size": "large", "page_size": 20, "mature": "false", "source": "flickr,wikimedia,stocksnap,rawpixel,nappy"})
    res = get(f"https://api.openverse.org/v1/images/?{p}").get("results", [])
    for r in res:
        if r["url"] in used or (r.get("width") or 0) < 800 or BAD.search((r.get("title") or "") + " " + " ".join(t.get("name", "") for t in r.get("tags") or [])):
            continue
        lic = f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip() if r["license"] not in ("cc0", "pdm") else ("CC0" if r["license"] == "cc0" else "Public domain")
        return {"url": r["url"], "author": r.get("creator") or "Unknown", "license": lic,
                "source": r.get("foreign_landing_url") or r["url"], "title": r.get("title") or q}
    return None

def commons(q, used):
    p = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f"{q} filetype:bitmap", "gsrlimit": 15, "prop": "imageinfo",
                                "iiprop": "url|extmetadata|size", "iiurlwidth": 1400})
    pages = get(f"https://commons.wikimedia.org/w/api.php?{p}").get("query", {}).get("pages", {})
    for pg in sorted(pages.values(), key=lambda x: x.get("index", 99)):
        ii = pg.get("imageinfo", [{}])[0]
        if ii.get("width", 0) < 800 or ii.get("width", 0) < ii.get("height", 1) or BAD.search(pg.get("title", "")):
            continue
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not re.search(r"CC0|Public domain|CC BY(-SA)? ", lic + " ", re.I) or re.search(r"NC|ND", lic):
            continue
        url = ii.get("thumburl") or ii["url"]
        if url in used:
            continue
        author = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "Unknown")).strip()
        return {"url": url, "author": author[:80], "license": lic, "source": ii.get("descriptionurl", url), "title": pg["title"]}
    return None

def save(img_bytes, path):
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = im.size; tw = min(w, int(h * 4 / 3)); th = int(tw * 3 / 4)
    im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th))
    im.thumbnail((1200, 900)); im.save(path, quality=82, optimize=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=60); ap.add_argument("--only", default=""); ap.add_argument("--redo", default="")
    a = ap.parse_args()
    decks = json.load(open(os.path.join(ROOT, "src/decks.json")))
    by_id = {d["id"]: d for d in decks}
    cpath = os.path.join(ROOT, "src/credits.json")
    credits = json.load(open(cpath)) if os.path.exists(cpath) else {}
    redo = set(filter(None, a.redo.split(",")))
    have = {f.rsplit(".", 1)[0] for f in os.listdir(os.path.join(ROOT, "img"))} - redo
    used = {c["url"] for c in credits.values()}
    todo = []
    for name, _ in photo_list(decks):
        if name in have or (a.only and not name.startswith(a.only + "-")):
            continue
        did = next(i for i in sorted(by_id, key=len, reverse=True) if name.startswith(i + "-"))
        d = by_id[did]; rest = name[len(did) + 1:]
        if rest == "cover": card = None
        else:
            i = int(rest[:2]) - 1; c = d["cards"][i]
            card = c["a"] if rest.endswith("a") and d["kind"] == "versus" else c["b"] if rest.endswith("b") and d["kind"] == "versus" else c[int(rest[3]) - 1] if d["kind"] == "triple" else c
        if d.get("noSearch") and rest != "cover":
            continue
        todo.append((name, query_for(d, card, name)))
    print(f"{len(todo)} photos to find; trying up to {a.max}")
    found = 0
    for name, q in todo[: a.max]:
        hit = None
        for src in (openverse, commons):
            try:
                hit = src(q, used)
            except Exception as e:
                print(f"  ! {src.__name__} {name}: {e}"); time.sleep(5)
            if hit: break
        if not hit:
            print(f"  - {name}: nothing for '{q}'"); continue
        try:
            save(get(hit["url"], binary=True), os.path.join(ROOT, "img", f"{name}.jpg"))
        except Exception as e:
            print(f"  ! download {name}: {e}"); continue
        hit["query"] = q; credits[name] = hit; used.add(hit["url"]); found += 1
        print(f"  + {name}  ({q})  {hit['license']}")
        time.sleep(3)
    json.dump(credits, open(cpath, "w"), ensure_ascii=False, indent=1)
    print(f"done: {found} photos")

if __name__ == "__main__":
    main()
