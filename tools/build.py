import os as _os
W = _os.environ.get("NG_WORK", _os.path.dirname(_os.path.abspath(__file__)))
SITE = _os.environ.get("NG_SITE", _os.path.join(W, ".."))
import json, re, hashlib, collections, glob
CATS = [
 ("anatomia", "Neuroanatomia e localizzazione"),
 ("neuroscienze", "Neuroscienze di base e neurofarmacologia"),
 ("neurofisio", "Neurofisiologia (EEG, EMG, PE)"),
 ("neuroradio", "Neuroradiologia"),
 ("neuropat", "Neuropatologia"),
 ("cerebrovascolare", "Malattie cerebrovascolari"),
 ("neurocritica", "Neurocritica, emergenze e trauma"),
 ("epilessia", "Epilessia"),
 ("sonno", "Disturbi del sonno"),
 ("cefalee", "Cefalee e dolore"),
 ("movimento", "Disturbi del movimento e cervelletto"),
 ("demielinizzanti", "Demielinizzanti e neuroimmunologia"),
 ("infettivo", "Neuroinfettivologia"),
 ("neuroonco", "Neuro-oncologia"),
 ("comportamentale", "Neurologia comportamentale e demenze"),
 ("psichiatria", "Psichiatria e dipendenze"),
 ("neuromuscolare", "Neuromuscolare, SNP e midollo"),
 ("autonomico", "Sistema nervoso autonomo"),
 ("neurooft", "Neuro-oftalmologia, otoneurologia e nervi cranici"),
 ("metabolico", "Disturbi metabolici, tossici e carenziali"),
 ("sistemiche", "Neurologia delle malattie sistemiche"),
 ("genetica", "Neurogenetica, sviluppo e neurocutanee"),
 ("pediatria", "Neuropediatria"),
 ("etica", "Etica, statistica e pratica clinica"),
]
# chapter name -> category (None = mixed, classify by keywords)
CHMAP = [
 (r"sleep", "sonno"), (r"epilep|seizure", "epilessia"), (r"headache|pain", "cefalee"),
 (r"vascular|stroke|cerebrovascular", "cerebrovascolare"),
 (r"critical|emergency|intensive|trauma", "neurocritica"),
 (r"movement|cerebell", "movimento"), (r"demyelinat|neuroimmun|inflammatory|paraneoplastic", "demielinizzanti"),
 (r"infect", "infettivo"), (r"oncolog|neoplas", "neuroonco"),
 (r"behavioral|dementia|neurocognitive", "comportamentale"),
 (r"psychiatr|substance", "psichiatria"),
 (r"neuromuscular|peripheral nervous|muscle|neuromuscular transmission|spinal cord|anterior horn", "neuromuscolare"),
 (r"autonomic", "autonomico"), (r"ophthalm|otolog|cranial nerves|retina|optic", "neurooft"),
 (r"metabolic|toxic|nutrition|vitamin|neurotoxic|inborn", "metabolico"),
 (r"systemic|general medical", "sistemiche"),
 (r"genetic|congenital|neurocutaneous|embryolog|developmental", "genetica"),
 (r"pediatric", "pediatria"), (r"neurophysiolog", "neurofisio"),
 (r"neuropatholog", "neuropat"), (r"radiolog", "neuroradio"),
 (r"neurochemistry|neuropharmacolog", "neuroscienze"), (r"neuroanatomy", "anatomia"),
]
MIXED = r"^(test |neuroscience and neuroanatomy|central nervous system|anatomy and physiology|localization|basic principles of neuroscience|pediatrics$|neurophysiology, epilepsy)"
KW = {
 "cerebrovascolare": r"stroke|infarct|tia\b|carotid|aneurysm|hemorrhage|thromb|embol|cavernoma|arteriovenous|moyamoya|cadasil|dissection|thromboly|tpa\b|tenecteplase|anticoag|watershed|lacun",
 "epilessia": r"seizure|epilep|antiseizure|antiepilep|status epilepticus|spike|levetiracetam|valpro|lamotrigin|carbamazepin|phenytoin|absence|infantile spasm",
 "sonno": r"sleep|narcolep|insomnia|apnea|cataplex|circadian|parasomn|restless legs|\brem\b|melatonin|orexin|hypocretin",
 "cefalee": r"headache|migraine|cluster|trigeminal neuralgia|neuralgia|cephalalg|triptan|pain\b|opioid|analges",
 "movimento": r"parkinson|tremor|dystoni|chorea|huntington|ballism|myoclon|tic\b|tics|tourette|ataxia|cerebell|levodopa|dopamine agonist|wilson|multiple system atrophy|progressive supranuclear|basal ganglia|deep brain",
 "demielinizzanti": r"multiple sclerosis|demyelinat|optic neuritis|neuromyelitis|aquaporin|\bmog\b|adem\b|natalizumab|ocrelizumab|interferon beta|autoimmune encephalitis|nmda receptor|paraneoplastic|oligoclonal",
 "infettivo": r"mening|encephalitis|abscess|hiv|aids|herpes|syphilis|lyme|tubercul|toxoplasm|cryptococ|prion|creutzfeldt|virus|viral|bacteri|fung|parasit|cysticerc|jc virus|pml\b|rabies|polio|leprosy|tetanus|botulism",
 "neuroonco": r"tumor|glioma|glioblastoma|astrocytoma|meningioma|oligodendroglioma|ependymoma|medulloblastoma|lymphoma|metasta|schwannoma|neoplas|craniopharyng|pituitary adenoma|chemotherap|radiotherap|idh\b|mgmt",
 "comportamentale": r"dementia|alzheimer|aphasia|amnesia|memory|frontotemporal|lewy|cognitive|apraxia|agnosia|neglect|mini mental|neuropsycholog|gerstmann|anosognosia|prosopagnosia",
 "psichiatria": r"depress|schizophren|bipolar|anxiety|psychos|personality|antidepress|antipsychot|ssri\b|lithium|autism|adhd|obsessive|ptsd|alcohol|cocaine|opioid use|substance|panic|eating disorder|conversion|somatic symptom|factitious|delirium",
 "neuromuscolare": r"neuropathy|myopathy|myasthen|lambert|guillain|cidp|amyotrophic|\bals\b|motor neuron|muscular dystrophy|myotonic|myositis|radiculopathy|plexus|plexopathy|nerve conduction|median nerve|ulnar|radial nerve|peroneal|sciatic|carpal tunnel|charcot-marie|spinal muscular atrophy|neuromuscular junction|acetylcholine receptor|creatine kinase|muscle biopsy|spinal cord|myelopathy|cauda equina|syringomyelia",
 "autonomico": r"autonomic|sympathetic|parasympathetic|orthostatic|dysautonom|baroreflex|sweat|horner|postural tachycardia|pots\b",
 "neurooft": r"pupil|nystagmus|diplopia|visual field|optic nerve|papilledema|retina|ocular|oculomotor|abducens|trochlear|ophthalmopleg|internuclear|saccade|vertigo|vestibular|hearing|tinnitus|cochlear|meniere|facial nerve|bell palsy|cranial nerve|hemianopia|scotoma",
 "metabolico": r"vitamin|b12|thiamine|wernicke|copper|hepatic encephalopathy|uremi|hyponatremia|hypoglycem|lead\b|mercury|arsenic|toxic|intoxication|poisoning|mitochondrial|lysosomal|storage disease|leukodystrophy|porphyria|metabolic|inborn error|phenylketon|organic acid|urea cycle",
 "sistemiche": r"lupus|sarcoid|vasculitis|behcet|sjogren|celiac|cardiac surgery|transplant|renal failure|hypothyroid|hyperthyroid|pregnan|diabet",
 "genetica": r"autosomal|x-linked|trinucleotide|gene\b|mutation|chromosom|trisomy|deletion|neurofibromatosis|tuberous sclerosis|sturge|von hippel|neurocutaneous|neural tube|migration|lissenceph|holoprosenceph|chiari|embryo|imprinting|mitochondrial dna",
 "pediatria": r"infant|neonat|newborn|child|toddler|month-old|boy\b|girl\b|preterm|cerebral palsy|developmental delay|febrile seizure",
 "neurofisio": r"\beeg\b|electroencephal|\bemg\b|electromyograph|evoked potential|nerve conduction|polysomnograph|f wave|h reflex|repetitive stimulation|fibrillation potential",
 "neuroradio": r"\bmri\b|\bct\b|imaging|t2-weighted|t1-weighted|flair|diffusion-weighted|angiograph|contrast enhancement",
 "neuroscienze": r"neurotransmitter|receptor|channel|glutamate|gaba|acetylcholine|dopamine|serotonin|norepinephrine|membrane potential|action potential|synap|axonal transport|pharmacokinet|enzyme|metabolized|cytochrome|half-life|mechanism of action",
 "anatomia": r"lesion|localiz|nucleus|tract|fasciculus|thalam|internal capsule|brainstem|medulla|pons|midbrain|cortex|lobe|artery supplies|dermatome|innervat|cerebrospinal fluid|ventric|hypothalam|limbic|hippocamp|amygdala",
 "etica": r"informed consent|ethic|autonomy|beneficence|maleficence|handoff|sensitivity|specificity|predictive value|bias\b|confidential|capacity|jcaho|joint commission|statistic|odds ratio|relative risk|number needed",
 "neurocritica": r"intracranial pressure|herniation|coma|brain death|traumatic brain|concussion|subdural|epidural|intubat|ventilat|icu\b|glasgow|cardiac arrest|hypotherm",
 "neuropat": r"histolog|biopsy shows|inclusion|pathologic|neuropatholog|plaques|tangles|rosenthal|negri|lewy bod|stain",
}
KWC = {k: re.compile(v, re.I) for k, v in KW.items()}

def chap_cat(ch):
    c = ch.lower()
    if re.match(MIXED, c): return None
    for rx, cat in CHMAP:
        if re.search(rx, c): return cat
    return None

def kw_cat(text, fallback):
    sc = collections.Counter()
    for k, rx in KWC.items():
        n = len(rx.findall(text))
        if n: sc[k] += n
    # imaging/anatomy/physiology are generic: down-weight
    for k in ("neuroradio", "anatomia", "neuroscienze", "pediatria"):
        sc[k] *= 0.6
    return sc.most_common(1)[0][0] if sc else fallback

BOOKMETA = {
 "bra": "Jordan, Mayans, Soileau — Neurology Self-Assessment (Bradley), 2016",
 "how": "Howard — Neurology Q&A Review, 2017",
 "mcg": "McGregor et al. — Neurology Board Review Q&A, 2e, 2025",
 "sou": "Souayah — Neurology Examination and Board Review, 3e, 2017",
 "mayo": "Mayo Clinic Neurology Board Review, 2e, 2022",
 "mow": "Mowzoon, Flemming — Neurology Board Review: Illustrated Study Guide, 2007",
 "ess": "Essential Neurology Board Review Q&A, 2026",
}
FALLBACK = {"bra": "anatomia", "mayo": "anatomia", "how": "anatomia", "sou": "anatomia", "mow": "neuroscienze"}

def clean(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    s = re.sub(r"(\w)- (\w)", lambda m: m.group(1)+m.group(2) if m.group(2).islower() else m.group(0), s)
    s = s.replace(" ,", ",").replace(" .", ".")
    return s

IMG_RX = re.compile(r"\b(figure|fig\.|shown|image|picture|photograph|depicted|illustrated|arrow|scan below|mri below|following (?:mri|ct|eeg|emg|image)|eeg|biopsy (?:is shown|shows)|tracing)\b", re.I)
NEG_RX = re.compile(r"\b(not|except|false|least likely|incorrect|untrue)\b", re.I)

def build():
    raw = []
    for f in sorted(glob.glob(W+"/raw_*.json")):
        if re.search(r"raw_[a-z]+\.json$", f): raw += json.load(open(f))
    out = []; seen = set()
    for r in raw:
        q = clean(r["q"]); opts = [clean(o) for o in r["opts"]]
        # options swallowing captions: trim at 'Figure ' etc.
        opts = [re.split(r"\s(?:Figure|Fig\.)\s?\d", o)[0].strip() for o in opts]
        CUT = r"\s(?:ANSWERS|QUESTIONS|Answers and Explanations|Answers|Base Knowledge|Explanation|Correct answer|References?\b|Suggested Reading|\d{1,3}\.\s+\(?[A-Ea-e]\)?[.\s]|[A-Z][A-Z ,&\-]{12,}\b)"
        opts = [re.split(CUT, o)[0].strip() for o in opts]
        expl = clean(r["expl"])
        expl = re.split(r"\s(?:References?|Suggested Reading)\s?:?\s(?=[A-Z])", expl)[0]
        idb = hashlib.md5(f'{r["book"]}|{r["chapter"]}|{r["n"]}'.encode()).hexdigest()[:8]
        qid = f'{r["book"]}-{idb}'
        if qid in seen: continue
        seen.add(qid)
        cc = chap_cat(r["chapter"])
        cat = cc or kw_cat(q+" "+" ".join(opts)+" "+expl[:400], FALLBACK.get(r["book"], "anatomia"))
        words = len((q+" "+" ".join(opts)).split())
        case = bool(re.match(r"^(An?|The)\s+\d{1,3}[- ](year|month|week|day)", q)) or bool(re.search(r"\b\d{1,3}-(year|month)-old\b", q))
        imgref = bool(IMG_RX.search(q))
        diff = 1 + (1 if case and words > 90 else 0) + (1 if NEG_RX.search(q) else 0) + (1 if len(opts) >= 5 else 0) + (1 if imgref else 0)
        lvl = 1 if diff <= 1 else 2 if diff <= 2 else 3
        out.append({"id": qid, "book": r["book"], "ch": r["chapter"], "n": r["n"], "page": r["page"], "pdfpage": r["pdfpage"],
                    "cat": cat, "case": case, "lvl": lvl, "w": words, "imgref": imgref,
                    "q": q, "opts": opts, "ans": r["ans"], "expl": expl})
    return out

if __name__ == "__main__":
    qs = build()
    json.dump(qs, open(W+"/all_en.json", "w"), ensure_ascii=False)
    print(len(qs))
    print(collections.Counter(q["cat"] for q in qs).most_common())
    print(collections.Counter(q["lvl"] for q in qs), sum(q["case"] for q in qs), sum(q["imgref"] for q in qs))
