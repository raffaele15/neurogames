# Neurogames

Web app per allenarsi a squadre al torneo di neurologia. Funziona su GitHub Pages, da computer e da telefono, e si può installare come app.

## Struttura

- `index.html`, `style.css`, `app.js`: l'app
- `sw.js`, `manifest.webmanifest`, `icons/`: installazione e uso offline
- `data/q-*.json`: domande per libro (testo originale inglese e traduzione automatica italiana)
- `data/meta.json`: libri e aree
- `data/team.json`: assegnazione delle aree ai quattro membri (creata dall'app con *Assegna aree*)
- `img/`: immagini delle domande (WebP compresso)
- `tools/`: script per rigenerare le domande dai PDF (vedi `tools/README.md`)
- `CLAUDE.md`: contesto per continuare a sviluppare l'app con Claude

## Pubblicazione

1. In GitHub Desktop: commit di tutti i file e *Push origin*.
2. Su github.com → repository → Settings → Pages → *Deploy from a branch* → `main` / root.
3. Dopo un paio di minuti l'app è su `https://<utente>.github.io/<repository>/`.

## Installazione sul telefono

- Android (Chrome): menu ⋮ → *Installa app*.
- iPhone (Safari): Condividi → *Aggiungi alla schermata Home*.

## Ripasso

Sistema Leitner a 6 livelli: una risposta sbagliata riporta la domanda al livello 0 (ricompare dopo 4 domande e torna in scadenza dopo 10 minuti); una giusta la fa salire di un livello (1, 3, 7, 14, 30 giorni). I progressi sono salvati nel browser di ciascuno e si possono copiare da un dispositivo all'altro dal Profilo.
