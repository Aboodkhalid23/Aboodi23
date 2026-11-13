(function(){
  var T = {
    fi:{title:'Reseptit',search:'Hae: pesto, voi, kantarelli…',all:'Kaikki',recipes:'reseptiä',results:'Tulokset',none:'Ei reseptejä haulla',
      batch:'Määrä',auto:'Ainekset lasketaan itse',ingredients:'Ainekset',method:'Valmistus',back:'Takaisin',
      nomethod:'Paperissa ei ole kirjoitettua valmistusohjetta.',original:'Näytä alkuperäinen paperi',minus:'Vähemmän',plus:'Enemmän',vegan:'vegaani',parts:'osaa',
      foot:'Reseptit luettu keittiön paperikansiosta. Jos jokin näyttää väärältä, tarkista alkuperäinen paperi.',
      have:'Minulla on',havehint:'Reseptissä {q}. Kirjoita, paljonko sinulla on, niin kaikki muut määrät lasketaan sen mukaan.',haveok:'Laske',
      calc:'Laskin',calcuse:'Käytä määränä',tiphave:'Napauta määrää: laske kaikki sen mukaan, mitä sinulla on.',
      gen:'Paperissa ei ollut ohjetta, joten tämä on lisätty. Tarkista keittiömestarilta.',
      tRecipes:'Reseptit',tFavs:'Suosikit',tPrep:'Prep-lista',tCalc:'Laskin',
      fav:'Lisää suosikkeihin',unfav:'Poista suosikeista',favs:'Suosikit',recent:'Viimeksi avatut',
      nofavs:'Ei vielä suosikkeja. Avaa resepti ja paina tähteä ☆.',
      addprep:'+ Lisää prep-listaan',inprep:'✓ Prep-listalla · poista',
      prepTitle:'Prep-lista',prepSub:'Tämän päivän valmistettavat',noprep:'Lista on tyhjä. Avaa resepti ja paina "Lisää prep-listaan".',
      totals:'Kaikki ainekset yhteensä',clear:'Tyhjennä lista',done:'valmis',of:'/',
      timer:'Ajastin',stop:'Pysäytä',ready:'Valmis!',
      newbtn:'Lisää uusi resepti kuvasta',newTitle:'Uusi resepti',newHint:'Ota kuva reseptipaperista. Jos resepti on usealla sivulla, lisää kaikki sivut. Resepti ilmestyy sovellukseen noin tunnin sisällä, suomeksi ja englanniksi.',
      newName:'Reseptin nimi (vapaaehtoinen)',newPick:'Ota kuva tai valitse',newSend:'Lähetä',newSending:'Lähetetään…',newOk:'Lähetetty! Resepti lisätään noin tunnin sisällä.',
      newErr:'Lähetys ei onnistunut. Tarkista netti ja yritä uudelleen.',newOff:'Kuvien lähetys ei ole vielä käytössä.',newPages:'sivua',newRemove:'Poista kuva',isNew:'uusi',cats:'Kategoriat',allAZ:'Kaikki reseptit A–Ö',allCats:'Kaikki kategoriat'},
    en:{title:'Recipes',search:'Search: pesto, butter, chanterelle…',all:'All',recipes:'recipes',results:'Results',none:'No recipes for',
      batch:'Batch',auto:'Amounts update automatically',ingredients:'Ingredients',method:'Method',back:'Back',
      nomethod:'No method is written on the paper.',original:'Show original paper',minus:'Less',plus:'More',vegan:'vegan',parts:'parts',
      foot:'Recipes read from the kitchen binder. If something looks wrong, check the original paper.',
      have:'I have',havehint:'The recipe uses {q}. Type how much you have and every other amount is worked out from it.',haveok:'Calculate',
      calc:'Calculator',calcuse:'Use as batch',tiphave:'Tap an amount to scale everything to what you have.',
      gen:'The paper had no method, so this was added. Check with the head chef.',
      tRecipes:'Recipes',tFavs:'Favourites',tPrep:'Prep list',tCalc:'Calculator',
      fav:'Add to favourites',unfav:'Remove from favourites',favs:'Favourites',recent:'Recently opened',
      nofavs:'No favourites yet. Open a recipe and tap the star ☆.',
      addprep:'+ Add to prep list',inprep:'✓ On prep list · remove',
      prepTitle:'Prep list',prepSub:'What to make today',noprep:'The list is empty. Open a recipe and tap "Add to prep list".',
      totals:'All ingredients combined',clear:'Clear list',done:'done',of:'/',
      timer:'Timer',stop:'Stop',ready:'Ready!',
      newbtn:'Add a new recipe from a photo',newTitle:'New recipe',newHint:'Take a photo of the recipe paper. If it has several pages, add all of them. The recipe appears in the app within about an hour, in Finnish and English.',
      newName:'Recipe name (optional)',newPick:'Take or choose a photo',newSend:'Send',newSending:'Sending…',newOk:'Sent! The recipe will be added within about an hour.',
      newErr:'Sending failed. Check the connection and try again.',newOff:'Photo upload is not switched on yet.',newPages:'pages',newRemove:'Remove photo',isNew:'new',cats:'Categories',allAZ:'All recipes A–Z',allCats:'All categories'}
  };
  var CATS = {
    kastike:['Kastikkeet ja dipit','Sauces & dips'], majo:['Majoneesit','Mayos'], oljy:['Öljyt ja vinegretit','Oils & dressings'],
    pesto:['Pestot','Pestos'], voi:['Voit','Butters'], liemi:['Liemet','Stocks'], keitto:['Keitot','Soups'], pohja:['Pohjat','Bases'],
    lisuke:['Lisukkeet ja risotot','Sides & risottos'], mari:['Marinadit','Marinades'], sailyke:['Hillot, chutneyt ja pikkelit','Jams, chutneys & pickles'],
    mauste:['Rapeat ja mausteet','Crunch & seasonings'], jalki:['Jälkiruoat','Desserts']
  };
  var U = {g:['g','g'],kg:['kg','kg'],ml:['ml','ml'],cl:['cl','cl'],dl:['dl','dl'],l:['l','l'],tl:['tl','tsp'],rkl:['rkl','tbsp'],kpl:['kpl','pcs'],
    prk:['prk','tub'],pss:['pss','bag'],pnt:['nippu','bunch'],rss:['rasia','box'],tlk:['tlk','can'],levy:['levyä','sheets'],tuubi:['tuubia','tubes'],osa:['osa','part']};
  var ICON = {
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
    var v = r>=100 ? Math.round(r) : r>=10 ? Math.round(r*10)/10 : Math.round(r*100)/100;
    return String(v).replace('.', lang==='fi' ? ',' : '.');
  }
  function fmt(q,u,m){
    if(q===null) return '';
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
    $('tab1').textContent = t.tRecipes; $('tab2').textContent = t.tFavs; $('tab3').textContent = t.tPrep; $('tab4').textContent = t.tCalc;
    document.querySelectorAll('[data-tab]').forEach(function(b){
      var on = (b.dataset.tab==='home' && (view==='home' || (view==='recipe' && listView==='home'))) ||
               (b.dataset.tab==='favs' && (view==='favs' || (view==='recipe' && listView==='favs'))) ||
               (b.dataset.tab==='prep' && (view==='prep' || (view==='recipe' && listView==='prep')));
      if(on) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current');
    });
    var n = prep.length; $('prepbadge').hidden = !n; $('prepbadge').textContent = n;
    document.querySelectorAll('[data-lang]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });
  }

  function rowHtml(r){
    var t = T[lang], i = L();
    var meta = CATS[r.c][i] + (r.p.length>1 ? ' · '+r.p.length+' '+t.parts : '');
    var fresh = r.added && (Date.now() - Date.parse(r.added)) < 14*864e5;
    return '<button type="button" class="row" data-open="'+r.id+'"><div class="t"><div class="n">'+esc(r.n[i])+
      (fresh?'<span class="tag">'+t.isNew+'</span>':'')+(r.v?'<span class="tag">'+t.vegan+'</span>':'')+'</div><div class="m">'+esc(r.n[1-i])+' · '+esc(meta)+'</div></div>'+
      (favs.indexOf(r.id)>-1 ? '<span class="star">★</span>' : '')+ICON.chev+'</button>';
  }

  function renderHome(){
    var t = T[lang], i = L(), fav = view==='favs';
    $('hometitle').textContent = fav ? t.favs : t.title;
    $('foot').textContent = t.foot;
    $('q').placeholder = t.search; $('q').setAttribute('aria-label', t.search);
    $('count').textContent = fav ? '' : R.length+' '+t.recipes;
    $('count').hidden = fav; document.querySelector('#home .search').hidden = fav;
    $('newbtn').hidden = fav; $('newbtntext').textContent = t.newbtn;
    var sortN = function(a,b){ return a.n[i].localeCompare(b.n[i], lang); };
    var html = '';
    if(fav){
      var f = favs.map(byId).filter(Boolean).sort(sortN);
      var rc = recent.map(byId).filter(Boolean).slice(0,8);
      html = (f.length ? '<div class="card list">'+f.map(rowHtml).join('')+'</div>' : '<p class="empty">'+t.nofavs+'</p>')+
        (rc.length ? '<h2 class="label">'+t.recent+'</h2><div class="card list">'+rc.map(rowHtml).join('')+'</div>' : '');
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
        (hits.length ? '<div class="card list">'+hits.map(rowHtml).join('')+'</div>' : '<p class="empty">'+esc(t.none)+' “'+esc($('q').value)+'”</p>');
    } else if(cat==='all'){
      var rc2 = recent.map(byId).filter(Boolean).slice(0,10);
      if(rc2.length) html += '<h2 class="label">'+t.recent+'</h2><div class="strip">'+rc2.map(function(r){
        return '<button type="button" class="mini" data-open="'+r.id+'"><b>'+esc(r.n[i])+'</b><span>'+esc(CATS[r.c][i])+'</span></button>'; }).join('')+'</div>';
      html += '<h2 class="label">'+t.cats+'</h2><div class="cats">'+
        '<button type="button" class="cat az" data-cat="az"><b>'+t.allAZ+'</b><span>'+R.length+' '+t.recipes+'</span></button>'+
        Object.keys(CATS).map(function(k){
          var n = R.filter(function(r){ return r.c===k; }).length; if(!n) return '';
          return '<button type="button" class="cat" data-cat="'+k+'"><b>'+esc(CATS[k][i])+'</b><span>'+n+' '+t.recipes+'</span></button>';
        }).join('')+'</div>';
    } else {
      var list = R.filter(function(r){ return cat==='az' || r.c===cat; }).sort(sortN);
      html = '<button type="button" class="crumb" data-cat="all">'+ICON.back+' '+t.allCats+'</button>'+
        '<h2 class="cathead">'+esc(cat==='az' ? t.allAZ : CATS[cat][i])+' <span>'+list.length+'</span></h2>'+
        '<div class="card list">'+list.map(rowHtml).join('')+'</div>';
    }
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
  function renderRecipe(){
    var r = cur, t = T[lang], i = L(), isFav = favs.indexOf(r.id)>-1, pe = prepEntry(r.id);
    var nIng = 0, nStep = 0; r.p.forEach(function(p){ nIng += p.i.length; nStep += (p.s||[]).length; });
    var html =
      '<div class="top"><button type="button" class="back" id="back">'+ICON.back+'<span>'+t.back+'</span></button>'+
      '<div class="tools"><button type="button" class="icon" id="favbtn" aria-pressed="'+isFav+'" aria-label="'+(isFav?t.unfav:t.fav)+'">'+ICON.star+'</button>'+LANGS+'</div></div>'+
      '<header class="rhead"><div class="eyebrow">'+esc(CATS[r.c][i])+(r.v?' · '+t.vegan:'')+(r.p.length>1?' · '+r.p.length+' '+t.parts:'')+'</div>'+
      '<h1 class="title">'+esc(r.n[i])+'</h1><div class="other">'+esc(r.n[1-i])+'</div></header>'+
      (r.note ? '<p class="callout">'+esc(r.note[i])+'</p>' : '')+
      '<div class="card scale"><div class="srow"><div><div class="k">'+t.batch+'</div><div class="h">'+t.auto+'</div></div>'+
      '<div class="step"><button type="button" id="minus" aria-label="'+t.minus+'">−</button><output id="pn" aria-live="polite">'+num(mult)+'×</output><button type="button" class="plus" id="plus" aria-label="'+t.plus+'">+</button></div></div>'+
      '<div class="quick">'+[0.5,1,2,3].map(function(v){return '<button type="button" data-p="'+v+'" aria-pressed="'+(v===mult)+'">'+num(v)+'×</button>'}).join('')+'</div>'+
      '<button type="button" class="addprep" id="prepbtn" aria-pressed="'+(!!pe)+'">'+(pe ? t.inprep : t.addprep)+'</button></div>'+
      '<div class="seg" role="tablist"><button type="button" role="tab" data-rtab="ing" aria-selected="'+(rtab==='ing')+'">'+t.ingredients+' <span>'+nIng+'</span></button>'+
      '<button type="button" role="tab" data-rtab="met" aria-selected="'+(rtab==='met')+'">'+t.method+' <span>'+nStep+'</span></button></div>';
    if(rtab==='ing'){
      html += '<p class="tip">'+t.tiphave+'</p>';
      r.p.forEach(function(p, pi){
        html += (p.t ? '<h2 class="part">'+esc(p.t[i])+'</h2>' : '')+'<div class="card">'+
          p.i.map(function(x,n){ var id='c'+pi+'-'+n, k=r.id+id;
            return '<div class="ing"><input type="checkbox" id="'+id+'" data-ing="'+k+'"'+(ingDone[k]?' checked':'')+'><label class="name" for="'+id+'">'+esc(x[2+i])+'</label>'+
            (x[0]===null ? '' : '<button type="button" class="qty" data-have="'+pi+'-'+n+'" aria-label="'+esc(t.have+': '+x[2+i])+'">'+esc(fmt(x[0],x[1]))+'</button>')+'</div>'; }).join('')+'</div>';
      });
    } else {
      var any = false;
      r.p.forEach(function(p, pi){
        if(!(p.s && p.s.length)) return; any = true;
        html += (p.t ? '<h2 class="part">'+esc(p.t[i])+'</h2>' : '')+(p.gen?'<p class="gen">'+t.gen+'</p>':'')+'<ol class="steps">'+p.s.map(function(s,n){
          var sec = findTime(s[i]) || findTime(s[0]), k = r.id+'s'+pi+'-'+n;
          return '<li class="'+(stepDone[k]?'ok':'')+'"><button type="button" class="num" data-sdone="'+k+'" aria-pressed="'+(!!stepDone[k])+'" aria-label="'+(n+1)+'">'+(stepDone[k]?'✓':(n+1))+'</button><div class="txt">'+esc(s[i])+
            (sec ? '<button type="button" class="tbtn" data-timer="'+sec+'" data-tname="'+esc(r.n[i]+' · '+(n+1))+'">'+ICON.clock+' '+t.timer+' '+clock(sec)+'</button>' : '')+'</div></li>';
        }).join('')+'</ol>';
      });
      if(!any) html += '<p class="nomethod">'+t.nomethod+'</p>';
    }
    html += '<a class="orig" href="https://drive.google.com/file/d/'+r.f+'/view" target="_blank" rel="noopener">'+t.original+' ↗</a>';
    $('recipe').innerHTML = html;
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
      r.p.forEach(function(part){ part.i.forEach(function(x){
        var name = x[2+i], u = x[1], q = x[0], key, unit, val;
        if(q===null){ key = norm(name)+'|-'; unit=''; val=0; }
        else if(MASS[u]){ key = norm(name)+'|g'; unit='g'; val=q*MASS[u]*p.m; }
        else if(VOL[u]){ key = norm(name)+'|ml'; unit='ml'; val=q*VOL[u]*p.m; }
        else { key = norm(name)+'|'+u; unit=u; val=q*p.m; }
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
    $('recipe').hidden = view!=='recipe';
    $('prep').hidden = view!=='prep';
    if(view==='recipe') renderRecipe(); else if(view==='prep') renderPrep(); else renderHome();
    setTabs();
  }

  function route(){
    var h = location.hash.replace('#','');
    if(h.indexOf('r-')===0 && byId(h.slice(2))){
      var r = byId(h.slice(2));
      if(cur!==r){ var pe = prepEntry(r.id); mult = pe ? pe.m : 1; rtab = 'ing'; $('recipe').innerHTML=''; }
      cur = r; view = 'recipe';
      recent = [r.id].concat(recent.filter(function(x){ return x!==r.id; })).slice(0,12); save('recent', recent);
    } else {
      cur = null; view = h==='suosikit' ? 'favs' : h==='lista' ? 'prep' : 'home'; listView = view;
    }
    render(); window.scrollTo(0,0); wake();
  }
  var HASH = {home:'', favs:'suosikit', prep:'lista'};
  function go(v){ if(location.hash.replace('#','')===HASH[v]) route(); else location.hash = HASH[v]; }

  function setLang(l){ lang = l; save('lang', l); document.documentElement.lang = l; render(); renderTimers(); }
  function syncPrep(){ var pe = cur && prepEntry(cur.id); if(pe){ pe.m = mult; save('prep', prep); } }

  document.addEventListener('click', function(e){
    var b = e.target.closest('button'); if(!b) return;
    if(b.dataset.lang){ setLang(b.dataset.lang); return; }
    if(b.dataset.tab){ if(b.dataset.tab==='calc') openCalc(); else { if(b.dataset.tab==='home' && view==='home'){ cat='all'; $('q').value=''; } go(b.dataset.tab); } return; }
    if(b.dataset.cat){ cat = b.dataset.cat; $('q').value=''; renderHome(); window.scrollTo(0,0); return; }
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
    if(b.dataset.p){ mult = +b.dataset.p; syncPrep(); render(); return; }
    if(b.dataset.have){ openHave(b.dataset.have); return; }
    if(b.dataset.timer){ startTimer(+b.dataset.timer, b.dataset.tname); return; }
    if(b.dataset.tstop){ stopTimer(+b.dataset.tstop); return; }
    if(b.dataset.close){ closeSheets(); return; }
    if(b.dataset.k){ key(b.dataset.k); return; }
    if(b.id==='calcuse'){ var v=calcVal(); if(v>0 && cur){ mult=v; syncPrep(); closeSheets(); render(); } return; }
    if(b.id==='haveok'){ applyHave(); return; }
    if(b.id==='newbtn'){ openNew(); return; }
    if(b.id==='newsend'){ sendNew(); return; }
    if(b.dataset.rmimg){ shots.splice(+b.dataset.rmimg,1); drawShots(); return; }
  });

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
    var body = JSON.stringify({name: $('newname').value.trim().slice(0,80), images: shots.map(function(s){ return s.split(',')[1]; })});
    fetch(UPLOAD, {method:'POST', body: body}).then(function(r){ return r.json(); }).then(function(j){
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
  function closeSheets(){ $('calcsheet').hidden = true; $('havesheet').hidden = true; $('newsheet').hidden = true; $('veil').hidden = true; }
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
  route(); renderTimers();
})();
