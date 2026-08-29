/* Meilleurs. : comportements partages de toutes les pages.
   Chaque bloc sort silencieusement si son point d'ancrage est absent :
   le meme fichier sert donc la home, le sommaire et les pages d'article. */
var REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Date du jour
(function(){
  var d = new Date();
  var el = document.getElementById('today');
  if(el) el.textContent = d.toLocaleDateString('fr-FR', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
})();

// Horloge temps réel, service en cours
(function(){
  var el = document.getElementById('clock');
  if(!el) return;
  function p(x){ return String(x).padStart(2,'0'); }
  function tick(){
    var n = new Date();
    el.textContent = p(n.getHours()) + ':' + p(n.getMinutes()) + ':' + p(n.getSeconds());
  }
  tick();
  setInterval(tick, 1000);
})();

// Ticker : duplication pour boucle infinie
(function(){
  var t = document.getElementById('ticker');
  if(t) t.innerHTML += t.innerHTML;
})();

// Burger overlay
(function(){
  var burger = document.getElementById('burger');
  var overlay = document.getElementById('overlay');
  var close = document.getElementById('close-overlay');
  if(!burger || !overlay) return;
  burger.addEventListener('click', function(){ overlay.classList.add('open'); overlay.setAttribute('aria-hidden','false'); overlay.removeAttribute('inert'); burger.setAttribute('aria-expanded','true'); });
  function shut(){ overlay.classList.remove('open'); overlay.setAttribute('aria-hidden','true'); overlay.setAttribute('inert',''); burger.setAttribute('aria-expanded','false'); }
  if(close) close.addEventListener('click', shut);
  overlay.querySelectorAll('a').forEach(function(a){ a.addEventListener('click', shut); });
})();

// Reveal on scroll : .rv isolés, puis groupes .stagger (délai par index)
(function(){
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
  }, {threshold:.12});
  document.querySelectorAll('.rv').forEach(function(el){
    if(!el.closest('.stagger')) io.observe(el);
  });
  var sio = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      var kids = e.target.querySelectorAll('.rv');
      kids.forEach(function(k, i){
        if(REDUCE){ k.classList.add('in'); }
        else setTimeout(function(){ k.classList.add('in'); }, i * 85);
      });
      sio.unobserve(e.target);
    });
  }, {threshold:.1});
  document.querySelectorAll('.stagger').forEach(function(g){ sio.observe(g); });
})();

// Mot rotatif du H1 : restaurants → bistrots → tables → comptoirs
(function(){
  var w = document.getElementById('rot-word');
  if(!w || REDUCE) return;
  var words = ['restaurants', 'bistrots', 'tables', 'comptoirs'];
  var i = 0;
  setInterval(function(){
    w.classList.add('out');
    setTimeout(function(){
      i = (i + 1) % words.length;
      w.firstElementChild.textContent = words[i];
      w.classList.add('pre');
      void w.offsetHeight;
      w.classList.remove('pre', 'out');
    }, 420);
  }, 2600);
})();

// Compteurs : notes du palmarès (0,0 → 19,4) et stats bistrot (0 → 312)
(function(){
  function fmt(v, dec){ return dec ? v.toFixed(1).replace('.', ',') : String(Math.round(v)); }
  function count(el, to, dur, dec){
    if(REDUCE){ el.textContent = fmt(to, dec); return; }
    var t0 = null;
    function step(ts){
      if(t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      var e = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(to * e, dec);
      if(p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var notes = document.querySelectorAll('.rank-meta .why b[data-v]');
  var stats = document.querySelectorAll('.bis-stats .st b[data-v]');
  if(!REDUCE){
    notes.forEach(function(b){ b.textContent = '0,0'; });
    stats.forEach(function(b){ b.textContent = '0'; });
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      if(e.target.id === 'rank-list') notes.forEach(function(b){ count(b, parseFloat(b.dataset.v), 1200, true); });
      else stats.forEach(function(b){ count(b, parseFloat(b.dataset.v), 1400, false); });
      io.unobserve(e.target);
    });
  }, {threshold:.25});
  var rl = document.getElementById('rank-list');
  var bs = document.querySelector('.bis-stats');
  if(rl) io.observe(rl);
  if(bs) io.observe(bs);
})();

// Palmarès : image en arche qui suit le curseur
(function(){
  var list = document.getElementById('rank-list');
  var float_ = document.getElementById('float-img');
  if(!list || !float_) return;
  var img = float_.querySelector('img');
  list.querySelectorAll('.rank-row').forEach(function(row){
    row.addEventListener('mouseenter', function(){
      img.src = row.dataset.img;
      img.onerror = function(){ this.onerror = null; this.src = row.dataset.fallback; };
      float_.classList.add('on');
    });
    row.addEventListener('mouseleave', function(){ float_.classList.remove('on'); });
  });
  document.addEventListener('mousemove', function(e){
    if(!float_.classList.contains('on')) return;
    float_.style.left = (e.clientX + 30) + 'px';
    float_.style.top = (e.clientY - 160) + 'px';
  });
})();

// Carrousel villes : dérive automatique (~25 px/s), flèches, drag, pauses
(function(){
  var sc = document.getElementById('dest-scroll');
  if(!sc) return;
  var prev = document.getElementById('dprev'), next = document.getElementById('dnext');
  var step = 340, pauseUntil = 0, down = false, sx = 0, sl = 0;
  function hold(ms){ pauseUntil = performance.now() + ms; }
  if(prev) prev.addEventListener('click', function(){ sc.scrollBy({left:-step, behavior:'smooth'}); hold(2400); });
  if(next) next.addEventListener('click', function(){ sc.scrollBy({left:step, behavior:'smooth'}); hold(2400); });
  sc.addEventListener('mousedown', function(e){ down = true; sc.classList.add('grabbing'); sx = e.pageX; sl = sc.scrollLeft; });
  window.addEventListener('mouseup', function(){ if(down){ down = false; sc.classList.remove('grabbing'); hold(1800); } });
  sc.addEventListener('mousemove', function(e){ if(!down) return; e.preventDefault(); sc.scrollLeft = sl - (e.pageX - sx); });
  if(REDUCE) return;
  var hover = false, seen = false, ret = false, pos = 0, last = null;
  sc.addEventListener('mouseenter', function(){ hover = true; });
  sc.addEventListener('mouseleave', function(){ hover = false; });
  sc.addEventListener('touchstart', function(){ hold(2600); }, {passive:true});
  new IntersectionObserver(function(e){ seen = e[0].isIntersecting; }, {threshold:.05}).observe(sc);
  function back(s0, t0){
    var D = 1600;
    (function stepB(n){
      var p = Math.min(1, (n - t0) / D);
      var e = 1 - Math.pow(1 - p, 3);
      pos = s0 * (1 - e);
      sc.scrollLeft = pos;
      if(p < 1) requestAnimationFrame(stepB);
      else { ret = false; hold(900); }
    })(t0);
  }
  function loop(t){
    if(last === null) last = t;
    var dt = Math.min(.05, (t - last) / 1000);
    last = t;
    var max = sc.scrollWidth - sc.clientWidth;
    if(seen && !hover && !down && !ret && t > pauseUntil && max > 10 && !document.hidden){
      if(Math.abs(sc.scrollLeft - pos) > 2) pos = sc.scrollLeft;
      pos = Math.min(max, pos + 25 * dt);
      sc.scrollLeft = pos;
      if(pos >= max - 1){ ret = true; back(pos, t); }
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();

/* ============================================================================
   SOMMAIRE, articles.html : rubriques, recherche, état vide.
   La grille se construit ici depuis window.ARTICLES, seule source de vérité :
   rien n'est écrit en dur dans la page, sinon le sommaire divergerait du
   catalogue. tools/build.py écrit la même liste entre les marqueurs S: de
   articles.html, pour les robots qui n'exécutent pas JavaScript.

   Contrat d'URL, à ne pas casser : « ?q= » porte la recherche, c'est la cible
   du SearchAction déclaré sur la page d'accueil, et « #cat= » porte la rubrique
   (un fragment, non une chaîne de requête : une URL en ?cat= serait une page
   distincte pour un crawler, explorée au détriment des vrais articles). Les
   deux sont relus au chargement et réécrits sans rechargement.
   ========================================================================== */
(function(){
  var grid = document.getElementById('articles-grid');
  if(!grid) return;

  var ARTS  = Array.isArray(window.ARTICLES) ? window.ARTICLES : [];
  var chips = document.getElementById('chips');
  var form  = document.getElementById('filter-form');
  var input = document.getElementById('filter-input');
  var count = document.getElementById('art-count');
  var empty = document.getElementById('empty-state');
  var eTtl  = document.getElementById('empty-title');
  var eHint = document.getElementById('empty-hint');
  var ALL   = 'Toutes';

  /* Libellés canoniques des rubriques. Le catalogue peut être saisi avec ou
     sans accents (« Enquete » ou « Enquête ») : la comparaison passe par norm,
     mais l'affichage et le data-cat des cartes, lu par la feuille de style,
     restent accentués. */
  var CATS = ['Palmarès', 'Enquête', 'Guide', 'Ouverture', 'Villes'];
  var MOIS = ['janvier','février','mars','avril','mai','juin',
              'juillet','août','septembre','octobre','novembre','décembre'];

  function norm(s){
    return String(s == null ? '' : s).normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  }
  function esc(s){
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function label(cat){
    for(var i = 0; i < CATS.length; i++){ if(norm(CATS[i]) === norm(cat)) return CATS[i]; }
    return String(cat == null ? '' : cat);
  }
  function frDate(iso){
    var p = String(iso == null ? '' : iso).split('-');
    if(p.length !== 3) return '';
    var j = parseInt(p[2], 10);
    return (j === 1 ? '1er' : j) + ' ' + MOIS[parseInt(p[1], 10) - 1] + ' ' + p[0];
  }
  function byDateDesc(a, b){ return String(b.date).localeCompare(String(a.date)); }

  /* Une parution sans photo garde une vignette typographique : la règle du
     catalogue interdit d'illustrer un établissement nommé par une banque
     d'images, un repli photographique serait un faux visuel. */
  function cardHTML(a){
    var cat = label(a.cat);
    var ph = a.photo
      ? '<div class="ph"><img src="' + esc(a.photo) + '" alt="" loading="lazy" decoding="async"></div>'
      : '<div class="ph ph--none" aria-hidden="true"><span>✺</span></div>';
    var dest = [a.dest, a.reading ? a.reading + ' min de lecture' : '']
      .filter(function(x){ return !!x; }).join(' · ');
    return '<a class="art-card" href="' + esc(a.url || '#') + '" data-cat="' + esc(cat) + '">' + ph +
      '<div class="meta"><span class="cat">' + esc(cat) + '</span>' +
      '<span class="date">' + esc(frDate(a.date)) + '</span></div>' +
      '<h3>' + esc(a.title) + '</h3>' +
      (dest ? '<p class="dest">' + esc(dest) + '</p>' : '') +
    '</a>';
  }

  var state = {cat: ALL, q: ''};

  /* La chaîne de requête d'abord (liens partagés, SearchAction), le fragment
     ensuite : les deux formes sont lues, une seule est publiée. */
  function param(name){
    var s = new URLSearchParams(location.search).get(name);
    if(s) return s;
    var h = new URLSearchParams(location.hash.replace(/^#/, '')).get(name);
    return h || '';
  }
  function readURL(){
    var c = param('cat');
    if(c){
      state.cat = ALL;
      for(var i = 0; i < CATS.length; i++){ if(norm(CATS[i]) === norm(c)) state.cat = CATS[i]; }
    }
    state.q = param('q');
  }
  function writeURL(){
    var qs = state.q ? '?q=' + encodeURIComponent(state.q) : '';
    var hs = state.cat !== ALL ? '#cat=' + norm(state.cat) : '';
    /* replaceState plutôt que pushState : filtrer n'est pas naviguer, et un
       historique d'une entrée par frappe rendrait le bouton retour inutilisable.
       Le try protège l'ouverture en file:// , où l'API lève une SecurityError. */
    try { history.replaceState(null, '', location.pathname + qs + hs); } catch(e){}
  }
  function syncChips(){
    if(!chips) return;
    chips.querySelectorAll('.chip').forEach(function(b){
      var on = norm(b.dataset.cat) === norm(state.cat);
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
  function setCount(n){
    if(!count) return;
    if(!ARTS.length){ count.textContent = 'Aucune parution publiée à ce jour'; return; }
    var t = n + (n > 1 ? ' parutions' : ' parution');
    if(state.cat !== ALL) t += ' · ' + state.cat;
    if(state.q) t += ' · « ' + state.q + ' »';
    count.textContent = t;
  }
  function setEmptyText(n){
    if(n || !eTtl || !eHint) return;
    if(!ARTS.length){
      eTtl.textContent = 'Les premières parutions arrivent.';
      eHint.textContent = 'Le sommaire s\'ouvrira au premier service. Rien n\'est publié ici tant ' +
        'qu\'une table n\'a pas été réservée sous un autre nom, mangée, et payée par la rédaction.';
    } else {
      eTtl.textContent = 'Rien sous ce filtre.';
      eHint.textContent = 'Aucune parution ne répond à cette recherche. Essayez une autre ville, ' +
        'une autre rubrique, ou revenez à la sélection complète.';
    }
  }
  function apply(){
    var q = norm(state.q);
    var res = ARTS.slice().sort(byDateDesc).filter(function(a){
      if(state.cat !== ALL && norm(label(a.cat)) !== norm(state.cat)) return false;
      if(!q) return true;
      return norm([a.title, a.dest, a.region, label(a.cat), a.slug].join(' ')).indexOf(q) !== -1;
    });
    grid.innerHTML = res.map(cardHTML).join('');
    /* Photo introuvable : on retombe sur la vignette typographique, jamais sur
       une image de banque, qui ferait passer un decor pour la maison citee. */
    grid.querySelectorAll('.ph img').forEach(function(img){
      img.addEventListener('error', function(){
        var ph = img.parentNode;
        if(!ph) return;
        ph.classList.add('ph--none');
        ph.setAttribute('aria-hidden', 'true');
        ph.innerHTML = '<span>✺</span>';
      }, {once:true});
    });
    grid.style.display = res.length ? '' : 'none';
    if(empty) empty.style.display = res.length ? 'none' : '';
    setEmptyText(res.length);
    setCount(res.length);
  }

  if(chips) chips.addEventListener('click', function(e){
    var b = e.target.closest('.chip');
    if(!b) return;
    state.cat = b.dataset.cat || ALL;
    syncChips(); apply(); writeURL();
  });
  if(input) input.addEventListener('input', function(){
    state.q = input.value; apply(); writeURL();
  });
  /* Sans JavaScript, la touche Entrée envoie le formulaire et recharge la page
     sur articles.html?q=… ; avec, on filtre sur place. */
  if(form) form.addEventListener('submit', function(e){
    e.preventDefault();
    state.q = input ? input.value : '';
    apply(); writeURL();
  });
  window.addEventListener('hashchange', function(){
    readURL();
    if(input) input.value = state.q;
    syncChips(); apply();
  });

  readURL();
  if(input) input.value = state.q;
  syncChips();
  apply();
})();

// Compteur de parutions des menus. Se tait tant que le catalogue est vide :
// « 0 parution » dirait moins bien que le libellé éditorial déjà en place.
(function(){
  var els = document.querySelectorAll('[data-art-count]');
  var n = Array.isArray(window.ARTICLES) ? window.ARTICLES.length : 0;
  if(!els.length || !n) return;
  els.forEach(function(el){ el.textContent = n + (n > 1 ? ' parutions' : ' parution'); });
})();

// Bouton « Rechercher » du masthead : sur le sommaire, il mène au champ de
// filtre. Ailleurs, faute de champ, le bloc ne s'installe pas.
(function(){
  var input = document.getElementById('filter-input');
  if(!input) return;
  document.querySelectorAll('.btn-search').forEach(function(b){
    b.addEventListener('click', function(){
      input.scrollIntoView({block:'center', behavior: REDUCE ? 'auto' : 'smooth'});
      input.focus({preventScroll:true});
    });
  });
})();

/* ============================================================================
   CONTACT, contact.html : validation, envoi, repli courriel.

   POINT DE BRANCHEMENT DE L'ENVOI, à configurer avant la mise en ligne.
   Deux montages possibles, aucun n'est câblé aujourd'hui :

     1. Backend maison ou service de formulaire (worker, Formspree, Netlify
        Forms...) : renseigner ENDPOINT avec l'URL qui reçoit un POST JSON
        {name, email, subject, message}. Toute réponse 2xx vaut accusé de
        réception, tout le reste bascule sur le repli courriel.

     2. EmailJS : ajouter le SDK dans contact.html,
        <script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
        puis, ici même, emailjs.init({publicKey:'…'}) et décommenter l'appel
        emailjs.send('service_…', 'template_…', …) dans send().

   Aucun identifiant de service n'est écrit dans ce dépôt : le fichier est
   public, une clé y serait lisible de tous.

   Tant que rien n'est configuré, le formulaire n'échoue pas en silence : il
   bascule sur l'adresse de la rédaction, message déjà recopié dans le courriel.
   ========================================================================== */
(function(){
  var form = document.getElementById('contact-form');
  if(!form) return;

  var ENDPOINT = '';                                  // vide = envoi non configuré
  var MAIL     = 'contact@lesmeilleursrestaurants.fr';

  var status   = document.getElementById('form-status');
  var btn      = document.getElementById('form-send');
  var lbl      = btn ? btn.querySelector('.lbl') : null;
  var success  = document.getElementById('form-success');
  var fallback = document.getElementById('form-fallback');
  var mailto   = document.getElementById('form-mailto');
  var again    = document.getElementById('form-again');
  var back     = document.getElementById('form-back');
  var fbSub    = fallback ? fallback.querySelector('.sub') : null;
  var DEF_MSG  = status ? status.textContent : '';
  var DEF_SUB  = fbSub ? fbSub.textContent : '';

  function say(msg, err){
    if(!status) return;
    status.textContent = msg;
    status.classList.toggle('err', !!err);
  }
  function show(panel){
    if(!panel) return;
    form.hidden = true;
    panel.hidden = false;
    panel.scrollIntoView({block:'center', behavior: REDUCE ? 'auto' : 'smooth'});
  }
  function backToForm(){
    if(success) success.hidden = true;
    if(fallback) fallback.hidden = true;
    form.hidden = false;
    if(btn) btn.disabled = false;
    if(lbl) lbl.textContent = 'Envoyer';
  }
  function values(){
    var f = form.elements;
    return {
      name: f.name.value.trim(),
      email: f.email.value.trim(),
      subject: f.subject.value,
      message: f.message.value.trim()
    };
  }
  /* Repli : un lien mailto prérempli, ouvert par le visiteur lui-même. Rien
     n'est transmis à un tiers, le message reste dans sa messagerie. */
  function mailtoHref(d){
    var body = 'Nom : ' + d.name + '\n' +
               'E-mail : ' + d.email + '\n' +
               'Motif : ' + d.subject + '\n\n' +
               d.message + '\n';
    return 'mailto:' + MAIL +
      '?subject=' + encodeURIComponent('[' + d.subject + '] ' + d.name) +
      '&body=' + encodeURIComponent(body);
  }
  function offerMail(d, sub){
    if(mailto) mailto.setAttribute('href', mailtoHref(d));
    if(fbSub) fbSub.textContent = sub || DEF_SUB;
    show(fallback);
  }
  function reason(err){
    return (err && (err.text || err.message || err.status)) || 'erreur réseau';
  }
  function send(d){
    if(ENDPOINT){
      return fetch(ENDPOINT, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(d)
      }).then(function(r){
        if(!r.ok) throw new Error('HTTP ' + r.status);
        return r;
      });
    }
    /* EmailJS, à décommenter une fois le service et le modèle créés :
    return emailjs.send('service_a_renseigner', 'template_a_renseigner', {
      name: d.name, from_name: d.name,
      email: d.email, from_email: d.email, reply_to: d.email,
      subject: d.subject, title: d.subject, message: d.message
    });
    */
    return Promise.reject(new Error('envoi non configuré'));
  }

  if(again) again.addEventListener('click', function(){
    form.reset(); backToForm(); say(DEF_MSG, false);
  });
  if(back) back.addEventListener('click', function(){ backToForm(); });

  form.addEventListener('submit', function(e){
    e.preventDefault();
    var f = form.elements;
    if(f.website && f.website.value){ show(success); return; }   // piège à robots
    var d = values();
    if(!d.name || !d.subject || !d.message || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)){
      say('Il manque un nom, un e-mail valide, un motif ou un message.', true);
      return;
    }
    if(f.consent && !f.consent.checked){
      say('Merci de cocher la case de consentement avant l\'envoi.', true);
      return;
    }
    if(!ENDPOINT && !window.emailjs){ offerMail(d, null); return; }
    if(btn) btn.disabled = true;
    if(lbl) lbl.textContent = 'Envoi…';
    say('Le message part vers la rédaction…', false);
    send(d).then(function(){
      say(DEF_MSG, false);
      show(success);
    }).catch(function(err){
      if(btn) btn.disabled = false;
      if(lbl) lbl.textContent = 'Envoyer';
      offerMail(d, 'L\'envoi automatique a échoué (' + reason(err) + '). Votre message ' +
        'n\'est pas perdu : le bouton ci-dessous ouvre votre messagerie avec le texte déjà recopié.');
    });
  });
})();
