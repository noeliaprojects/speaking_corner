import json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SansB", F + "DejaVuSans-Bold.ttf"))
INK, RED, MUTED = HexColor("#1b2340"), HexColor("#d8432f"), HexColor("#5d6584")
here = os.path.dirname(os.path.abspath(__file__))
decks = {d["id"]: d for d in json.load(open(os.path.join(here, "decks.json")))}
os.makedirs(os.path.join(here, "print"), exist_ok=True)

W, H = A4
M = 8 * mm  # printable margin


def grid_pdf(path, items, cols, rows, draw, title):
    cw, ch = (W - 2 * M) / cols, (H - 2 * M) / rows
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle(title)
    per = cols * rows
    for p in range(0, len(items), per):
        page = items[p:p + per]
        for i, it in enumerate(page):
            col, row = i % cols, i // cols
            x, y = M + col * cw, H - M - (row + 1) * ch
            draw(c, it, x, y, cw, ch)
        # cut lines (dashed, shared edges => one cut per line)
        c.setDash(3, 3); c.setStrokeColor(MUTED); c.setLineWidth(0.4)
        nrows = (len(page) + cols - 1) // cols
        for k in range(cols + 1):
            c.line(M + k * cw, H - M, M + k * cw, H - M - nrows * ch)
        for k in range(nrows + 1):
            c.line(M, H - M - k * ch, M + cols * cw, H - M - k * ch)
        c.setDash()
        c.showPage()
    c.save()


def fit(c, text, font, size, maxw):
    while pdfmetrics.stringWidth(text, font, size) > maxw and size > 8:
        size -= 1
    return size


def wrap(text, font, size, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def taboo_card(c, it, x, y, w, h):
    pad = 5 * mm
    c.setFillColor(INK); c.rect(x + pad, y + h - pad - 16 * mm, w - 2 * pad, 16 * mm, stroke=0, fill=1)
    word = it["w"].upper()
    s = fit(c, word, "SansB", 18, w - 4 * pad)
    c.setFillColor(HexColor("#ffffff")); c.setFont("SansB", s)
    c.drawCentredString(x + w / 2, y + h - pad - 10.5 * mm, word)
    c.setFillColor(RED); c.setFont("SansB", 8)
    c.drawCentredString(x + w / 2, y + h - pad - 21 * mm, "DON'T SAY")
    c.setFillColor(INK); c.setFont("Sans", 12)
    for k, t in enumerate(it["no"]):
        c.drawCentredString(x + w / 2, y + h - pad - 28 * mm - k * 6 * mm, t)
    c.setFillColor(MUTED); c.setFont("Sans", 6.5)
    c.drawCentredString(x + w / 2, y + pad - 1 * mm, "Taboo · Speaking Corner")


def role_card(c, it, x, y, w, h):
    pad = 6 * mm
    c.setFillColor(RED); c.setFont("SansB", 8)
    c.drawCentredString(x + w / 2, y + h - pad - 3 * mm, "SECRET ROLE")
    c.setFillColor(INK)
    lines = wrap(it, "SansB", 15, w - 2 * pad)
    top = y + h / 2 + (len(lines) - 1) * 9.5 / 2
    c.setFont("SansB", 15)
    for k, l in enumerate(lines):
        c.drawCentredString(x + w / 2, top - k * 19 - 4, l)
    c.setFillColor(MUTED); c.setFont("Sans", 7)
    c.drawCentredString(x + w / 2, y + pad - 1 * mm, "Answer only yes or no. Don't show this card!")


t = decks["taboo"]["cards"]
grid_pdf(os.path.join(here, "print/taboo-cards.pdf"), t, 3, 4, taboo_card, "Taboo cards")
r = decks["hot-seat"]["cards"]
grid_pdf(os.path.join(here, "print/hot-seat-roles.pdf"), r, 3, 4, role_card, "Hot Seat secret roles")
print("ok", len(t), len(r))
