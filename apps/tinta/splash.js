// Tintå: avausanimaatiot / حركات الشعار عند فتح التطبيق
// 10 مشاهد من المطبخ مرسومة بالكود فريم بفريم، وحدة عشوائية كل مرة.
(function(){
var LOGO='LOGO_DATA',TAGT='RESEPTIT · RECIPES';
var img=new Image(),ready=new Promise(function(r){img.onload=r;img.onerror=r});img.src=LOGO;if(img.complete)ready=Promise.resolve();

// ---------- helpers ----------
function cl(v,a,b){return v<a?a:v>b?b:v}
function P(t,a,b){return cl((t-a)/(b-a),0,1)}
function E(t){t=cl(t,0,1);return 1-Math.pow(1-t,3)}
function EIO(t){t=cl(t,0,1);return t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2}
function EB(t){t=cl(t,0,1);var c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)}
function N(v,s){return Math.sin(v*1.7+s)*.5+Math.sin(v*3.1+s*2.3)*.3+Math.sin(v*5.3+s*.7)*.2}
function R(a,b){return a+Math.random()*(b-a)}
function mk(w,h){var c=document.createElement('canvas');c.width=Math.max(1,Math.round(w));c.height=Math.max(1,Math.round(h));return c}
var SP={};
function sprite(col,a){var k=col+a;if(SP[k])return SP[k];var c=mk(64,64),x=c.getContext('2d'),g=x.createRadialGradient(32,32,0,32,32,32);g.addColorStop(0,'rgba('+col+','+a+')');g.addColorStop(.5,'rgba('+col+','+(a*.45)+')');g.addColorStop(1,'rgba('+col+',0)');x.fillStyle=g;x.fillRect(0,0,64,64);return SP[k]=c}
function dot(x,s,px,py,r,a){if(a<=0||r<=0)return;x.globalAlpha=a;x.drawImage(s,px-r,py-r,r*2,r*2)}
function tint(src,col){var c=mk(src.width,src.height),x=c.getContext('2d');x.drawImage(src,0,0);x.globalCompositeOperation='source-in';x.fillStyle=col;x.fillRect(0,0,c.width,c.height);return c}
function rr(x,a,b,w,h,r){x.beginPath();x.moveTo(a+r,b);x.arcTo(a+w,b,a+w,b+h,r);x.arcTo(a+w,b+h,a,b+h,r);x.arcTo(a,b+h,a,b,r);x.arcTo(a,b,a+w,b,r);x.closePath()}

function bg(S,glow){var x=S.x;x.globalCompositeOperation='source-over';x.globalAlpha=1;x.fillStyle='#0E0D0C';x.fillRect(0,0,S.W,S.H);if(glow>0){x.globalAlpha=glow;x.drawImage(S.G,S.cx-S.lw*1.6,S.cy-S.lw*1.6,S.lw*3.2,S.lw*3.2);x.globalAlpha=1}}
function logo(S,a,sc,o){o=o||{};var x=S.x,w=S.lw*sc,h=S.lh*sc,px=S.cx-w/2+(o.dx||0),py=S.cy-h/2+(o.dy||0);
  if(o.g&&o.ga>0){x.globalAlpha=Math.min(1,o.ga/5);for(var i=0;i<10;i++){var an=i/10*6.283,r=o.gr*(i%2?1:.55);x.drawImage(o.g,px+Math.cos(an)*r,py+Math.sin(an)*r,w,h)}}
  if(a>0){x.globalAlpha=Math.min(1,a);x.drawImage(o.src||S.L,px,py,w,h)}x.globalAlpha=1}
function wipe(S,f,soft){var c=S.tmp,x=c.getContext('2d'),W=c.width;x.globalCompositeOperation='source-over';x.clearRect(0,0,W,c.height);x.drawImage(S.L,0,0);x.globalCompositeOperation='destination-in';var e=f*(1+soft)*W,g=x.createLinearGradient(e-soft*W,0,e+.001,0);g.addColorStop(0,'#000');g.addColorStop(1,'rgba(0,0,0,0)');x.fillStyle=g;x.fillRect(0,0,W,c.height);x.globalCompositeOperation='source-over';return c}
function shine(S,f){if(f<=0||f>=1)return;var c=S.tmp2,x=c.getContext('2d'),W=c.width;x.globalCompositeOperation='source-over';x.clearRect(0,0,W,c.height);x.drawImage(S.L,0,0);x.globalCompositeOperation='source-in';var p=(f*1.6-.3)*W,g=x.createLinearGradient(p-W*.16,0,p+W*.16,0);g.addColorStop(0,'rgba(255,190,140,0)');g.addColorStop(.5,'rgba(255,236,214,1)');g.addColorStop(1,'rgba(255,190,140,0)');x.fillStyle=g;x.fillRect(0,0,W,c.height);x.globalCompositeOperation='source-over';
  S.x.globalCompositeOperation='lighter';S.x.globalAlpha=.85;S.x.drawImage(c,S.cx-S.lw/2,S.cy-S.lh/2,S.lw,S.lh);S.x.globalCompositeOperation='source-over';S.x.globalAlpha=1}
function tag(S,a,dy){if(a<=0)return;var x=S.x,s=TAGT,sp=S.lw*.028,w=0,i;x.globalAlpha=a;x.fillStyle='#E6A774';x.font='600 '+Math.max(7,Math.round(S.lw*.052))+'px -apple-system,BlinkMacSystemFont,system-ui,sans-serif';x.textBaseline='middle';
  for(i=0;i<s.length;i++)w+=x.measureText(s[i]).width+sp;w-=sp;var px=S.cx-w/2,py=S.cy+S.lh*.5+S.lw*.17+(dy||0);for(i=0;i<s.length;i++){x.fillText(s[i],px,py);px+=x.measureText(s[i]).width+sp}x.globalAlpha=1}
function fin(S,t,ta,ts){var x=S.x,k=E(P(t,ta,ta+.9)),lk=E(P(t,ta-.2,ta+.8));
  if(lk>0){var y=S.cy+S.lh*.5+S.lw*.085,w=S.lw*.34*lk,g=x.createLinearGradient(S.cx-w,0,S.cx+w,0);g.addColorStop(0,'rgba(208,138,80,0)');g.addColorStop(.5,'rgba(208,138,80,.95)');g.addColorStop(1,'rgba(208,138,80,0)');x.globalAlpha=1;x.fillStyle=g;x.fillRect(S.cx-w,y,w*2,1)}
  tag(S,k,(1-k)*8);shine(S,P(t,ts,ts+1.3))}
function flame(x,bx,by,tx,ty,ca,sa,bw,c0,c1){var px=-sa*bw,py=ca*bw,mx=(bx+tx)/2,my=(by+ty)/2,g=x.createLinearGradient(bx,by,tx,ty);g.addColorStop(0,c0);g.addColorStop(1,c1);x.fillStyle=g;x.globalAlpha=1;x.beginPath();x.moveTo(bx+px,by+py);x.quadraticCurveTo(mx+px*1.4,my+py*1.4,tx,ty);x.quadraticCurveTo(mx-px*1.4,my-py*1.4,bx-px,by-py);x.closePath();x.fill()}
function steamP(S,list,sp){var x=S.x;return list.filter(function(p){p.l+=S.dt;p.x+=(p.vx||0)*S.dt+N(S.t*1.3+p.ph,p.ph)*S.lw*.16*S.dt;p.y+=p.vy*S.dt;p.r+=S.lw*(p.g||.05)*S.dt;var k=p.l/p.L;if(k>=1)return false;dot(x,sp,p.x,p.y,p.r,Math.sin(Math.PI*k)*(p.a||1));return true})}
function drawLeaf(x,L,c){var C=[['#3F6B30','#7DA35F'],['#4E7A3A','#9BC27A'],['#355E28','#6E9A52']][c],g=x.createLinearGradient(0,-L*.3,0,L*.3);g.addColorStop(0,C[1]);g.addColorStop(1,C[0]);x.fillStyle=g;x.globalAlpha=1;x.beginPath();x.moveTo(-L*.5,0);x.bezierCurveTo(-L*.2,-L*.42,L*.25,-L*.4,L*.5,0);x.bezierCurveTo(L*.25,L*.4,-L*.2,L*.42,-L*.5,0);x.fill();
  x.strokeStyle='rgba(25,45,18,.7)';x.lineWidth=.9;x.beginPath();x.moveTo(-L*.55,0);x.quadraticCurveTo(0,-L*.03,L*.46,0);x.stroke();x.strokeStyle='rgba(255,255,255,.14)';x.beginPath();for(var i=-2;i<=2;i++){x.moveTo(i*L*.14,-L*.01);x.lineTo(i*L*.14+L*.1,-L*.17);x.moveTo(i*L*.14,L*.01);x.lineTo(i*L*.14+L*.1,L*.15)}x.stroke()}
function drawShaker(x,lw){var w=lw*.22,h=lw*.3,g=x.createLinearGradient(-w/2,0,w/2,0);g.addColorStop(0,'rgba(255,255,255,.10)');g.addColorStop(.3,'rgba(255,255,255,.38)');g.addColorStop(1,'rgba(255,255,255,.06)');
  x.fillStyle='rgba(243,238,230,.85)';rr(x,-w/2+3,lw*.02,w-6,h/2,w*.12);x.fill();
  x.fillStyle=g;rr(x,-w/2,-h/2+lw*.06,w,h,w*.18);x.fill();x.strokeStyle='rgba(255,255,255,.3)';x.lineWidth=1;x.stroke();
  var gc=x.createLinearGradient(-w/2,0,w/2,0);gc.addColorStop(0,'#6E6A66');gc.addColorStop(.4,'#EDE9E3');gc.addColorStop(1,'#5A5652');x.fillStyle=gc;rr(x,-w/2-1,-h/2-lw*.06,w+2,lw*.13,w*.25);x.fill();
  x.fillStyle='#2A2622';for(var i=-1;i<=1;i++)for(var j=0;j<2;j++){x.beginPath();x.arc(i*w*.22,-h/2-lw*.035+j*lw*.04,1.3,0,6.283);x.fill()}}
function drawKnife(x,lw){var L=lw*1.15,h=lw*.17,g=x.createLinearGradient(0,-h/2,0,h/2);g.addColorStop(0,'#F4F2EE');g.addColorStop(.45,'#B9B6B1');g.addColorStop(.55,'#8E8B86');g.addColorStop(1,'#E9E6E1');
  x.fillStyle=g;x.beginPath();x.moveTo(-L*.08,-h/2);x.lineTo(L*.42,-h/2);x.quadraticCurveTo(L*.6,-h*.45,L*.64,-h*.25);x.quadraticCurveTo(L*.5,h*.45,L*.1,h/2);x.lineTo(-L*.08,h/2);x.closePath();x.fill();
  x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=1;x.beginPath();x.moveTo(-L*.06,h*.46);x.lineTo(L*.1,h*.48);x.quadraticCurveTo(L*.5,h*.43,L*.63,-h*.24);x.stroke();
  x.fillStyle='#C9C5BF';x.fillRect(-L*.12,-h*.55,L*.05,h*1.1);
  var gh=x.createLinearGradient(0,-h*.35,0,h*.35);gh.addColorStop(0,'#5A3A24');gh.addColorStop(1,'#2A1A10');x.fillStyle=gh;rr(x,-L*.46,-h*.34,L*.35,h*.68,h*.25);x.fill();
  x.fillStyle='#D9D5CF';[-.38,-.28,-.18].forEach(function(p){x.beginPath();x.arc(L*p,0,h*.07,0,6.283);x.fill()})}

// ---------- scenes ----------
var SC=[
// 1 نار الطباخ
{k:'fire',d:7,init:function(S){S.f=[];S.e=[];var n=34;for(var i=0;i<n;i++)S.f.push({a:i/n*6.283-1.571,ph:R(0,50),h:R(.8,1.2),ti:.5+i/n*1.2})},
 draw:function(S,t){var x=S.x,R0=S.lw*.64;bg(S,.6*E(P(t,.6,2.4)));
  x.globalAlpha=E(P(t,0,.5));x.lineWidth=S.lw*.034;x.strokeStyle='#2B2520';x.beginPath();x.arc(S.cx,S.cy,R0,0,6.283);x.stroke();x.lineWidth=1;x.strokeStyle='rgba(208,138,80,.3)';x.beginPath();x.arc(S.cx,S.cy,R0+S.lw*.02,0,6.283);x.stroke();
  x.globalCompositeOperation='lighter';
  S.f.forEach(function(f){var k=E(P(t,f.ti,f.ti+.45));if(k<=0)return;var fl=1+.3*N(t*9,f.ph),h=S.lw*.16*f.h*k*fl,bw=S.lw*.026,ca=Math.cos(f.a),sa=Math.sin(f.a),bx=S.cx+ca*R0,by=S.cy+sa*R0,sw=N(t*6,f.ph+9)*h*.32,tx=bx+ca*h-sa*sw,ty=by+sa*h+ca*sw;
   flame(x,bx,by,tx,ty,ca,sa,bw*1.5,'rgba(255,150,60,.55)','rgba(255,80,20,0)');
   flame(x,bx,by,bx+(tx-bx)*.62,by+(ty-by)*.62,ca,sa,bw,'rgba(80,140,255,.95)','rgba(150,200,255,0)');
   if(t<6.4&&Math.random()<.05*k)S.e.push({x:tx,y:ty,vx:ca*R(10,30),vy:sa*R(10,30)-R(25,55),l:0,L:R(.8,1.7),r:R(1,2.4)})});
  var sp=sprite('255,160,70',1);S.e=S.e.filter(function(e){e.l+=S.dt;e.x+=e.vx*S.dt+N(S.t*4,e.L)*10*S.dt;e.y+=e.vy*S.dt;var a=1-e.l/e.L;if(a<=0)return false;dot(x,sp,e.x,e.y,e.r*3,a);return true});
  x.globalCompositeOperation='source-over';x.globalAlpha=1;
  var a=E(P(t,1.7,3)),heat=1-P(t,2.8,5);logo(S,a,.9+.1*E(P(t,1.7,3.2)),{g:S.tint('#FF8A3D'),gr:S.lw*.03,ga:a*(.35+.9*heat)});
  if(heat>0)logo(S,a*heat*.8,.9+.1*E(P(t,1.7,3.2)),{src:S.tint('#FFB070')});
  fin(S,t,3.4,4.8)}},
// 2 بخار الطبخ
{k:'steam',d:7,init:function(S){S.p=[]},
 draw:function(S,t){var x=S.x,rimY=S.cy+S.lh*.95,rx=S.lw*.62;bg(S,.3);var thin=1-.45*P(t,3,4.5);
  x.globalAlpha=E(P(t,0,.8));var g=x.createLinearGradient(S.cx-rx,0,S.cx+rx,0);g.addColorStop(0,'#5A3A22');g.addColorStop(.35,'#E6A774');g.addColorStop(1,'#6E4325');x.strokeStyle=g;x.lineWidth=S.lw*.03;x.beginPath();x.ellipse(S.cx,rimY,rx,rx*.16,0,0,6.283);x.stroke();x.globalAlpha=1;
  if(t<6.4){var n=95*S.dt*(.4+P(t,0,1.4))*thin;for(;n>0;n--)if(n>=1||Math.random()<n)S.p.push({x:S.cx+R(-rx*.85,rx*.85),y:rimY-R(0,6),vy:-S.lw*R(.26,.4),r:R(.06,.11)*S.lw,l:0,L:R(2.4,3.6),ph:R(0,50),f:Math.random()<.18,a:.75})}
  var sp=sprite('236,224,210',.2),back=S.p.filter(function(p){return !p.f}),front=S.p.filter(function(p){return p.f});
  back=steamP(S,back,sp);
  var a=E(P(t,1.8,3.8));logo(S,a,1,{dy:(1-a)*S.lw*.1,g:S.tint('#EBDCCB'),gr:S.lw*.05*(1-a)+S.lw*.012,ga:a*.8*(1-P(t,3.6,5.2))});
  front=steamP(S,front,sp);S.p=back.concat(front);fin(S,t,4,5)}},
// 3 غطاء الطبق
{k:'cloche',d:7.4,init:function(S){S.p=[];S.b=0},
 draw:function(S,t){var x=S.x,lw=S.lw,py=S.cy+S.lh*.45,prx=lw*.92,pry=lw*.2,lift=EIO(P(t,2,3.2)),ap=E(P(t,0,.9));
  bg(S,.2+.5*E(P(t,2.1,3.4)));
  if(t>2){x.globalCompositeOperation='lighter';var ra=E(P(t,2,2.8))*(1-.65*P(t,3.6,6));x.save();x.translate(S.cx,py);for(var i=0;i<16;i++){var an=-Math.PI+(i+.5)/16*Math.PI+N(t*.5,i)*.06,L=lw*1.5,g=x.createLinearGradient(0,0,Math.cos(an)*L,Math.sin(an)*L);g.addColorStop(0,'rgba(255,190,120,'+(.2*ra)+')');g.addColorStop(1,'rgba(255,190,120,0)');x.fillStyle=g;x.beginPath();x.moveTo(0,0);x.lineTo(Math.cos(an-.06)*L,Math.sin(an-.06)*L);x.lineTo(Math.cos(an+.06)*L,Math.sin(an+.06)*L);x.closePath();x.fill()}x.restore();x.globalCompositeOperation='source-over'}
  x.globalAlpha=ap;var g2=x.createLinearGradient(0,py-pry,0,py+pry);g2.addColorStop(0,'#2E2822');g2.addColorStop(1,'#141210');x.fillStyle=g2;x.beginPath();x.ellipse(S.cx,py,prx,pry,0,0,6.283);x.fill();x.strokeStyle='rgba(230,167,116,.4)';x.lineWidth=1.2;x.stroke();x.strokeStyle='rgba(255,255,255,.07)';x.beginPath();x.ellipse(S.cx,py,prx*.72,pry*.72,0,0,6.283);x.stroke();x.globalAlpha=1;
  var a=E(P(t,2.3,3.4));logo(S,a,.94+.06*a,{g:S.tint('#FFB070'),gr:lw*.025,ga:a*.7*(1-P(t,3.6,5.4))});
  var sp=sprite('236,224,210',.22);
  if(t>1.1&&t<2.1&&Math.random()<.55)S.p.push({x:S.cx+R(-prx*.7,prx*.7),y:py-2,vx:R(-10,10),vy:-R(15,35),r:lw*.06,l:0,L:1.5,ph:R(0,9)});
  if(t>2.05&&!S.b){S.b=1;for(var i=0;i<55;i++)S.p.push({x:S.cx+R(-prx*.6,prx*.6),y:py-R(0,lw*.3),vx:R(-35,35),vy:-R(30,100),r:lw*R(.06,.12),l:0,L:R(1.6,2.8),ph:R(0,9)})}
  S.p=steamP(S,S.p,sp);
  if(lift<1){var sh=t>1.1&&t<2?Math.sin(t*50)*.04*P(t,1.1,1.9):0,s=.85+.15*EB(P(t,0,.9)),dr=lw*.76,dh=lw*.66;x.save();x.globalAlpha=ap*(1-P(t,2.8,3.2));x.translate(S.cx+lift*lw*.3,py-lift*S.H*.6);x.rotate(sh-lift*.3);x.scale(s,s);
   var hx=.28+.1*N(t*.8,3),g3=x.createLinearGradient(-dr,0,dr,0);g3.addColorStop(0,'#4A2E1A');g3.addColorStop(hx,'#F6D9B8');g3.addColorStop(Math.min(.95,hx+.14),'#C98A55');g3.addColorStop(1,'#3E2616');
   x.fillStyle=g3;x.beginPath();x.moveTo(-dr,0);x.bezierCurveTo(-dr,-dh*1.05,dr,-dh*1.05,dr,0);x.closePath();x.fill();
   x.strokeStyle='rgba(255,240,220,.5)';x.lineWidth=2;x.beginPath();x.moveTo(-dr*.72,-dh*.18);x.bezierCurveTo(-dr*.7,-dh*.6,-dr*.35,-dh*.76,-dr*.05,-dh*.78);x.stroke();
   x.fillStyle='#7A4A26';x.beginPath();x.ellipse(0,0,dr*1.05,lw*.035,0,0,6.283);x.fill();
   x.fillStyle=g3;x.fillRect(-lw*.022,-dh*.86,lw*.044,lw*.06);x.beginPath();x.ellipse(0,-dh*.88,lw*.075,lw*.045,0,0,6.283);x.fill();x.restore()}
  fin(S,t,3.8,4.9)}},
// 4 رشة ملح وبهارات
{k:'salt',d:7.2,init:function(S){var c=S.L,w=c.width,h=c.height,d=c.getContext('2d').getImageData(0,0,w,h).data,pts=[],st=Math.max(1,Math.round(w/150));for(var y=0;y<h;y+=st)for(var i=0;i<w;i+=st)if(d[(y*w+i)*4+3]>110)pts.push([i/w,y/h]);
  for(var k=pts.length-1;k>0;k--){var j=Math.random()*(k+1)|0,q=pts[k];pts[k]=pts[j];pts[j]=q}pts=pts.slice(0,1400);
  var C=['#F3EEE6','#FFFFFF','#F3EEE6','#E6A774','#D08A50','#8C7766','#C0652A'],u=S.lw/200;
  S.g=pts.map(function(p,i){var ts=.35+Math.random()*1.7;return{tx:S.cx-S.lw/2+p[0]*S.lw,ty:S.cy-S.lh/2+p[1]*S.lh,x:0,y:0,vx:0,vy:0,on:false,ts:ts,ta:ts+R(.45,1),c:C[i%C.length],r:R(1,2)*u*1.4}})},
 draw:function(S,t){var x=S.x,u=S.lw/200;bg(S,.3*E(P(t,1.4,3.4)));var shx=S.cx+N(t*.9,1)*S.lw*.18,shy=S.H*.14-P(t,2.3,3.1)*S.H*.35,rot=t<2.3?Math.sin(t*24)*.35:-.25*P(t,2.3,2.6);
  var fa=1-P(t,3.8,4.6);S.g.forEach(function(g){if(t<g.ts)return;if(!g.on){g.on=true;g.x=shx+R(-6,6)*u;g.y=shy+S.lw*.2;g.vx=R(-45,45)*u;g.vy=R(30,90)*u}
   if(t<g.ta){g.vy+=430*u*S.dt;g.vx*=.99}else{g.vx+=((g.tx-g.x)*55-g.vx*10.5)*S.dt;g.vy+=((g.ty-g.y)*55-g.vy*10.5)*S.dt}
   g.x+=g.vx*S.dt;g.y+=g.vy*S.dt;if(fa<=0)return;x.globalAlpha=fa;x.fillStyle=g.c;x.fillRect(g.x-g.r/2,g.y-g.r/2,g.r,g.r)});x.globalAlpha=1;
  if(t<3.1){x.save();x.globalAlpha=E(P(t,0,.4))*(1-P(t,2.5,3.1));x.translate(shx,shy);x.rotate(Math.PI+rot);drawShaker(x,S.lw);x.restore();x.globalAlpha=1}
  logo(S,E(P(t,3.6,4.5)),1,{});fin(S,t,4.4,5.2)}},
// 5 ضربة سكين
{k:'knife',d:7,init:function(S){S.p=[];S.sp=0},
 draw:function(S,t){var x=S.x,lw=S.lw,an=-.14,m=Math.tan(an);bg(S,.3);
  var a=E(P(t,.2,1.2)),sep=E(P(t,1.8,2.6))*(1-EB(P(t,3,3.9))),off=lw*.07*sep,cut=t>=1.75;
  function piece(top,dx,dy){x.save();x.translate(dx,dy);x.beginPath();if(top){x.moveTo(-50,-50);x.lineTo(S.W+50,-50)}else{x.moveTo(-50,S.H+50);x.lineTo(S.W+50,S.H+50)}x.lineTo(S.W+50,S.cy+m*(S.W+50-S.cx));x.lineTo(-50,S.cy+m*(-50-S.cx));x.closePath();x.clip();logo(S,a,1,{});x.restore()}
  if(!cut)logo(S,a,1,{});else{piece(true,-off*.4,-off);piece(false,off*.4,off)}
  var kp=EIO(P(t,1.2,2.1)),kx=-lw*1.2+(S.W+lw*2.4)*kp,ky=S.cy+m*(kx-S.cx);
  if(t>1.2){var ta=t<2.1?1:1-P(t,2.1,2.7);if(ta>0){var x0=Math.max(S.cx-lw*.7,-10),x1=Math.min(kx+lw*.55,S.cx+lw*.7);if(x1>x0){x.globalCompositeOperation='lighter';var g=x.createLinearGradient(x0,0,x1,0);g.addColorStop(0,'rgba(255,220,180,0)');g.addColorStop(1,'rgba(255,240,220,'+ta+')');x.strokeStyle=g;x.lineWidth=2;x.beginPath();x.moveTo(x0,S.cy+m*(x0-S.cx));x.lineTo(x1,S.cy+m*(x1-S.cx));x.stroke();x.globalCompositeOperation='source-over'}}}
  if(kx+lw*.55>S.cx&&!S.sp){S.sp=1;for(var i=0;i<46;i++){var px=S.cx+R(-lw*.5,lw*.5);S.p.push({x:px,y:S.cy+m*(px-S.cx),vx:R(-60,60),vy:R(-110,-20),l:0,L:R(.5,1.1),r:R(1,2.2)})}}
  var sp=sprite('255,200,140',1);x.globalCompositeOperation='lighter';S.p=S.p.filter(function(p){p.l+=S.dt;p.vy+=260*S.dt;p.x+=p.vx*S.dt;p.y+=p.vy*S.dt;var k=1-p.l/p.L;if(k<=0)return false;dot(x,sp,p.x,p.y,p.r*2.5,k);return true});
  var fl=P(t,3.5,4.1);if(fl>0&&fl<1){var w=lw*.7,g4=x.createLinearGradient(S.cx-w,0,S.cx+w,0);g4.addColorStop(0,'rgba(255,220,180,0)');g4.addColorStop(.5,'rgba(255,236,214,'+(Math.sin(Math.PI*fl))+')');g4.addColorStop(1,'rgba(255,220,180,0)');x.strokeStyle=g4;x.lineWidth=2.5;x.beginPath();x.moveTo(S.cx-w,S.cy-m*w);x.lineTo(S.cx+w,S.cy+m*w);x.stroke()}
  x.globalCompositeOperation='source-over';x.globalAlpha=1;
  if(kp>0&&kp<1){x.save();x.translate(kx,ky-lw*.06);x.rotate(an);drawKnife(x,lw);x.restore()}
  fin(S,t,4.2,5.2)}},
// 6 لمسة الصوص
{k:'sauce',d:7.2,init:function(S){var lw=S.lw,p0=[S.cx-lw*.68,S.cy+S.lh*.62],p1=[S.cx-lw*.2,S.cy+S.lh*.05],p2=[S.cx+lw*.25,S.cy+S.lh*1.05],p3=[S.cx+lw*.66,S.cy+S.lh*.22];S.pts=[];
  for(var i=0;i<=180;i++){var u=i/180,v=1-u,X=v*v*v*p0[0]+3*v*v*u*p1[0]+3*v*u*u*p2[0]+u*u*u*p3[0],Y=v*v*v*p0[1]+3*v*v*u*p1[1]+3*v*u*u*p2[1]+u*u*u*p3[1];S.pts.push([X,Y,lw*.075*Math.pow(Math.sin(Math.PI*Math.min(.98,u*1.08+.02)),.55)*(1-u*.4)+lw*.006])}S.end=p3},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.3);var k=EIO(P(t,.5,1.9)),n=Math.floor(k*S.pts.length),i;
  x.fillStyle='rgba(0,0,0,.35)';for(i=0;i<n;i+=2){var q=S.pts[i];x.beginPath();x.arc(q[0]+1.5,q[1]+2.5,q[2],0,6.283);x.fill()}
  var g=x.createLinearGradient(S.cx-lw,0,S.cx+lw,0);g.addColorStop(0,'#5E3418');g.addColorStop(.5,'#B8703A');g.addColorStop(1,'#E0A06A');x.fillStyle=g;
  for(i=0;i<n;i++){var p=S.pts[i];x.beginPath();x.arc(p[0],p[1],p[2],0,6.283);x.fill()}
  if(n>12){x.strokeStyle='rgba(255,232,205,.5)';x.lineWidth=lw*.012;x.lineCap='round';x.beginPath();for(i=10;i<n-4;i++){var p2=S.pts[i];if(i===10)x.moveTo(p2[0]-p2[2]*.2,p2[1]-p2[2]*.45);else x.lineTo(p2[0]-p2[2]*.2,p2[1]-p2[2]*.45)}x.stroke()}
  [[.10,.07,.045,2.0],[.17,.09,.03,2.15],[.22,.11,.02,2.3]].forEach(function(d){var s=EB(P(t,d[3],d[3]+.35));if(s<=0)return;x.fillStyle=g;x.beginPath();x.arc(S.end[0]+lw*d[0]-lw*.06,S.end[1]+lw*d[1],lw*d[2]*s,0,6.283);x.fill();x.fillStyle='rgba(255,232,205,.6)';x.beginPath();x.arc(S.end[0]+lw*d[0]-lw*.06-lw*d[2]*.3*s,S.end[1]+lw*d[1]-lw*d[2]*.3*s,lw*d[2]*.25*s,0,6.283);x.fill()});
  var w=P(t,2.1,4);if(w>0){var f=EIO(w),c=wipe(S,f,.12);x.globalAlpha=1;x.drawImage(c,S.cx-lw/2,S.cy-S.lh/2,lw,S.lh);if(w<1){x.globalCompositeOperation='lighter';dot(x,sprite('255,200,140',1),S.cx-lw/2+(f*1.12-.06)*lw,S.cy+N(t*7,2)*S.lh*.28,lw*.05,.9);x.globalCompositeOperation='source-over'}}
  fin(S,t,4.2,5.1)}},
// 7 قطرة زيت
{k:'oil',d:7.2,init:function(S){S.p=[];S.hit=0},
 draw:function(S,t){var x=S.x,lw=S.lw,sy=S.cy+S.lh*.66,rx=lw*.88,ry=lw*.13;bg(S,.2+.35*E(P(t,1.2,3.2)));
  x.globalAlpha=E(P(t,0,.8));var g=x.createRadialGradient(S.cx,sy,0,S.cx,sy,rx);g.addColorStop(0,'rgba(233,180,76,.26)');g.addColorStop(1,'rgba(233,180,76,0)');x.fillStyle=g;x.save();x.translate(S.cx,sy);x.scale(1,ry/rx);x.beginPath();x.arc(0,0,rx,0,6.283);x.restore();x.fill();x.globalAlpha=1;
  [1.2,1.5,1.85,2.8,3.9,5].forEach(function(t0,i){var k=P(t,t0,t0+1.8);if(k<=0||k>=1)return;x.globalAlpha=(1-k)*(i<3?.95:.4);x.strokeStyle=i%2?'#D08A50':'#E9B44C';x.lineWidth=1.4;x.beginPath();x.ellipse(S.cx,sy,rx*k*1.1+1,ry*k*1.1+.3,0,0,6.283);x.stroke()});x.globalAlpha=1;
  var fk=P(t,.3,1.2);if(fk>0&&fk<1){var y0=-lw*.3,y=y0+(sy-y0)*fk*fk,d=lw*.065;x.save();x.translate(S.cx,y-d);x.scale(1,1.15);var og=x.createRadialGradient(-d*.35,-d*.35,0,0,0,d*1.4);og.addColorStop(0,'#FFF4D2');og.addColorStop(.45,'#E9B44C');og.addColorStop(1,'#8A5E12');x.fillStyle=og;x.beginPath();x.moveTo(0,-2.4*d);x.bezierCurveTo(d*.6,-1.4*d,d*1.05,-.6*d,d,0);x.arc(0,0,d,0,Math.PI);x.bezierCurveTo(-d*1.05,-.6*d,-d*.6,-1.4*d,0,-2.4*d);x.fill();x.fillStyle='rgba(255,255,255,.75)';x.beginPath();x.ellipse(-d*.35,-d*.3,d*.18,d*.28,-.4,0,6.283);x.fill();x.restore()}
  if(fk>=1&&!S.hit){S.hit=1;for(var i=0;i<30;i++)S.p.push({x:S.cx+R(-6,6),y:sy,vx:R(-1,1)*lw*.9,vy:-R(.7,1.5)*lw*1.4,l:0,L:R(.6,1.1),r:R(1.2,2.6)})}
  var sp=sprite('240,190,90',1);x.globalCompositeOperation='lighter';S.p=S.p.filter(function(p){p.l+=S.dt;p.vy+=lw*6*S.dt;p.x+=p.vx*S.dt;p.y+=p.vy*S.dt;if(p.y>sy+2)return false;var k=1-p.l/p.L;if(k<=0)return false;dot(x,sp,p.x,p.y,p.r*2.4,k);return true});x.globalCompositeOperation='source-over';x.globalAlpha=1;
  var a=E(P(t,1.5,3.1)),dy=(1-E(P(t,1.5,3.3)))*S.lh*.55,gl={g:S.tint('#E9B44C'),gr:lw*.025,ga:a*.7*(1-P(t,3.6,5.4)),dy:dy};
  x.save();x.beginPath();x.rect(0,0,S.W,sy);x.clip();logo(S,a,1,gl);x.restore();
  x.save();x.beginPath();x.rect(0,sy,S.W,S.H);x.clip();x.translate(N(t*3,1)*2,2*sy);x.scale(1,-1);logo(S,a*.16,1,{dy:dy});x.restore();
  fin(S,t,4,5)}},
// 8 أوراق ريحان
{k:'herbs',d:7.4,init:function(S){S.l=[];var n=11;for(var i=0;i<n;i++){var an=i/n*6.283+R(-.15,.15);S.l.push({tx:S.cx+Math.cos(an)*S.lw*.8,ty:S.cy+Math.sin(an)*S.lh*.95,sx:S.cx+R(-S.W*.45,S.W*.45),sy:-R(40,180),t0:.3+i*.16+R(0,.15),dur:R(1.8,2.4),rot:an+1.571+R(-.4,.4),ph:R(0,50),s:R(.85,1.15),c:i%3})}},
 draw:function(S,t){var x=S.x;bg(S,.28*E(P(t,1.2,3.2)));
  S.l.forEach(function(l){var k=P(t,l.t0,l.t0+l.dur);if(k<=0)return;var e=E(k),X=l.sx+(l.tx-l.sx)*e+(1-e)*S.lw*.35*Math.sin(t*2.4+l.ph),Y=l.sy+(l.ty-l.sy)*EIO(k),fl=k<1?Math.cos(t*4.5+l.ph)*(1-e)+e:1,ro=l.rot+(1-e)*Math.sin(t*1.8+l.ph)*1.6;
   if(k>=1){var q=t-l.t0-l.dur;ro+=Math.sin(q*7)*.08*Math.exp(-q*2.5)}
   x.save();x.translate(X,Y);x.rotate(ro);x.scale(1,Math.abs(fl)<.08?.08:fl);drawLeaf(x,S.lw*.15*l.s,l.c);x.restore()});
  var a=E(P(t,2.6,3.8));logo(S,a,.95+.05*a,{g:S.tint('#7DA35F'),gr:S.lw*.02,ga:a*.4*(1-P(t,3.8,5.2))});fin(S,t,4.1,5.1)}},
// 9 دقيق
{k:'flour',d:7,init:function(S){S.p=[];S.c=[];S.b=0},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.22);var dk=P(t,.2,.9);
  if(dk<1){var y=S.cy-S.H*.45+S.H*.45*dk*dk,g=x.createRadialGradient(S.cx-lw*.03,y-lw*.03,0,S.cx,y,lw*.1);g.addColorStop(0,'#FFF8EE');g.addColorStop(1,'#CDBFAE');x.globalAlpha=E(P(t,.2,.4));x.fillStyle=g;x.beginPath();x.arc(S.cx,y,lw*.085,0,6.283);x.fill();x.globalAlpha=1}
  if(dk>=1&&!S.b){S.b=1;for(var i=0;i<560;i++){var an=R(0,6.283),v=Math.pow(Math.random(),.6)*lw*2.7;S.p.push({x:S.cx,y:S.cy,vx:Math.cos(an)*v,vy:Math.sin(an)*v*.7-lw*.3,r:R(.7,1.9),l:0,L:R(2,4)})}for(i=0;i<28;i++){an=R(0,6.283);v=R(.2,1)*lw*.95;S.c.push({x:S.cx,y:S.cy,vx:Math.cos(an)*v,vy:Math.sin(an)*v*.6,r:lw*R(.15,.3),l:0,L:R(2,3.4)})}}
  var a=E(P(t,1.2,3));logo(S,a,1+.07*(1-E(P(t,1,3))),{});
  var sc=sprite('245,238,228',.3);S.c=S.c.filter(function(c){c.l+=S.dt;var d=Math.exp(-2.2*S.dt);c.vx*=d;c.vy*=d;c.x+=c.vx*S.dt;c.y+=c.vy*S.dt;c.r+=lw*.25*S.dt;var k=c.l/c.L;if(k>=1)return false;dot(x,sc,c.x,c.y,c.r,(1-k)*(1-k));return true});
  x.fillStyle='#F5EEE4';S.p=S.p.filter(function(p){p.l+=S.dt;var d=Math.exp(-2.6*S.dt);p.vx*=d;p.vy=p.vy*d+lw*.35*S.dt;p.x+=p.vx*S.dt;p.y+=p.vy*S.dt;var k=p.l/p.L;if(k>=1)return false;x.globalAlpha=(1-k)*.9;x.fillRect(p.x,p.y,p.r,p.r);return true});x.globalAlpha=1;
  fin(S,t,3.6,4.6)}},
// 10 قدر يغلي
{k:'boil',d:7.2,init:function(S){S.b=[];S.p=[]},
 draw:function(S,t){var x=S.x,lw=S.lw,R0=lw*.74;bg(S,.25);x.globalAlpha=E(P(t,0,.8));
  var g=x.createRadialGradient(S.cx,S.cy,R0*.1,S.cx,S.cy,R0);g.addColorStop(0,'#33241A');g.addColorStop(1,'#120E0B');x.fillStyle=g;x.beginPath();x.arc(S.cx,S.cy,R0,0,6.283);x.fill();
  var gr=x.createLinearGradient(S.cx-R0,S.cy-R0,S.cx+R0,S.cy+R0);gr.addColorStop(0,'#F0B888');gr.addColorStop(.5,'#6E4325');gr.addColorStop(1,'#C98A55');x.lineWidth=lw*.05;x.strokeStyle=gr;x.beginPath();x.arc(S.cx,S.cy,R0+lw*.024,0,6.283);x.stroke();x.globalAlpha=1;
  var n=(t<6.6?(3+30*E(P(t,.4,2.8))):0)*S.dt;for(;n>0;n--)if(n>=1||Math.random()<n){var an=R(0,6.283),r=Math.sqrt(Math.random())*R0*.86;S.b.push({x:S.cx+Math.cos(an)*r,y:S.cy+Math.sin(an)*r,R:lw*R(.015,.055),l:0,L:R(.5,1.3)})}
  S.b=S.b.filter(function(b){b.l+=S.dt;var k=b.l/b.L;if(k>=1.25)return false;if(k<1){var r=b.R*E(k);x.globalAlpha=1;x.strokeStyle='rgba(230,167,116,.75)';x.lineWidth=1;x.beginPath();x.arc(b.x,b.y,r,0,6.283);x.stroke();x.fillStyle='rgba(255,220,180,.10)';x.fill();x.fillStyle='rgba(255,255,255,.7)';x.beginPath();x.arc(b.x-r*.35,b.y-r*.35,r*.2,0,6.283);x.fill()}else{var q=(k-1)/.25;x.globalAlpha=1-q;x.strokeStyle='rgba(255,220,180,.85)';x.lineWidth=1;x.beginPath();x.arc(b.x,b.y,b.R*(1+q),0,6.283);x.stroke()}return true});x.globalAlpha=1;
  if(t>2&&t<6.5&&Math.random()<.35)S.p.push({x:S.cx+R(-R0*.6,R0*.6),y:S.cy+R(-R0*.3,R0*.5),vy:-lw*R(.2,.35),r:lw*.07,l:0,L:R(2,3),ph:R(0,30),a:.7});
  S.p=steamP(S,S.p,sprite('236,224,210',.16));
  var a=E(P(t,2.4,3.8));logo(S,a,.9+.1*E(P(t,2.4,4)),{g:S.tint('#E6A774'),gr:lw*.022,ga:a*.55*(1-P(t,4,5.4))});fin(S,t,4.1,5)}}
];

// ---------- engine ----------
function mount(host,i,opts){opts=opts||{};var sc=SC[i],alive=true,raf=0;
  var c=document.createElement('canvas');c.style.cssText='position:absolute;left:0;top:0;width:100%;height:100%;display:block';host.innerHTML='';host.appendChild(c);
  var W=host.clientWidth||innerWidth,H=host.clientHeight||innerHeight,dpr=Math.min(window.devicePixelRatio||1,2);c.width=Math.round(W*dpr);c.height=Math.round(H*dpr);
  var x=c.getContext('2d'),lw=Math.min(W*.6,270),S={x:x,W:W,H:H,cx:W/2,cy:H*.46,lw:lw,lh:lw*252/360,dpr:dpr,t:0,dt:0};
  x.fillStyle='#0E0D0C';x.fillRect(0,0,c.width,c.height);
  ready.then(function(){if(!alive)return;
    var L=mk(lw*dpr,S.lh*dpr);L.getContext('2d').drawImage(img,0,0,L.width,L.height);S.L=L;S.tmp=mk(L.width,L.height);S.tmp2=mk(L.width,L.height);S.G=sprite('208,138,80',.55);S.T={};
    S.tint=function(col){return S.T[col]||(S.T[col]=tint(L,col))};
    if(opts.still){x.setTransform(dpr,0,0,dpr,0,0);bg(S,.3);logo(S,1,1,{});tag(S,1,0);return}
    sc.init&&sc.init(S);var t0=null,last=0;
    function f(now){if(!alive)return;if(t0===null){t0=now;last=now}S.t=(now-t0)/1000;S.dt=Math.min(.05,Math.max(0,(now-last)/1000));last=now;
      x.setTransform(dpr,0,0,dpr,0,0);try{sc.draw(S,S.t)}catch(err){alive=false;try{x.setTransform(dpr,0,0,dpr,0,0);bg(S,.3);logo(S,1,1,{});tag(S,1,0)}catch(e2){}return}x.globalAlpha=1;x.globalCompositeOperation='source-over';raf=requestAnimationFrame(f)}
    raf=requestAnimationFrame(f)});
  return function(){alive=false;cancelAnimationFrame(raf)}}
function pick(){var n=SC.length,last=-1,i;try{last=parseInt(localStorage.getItem('tinta-splash'),10)}catch(e){}i=Math.floor(Math.random()*n);if(i===last)i=(i+1+Math.floor(Math.random()*(n-1)))%n;try{localStorage.setItem('tinta-splash',String(i))}catch(e){}return i}
window.TintaSplash={SC:SC,mount:mount,pick:pick,dur:function(i){return SC[i].d*1000}};

// ---------- in the app / بالتطبيق ----------
var e=document.getElementById('splash');if(!e)return;
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches,tm,t2,stop=function(){},hid=0,started=false;
function go(){clearTimeout(tm);if(e.classList.contains('out'))return;e.classList.add('out');t2=setTimeout(function(){e.classList.add('gone');stop();e.innerHTML=''},700)}
function show(){clearTimeout(tm);clearTimeout(t2);stop();e.classList.remove('out','gone');var i=pick();stop=mount(e,i,{still:RM});tm=setTimeout(go,RM?900:SC[i].d*1000)}
function start(){if(started)return;started=true;show()}
e.addEventListener('click',go);
// نبدي الحركة بعد ما التطبيق يخلص تحميله، حتى تمشي ناعمة بدون تقطيع
if(document.readyState==='complete')setTimeout(start,60);else{window.addEventListener('load',function(){setTimeout(start,120)});setTimeout(start,3000)}
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden'){hid=Date.now()}else if(started&&hid&&Date.now()-hid>3000&&!document.body.classList.contains('cooking')){show()}});
window.addEventListener('pageshow',function(v){if(v.persisted&&started)show()});
})();
