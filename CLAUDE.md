# Neurogames — contesto per Claude

App web (PWA statica, GitHub Pages) per allenare una squadra di 4 specializzandi al torneo di neurologia a quiz (risposta multipla a tempo) del **26/10/2026 ore 17:00**. Utente/proprietario: Raffaele. Lingua dell'interfaccia e delle risposte: italiano.

## Squadra e login
Raffaele, Giorgia, Clara, Benedetta. Login = scelta nome + password, scritte di proposito in chiaro in `app.js` (`USERS`): è un gioco, va bene così.

## File
- `index.html`, `style.css` (token colore, tema chiaro/scuro), `app.js` (tutta la logica, JS vanilla, nessun build step).
- `sw.js`: service worker, network-first per i file app, cache-first per `img/`. **Incrementare `VERSION` (ora `ng-v7`) a ogni modifica di file app.**
- `manifest.webmanifest`, `icons/` (logo = `icons/logo.png`).
- `data/q-{bra,how,mcg,sou,mayo,mow,ess}.json`: domande per libro. Campi: `id, b`(libro) `, ch`(capitolo) `, p`(pagina) `, c`(area) `, l`(livello 1–3) `, w`(parole) `, q, o`(opzioni) `, a`(indice risposta) `, e`(spiegazione) `, cs`(caso clinico) `, im`(immagini) `, mi`(immagine mancante) `, qi, oi, ei`(traduzioni IT).
- `data/meta.json`: libri e 24 aree. `data/team.json`: `{"assignments": {"<area>": "<Nome>"}}` (accetta anche il vecchio `{"map": {area: indice}}`).
- `img/`: WebP compressi. `tools/`: pipeline per rigenerare i dati dai PDF (vedi `tools/README.md`).

## Funzioni principali (app.js)
- Ripasso Leitner: `INT = [10min,1g,3g,7g,14g,30g]`; sbagliata → livello 0 e ricompare dopo 4 domande (`REQUEUE_GAP`). Stati: nuove, in apprendimento, breve/medio/lungo termine; "recuperate" = sbagliate poi 2 giuste di fila.
- Sessione: modalità (ripasso consigliato, tutte, sbagliate, nuove) + casella **"Solo le mie aree"**; impostazioni comprimibili (libri, aree, livello, tipo, immagini, secondi, tempo extra per casi lunghi: +1 s ogni 4 parole oltre 40, max 90 s, lingua).
- Traduzione IT con pulsante per vedere l'originale; lingua predefinita selezionabile.
- Libreria con filtro per area e ricerca su domanda+risposte.
- Profilo: statistiche totali/per area, storico, liste cliccabili, segnalazioni ("Segnala domanda" con motivo; copia elenco), "Non mostrare più" (ripristinabile).
- Aree: sola lettura del proprietario di ogni area; editor **"Assegna aree"** genera il JSON e lo condivide (share sheet come .txt / testo, fallback copia). Raffaele lo salva come `data/team.json` e fa push.
- Countdown alla gara nel login e nella banda in alto.
- Dati utente in `localStorage`, chiavi `ng_<key>_<utente>` (srs, hist, set, hidden, reports) + `ng_session`, `ng_lastuser`, `ng_tab`. Nessun backend (scelta voluta). Su iPhone l'app installata ha storage separato da Safari: si usa "Copia/Importa progressi" dal Profilo.

## Lavoro sui dati
- 5533 domande (20 escluse in `tools/review/broken.json` perché fuse con la successiva). Duplicati tra libri tenuti di proposito.
- Problemi già risolti: legature fi/fl spezzate (PDF Howard), intestazioni di pagina nel testo, opzioni troncate su più righe, immagini abbinate male (revisione in `tools/review/decisions.json`).
- Per correggere una singola domanda basta modificare il JSON in `data/`; per correzioni sistematiche modificare `tools/` e rilanciare `tools/run_all.sh` (serve avere i PDF in `Code projects/Neurogames/quiz database`).

## Pubblicazione
Commit e push su `main` (Raffaele usa GitHub Desktop) → GitHub Pages si aggiorna. Testare a 390 px di larghezza (mobile) senza errori in console.

## Preferenze di Raffaele
Risposte brevi, in italiano.
