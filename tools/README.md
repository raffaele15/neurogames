# tools/ — rigenerare le domande dai PDF

Pipeline Python che estrae le domande dai 7 libri, le pulisce, abbina le immagini, traduce in italiano e scrive `../data/` e `../img/`.

## Requisiti

```bash
pip install pymupdf pillow ctranslate2 sentencepiece
```

- **PDF**: non sono nel repo (copyright). Gli script li cercano in `tools/books/`, altrimenti in `../../quiz database/` (cioè `Code projects/Neurogames/quiz database`), oppure nel percorso indicato da `NG_BOOKS`. I nomi dei file devono restare quelli originali.
- **Modello di traduzione** (solo per frasi nuove): `tools/mt/` = Helsinki-NLP `opus-mt-tc-big-en-it` convertito per CTranslate2:
  ```bash
  pip install transformers torch sentencepiece
  ct2-transformers-converter --model Helsinki-NLP/opus-mt-tc-big-en-it --output_dir mt --quantization int8
  cp ~/.cache/huggingface/hub/models--Helsinki-NLP--opus-mt-tc-big-en-it/snapshots/*/{source,target}.spm mt/
  ```
  Se nessuna frase è cambiata il modello non serve: in `run_all.sh` si può saltare `translate.py` solo se esiste già `all_it.json` aggiornato; altrimenti serve il modello.

## Uso

```bash
cd tools
bash run_all.sh        # tutto, ~2 minuti
```

Ordine dei passi (vedi `run_all.sh`):

| Script | Cosa fa | Output |
|---|---|---|
| `parse.py <libro>` | parser per libro (PyMuPDF, colonne, numerazione, opzioni su più righe) | `raw_<libro>.json` |
| `build.py` | pulizia testo, id stabili (hash), categoria (24 aree), livello 1–3, parole | `all_en.json` |
| `images2.py` | estrae e abbina figure (didascalie per Souayah/Bradley, posizione per gli altri) | `../img/*.webp`, campo `imgs` |
| `fixlig.py w` | ricongiunge "fi"/"fl" spezzati (legature del PDF di Howard) | `all_en.json` |
| `fixhdr.py w` | toglie intestazioni di pagina finite nel testo (McGregor, Howard, Souayah, Essential) | `all_en.json` |
| `translate.py` | traduzione per frase con cache | `all_it.json`, `tr/cache.json` |
| `export.py` | scrive i JSON dell'app, esclude `review/broken.json`, applica `review/decisions.json`, elimina immagini non usate. **Non tocca `data/team.json`** | `../data/q-*.json`, `../data/meta.json` |

Altri: `extract.py` salva il testo grezzo dei PDF in `txt2/` per ispezionarlo; `sheets.py` crea fogli di controllo immagini in `review/` (per decidere cosa tenere); `check.py` stima per capitolo se le risposte corrispondono alle spiegazioni (utile dopo modifiche al parser).

File di stato (versionati):
- `review/decisions.json`: `{id: [indici immagini da tenere]}` (revisione manuale)
- `review/broken.json`: id esclusi (domande fuse con la successiva, risposte perse)
- `tr/cache.json`: traduzioni già fatte (inglese → italiano)

Variabili: `NG_WORK` (cartella di lavoro, default `tools/`), `NG_SITE` (sito, default `..`), `NG_BOOKS` (PDF).
