/* Tintå: piirretyt ruokakuvat jokaiselle reseptille (SVG). / رسوم الأكلات لكل وصفة. */
var TintaDish = (function(){
  var uid = 0;
  function id(p){ return p + (++uid); }
  function shadow(){ return '<ellipse cx="100" cy="176" rx="80" ry="14" fill="#000" opacity=".5"/>'; }
  function plate(inner){ var g = id('pl'), r = id('rm');
    return shadow()+'<defs><radialGradient id="'+g+'" cx="42%" cy="36%" r="70%"><stop offset="0" stop-color="#3D3833"/><stop offset=".65" stop-color="#211E1B"/><stop offset="1" stop-color="#100E0D"/></radialGradient>'+
      '<linearGradient id="'+r+'" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5B544C"/><stop offset=".5" stop-color="#2A2622"/><stop offset="1" stop-color="#0E0C0B"/></linearGradient></defs>'+
      '<circle cx="100" cy="100" r="88" fill="url(#'+r+')"/><circle cx="100" cy="100" r="82" fill="url(#'+g+')"/>'+
      '<circle cx="100" cy="100" r="66" fill="none" stroke="#000" stroke-width="3" opacity=".3"/>'+inner; }
  function leaf(x, y, rot, c){ c = c || '#5E9E4E'; return '<g transform="rotate('+rot+' '+x+' '+y+')"><ellipse cx="'+x+'" cy="'+y+'" rx="9" ry="4" fill="'+c+'"/><path d="M'+(x-8)+' '+y+' L'+(x+8)+' '+y+'" stroke="#2F5A26" stroke-width=".8"/></g>'; }
  function herbs(pts, c){ return pts.map(function(p){ return leaf(p[0], p[1], p[2], c); }).join(''); }
  function dots(n, c, cx, cy, rad, size, seed){ var s = '', a = seed || 1;
    for(var k = 0; k < n; k++){ a = (a * 9301 + 49297) % 233280; var r1 = a / 233280; a = (a * 9301 + 49297) % 233280; var r2 = a / 233280;
      var ang = r1 * 6.283, d = Math.sqrt(r2) * rad; s += '<circle cx="'+(cx + Math.cos(ang) * d).toFixed(1)+'" cy="'+(cy + Math.sin(ang) * d).toFixed(1)+'" r="'+size+'" fill="'+c+'"/>'; }
    return s; }
  function pool(c1, c2, extra){ var g = id('po');
    return '<defs><radialGradient id="'+g+'" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="'+c1+'"/><stop offset="1" stop-color="'+c2+'"/></radialGradient></defs>'+
      '<circle cx="100" cy="100" r="60" fill="url(#'+g+')"/>'+
      '<path d="M64 90 C76 66 120 62 136 84" stroke="#fff" stroke-width="6" fill="none" opacity=".25" stroke-linecap="round"/>'+
      '<path d="M74 116 C92 132 120 130 132 112" stroke="#000" stroke-width="4" fill="none" opacity=".15" stroke-linecap="round"/>'+(extra || ''); }
  var T = {
    bowl: function(o){ return plate(pool(o.c1, o.c2, (o.swirl ? '<path d="M82 98 q18 -20 36 0 q-18 18 -36 0z" fill="'+o.swirl+'" opacity=".9"/>' : '')+(o.specks ? dots(18, o.specks, 100, 100, 46, 2.2, o.seed) : '')+(o.herb === false ? '' : herbs([[112, 120, 30], [122, 113, -25], [80, 84, 60]], o.herb)))); },
    oil: function(o){ var g = id('oi'); return plate('<circle cx="100" cy="100" r="44" fill="#E9E3DA"/><circle cx="100" cy="100" r="44" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="2"/>'+
      '<defs><radialGradient id="'+g+'" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="'+o.c1+'"/><stop offset="1" stop-color="'+o.c2+'"/></radialGradient></defs><circle cx="100" cy="100" r="36" fill="url(#'+g+')"/>'+
      '<ellipse cx="88" cy="88" rx="12" ry="7" fill="#fff" opacity=".35"/><circle cx="152" cy="68" r="6" fill="'+o.c1+'"/><circle cx="56" cy="138" r="4.5" fill="'+o.c1+'"/><circle cx="150" cy="140" r="3.5" fill="'+o.c1+'"/>'+herbs([[52, 70, -40], [62, 60, 15]], o.herb)); },
    balls: function(o){ var g = '', P = [[78, 92], [120, 86], [100, 124], [134, 120]];
      P.forEach(function(q){ var s = id('ba'); g += '<defs><radialGradient id="'+s+'" cx="35%" cy="30%" r="72%"><stop offset="0" stop-color="#FBE0A0"/><stop offset=".5" stop-color="'+o.c1+'"/><stop offset="1" stop-color="#5E3410"/></radialGradient></defs>'+
        '<circle cx="'+(q[0] + 4)+'" cy="'+(q[1] + 6)+'" r="22" fill="#000" opacity=".4"/><circle cx="'+q[0]+'" cy="'+q[1]+'" r="22" fill="url(#'+s+')"/>'+dots(9, '#7A4614', q[0], q[1], 15, 1.3, q[0])+'<circle cx="'+(q[0] - 8)+'" cy="'+(q[1] - 8)+'" r="3" fill="#FFF3D0" opacity=".8"/>'; });
      return plate('<path d="M58 132 C80 154 142 154 152 130" stroke="#3E7D3A" stroke-width="8" fill="none" stroke-linecap="round"/>'+g+herbs([[68, 66, -30], [146, 146, 20]])); },
    jar: function(o){ var g = id('ja'); return '<ellipse cx="100" cy="178" rx="60" ry="10" fill="#000" opacity=".55"/>'+
      '<defs><linearGradient id="'+g+'" x1="0" x2="1"><stop offset="0" stop-color="'+o.c2+'"/><stop offset=".4" stop-color="'+o.c1+'"/><stop offset=".75" stop-color="'+o.c1+'"/><stop offset="1" stop-color="'+o.c2+'"/></linearGradient></defs>'+
      '<rect x="54" y="58" width="92" height="120" rx="22" fill="url(#'+g+')"/>'+(o.bits ? dots(22, o.bits, 100, 128, 34, 3, o.seed) : '')+
      '<rect x="54" y="58" width="92" height="120" rx="22" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="2"/>'+
      '<rect x="64" y="70" width="11" height="94" rx="5.5" fill="#fff" opacity=".2"/>'+
      '<rect x="58" y="32" width="84" height="28" rx="8" fill="#26231F"/><rect x="58" y="32" width="84" height="9" rx="4.5" fill="#3D3833"/>'+
      '<rect x="70" y="100" width="60" height="30" rx="6" fill="#F3EEE6" opacity=".93"/><text x="100" y="120" text-anchor="middle" font-family="Georgia,serif" font-style="italic" font-size="14" fill="#2A1F18">tintå</text>'; },
    butter: function(o){ return plate('<path d="M56 94 L100 72 L146 94 L100 116 Z" fill="'+(o.c1 || '#FBE7A1')+'"/><path d="M56 94 L56 120 L100 142 L100 116 Z" fill="'+(o.c2 || '#E9C766')+'"/><path d="M146 94 L146 120 L100 142 L100 116 Z" fill="#D2AA45"/>'+
      '<path d="M70 94 L100 80 L132 94" stroke="#fff" stroke-width="3" opacity=".5" fill="none"/>'+(o.top || '')+herbs([[150, 60, 0], [160, 70, 40]], o.herb || '#5E9E4E')); },
    scoops: function(o){ var g = '', P = [[84, 96], [118, 92], [100, 122]];
      P.forEach(function(q){ var s = id('sc'); g += '<defs><radialGradient id="'+s+'" cx="35%" cy="30%" r="72%"><stop offset="0" stop-color="#F3F8DC"/><stop offset=".55" stop-color="'+o.c1+'"/><stop offset="1" stop-color="'+o.c2+'"/></radialGradient></defs>'+
        '<circle cx="'+(q[0] + 3)+'" cy="'+(q[1] + 6)+'" r="23" fill="#000" opacity=".35"/><circle cx="'+q[0]+'" cy="'+q[1]+'" r="23" fill="url(#'+s+')"/>'; });
      return plate(g+dots(14, '#5C7A2A', 100, 104, 30, 2.4, 7)+herbs([[140, 70, 30]], '#6FA34A')); },
    seeds: function(o){ return plate('<circle cx="100" cy="100" r="46" fill="#E9E3DA"/><circle cx="100" cy="100" r="40" fill="'+o.c2+'"/>'+dots(90, o.c1, 100, 100, 37, o.size || 2, o.seed)+dots(30, o.c3 || o.c1, 100, 100, 37, (o.size || 2) * .8, (o.seed || 1) + 5)); },
    greens: function(o){ var s = ''; for(var k = 0; k < 26; k++){ var a = k * 137.5 * Math.PI / 180, d = 10 + (k % 7) * 6; s += leaf(100 + Math.cos(a) * d, 100 + Math.sin(a) * d, (k * 47) % 180, ['#4E8F3E', '#6FB04F', '#3C7A30', '#86C266'][k % 4]); } return plate(s); },
    sticks: function(o){ var s = ''; [[60, 80, 140, 70], [58, 100, 146, 96], [64, 120, 140, 128], [70, 138, 132, 150]].forEach(function(p, k){
      s += '<line x1="'+p[0]+'" y1="'+p[1]+'" x2="'+p[2]+'" y2="'+p[3]+'" stroke="#000" stroke-opacity=".35" stroke-width="17" stroke-linecap="round" transform="translate(3 5)"/><line x1="'+p[0]+'" y1="'+p[1]+'" x2="'+p[2]+'" y2="'+p[3]+'" stroke="'+(k % 2 ? o.c1 : o.c2)+'" stroke-width="16" stroke-linecap="round"/><line x1="'+(p[0] + 6)+'" y1="'+(p[1] - 3)+'" x2="'+(p[2] - 10)+'" y2="'+(p[3] - 3)+'" stroke="#fff" stroke-opacity=".3" stroke-width="3" stroke-linecap="round"/>'; });
      return plate(s+herbs([[100, 64, 10], [112, 158, -20]])); },
    shrooms: function(o){ var s = ''; [[80, 100], [118, 90], [104, 124], [136, 122], [72, 132]].forEach(function(p){
      s += '<path d="M'+(p[0] - 14)+' '+p[1]+' q14 -22 28 0 q-6 6 -14 6 q-8 0 -14 -6z" fill="#E7A23A"/><rect x="'+(p[0] - 3)+'" y="'+(p[1] + 3)+'" width="6" height="12" rx="3" fill="#F2D49A"/><path d="M'+(p[0] - 8)+' '+(p[1] - 6)+' q8 -8 16 0" stroke="#FFD27A" stroke-width="2" fill="none"/>'; });
      return plate(pool('#3A2A1C', '#1E1610', s)); }
  };
  // Resepti -> kuva. / الوصفة -> الرسمة.
  var BY = {
    'pistaasikastike': ['bowl', {c1:'#B9C46A', c2:'#6E7A2E', specks:'#4E5A20'}],
    'vegesmetana': ['bowl', {c1:'#FFFBF2', c2:'#E9E1D0', swirl:'#fff'}],
    'wasabiseesam-limemajoneesi': ['bowl', {c1:'#EEF3D6', c2:'#C9D79A', specks:'#2A2A22', seed:3}],
    'ponzu': ['oil', {c1:'#8A4B1E', c2:'#3A1A08'}],
    'wasabimajo': ['bowl', {c1:'#E4F0C2', c2:'#A9C46A', swirl:'#F4F9E4'}],
    'sesam-mysli': ['seeds', {c1:'#1A1715', c2:'#C9A56A', c3:'#E8D3A8', size:2.2, seed:4}],
    'pistaasijaatelo': ['scoops', {c1:'#A8C46A', c2:'#5E7A2A'}],
    'ruohosipuliolj': ['oil', {c1:'#5DB040', c2:'#1F5E14'}],
    'timjamioljy': ['oil', {c1:'#7DAA45', c2:'#2F5A1A'}],
    'aranchini': ['balls', {c1:'#D9902E'}],
    'grilli-sitruunavine': ['oil', {c1:'#F2D24A', c2:'#B07A10', herb:'#6E9E3E'}],
    'kantarellikeitto': ['bowl', {c1:'#F4CC7A', c2:'#B57A26', swirl:'#FBEBC8'}],
    'tomaattikastike': ['bowl', {c1:'#E8502E', c2:'#8E1F10', specks:'#5E140A', seed:2}],
    'palsternakka-omenapyre': ['bowl', {c1:'#FFF4DA', c2:'#E6D2A2', swirl:'#FFFDF5'}],
    'simpukkaliemi-porre': ['bowl', {c1:'#F7E7B5', c2:'#C9A34A', swirl:'#FFF6DC'}],
    'sitruunadippi': ['bowl', {c1:'#FFE57A', c2:'#D9B02A', swirl:'#FFF6C8'}],
    'seesam-vine': ['oil', {c1:'#C98A3A', c2:'#6A3A10'}],
    'punajuuri-palsternakka-glace': ['oil', {c1:'#8E1F4A', c2:'#3A0A1E'}],
    'carpa-relish': ['bowl', {c1:'#E2452E', c2:'#9A2010', specks:'#F2E6C8', seed:9}],
    'beluga': ['seeds', {c1:'#1C1A18', c2:'#3A3530', c3:'#4E4840', size:3, seed:11}],
    'pasta-sas': ['bowl', {c1:'#F07A3A', c2:'#A9361C', swirl:'#FFC79A'}],
    'samppanjarisotto': ['bowl', {c1:'#F6E3A8', c2:'#CDA84E', specks:'#FFF7DE', seed:5}],
    'sitruunavoi': ['butter', {top:'<circle cx="100" cy="92" r="9" fill="#F7D84A"/><circle cx="100" cy="92" r="5" fill="#FFF0A0"/>'}],
    'lohen-pinaatin-voi': ['butter', {top:'<circle cx="100" cy="92" r="9" fill="#F7D84A"/>'}],
    'mustikkahillo': ['jar', {c1:'#5B3A8C', c2:'#22113D', bits:'#7E5AB8', seed:6}],
    'puolukka-chutney': ['jar', {c1:'#C2203A', c2:'#5E0A18', bits:'#E2405A', seed:8}],
    'aioli': ['bowl', {c1:'#FFF8E6', c2:'#E8DCC0', swirl:'#fff'}],
    'srirachamajoneesi': ['bowl', {c1:'#F49A5A', c2:'#C2502A', swirl:'#FFD3B0'}],
    'rapu-tryffelimajoneesi': ['bowl', {c1:'#F2E2C4', c2:'#C9AE84', specks:'#1A1512', seed:12}],
    'yrttioljy': ['oil', {c1:'#5DB040', c2:'#1F5E14'}],
    'parmesan-broiler': ['oil', {c1:'#C9A040', c2:'#6A4A14', herb:'#4E7A3A'}],
    'ele-voi': ['oil', {c1:'#E6C84A', c2:'#8A6A10'}],
    'vegaaninen-ricotta': ['bowl', {c1:'#FFFDF6', c2:'#EAE2CE', specks:'#F7D84A', seed:13}],
    'savumantelipesto': ['bowl', {c1:'#7AA04A', c2:'#3E5A1E', specks:'#8A5A2E', seed:14}],
    'artisokkakastike': ['bowl', {c1:'#DCE4B4', c2:'#9AAA5E', swirl:'#F2F6DC'}],
    'valkosipulivoi': ['butter', {top:'<ellipse cx="100" cy="92" rx="10" ry="7" fill="#F7F2E6"/><path d="M100 85 v-6" stroke="#C9B48A" stroke-width="2"/>'}],
    'kurpitsansiemenpesto': ['bowl', {c1:'#5E8F3A', c2:'#2A4A1A', specks:'#2E5A1E', seed:15}],
    'kimchi': ['jar', {c1:'#D2402A', c2:'#6A1408', bits:'#F2E2B0', seed:16}],
    'kantarellit-keiton-paalle': ['shrooms', {}],
    'punkkupojo': ['bowl', {c1:'#7A2A2A', c2:'#2E0A0A', swirl:'#A2504A', herb:'#4E7A3A'}],
    'vadelmamelba': ['bowl', {c1:'#E04A6A', c2:'#8E1C3A', specks:'#C7224A', seed:17}],
    'vadelmakastike': ['bowl', {c1:'#E85A7A', c2:'#9A1E40', swirl:'#F79AB0'}],
    'vihermix': ['greens', {}],
    'chili-lepeoljy': ['oil', {c1:'#E0402A', c2:'#7A140A', herb:'#3E8A30'}],
    'keiton-vine': ['oil', {c1:'#6FB04F', c2:'#2A5A1A'}],
    'tonnikala-cevicheliemi': ['oil', {c1:'#9A5A2A', c2:'#3A1A08', herb:'#7AB84A'}],
    'tryffelisuola': ['seeds', {c1:'#FFFFFF', c2:'#D9D3C8', c3:'#2A2420', size:2, seed:18}],
    'uunijuurekset': ['sticks', {c1:'#F08A2A', c2:'#E8A64A'}],
    'omena-chutney': ['jar', {c1:'#D9A84A', c2:'#7A4A10', bits:'#F2D88A', seed:19}],
    'balsamico-vinegrette': ['oil', {c1:'#4A2A1A', c2:'#1A0A04'}],
    'pikkeliliemi': ['jar', {c1:'#E9E6C4', c2:'#A8A26A', bits:'#C9A52A', seed:20}],
    'korea-glaze': ['oil', {c1:'#B05A1A', c2:'#4A1A04'}],
    'daikon': ['jar', {c1:'#F4F0E2', c2:'#C9C2A8', bits:'#E6C84A', seed:21}],
    'hillottu-fenkoli': ['jar', {c1:'#E9E2B0', c2:'#9A9A5A', bits:'#C9D88A', seed:22}],
    'tandoori-mari': ['bowl', {c1:'#F08A4A', c2:'#B03A10', swirl:'#FFD0A8'}]
  };
  var CAT = { majo:['bowl', {c1:'#FFF8E6', c2:'#E8DCC0', swirl:'#fff'}], kastike:['bowl', {c1:'#E8A050', c2:'#9A4A1A'}], oljy:['oil', {c1:'#7DB045', c2:'#2F5A1A'}],
    pesto:['bowl', {c1:'#6FAF3E', c2:'#2F6420', specks:'#2E4A1E'}], voi:['butter', {}], liemi:['bowl', {c1:'#A0622A', c2:'#4A2A0E'}], keitto:['bowl', {c1:'#F2C46D', c2:'#B57A26'}],
    pohja:['bowl', {c1:'#FFFDF6', c2:'#EAE2CE'}], lisuke:['bowl', {c1:'#F2D9A0', c2:'#C29A4E'}], mari:['bowl', {c1:'#E8904A', c2:'#A04010'}], sailyke:['jar', {c1:'#C2603A', c2:'#5E200A'}],
    mauste:['seeds', {c1:'#2A2420', c2:'#D9D3C8'}], jalki:['bowl', {c1:'#E04A6A', c2:'#8E1C3A'}] };
  function pick(r){ return BY[r.id] || CAT[r.c] || CAT.kastike; }
  function svg(r, cls){ var p = pick(r), o = {}; for(var k in p[1]) o[k] = p[1][k];
    return '<svg class="'+(cls || 'dish')+'" viewBox="0 0 200 200" aria-hidden="true">'+T[p[0]](o)+'</svg>'; }
  function cat(c, cls){ return svg({id:'', c:c}, cls); }
  return { svg: svg, cat: cat };
})();
