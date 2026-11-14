(function(){
  var T = {
    fi:{title:'Reseptit',search:'Hae: pesto, voi, kantarelli…',all:'Kaikki',recipes:'reseptiä',results:'Tulokset',none:'Ei reseptejä haulla',
      batch:'Määrä',auto:'Ainekset lasketaan itse',ingredients:'Ainekset',method:'Valmistus',back:'Takaisin',
      nomethod:'Paperissa ei ole kirjoitettua valmistusohjetta.',original:'Näytä alkuperäinen paperi',minus:'Vähemmän',plus:'Enemmän',vegan:'vegaani',parts:'osaa',
      foot:'Reseptit luettu keittiön paperikansiosta. Jos jokin näyttää väärältä, tarkista alkuperäinen paperi.',
      have:'Minulla on',havehint:'Reseptissä {q}. Kirjoita, paljonko sinulla on, niin kaikki muut määrät lasketaan sen mukaan.',haveok:'Laske',
      calc:'Laskin',calcuse:'Käytä määränä',tiphave:'Vinkki: napauta minkä tahansa aineen määrää, niin voit laskea kaiken sen mukaan.',
      gen:'Paperissa ei ollut ohjetta, joten tämä on lisätty. Tarkista keittiömestarilta.',
      tRecipes:'Reseptit',tNew:'Uusi',tFavs:'Suosikit',tPrep:'Prep-lista',tCalc:'Laskin',
      fav:'Lisää suosikkeihin',unfav:'Poista suosikeista',favs:'Suosikit',recent:'Viimeksi avatut',
      nofavs:'Ei vielä suosikkeja. Avaa resepti ja paina tähteä ☆.',
      addprep:'+ Lisää prep-listaan',inprep:'✓ Prep-listalla · poista',
      prepTitle:'Prep-lista',prepSub:'Tämän päivän valmistettavat',noprep:'Lista on tyhjä. Avaa resepti ja paina "Lisää prep-listaan".',
      totals:'Kaikki ainekset yhteensä',clear:'Tyhjennä lista',done:'valmis',of:'/',
      timer:'Ajastin',stop:'Pysäytä',ready:'Valmis!',
      newbtn:'Lisää uusi resepti kuvasta',newTitle:'Uusi resepti',newHint:'Ota kuva reseptipaperista. Jos resepti on usealla sivulla, lisää kaikki sivut. Resepti ilmestyy sovellukseen noin tunnin sisällä, suomeksi ja englanniksi.',
      newName:'Reseptin nimi (vapaaehtoinen)',newPick:'Ota kuva tai valitse',newSend:'Lähetä',newSending:'Lähetetään…',newOk:'Lähetetty! Resepti lisätään noin tunnin sisällä.',
      newErr:'Lähetys ei onnistunut. Tarkista netti ja yritä uudelleen.',newOff:'Kuvien lähetys ei ole vielä käytössä.',newPages:'sivua',newRemove:'Poista kuva',isNew:'uusi',cook:'Aloita kokkaus',partAmt:'Tämän osan määrä',partMain:'Pääosa · {m}× (yllä olevan määrän mukaan)',onlyPart:'Koskee vain osaa: {p}. Muille osille on oma määrä.',hiMorning:'Huomenta',hiDay:'Hei',hiEve:'Iltaa',helloSub:'Mitä tänään tehdään?',ingShort:'ainesta',stepShort:'vaihetta',tNeeds:'Tarvitaan',needTitle:'Mitä tarvitaan?',needSub:'Kirjoita mitä keittiö tarvitsee. Kaikki näkevät sen heti.',needAsk:'Mitä tarvitaan?',needEx:'Esim. Kurkkua 5 kg',needSend:'Lähetä',needSent:'Lähetetty kaikille',needOpen:'Odottaa',needNone:'Ei avoimia pyyntöjä.',needDone:'Hoidettu',needDoneList:'Hoidettu (3 pv)',needUndo:'Palauta',needNew:'Uusi pyyntö',wTitle:'Tervetuloa Tintå-keittiöön',wHint:'Kirjoita nimesi ja keittiön koodi kerran. Puhelin muistaa ne, eikä niitä kysytä uudelleen.',wStart:'Aloita',wSkip:'Myöhemmin',wOk:'Tervetuloa',wBad:'Väärä koodi. Kysy esimieheltä.',wWait:'Liian monta yritystä. Odota 15 min.',pinTitle:'Keittiön koodi',pinHint:'Kirjoita keittiön koodi. Saat sen esimieheltä. Koodi kysytään vain kerran tällä puhelimella.',pinOk:'Jatka',updTitle:'Resepti on päivitetty',updUse:'Keittiö on muuttanut tätä reseptiä. Tee tämän uuden version mukaan.',updTag:'päivitetty',updHome:'{n} reseptiä päivitetty – katso muutokset',kitchen:'Keittiön muutokset',editsOn:'{n} määrää muutettu keittiössä. Muutetut näkyvät aineksissa.',someone:'Joku',del:'Poista',yourName:'Nimesi',noteAll:'Kirjoita muutos kaikille',noteEx:'Esim. Vähemmän suolaa: 1 rkl riittää.',saveAll:'Tallenna kaikille',saving:'Tallennetaan…',saveErr:'Tallennus ei onnistunut. Tarkista netti.',editBtn:'Muokkaa määriä',editTitle:'Muokkaa määriä',editHint:'Muuta määrät yhden reseptin mukaan (1×). Tallennus näkyy kaikille.',editWhy:'Mitä muutit ja miksi?',cancel:'Peruuta',changed:'muutettu',was:'oli',autoNote:'{n} määrää muutettu.',howMuch:'Paljonko teet?',byIng:'Laske tämän aineen mukaan:',amount:'Määrä',unit:'Yksikkö',factor:'Kaikki ainekset lasketaan:',saved:'muistetaan tässä puhelimessa',cookStep:'Vaihe',cookPrev:'Edellinen',cookNext:'Seuraava',cookDone:'Valmis',cookHere:'Tässä vaiheessa',cookClose:'Sulje kokkaustila',size:'Tekstin koko',share:'Jaa resepti',copied:'Resepti kopioitu',notes:'Omat muistiinpanot',notesHint:'Näkyy vain tässä puhelimessa.',more:'Lisää',cats:'Kategoriat',allAZ:'Kaikki reseptit A–Ö',allCats:'Kaikki kategoriat'},
    en:{title:'Recipes',search:'Search: pesto, butter, chanterelle…',all:'All',recipes:'recipes',results:'Results',none:'No recipes for',
      batch:'Batch',auto:'Amounts update automatically',ingredients:'Ingredients',method:'Method',back:'Back',
      nomethod:'No method is written on the paper.',original:'Show original paper',minus:'Less',plus:'More',vegan:'vegan',parts:'parts',
      foot:'Recipes read from the kitchen binder. If something looks wrong, check the original paper.',
      have:'I have',havehint:'The recipe uses {q}. Type how much you have and every other amount is worked out from it.',haveok:'Calculate',
      calc:'Calculator',calcuse:'Use as batch',tiphave:'Tip: tap any ingredient amount to scale everything by it.',
      gen:'The paper had no method, so this was added. Check with the head chef.',
      tRecipes:'Recipes',tNew:'New',tFavs:'Favourites',tPrep:'Prep list',tCalc:'Calculator',
      fav:'Add to favourites',unfav:'Remove from favourites',favs:'Favourites',recent:'Recently opened',
      nofavs:'No favourites yet. Open a recipe and tap the star ☆.',
      addprep:'+ Add to prep list',inprep:'✓ On prep list · remove',
      prepTitle:'Prep list',prepSub:'What to make today',noprep:'The list is empty. Open a recipe and tap "Add to prep list".',
      totals:'All ingredients combined',clear:'Clear list',done:'done',of:'/',
      timer:'Timer',stop:'Stop',ready:'Ready!',
      newbtn:'Add a new recipe from a photo',newTitle:'New recipe',newHint:'Take a photo of the recipe paper. If it has several pages, add all of them. The recipe appears in the app within about an hour, in Finnish and English.',
      newName:'Recipe name (optional)',newPick:'Take or choose a photo',newSend:'Send',newSending:'Sending…',newOk:'Sent! The recipe will be added within about an hour.',
      newErr:'Sending failed. Check the connection and try again.',newOff:'Photo upload is not switched on yet.',newPages:'pages',newRemove:'Remove photo',isNew:'new',cook:'Start cooking',partAmt:'Amount for this part',partMain:'Main part · {m}× (from the amount above)',onlyPart:'Applies only to: {p}. Other parts have their own amount.',hiMorning:'Good morning',hiDay:'Hi',hiEve:'Good evening',helloSub:'What are we making today?',ingShort:'ingredients',stepShort:'steps',tNeeds:'Needed',needTitle:'What do we need?',needSub:'Write what the kitchen needs. Everyone sees it right away.',needAsk:'What is needed?',needEx:'E.g. Cucumber 5 kg',needSend:'Send',needSent:'Sent to everyone',needOpen:'Waiting',needNone:'No open requests.',needDone:'Done',needDoneList:'Done (3 days)',needUndo:'Undo',needNew:'New request',wTitle:'Welcome to the Tintå kitchen',wHint:'Enter your name and the kitchen code once. The phone remembers them and will not ask again.',wStart:'Start',wSkip:'Later',wOk:'Welcome',wBad:'Wrong code. Ask your manager.',wWait:'Too many tries. Wait 15 min.',pinTitle:'Kitchen code',pinHint:'Enter the kitchen code. Ask your manager for it. It is asked only once on this phone.',pinOk:'Continue',updTitle:'This recipe was updated',updUse:'The kitchen changed this recipe. Work from this new version.',updTag:'updated',updHome:'{n} recipes updated – see the changes',kitchen:'Kitchen changes',editsOn:'{n} amounts changed by the kitchen. They are marked in the ingredients.',someone:'Someone',del:'Delete',yourName:'Your name',noteAll:'Write a change for everyone',noteEx:'E.g. Less salt: 1 tbsp is enough.',saveAll:'Save for everyone',saving:'Saving…',saveErr:'Saving failed. Check the connection.',editBtn:'Edit amounts',editTitle:'Edit amounts',editHint:'Change amounts for one batch (1×). Saving shows it to everyone.',editWhy:'What did you change and why?',cancel:'Cancel',changed:'changed',was:'was',autoNote:'{n} amounts changed.',howMuch:'How much are you making?',byIng:'Scale by this ingredient:',amount:'Amount',unit:'Unit',factor:'All ingredients scaled:',saved:'remembered on this phone',cookStep:'Step',cookPrev:'Back',cookNext:'Next',cookDone:'Done',cookHere:'In this step',cookClose:'Close cooking mode',size:'Text size',share:'Share recipe',copied:'Recipe copied',notes:'My notes',notesHint:'Only visible on this phone.',more:'More',cats:'Categories',allAZ:'All recipes A–Z',allCats:'All categories'}
  };
  var LEAF = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13.5 2.5C7 2.5 3 5.5 3 10c0 1.2.4 2.3 1 3.1C5 9.8 7.5 7.4 10.5 6c-2.6 1.8-4.6 4.2-5.6 7.4.7.4 1.6.6 2.6.6 4.5 0 7-4 6-11.5z" fill="currentColor"/></svg>';
  function vbadge(cls){ return '<span class="vbadge '+(cls||'')+'">'+LEAF+'<b>'+T[lang].vegan+'</b></span>'; }
  var HOT = {kastike:1, liemi:1, keitto:1, pohja:1, lisuke:1};
  var CATS = {
    kastike:['Kastikkeet ja dipit','Sauces & dips'], majo:['Majoneesit','Mayos'], oljy:['Öljyt ja vinegretit','Oils & dressings'],
    pesto:['Pestot','Pestos'], voi:['Voit','Butters'], liemi:['Liemet','Stocks'], keitto:['Keitot','Soups'], pohja:['Pohjat','Bases'],
    lisuke:['Lisukkeet ja risotot','Sides & risottos'], mari:['Marinadit','Marinades'], sailyke:['Hillot, chutneyt ja pikkelit','Jams, chutneys & pickles'],
    mauste:['Rapeat ja mausteet','Crunch & seasonings'], jalki:['Jälkiruoat','Desserts']
  };
  var U = {g:['g','g'],kg:['kg','kg'],ml:['ml','ml'],cl:['cl','cl'],dl:['dl','dl'],l:['l','l'],tl:['tl','tsp'],rkl:['rkl','tbsp'],kpl:['kpl','pcs'],
    prk:['prk','tub'],pss:['pss','bag'],pnt:['nippu','bunch'],rss:['rasia','box'],tlk:['tlk','can'],levy:['levyä','sheets'],tuubi:['tuubia','tubes'],osa:['osa','part']};
  var CICON = {
    kastike:'M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z', majo:'M7 4h10M6 7h12v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z', oljy:'M10 2h4M10 2v4l-3 4v10a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V10l-3-4V2',
    pesto:'M5 19c0-8 6-14 14-14 0 8-6 14-14 14zM5 19l8-8', voi:'M4 9l8-4 8 4-8 4zM4 9v6l8 4 8-4V9', liemi:'M4 10h16v6a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM2 10h20M9 6V4M15 6V4',
    keitto:'M3 11h18a9 9 0 0 1-18 0zM8 7c0-1 1-1 1-2M12 7c0-1 1-1 1-2M16 7c0-1 1-1 1-2', pohja:'M4 14h16v4H4zM6 14V9h12v5', lisuke:'M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    mari:'M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-3 2-4 3-7 1 2 2 3 3 3 0-3-1-5 0-7z', sailyke:'M8 3h8v3H8zM6 6h12v13a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2zM6 11h12', mauste:'M8 9h8l-1 11H9zM9 9l1-5h4l1 5', jalki:'M4 20h16M5 20v-7h14v7M8 13V9M12 13V9M16 13V9', az:'M4 6h16M4 12h16M4 18h16'
  };
  function cicon(k){ return '<span class="cico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+CICON[k]+'"></path></svg></span>'; }
  var ICON = {
    aa:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 19 8 6l5 13M4.8 14.5h6.4M14 19l3.5-9 3.5 9M15 16.5h5"></path></svg>',
    play:'<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"></path></svg>',
    share:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M8 7l4-4 4 4M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"></path></svg>',
    back:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="m15 6-6 6 6 6"></path></svg>',
    star:'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"></path></svg>',
    clock:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="13" r="8"></circle><path d="M12 9v4l2.5 2M10 2h4"></path></svg>',
    chev:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6E675E" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6"></path></svg>'
  };
  var LANGS = '<div class="lang" role="group" aria-label="Kieli / Language"><button type="button" data-lang="fi">FI</button><button type="button" data-lang="en">EN</button></div>';

  /* ---------- tallennus (vain tällä laitteella) ---------- */
  function load(k, d){ try{ var v = localStorage.getItem('tinta-'+k); return v ? JSON.parse(v) : d; }catch(e){ return d; } }
  function save(k, v){ try{ localStorage.setItem('tinta-'+k, JSON.stringify(v)); }catch(e){} }
  var lang = load('lang','fi'); if(lang!=='en') lang='fi';
  var favs = load('favs', []), recent = load('recent', []), prep = load('prep', []), pdone = load('pdone', {});
  var cat = 'all', cur = null, mult = 1, view = 'home', listView = 'home';

  var L = function(){ return lang==='fi' ? 0 : 1; };
  var $ = function(id){ return document.getElementById(id); };
  var byId = function(id){ return R.filter(function(x){ return x.id===id; })[0]; };
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]}); }
  function norm(s){ return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,''); }

  function num(r){
    var v = r>=100 ? Math.round(r) : r>=1 ? Math.round(r*10)/10 : Math.round(r*100)/100;
    return String(v).replace('.', lang==='fi' ? ',' : '.');
  }
  function fmt(q,u,m){
    if(q===null) return '';
    if(u==='osa') m = 1;
    q = q*(m===undefined ? mult : m);
    if(u==='g' && q>=1000){q=q/1000;u='kg'}
    else if(u==='kg' && q<1){q=q*1000;u='g'}
    else if(u==='ml' && q>=1000){q=q/1000;u='l'}
    else if(u==='ml' && q>=100){q=q/100;u='dl'}
    else if(u==='dl' && q>=10){q=q/10;u='l'}
    else if(u==='l' && q<1){q=q*10;u='dl'}
    var unit = U[u] ? U[u][L()] : u;
    if(u==='osa' && q!==1) unit = lang==='fi' ? 'osaa' : 'parts';
    if(u==='pnt' && q!==1) unit = lang==='fi' ? 'nippua' : 'bunches';
    return num(q)+' '+unit;
  }

  /* ---------- näkymät ---------- */
  function setTabs(){
    var t = T[lang];
    $('tab1').textContent = t.tRecipes; $('tab2').textContent = t.tNeeds; $('tab3').textContent = t.tPrep; $('tab4').textContent = t.tCalc; $('tab5').textContent = t.tNew;
    document.querySelectorAll('[data-tab]').forEach(function(b){
      var on = (b.dataset.tab==='home' && (view==='home' || (view==='recipe' && listView==='home'))) ||
               (b.dataset.tab==='needs' && view==='needs') ||
               (b.dataset.tab==='prep' && (view==='prep' || (view==='recipe' && listView==='prep')));
      if(on) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current');
    });
    var n = prep.length; $('prepbadge').hidden = !n; $('prepbadge').textContent = n;
    var u = unseenList().length; $('homebadge').hidden = !u; $('homebadge').textContent = u;
    var nn = newNeeds().length; $('needbadge').hidden = !nn; $('needbadge').textContent = nn;
    try{ if(navigator.setAppBadge){ if(u+nn) navigator.setAppBadge(u+nn); else navigator.clearAppBadge(); } }catch(e){}
    document.querySelectorAll('[data-lang]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });
  }

  function rowHtml(r){
    var t = T[lang], i = L();
    var meta = CATS[r.c][i] + (r.p.length>1 ? ' · '+r.p.length+' '+t.parts : '');
    var fresh = r.added && (Date.now() - Date.parse(r.added)) < 14*864e5;
    return '<button type="button" class="row" data-open="'+r.id+'"><span class="thumb">'+TintaDish.svg(r,'dish')+'</span><div class="t"><div class="n">'+esc(r.n[i])+
      (isUnseen(r.id)?'<span class="tag upd">'+t.updTag+'</span>':'')+(fresh?'<span class="tag">'+t.isNew+'</span>':'')+(r.v?'<span class="tag veg">'+LEAF+t.vegan+'</span>':'')+'</div><div class="m">'+esc(r.n[1-i])+' · '+esc(meta)+'</div></div>'+
      (favs.indexOf(r.id)>-1 ? '<span class="star">★</span>' : '')+ICON.chev+'</button>';
  }

  function card(r){
    var t = T[lang], i = L(), fresh = r.added && (Date.now() - Date.parse(r.added)) < 14*864e5, up = isUnseen(r.id);
    var nI = 0; r.p.forEach(function(p){ nI += p.i.length; });
    return '<button type="button" class="rcard" data-open="'+r.id+'">'+(up ? '<span class="ctag">'+t.updTag+'</span>' : fresh ? '<span class="ctag">'+t.isNew+'</span>' : '')+
      (favs.indexOf(r.id)>-1 ? '<span class="cstar">★</span>' : '')+(r.v ? vbadge((up||fresh)?'low':'') : '')+TintaDish.svg(r,'dish')+
      '<b>'+esc(r.n[i])+'</b><span>'+esc(CATS[r.c][i])+' · '+nI+' '+t.ingShort+'</span></button>';
  }
  function mini(r){ var i = L(); return '<button type="button" class="mini" data-open="'+r.id+'">'+TintaDish.svg(r,'dish')+'<b>'+esc(r.n[i])+'</b></button>'; }
  function renderHome(){
    var t = T[lang], i = L(), fav = view==='favs';
    $('avatar').textContent = myName || t.yourName;
    $('foot').textContent = t.foot;
    $('q').placeholder = t.search; $('q').setAttribute('aria-label', t.search);
    var sortN = function(a,b){ return a.n[i].localeCompare(b.n[i], lang); };
    var html = '';
    if(fav){
      var f = favs.map(byId).filter(Boolean).sort(sortN);
      html = '<h2 class="label">⭐ '+t.favs+'</h2>'+(f.length ? '<div class="rgrid">'+f.map(card).join('')+'</div>' : '<p class="empty">'+t.nofavs+'</p>');
      $('homelists').innerHTML = html; return;
    }
    var q = norm($('q').value.trim());
    if(q){
      var hits = R.filter(function(r){
        var parts = [r.n[0], r.n[1]];
        r.p.forEach(function(p){ if(p.t) parts.push(p.t[0], p.t[1]); p.i.forEach(function(x){parts.push(x[2], x[3])}); });
        return norm(parts.join(' ')).indexOf(q)>-1;
      }).sort(sortN);
      html = '<h2 class="label">'+t.results+' · '+hits.length+'</h2>'+
        (hits.length ? '<div class="rgrid">'+hits.map(card).join('')+'</div>' : '<p class="empty">'+esc(t.none)+' “'+esc($('q').value)+'”</p>');
      $('homelists').innerHTML = html; return;
    }
    var keys = Object.keys(CATS).filter(function(k){ return R.some(function(r){ return r.c===k; }); });
    html += '<div class="cchips">'+'<button type="button" class="cchip'+(cat==='all'?' on':'')+'" data-cat="all"><span class="cic all">'+R.length+'</span>'+t.all+'</button>'+
      keys.map(function(k){ return '<button type="button" class="cchip'+(cat===k?' on':'')+'" data-cat="'+k+'">'+TintaDish.cat(k,'cic')+esc(CATS[k][i].split(' ')[0])+'</button>'; }).join('')+'</div>';
    if(cat==='all'){
      var ul = unseenList();
      if(ul.length) html += '<div class="updlist"><div class="k">🔔 '+t.updHome.replace('{n}', ul.length)+'</div>'+ul.slice(0,6).map(function(r){
        var lb = lastBy(r.id);
        return '<button type="button" class="urow" data-open="'+r.id+'"><b>'+esc(r.n[i])+'</b><span>'+esc((lb && lb.by) || t.someone)+' · '+when(latest(r.id))+'</span></button>'; }).join('')+'</div>';
      var fv = favs.map(byId).filter(Boolean);
      if(fv.length) html += '<h2 class="label">⭐ '+t.favs+'</h2><div class="strip">'+fv.map(mini).join('')+'</div>';
      var rc2 = recent.map(byId).filter(Boolean).slice(0,10);
      if(rc2.length) html += '<h2 class="label">'+t.recent+'</h2><div class="strip">'+rc2.map(mini).join('')+'</div>';
    }
    var list = R.filter(function(r){ return cat==='all' || r.c===cat; }).sort(sortN);
    html += '<h2 class="label">'+esc(cat==='all' ? t.allAZ : CATS[cat][i])+' · '+list.length+'</h2><div class="rgrid">'+list.map(card).join('')+'</div>';
    $('homelists').innerHTML = html;
  }

  /* ajastimen tunnistus valmistusvaiheesta: "15 min", "2 h 30 min", "5 minuuttia" */
  function findTime(s){
    var m = s.match(/(\d+(?:[.,]\d+)?)\s*(?:h|t|tuntia|tunti|hours?)\b\s*(?:(\d+)\s*(?:min|minuuttia|minutes?))?/i);
    if(m) return Math.round(parseFloat(m[1].replace(',','.'))*3600 + (m[2] ? +m[2]*60 : 0));
    m = s.match(/(\d+(?:[.,]\d+)?)\s*(?:min|minuuttia|minuutin|minutes?)\b/i);
    if(m) return Math.round(parseFloat(m[1].replace(',','.'))*60);
    return 0;
  }
  function clock(sec){ var h=Math.floor(sec/3600), m=Math.floor(sec%3600/60), s=sec%60; return (h? h+':'+(m<10?'0':'') : '')+m+':'+(s<10?'0':'')+s; }

  function prepEntry(id){ return prep.filter(function(p){ return p.id===id; })[0]; }

  var ingDone = {}, stepDone = {}, rtab = 'ing';
  /* Jokaisella osalla oma määrä. / كل جزء إله كميته. */
  var partMults = load('partm', {});
  function basePart(r){ var b = bases[r.id], ref = (b && ingAt(r, b.ref)) ? b.ref : defaultBase(r); return ref ? +String(ref).split('-')[0] : 0; }
  function multFor(r, pi, m){ var mm = m===undefined ? mult : m; if(r.p.length < 2 || pi===basePart(r)) return mm; var pm = (partMults[r.id]||{})[pi]; return pm===undefined ? 1 : pm; }
  function partCtl(r, pi){
    if(r.p.length < 2) return '';
    var t = T[lang], v = multFor(r, pi);
    if(pi===basePart(r)) return '<div class="pmeta">'+t.partMain.replace('{m}', num(v))+'</div>';
    return '<div class="pctl"><span class="k">'+t.partAmt+'</span><div class="pq">'+
      '<button type="button" data-pstep="'+pi+'" data-d="-0.5" aria-label="'+t.minus+'">−</button><output>'+num(v)+'×</output><button type="button" data-pstep="'+pi+'" data-d="0.5" aria-label="'+t.plus+'">+</button>'+
      [0.5,1,2,3].map(function(x){ return '<button type="button" class="pv" data-pp="'+pi+'" data-pv="'+x+'" aria-pressed="'+(x===v)+'">'+num(x)+'×</button>'; }).join('')+'</div></div>';
  }
  function setPart(r, pi, v){ partMults[r.id] = partMults[r.id] || {}; partMults[r.id][pi] = Math.max(0.5, Math.round(v*2)/2); save('partm', partMults); }
  /* ---------- Määrä: pääaineen mukaan tai kertoimella ---------- */
  var MASS = {g:1,kg:1000}, VOL = {ml:1,cl:10,dl:100,l:1000};
  var bases = load('base', {});
  function unitsFor(u){ return MASS[u] ? ['kg','g'] : VOL[u] ? ['l','dl','ml'] : [u]; }
  function fac(u){ return MASS[u] || VOL[u] || 1; }
  function ingAt(r, ref){ var a = String(ref).split('-'); var p = r.p[+a[0]]; return p && p.i[+a[1]]; }
  function candidates(r){
    var out = [];
    r.p.forEach(function(p, pi){ p.i.forEach(function(x, n){ if(x[0]!==null && x[0]>0) out.push({ref:pi+'-'+n, x:x, part:p.t}); }); });
    return out;
  }
  function defaultBase(r){
    var c = candidates(r); if(!c.length) return null;
    var best = c[0];
    c.forEach(function(o){ if((MASS[o.x[1]]||VOL[o.x[1]]) && o.x[0]*fac(o.x[1]) > (MASS[best.x[1]]||VOL[best.x[1]] ? best.x[0]*fac(best.x[1]) : 0)) best = o; });
    return best.ref;
  }
  function niceAmount(q, u){
    var v = q*fac(u), opts = unitsFor(u), pick = opts[opts.length-1];
    for(var k=0;k<opts.length;k++){ if(v/fac(opts[k]) >= 1){ pick = opts[k]; break; } }
    var w = v/fac(pick); return {v: w>=100 ? Math.round(w) : Math.round(w*10)/10, u: pick};
  }
  function scaleCard(r){
    var t = T[lang], i = L(), c = candidates(r), b = bases[r.id];
    var ref = (b && ingAt(r, b.ref)) ? b.ref : defaultBase(r);
    if(!ref) return '';
    var x = ingAt(r, ref), cur2 = niceAmount(x[0]*mult, x[1]);
    var unitSel = unitsFor(x[1]).map(function(u){ return '<option value="'+u+'"'+(u===cur2.u?' selected':'')+'>'+esc(U[u]?U[u][i]:u)+'</option>'; }).join('');
    return '<div class="card scale" id="scalecard"><div class="k">'+t.howMuch+'</div>'+
      '<label class="hint" for="basesel">'+t.byIng+'</label>'+
      '<select id="basesel" class="sel">'+c.map(function(o){ return '<option value="'+o.ref+'"'+(o.ref===ref?' selected':'')+'>'+esc(o.x[2+i]+(o.part?' ('+o.part[i]+')':''))+'</option>'; }).join('')+'</select>'+
      '<div class="brow"><input id="baseamt" type="text" inputmode="decimal" autocomplete="off" aria-label="'+t.amount+'" value="'+String(cur2.v).replace('.', lang==='fi'?',':'.')+'">'+
      '<select id="baseunit" class="sel unit" aria-label="'+t.unit+'">'+unitSel+'</select>'+
      '<button type="button" class="calcgo" id="basego">'+t.haveok+'</button></div>'+
      '<div class="brief">'+t.factor+' <b>'+num(mult)+'×</b>'+(b ? ' · '+t.saved : '')+(r.p.length>1 && r.p[basePart(r)].t ? '<br>'+t.onlyPart.replace('{p}', r.p[basePart(r)].t[i]) : '')+'</div>'+
      '<div class="quick">'+[0.5,1,2,3].map(function(v){return '<button type="button" data-p="'+v+'" aria-pressed="'+(v===mult && !b)+'">'+num(v)+'×</button>'}).join('')+'</div>'+
      '<button type="button" class="addprep" id="prepbtn" aria-pressed="'+(!!prepEntry(r.id))+'">'+(prepEntry(r.id) ? t.inprep : t.addprep)+'</button></div>';
  }
  function applyBase(){
    var r = cur, ref = $('basesel').value, x = ingAt(r, ref);
    var v = parseFloat(String($('baseamt').value).replace(',', '.')), u = $('baseunit').value;
    if(!x || !(v>0)){ $('baseamt').focus(); return; }
    mult = (v*fac(u)) / (x[0]*fac(x[1]));
    bases[r.id] = {ref: ref, v: v, u: u}; save('base', bases);
    syncPrep(); render();
  }
  function multFromBase(r){
    var b = bases[r.id], x = b && ingAt(r, b.ref);
    return x ? (b.v*fac(b.u)) / (x[0]*fac(x[1])) : null;
  }

  function renderRecipe(){
    var r = cur, t = T[lang], i = L(), isFav = favs.indexOf(r.id)>-1, pe = prepEntry(r.id);
    var nIng = 0, nStep = 0; r.p.forEach(function(p){ nIng += p.i.length; nStep += (p.s||[]).length; });
    var html =
      '<div class="top"><button type="button" class="back" id="back">'+ICON.back+'<span>'+t.back+'</span></button>'+
      '<div class="tools"><button type="button" class="icon" id="sizebtn" aria-label="'+t.size+'">'+ICON.aa+'</button><button type="button" class="icon" id="favbtn" aria-pressed="'+isFav+'" aria-label="'+(isFav?t.unfav:t.fav)+'">'+ICON.star+'</button>'+LANGS+'</div></div>'+
      '<div class="rhero'+(HOT[r.c]?' hot':'')+'">'+(r.v?vbadge('big'):'')+(HOT[r.c]?'<div class="steam" aria-hidden="true"><i></i><i></i><i></i><i></i></div>':'')+TintaDish.svg(r,'dish big')+'</div>'+
      '<header class="rhead sheet"><div class="eyebrow">'+esc(CATS[r.c][i])+(r.v?' · '+t.vegan:'')+(r.p.length>1?' · '+r.p.length+' '+t.parts:'')+'</div>'+
      '<h1 class="title">'+esc(r.n[i])+'</h1><div class="other">'+esc(r.n[1-i])+'</div>'+
      '<div class="stats"><div class="stt"><b>'+nIng+'</b><span>'+t.ingShort+'</span></div><div class="stt"><b>'+nStep+'</b><span>'+t.stepShort+'</span></div><div class="stt acc"><b>'+num(mult)+'×</b><span>'+t.batch+'</span></div></div></header>'+
      (r.note ? '<p class="callout">'+esc(r.note[i])+'</p>' : '')+
      updBanner(r)+kitchenNotes(r)+
      scaleCard(r)+
      '<div class="seg" role="tablist"><button type="button" role="tab" data-rtab="ing" aria-selected="'+(rtab==='ing')+'">'+t.ingredients+' <span>'+nIng+'</span></button>'+
      '<button type="button" role="tab" data-rtab="met" aria-selected="'+(rtab==='met')+'">'+t.method+' <span>'+nStep+'</span></button></div>';
    if(rtab==='ing'){
      if(editMode){
        html += '<div class="editbox"><div class="k">'+t.editTitle+'</div><p class="hint">'+t.editHint+'</p></div>';
        r.p.forEach(function(p, pi){
          html += (p.t ? '<h2 class="part">'+esc(p.t[i])+'</h2>' : '')+'<div class="card">'+
            p.i.map(function(x,n){ if(x[0]===null) return '<div class="ing"><span class="name">'+esc(x[2+i])+'</span></div>';
              return '<div class="ing"><label class="name" for="e'+pi+'-'+n+'">'+esc(x[2+i])+'</label><input class="einp" id="e'+pi+'-'+n+'" data-eref="'+pi+'-'+n+'" type="text" inputmode="decimal" value="'+String(x[0]).replace('.', lang==='fi'?',':'.')+'"><span class="eunit">'+esc(U[x[1]]?U[x[1]][i]:x[1])+'</span></div>'; }).join('')+'</div>';
        });
        html += '<label class="field" for="editwhy"><span>'+t.editWhy+'</span><textarea id="editwhy" rows="2"></textarea></label>'+
          nameField()+
          '<div class="erow"><button type="button" class="sharebtn" id="editcancel">'+t.cancel+'</button><button type="button" class="use solid" id="editsave">'+t.saveAll+'</button></div><p class="status" id="editstatus"></p>';
      } else {
        html += '<p class="tip">'+t.tiphave+'</p>';
        r.p.forEach(function(p, pi){
          var pm = multFor(r, pi);
          html += (p.t ? '<h2 class="part">'+esc(p.t[i])+'</h2>' : '')+partCtl(r, pi)+'<div class="card">'+
            p.i.map(function(x,n){ var id='c'+pi+'-'+n, k=r.id+id;
              var chg = x._e ? '<span class="chg">'+t.changed+' · '+t.was+' '+esc(fmt(x._o,x[1],1))+'</span>' : '';
              return '<div class="ing'+(x._e?' changed':'')+'"><input type="checkbox" id="'+id+'" data-ing="'+k+'"'+(ingDone[k]?' checked':'')+'><label class="name" for="'+id+'">'+esc(x[2+i])+chg+'</label>'+
              (x[0]===null ? '' : '<button type="button" class="qty" data-have="'+pi+'-'+n+'" aria-label="'+esc(t.have+': '+x[2+i])+'">'+esc(fmt(x[0],x[1],pm))+'</button>')+'</div>'; }).join('')+'</div>';
        });
        html += '<button type="button" class="sharebtn editbtn" id="editbtn">✎ '+t.editBtn+'</button>';
      }
    } else {
      var any = r.p.some(function(p){ return p.s && p.s.length; });
      if(any) html += '<button type="button" class="cookbtn" id="cookbtn">'+ICON.play+' '+t.cook+'</button>';
      r.p.forEach(function(p, pi){
        if(!(p.s && p.s.length)) return;
        html += (p.t ? '<h2 class="part">'+esc(p.t[i])+'</h2>' : '')+(p.gen?'<p class="gen">'+t.gen+'</p>':'')+'<ol class="steps">'+p.s.map(function(s,n){
          var sec = findTime(s[i]) || findTime(s[0]), k = r.id+'s'+pi+'-'+n;
          return '<li class="'+(stepDone[k]?'ok':'')+'"><button type="button" class="num" data-sdone="'+k+'" aria-pressed="'+(!!stepDone[k])+'" aria-label="'+(n+1)+'">'+(stepDone[k]?'✓':(n+1))+'</button><div class="txt">'+esc(s[i])+
            (sec ? '<button type="button" class="tbtn" data-timer="'+sec+'" data-tname="'+esc(r.n[i]+' · '+(n+1))+'">'+ICON.clock+' '+t.timer+' '+clock(sec)+'</button>' : '')+'</div></li>';
        }).join('')+'</ol>';
      });
      if(!any) html += '<p class="nomethod">'+t.nomethod+'</p>';
    }
    html += '<h2 class="label">'+t.more+'</h2><div class="card more">'+
      '<label class="field" for="noteta"><span>'+t.noteAll+'</span><textarea id="noteta" rows="3" placeholder="'+t.noteEx+'"></textarea></label>'+
      nameField()+
      '<button type="button" class="use solid" id="notesave">'+t.saveAll+'</button><p class="status" id="notestatus"></p>'+
      '<button type="button" class="sharebtn" id="sharebtn">'+ICON.share+' '+t.share+'</button></div>';
    if(r.f) html += '<a class="orig" href="paper/'+esc(r.f)+'.jpg" target="_blank" rel="noopener">'+t.original+' ↗</a>';
    $('recipe').innerHTML = html;
    document.querySelectorAll('#recipe [data-lang]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });
  }

  function renderPrep(){
    var t = T[lang], i = L();
    var html = '<div class="top"><span></span>'+LANGS+'</div><h1 class="big">'+t.prepTitle+'</h1><p class="sub">'+t.prepSub+'</p>';
    if(!prep.length){ $('prep').innerHTML = html+'<p class="empty">'+t.noprep+'</p>'; return; }
    var nd = prep.filter(function(p){ return pdone[p.id]; }).length;
    html += '<div class="label">'+nd+' '+t.of+' '+prep.length+' '+t.done+'</div><div class="list">';
    prep.forEach(function(p){
      var r = byId(p.id); if(!r) return;
      html += '<div class="prow'+(pdone[p.id]?' ok':'')+'"><input type="checkbox" data-pdone="'+p.id+'"'+(pdone[p.id]?' checked':'')+' aria-label="'+esc(r.n[i])+' '+t.done+'">'+
        '<button type="button" class="open" data-open="'+p.id+'"><b>'+esc(r.n[i])+'</b><span>'+num(p.m)+'× · '+esc(CATS[r.c][i])+'</span></button>'+
        '<button type="button" class="x" data-prm="'+p.id+'" aria-label="'+t.clear+'">×</button></div>';
    });
    html += '</div>';
    // yhdistetyt ainekset
    var tot = {}, order = [];
    var MASS = {g:1,kg:1000}, VOL = {ml:1,cl:10,dl:100,l:1000};
    prep.forEach(function(p){
      var r = byId(p.id); if(!r) return;
      r.p.forEach(function(part, ppi){ var pmul = multFor(r, ppi, p.m); part.i.forEach(function(x){
        var name = x[2+i], u = x[1], q = x[0], key, unit, val; if(u==='osa') pmul = 1;
        if(q===null){ key = norm(name)+'|-'; unit=''; val=0; }
        else if(MASS[u]){ key = norm(name)+'|g'; unit='g'; val=q*MASS[u]*pmul; }
        else if(VOL[u]){ key = norm(name)+'|ml'; unit='ml'; val=q*VOL[u]*pmul; }
        else { key = norm(name)+'|'+u; unit=u; val=q*pmul; }
        if(!tot[key]){ tot[key] = {name:name, unit:unit, q:0, none:q===null}; order.push(key); }
        tot[key].q += val;
      }); });
    });
    order.sort(function(a,b){ return tot[a].name.localeCompare(tot[b].name, lang); });
    html += '<div class="label">'+t.totals+'</div>'+order.map(function(k, n){
      var o = tot[k], id = 'tot'+n;
      return '<div class="ing"><input type="checkbox" id="'+id+'"><label class="name" for="'+id+'">'+esc(o.name)+'</label>'+
        (o.none ? '' : '<span class="qty">'+esc(fmt(o.q,o.unit,1))+'</span>')+'</div>';
    }).join('');
    html += '<button type="button" class="clear" id="prepclear">'+t.clear+'</button>';
    $('prep').innerHTML = html;
  }

  function render(){
    $('home').hidden = !(view==='home' || view==='favs');
    $('needs').hidden = view!=='needs';
    $('recipe').hidden = view!=='recipe';
    $('prep').hidden = view!=='prep';
    if(view==='recipe') renderRecipe(); else if(view==='prep') renderPrep(); else if(view==='needs') renderNeeds(); else renderHome();
    setTabs();
  }

  function route(){
    var h = location.hash.replace('#','');
    if(h.indexOf('r-')===0 && byId(h.slice(2))){
      var r = byId(h.slice(2));
      if(cur!==r){ freshOpen = isUnseen(r.id) ? r.id : null; markSeen(r.id); }
      if(cur!==r){ var pe = prepEntry(r.id), mb = multFromBase(r); mult = pe ? pe.m : (mb || 1); rtab = 'ing'; editMode = false; $('recipe').innerHTML=''; }
      cur = r; view = 'recipe';
      recent = [r.id].concat(recent.filter(function(x){ return x!==r.id; })).slice(0,12); save('recent', recent);
    } else {
      cur = null; view = h==='suosikit' ? 'favs' : h==='lista' ? 'prep' : h==='tarvitaan' ? 'needs' : 'home'; listView = view;
    }
    render(); $('scroller').scrollTop = 0; wake();
  }
  var HASH = {home:'', favs:'suosikit', prep:'lista', needs:'tarvitaan'};
  function go(v){ if(location.hash.replace('#','')===HASH[v]) route(); else location.hash = HASH[v]; }

  function setLang(l){ lang = l; save('lang', l); document.documentElement.lang = l; render(); renderTimers(); drawInstall(); }
  function syncPrep(){ var pe = cur && prepEntry(cur.id); if(pe){ pe.m = mult; save('prep', prep); } }

  document.addEventListener('click', function(e){
    var b = e.target.closest('button'); if(!b) return;
    if(b.dataset.lang){ setLang(b.dataset.lang); return; }
    if(b.id==='langone'){ setLang(lang==='fi' ? 'en' : 'fi'); return; }
    if(b.dataset.tab){ if(b.dataset.tab==='calc') openCalc(); else if(b.dataset.tab==='new') openNew(); else { if(b.dataset.tab==='home' && view==='home'){ cat='all'; $('q').value=''; } go(b.dataset.tab); } return; }
    if(b.dataset.cat){ cat = b.dataset.cat; $('q').value=''; renderHome(); $('scroller').scrollTop = 0; return; }
    if(b.dataset.rtab){ rtab = b.dataset.rtab; renderRecipe(); setTabs(); return; }
    if(b.dataset.sdone){ if(stepDone[b.dataset.sdone]) delete stepDone[b.dataset.sdone]; else stepDone[b.dataset.sdone]=1; renderRecipe(); setTabs(); return; }
    if(b.dataset.open){ location.hash = 'r-'+b.dataset.open; return; }
    if(b.id==='back'){ go(listView); return; }
    if(b.id==='favbtn'){ var k = favs.indexOf(cur.id); if(k>-1) favs.splice(k,1); else favs.push(cur.id); save('favs',favs); render(); return; }
    if(b.id==='prepbtn'){ var pe = prepEntry(cur.id); if(pe) prep = prep.filter(function(p){ return p!==pe; }); else prep.push({id:cur.id, m:mult}); save('prep',prep); render(); return; }
    if(b.dataset.prm){ prep = prep.filter(function(p){ return p.id!==b.dataset.prm; }); delete pdone[b.dataset.prm]; save('prep',prep); save('pdone',pdone); render(); return; }
    if(b.id==='prepclear'){ prep = []; pdone = {}; save('prep',prep); save('pdone',pdone); render(); return; }
    if(b.id==='minus'){ mult = Math.max(0.5, mult-0.5); syncPrep(); render(); return; }
    if(b.id==='plus'){ mult = mult+0.5; syncPrep(); render(); return; }
    if(b.dataset.p){ mult = +b.dataset.p; delete bases[cur.id]; save('base', bases); syncPrep(); render(); return; }
    if(b.id==='basego'){ applyBase(); return; }
    if(b.dataset.pp){ setPart(cur, +b.dataset.pp, +b.dataset.pv); renderRecipe(); setTabs(); return; }
    if(b.dataset.pstep){ var pi0 = +b.dataset.pstep; setPart(cur, pi0, multFor(cur, pi0) + (+b.dataset.d)); renderRecipe(); setTabs(); return; }
    if(b.dataset.have){ $('basesel').value = b.dataset.have; onBaseSel(); var sc = $('scalecard'), sv = $('scroller'); sv.scrollTo({top: sc.getBoundingClientRect().top - sv.getBoundingClientRect().top + sv.scrollTop - 80, behavior:'smooth'}); setTimeout(function(){ $('baseamt').focus(); $('baseamt').select(); }, 350); return; }
    if(b.dataset.timer){ startTimer(+b.dataset.timer, b.dataset.tname); return; }
    if(b.dataset.tstop){ stopTimer(+b.dataset.tstop); return; }
    if(b.dataset.close){ closeSheets(); return; }
    if(b.dataset.k){ key(b.dataset.k); return; }
    if(b.id==='calcuse'){ var v=calcVal(); if(v>0 && cur){ mult=v; syncPrep(); closeSheets(); render(); } return; }
    if(b.id==='haveok'){ applyHave(); return; }
    if(b.id==='newbtn'){ openNew(); return; }
    if(b.id==='sizebtn'){ zoomIdx = (zoomIdx+1)%ZOOMS.length; save('zoom', zoomIdx); applyZoom(); return; }
    if(b.id==='cookbtn'){ openCook(0); return; }
    if(b.id==='cookprev'){ openCook(cookAt-1); return; }
    if(b.id==='cooknext'){ if(cookAt>=cookSteps.length-1) closeCook(); else openCook(cookAt+1); return; }
    if(b.id==='cookclose'){ closeCook(); return; }
    if(b.id==='sharebtn'){ shareRecipe(); return; }
    if(b.id==='newsend'){ sendNew(); return; }
    if(b.dataset.rmimg){ shots.splice(+b.dataset.rmimg,1); drawShots(); return; }
  });

  /* ---------- Keittiön PIN (vain keittiön väelle) ---------- */
  var kpin = load('pin', ''), pinNext = null;
  function askPin(next){
    var t = T[lang]; pinNext = next;
    $('pintitle').textContent = t.pinTitle; $('pinhint').textContent = t.pinHint; $('pinok').textContent = t.pinOk; $('pinin').value = '';
    $('pinsheet').hidden = false; $('veil').hidden = false;
    setTimeout(function(){ $('pinin').focus(); }, 50);
  }
  function pinDone(){
    var v = $('pinin').value.replace(/\D/g,'');
    if(v.length < 3){ $('pinin').focus(); return; }
    kpin = v; save('pin', v); $('pinsheet').hidden = true;
    var keepVeil = !$('newsheet').hidden; if(!keepVeil) $('veil').hidden = true;
    if(pinNext){ var f = pinNext; pinNext = null; f(); }
  }
  document.addEventListener('click', function(e){ var b = e.target.closest('button'); if(b && b.id==='pinok') pinDone(); });
  document.addEventListener('keydown', function(e){ if(e.target.id==='pinin' && e.key==='Enter'){ e.preventDefault(); pinDone(); } });

  /* ---------- Uusi resepti kuvasta ---------- */
  var UPLOAD = (window.TINTA_UPLOAD || ''), shots = [];
  function openNew(){
    var t = T[lang];
    $('newtitle').textContent = t.newTitle; $('newhint').textContent = t.newHint;
    $('newnamelabel').textContent = t.newName; $('newpicktext').textContent = t.newPick;
    $('newsend').textContent = t.newSend; $('newstatus').textContent = UPLOAD ? '' : t.newOff;
    $('newsend').disabled = !UPLOAD || !shots.length;
    drawShots();
    $('newsheet').hidden = false; $('veil').hidden = false;
  }
  function drawShots(){
    var t = T[lang];
    $('newshots').innerHTML = shots.map(function(s,k){
      return '<div class="shot"><img src="'+s+'" alt="'+(k+1)+'"><button type="button" class="x" data-rmimg="'+k+'" aria-label="'+t.newRemove+'">×</button></div>';
    }).join('');
    $('newsend').disabled = !UPLOAD || !shots.length;
  }
  function shrink(file){
    return new Promise(function(res, rej){
      var url = URL.createObjectURL(file), img = new Image();
      img.onload = function(){
        var s = Math.min(1, 1800/Math.max(img.width, img.height)), c = document.createElement('canvas');
        c.width = Math.round(img.width*s); c.height = Math.round(img.height*s);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url); res(c.toDataURL('image/jpeg', 0.82));
      };
      img.onerror = function(){ URL.revokeObjectURL(url); rej(); };
      img.src = url;
    });
  }
  $('newfile').addEventListener('change', function(e){
    var fs = Array.prototype.slice.call(e.target.files || []).slice(0, 6 - shots.length);
    Promise.all(fs.map(shrink)).then(function(list){ shots = shots.concat(list); drawShots(); }).catch(function(){});
    e.target.value = '';
  });
  function sendNew(){
    var t = T[lang];
    if(!UPLOAD || !shots.length) return;
    $('newsend').disabled = true; $('newstatus').textContent = t.newSending;
    if(!kpin){ $('newsend').disabled = false; $('newstatus').textContent = ''; askPin(sendNew); return; }
    var body = JSON.stringify({pin: kpin, name: $('newname').value.trim().slice(0,80), images: shots.map(function(s){ return s.split(',')[1]; })});
    fetch(UPLOAD, {method:'POST', body: body}).then(function(r){ return r.json(); }).then(function(j){
      if(j && j.err==='pin'){ kpin=''; save('pin',''); $('newsend').disabled = false; $('newstatus').textContent = ''; askPin(sendNew); return; }
      if(!j || !j.ok) throw 0;
      shots = []; $('newname').value = ''; drawShots(); $('newstatus').textContent = t.newOk;
    }).catch(function(){ $('newstatus').textContent = t.newErr; $('newsend').disabled = false; });
  }
  document.addEventListener('change', function(e){
    var c = e.target;
    if(c.dataset && c.dataset.ing){ if(c.checked) ingDone[c.dataset.ing]=1; else delete ingDone[c.dataset.ing]; return; }
    if(c.dataset && c.dataset.pdone){ if(c.checked) pdone[c.dataset.pdone]=1; else delete pdone[c.dataset.pdone]; save('pdone',pdone); renderPrep(); }
  });
  $('q').addEventListener('input', renderHome);
  window.addEventListener('hashchange', route);

  /* ---------- "Minulla on" ---------- */
  var haveItem = null;
  function openHave(ref){
    var a = ref.split('-'), x = cur.p[+a[0]].i[+a[1]], t = T[lang];
    haveItem = x;
    $('havetitle').textContent = x[2+L()];
    $('havehint').textContent = t.havehint.replace('{q}', fmt(x[0],x[1]));
    $('haveunit').textContent = U[x[1]] ? U[x[1]][L()] : x[1];
    $('havelabel').textContent = t.have;
    $('haveok').textContent = t.haveok;
    $('havein').value = '';
    $('havesheet').hidden = false; $('veil').hidden = false;
    setTimeout(function(){ $('havein').focus(); }, 50);
  }
  function applyHave(){
    var v = parseFloat(String($('havein').value).replace(',', '.'));
    if(!(v>0) || !haveItem){ $('havein').focus(); return; }
    mult = v / haveItem[0]; syncPrep();
    closeSheets(); render();
  }
  $('havein').addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); applyHave(); } });

  /* ---------- Laskin ---------- */
  var acc = null, op = null, curv = '0', fresh = true;
  function show(){ $('calcdisp').textContent = curv.replace('.', lang==='fi' ? ',' : '.'); $('calcexp').textContent = acc===null ? '' : num(acc)+' '+op; }
  function calc(a,o,b){ return o==='+'?a+b : o==='−'?a-b : o==='×'?a*b : o==='÷'?(b===0?NaN:a/b) : b; }
  function calcVal(){ var v = parseFloat(curv); if(acc!==null && op) v = calc(acc,op,v); return Math.round(v*1e6)/1e6; }
  function key(k){
    if(/^[0-9]$/.test(k)){ curv = (fresh || curv==='0') ? k : (curv.length<12 ? curv+k : curv); fresh=false; }
    else if(k==='.'){ if(fresh){curv='0.';fresh=false;} else if(curv.indexOf('.')<0) curv+='.'; }
    else if(k==='C'){ acc=null; op=null; curv='0'; fresh=true; }
    else if(k==='back'){ curv = curv.length>1 ? curv.slice(0,-1) : '0'; }
    else if(k==='='){ if(op!==null){ var r=calcVal(); curv = isFinite(r) ? String(r) : '0'; acc=null; op=null; fresh=true; } }
    else { if(op!==null && !fresh){ var r2=calcVal(); acc = isFinite(r2)?r2:0; } else if(acc===null){ acc=parseFloat(curv); } op=k; fresh=true; curv = String(acc); }
    show();
  }
  function openCalc(){
    var t = T[lang];
    $('calctitle').textContent = t.calc;
    $('calcuse').hidden = view!=='recipe'; $('calcuse').textContent = t.calcuse;
    show();
    $('calcsheet').hidden = false; $('veil').hidden = false;
  }
  function closeSheets(){ $('calcsheet').hidden = true; $('havesheet').hidden = true; $('newsheet').hidden = true; $('pinsheet').hidden = true; $('instsheet').hidden = true; $('veil').hidden = true; }
  $('veil').addEventListener('click', closeSheets);
  document.addEventListener('keydown', function(e){
    if($('calcsheet').hidden){ if(e.key==='Escape') closeSheets(); return; }
    var m = {'*':'×','x':'×','/':'÷','-':'−','+':'+','Enter':'=','=':'=','Backspace':'back','Escape':'close',',':'.','.':'.'};
    var k = /^[0-9]$/.test(e.key) ? e.key : m[e.key];
    if(k==='close'){ closeSheets(); } else if(k){ e.preventDefault(); key(k); }
  });

  /* ---------- Ajastimet ---------- */
  var timers = load('timers', []), tid = 0, actx = null;
  timers.forEach(function(x){ tid = Math.max(tid, x.id); });
  function beep(){
    try{
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      [0, .35, .7].forEach(function(d){
        var o = actx.createOscillator(), g = actx.createGain();
        o.frequency.value = 880; o.connect(g); g.connect(actx.destination);
        g.gain.setValueAtTime(0.0001, actx.currentTime+d); g.gain.exponentialRampToValueAtTime(0.4, actx.currentTime+d+0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, actx.currentTime+d+0.3);
        o.start(actx.currentTime+d); o.stop(actx.currentTime+d+0.32);
      });
    }catch(e){}
    try{ navigator.vibrate && navigator.vibrate([300,150,300,150,300]); }catch(e){}
  }
  function startTimer(sec, name){
    try{ actx = actx || new (window.AudioContext || window.webkitAudioContext)(); if(actx.state==='suspended') actx.resume(); }catch(e){}
    timers.push({id:++tid, name:name, end:Date.now()+sec*1000, rang:false}); save('timers', timers); renderTimers();
  }
  function stopTimer(id){ timers = timers.filter(function(x){ return x.id!==id; }); save('timers', timers); renderTimers(); }
  function renderTimers(){
    var t = T[lang], now = Date.now();
    $('timers').innerHTML = timers.map(function(x){
      var left = Math.max(0, Math.round((x.end-now)/1000));
      return '<div class="timer'+(left===0?' ring':'')+'"><span class="tn">'+esc(x.name)+'</span><span class="tv">'+(left===0 ? t.ready : clock(left))+'</span>'+
        '<button type="button" data-tstop="'+x.id+'" aria-label="'+t.stop+'">×</button></div>';
    }).join('');
  }
  setInterval(function(){
    if(!timers.length) return;
    var now = Date.now(), rang = false;
    timers.forEach(function(x){ if(!x.rang && x.end<=now){ x.rang = true; rang = true; } });
    if(rang){ beep(); save('timers', timers); }
    else if(timers.some(function(x){ return x.rang && (Math.floor((now-x.end)/1000)%5===0); })) beep();
    renderTimers();
  }, 1000);

  /* ---------- Näyttö pysyy päällä reseptissä ja ajastimen aikana ---------- */
  var lock = null;
  function wake(){
    try{
      var want = view==='recipe' || timers.length>0;
      if(want && navigator.wakeLock && !lock){ navigator.wakeLock.request('screen').then(function(l){ lock=l; l.addEventListener('release',function(){ lock=null; }); }).catch(function(){}); }
      else if(!want && lock){ lock.release(); lock=null; }
    }catch(e){}
  }
  document.addEventListener('visibilitychange', function(){ if(document.visibilityState==='visible') wake(); });

  document.documentElement.lang = lang;
  function onBaseSel(){
    var x = ingAt(cur, $('basesel').value); if(!x) return;
    var a = niceAmount(x[0]*mult, x[1]);
    $('baseunit').innerHTML = unitsFor(x[1]).map(function(u){ return '<option value="'+u+'"'+(u===a.u?' selected':'')+'>'+esc(U[u]?U[u][L()]:u)+'</option>'; }).join('');
    $('baseamt').value = String(a.v).replace('.', lang==='fi'?',':'.');
  }
  document.addEventListener('change', function(e){ if(e.target.id==='basesel') onBaseSel(); });
  document.addEventListener('keydown', function(e){ if(e.target.id==='baseamt' && e.key==='Enter'){ e.preventDefault(); applyBase(); } });

  /* ---------- Tekstin koko ---------- */
  var ZOOMS = [1, 1.15, 1.3], zoomIdx = load('zoom', 0); if(!(zoomIdx>=0 && zoomIdx<3)) zoomIdx = 0;
  function applyZoom(){ document.documentElement.style.setProperty('--z', ZOOMS[zoomIdx]); }
  applyZoom();

  /* ---------- Keittiön yhteiset muutokset (näkyvät kaikille) ---------- */
  var changes = load('changes', {notes:{}, edits:{}}), editMode = false, myName = load('name', '');
  var seen = load('seen', {}), freshOpen = null;
  function latest(id){
    var m = '';
    ((changes.notes||{})[id] || []).forEach(function(n){ if(n.at > m) m = n.at; });
    var e = (changes.edits||{})[id] || {}; Object.keys(e).forEach(function(k){ if(e[k].at > m) m = e[k].at; });
    return m;
  }
  function lastBy(id){
    var best = null;
    ((changes.notes||{})[id] || []).forEach(function(n){ if(!best || n.at > best.at) best = n; });
    var e = (changes.edits||{})[id] || {}; Object.keys(e).forEach(function(k){ if(!best || e[k].at > best.at) best = e[k]; });
    return best;
  }
  function isUnseen(id){ var m = latest(id); return !!m && (!seen[id] || m > seen[id]); }
  function unseenList(){ return R.filter(function(r){ return isUnseen(r.id); }).sort(function(a,b){ return latest(b.id) > latest(a.id) ? 1 : -1; }); }
  function markSeen(id){ var m = latest(id); if(m){ seen[id] = m; save('seen', seen); } }
  function updBanner(r){
    if(freshOpen!==r.id) return '';
    var t = T[lang], lb = lastBy(r.id);
    return '<div class="updbanner"><div class="k">🔔 '+t.updTitle+'</div><p>'+t.updUse+'</p>'+(lb ? '<span>'+esc(lb.by || t.someone)+' · '+when(lb.at)+'</span>' : '')+'</div>';
  }
  function applyEdits(){
    R.forEach(function(r){ r.p.forEach(function(p){ p.i.forEach(function(x){ if(x._o!==undefined){ x[0] = x._o; delete x._o; delete x._e; } }); }); });
    Object.keys(changes.edits || {}).forEach(function(id){
      var r = byId(id); if(!r) return;
      Object.keys(changes.edits[id]).forEach(function(ref){
        var x = ingAt(r, ref), e = changes.edits[id][ref]; if(!x || x[0]===null) return;
        x._o = x[0]; x._e = e; x[0] = e.q;
      });
    });
  }
  function when(at){ try{ var d = new Date(at); return d.toLocaleDateString(lang==='fi'?'fi-FI':'en-GB', {day:'numeric', month:'numeric'})+' '+d.toLocaleTimeString(lang==='fi'?'fi-FI':'en-GB', {hour:'2-digit', minute:'2-digit'}); }catch(e){ return ''; } }
  function kitchenNotes(r){
    var t = T[lang], ns = ((changes.notes||{})[r.id] || []).slice().reverse();
    var ne = Object.keys((changes.edits||{})[r.id] || {}).length;
    if(!ns.length && !ne) return '';
    return '<div class="knotes"><div class="k">'+t.kitchen+'</div>'+
      (ne ? '<p class="kedit">'+t.editsOn.replace('{n}', ne)+'</p>' : '')+
      ns.map(function(n){ return '<div class="kn"><p>'+esc(n.t)+'</p><span>'+esc(n.by || t.someone)+' · '+when(n.at)+'</span>'+'</div>'; }).join('')+'</div>';
  }
  function nameField(){ var t = T[lang]; return '<label class="field" for="myname"><span>'+t.yourName+'</span><input id="myname" type="text" autocomplete="name" value="'+esc(myName)+'"></label>'; }
  function post(body){
    if(!UPLOAD) return Promise.reject('off');
    if(!kpin) return Promise.reject('pin');
    body.pin = kpin;
    return fetch(UPLOAD, {method:'POST', body: JSON.stringify(body)}).then(function(r){ return r.json(); }).then(function(j){
      if(j && j.err==='pin'){ kpin=''; save('pin',''); throw 'pin'; }
      if(!j || !j.ok) throw 0;
      if(j.notes){ changes = {notes:j.notes, edits:j.edits||{}, needs:j.needs||changes.needs||[]}; save('changes', changes); applyEdits(); }
      return j;
    });
  }
  function fetchChanges(){
    if(!UPLOAD) return;
    fetch(UPLOAD+'?what=changes', {cache:'no-store'}).then(function(r){ return r.json(); }).then(function(j){
      if(!j || !j.ok) return;
      var before = newNeeds().map(function(x){ return x.id; });
      changes = {notes:j.notes||{}, edits:j.edits||{}, needs:j.needs||[]}; save('changes', changes); applyEdits();
      announce(before);
      if(view==='recipe' && !editMode){ renderRecipe(); setTabs(); } else if(view!=='recipe' && !(view==='needs' && document.activeElement && document.activeElement.id==='needin')) render(); else setTabs();
    }).catch(function(){});
  }
  function keepName(){ var el = $('myname'); if(el){ myName = el.value.trim().slice(0,40); save('name', myName); } }
  function saveNote(){
    var t = T[lang], txt = $('noteta').value.trim(); keepName();
    if(!txt){ $('noteta').focus(); return; }
    $('notesave').disabled = true; $('notestatus').textContent = t.saving;
    post({action:'note', id:cur.id, text:txt, by:myName}).then(function(){ renderRecipe(); setTabs(); }).catch(function(e){
      $('notesave').disabled = false; $('notestatus').textContent = e==='off' ? t.newOff : e==='pin' ? '' : t.saveErr; if(e==='pin') askPin(saveNote); });
  }
  function saveEdits(){
    var t = T[lang], q = {}, n = 0; keepName();
    document.querySelectorAll('[data-eref]').forEach(function(inp){
      var x = ingAt(cur, inp.dataset.eref), v = parseFloat(String(inp.value).replace(',', '.'));
      if(!x || !(v>=0)) return;
      if(Math.abs(v - x[0]) > 1e-9){ var orig = x._o!==undefined ? x._o : x[0]; q[inp.dataset.eref] = Math.abs(v-orig)<1e-9 ? null : v; n++; }
    });
    if(!n){ editMode = false; renderRecipe(); return; }
    $('editsave').disabled = true; $('editstatus').textContent = t.saving;
    var why = $('editwhy').value.trim();
    post({action:'edit', id:cur.id, q:q, by:myName, text: why || t.autoNote.replace('{n}', n)}).then(function(){ editMode = false; renderRecipe(); setTabs(); }).catch(function(e){
      $('editsave').disabled = false; $('editstatus').textContent = e==='off' ? t.newOff : e==='pin' ? '' : t.saveErr; if(e==='pin') askPin(saveEdits); });
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('button'); if(!b) return;
    if(b.id==='editbtn'){ editMode = true; renderRecipe(); return; }
    if(b.id==='editcancel'){ editMode = false; renderRecipe(); return; }
    if(b.id==='editsave'){ saveEdits(); return; }
    if(b.id==='notesave'){ saveNote(); return; }
  });
  applyEdits();
  setTimeout(fetchChanges, 300);
  setInterval(function(){ if(document.visibilityState==='visible') fetchChanges(); }, 60000);
  document.addEventListener('visibilitychange', function(){ if(document.visibilityState==='visible') fetchChanges(); });

  /* ---------- Tarvitaan: mitä keittiö tarvitsee (näkyy kaikille) ---------- */
  var seenNeeds = load('seenNeeds', '');
  function openNeeds(){ return ((changes.needs)||[]).filter(function(x){ return !x.done; }); }
  function newNeeds(){ return openNeeds().filter(function(x){ return x.at > seenNeeds && x.by !== myName; }); }
  function announce(beforeIds){
    var fresh = newNeeds().filter(function(x){ return beforeIds.indexOf(x.id) < 0; });
    if(!fresh.length || view==='needs') return;
    var t = T[lang], x = fresh[fresh.length-1];
    toast('🛒 '+t.needNew+': '+x.t+(x.by ? ' · '+x.by : ''));
  }
  var toastT = null;
  function toast(msg){
    var el = $('toast'); el.textContent = msg; el.hidden = false;
    try{ navigator.vibrate && navigator.vibrate([120,80,120]); }catch(e){}
    clearTimeout(toastT); toastT = setTimeout(function(){ el.hidden = true; }, 6000);
  }
  function renderNeeds(){
    var t = T[lang], list = (changes.needs||[]).slice().reverse();
    var open = list.filter(function(x){ return !x.done; }), done = list.filter(function(x){ return x.done && (Date.now()-Date.parse(x.doneAt||x.at)) < 3*864e5; });
    var html = '<div class="top"><span class="vtitle">'+t.tNeeds+'</span>'+LANGS+'</div>'+
      '<h1 class="big">'+t.needTitle+'</h1><p class="sub">'+t.needSub+'</p>'+
      '<div class="needform"><label class="hint" for="needin">'+t.needAsk+'</label>'+
      '<div class="brow"><input id="needin" type="text" autocomplete="off" maxlength="200" placeholder="'+t.needEx+'"><button type="button" class="calcgo" id="needsend">'+t.needSend+'</button></div>'+
      '<p class="status" id="needstatus"></p></div>'+
      '<h2 class="label">'+t.needOpen+' · '+open.length+'</h2>'+
      (open.length ? '<div class="card list">'+open.map(function(x){
        var isNew = x.at > seenNeeds && x.by !== myName;
        return '<div class="nrow'+(isNew?' fresh':'')+'"><div class="t"><b>'+esc(x.t)+'</b><span>'+esc(x.by||t.someone)+' · '+when(x.at)+'</span></div>'+
          '<button type="button" class="nbtn" data-needdone="'+esc(x.id)+'">✓ '+t.needDone+'</button></div>'; }).join('')+'</div>' : '<p class="empty">'+t.needNone+'</p>')+
      (done.length ? '<h2 class="label">'+t.needDoneList+'</h2><div class="card list">'+done.map(function(x){
        return '<div class="nrow ok"><div class="t"><b>'+esc(x.t)+'</b><span>✓ '+esc(x.doneBy||t.someone)+' · '+when(x.doneAt||x.at)+'</span></div>'+
          '<button type="button" class="nbtn ghost" data-needundo="'+esc(x.id)+'">'+t.needUndo+'</button></div>'; }).join('')+'</div>' : '');
    $('needs').innerHTML = html;
    document.querySelectorAll('#needs [data-lang]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });
    var latest = (changes.needs||[]).reduce(function(m,x){ return x.at > m ? x.at : m; }, seenNeeds);
    if(latest !== seenNeeds){ seenNeeds = latest; save('seenNeeds', seenNeeds); setTimeout(setTabs, 0); }
  }
  function sendNeed(){
    var t = T[lang], v = $('needin').value.trim(); if(!v){ $('needin').focus(); return; }
    $('needsend').disabled = true; $('needstatus').textContent = t.saving;
    post({action:'need', text:v, by:myName}).then(function(){ renderNeeds(); setTabs(); toast('✓ '+t.needSent); }).catch(function(e){
      $('needsend').disabled = false; $('needstatus').textContent = e==='off' ? t.newOff : e==='pin' ? '' : t.saveErr; if(e==='pin') askPin(sendNeed); });
  }
  function markNeed(id, done){
    post({action:'needdone', id:id, done:done, by:myName}).then(function(){ renderNeeds(); setTabs(); }).catch(function(e){ if(e==='pin') askPin(function(){ markNeed(id, done); }); });
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('button'); if(!b) return;
    if(b.id==='needsend'){ sendNeed(); return; }
    if(b.dataset.needdone){ markNeed(b.dataset.needdone, true); return; }
    if(b.dataset.needundo){ markNeed(b.dataset.needundo, false); return; }
    if(b.id==='toast'){ $('toast').hidden = true; go('needs'); return; }
    if(b.id==='welcomeok'){ welcomeDone(); return; }
    if(b.id==='avatar'){ welcome(true); return; }
    if(b.id==='welcomeskip'){ $('welcome').hidden = true; $('veil').hidden = true; save('welcomed', 1); return; }
  });
  document.addEventListener('keydown', function(e){ if(e.target.id==='needin' && e.key==='Enter'){ e.preventDefault(); sendNeed(); } });

  /* ---------- Tervetuloa: nimi + koodi kerran ---------- */
  function welcome(force){
    if(!UPLOAD || (!force && ((kpin && myName) || load('welcomed', 0)))) return;
    var t = T[lang];
    $('wtitle').textContent = t.wTitle; $('whint').textContent = t.wHint; $('wnamel').textContent = t.yourName; $('wpinl').textContent = t.pinTitle;
    $('welcomeok').textContent = t.wStart; $('welcomeskip').textContent = t.wSkip; $('wname').value = myName; $('wstatus').textContent = '';
    $('welcome').hidden = false; $('veil').hidden = false;
  }
  function welcomeDone(){
    var t = T[lang], nm = $('wname').value.trim().slice(0,40), pn = $('wpin').value.replace(/\D/g,'');
    if(!nm){ $('wname').focus(); return; }
    if(pn.length < 3){ $('wpin').focus(); return; }
    $('welcomeok').disabled = true; $('wstatus').textContent = t.saving;
    fetch(UPLOAD, {method:'POST', body: JSON.stringify({action:'ping', pin:pn})}).then(function(r){ return r.json(); }).then(function(j){
      $('welcomeok').disabled = false;
      if(j && j.ok){ myName = nm; save('name', nm); kpin = pn; save('pin', pn); save('welcomed', 1); $('welcome').hidden = true; $('veil').hidden = true; toast('✓ '+t.wOk+', '+nm); render(); }
      else { $('wstatus').textContent = j && j.err==='wait' ? t.wWait : t.wBad; $('wpin').value=''; $('wpin').focus(); }
    }).catch(function(){ $('welcomeok').disabled = false; $('wstatus').textContent = t.saveErr; });
  }
  setTimeout(welcome, 800);

  /* ---------- Jaa resepti tekstinä ---------- */
  function recipeText(){
    var r = cur, i = L(), t = T[lang], out = [r.n[i]+(mult!==1 ? ' ('+num(mult)+'×)' : ''), ''];
    r.p.forEach(function(p, pi){
      if(p.t) out.push('— '+p.t[i]+(r.p.length>1 ? ' ('+num(multFor(r, pi))+'×)' : '')+' —');
      p.i.forEach(function(x){ out.push('• '+(x[0]===null ? '' : fmt(x[0],x[1],multFor(r, pi))+' ')+x[2+i]); });
      if(p.s && p.s.length){ out.push(''); p.s.forEach(function(s,n){ out.push((n+1)+'. '+s[i]); }); }
      out.push('');
    });
    return out.join('\n').trim();
  }
  function shareRecipe(){
    var text = recipeText(), t = T[lang];
    if(navigator.share){ navigator.share({title: cur.n[L()], text: text}).catch(function(){}); return; }
    try{ navigator.clipboard.writeText(text).then(function(){ $('sharebtn').textContent = '✓ '+t.copied; }); }catch(e){}
  }

  /* ---------- Kokkaustila: vaihe kerrallaan ---------- */
  var cookSteps = [], cookAt = 0;
  function stepIngs(part, text){
    var tx = norm(text);
    return part.i.filter(function(x){
      return [x[2], x[3]].some(function(nm){ var w = norm(nm).split(/[ ,(]/)[0]; return w.length>2 && tx.indexOf(w.slice(0, Math.max(4, w.length-2)))>-1; });
    });
  }
  function openCook(n){
    var r = cur; cookSteps = [];
    r.p.forEach(function(p, pi){ (p.s||[]).forEach(function(s, si){ cookSteps.push({p:p, pi:pi, si:si, s:s}); }); });
    if(!cookSteps.length) return;
    cookAt = Math.max(0, Math.min(n, cookSteps.length-1));
    var t = T[lang], i = L(), c = cookSteps[cookAt], sec = findTime(c.s[i]) || findTime(c.s[0]);
    var ings = stepIngs(c.p, c.s[0]+' '+c.s[1]);
    var bar = cookSteps.map(function(_, k){ return '<i class="'+(k<=cookAt?'on':'')+'"></i>'; }).join('');
    $('cook').innerHTML =
      '<div class="ctop"><button type="button" class="x" id="cookclose" aria-label="'+t.cookClose+'">×</button><div class="cname">'+esc(r.n[i])+(mult!==1?' · '+num(mult)+'×':'')+'</div><span class="ccount">'+(cookAt+1)+' / '+cookSteps.length+'</span></div>'+
      '<div class="cbar" aria-hidden="true">'+bar+'</div>'+
      '<div class="cbody">'+(c.p.t ? '<div class="cpart">'+esc(c.p.t[i])+'</div>' : '')+
      '<div class="cstep">'+t.cookStep+' '+(c.si+1)+'</div><p class="ctext">'+esc(c.s[i])+'</p>'+
      (ings.length ? '<div class="chere"><div class="k">'+t.cookHere+'</div>'+ings.map(function(x){ return '<div class="crow"><span>'+esc(x[2+i])+'</span><b>'+esc(fmt(x[0],x[1],multFor(r, c.pi)))+'</b></div>'; }).join('')+'</div>' : '')+
      (sec ? '<button type="button" class="tbtn big" data-timer="'+sec+'" data-tname="'+esc(r.n[i]+' · '+(c.si+1))+'">'+ICON.clock+' '+t.timer+' '+clock(sec)+'</button>' : '')+
      '</div><div class="cnav"><button type="button" id="cookprev"'+(cookAt===0?' disabled':'')+'>'+t.cookPrev+'</button><button type="button" id="cooknext" class="go">'+(cookAt===cookSteps.length-1 ? t.cookDone : t.cookNext)+'</button></div>';
    $('cook').hidden = false; document.body.classList.add('cooking'); wake();
  }
  function closeCook(){ $('cook').hidden = true; document.body.classList.remove('cooking'); }
  document.addEventListener('keydown', function(e){ if($('cook').hidden) return; if(e.key==='ArrowRight') openCook(cookAt+1); if(e.key==='ArrowLeft') openCook(cookAt-1); if(e.key==='Escape') closeCook(); });
  window.addEventListener('hashchange', closeCook);

  /* ---------- Uusi versio: lataa automaattisesti ---------- */
  function checkVersion(){
    if(!window.TINTA_VER || location.protocol.indexOf('http')!==0) return;
    fetch('version.txt?'+Date.now(), {cache:'no-store'}).then(function(r){ return r.ok ? r.text() : ''; }).then(function(v){
      v = (v||'').trim(); if(!v || v===window.TINTA_VER) return;
      // نعيد التحميل مرة وحدة بس لكل نسخة، حتى ما يدخل بدوامة إعادة تحميل
      try { if(sessionStorage.getItem('tinta-reloaded')===v) return; sessionStorage.setItem('tinta-reloaded', v); } catch(e){ return; }
      location.reload();
    }).catch(function(){});
  }
  // الفحص يصير بعد ما تخلص حركة الشعار، حتى ما يقطعها
  var vT; document.addEventListener('visibilitychange', function(){ if(document.visibilityState==='visible'){ clearTimeout(vT); vT=setTimeout(checkVersion, 9000); } });
  setTimeout(checkVersion, 9000);

  // ---- Lisää kotinäytölle / زر "أضف للشاشة الرئيسية" للي يفتح الرابط بالمتصفح ----
  var IA = {
    fi:{t:'Lisää Tintå kotinäytölle',s:'Avautuu kuin sovellus, koko näytöllä.',b:'Lisää',how:'Lisää kotinäytölle',ok:'Selvä',
      ios:['Napauta <b>Jaa</b>-painiketta {share}. Uusissa iPhoneissa se on alhaalla <b>•••</b>-valikossa.','Valitse listasta <b>Lisää Koti-valikkoon</b> {plus}','Napauta <b>Lisää</b>. Tintå on nyt kotinäytölläsi.'],
      and:['Napauta selaimen valikkoa {dots} oikeasta yläkulmasta','Valitse <b>Asenna sovellus</b> tai <b>Lisää aloitusnäytölle</b>','Vahvista <b>Asenna</b>. Tintå on nyt kotinäytölläsi.']},
    en:{t:'Add Tintå to your home screen',s:'Opens like an app, full screen.',b:'Add',how:'Add to home screen',ok:'Got it',
      ios:['Tap the <b>Share</b> button {share}. On newer iPhones it is in the <b>•••</b> menu at the bottom.','Choose <b>Add to Home Screen</b> {plus}','Tap <b>Add</b>. Tintå is now on your home screen.'],
      and:['Tap the browser menu {dots} in the top right','Choose <b>Install app</b> or <b>Add to Home screen</b>','Confirm <b>Install</b>. Tintå is now on your home screen.']}
  };
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent || '') || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var deferredInstall = null;
  var IICON = {share:'<svg viewBox="0 0 24 24" fill="none" stroke="#5AA0FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M8 7l4-4 4 4"/><path d="M5 11v9h14v-9"/></svg>',
    plus:'<svg viewBox="0 0 24 24" fill="none" stroke="#F3EEE6" stroke-width="2" stroke-linecap="round"><rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/></svg>',
    dots:'<svg viewBox="0 0 24 24" fill="#F3EEE6"><circle cx="12" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="12" cy="19" r="2"/></svg>'};
  function drawInstall(){ var el = $('install'); if(!el) return;
    if(standalone || Date.now() < (+load('instx', 0) || 0)){ el.hidden = true; return; }
    var a = IA[lang] || IA.fi;
    el.innerHTML = '<img src="icon-180.png" alt=""><div class="it"><b>'+a.t+'</b><span>'+a.s+'</span></div><button type="button" class="ib" id="instgo">'+a.b+'</button><button type="button" class="ix" id="instno" aria-label="'+T[lang].cancel+'">×</button>';
    el.hidden = false; }
  function showHow(){ var a = IA[lang] || IA.fi, st = isIOS ? a.ios : a.and;
    $('insttitle').textContent = a.how; $('instok').textContent = a.ok;
    $('isteps').innerHTML = st.map(function(x, n){ return '<li><span class="n">'+(n+1)+'</span><span>'+x.replace(/\{(\w+)\}/g, function(m, k){ return '<span class="ic">'+IICON[k]+'</span>'; })+'</span></li>'; }).join('');
    $('instsheet').hidden = false; $('veil').hidden = false; }
  window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); deferredInstall = e; drawInstall(); });
  window.addEventListener('appinstalled', function(){ deferredInstall = null; save('instx', Date.now() + 1e12); drawInstall(); });
  document.addEventListener('click', function(e){ var b = e.target.closest && e.target.closest('button'); if(!b) return;
    if(b.id === 'instno'){ save('instx', Date.now() + 3*864e5); drawInstall(); }
    else if(b.id === 'instgo'){
      if(deferredInstall){ deferredInstall.prompt(); deferredInstall.userChoice.then(function(c){ if(c && c.outcome === 'accepted') save('instx', Date.now() + 1e12); deferredInstall = null; drawInstall(); }).catch(function(){}); }
      else showHow(); }
    else if(b.id === 'instok'){ closeSheets(); } });
  drawInstall();

  route(); renderTimers();
})();
