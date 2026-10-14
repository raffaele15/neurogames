import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import pymupdf, json, re, os, collections, sys, shutil
from PIL import Image
sys.path.insert(0, W)
import parse as P
os.chdir(_os.environ.get("NG_BOOKS") or (W+"/books" if _os.path.isdir(W+"/books") else _os.path.join(W, "..", "..", "quiz database")))
OUT = SITE+"/img"
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
qs = json.load(open(W+"/all_en.json"))
for q in qs: q.pop("imgs", None); q.pop("imgsrc", None)
bybook = collections.defaultdict(list)
for q in qs: bybook[q["book"]].append(q)
stats = collections.Counter()
ALLOW_VECTOR = True
WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}

def save(page, rect, q, how):
    rect = rect & page.rect
    if rect.width < 40 or rect.height < 40: return
    if len(q.get("imgs", [])) >= 4: return
    zoom = min(2.2, 1100/max(rect.width, 1))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=rect)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    from PIL import ImageStat
    if max(ImageStat.Stat(im.convert("L")).stddev) < 12: return
    if im.width > 1000: im = im.resize((1000, int(im.height*1000/im.width)))
    name = f'{q["id"]}-{len(q.get("imgs", []))}.webp'
    im.save(os.path.join(OUT, name), "WEBP", quality=58, method=6)
    q.setdefault("imgs", []).append(name); q["imgsrc"] = how; stats[how] += 1

def text_blocks(page): return [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
def img_rects(page):
    return [pymupdf.Rect(i["bbox"]) & page.rect for i in page.get_image_info() if i["bbox"][2]-i["bbox"][0] > 40 and i["bbox"][3]-i["bbox"][1] > 40]

def figure_region(page, cap):
    """region of the figure that sits right above a caption block"""
    cx0, cy0, cx1 = cap[0], cap[1], cap[2]
    W = page.rect.width
    # column span: if caption is narrow, assume its column
    col0, col1 = (cx0-8, cx1+8) if cx1-cx0 < 0.6*W else (30, W-30)
    if cx1-cx0 < 0.6*W:
        if cx0 < W*0.45: col0, col1 = 25, W*0.5
        else: col0, col1 = W*0.5, W-25
    imgs = [r for r in img_rects(page) if r.y1 <= cy0+6 and r.y1 > cy0-70 and r.x1 > col0 and r.x0 < col1]
    if imgs:
        best = max(imgs, key=lambda r: r.y1)
        reg = pymupdf.Rect(best)
        changed = True
        while changed:  # grow over adjacent panels (side by side or stacked)
            changed = False
            for r in img_rects(page):
                if reg.contains(r) or not (r.x1 > col0 and r.x0 < col1): continue
                if (reg + (-30, -30, 30, 30)).intersects(r):
                    reg |= r; changed = True
        return reg
    if not ALLOW_VECTOR: return None
    # vector figure: from the last text block above (same column) to the caption
    above = [b for b in text_blocks(page) if b[3] <= cy0-2 and b[2] > col0 and b[0] < col1
             and (len(b[4].strip()) > 60 or re.match(r"^\s*(\d{1,3}\.|\([A-E]\))", b[4]))]
    above = [b for b in above if b[3] <= cy0-2]
    tops = [b[3] for b in above if b[3] < cy0-30]
    if not tops: return None
    top = max(tops)
    if cy0-top < 40 or cy0-top > 520: return None
    reg = pymupdf.Rect(col0, top+2, col1, cy0-2)
    # reject if a question/option starts inside the region
    for b in text_blocks(page):
        r = pymupdf.Rect(b[:4])
        if reg.contains(r) and re.match(r"^\s*(\d{1,3}\.|\(?[A-E][.)])\s", b[4]): return None
    return reg

def do_captions(book, d, items):
    if book == "sou":
        idx = collections.defaultdict(list)
        for q in items:
            for m in re.finditer(r"Figures?\s+(\d+[-–]\d+)", q["q"]): idx[m.group(1).replace("–", "-")].append(q)
        rx = re.compile(r"^\s*Figure\s+(\d+[-–]\d+)")
        for page in d:
            for b in text_blocks(page):
                m = rx.match(b[4])
                if not m: continue
                key = m.group(1).replace("–", "-")
                for q in idx.get(key, []):
                    reg = figure_region(page, b)
                    if reg: save(page, reg, q, "caption")
    if book == "bra":
        idx = {}
        for q in items:
            t = WORDNUM.get(q["ch"].split()[-1].lower())
            if t: idx[(t, q["n"])] = q
        rx = re.compile(r"^\s*Figures? for Questions? (\d)\.(\d+)")
        for page in d:
            for b in text_blocks(page):
                m = rx.match(b[4])
                if not m: continue
                q = idx.get((int(m.group(1)), int(m.group(2))))
                if q:
                    reg = figure_region(page, b)
                    if reg: save(page, reg, q, "caption")

def locate(page, stem):
    words = stem.split()
    for k in (8, 6, 4):
        frag = " ".join(words[:k])
        if len(frag) < 12: continue
        r = page.search_for(frag)
        if r: return r[0]
    return None

def okey(r, W):
    col = 0 if (r.x0+r.x1)/2 < W/2 or r.width > 0.6*W else 1
    return (col, r.y0)

def do_positional(book, d, items, nextpage=True):
    pages = collections.defaultdict(list)
    for q in items: pages[q["pdfpage"]].append(q)
    for pno, pqs in pages.items():
        page = d[pno]; W = page.rect.width
        starts = [(r, q) for q in pqs for r in [locate(page, q["q"])] if r]
        rects = img_rects(page)
        merged = []
        for r in sorted(rects, key=lambda r: (r.y0, r.x0)):
            for m in merged:
                if (m + (-6, -6, 6, 6)).intersects(r): m |= r; break
            else: merged.append(pymupdf.Rect(r))
        for fig in merged:
            if fig.width < 70 or fig.height < 70: continue
            cand = [(r, q) for r, q in starts if okey(r, W) <= okey(fig, W)]
            if not cand: continue
            r, q = max(cand, key=lambda x: okey(x[0], W))
            if q["imgref"]: save(page, fig, q, "position")
        # figure on next page top, belonging to last question of this page that still has none
        if nextpage and pno+1 < len(d) and starts:
            r, q = max(starts, key=lambda x: okey(x[0], W))
            if q["imgref"] and not q.get("imgs"):
                nxt = d[pno+1]; W2 = nxt.rect.width
                others = [locate(nxt, o["q"]) for o in pages.get(pno+1, [])]
                first_q = min([okey(x, W2) for x in others if x] or [(9, 1e9)])
                for fig in img_rects(nxt):
                    if fig.width > 70 and fig.height > 70 and okey(fig, W2) < first_q:
                        save(nxt, fig, q, "nextpage")

for book, items in bybook.items():
    d = P.pdf(book)
    if book in ("sou", "bra"):
        ALLOW_VECTOR = book == "sou"
        do_captions(book, d, items)
        # questions that cite an image but got no caption match: positional fallback
        rest = [q for q in items if q["imgref"] and not q.get("imgs")]
        do_positional(book, d, rest, nextpage=False)
    else:
        do_positional(book, d, items)
    print(book, dict(stats), flush=True)

json.dump(qs, open(W+"/all_en.json", "w"), ensure_ascii=False)
print("questions with images:", sum(1 for q in qs if q.get("imgs")), "files:", len(os.listdir(OUT)))
