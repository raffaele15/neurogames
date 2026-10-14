import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json, re, ctranslate2, sentencepiece as spm, time, os, sys
qs = json.load(open(W+"/all_en.json"))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(“\"])")
def sents(t):
    out=[]
    for s in SPLIT.split(t):
        while len(s) > 600:
            cut = s.rfind("; ", 0, 600)
            if cut < 200: cut = s.rfind(", ", 0, 600)
            if cut < 200: cut = 600
            out.append(s[:cut+1]); s = s[cut+1:].strip()
        if s: out.append(s)
    return out
segs = set()
for q in qs:
    for s in sents(q["q"]): segs.add(s)
    for o in q["opts"]: segs.add(o)
    for s in sents(q["expl"]): segs.add(s)
segs = sorted(segs, key=len)
cache_f = W+"/tr/cache.json"
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
todo = [s for s in segs if s not in cache]
print("segments", len(segs), "todo", len(todo), flush=True)
tr = ctranslate2.Translator(W+"/mt", device="cpu", compute_type="int8", inter_threads=1, intra_threads=os.cpu_count())
sp = spm.SentencePieceProcessor(model_file=W+"/mt/source.spm"); tp = spm.SentencePieceProcessor(model_file=W+"/mt/target.spm")
t0 = time.time(); B = 64
for i in range(0, len(todo), B):
    batch = todo[i:i+B]
    res = tr.translate_batch([sp.encode(s, out_type=str)[:400]+["</s>"] for s in batch], beam_size=2, max_batch_size=B,
                             repetition_penalty=1.1, max_decoding_length=512, no_repeat_ngram_size=0)
    for s, r in zip(batch, res): cache[s] = tp.decode_pieces(r.hypotheses[0])
    if (i//B) % 20 == 0:
        json.dump(cache, open(cache_f, "w"), ensure_ascii=False)
        el = time.time()-t0; done = i+len(batch)
        print(f"{done}/{len(todo)} {el:.0f}s eta {el/done*(len(todo)-done)/60:.0f}min", flush=True)
json.dump(cache, open(cache_f, "w"), ensure_ascii=False)
for q in qs:
    q["q_it"] = " ".join(cache[s] for s in sents(q["q"]))
    q["opts_it"] = [cache[o] for o in q["opts"]]
    q["expl_it"] = " ".join(cache[s] for s in sents(q["expl"]))
json.dump(qs, open(W+"/all_it.json", "w"), ensure_ascii=False)
print("DONE", time.time()-t0, flush=True)
