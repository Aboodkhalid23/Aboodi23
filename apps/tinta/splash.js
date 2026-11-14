// Tintå: avausanimaatiot / حركات الشعار عند فتح التطبيق (8 أشكال من المطبخ، وحدة عشوائية كل مرة)
(function(){
var SLOW=.55,HOLD=900,L='LOGO_DATA',CSS=`
.tsp{position:relative;width:200px;height:420px;flex:none;display:flex;align-items:center;justify-content:center}
.tsp .lg{position:relative;width:120px;aspect-ratio:360/252}
.tsp .lg img{position:absolute;inset:0;width:100%;height:100%}
.tsp .tag{position:absolute;bottom:31%;left:0;right:0;text-align:center;font:600 7px system-ui,sans-serif;letter-spacing:.4em;padding-left:.4em;color:#E6A774;opacity:0}
.tsp canvas{position:absolute;inset:0;width:100%;height:100%}
.clo .tag{bottom:22%}
/* steam */
.ste .lg{opacity:0}
.ste.play .lg{animation:rise 1.2s .5s cubic-bezier(.16,1,.3,1) forwards}
.ste.play .tag{animation:fade .6s 1.4s forwards}
/* oil drop */
.oil svg{position:absolute;width:200px;left:0;top:50%;transform:translateY(-50%);overflow:visible}
.oil .drop{transform-box:fill-box;transform-origin:50% 100%;transform:translateY(-190px)}
.oil .rip{transform-box:fill-box;transform-origin:center;opacity:0}
.oil .spl{opacity:0}
.oil .lg{opacity:0}
.oil.play .drop{animation:dropF .55s .15s cubic-bezier(.55,0,1,.45) forwards}
.oil.play .rip{animation:rip 1.3s .7s cubic-bezier(.2,.7,.3,1) forwards}
.oil.play .r2{animation-delay:.85s}.oil.play .r3{animation-delay:1s}
.oil.play .spl{animation:spl .6s .7s cubic-bezier(.2,.7,.3,1) forwards}
.oil.play .lg{animation:rise 1s .9s cubic-bezier(.16,1,.3,1) forwards}
.oil.play .tag{animation:fade .6s 1.6s forwards}
@keyframes dropF{0%{transform:translateY(-190px) scaleY(1.15)}92%{transform:translateY(0) scaleY(1.15)}100%{transform:translateY(0) scale(1.6,.1);opacity:0}}
@keyframes rip{0%{opacity:.9;transform:scale(.1)}100%{opacity:0;transform:scale(1.5)}}
@keyframes spl{0%{opacity:1;transform:none}100%{opacity:0;transform:translate(var(--x),var(--y))}}
/* herbs */
.her .leaf{opacity:0}
.her .lg{opacity:0}
.her.play .leaf{animation:leafF 1.1s cubic-bezier(.2,.7,.3,1) forwards;animation-delay:calc(var(--d) * 1ms)}
.her.play .lg{animation:rise 1s 1s cubic-bezier(.16,1,.3,1) forwards}
.her.play .tag{animation:fade .6s 1.7s forwards}
.her .leaf{position:absolute;left:calc(50% + var(--x) * 1px);top:calc(50% + var(--y) * 1px);width:30px;margin:-10px -15px}
@keyframes leafF{0%{opacity:0;transform:translate(calc(var(--x) * -.3px),-220px) rotate(calc(var(--r) * 1deg - 200deg))}30%{opacity:1}60%{transform:translate(calc(var(--x) * .12px),-12px) rotate(calc(var(--r) * 1deg + 20deg))}100%{opacity:1;transform:rotate(calc(var(--r) * 1deg))}}
/* burner */
.fir svg{position:absolute;width:200px;left:0;top:50%;transform:translateY(-50%);overflow:visible}
.fir .fl{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0)}
.fir .glow{opacity:0}
.fir .lg{opacity:0}
.fir.play .fl{animation:ign .3s calc(var(--d) * 1ms) cubic-bezier(.3,1.6,.5,1) forwards,flick .18s calc(var(--d) * 1ms + 300ms) ease-in-out infinite alternate}
.fir.play .glow{animation:fade 1s .4s forwards}
.fir.play .lg{animation:sear 1.1s .8s ease-out forwards}
.fir.play .tag{animation:fade .6s 1.6s forwards}
@keyframes ign{to{transform:scaleY(1)}}
@keyframes flick{from{transform:scaleY(1) scaleX(1)}to{transform:scaleY(.82) scaleX(1.08)}}
@keyframes sear{0%{opacity:0;filter:drop-shadow(0 0 0 rgba(255,140,60,0)) brightness(2)}50%{opacity:1;filter:drop-shadow(0 0 10px rgba(255,140,60,.9)) brightness(1.4)}100%{opacity:1;filter:drop-shadow(0 0 3px rgba(255,140,60,.35))}}
@media (prefers-reduced-motion:reduce){.tsp.play *{animation-duration:.01s!important;animation-delay:0s!important;animation-iteration-count:1!important}}
.clo svg{position:absolute;width:190px;left:50%;top:50%;transform:translate(-50%,-50%);overflow:visible}
.clo .plate{opacity:0;transform-origin:100px 110px}
.clo .lid{transform-origin:100px 100px}
.clo .lg{position:absolute;width:96px;opacity:0}
.clo .puff{opacity:0}
.clo.play .plate{animation:plateIn .6s cubic-bezier(.16,1,.3,1) forwards}
.clo.play .lid{animation:lidUp .9s .75s cubic-bezier(.5,0,.2,1) forwards}
.clo.play .lg{animation:rise .8s 1s cubic-bezier(.16,1,.3,1) forwards}
.clo.play .puff{animation:puff 1.4s 1s ease-out forwards}
.clo.play .puff:nth-child(2){animation-delay:1.1s}.clo.play .puff:nth-child(3){animation-delay:1.2s}
.clo.play .tag{animation:fade .6s 1.6s forwards}
@keyframes plateIn{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:none}}
@keyframes lidUp{0%{transform:none}25%{transform:translateY(4px)}100%{transform:translate(18px,-150px) rotate(14deg);opacity:0}}
@keyframes puff{0%{opacity:0;transform:translateY(0) scale(.6)}30%{opacity:.5}100%{opacity:0;transform:translateY(-60px) scale(1.6)}}
@keyframes rise{from{opacity:0;transform:translateY(8px);filter:blur(4px)}to{opacity:1;transform:none;filter:none}}
@keyframes fade{to{opacity:1}}
/* 2 sauce swoosh */
.sau svg{position:absolute;width:180px;left:50%;top:50%;transform:translate(-50%,-38%);overflow:visible}
.sau .sw{stroke-dasharray:300;stroke-dashoffset:300}
.sau .dot{transform-box:fill-box;transform-origin:center;transform:scale(0)}
.sau .lg img{-webkit-mask:linear-gradient(90deg,#000 45%,transparent 55%) 100% 0/250% 100% no-repeat;mask:linear-gradient(90deg,#000 45%,transparent 55%) 100% 0/250% 100% no-repeat}
.sau.play .sw{animation:draw .75s .2s cubic-bezier(.6,0,.2,1) forwards}
.sau.play .dot{animation:dot .35s cubic-bezier(.3,1.6,.5,1) forwards}
.sau.play .d1{animation-delay:.9s}.sau.play .d2{animation-delay:1s}.sau.play .d3{animation-delay:1.1s}
.sau.play .lg img{animation:inkW 1.2s .85s cubic-bezier(.45,.05,.35,1) forwards}
.sau.play .tag{animation:fade .6s 1.9s forwards}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes dot{to{transform:scale(1)}}
@keyframes inkW{to{-webkit-mask-position:0 0;mask-position:0 0}}
/* 3 spices */
.spi canvas{position:absolute;inset:0;width:100%;height:100%}
.spi .lg{opacity:0}
.spi.play .lg{animation:fade .5s 1.75s forwards}
.spi.play .tag{animation:fade .6s 1.9s forwards}
/* 4 knife */
.kni .lg img{transition:none}
.kni .top{clip-path:polygon(0 0,100% 0,100% 46%,0 60%)}
.kni .bot{clip-path:polygon(0 60%,100% 46%,100% 100%,0 100%)}
.kni .lg{opacity:0}
.kni .blade{position:absolute;left:-30%;width:160%;top:53%;height:2px;background:linear-gradient(90deg,transparent,#fff 45%,#F6C08E 55%,transparent);transform:rotate(-8deg) translateX(-120%);box-shadow:0 0 12px 2px rgba(246,192,142,.6);opacity:0}
.kni.play .lg{animation:fade .35s .1s forwards}
.kni.play .blade{animation:slash .5s .6s cubic-bezier(.7,0,.3,1) forwards}
.kni.play .top{animation:topS 1.1s .85s cubic-bezier(.16,1,.3,1) forwards}
.kni.play .bot{animation:botS 1.1s .85s cubic-bezier(.16,1,.3,1) forwards}
.kni.play .tag{animation:fade .6s 1.8s forwards}
@keyframes slash{0%{opacity:1;transform:rotate(-8deg) translateX(-60%)}100%{opacity:0;transform:rotate(-8deg) translateX(60%)}}
@keyframes topS{0%{transform:none}30%{transform:translate(-7px,-5px)}100%{transform:none}}
@keyframes botS{0%{transform:none}30%{transform:translate(7px,5px)}100%{transform:none}}
`,TAG='<div class="tag">RESEPTIT · RECIPES</div>',IMG='<img src="'+L+'" alt="">';
function leaves(){var P=[[-78,-46,-30],[70,-52,40],[-88,22,-70],[84,26,80],[-30,62,10],[36,60,-20],[2,-70,90]],s='';
  P.forEach(function(p,i){var g=i%2?'#7DA35F':'#5E8C4A';s+='<svg class="leaf" viewBox="0 0 30 20" style="--x:'+p[0]+';--y:'+p[1]+';--r:'+p[2]+';--d:'+(i*90)+'" aria-hidden="true"><path d="M1 10 C8 0,22 0,29 10 C22 20,8 20,1 10Z" fill="'+g+'"/><path d="M2 10 H27" stroke="#2F4A26" stroke-width=".8"/></svg>'});return s;}
function ring(){var s='',n=20;for(var i=0;i<n;i++){s+='<g transform="rotate('+(i*360/n)+' 100 100) translate(100 24)"><path class="fl" style="--d:'+(i*28)+'" d="M0 0 C-5 -5,-4 -13,0 -20 C4 -13,5 -5,0 0Z" fill="url(#fg)"/></g>'}return s;}
var V=[
 {k:'clo',t:2700,h:function(){return '<svg viewBox="0 0 200 200" aria-hidden="true"><defs><linearGradient id="dm" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#F0C9A0"/><stop offset=".5" stop-color="#C98A55"/><stop offset="1" stop-color="#6E4325"/></linearGradient><filter id="bl"><feGaussianBlur stdDeviation="6"/></filter></defs><g class="plate"><ellipse cx="100" cy="112" rx="92" ry="92" fill="#16130F" stroke="#2E2822" stroke-width="2"/><ellipse cx="100" cy="112" rx="66" ry="66" fill="none" stroke="#2A241F" stroke-width="1.5"/></g><g><ellipse class="puff" cx="85" cy="90" rx="22" ry="14" fill="#EBDCCB" filter="url(#bl)"/><ellipse class="puff" cx="115" cy="86" rx="18" ry="12" fill="#EBDCCB" filter="url(#bl)"/><ellipse class="puff" cx="100" cy="80" rx="20" ry="13" fill="#EBDCCB" filter="url(#bl)"/></g><g class="lid"><g class="plate"><path d="M24 124 A76 76 0 0 1 176 124 Z" fill="url(#dm)"/><path d="M40 112 A62 62 0 0 1 92 56" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round"/><rect x="18" y="122" width="164" height="7" rx="3.5" fill="#8A5A33"/><circle cx="100" cy="44" r="9" fill="url(#dm)"/><rect x="96" y="48" width="8" height="6" fill="#8A5A33"/></g></g></svg><div class="lg">'+IMG+'</div>'+TAG}},
 {k:'sau',t:2800,h:function(){return '<svg viewBox="0 0 200 80" aria-hidden="true"><defs><linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#7A4A26"/><stop offset=".6" stop-color="#D08A50"/><stop offset="1" stop-color="#E6A774"/></linearGradient></defs><path class="sw" d="M18 52 C60 30, 110 70, 182 34" fill="none" stroke="url(#sg)" stroke-width="13" stroke-linecap="round"/><circle class="dot d1" cx="160" cy="60" r="5" fill="#D08A50"/><circle class="dot d2" cx="176" cy="58" r="3.4" fill="#C07A45"/><circle class="dot d3" cx="188" cy="55" r="2.2" fill="#B06A38"/></svg><div class="lg">'+IMG+'</div>'+TAG}},
 {k:'spi',t:2800,h:function(){return '<canvas></canvas><div class="lg">'+IMG+'</div>'+TAG},run:spice},
 {k:'kni',t:2500,h:function(){return '<i class="blade"></i><div class="lg"><img class="top" src="'+L+'" alt=""><img class="bot" src="'+L+'" alt=""></div>'+TAG}},
 {k:'oil',t:2700,h:function(){return '<svg viewBox="0 0 200 200" aria-hidden="true"><defs><radialGradient id="og" cx=".35" cy=".35"><stop offset="0" stop-color="#FFF1C9"/><stop offset=".45" stop-color="#E9B44C"/><stop offset="1" stop-color="#9A6A18"/></radialGradient></defs><ellipse class="rip" cx="100" cy="128" rx="70" ry="18" fill="none" stroke="#E9B44C" stroke-width="1.6"/><ellipse class="rip r2" cx="100" cy="128" rx="70" ry="18" fill="none" stroke="#D08A50" stroke-width="1.2"/><ellipse class="rip r3" cx="100" cy="128" rx="70" ry="18" fill="none" stroke="#E6A774" stroke-width=".8"/><circle class="spl" style="--x:-34px;--y:-38px" cx="100" cy="126" r="3" fill="#E9B44C"/><circle class="spl" style="--x:30px;--y:-46px" cx="100" cy="126" r="2.4" fill="#E9B44C"/><circle class="spl" style="--x:-14px;--y:-56px" cx="100" cy="126" r="2" fill="#F3D27A"/><circle class="spl" style="--x:46px;--y:-22px" cx="100" cy="126" r="2" fill="#D08A50"/><path class="drop" d="M100 100 C92 112,88 118,88 123 A12 12 0 0 0 112 123 C112 118,108 112,100 100Z" fill="url(#og)"/></svg><div class="lg">'+IMG+'</div>'+TAG}},
 {k:'her',t:2800,h:function(){return leaves()+'<div class="lg">'+IMG+'</div>'+TAG}},
 {k:'fir',t:2700,h:function(){return '<svg viewBox="0 0 200 200" aria-hidden="true"><defs><linearGradient id="fg" x1="0" x2="0" y1="1" y2="0"><stop offset="0" stop-color="#3D7BFF"/><stop offset=".45" stop-color="#7FB2FF"/><stop offset=".7" stop-color="#FFB25A"/><stop offset="1" stop-color="#FF7A2A" stop-opacity=".2"/></linearGradient><radialGradient id="gw"><stop offset="0" stop-color="#FF8A3D" stop-opacity=".28"/><stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient></defs><circle class="glow" cx="100" cy="100" r="95" fill="url(#gw)"/><circle cx="100" cy="100" r="78" fill="none" stroke="#2A241F" stroke-width="3"/>'+ring()+'</svg><div class="lg">'+IMG+'</div>'+TAG}},
 {k:'ste',t:2700,h:function(){return '<canvas></canvas><div class="lg">'+IMG+'</div>'+TAG},run:steam}
];
var PTS=null;
function pts(img){if(PTS)return PTS;var c=document.createElement('canvas'),w=c.width=180,h=c.height=126,x=c.getContext('2d');x.drawImage(img,0,0,w,h);var d=x.getImageData(0,0,w,h).data,r=[];
  for(var y=0;y<h;y+=2)for(var i=0;i<w;i+=2)if(d[(y*w+i)*4+3]>120)r.push([i/w,y/h]);for(var k=r.length-1;k>0;k--){var j=Math.random()*(k+1)|0,t=r[k];r[k]=r[j];r[j]=t}return PTS=r.slice(0,900);}
function spice(st,k){var c=st.querySelector('canvas'),img=st.querySelector('.lg img'),x=c.getContext('2d'),S=2*k,W=c.width=200*S,H=c.height=420*S,lw=120*S,lh=lw*252/360,ox=(W-lw)/2,oy=(H-lh)/2,t0=performance.now(),id,
  C=['#2B2520','#3A3029','#F3EEE6','#E6A774','#D08A50','#8A4A22','#F3EEE6'];
  function go(){var P=pts(img).map(function(p,i){return{tx:ox+p[0]*lw,ty:oy+p[1]*lh,sx:W*(.2+Math.random()*.6),sy:-20-Math.random()*H*.6,d:Math.random()*500,c:C[i%C.length],r:(1+Math.random()*1.3)*S*.6}});
  function e(t){return 1-Math.pow(1-t,3)}
  function f(t){var el=(t-t0)*SLOW;x.clearRect(0,0,W,H);var fade=el>1700?Math.max(0,1-(el-1700)/500):1;
    P.forEach(function(p){var q=Math.min(1,Math.max(0,(el-p.d)/1100)),z=e(q),wob=Math.sin(el/120+p.d)*(1-z)*8*S/2;
      x.globalAlpha=fade*(q>0?1:0);x.fillStyle=p.c;x.beginPath();x.arc(p.sx+(p.tx-p.sx)*z+wob,p.sy+(p.ty-p.sy)*z,p.r,0,7);x.fill();});
    if(el<2300)id=requestAnimationFrame(f);else x.clearRect(0,0,W,H);}
  id=requestAnimationFrame(f);}
  if(img.complete)go();else img.onload=go;return function(){cancelAnimationFrame(id)};}
function steam(st,k){var c=st.querySelector('canvas'),x=c.getContext('2d'),S=2*k,W=c.width=200*S,H=c.height=420*S,P=[],t0=performance.now(),id;
  function f(t){var e=(t-t0)*SLOW;x.clearRect(0,0,W,H);if(e<1800&&P.length<70)for(var j=0;j<2;j++)P.push({x:W/2+(Math.random()-.5)*W*.5,y:H*.62,r:(22+Math.random()*22)*S/2,vy:(.7+Math.random()*.8)*S/2,ph:Math.random()*6,a:0});
    P.forEach(function(p){p.y-=p.vy*2.2*SLOW;p.ph+=.03*SLOW;p.x+=Math.sin(p.ph)*.9*S/2;p.r+=.25*S/2*SLOW;p.a=Math.min(p.a+.008*SLOW,.07);
      var g=x.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r);g.addColorStop(0,'rgba(240,215,190,'+p.a+')');g.addColorStop(1,'rgba(240,215,190,0)');x.fillStyle=g;x.beginPath();x.arc(p.x,p.y,p.r,0,7);x.fill();});
    P=P.filter(function(p){return p.y>-p.r});if(e<4000)id=requestAnimationFrame(f);}
  id=requestAnimationFrame(f);return function(){cancelAnimationFrame(id)};}
function css(){if(document.getElementById('tsp-css'))return;var s=document.createElement('style');s.id='tsp-css';s.textContent=CSS;document.head.appendChild(s);}
// mount(host, index, scale) -> stop()
function mount(host,i,k){css();k=k||1;var v=V[i],st=document.createElement('div');st.className='tsp '+v.k;st.style.transform='scale('+k+')';st.innerHTML=v.h();host.innerHTML='';host.appendChild(st);void st.offsetWidth;st.classList.add('play');getComputedStyle(st).opacity;try{(st.getAnimations?st.getAnimations({subtree:true}):[]).forEach(function(a){a.playbackRate=SLOW})}catch(e){}return v.run?v.run(st,k):function(){};}
function dur(i){return V[i].t/SLOW+HOLD}
function pick(){var n=V.length,last=-1,i;try{last=+localStorage.getItem('tinta-splash')}catch(e){}i=Math.floor(Math.random()*n);if(i===last)i=(i+1+Math.floor(Math.random()*(n-1)))%n;try{localStorage.setItem('tinta-splash',i)}catch(e){}return i;}
window.TintaSplash={V:V,mount:mount,pick:pick,dur:dur};
// In the app / بالتطبيق
var e=document.getElementById('splash');if(!e)return;
var R=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches,tm,t2,stop=function(){},hid=0;
function go(){clearTimeout(tm);if(e.classList.contains('out'))return;e.classList.add('out');t2=setTimeout(function(){e.classList.add('gone');stop();e.innerHTML=''},600)}
function show(){clearTimeout(tm);clearTimeout(t2);stop();e.classList.remove('out','gone');var i=pick(),k=Math.min(innerWidth/200*0.95,innerHeight/420,2.2);stop=mount(e,i,k);tm=setTimeout(go,R?600:dur(i))}
e.addEventListener('click',go);show();
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden'){hid=Date.now()}else if(hid&&Date.now()-hid>3000&&!document.body.classList.contains('cooking')){show()}});
window.addEventListener('pageshow',function(v){if(v.persisted)show()});
})();
