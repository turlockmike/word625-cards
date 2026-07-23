/* Picture Words — Fluent-Forever 625 Japanese vocab for kids.
 * Pedagogy (Mike, 2026-07-23): PICTURE on front -> produce kana + audio on back, NO English on card.
 * Offline-first flashcards with FSRS. Multi-profile, no login. Progress in localStorage
 * (source of truth). Optional cloud sync is additive via sync.js (off unless SYNC_ENDPOINT set).
 *
 * Card content is loaded at boot from two static JSON files (SW-cached for offline):
 *   media/img/images.json  -> [{en, slug, file, category, status, ...}]  (the images we have)
 *   data/words.json        -> [{id|en, kana, en, audio}]                 (kana + audio; DECK-gated)
 * v1 shows every image with status==='ok'. Until words.json lands (AnkiWeb deck quota-gated),
 * the back STUBS the kana/audio with a clear placeholder — the interaction shell, FSRS, flip,
 * and profile-select are the deliverable; content fills in on deck-day. */
(function(){
  "use strict";
  const $ = s => document.querySelector(s);
  const now = () => Date.now();

  // ---- card model (populated at boot) ----
  let CARDS = {};      // slug -> {slug, en, file, category, kana|null, audio|null, status}
  let ALLIDS = [];     // ordered introduction list (by category, then within)
  let TOTAL = 0;
  let dataReady = false;

  const IMG_DIR = 'media/img/';
  const AUDIO_DIR = 'media/audio/';

  async function loadJSON(url){
    try{ const r = await fetch(url, {cache:'no-cache'}); if(!r.ok) throw 0; return await r.json(); }
    catch(e){ return null; }
  }

  // Merge images.json (what pictures exist) with words.json (kana + audio, deck-gated).
  // Card id = slug (stable, filesystem-safe; both files key on en/slug).
  async function loadData(){
    const imgs = await loadJSON(IMG_DIR+'images.json') || [];
    const words = await loadJSON('data/words.json');    // null until the deck lands
    const byEn = {};
    if(Array.isArray(words)){
      words.forEach(w=>{ const k=(w.en||w.english||'').trim().toLowerCase(); if(k) byEn[k]=w; });
    }
    imgs.filter(e=>e && e.status==='ok' && e.file).forEach(e=>{
      const slug = (e.slug || e.en || '').trim().toLowerCase();
      if(!slug) return;
      const w = byEn[(e.en||slug).trim().toLowerCase()] || null;
      CARDS[slug] = {
        slug, en: e.en||slug, file: e.file, category: e.category||'',
        kana:  w ? (w.kana||null) : null,
        audio: w ? (w.audio||null) : null,
        status: e.status
      };
    });
    // ordered: keep images.json order (already category-grouped)
    const orderIdx = {}; let i=0;
    imgs.forEach(e=>{ const s=(e.slug||e.en||'').trim().toLowerCase(); if(s && !(s in orderIdx)) orderIdx[s]=i++; });
    ALLIDS = Object.keys(CARDS).sort((a,b)=>(orderIdx[a]??1e9)-(orderIdx[b]??1e9));
    TOTAL = ALLIDS.length;
    dataReady = true;
  }

  // ---- persistence (w625 namespace — isolated from the kana app on shared origins) ----
  const META_KEY = 'w625_meta_v1';
  const deckKey = pid => 'w625_deck_'+pid;
  function deviceId(){
    let d = localStorage.getItem('w625_device');
    if(!d){ d = 'd'+Math.random().toString(36).slice(2,10); localStorage.setItem('w625_device',d); }
    return d;
  }
  function loadMeta(){
    try{ return JSON.parse(localStorage.getItem(META_KEY)) || {active:null,profiles:[]}; }
    catch(e){ return {active:null,profiles:[]}; }
  }
  function saveMeta(m){ localStorage.setItem(META_KEY, JSON.stringify(m)); }
  function loadDeck(pid){
    try{ const d=JSON.parse(localStorage.getItem(deckKey(pid)));
         if(d&&d.cards&&d.introduced) return d; }catch(e){}
    return {cards:{}, introduced:[], reviews:0, updatedAt:now(), device:deviceId()};
  }
  function saveDeck(pid,d){ d.updatedAt=now(); d.device=deviceId();
    localStorage.setItem(deckKey(pid), JSON.stringify(d));
    if(window.KanaSync) window.KanaSync.onSave(pid,d); } // additive: no-op when sync off/unreachable

  // ---- app state ----
  let meta = loadMeta();
  let pid = meta.active;
  let deck = null;
  let session = [];        // in-memory queue of due cardIds
  let flipped = false;
  let showPicker = false;

  // ---- profile helpers ----
  function profileName(id){ const p=meta.profiles.find(p=>p.id===id); return p?p.name:'—'; }
  function newProfile(name){
    const id='p'+Math.random().toString(36).slice(2,8);
    meta.profiles.push({id,name}); meta.active=id; saveMeta(meta);
    pid=id; deck=loadDeck(pid); saveDeck(pid,deck);
    showPicker=false;
    introduceNext(3); // start everyone with 3 cards
    startSession();
    syncPull(); // same-named learner on another device? pull their existing progress
  }
  function switchProfile(id){ showPicker=false; meta.active=id; saveMeta(meta); pid=id; deck=loadDeck(pid); startSession(); syncPull(); }
  function deleteProfile(id){
    localStorage.removeItem(deckKey(id));
    meta.profiles = meta.profiles.filter(p=>p.id!==id);
    if(meta.active===id){ meta.active = meta.profiles[0] ? meta.profiles[0].id : null; }
    saveMeta(meta);
    pid = meta.active; deck = pid? loadDeck(pid) : null;
    if(pid && deck.introduced.length===0) introduceNext(3);
    render();
  }

  // ---- deck logic ----
  function introduceNext(n){
    let added=0;
    for(const id of ALLIDS){
      if(added>=n) break;
      if(!deck.cards[id]){
        deck.cards[id]={S:0,D:0,reps:0,lapses:0,last:0,due:now(),state:'new'};
        deck.introduced.push(id); added++;
      }
    }
    saveDeck(pid,deck);
    return added;
  }
  function dueIds(){
    const t=now();
    return deck.introduced.filter(id=>deck.cards[id] && deck.cards[id].due<=t)
      .sort((a,b)=>deck.cards[a].due-deck.cards[b].due);
  }
  function learnedCount(){
    return deck.introduced.filter(id=>{const c=deck.cards[id];return c && c.reps>0 && c.S>=1;}).length;
  }
  function startSession(){ session = dueIds(); flipped=false; render(); }

  function syncPull(){
    if(!window.KanaSync || !pid) return;
    const target=pid;
    window.KanaSync.pull(target).then(changed=>{
      if(changed && pid===target){ deck=loadDeck(pid); render(); }
    }).catch(()=>{});
  }

  function grade(g){ // g: 1 bad, 2 okay, 3 good
    const id=session[0]; if(!id) return;
    const c=deck.cards[id];
    const r=window.FSRS.schedule(c,g,now());
    Object.assign(c,r);
    deck.reviews=(deck.reviews||0)+1;
    saveDeck(pid,deck);
    session.shift();
    if(g===1){ const pos=Math.min(3,session.length); session.splice(pos,0,id); }
    flipped=false;
    if(session.length===0) session=dueIds();
    render();
  }

  // ================= RENDERING =================
  const main = $('#main');

  function render(){
    updateHeader();
    if(!dataReady){ renderLoading(); return; }
    if(TOTAL===0){ renderNoContent(); return; }
    if(!pid || showPicker){ renderPicker(); return; }
    if(session.length===0){ renderCaughtUp(); return; }
    renderCard(session[0]);
  }
  function updateHeader(){
    $('#profileName').textContent = pid ? profileName(pid) : '—';
    $('#totalCount').textContent = TOTAL;
    if(deck){
      $('#dueCount').textContent = dueIds().length;
      $('#learnedCount').textContent = learnedCount();
    }
  }

  function renderLoading(){
    main.innerHTML = `<div class="center"><h2>Loading…</h2></div>`;
  }
  function renderNoContent(){
    main.innerHTML = `<div class="center"><h2>No cards yet</h2>
      <p>Pictures haven't been added yet. Check back soon.</p></div>`;
  }

  function renderPicker(){
    const has = meta.profiles.length>0;
    const list = meta.profiles.map(p=>
      `<div class="pcard ${p.id===pid?'active':''}" data-pick="${p.id}">
         <span style="display:flex;align-items:center"><span class="av">${esc((p.name[0]||'?')).toUpperCase()}</span>${esc(p.name)}</span>
         <button class="del" data-del="${p.id}" title="remove">✕</button>
       </div>`).join('');
    main.innerHTML =
     `<div class="center">
        <h2>Who's studying?</h2>
        ${has ? `<div class="plist">${list}</div>` :
                `<p>No login, no password — just make a profile for each learner.</p>`}
        <div id="createWrap" style="${has?'display:none':''};display:flex;flex-direction:column;gap:10px;align-items:center;width:100%;max-width:300px">
          <input id="pname" placeholder="Type a name" maxlength="16"
            style="font-size:18px;padding:14px;border:2px solid #ece6df;border-radius:14px;width:100%;text-align:center">
          <button class="bigbtn" id="createP" style="width:100%">Start learning →</button>
        </div>
        ${has ? `<button class="bigbtn ghost" id="showCreate" style="max-width:300px;width:100%">➕ New profile</button>` : ''}
      </div>`;
    main.querySelectorAll('[data-pick]').forEach(el=>el.onclick=e=>{
      if(e.target.closest('[data-del]')) return;
      switchProfile(el.dataset.pick);
    });
    main.querySelectorAll('[data-del]').forEach(b=>b.onclick=e=>{
      e.stopPropagation();
      const id=b.dataset.del, nm=profileName(id);
      if(confirm('Remove '+nm+' and their progress from THIS device?')) deleteProfile(id);
    });
    const sc=$('#showCreate'); if(sc) sc.onclick=()=>{ $('#createWrap').style.display='flex'; sc.style.display='none'; $('#pname').focus(); };
    const cp=$('#createP'); if(cp){
      const go=()=>{ const n=$('#pname').value.trim(); if(n){ newProfile(n); render(); } };
      cp.onclick=go;
      $('#pname').addEventListener('keydown',e=>{ if(e.key==='Enter') go(); });
    }
  }

  function renderCaughtUp(){
    const remaining = TOTAL - deck.introduced.length;
    let soon=null;
    deck.introduced.forEach(id=>{const d=deck.cards[id].due; if(d>now()&&(soon===null||d<soon))soon=d;});
    const soonTxt = soon? `Next review ready ${relTime(soon)}.` : '';
    main.innerHTML =
     `<div class="center">
        <h2>🎉 All caught up!</h2>
        <p>${soonTxt||'Nice work.'} ${remaining>0?`You've learned ${deck.introduced.length} of ${TOTAL} words.`:'You\'ve unlocked every word!'}</p>
        ${remaining>0?`<button class="bigbtn" id="addBtn">➕ Add 3 new words</button>`:''}
        ${soon?`<button class="bigbtn ghost" id="reviewAhead">Review ahead anyway</button>`:''}
      </div>`;
    if(remaining>0) $('#addBtn').onclick=()=>{ introduceNext(3); startSession(); };
    if(soon) $('#reviewAhead') && ($('#reviewAhead').onclick=()=>{
      session=deck.introduced.slice().sort((a,b)=>deck.cards[a].due-deck.cards[b].due).slice(0,10); render(); });
  }

  function renderCard(id){
    const c=CARDS[id];
    const hasKana = !!c.kana;
    const answerInner = hasKana
      ? `<div class="kana">${esc(c.kana)}</div>
         <button class="audiobtn" id="audioBtn" ${c.audio?'':'disabled'}>🔊 Play</button>
         <div class="enhint">${esc(c.en)}</div>`
      : `<div class="kana stub">かな + 🔊 coming soon<br><span style="font-size:13px">(word list is being added)</span></div>
         <div class="enhint">${esc(c.en)}</div>`;
    main.innerHTML =
     `<div class="card">
        <div class="imgwrap">
          <img class="cardimg" id="cardImg" src="${esc(IMG_DIR+c.file)}" alt="">
        </div>
        <div id="answer">${answerInner}</div>
      </div>
      <div class="actions">
        <button class="flipbtn" id="flipBtn">Show answer →</button>
        <div class="grade" id="grade">
          <button class="b-bad"  data-g="1">Missed<span class="sub">again</span></button>
          <button class="b-okay" data-g="2">Close<span class="sub">soon</span></button>
          <button class="b-good" data-g="3">Got it<span class="sub">later</span></button>
        </div>
      </div>`;
    $('#flipBtn').onclick=()=>doFlip(id);
    $('#grade').querySelectorAll('button').forEach(b=>b.onclick=()=>grade(+b.dataset.g));
  }

  let curAudio=null;
  function playAudio(c){
    if(!c.audio) return;
    try{ if(curAudio){ curAudio.pause(); } curAudio = new Audio(AUDIO_DIR+c.audio); curAudio.play().catch(()=>{}); }
    catch(e){}
  }

  function doFlip(id){
    if(flipped) return; flipped=true;
    $('#answer').classList.add('show');
    $('#flipBtn').style.display='none';
    $('#grade').classList.add('show');
    const c=CARDS[id];
    const ab=$('#audioBtn');
    if(ab && c.audio){ ab.onclick=()=>playAudio(c); playAudio(c); } // auto-play once on reveal
  }

  // ================= SETTINGS SHEET =================
  $('#gearBtn').onclick=()=>openSheet();
  $('#profileBtn').onclick=()=>{ showPicker=true; render(); };
  $('#closeSheet').onclick=()=>$('#sheet').classList.remove('show');
  $('#sheet').addEventListener('click',e=>{ if(e.target.id==='sheet') e.target.classList.remove('show'); });

  function openSheet(){
    $('#s_learned').textContent = deck? learnedCount()+' / '+TOTAL : '0';
    $('#s_reviews').textContent = deck? (deck.reviews||0) : '0';
    injectProfileControls();
    $('#sheet').classList.add('show');
  }
  function injectProfileControls(){
    let box=$('#profileControls');
    if(!box){ box=document.createElement('div'); box.id='profileControls';
      const inner=$('.sheetinner'); inner.insertBefore(box, inner.children[1]); }
    box.innerHTML =
      `<div class="row"><span>Profile</span><span>
        <select id="profSel" style="font-size:14px;padding:6px;border-radius:8px;border:1px solid #e6ded4">
          ${meta.profiles.map(p=>`<option value="${p.id}" ${p.id===pid?'selected':''}>${esc(p.name)}</option>`).join('')}
        </select></span></div>
       <div class="row"><span>Add another learner</span>
        <button class="ghost" id="addProf" style="color:var(--accent)">+ New</button></div>`;
    $('#profSel').onchange=e=>{ switchProfile(e.target.value); $('#sheet').classList.remove('show'); };
    $('#addProf').onclick=()=>{ const n=prompt('New learner name:'); if(n&&n.trim()){ newProfile(n.trim()); $('#sheet').classList.remove('show'); render(); } };
  }

  // ---- backup / restore (manual cross-device bridge until cloud sync) ----
  $('#backupBtn').onclick=()=>{
    const payload={v:1, meta, decks:{}};
    meta.profiles.forEach(p=>payload.decks[p.id]=loadDeck(p.id));
    const code=b64(JSON.stringify(payload));
    $('#backupArea').value=code;
    if(navigator.clipboard) navigator.clipboard.writeText(code).catch(()=>{});
    $('#backupBtn').textContent='Copied ✓ — paste on the other device';
    setTimeout(()=>$('#backupBtn').textContent='Copy backup code',2500);
  };
  $('#restoreBtn').onclick=()=>{
    try{
      const p=JSON.parse(unb64($('#backupArea').value.trim()));
      if(!p||!p.decks||!p.meta) throw 0;
      const inMeta=p.meta;
      inMeta.profiles.forEach(prof=>{
        if(!meta.profiles.find(x=>x.id===prof.id)) meta.profiles.push(prof);
        const local=loadDeck(prof.id), incoming=p.decks[prof.id];
        if(!incoming) return;
        saveDeck(prof.id, mergeDeck(local,incoming));
      });
      meta.active=inMeta.active||meta.active; saveMeta(meta);
      pid=meta.active; deck=loadDeck(pid);
      $('#sheet').classList.remove('show'); startSession();
      alert('Progress restored & merged ✓');
    }catch(e){ alert('That code didn\'t look right — recopy it from the other device.'); }
  };
  function mergeDeck(a,b){
    const out={cards:{},introduced:[],reviews:Math.max(a.reviews||0,b.reviews||0)};
    const ids=new Set([...a.introduced,...b.introduced]);
    ids.forEach(id=>{
      const ca=a.cards[id], cb=b.cards[id];
      out.cards[id]= !ca?cb : !cb?ca : (cb.last>=ca.last? cb:ca);
      out.introduced.push(id);
    });
    out.introduced.sort((x,y)=>ALLIDS.indexOf(x)-ALLIDS.indexOf(y));
    return out;
  }

  $('#resetBtn').onclick=()=>{
    if(!confirm('Erase ALL progress for '+profileName(pid)+'? This cannot be undone.')) return;
    localStorage.removeItem(deckKey(pid)); deck=loadDeck(pid); introduceNext(3); startSession();
    $('#sheet').classList.remove('show');
  };

  // ---- utils ----
  function esc(s){ return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function b64(s){ return btoa(unescape(encodeURIComponent(s))); }
  function unb64(s){ return decodeURIComponent(escape(atob(s))); }
  function relTime(t){
    const m=Math.round((t-now())/60000);
    if(m<60) return 'in '+Math.max(1,m)+' min';
    const h=Math.round(m/60); if(h<24) return 'in '+h+' hr';
    return 'in '+Math.round(h/24)+' day'+(Math.round(h/24)>1?'s':'');
  }

  // ---- boot (async: load card data, then start) ----
  render(); // shows "Loading…"
  loadData().then(()=>{
    if(pid){ deck=loadDeck(pid); if(deck.introduced.length===0) introduceNext(3); startSession(); syncPull(); }
    else render();
  });

  window.Word625App={ loadDeck, saveDeck, loadMeta, mergeDeck, get pid(){return pid;}, get cards(){return CARDS;} };
})();
