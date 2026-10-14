import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json, re, os, sys, collections
sys.path.insert(0, W)
from build import CATS, BOOKMETA
src = W+"/all_it.json" if os.path.exists(W+"/all_it.json") else W+"/all_en.json"
qs = json.load(open(src))
BROKEN = set(json.load(open(W+"/review/broken.json")))
qs = [q for q in qs if q["id"] not in BROKEN]
imgs = {q["id"]: q.get("imgs") for q in json.load(open(W+"/all_en.json"))}
DEC = json.load(open(W+"/review/decisions.json"))
for k, keep in DEC.items():
    if imgs.get(k): imgs[k] = [imgs[k][i] for i in keep if i < len(imgs[k])] or None
SHORT = {"bra": "Bradley Self-Assessment", "how": "Howard Q&A", "mcg": "McGregor Q&A", "sou": "Souayah",
         "mayo": "Mayo Clinic Board Review", "mow": "Mowzoon Illustrated", "ess": "Essential Neurology Q&A"}
STRONG = re.compile(r"\b(figure|fig\.|is shown|are shown|shown (?:here|below|above)|depicted|image below|arrow|following (?:image|picture|photograph|mri|ct|eeg|tracing)|this (?:image|picture|photograph|tracing))\b", re.I)
os.makedirs(SITE+"/data", exist_ok=True)
by = collections.defaultdict(list); used = set()
for q in qs:
    im = imgs.get(q["id"])
    o = {"id": q["id"], "b": q["book"], "ch": q["ch"], "p": q["page"], "c": q["cat"], "l": q["lvl"], "w": q["w"],
         "q": q["q"], "o": q["opts"], "a": q["ans"], "e": q["expl"]}
    if q["case"]: o["cs"] = 1
    if im: o["im"] = im; used.update(im)
    elif STRONG.search(q["q"]): o["mi"] = 1
    if q.get("q_it"): o["qi"] = q["q_it"]; o["oi"] = q["opts_it"]; o["ei"] = q["expl_it"]
    by[q["book"]].append(o)
order = ["mcg", "ess", "mayo", "sou", "how", "bra", "mow"]
meta = {"books": {k: {"title": BOOKMETA[k], "short": SHORT[k], "count": len(by[k])} for k in order if by[k]},
        "cats": [list(c) for c in CATS], "total": len(qs), "translated": src.endswith("it.json")}
for k, v in by.items():
    json.dump(v, open(f"{SITE}/data/q-{k}.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(meta, open(SITE+"/data/meta.json", "w"), ensure_ascii=False, indent=1)
# team.json non viene toccato (lo gestisce l'app con 'Assegna aree')
print(src, len(qs), {k: len(v) for k, v in by.items()}, "missing-img:", sum(1 for v in by.values() for o in v if o.get("mi")))

# remove image files no longer referenced
import os as _os
for f in _os.listdir(SITE+"/img"):
    if f not in used: _os.remove(SITE+"/img/"+f)
print("images kept:", len(used))
