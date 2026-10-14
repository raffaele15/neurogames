"use strict";
/* ================= costanti ================= */
const USERS = [
  { name: "Raffaele", pw: "neuro" },
  { name: "Giorgia", pw: "pasticciotto" },
  { name: "Clara", pw: "tarantella" },
  { name: "Benedetta", pw: "ciotari" },
];
const MC = ["var(--m0)", "var(--m1)", "var(--m2)", "var(--m3)"];
const MIN = 60e3, H = 60 * MIN, D = 24 * H;
const INT = [10 * MIN, 1 * D, 3 * D, 7 * D, 14 * D, 30 * D]; // livelli Leitner 0..5
const REQUEUE_GAP = 4;
const PAGE = 40;
const CONTEST = new Date("2026-10-26T17:00:00+01:00"); // data e ora della gara (ora italiana)

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const ls = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { } },
  del(k) { try { localStorage.removeItem(k); } catch { } },
};
function fmtDur(ms) { if (ms < H) return Math.max(1, Math.round(ms / MIN)) + " min"; if (ms < D) return Math.round(ms / H) + " h"; const d = Math.round(ms / D); return d + (d === 1 ? " giorno" : " giorni"); }
function pct(a, b) { return b ? Math.round(a / b * 100) : 0; }
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0;[a[i], a[j]] = [a[j], a[i]]; } return a; }
function norm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }

/* ================= stato ================= */
let META = null, Q = [], QBYID = new Map(), CATNAME = {};
let me = null, uidx = 0;
let team = null;
let srs = {}, hist = [], settings = null;

const DEF_SETTINGS = { srcs: null, cats: null, lvls: [1, 2, 3], kind: "all", imgs: "all", hideMissing: true, secs: 30, extraTime: true, lang: "it", mode: "review", nq: 20 };
const key = k => `ng_${k}_${me}`;
function loadUser() {
  srs = ls.get(key("srs"), {}); hist = ls.get(key("hist"), []);
  settings = Object.assign({}, DEF_SETTINGS, ls.get(key("set"), {}));
  if (!settings.srcs) settings.srcs = Object.keys(META.books);
  if (!settings.cats) settings.cats = META.cats.map(c => c[0]);
}
const saveSrs = () => ls.set(key("srs"), srs);
const saveHist = () => ls.set(key("hist"), hist.slice(-6000));
const saveSettings = () => ls.set(key("set"), settings);
const saveTeam = () => ls.set("ng_team2", team);

/* ================= testo bilingue ================= */
function T(q, lang) {
  const it = lang === "it" && q.qi;
  return { q: it ? q.qi : q.q, o: it ? q.oi : q.o, e: it ? q.ei : q.e, it };
}
function srcLine(q) {
  const b = META.books[q.b]; return `${b.short} · ${esc(q.ch)} · p. ${esc(q.p)}`;
}

/* ================= SRS ================= */
function card(id) { return srs[id]; }
function isDue(id, now = Date.now()) { const c = srs[id]; return !!c && c.due <= now; }
function grade(id, ok) {
  const c = Object.assign({ box: 0, due: 0, seen: 0, ok: 0, streak: 0, lapses: 0, recovered: false }, srs[id]);
  c.seen++;
  if (ok) { c.ok++; c.streak++; c.box = Math.min(INT.length - 1, srs[id] ? c.box + 1 : 1); if (c.lapses > 0 && c.streak >= 2) c.recovered = true; }
  else { c.box = 0; c.streak = 0; c.lapses++; }
  c.due = Date.now() + INT[c.box]; c.last = ok ? 1 : 0; c.t = Date.now();
  srs[id] = c; saveSrs();
  hist.push([id, Date.now(), ok ? 1 : 0]); saveHist();
  return c;
}
function stateOf(id) {
  const c = srs[id];
  if (!c) return "new";
  if (c.box === 0) return "learning";
  if (c.box <= 2) return "short";
  if (c.box <= 4) return "mid";
  return "long";
}
const STATES = [["new", "Nuove", "var(--s0)"], ["learning", "In apprendimento", "var(--s1)"], ["short", "Breve termine", "var(--s2)"], ["mid", "Medio termine", "var(--s3)"], ["long", "Lungo termine", "var(--s4)"]];

/* ================= login ================= */
function showLogin() {
  $("#boot").hidden = true; $("#app").hidden = true; $("#login").hidden = false;
  let pick = ls.get("ng_lastuser", 0);
  const render = () => {
    $("#whoList").innerHTML = USERS.map((u, i) => `<button role="radio" aria-checked="${i === pick}" data-u="${i}"><span class="dot" style="background:${MC[i]}">${u.name[0]}</span>${esc(u.name)}</button>`).join("");
    $$("#whoList button").forEach(b => b.onclick = () => { pick = +b.dataset.u; render(); $("#pw").focus(); });
  };
  render();
  const go = () => {
    const u = USERS[pick];
    if ($("#pw").value.trim().toLowerCase() !== u.pw) { $("#loginMsg").textContent = "Password errata per " + u.name + "."; return; }
    ls.set("ng_session", u.name); ls.set("ng_lastuser", pick); $("#pw").value = ""; $("#loginMsg").textContent = "";
    enter(u.name);
  };
  $("#loginBtn").onclick = go;
  $("#pw").onkeydown = e => { if (e.key === "Enter") go(); };
}
function enter(name) {
  me = name; uidx = USERS.findIndex(u => u.name === name);
  loadUser();
  $("#login").hidden = true; $("#boot").hidden = true; $("#app").hidden = false;
  $("#meName").textContent = me; $("#meDot").textContent = me[0]; $("#meDot").style.background = MC[uidx];
  buildSettingsUI(); showTab(ls.get("ng_tab", "play")); renderAll();
}
$("#logout").onclick = () => { clearInterval(tick); ls.del("ng_session"); me = null; showLogin(); };

/* ================= impostazioni ================= */
function buildSettingsUI() {
  $("#srcList").innerHTML = Object.entries(META.books).map(([k, b]) => `<label><input type="checkbox" name="src" value="${k}" ${settings.srcs.includes(k) ? "checked" : ""}> <span>${esc(b.short)} <span class="muted">(${b.count})</span></span></label>`).join("");
  $("#catList").innerHTML = META.cats.map(([c, n]) => `<label><input type="checkbox" name="cat" value="${c}" ${settings.cats.includes(c) ? "checked" : ""}> <span>${esc(n)}</span></label>`).join("");
  $$('input[name=lvl]').forEach(i => i.checked = settings.lvls.includes(+i.value));
  $$('input[name=kind]').forEach(i => i.checked = i.value === settings.kind);
  $$('input[name=imgs]').forEach(i => i.checked = i.value === settings.imgs);
  $$('input[name=lang]').forEach(i => i.checked = i.value === settings.lang);
  $("#hideMissing").checked = settings.hideMissing; $("#secs").value = settings.secs; $("#extraTime").checked = settings.extraTime;
  $("#mode").value = settings.mode; $("#nq").value = settings.nq;
  $("#ladder").innerHTML = INT.map((ms, i) => i ? `<span class="chip plain">liv. ${i} <b>${fmtDur(ms)}</b></span>` : "").join("");
}
function readSettings() {
  settings.srcs = $$('input[name=src]:checked').map(i => i.value);
  settings.cats = $$('input[name=cat]:checked').map(i => i.value);
  settings.lvls = $$('input[name=lvl]:checked').map(i => +i.value);
  settings.kind = ($('input[name=kind]:checked') || {}).value || "all";
  settings.imgs = ($('input[name=imgs]:checked') || {}).value || "all";
  settings.lang = ($('input[name=lang]:checked') || {}).value || "it";
  settings.hideMissing = $("#hideMissing").checked;
  settings.secs = Math.max(5, +$("#secs").value || 30); settings.extraTime = $("#extraTime").checked;
  settings.mode = $("#mode").value; settings.nq = Math.max(1, +$("#nq").value || 20);
  saveSettings(); updateSetupInfo();
}
$("#settings").addEventListener("change", readSettings);
$("#mode").onchange = readSettings; $("#nq").onchange = readSettings;
$$("[data-all]").forEach(b => b.onclick = e => { e.preventDefault(); $$(`#${b.dataset.all} input`).forEach(i => i.checked = true); readSettings(); });
$$("[data-none]").forEach(b => b.onclick = e => { e.preventDefault(); $$(`#${b.dataset.none} input`).forEach(i => i.checked = false); readSettings(); });
$("#catMine").onclick = e => { e.preventDefault(); $$("#catList input").forEach(i => i.checked = team.map[i.value] === uidx); readSettings(); };

function filtered() {
  const S = settings, srcs = new Set(S.srcs), cats = new Set(S.cats), lv = new Set(S.lvls), rep = new Set([...reports(), ...hiddenQ()]);
  return Q.filter(q => !rep.has(q.id) && srcs.has(q.b) && cats.has(q.c) && lv.has(q.l)
    && (S.kind === "all" || (S.kind === "case" ? q.cs : !q.cs))
    && (S.imgs === "all" || (S.imgs === "only" ? q.im : !q.im))
    && !(S.hideMissing && q.mi));
}
function pool() {
  const base = filtered(), m = settings.mode;
  if (m === "mine") return base.filter(q => team.map[q.c] === uidx);
  if (m === "wrong") return base.filter(q => srs[q.id] && srs[q.id].lapses > 0);
  if (m === "new") return base.filter(q => !srs[q.id]);
  return base;
}
function updateSetupInfo() {
  const p = pool(), now = Date.now(), due = p.filter(q => isDue(q.id, now)).length, nw = p.filter(q => !srs[q.id]).length;
  $("#setupInfo").innerHTML = p.length ? `${p.length} domande · <span class="due">${due} da ripassare</span> · ${nw} nuove` : (settings.mode === "mine" ? "Non hai aree assegnate: assegnale nella scheda Aree." : "Nessuna domanda con queste impostazioni.");
  $("#start").disabled = !p.length;
  const allDue = Q.filter(q => isDue(q.id, now)).length;
  $("#dueChip").textContent = allDue ? `${allDue} da ripassare` : "In pari";
}
function buildSession(list, n) {
  const now = Date.now();
  const due = list.filter(q => isDue(q.id, now)).sort((a, b) => srs[a.id].box - srs[b.id].box || srs[a.id].due - srs[b.id].due);
  const fresh = shuffle(list.filter(q => !srs[q.id]));
  const later = list.filter(q => srs[q.id] && !isDue(q.id, now)).sort((a, b) => srs[a.id].due - srs[b.id].due);
  return [...due, ...fresh, ...later].slice(0, n);
}

/* ================= quiz ================= */
let S = null, tick = null;
function timeFor(q) {
  if (!settings.extraTime) return { t: settings.secs, x: 0 };
  const x = Math.min(90, Math.max(0, Math.round((q.w - 40) / 4)));
  return { t: settings.secs + x, x };
}
function startSession(list) {
  if (!list.length) return;
  S = { list, i: 0, ok: 0, answered: 0, miss: {}, repeats: {}, lang: settings.lang };
  showTab("play");
  $("#setup").hidden = true; $("#result").hidden = true; $("#quiz").hidden = false; showQ();
}
$("#start").onclick = () => { readSettings(); startSession(buildSession(pool(), settings.nq)); };

function imgsHTML(q) {
  if (!q.im) return "";
  return q.im.map(n => `<img src="img/${n}" alt="Figura della domanda" loading="lazy">`).join("");
}
function bindZoom(root) {
  root.querySelectorAll("img").forEach(i => i.onclick = () => { $("#zoomImg").src = i.src; $("#zoom").showModal(); });
}

/* ---- domande nascoste e segnalazioni (per utente) ---- */
const hiddenQ = () => ls.get(key("hidden"), []);
const reportsAll = () => ls.get(key("reports"), []);
function reports() { return reportsAll().map(r => r.id); }
const REPTYPES = [["text", "Testo troncato o illeggibile"], ["ans", "Risposta o spiegazione errata"], ["tr", "Traduzione sbagliata"], ["img", "Immagine sbagliata o mancante"], ["other", "Altro"]];
function actionsHTML(q) {
  const hid = hiddenQ().includes(q.id), rep = reportsAll().find(r => r.id === q.id);
  return `<div class="qactions" data-qa="${q.id}">
    <div class="row" style="gap:6px">
      <button class="ghost" data-act="hide">${hid ? "Mostra di nuovo" : "Non mostrare più"}</button>
      <button class="ghost" data-act="report">${rep ? "Segnalata ✓" : "Segnala domanda"}</button>
    </div>
    <form class="repform" hidden>
      <label class="lbl" for="rt-${q.id}">Problema</label>
      <select id="rt-${q.id}" name="type">${REPTYPES.map(([k, n]) => `<option value="${k}" ${rep && rep.type === k ? "selected" : ""}>${n}</option>`).join("")}</select>
      <label class="lbl" for="rn-${q.id}">Motivazione</label>
      <textarea id="rn-${q.id}" name="note" placeholder="Descrivi il problema (facoltativo)">${esc(rep ? rep.note : "")}</textarea>
      <div class="row"><button class="primary" type="submit">Salva segnalazione</button>${rep ? `<button type="button" data-act="unreport">Rimuovi segnalazione</button>` : ""}<button type="button" data-act="cancel">Annulla</button></div>
    </form>
    <div class="status"></div>
  </div>`;
}
function bindActions(root, onChange) {
  const box = root.querySelector("[data-qa]"); if (!box) return;
  const id = box.dataset.qa, form = box.querySelector("form"), st = box.querySelector(".status");
  const open = type => { form.hidden = false; if (type) form.type.value = type; form.note.focus(); };
  box.querySelectorAll("[data-act]").forEach(b => b.onclick = e => {
    e.preventDefault();
    const a = b.dataset.act;
    if (a === "hide") {
      const h = hiddenQ(), i = h.indexOf(id);
      if (i >= 0) { h.splice(i, 1); st.textContent = "La domanda tornerà nelle tue sessioni."; }
      else { h.push(id); st.textContent = "Non vedrai più questa domanda. Puoi ripristinarla dal Profilo."; }
      ls.set(key("hidden"), h); b.textContent = i >= 0 ? "Non mostrare più" : "Mostra di nuovo"; onChange && onChange();
    }
    if (a === "report") open();
    if (a === "reportimg") open("img");
    if (a === "cancel") form.hidden = true;
    if (a === "unreport") { ls.set(key("reports"), reportsAll().filter(r => r.id !== id)); box.outerHTML = actionsHTML(QBYID.get(id)); bindActions(root, onChange); onChange && onChange(); }
  });
  form.onsubmit = e => {
    e.preventDefault();
    const r = reportsAll().filter(x => x.id !== id);
    r.push({ id, type: form.type.value, note: form.note.value.trim(), t: Date.now(), user: me });
    ls.set(key("reports"), r);
    form.hidden = true; box.querySelector('[data-act="report"]').textContent = "Segnalata ✓";
    st.textContent = "Segnalazione salvata. La domanda è esclusa dalle tue sessioni; invia l'elenco dal Profilo.";
    onChange && onChange();
  };
}
function renderReports() {
  const r = reportsAll(), box = $("#repBox"); if (!box) return;
  box.hidden = !r.length;
  $("#repCount").textContent = r.length;
  const tn = Object.fromEntries(REPTYPES);
  $("#repList").value = r.map(x => { const q = QBYID.get(x.id); return `${x.id} [${tn[x.type] || x.type}] ${q ? META.books[q.b].short + " p." + q.p : ""}${x.note ? " — " + x.note : ""}`; }).join("\n");
  const h = hiddenQ(), hb = $("#hidBox");
  hb.hidden = !h.length; $("#hidCount").textContent = h.length;
  $("#hidList").innerHTML = h.map(id => QBYID.get(id)).filter(Boolean).map(q => qItem(q)).join("");
  bindItems($("#hidList"));
}
$("#repCopy").onclick = async () => {
  try { await navigator.clipboard.writeText(`Segnalazioni Neurogames di ${me}\n` + $("#repList").value); $("#repMsg").textContent = "Elenco copiato: mandalo a Raffaele."; }
  catch { $("#repList").select(); $("#repMsg").textContent = "Copia il testo selezionato."; }
};
$("#hidReset").onclick = () => { ls.set(key("hidden"), []); renderReports(); updateSetupInfo(); };
$("#zoom").onclick = () => $("#zoom").close();

function renderQText() {
  const q = S.list[S.i], t = T(q, S.lang);
  $("#stem").textContent = t.q;
  $$("#opts .opt").forEach((b, i) => b.querySelector(".tx").textContent = t.o[i]);
  $("#qLang").textContent = S.lang === "it" ? "EN" : "IT";
  $("#qLang").hidden = !q.qi;
  if (S.done) renderExpl();
}
function showQ() {
  const q = S.list[S.i]; const tf = timeFor(q);
  S.secs = tf.t; S.left = tf.t; S.done = false;
  const c = srs[q.id];
  $("#qMeta").textContent = `${S.i + 1} / ${S.list.length} · ${CATNAME[q.c]}${c ? " · liv. " + c.box : " · nuova"}`;
  $("#extraInfo").textContent = tf.x ? `Caso lungo: +${tf.x} s` : "";
  $("#opts").innerHTML = q.o.map((o, i) => `<button class="opt" data-i="${i}"><span class="k">${"ABCDEF"[i]}</span><span class="tx"></span></button>`).join("");
  $$("#opts .opt").forEach(b => b.onclick = () => answer(+b.dataset.i));
  $("#qImgs").innerHTML = imgsHTML(q); bindZoom($("#qImgs"));
  $("#after").hidden = true; $("#qActs").dataset.id = ""; renderQText(); drawClock();
  clearInterval(tick); tick = setInterval(() => { S.left -= .25; drawClock(); if (S.left <= 0) answer(-1); }, 250);
  window.scrollTo({ top: 0, behavior: "smooth" });
}
$("#qLang").onclick = () => { S.lang = S.lang === "it" ? "en" : "it"; renderQText(); };
function drawClock() { const l = Math.max(0, S.left); $("#clock").textContent = Math.ceil(l); $("#bar i").style.width = (l / S.secs * 100) + "%"; $("#bar").classList.toggle("low", l <= S.secs * .25); }
function renderExpl() {
  const q = S.list[S.i], t = T(q, S.lang), r = S.res;
  const head = r.i < 0 ? "Tempo scaduto." : r.ok ? "Corretto." : "Sbagliato.";
  const back = r.ok ? `Torna tra ${fmtDur(INT[r.c.box])} (livello ${r.c.box}).` : `Ricompare tra ${REQUEUE_GAP} domande e torna in scadenza tra 10 minuti.`;
  $("#expl").innerHTML = `<div><strong>${head}</strong> Risposta: <b>${"ABCDEF"[q.a]}</b> — ${esc(t.o[q.a])}</div>
    <div>${esc(t.e) || '<span class="muted">Nessuna spiegazione nel libro.</span>'}</div>
    ${t.it ? `<div class="hint">Traduzione automatica · usa il pulsante EN per l'originale.</div>` : ""}
    <div class="src">${srcLine(q)}</div><div class="src">${back}</div>`;
  if (!$("#qActs").dataset.id || $("#qActs").dataset.id !== q.id) { $("#qActs").innerHTML = actionsHTML(q); $("#qActs").dataset.id = q.id; bindActions($("#qActs"), updateSetupInfo); }
}
function answer(i) {
  if (S.done) return; S.done = true; clearInterval(tick);
  const q = S.list[S.i], ok = i === q.a; S.answered++;
  if (ok) S.ok++; else {
    S.miss[q.c] = (S.miss[q.c] || 0) + 1;
    const r = S.repeats[q.id] || 0;
    if (r < 2) { S.repeats[q.id] = r + 1; S.list.splice(Math.min(S.list.length, S.i + 1 + REQUEUE_GAP), 0, q); }
  }
  const c = grade(q.id, ok); S.res = { i, ok, c };
  $$("#opts .opt").forEach(b => { const k = +b.dataset.i; b.disabled = true; if (k === q.a) b.classList.add("right"); else if (k === i) b.classList.add("wrong"); });
  renderExpl(); $("#after").hidden = false; $("#next").focus({ preventScroll: true });
}
$("#next").onclick = () => { S.i++; S.i < S.list.length ? showQ() : finish(); };
$("#stop").onclick = finish;
document.addEventListener("keydown", e => {
  if ($("#quiz").hidden || e.target.matches("input,textarea,select") || $("#detail").open) return;
  if (!S.done && /^[1-6]$/.test(e.key)) { const b = $(`#opts .opt[data-i="${+e.key - 1}"]`); if (b) b.click(); }
  else if (S.done && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); $("#next").click(); }
});
function finish() {
  clearInterval(tick); $("#quiz").hidden = true; $("#setup").hidden = false; $("#result").hidden = false;
  const m = Object.entries(S.miss);
  $("#result").innerHTML = `<h2>Risultato: ${S.ok} / ${S.answered} (${pct(S.ok, S.answered)}%)</h2>${m.length ? `<div><div class="lbl">Errori per area</div><div class="row" style="margin-top:6px;gap:6px">${m.map(([c, n]) => `<span class="chip plain">${esc(CATNAME[c])} <b>${n}</b></span>`).join("")}</div></div>` : "<p>Nessun errore.</p>"}`;
  renderAll();
}

/* ================= dettaglio domanda (libreria, profilo) ================= */
let DQ = null, DL = "it", DD = false;
function openDetail(id) {
  DQ = QBYID.get(id); if (!DQ) return; DL = settings.lang; DD = false; $("#dActs").dataset.id = "";
  $("#dAfter").hidden = true; $("#dReveal").hidden = false; renderDetail(); $("#detail").showModal();
}
function renderDetail() {
  const q = DQ, t = T(q, DL), c = srs[q.id];
  $("#dMeta").textContent = `${CATNAME[q.c]}${c ? ` · liv. ${c.box} · ${c.ok}/${c.seen} corrette` : " · mai vista"}`;
  $("#dStem").textContent = t.q;
  $("#dImgs").innerHTML = imgsHTML(q); bindZoom($("#dImgs"));
  $("#dOpts").innerHTML = t.o.map((o, i) => `<button class="opt ${DD ? (i === q.a ? "right" : (i === DD.i ? "wrong" : "")) : ""}" data-i="${i}" ${DD ? "disabled" : ""}><span class="k">${"ABCDEF"[i]}</span><span>${esc(o)}</span></button>`).join("");
  $$("#dOpts .opt").forEach(b => b.onclick = () => { if (DD) return; const i = +b.dataset.i; DD = { i }; grade(q.id, i === q.a); revealDetail(); });
  $("#dLang").textContent = DL === "it" ? "EN" : "IT"; $("#dLang").hidden = !q.qi;
  if ($("#dActs").dataset.id !== q.id) { $("#dActs").innerHTML = actionsHTML(q); $("#dActs").dataset.id = q.id; bindActions($("#dActs"), () => renderAll(true)); }
  if (!$("#dAfter").hidden) fillDetailExpl();
}
function fillDetailExpl() {
  const q = DQ, t = T(q, DL);
  const head = DD && DD.i >= 0 ? (DD.i === q.a ? "<strong>Corretto.</strong> " : "<strong>Sbagliato.</strong> ") : "";
  $("#dExpl").innerHTML = `<div>${head}Risposta: <b>${"ABCDEF"[q.a]}</b> — ${esc(t.o[q.a])}</div><div>${esc(t.e)}</div>${t.it ? `<div class="hint">Traduzione automatica.</div>` : ""}<div class="src">${srcLine(q)}</div>`;
}
function revealDetail() { if (!DD) DD = { i: -2 }; $("#dAfter").hidden = false; $("#dReveal").hidden = true; renderDetail(); fillDetailExpl(); renderAll(true); }
$("#dReveal").onclick = revealDetail;
$("#dLang").onclick = () => { DL = DL === "it" ? "en" : "it"; renderDetail(); };
$("#dClose").onclick = () => $("#detail").close();
$("#detail").addEventListener("click", e => { if (e.target === $("#detail")) $("#detail").close(); });

function qItem(q, extra = "") {
  const t = T(q, settings.lang), st = stateOf(q.id), c = srs[q.id];
  const stl = { new: "nuova", learning: "in apprendimento", short: "breve", mid: "medio", long: "lungo" }[st];
  return `<button class="qi" data-q="${q.id}"><span class="ttl"><span class="tag">${esc(CATNAME[q.c])}</span><span class="tag">${stl}</span>${c && c.lapses ? `<span class="tag bad">${c.lapses} errori</span>` : ""}${q.im ? '<span class="tag">immagine</span>' : ""}${extra}<span class="muted" style="font-size:.8rem">${esc(META.books[q.b].short)} p.${esc(q.p)}</span></span><p>${esc(t.q)}</p></button>`;
}
function bindItems(root) { root.querySelectorAll("[data-q]").forEach(b => b.onclick = () => openDetail(b.dataset.q)); }

/* ================= libreria ================= */
let libShown = PAGE, libRes = [];
function renderLib() {
  const qq = norm($("#libQ").value.trim()), c = $("#libCat").value, b = $("#libSrc").value, st = $("#libState").value, im = $("#libImg").value, now = Date.now();
  const terms = qq.split(/\s+/).filter(Boolean);
  libRes = Q.filter(q => {
    if (c && q.c !== c) return false; if (b && q.b !== b) return false; if (im && !q.im) return false;
    if (st) {
      const s = srs[q.id];
      if (st === "new" && s) return false;
      if (st === "wrong" && !(s && s.lapses)) return false;
      if (st === "learning" && !(s && s.box === 0)) return false;
      if (st === "learned" && !(s && s.box >= 1 && s.streak >= 1)) return false;
      if (st === "due" && !isDue(q.id, now)) return false;
    }
    if (terms.length) { const h = q._s || (q._s = norm([q.q, ...q.o, q.qi || "", ...(q.oi || [])].join(" "))); return terms.every(t => h.includes(t)); }
    return true;
  });
  $("#libCount").textContent = `${libRes.length} domande`;
  $("#lib").innerHTML = libRes.slice(0, libShown).map(q => qItem(q)).join("") || `<div class="notice">Nessuna domanda trovata.</div>`;
  $("#libMore").hidden = libRes.length <= libShown; bindItems($("#lib"));
}
let libT = null;
$("#libQ").oninput = () => { clearTimeout(libT); libT = setTimeout(() => { libShown = PAGE; renderLib(); }, 200); };
["#libCat", "#libSrc", "#libState", "#libImg"].forEach(s => $(s).onchange = () => { libShown = PAGE; renderLib(); });
$("#libMore").onclick = () => { libShown += PAGE; renderLib(); };
$("#libTrain").onclick = () => { if (libRes.length) startSession(buildSession(libRes, settings.nq)); };

/* ================= aree ================= */
const inCat = c => Q.filter(q => q.c === c);
function renderCats() {
  const load = [0, 0, 0, 0], cnt = {}; Q.forEach(q => cnt[q.c] = (cnt[q.c] || 0) + 1);
  META.cats.forEach(([c]) => { const a = team.map[c]; if (a >= 0) load[a] += cnt[c] || 0; });
  const un = META.cats.filter(([c]) => !(team.map[c] >= 0)).reduce((s, [c]) => s + (cnt[c] || 0), 0);
  $("#load").innerHTML = USERS.map((u, i) => `<span class="chip"><span class="dot" style="background:${MC[i]}">${u.name[0]}</span>${esc(u.name)} <b>${load[i]}</b></span>`).join("") + (un ? `<span class="chip plain">Non assegnate <b>${un}</b></span>` : "");
  const now = Date.now();
  $("#cats").innerHTML = META.cats.map(([c, n]) => {
    const a = team.map[c], has = a >= 0, qs = Q.filter(q => q.c === c), due = qs.filter(q => isDue(q.id, now)).length;
    return `<div class="cat" style="--mc:${has ? MC[a] : "var(--line)"}"><h3>${esc(n)}</h3>
      <div><span class="cnt">${qs.length}</span> <span class="muted">domande</span>${due ? ` · <span class="due">${due} da ripassare</span>` : ""}</div>
      <select data-as="${c}" aria-label="Assegna ${esc(n)}"><option value="-1">Non assegnata</option>${USERS.map((u, i) => `<option value="${i}" ${a == i ? "selected" : ""}>${esc(u.name)}</option>`).join("")}</select>
      <button data-train="${c}">Allenati su quest'area</button></div>`;
  }).join("");
  $$("[data-as]").forEach(s => s.onchange = () => { team.map[s.dataset.as] = +s.value; saveTeam(); renderAll(); });
  $$("[data-train]").forEach(b => b.onclick = () => {
    const c = b.dataset.train, f = filtered().filter(q => q.c === c);
    startSession(buildSession(f.length ? f : inCat(c), settings.nq));
  });
}
$("#autoSplit").onclick = () => {
  const load = [0, 0, 0, 0], n = [0, 0, 0, 0];
  META.cats.map(([c]) => [c, inCat(c).length]).sort((a, b) => b[1] - a[1]).forEach(([c, k]) => {
    let b = 0; for (let i = 1; i < 4; i++) if (load[i] < load[b] || (load[i] === load[b] && n[i] < n[b])) b = i;
    team.map[c] = b; load[b] += k; n[b]++;
  });
  saveTeam(); renderAll();
};

/* ================= profilo ================= */
let meShown = PAGE;
function renderMe() {
  $("#meTitle").textContent = `Statistiche di ${me}`;
  const vals = Object.entries(srs);
  const answers = hist.length, correct = hist.filter(h => h[2]).length;
  const seenQ = vals.length;
  const learned = vals.filter(([, c]) => c.box >= 1 && c.streak >= 1).length;
  const recovered = vals.filter(([, c]) => c.recovered).length;
  const days = new Set(hist.map(h => new Date(h[1]).toDateString())).size;
  $("#kpis").innerHTML = [
    [answers ? pct(correct, answers) + "%" : "—", "risposte corrette"],
    [answers, "risposte date"], [`${seenQ}/${Q.length}`, "domande viste"],
    [learned, "apprese"], [recovered, "recuperate"], [days, "giorni di allenamento"],
  ].map(([b, s]) => `<div class="kpi"><b>${b}</b><span>${s}</span></div>`).join("");
  const cnt = { new: 0, learning: 0, short: 0, mid: 0, long: 0 };
  Q.forEach(q => cnt[stateOf(q.id)]++);
  $("#learnBar").innerHTML = STATES.map(([k, , col]) => cnt[k] ? `<i style="width:${cnt[k] / Q.length * 100}%;background:${col}" title="${k}"></i>` : "").join("");
  $("#learnLegend").innerHTML = STATES.map(([k, n, col]) => `<span class="chip plain"><span class="sw" style="background:${col}"></span>${n} <b>${cnt[k]}</b></span>`).join("");
  // per area: dallo storico
  const by = {}; hist.forEach(([id, , ok]) => { const q = QBYID.get(id); if (!q) return; const b = by[q.c] || (by[q.c] = [0, 0]); b[1]++; if (ok) b[0]++; });
  const rows = META.cats.filter(([c]) => by[c]).sort((a, b) => pct(...by[a[0]]) - pct(...by[b[0]]));
  $("#catStats").innerHTML = rows.length ? rows.map(([c, n]) => { const [o, t] = by[c]; return `<div class="cs"><span>${esc(n)}</span><span class="v">${pct(o, t)}% · ${o}/${t}</span><div class="bar"><i style="width:${pct(o, t)}%"></i></div></div>`; }).join("") : `<p class="muted">Ancora nessuna risposta.</p>`;
  renderMeList(); renderReports();
}
function renderMeList() {
  const v = $("#meList").value; let items = [];
  if (v === "hist") {
    items = hist.slice().reverse().slice(0, meShown).map(([id, t, ok]) => { const q = QBYID.get(id); return q ? qItem(q, `<span class="tag ${ok ? "ok" : "bad"}">${ok ? "✓ corretta" : "✗ sbagliata"}</span><span class="muted" style="font-size:.8rem">${new Date(t).toLocaleString("it-IT", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>`) : ""; });
    $("#meMore").hidden = hist.length <= meShown;
  } else {
    const ids = Object.entries(srs).filter(([, c]) => v === "wrong" ? c.last === 0 : v === "recovered" ? c.recovered : (c.box >= 1 && c.streak >= 1)).sort((a, b) => (b[1].t || 0) - (a[1].t || 0));
    items = ids.slice(0, meShown).map(([id]) => QBYID.get(id)).filter(Boolean).map(q => qItem(q));
    $("#meMore").hidden = ids.length <= meShown;
  }
  $("#meQs").innerHTML = items.join("") || `<p class="muted">Niente da mostrare.</p>`;
  bindItems($("#meQs"));
}
$("#meList").onchange = () => { meShown = PAGE; renderMeList(); };
$("#meMore").onclick = () => { meShown += PAGE; renderMeList(); };
$("#expProg").onclick = async () => {
  const data = JSON.stringify({ user: me, srs, hist, settings });
  try { await navigator.clipboard.writeText(data); $("#progMsg").textContent = "Progressi copiati: incollali sull'altro dispositivo con Importa."; }
  catch { $("#progBox").hidden = false; $("#progBox").value = data; $("#progBox").select(); $("#progMsg").textContent = "Copia il testo selezionato."; }
};
$("#impProg").onclick = () => {
  const box = $("#progBox");
  if (box.hidden || !box.value.trim()) { box.hidden = false; box.value = ""; box.focus(); $("#progMsg").textContent = "Incolla i progressi e premi di nuovo Importa."; return; }
  try {
    const d = JSON.parse(box.value);
    if (!d.srs) throw 0;
    for (const [id, c] of Object.entries(d.srs)) if (!srs[id] || (c.t || 0) > (srs[id].t || 0)) srs[id] = c;
    const seen = new Set(hist.map(h => h[0] + h[1])); (d.hist || []).forEach(h => { if (!seen.has(h[0] + h[1])) hist.push(h); });
    hist.sort((a, b) => a[1] - b[1]); saveSrs(); saveHist(); box.hidden = true; $("#progMsg").textContent = "Progressi uniti."; renderAll();
  } catch { $("#progMsg").textContent = "Testo non valido: incolla esattamente quello copiato."; }
};
$("#resetSrs").onclick = e => {
  const b = e.currentTarget; if (!b.dataset.c) { b.dataset.c = 1; b.textContent = "Conferma azzeramento"; return; }
  srs = {}; hist = []; saveSrs(); saveHist(); b.dataset.c = ""; b.textContent = "Azzera progressi"; renderAll();
};

/* ================= tab e render ================= */
function showTab(t) {
  $$(".tabbar [data-tab]").forEach(b => { const on = b.dataset.tab === t; b.setAttribute("aria-selected", on); $("#p-" + b.dataset.tab).hidden = !on; });
  ls.set("ng_tab", t); window.scrollTo(0, 0);
  if (t === "lib") renderLib(); if (t === "me") renderMe(); if (t === "cat") renderCats();
}
$$(".tabbar [data-tab]").forEach(b => b.onclick = () => showTab(b.dataset.tab));
function renderAll(light) {
  updateSetupInfo();
  const t = ls.get("ng_tab", "play");
  if (t === "lib" && !light) renderLib(); if (t === "me") renderMe(); if (t === "cat") renderCats();
}

/* ================= countdown ================= */
function drawCountdown() {
  let ms = CONTEST - Date.now(); const done = ms <= 0; ms = Math.max(0, ms);
  const d = Math.floor(ms / D), h = Math.floor(ms % D / H), m = Math.floor(ms % H / MIN), s = Math.floor(ms % MIN / 1000);
  const p = n => String(n).padStart(2, "0");
  const txt = done ? "È il giorno della gara!" : `${d} ${d === 1 ? "giorno" : "giorni"} · ${p(h)}:${p(m)}:${p(s)}`;
  $$("[data-cd]").forEach(e => e.textContent = txt);
}
drawCountdown(); setInterval(drawCountdown, 1000);

/* ================= installazione PWA ================= */
let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); deferredPrompt = e; $("#installBox").hidden = false; });
$("#installBtn").onclick = async () => { if (!deferredPrompt) return; deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; $("#installBox").hidden = true; };
if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => { });

/* ================= avvio ================= */
(async function boot() {
  try {
    META = await (await fetch("data/meta.json")).json();
    CATNAME = Object.fromEntries(META.cats);
    const parts = await Promise.all(Object.keys(META.books).map(k => fetch(`data/q-${k}.json`).then(r => r.json())));
    Q = parts.flat(); Q.forEach(q => QBYID.set(q.id, q));
    const def = await fetch("data/team.json").then(r => r.json()).catch(() => ({ map: {} }));
    team = ls.get("ng_team2", null) || { map: def.map || {} };
    const opt = (v, t) => `<option value="${v}">${esc(t)}</option>`;
    $("#libCat").innerHTML = opt("", "Tutte le aree") + META.cats.map(([c, n]) => opt(c, n)).join("");
    $("#libSrc").innerHTML = opt("", "Tutte le fonti") + Object.entries(META.books).map(([k, b]) => opt(k, b.short)).join("");
  } catch (e) {
    $("#boot").textContent = "Impossibile caricare le domande. Controlla la connessione e ricarica la pagina."; return;
  }
  const s = ls.get("ng_session", null);
  if (s && USERS.some(u => u.name === s)) enter(s); else showLogin();
})();
