"""Generate installable PNG app icons using only the Python standard library.
The symbol is an original pair of overlapping conversation bubbles, not a font.
Executed by build.py during GitHub Pages deployment.
"""
from pathlib import Path
import math,struct,zlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"icons"
OUT.mkdir(exist_ok=True)
def rr(x,y,x0,y0,x1,y1,r):
    cx=max(x0+r,min(x,x1-r));cy=max(y0+r,min(y,y1-r))
    return (x-cx)**2+(y-cy)**2<=r*r
def build(sz):
    out=bytearray()
    for j in range(sz):
        out.append(0)
        y=(j+.5)/sz
        for i in range(sz):
            x=(i+.5)/sz
            c=(22,111,105,255)
            # Teal base with generous padding for maskable launcher cropping.
            if rr(x,y,.22,.24,.77,.67,.12):
                c=(255,253,246,255)
            # A second, smaller speech bubble overlapping the top-right corner.
            if rr(x,y,.44,.38,.85,.77,.095):
                c=(249,179,114,255)
            # Tail of orange bubble.
            if .52<x<.69 and .72<y<.83 and y<(.83-(x-.52)*.42):
                c=(249,179,114,255)
            # Tail of white bubble (front bubble tail would otherwise be behind).
            if .26<x<.42 and .60<y<.74 and y<(.74-(x-.26)*.65):
                c=(255,253,246,255)
            # Two tiny ink dots suggest a conversation.
            if ((x-.565)**2+(y-.56)**2)<.019**2 or ((x-.687)**2+(y-.56)**2)<.019**2:
                c=(22,111,105,255)
            out.extend(c)
    def chunk(typ,data):return struct.pack(">I",len(data))+typ+data+struct.pack(">I",zlib.crc32(typ+data)&0xffffffff)
    head=b"\x89PNG\r\n\x1a\n"
    ihdr=struct.pack(">2I5B",sz,sz,8,6,0,0,0)
    return head+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(bytes(out),9))+chunk(b"IEND",b"")
for size in (192,512):
    (OUT/f"app-{size}.png").write_bytes(build(size))
print("Generated installable PNG app icons: 192px and 512px")
