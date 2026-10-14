import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import pymupdf, glob, re, json, collections, sys, os
os.chdir(_os.environ.get("NG_BOOKS") or (W+"/books" if _os.path.isdir(W+"/books") else _os.path.join(W, "..", "..", "quiz database")))
BOOKS = {
 "bra": ("Self-Assessment", "Neurology Self-Assessment (Bradley companion, 2016)"),
 "how": ("Howard", "Neurology Q&A Review — Howard (2017)"),
 "mcg": ("Neurology Board Review - Q", "Neurology Board Review Q&A — McGregor (2025)"),
 "sou": ("Souayah", "Neurology Examination and Board Review — Souayah (2017)"),
 "mayo": ("Mayo Clinic Neurology", "Mayo Clinic Neurology Board Review, 2e (2022)"),
 "mow": ("Illustrated", "Neurology Board Review: Illustrated Study Guide — Mowzoon (2007)"),
 "ess": ("Essential", "Essential Neurology Board Review Q&A (2026)"),
}
def pdf(k): return pymupdf.open([f for f in glob.glob("*.pdf") if BOOKS[k][0] in f][0])

def page_text_cols(p):
    W = p.rect.width
    bl = [b for b in p.get_text("blocks") if b[6] == 0 and b[4].strip()]
    def col(b):
        if b[2]-b[0] > 0.6*W: return 0
        return 1 if b[0] < W*0.48 else 2
    fulls = sorted([b for b in bl if col(b) == 0], key=lambda b: b[1])
    c1 = sorted([b for b in bl if col(b) == 1], key=lambda b: (b[1], b[0]))
    c2 = sorted([b for b in bl if col(b) == 2], key=lambda b: (b[1], b[0]))
    top = min([b[1] for b in c1+c2], default=1e9)
    seq = [b for b in fulls if b[1] <= top]+c1+c2+[b for b in fulls if b[1] > top]
    return "\n".join(b[4] for b in seq)

COLS = {"sou", "mayo", "mcg", "ess"}
def lines_of(k, doc):
    """list of (pdf_page_index, line)"""
    out = []
    for i, p in enumerate(doc):
        t = page_text_cols(p) if k in COLS else p.get_text()
        for ln in t.split("\n"):
            s = ln.replace("­", "-").replace("ﬁ", "fi").replace("ﬂ", "fl").replace("​", "")
            s = re.sub(r"ﬁ\s", "fi", s); s = re.sub(r"ﬂ\s", "fl", s)
            s = s.replace("\t", " ").strip()
            if s: out.append((i, s))
    # drop running headers: frequent short lines at page top/bottom
    bypage = collections.defaultdict(list)
    for i, s in out: bypage[i].append(s)
    edge = collections.Counter()
    for i, ls in bypage.items():
        for s in ls[:3]+ls[-2:]: edge[re.sub(r"\d+", "#", s)] += 1
    bad = {s for s, c in edge.items() if c > 10 and len(s) < 110 and not re.match(r"^\(?[A-Fa-f][.)]", s)}
    res = []
    for i, s in out:
        n = re.sub(r"\d+", "#", s)
        ls = bypage[i]
        is_edge = s in ls[:3] or s in ls[-2:]
        if re.match(r"^\d{1,3}\.\s", s) or re.match(r"^[IVX]+\.\d", s): res.append((i, s)); continue
        if re.fullmatch(r"(QUESTIONS|ANSWERS|Questions|Answers|Answers and Explanations|Answers of Questions)", s): res.append((i, s)); continue
        if re.match(r"^#+\s*•", n) or re.search(r"•\s*#+$", n): continue
        if (is_edge and n in bad) or re.fullmatch(r"[#\s]+", n) or "版权" in s: continue
        res.append((i, s))
    return res

def join(parts):
    t = ""
    for p in parts:
        if t.endswith("-") and p[:1].islower(): t = t[:-1]+p
        elif t: t += " "+p
        else: t = p
    return re.sub(r"\s+", " ", t).strip()

# ---------- generic question stream parser ----------
def parse_qs(lines, qre, ore, upper=True, inline_ans=None):
    qs = []; cur = None; last = 0; field = None; seenq = set(); grp = 0
    def close():
        if cur: qs.append(cur)
    for pg, s in lines:
        m = qre.match(s)
        if m:
            n = int(m.group(1))
            if n == 1 and cur is not None and (cur["opts"] or cur["in_expl"]) and (last >= 3 or 1 in seenq) and not inline_ans:
                grp += 1; seenq = set()
            if n not in seenq and ((cur is None and n <= 5) or (cur is not None and abs(n-last) <= 10 and (cur["opts"] or cur["in_expl"]))):
                seenq.add(n); close()
                cur = {"n": n, "g": grp, "page": pg, "stem": [m.group(2)] if m.group(2) else [], "opts": [], "ans": None, "expl": [], "in_expl": False}
                last = n; field = "stem"; continue
        if cur is None: continue
        if inline_ans:
            ma = inline_ans.match(s)
            if ma:
                cur["ans"] = ma.group(1).upper(); cur["in_expl"] = True; field = "expl"; continue
            if cur["in_expl"]:
                if re.match(r"^(References?|Suggested Reading)\b", s): field = "ref"; continue
                if field == "expl" and s != "Explanation": cur["expl"].append(s)
                continue
        mo = ore.match(s)
        if mo:
            L = mo.group(1).upper(); exp = chr(65+len(cur["opts"]))
            if L == exp:
                cur["opts"].append([mo.group(2)]); field = "opt"; continue
        if field == "stem": cur["stem"].append(s)
        elif field == "opt" and cur["opts"]:
            # limit continuation to avoid swallowing captions
            prev = cur["opts"][-1][-1]
            joined = " ".join(cur["opts"][-1])
            cont = (re.match(r"^[a-z(\[0-9–-]", s) or joined.count("(") > joined.count(")") or
                    re.match(r"^(Syndrome|Disease|Disorder|Sclerosis|Syndromes|Type|Palsy|Atrophy|Dystrophy|Myopathy|Neuropathy|Encephalopathy)\b", s) or re.search(r"([-,/]|\b(with|of|and|or|the|to|in|for|a|an|by|on|at|from|vs\.?))$", prev))
            if cont and sum(len(x) for x in cur["opts"][-1]) < 320 and not re.match(r"^(Figure|Fig\.|Table|\(Reproduced|Courtesy)", s):
                cur["opts"][-1].append(s)
            else: field = None
    close()
    return qs

def parse_ans(lines, are, multiline_letter=None):
    """returns {n: (letter, expl)}"""
    res = {}; cur = None; last = 0; grp = 0
    for pg, s in lines:
        m = are.match(s)
        if m:
            n = int(m.group(1))
            if n == 1 and last >= 3: grp += 1
            n = (grp, n)
            if n not in res and (cur is None or n != cur[0]) and ((cur is None and n[1] <= 5) or (cur is not None and (n[1] == 1 or abs(n[1]-last) <= 10))):
                if cur: res[cur[0]] = cur
                L = m.group(2)
                cur = [n, L.upper() if L else None, [m.group(3)] if m.lastindex >= 3 and m.group(3) else []]
                last = n[1]; continue
        if cur is None: continue
        if cur[1] is None and multiline_letter:
            ml = multiline_letter.match(s)
            if ml: cur[1] = ml.group(1).upper(); rest = ml.group(2) if ml.lastindex and ml.lastindex >= 2 else ""
            if ml:
                if rest: cur[2].append(rest)
                continue
        if re.match(r"^(References?|Suggested Reading|REFERENCES)\s*$", s): cur.append("stop"); continue
        if cur[-1] == "stop": continue
        cur[2].append(s)
    if cur: res[cur[0]] = cur
    return {n: (v[1], join(v[2] if isinstance(v[2], list) else [])) for n, v in res.items()}

def toc(doc): return [(l, t.strip(), p-1) for l, t, p in doc.get_toc()]

def section_slices(lines, start, end):
    return [(p, s) for p, s in lines if start <= p < end]

def find_line(lines, start, end, rx):
    for idx, (p, s) in enumerate(lines):
        if start <= p < end and re.match(rx, s): return idx
    return None

out = []
def emit(book, chapter, qs, answers, doc, default_cat=None):
    ok = 0
    for q in qs:
        a = answers.get((q["g"], q["n"])) if answers is not None else (q["ans"], join(q["expl"]))
        if not a or not a[0] or len(q["opts"]) < 2: continue
        idx = ord(a[0])-65
        if idx >= len(q["opts"]): continue
        stem = join(q["stem"]); opts = [join(o) for o in q["opts"]]
        if len(stem) < 8: continue
        out.append({"book": book, "chapter": chapter, "n": q["n"] + 1000*q["g"], "q": stem, "opts": opts, "ans": idx,
                    "expl": a[1], "pdfpage": q["page"], "page": doc[q["page"]].get_label() or str(q["page"]+1),
                    "defcat": default_cat})
        ok += 1
    return ok

stats = {}
# ---------- Bradley ----------
def do_bra():
    d = pdf("bra"); L = lines_of("bra", d); T = toc(d)
    tests = [(t, p) for l, t, p in T if l == 1 and t.startswith("Test")]
    tests.append(("Index", [p for l, t, p in T if t == "Index"][0]))
    n = 0
    for i in range(0, len(tests)-1, 2):
        qt, qp = tests[i]; at, ap = tests[i+1]; end = tests[i+2][1]
        qs = parse_qs(section_slices(L, qp, ap), re.compile(r"^(\d{1,3})\.\s*(.*)$"), re.compile(r"^([A-F])\.\s+(.*)$"))
        an = parse_ans(section_slices(L, ap, end), re.compile(r"^(\d{1,3})\.\s+([A-F])\.?(?:\s+(.*))?$"))
        n += emit("bra", qt.replace(" Questions", ""), qs, an, d)
    stats["bra"] = n

def chapters_with_qa(T, qname=r"^Questions$", aname=r"^Answers"):
    chs = []
    lev1 = [(t, p) for l, t, p in T if l == 1]
    for i, (t, p) in enumerate(lev1):
        end = lev1[i+1][1] if i+1 < len(lev1) else 10**6
        sub = [(tt, pp) for l, tt, pp in T if l >= 2 and p <= pp < end]
        q = [pp for tt, pp in sub if re.match(qname, tt, re.I)]
        a = [pp for tt, pp in sub if re.match(aname, tt, re.I)]
        if q and a: chs.append((t, q[0], a[0], end, p))
    return chs

def do_how():
    d = pdf("how"); L = lines_of("how", d); T = toc(d); n = 0
    for t, qp, ap, end, cp in chapters_with_qa(T):
        ai = find_line(L, ap, ap+1, r"^.*Answers")  # answers start page
        qs = parse_qs(section_slices(L, qp, ap+1), re.compile(r"^(\d{1,3})\.\s+(.*)$"), re.compile(r"^([A-F])\.\s+(.*)$"))
        an = parse_ans(section_slices(L, ap, end), re.compile(r"^(\d{1,3})\.\s+([A-F])\.\s*(.*)$"))
        n += emit("how", re.sub(r"^Chapter \d+:\s*", "", t), qs, an, d)
    stats["how"] = n

def do_sou():
    d = pdf("sou"); L = lines_of("sou", d); T = toc(d); n = 0
    for t, qp, ap, end, cp in chapters_with_qa(T, aname=r"^Answers"):
        qp = cp
        # answers may start mid-page: split at the answers header line
        ai = find_line(L, ap, ap+2, r"^Answers( and Explanations| of Questions)?$")
        ql = [x for x in L if qp <= x[0] <= ap]; al = [x for x in L if ap <= x[0] < end]
        if ai is not None:
            ql = [x for j, x in enumerate(L) if qp <= x[0] and j < ai]
            al = [x for j, x in enumerate(L) if j > ai and x[0] < end]
        qs = parse_qs(ql, re.compile(r"^(\d{1,3})\.\s*(.*)$"), re.compile(r"^\(([A-E])\)\s*(.*)$"))
        an = parse_ans(al, re.compile(r"^(\d{1,3})\.\s*\(([A-E])\)\s*(.*)$"))
        n += emit("sou", re.sub(r"^\d+\.\s*", "", t), qs, an, d)
    stats["sou"] = n

def do_mcg():
    d = pdf("mcg"); L = lines_of("mcg", d); T = toc(d); n = 0
    lev1 = [(i, t, p) for i, (l, t, p) in enumerate(T) if l == 1 and re.match(r"^\d+\.", t)]
    for j, (i, t, p) in enumerate(lev1):
        end = lev1[j+1][2] if j+1 < len(lev1) else len(d)
        sub = T[i+1:(lev1[j+1][0] if j+1 < len(lev1) else len(T))]
        ap = [pp for l, tt, pp in sub if tt.strip().upper() == "ANSWERS"]
        if not ap: ap = [pp for l, tt, pp in sub if l == 2 and tt.strip().upper() != "QUESTIONS"]
        if not ap: continue
        ap = ap[0]
        ql = [x for x in L if p <= x[0] < ap]; al = [x for x in L if ap <= x[0] < end]
        qs = parse_qs(ql, re.compile(r"^(\d{1,3})\.\s*(.*)$"), re.compile(r"^([A-F])\.\s+(.*)$"))
        an = parse_ans(al, re.compile(r"^(\d{1,3})\.\s+([A-F])(?:\s+(.*))?$"))
        n += emit("mcg", re.sub(r"^\d+\.\s*", "", t).strip().title(), qs, an, d)
    stats["mcg"] = n

ROMAN = r"([IVX]+)"
def do_mayo():
    d = pdf("mayo"); L = lines_of("mayo", d); T = toc(d); n = 0
    secs = sorted([(t, p) for l, t, p in T if l == 1 and t.startswith("Section")], key=lambda x: x[1])
    qa = sorted([p for l, t, p in T if l == 2 and t.startswith("Questions and Answers")])
    sugg = sorted([p for l, t, p in T if l == 2 and t.startswith("Suggested Reading")])
    for qp in qa:
        end = min([s for s in sugg if s >= qp] or [qp+20])+1
        sec = [t for t, p in secs if p <= qp][-1]
        ai = None
        for j, (p, s) in enumerate(L):
            if qp <= p < end and s == "Answers": ai = j; break
        if ai is None: continue
        ql = [x for j, x in enumerate(L) if qp <= x[0] and j < ai]
        al = [x for j, x in enumerate(L) if j > ai and x[0] < end]
        qs = parse_qs(ql, re.compile(r"^[IVX]+\.(\d{1,3})\.\s*(.*)$"), re.compile(r"^([a-e])\.\s+(.*)$"))
        an = parse_ans(al, re.compile(r"^[IVX]+\.(\d{1,3})\.\s*(?:Answer\s+([a-e])\.?)?\s*(.*)$"),
                       multiline_letter=re.compile(r"^Answer\s+([a-e])\.?\s*(.*)$"))
        n += emit("mayo", re.sub(r"^Section [IVX]+:\s*", "", sec).replace("- ", "-"), qs, an, d)
    stats["mayo"] = n

def do_mow():
    d = pdf("mow"); L = lines_of("mow", d); T = toc(d); n = 0
    chs = [(t, p) for l, t, p in T if l == 1 and t.startswith("Chapter")]
    chs.append(("Index", [p for l, t, p in T if t == "Index"][0]))
    for i in range(len(chs)-1):
        t, p = chs[i]; end = chs[i+1][1]
        qi = None; ai = None
        for j, (pg, s) in enumerate(L):
            if p <= pg < end:
                if s == "QUESTIONS": qi = j
                if s == "ANSWERS" and qi is not None: ai = j
        if qi is None or ai is None: continue
        ql = L[qi+1:ai]; al = [x for x in L[ai+1:] if x[0] < end]
        qs = parse_qs(ql, re.compile(r"^(\d{1,3})\.\s*(.*)$"), re.compile(r"^([a-e])\.\s*(.*)$"))
        an = parse_ans(al, re.compile(r"^(\d{1,3})\.\s*Answer:\s*([a-e])\.?\s*(.*)$"))
        n += emit("mow", re.sub(r"^Chapter \d+\.\s*", "", t).title(), qs, an, d)
    stats["mow"] = n

def do_ess():
    d = pdf("ess"); L = lines_of("ess", d); T = toc(d); n = 0
    chs = [(t, p) for l, t, p in T if l == 1 and re.match(r"^\d+:", t)]
    chs.append(("Index", len(d)))
    for i in range(len(chs)-1):
        t, p = chs[i]; end = chs[i+1][1]
        qs = parse_qs(section_slices(L, p, end), re.compile(r"^(\d{1,3})\.\s+(.*)$"), re.compile(r"^([A-F])\.\s+(.*)$"),
                      inline_ans=re.compile(r"^Correct answers?:\s*([A-F])\b"))
        n += emit("ess", re.sub(r"^\d+:\s*", "", t), qs, None, d)
    stats["ess"] = n

if __name__ == "__main__":
    which = sys.argv[1:] or list(BOOKS)
    for k in which: globals()["do_"+k]()
    print(stats)
    json.dump(out, open(W+"/raw_%s.json" % "_".join(which), "w"), ensure_ascii=False)
