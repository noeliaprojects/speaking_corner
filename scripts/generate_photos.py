"""Generate the missing slide photos with the OpenAI Images API.
Reads every photo prompt from src/decks.json (same list as Info > Photos), skips photos already in img/,
and saves new ones as img/<name>.jpg. Needs the OPENAI_API_KEY environment variable.
Usage: python3 scripts/generate_photos.py --max 20 --quality medium [--only deck-id]"""
import argparse, base64, io, json, os, re, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = {"use-it-for", "defend-the-object", "great-swap"}
STYLE = ("Realistic photograph, natural light, simple and uncluttered, no text, no logos or brand names, "
         "no real or famous people, people only from behind or far away (no recognisable faces) unless the description says otherwise, "
         "landscape format, the photo fills the whole frame with no borders.")

def photo_list(decks):
    out = []
    for d in decks:
        if d.get("coverP"):
            out.append((f"{d['id']}-cover", d["coverP"]))
        if not d.get("img") or d["id"] in LEGACY:
            continue
        p = d["imgP"]
        def sub(x):
            x = x if p.startswith("{x}") else x[:1].lower() + x[1:]
            return p.replace("{x}", x)
        for i, c in enumerate(d["cards"]):
            n = f"{i+1:02d}"
            if d["kind"] == "versus":
                out += [(f"{d['id']}-{n}a", sub(c["a"])), (f"{d['id']}-{n}b", sub(c["b"]))]
            elif d["kind"] == "triple":
                out += [(f"{d['id']}-{n}-{k+1}", sub(x)) for k, x in enumerate(c)]
            else:
                out.append((f"{d['id']}-{n}", sub(c["t"] if isinstance(c, dict) else c)))
    return out

def generate(prompt, quality, key):
    body = json.dumps({"model": "gpt-image-1", "prompt": f"{prompt}. {STYLE}", "size": "1536x1024",
                       "quality": quality, "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    return base64.b64decode(data["data"][0]["b64_json"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--quality", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Add it in GitHub: Settings > Secrets and variables > Actions.")
    decks = json.load(open(os.path.join(ROOT, "src/decks.json")))
    have = {f.rsplit(".", 1)[0] for f in os.listdir(os.path.join(ROOT, "img"))}
    todo = [(n, p) for n, p in photo_list(decks) if n not in have and (not a.only or n.startswith(a.only + "-"))]
    print(f"{len(todo)} photos missing; generating up to {a.max}")
    done = 0
    credits_path = os.path.join(ROOT, "src/credits.json")
    credits = json.load(open(credits_path)) if os.path.exists(credits_path) else {}
    for name, prompt in todo[: a.max]:
        try:
            raw = generate(prompt, a.quality, key)
        except Exception as e:
            print(f"  ! {name}: {e}")
            continue
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((1200, 800))
        # Visible credit on each AI-produced image, as requested by the teacher.
        label = "Created with ChatGPT (OpenAI)"
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17) if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") else ImageFont.load_default()
        bb = draw.textbbox((0,0), label, font=font)
        width = bb[2]-bb[0]
        margin = 11
        x = max(6, im.width-width-2*margin)
        y = im.height-35
        draw.rounded_rectangle((x-7,y-5,im.width-8,im.height-7),radius=5,fill=(21,48,46))
        draw.text((x,y),label,font=font,fill=(255,255,255))
        im.save(os.path.join(ROOT, "img", f"{name}.jpg"), quality=82, optimize=True)
        credits[name] = {"title": prompt[:140], "author": "ChatGPT (OpenAI)", "license": "AI-generated", "source": "https://openai.com/", "generated": True, "query": prompt}
        done += 1
        print(f"  + {name}")
    json.dump(credits,open(credits_path,"w"),ensure_ascii=False,indent=1)
    print(f"done: {done} new photos")

if __name__ == "__main__":
    main()
