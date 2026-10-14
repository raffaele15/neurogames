#!/usr/bin/env bash
# Rigenera le domande dai PDF. Eseguire dalla cartella tools/ (vedi README.md).
set -euo pipefail
cd "$(dirname "$0")"
for b in bra how mcg sou mayo mow ess; do python3 parse.py $b; done   # PDF -> raw_<libro>.json
python3 build.py          # raw -> all_en.json (pulizia, categorie, livello)
python3 images2.py        # immagini -> ../img/*.webp + campo imgs
python3 fixlig.py w       # parole spezzate dopo legature fi/fl (Howard)
python3 fixhdr.py w       # intestazioni di pagina finite nel testo
python3 translate.py      # traduzione IT (usa tr/cache.json, traduce solo frasi nuove)
python3 export.py         # scrive ../data/q-*.json e meta.json, elimina immagini non usate
