// Tintå: lisäanimaatiot / 12 حركة إضافية (شوية، صوص، طماطة، عجين، قهوة، صحن، شموع، ثلج، كريسمس، ألعاب نارية، عيد ميلاد، صباح الخير)
(function(){
var T=window.TintaSplash,H=T.H,cl=H.cl,P=H.P,E=H.E,EIO=H.EIO,EB=H.EB,N=H.N,R=H.R,mk=H.mk,sprite=H.sprite,dot=H.dot,rr=H.rr,bg=H.bg,logo=H.logo,wipe=H.wipe,shine=H.shine,tag=H.tag,fin=H.fin,steamP=H.steamP,drawLeaf=H.drawLeaf;
function maskFill(S,key,fn){var c=S[key]||(S[key]=mk(S.L.width,S.L.height)),x=c.getContext('2d');x.setTransform(1,0,0,1,0,0);x.globalCompositeOperation='source-over';x.globalAlpha=1;x.clearRect(0,0,c.width,c.height);x.drawImage(S.L,0,0);x.globalCompositeOperation='source-in';fn(x,c.width,c.height);x.globalCompositeOperation='source-over';return c}
function retint(S,key,src,col){var c=S[key]||(S[key]=mk(src.width,src.height)),x=c.getContext('2d');x.globalCompositeOperation='source-over';x.clearRect(0,0,c.width,c.height);x.drawImage(src,0,0);x.globalCompositeOperation='source-in';x.fillStyle=col;x.fillRect(0,0,c.width,c.height);x.globalCompositeOperation='source-over';return c}
function text(S,s,y,size,col,a,font){if(a<=0)return;var x=S.x;x.globalAlpha=a;x.fillStyle=col;x.font=(font||'italic 600 ')+Math.round(size)+'px Georgia,"Times New Roman",serif';x.textAlign='center';x.textBaseline='middle';x.fillText(s,S.cx,y);x.textAlign='start';x.globalAlpha=1}
function stream(x,x0,y0,y1,w,c0,c1,t){if(y1<=y0)return;var g=x.createLinearGradient(0,y0,0,y1);g.addColorStop(0,c0);g.addColorStop(1,c1);x.fillStyle=g;x.globalAlpha=1;x.beginPath();var n=12,i,yy,ww;for(i=0;i<=n;i++){yy=y0+(y1-y0)*i/n;ww=w*(1+.15*Math.sin(t*20+i));x.lineTo(x0+N(t*3+i*.3,1)*1.5-ww/2,yy)}for(i=n;i>=0;i--){yy=y0+(y1-y0)*i/n;ww=w*(1+.15*Math.sin(t*20+i));x.lineTo(x0+N(t*3+i*.3,1)*1.5+ww/2,yy)}x.closePath();x.fill()}

var NEW=[
// 1 الشوية
{k:'grill',n:'الشوية',d:7.6,init:function(S){S.p=[];S.e=[];S.c=[];for(var i=0;i<22;i++)S.c.push({x:R(-.7,.7),y:R(-.55,.55),r:R(.12,.22),ph:R(0,50)})},
 draw:function(S,t){var x=S.x,lw=S.lw,heat=E(P(t,0,2));bg(S,.15+.35*heat);
  x.save();x.translate(S.cx,S.cy);x.rotate(-.42);x.globalCompositeOperation='lighter';
  S.c.forEach(function(c){dot(x,sprite('255,110,40',.9),c.x*lw,c.y*lw,c.r*lw*(1+.15*N(t*3,c.ph)),heat*(.35+.2*N(t*2,c.ph)))});
  x.globalCompositeOperation='source-over';
  for(var i=-6;i<=6;i++){var y=i*lw*.13,g=x.createLinearGradient(0,y-lw*.02,0,y+lw*.02);g.addColorStop(0,'#3A332D');g.addColorStop(.5,'rgb('+Math.round(42+180*heat)+','+Math.round(36+60*heat)+',30)');g.addColorStop(1,'#1A1714');x.fillStyle=g;x.globalAlpha=E(P(t,0,.6));x.fillRect(-lw*.95,y-lw*.017,lw*1.9,lw*.034)}
  x.restore();x.globalAlpha=1;
  var a=E(P(t,1.5,2.5));if(a>0){logo(S,a,1,{g:S.tint('#FF8A3D'),gr:lw*.02,ga:a*.5});
   var m=E(P(t,2.4,3.6));if(m>0){var c=maskFill(S,'gm',function(cx,w,h){cx.translate(w/2,h/2);cx.rotate(-.42);for(var i=-8;i<=8;i++){cx.fillStyle='rgba(58,30,14,.85)';cx.fillRect(-w,i*S.lw*.13*S.dpr-S.lw*.012*S.dpr,w*2,S.lw*.024*S.dpr)}});x.globalAlpha=m;x.drawImage(c,S.cx-lw/2,S.cy-S.lh/2,lw,S.lh);x.globalAlpha=1}}
  if(t>2.3&&t<6.6&&Math.random()<.6)S.p.push({x:S.cx+R(-lw*.45,lw*.45),y:S.cy+R(-S.lh*.3,S.lh*.3),vy:-lw*R(.2,.35),r:lw*.05,l:0,L:R(1.6,2.6),ph:R(0,30),a:.8});
  S.p=steamP(S,S.p,sprite('170,160,150',.16));
  if(t<6.4&&Math.random()<.25*heat)S.e.push({x:S.cx+R(-lw*.7,lw*.7),y:S.cy+R(-lw*.4,lw*.5),vx:R(-15,15),vy:-R(30,70),l:0,L:R(.6,1.3)});
  x.globalCompositeOperation='lighter';S.e=S.e.filter(function(e){e.l+=S.dt;e.x+=e.vx*S.dt;e.y+=e.vy*S.dt;var k=1-e.l/e.L;if(k<=0)return false;dot(x,sprite('255,160,70',1),e.x,e.y,3.5,k);return true});x.globalCompositeOperation='source-over';
  fin(S,t,4.2,5.4)}},
// 2 صب الصوص يلف
{k:'pour',n:'صب ويلف',d:7.4,init:function(S){},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.3);var grow=E(P(t,.7,2.8)),Rm=lw*.6*grow,rot=t*1.1,top=P(t,1.9,2.5)*S.cy,bot=P(t,.25,.7)*S.cy;
  if(grow>0){var th=6*6.283*grow,n=Math.floor(260*grow),fade=1-.55*P(t,3,4.2);for(var i=0;i<n;i++){var u=i/260,a=u*6*6.283+rot,r=Rm*(i/Math.max(1,n)),px=S.cx+Math.cos(a)*r,py=S.cy+Math.sin(a)*r*.92,w=lw*.032*(1-.6*i/Math.max(1,n))+1;x.globalAlpha=fade;x.fillStyle=i%2?'#B8642E':'#9C4A1E';x.beginPath();x.arc(px,py,w,0,6.283);x.fill();if(i%3===0){x.fillStyle='rgba(255,220,190,.35)';x.beginPath();x.arc(px-w*.3,py-w*.4,w*.35,0,6.283);x.fill()}}x.globalAlpha=1}
  if(bot>top)stream(x,S.cx,top,bot,lw*.04,'#C27A42','#8E4419',t);
  var a=E(P(t,2.6,3.8));logo(S,a,.6+.4*E(P(t,2.6,3.9)),{g:S.tint('#E6A774'),gr:lw*.02,ga:a*.5*(1-P(t,4,5.4))});fin(S,t,4.3,5.4)}},
// 3 تقطيع طماطة
{k:'tomato',n:'تقطيع طماطة',d:7.6,init:function(S){S.sl=[];for(var i=0;i<6;i++)S.sl.push({a:-1.571+i/6*6.283,ph:R(0,9),sp:R(-1,1)})},
 draw:function(S,t){var x=S.x,lw=S.lw,r=lw*.2;bg(S,.3);
  function slice(px,py,rr2,ro){x.save();x.translate(px,py);x.rotate(ro);x.fillStyle='#C9301F';x.beginPath();x.arc(0,0,rr2,0,6.283);x.fill();x.fillStyle='#F07A5E';x.beginPath();x.arc(0,0,rr2*.84,0,6.283);x.fill();
   for(var k=0;k<4;k++){var an=k*1.571+.785;x.fillStyle='#F4A27E';x.beginPath();x.ellipse(Math.cos(an)*rr2*.45,Math.sin(an)*rr2*.45,rr2*.26,rr2*.18,an,0,6.283);x.fill();x.fillStyle='#F7E3A0';for(var j=0;j<3;j++){x.beginPath();x.ellipse(Math.cos(an)*rr2*(.35+j*.1),Math.sin(an)*rr2*(.35+j*.1),rr2*.04,rr2*.025,an,0,6.283);x.fill()}}
   x.fillStyle='#F8B79C';x.beginPath();x.arc(0,0,rr2*.14,0,6.283);x.fill();x.restore()}
  if(t<2.05){var s=EB(P(t,0,.8)),y=S.cy-(1-E(P(t,0,.6)))*S.H*.4;x.save();x.translate(S.cx,y);x.scale(s,s);var g=x.createRadialGradient(-r*.35,-r*.35,r*.1,0,0,r);g.addColorStop(0,'#FF7A5C');g.addColorStop(.6,'#E2381F');g.addColorStop(1,'#8E1A0E');x.fillStyle=g;x.beginPath();x.arc(0,0,r,0,6.283);x.fill();x.fillStyle='rgba(255,255,255,.55)';x.beginPath();x.ellipse(-r*.4,-r*.45,r*.16,r*.1,-.6,0,6.283);x.fill();
   x.fillStyle='#4E7A3A';for(var k=0;k<5;k++){x.save();x.translate(0,-r*.92);x.rotate(k/5*6.283);x.beginPath();x.ellipse(0,-r*.16,r*.07,r*.18,0,0,6.283);x.fill();x.restore()}x.restore()}
  [1.2,1.5,1.8].forEach(function(t0,i){var k=P(t,t0,t0+.25);if(k<=0||k>=1)return;var xx=S.cx+(i-1)*r*.6;x.globalCompositeOperation='lighter';x.strokeStyle='rgba(255,240,220,'+Math.sin(Math.PI*k)+')';x.lineWidth=2;x.beginPath();x.moveTo(xx,S.cy-r*1.6);x.lineTo(xx,S.cy+r*1.6);x.stroke();x.globalCompositeOperation='source-over'});
  if(t>=2.05){var k=EB(P(t,2.05,3));S.sl.forEach(function(s2){var an=s2.a+t*.18,rad=lw*.72*k,px=S.cx+Math.cos(an)*rad,py=S.cy+Math.sin(an)*rad*.9;slice(px,py,lw*.11*(.7+.3*k),s2.sp*t*.6+s2.ph)})}
  var a=E(P(t,2.6,3.7));logo(S,a,.92+.08*a,{});fin(S,t,4.2,5.3)}},
// 4 العجين والشوبك
{k:'dough',n:'العجين والشوبك',d:7.8,init:function(S){S.p=[]},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.3);var pin=EIO(P(t,1,3.2)),px=S.cx-lw*.75+pin*lw*1.5,da=E(P(t,0,.7))*(1-P(t,4.2,5.2)),grow=.45+.6*pin;
  if(da>0){x.globalAlpha=da;var g=x.createRadialGradient(S.cx-lw*.2,S.cy-lw*.1,lw*.1,S.cx,S.cy,lw*grow);g.addColorStop(0,'#F4E6CF');g.addColorStop(1,'#D9C3A2');x.fillStyle=g;x.beginPath();for(var i=0;i<=40;i++){var an=i/40*6.283,rx=lw*grow*(1+.04*Math.sin(an*5+1)),ry=S.lh*.85*(.7+.3*pin)*(1+.05*Math.sin(an*3));x.lineTo(S.cx+Math.cos(an)*rx,S.cy+Math.sin(an)*ry)}x.closePath();x.fill();x.globalAlpha=1;
   var f=cl((px-(S.cx-lw/2))/lw,0,1.1);if(f>0){var c=wipe(S,f/1.1,.05),hi=retint(S,'dh',c,'#FFF7EA'),lo=retint(S,'dl',c,'#A07C55');x.globalAlpha=da*.8;x.drawImage(hi,S.cx-lw/2-1,S.cy-S.lh/2-1,lw,S.lh);x.globalAlpha=da;x.drawImage(lo,S.cx-lw/2,S.cy-S.lh/2,lw,S.lh);x.globalAlpha=1}}
  if(pin>0&&pin<1&&Math.random()<.5)S.p.push({x:px+R(-6,6),y:S.cy+R(-S.lh*.6,S.lh*.6),vy:-lw*R(.05,.15),vx:R(-20,20),r:lw*.03,l:0,L:R(.8,1.5),ph:R(0,9),a:.8});
  S.p=steamP(S,S.p,sprite('245,238,228',.35));
  var pa=E(P(t,.6,1))*(1-P(t,3.2,3.7));if(pa>0){var ph=lw*1.05,pw=lw*.12,py=S.cy+(1-E(P(t,.6,1)))*-S.H*.3;x.globalAlpha=pa;var gw=x.createLinearGradient(px-pw/2,0,px+pw/2,0);gw.addColorStop(0,'#7A4E2A');gw.addColorStop(.35,'#E2B07A');gw.addColorStop(1,'#6A4022');x.fillStyle=gw;rr(x,px-pw/2,py-ph/2,pw,ph,pw*.4);x.fill();x.fillStyle='#5A3A20';rr(x,px-pw*.25,py-ph/2-lw*.16,pw*.5,lw*.17,pw*.2);x.fill();rr(x,px-pw*.25,py+ph/2-lw*.01,pw*.5,lw*.17,pw*.2);x.fill();
   x.strokeStyle='rgba(90,55,25,.4)';x.lineWidth=1;for(var j=0;j<3;j++){var off=((t*90+j*pw*.33)%pw)-pw/2;x.beginPath();x.moveTo(px+off,py-ph/2+4);x.lineTo(px+off,py+ph/2-4);x.stroke()}x.globalAlpha=1}
  logo(S,E(P(t,4.2,5.2)),1,{});fin(S,t,5,5.9)}},
// 5 قهوة الصبح
{k:'latte',n:'قهوة الصبح',d:7.8,init:function(S){S.p=[];S.tagDy=S.lw*.42},
 draw:function(S,t){var x=S.x,lw=S.lw,ca=E(P(t,0,.8));bg(S,.25);x.globalAlpha=ca;
  var g=x.createRadialGradient(S.cx,S.cy,lw*.5,S.cx,S.cy,lw*.86);g.addColorStop(0,'#D8D2C8');g.addColorStop(1,'#9C958B');x.fillStyle=g;x.beginPath();x.arc(S.cx,S.cy,lw*.84,0,6.283);x.fill();
  x.fillStyle='#F4F1EC';x.beginPath();x.arc(S.cx,S.cy,lw*.66,0,6.283);x.fill();x.fillStyle='#F4F1EC';rr(x,S.cx+lw*.6,S.cy-lw*.08,lw*.22,lw*.16,lw*.08);x.fill();
  var cg=x.createRadialGradient(S.cx,S.cy,lw*.1,S.cx,S.cy,lw*.58);cg.addColorStop(0,'#7A4A2A');cg.addColorStop(.85,'#4A2A16');cg.addColorStop(1,'#A06A3C');x.fillStyle=cg;x.beginPath();x.arc(S.cx,S.cy,lw*.58,0,6.283);x.fill();x.globalAlpha=1;
  var fr=E(P(t,.9,2.8))*lw*.46;if(fr>0){x.fillStyle='#F3E6D3';x.beginPath();for(var i=0;i<=48;i++){var an=i/48*6.283,rr2=fr*(1+.05*N(an*2+t,3));x.lineTo(S.cx+Math.cos(an)*rr2,S.cy+Math.sin(an)*rr2)}x.closePath();x.fill();x.strokeStyle='rgba(160,106,60,.35)';x.lineWidth=2;x.stroke()}
  var top=P(t,2.2,2.7)*S.cy,bot=P(t,.6,.95)*S.cy;if(bot>top)stream(x,S.cx,top,bot,lw*.035,'#FFFFFF','#F1E4D0',t);
  var w=P(t,2.8,4.2);if(w>0){var c=wipe(S,EIO(w),.1),br=retint(S,'lb',c,'#7A4A2A'),sc=.72;x.drawImage(br,S.cx-lw*sc/2,S.cy-S.lh*sc/2,lw*sc,S.lh*sc)}
  if(t>1.5&&t<7&&Math.random()<.3)S.p.push({x:S.cx+R(-lw*.3,lw*.3),y:S.cy-lw*.2,vy:-lw*R(.15,.25),r:lw*.06,l:0,L:R(1.8,2.6),ph:R(0,30),a:.6});
  S.p=steamP(S,S.p,sprite('236,224,210',.14));
  var k=E(P(t,4.4,5.3));tag(S,k,(1-k)*8)}},
// 6 ترتيب الصحن
{k:'plate',n:'ترتيب الصحن',d:7.6,init:function(S){},
 draw:function(S,t){var x=S.x,lw=S.lw,rot=t*.22,pa=E(P(t,0,.8));bg(S,.25);
  x.globalAlpha=pa;var g=x.createRadialGradient(S.cx-lw*.2,S.cy-lw*.2,lw*.1,S.cx,S.cy,lw*.9);g.addColorStop(0,'#2C2824');g.addColorStop(1,'#161311');x.fillStyle=g;x.beginPath();x.arc(S.cx,S.cy,lw*.86,0,6.283);x.fill();x.strokeStyle='rgba(230,167,116,.3)';x.lineWidth=1.2;x.stroke();x.strokeStyle='rgba(255,255,255,.05)';x.beginPath();x.arc(S.cx,S.cy,lw*.66,0,6.283);x.stroke();x.globalAlpha=1;
  var sw=EIO(P(t,2.4,3.1));if(sw>0){x.strokeStyle='#B8703A';x.lineWidth=lw*.03;x.lineCap='round';x.beginPath();x.arc(S.cx,S.cy,lw*.56,1.1+rot,1.1+rot+1.0*sw);x.stroke()}
  for(var i=0;i<7;i++){var s=EB(P(t,.6+i*.13,.95+i*.13));if(s<=0)continue;var an=3.5+i*.28+rot;x.fillStyle=i%2?'#D08A50':'#8E4A22';x.beginPath();x.arc(S.cx+Math.cos(an)*lw*.62,S.cy+Math.sin(an)*lw*.62,lw*(.022+.012*(3-Math.abs(3-i))/3)*s,0,6.283);x.fill()}
  for(i=0;i<7;i++){s=EB(P(t,1.5+i*.12,1.9+i*.12));if(s<=0)continue;an=.25+i*.36+rot;x.save();x.translate(S.cx+Math.cos(an)*lw*.64,S.cy+Math.sin(an)*lw*.64);x.rotate(an+i);x.scale(s,s);drawLeaf(x,lw*.09,i%3);x.restore()}
  for(i=0;i<5;i++){s=EB(P(t,2.1+i*.08,2.4+i*.08));if(s<=0)continue;an=2.4+i*.12+rot;x.fillStyle=['#F2A7C3','#F7D36B','#C9A3F0'][i%3];x.beginPath();x.arc(S.cx+Math.cos(an)*lw*.7,S.cy+Math.sin(an)*lw*.7,lw*.016*s,0,6.283);x.fill()}
  var a=E(P(t,2.6,3.6));logo(S,a,.9+.1*a,{});fin(S,t,4.1,5.2)}},
// 7 الليل والشموع
{k:'night',n:'الليل والشموع',d:7.6,init:function(S){S.b=[];for(var i=0;i<18;i++)S.b.push({x:R(0,S.W),y:R(0,S.H),r:R(.12,.3)*S.lw,ph:R(0,50),c:['255,190,110','255,150,80','255,220,160'][i%3]})},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.15*E(P(t,1,3)));x.globalCompositeOperation='lighter';S.b.forEach(function(b){dot(x,sprite(b.c,.35),b.x+N(t*.3,b.ph)*20,b.y+N(t*.25,b.ph+3)*20,b.r,E(P(t,.3,2.5))*(.25+.15*N(t,b.ph)))});x.globalCompositeOperation='source-over';
  var by=S.cy+S.lh*1.65;[-1,0,1].forEach(function(k,i){var cx2=S.cx+k*lw*.42,h=lw*(i===1?.36:.26),w=lw*.09,ti=.4+i*.5,on=E(P(t,ti,ti+.3));var g=x.createLinearGradient(cx2-w/2,0,cx2+w/2,0);g.addColorStop(0,'#CDBFA6');g.addColorStop(.4,'#F6EEDD');g.addColorStop(1,'#B8A88E');x.globalAlpha=E(P(t,0,.6));x.fillStyle=g;rr(x,cx2-w/2,by-h,w,h,w*.15);x.fill();x.strokeStyle='#2A241F';x.lineWidth=1.2;x.beginPath();x.moveTo(cx2,by-h);x.lineTo(cx2,by-h-lw*.03);x.stroke();
   if(on>0){var fl=1+.18*N(t*9,i*7),sw=N(t*5,i)*lw*.008,fh=lw*.075*on*fl,fx=cx2+sw,fy=by-h-lw*.03;x.globalCompositeOperation='lighter';dot(x,sprite('255,170,80',.7),fx,fy-fh*.4,lw*.2*on,.8);x.globalCompositeOperation='source-over';x.globalAlpha=1;var fg=x.createLinearGradient(0,fy,0,fy-fh);fg.addColorStop(0,'#FFE7B0');fg.addColorStop(.5,'#FFB347');fg.addColorStop(1,'rgba(255,120,40,0)');x.fillStyle=fg;x.beginPath();x.moveTo(fx,fy-fh);x.quadraticCurveTo(fx+lw*.022,fy-fh*.35,fx,fy);x.quadraticCurveTo(fx-lw*.022,fy-fh*.35,fx,fy-fh);x.fill();x.fillStyle='rgba(120,170,255,.7)';x.beginPath();x.arc(fx,fy-lw*.006,lw*.008,0,6.283);x.fill()}});x.globalAlpha=1;
  var a=E(P(t,1.8,3.2));logo(S,a,1,{g:S.tint('#FFC27A'),gr:lw*.025,ga:a*.7});fin(S,t,3.9,5.1)}},
// 8 ثلج فنلندا
{k:'snow',n:'ثلج فنلندا',d:7.8,init:function(S){S.f=[];for(var i=0;i<170;i++)S.f.push({x:R(0,S.W),y:R(-S.H,S.H),z:R(.3,1),ph:R(0,50)});
  var c=S.L,w=c.width,h=c.height,d=c.getContext('2d').getImageData(0,0,w,h).data;S.cap=[];for(var X=0;X<w;X+=Math.max(1,Math.round(w/110))){for(var Y=0;Y<h;Y++){if(d[(Y*w+X)*4+3]>120){S.cap.push({x:X/w,y:Y/h,s:R(.6,1.4),d:R(0,1.5)});break}}}},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,0);x.globalAlpha=.35*E(P(t,0,2));x.drawImage(sprite('110,150,220',.5),S.cx-lw*1.5,S.cy-lw*1.5,lw*3,lw*3);x.globalAlpha=1;
  var a=E(P(t,1,2.4));logo(S,a,1,{g:S.tint('#BFD9FF'),gr:lw*.02,ga:a*.5});
  x.fillStyle='#FFFFFF';S.cap.forEach(function(c){var k=E(P(t,2+c.d,3.6+c.d));if(k<=0)return;x.globalAlpha=k*.95;x.beginPath();x.arc(S.cx-lw/2+c.x*lw,S.cy-S.lh/2+c.y*S.lh-1.2*c.s*k,1.4*c.s*k*lw/200+.4,0,6.283);x.fill()});x.globalAlpha=1;
  S.f.forEach(function(f){f.y+=lw*.28*f.z*S.dt;f.x+=N(t*.7,f.ph)*12*f.z*S.dt;if(f.y>S.H+5){f.y=-5;f.x=R(0,S.W)}x.globalAlpha=.4+.5*f.z;x.fillStyle='#F2F6FF';x.beginPath();x.arc(f.x,f.y,(.8+2*f.z)*lw/220,0,6.283);x.fill()});x.globalAlpha=1;
  fin(S,t,4.4,5.6)}},
// 9 أضواء الكريسمس
{k:'lights',n:'أضواء الكريسمس',when:function(d){return d.getMonth()===11&&d.getDate()<=26},d:7.6,init:function(S){S.s=[]},
 draw:function(S,t){var x=S.x,lw=S.lw,C=['255,80,70','255,200,80','90,210,120','110,170,255','255,150,60'];bg(S,.25);
  function line(y0,sag,off,startT){var sw=Math.sin(t*1.4+off)*S.lh*.05,n=13;x.strokeStyle='#2E2A26';x.lineWidth=1.5;x.globalAlpha=1;x.beginPath();for(var i=0;i<=40;i++){var u=i/40,X=u*S.W,Y=y0+Math.sin(Math.PI*u)*(sag+sw);i?x.lineTo(X,Y):x.moveTo(X,Y)}x.stroke();
   for(i=1;i<n;i++){var u2=i/n,bx=u2*S.W,byy=y0+Math.sin(Math.PI*u2)*(sag+sw)+lw*.03,on=P(t,startT+i*.1,startT+i*.1+.15),tw=.65+.35*N(t*3,i+off*7),col=C[(i+off)%C.length];
    x.fillStyle='#3A332C';x.fillRect(bx-lw*.012,byy-lw*.035,lw*.024,lw*.02);x.fillStyle=on>0?'rgb('+col+')':'#3A332C';x.globalAlpha=on>0?.6+.4*tw*on:1;x.beginPath();x.ellipse(bx,byy,lw*.022,lw*.032,0,0,6.283);x.fill();
    if(on>0){x.globalCompositeOperation='lighter';dot(x,sprite(col,.8),bx,byy,lw*.14,on*tw*.8);x.globalCompositeOperation='source-over'}x.globalAlpha=1}}
  line(S.cy-S.lh*1.15,S.lh*.35,0,.4);line(S.cy+S.lh*1.05,S.lh*.3,2,1.1);
  if(t>2&&Math.random()<.2)S.s.push({x:S.cx+R(-lw*.7,lw*.7),y:S.cy+R(-S.lh*.8,S.lh*.8),l:0,L:R(.5,1)});
  x.globalCompositeOperation='lighter';S.s=S.s.filter(function(s){s.l+=S.dt;var k=s.l/s.L;if(k>=1)return false;var a=Math.sin(Math.PI*k),r=lw*.03*a;x.strokeStyle='rgba(255,236,200,'+a+')';x.lineWidth=1;x.beginPath();x.moveTo(s.x-r,s.y);x.lineTo(s.x+r,s.y);x.moveTo(s.x,s.y-r);x.lineTo(s.x,s.y+r);x.stroke();return true});x.globalCompositeOperation='source-over';
  var a=E(P(t,1.8,3));logo(S,a,1,{g:S.tint('#FFD27A'),gr:lw*.02,ga:a*.45});fin(S,t,4.1,5.3)}},
// 10 ألعاب نارية لرأس السنة
{k:'fireworks',n:'ألعاب نارية',when:function(d){return (d.getMonth()===11&&d.getDate()===31)||(d.getMonth()===0&&d.getDate()===1)},d:8,init:function(S){S.r=[];S.p=[];var X=[.25,.72,.45,.82,.15,.55];[.2,.8,1.4,2,2.6,3.3].forEach(function(t0,i){S.r.push({t0:t0,x:S.W*X[i],ty:S.H*R(.12,.34),done:0,c:[['255,210,120','255,160,70'],['255,120,90','255,220,180'],['230,167,116','255,255,255'],['140,190,255','255,255,255'],['255,200,80','255,120,60'],['208,138,80','255,230,200']][i]})})},
 draw:function(S,t){var x=S.x,lw=S.lw;x.globalCompositeOperation='source-over';x.globalAlpha=1;x.fillStyle='rgba(14,13,12,.28)';x.fillRect(0,0,S.W,S.H);if(t<.05){bg(S,0)}
  x.globalCompositeOperation='lighter';
  S.r.forEach(function(r){var k=P(t,r.t0,r.t0+.8);if(k<=0)return;if(k<1){var y=S.H+10-(S.H+10-r.ty)*E(k);dot(x,sprite('255,220,170',1),r.x+N(t*8,r.x)*2,y,4,1);dot(x,sprite('255,170,90',.5),r.x,y+10,6,.6)}else if(!r.done){r.done=1;for(var i=0;i<90;i++){var an=R(0,6.283),v=R(.3,1)*lw*1.1;S.p.push({x:r.x,y:r.ty,vx:Math.cos(an)*v,vy:Math.sin(an)*v,l:0,L:R(1.2,2.2),c:r.c[i%2]})}}});
  S.p=S.p.filter(function(p){p.l+=S.dt;var d=Math.exp(-1.6*S.dt);p.vx*=d;p.vy=p.vy*d+lw*.35*S.dt;p.x+=p.vx*S.dt;p.y+=p.vy*S.dt;var k=1-p.l/p.L;if(k<=0)return false;dot(x,sprite(p.c,1),p.x,p.y,2.6+2*k,k*(.6+.4*Math.random()));return true});
  x.globalCompositeOperation='source-over';
  var a=E(P(t,2.8,3.9));logo(S,a,1,{g:S.tint('#FFD27A'),gr:lw*.025,ga:a*.6});fin(S,t,4.6,5.9)}},
// 11 عيد ميلاد شيف
{k:'bday',n:'عيد ميلاد شيف',when:function(){return false},d:7.8,init:function(S){S.c=[];for(var i=0;i<140;i++)S.c.push({x:R(0,S.W),y:R(-S.H*1.2,-10),vy:R(.25,.5)*S.lw,ph:R(0,50),w:R(4,8),h:R(2,4),c:['#E6A774','#F3EEE6','#D08A50','#F2A7C3','#F7D36B','#9BC27A'][i%6]});S.bl=[{x:-.55,c:'#D08A50',d:0},{x:.6,c:'#E6A774',d:.3},{x:-.15,c:'#F3E3CC',d:.6}]},
 draw:function(S,t){var x=S.x,lw=S.lw;bg(S,.3);
  S.bl.forEach(function(b){var k=P(t,.2+b.d,6+b.d),bx=S.cx+b.x*lw+N(t,b.d*9)*lw*.08,by=S.H+lw*.4-k*(S.H+lw*1.4);x.strokeStyle='rgba(243,238,230,.4)';x.lineWidth=1;x.beginPath();x.moveTo(bx,by+lw*.16);x.quadraticCurveTo(bx+N(t*2,b.d)*10,by+lw*.35,bx,by+lw*.55);x.stroke();var g=x.createRadialGradient(bx-lw*.04,by-lw*.05,lw*.01,bx,by,lw*.16);g.addColorStop(0,'#FFFFFF');g.addColorStop(.25,b.c);g.addColorStop(1,'#5A3A22');x.fillStyle=g;x.globalAlpha=.95;x.beginPath();x.ellipse(bx,by,lw*.12,lw*.15,0,0,6.283);x.fill();x.globalAlpha=1});
  var a=E(P(t,1,2.2));logo(S,a,.9,{dy:-S.lh*.15});
  S.c.forEach(function(c){if(t<.3)return;c.y+=c.vy*S.dt;c.x+=N(t*1.5,c.ph)*20*S.dt;if(c.y>S.H+10&&t<5.5){c.y=-10;c.x=R(0,S.W)}x.save();x.translate(c.x,c.y);x.rotate(t*2+c.ph);x.scale(1,Math.cos(t*5+c.ph));x.fillStyle=c.c;x.fillRect(-c.w/2,-c.h/2,c.w,c.h);x.restore()});
  var k=E(P(t,2.2,3.2));text(S,'Hyvää syntymäpäivää',S.cy+S.lh*.42+(1-k)*8,lw*.085,'#F3EEE6',k);var k2=E(P(t,2.6,3.6));text(S,'Happy birthday, Chef!',S.cy+S.lh*.42+lw*.12+(1-k2)*8,lw*.06,'#E6A774',k2,'600 ');
  x.save();x.translate(0,-S.lh*.15);shine(S,P(t,4,5.3));x.restore()}},
// 12 صباح الخير يا مطبخ
{k:'morning',n:'صباح الخير',d:7.8,init:function(S){S.bd=[{y:.22,s:1,d:.6},{y:.26,s:.8,d:.9}]},
 draw:function(S,t){var x=S.x,lw=S.lw,hz=S.cy+S.lh*.8,rise=E(P(t,.3,3));bg(S,0);
  var sky=x.createLinearGradient(0,0,0,hz);sky.addColorStop(0,'rgba(40,24,16,'+(.9*rise)+')');sky.addColorStop(1,'rgba(200,110,50,'+(.55*rise)+')');x.fillStyle=sky;x.fillRect(0,0,S.W,hz);
  var sy=hz+lw*.3-rise*lw*.45;x.save();x.beginPath();x.rect(0,0,S.W,hz);x.clip();x.globalCompositeOperation='lighter';x.save();x.translate(S.cx,sy);x.rotate(t*.08);for(var i=0;i<18;i++){x.rotate(6.283/18);var g=x.createLinearGradient(0,0,lw*1.4,0);g.addColorStop(0,'rgba(255,190,110,'+(.18*rise)+')');g.addColorStop(1,'rgba(255,190,110,0)');x.fillStyle=g;x.beginPath();x.moveTo(0,0);x.lineTo(lw*1.4,-lw*.06);x.lineTo(lw*1.4,lw*.06);x.closePath();x.fill()}x.restore();
  var sg=x.createRadialGradient(S.cx,sy,0,S.cx,sy,lw*.26);sg.addColorStop(0,'rgba(255,240,200,1)');sg.addColorStop(.6,'rgba(255,170,80,.9)');sg.addColorStop(1,'rgba(255,120,40,0)');x.fillStyle=sg;x.beginPath();x.arc(S.cx,sy,lw*.26,0,6.283);x.fill();x.restore();
  x.strokeStyle='rgba(230,167,116,.5)';x.lineWidth=1;x.beginPath();x.moveTo(0,hz);x.lineTo(S.W,hz);x.stroke();
  x.globalCompositeOperation='source-over';S.bd.forEach(function(b){var k=P(t,b.d,b.d+4.5);if(k<=0||k>=1)return;var bx=-20+(S.W+40)*k,by=S.H*b.y+Math.sin(k*9)*6,f=Math.sin(t*10+b.d*5)*lw*.025*b.s;x.strokeStyle='#1A1410';x.lineWidth=1.6;x.beginPath();x.moveTo(bx-lw*.04*b.s,by-f);x.quadraticCurveTo(bx-lw*.015*b.s,by-lw*.01,bx,by);x.quadraticCurveTo(bx+lw*.015*b.s,by-lw*.01,bx+lw*.04*b.s,by-f);x.stroke()});
  var a=E(P(t,1.6,2.8));logo(S,a,1,{dy:-S.lh*.2,g:S.tint('#FFC27A'),gr:lw*.02,ga:a*.5});
  var k=E(P(t,3,3.9));text(S,'Huomenta, keittiö',hz+lw*.14+(1-k)*8,lw*.085,'#F3EEE6',k);var k2=E(P(t,3.4,4.3));text(S,'Good morning, kitchen',hz+lw*.26+(1-k2)*8,lw*.055,'#E6A774',k2,'600 ');
  x.save();x.translate(0,-S.lh*.2);shine(S,P(t,4.6,5.9));x.restore()}}
];
// ---- Lisää keittiöanimaatioita / حركات طبخ إضافية ----
function pts2(S){if(S._pts)return S._pts;var c=S.L,w=c.width,h=c.height,d=c.getContext('2d').getImageData(0,0,w,h).data,r=[],st=Math.max(1,Math.round(w/150));for(var y=0;y<h;y+=st)for(var i=0;i<w;i+=st)if(d[(y*w+i)*4+3]>110)r.push([i/w,y/h]);for(var k=r.length-1;k>0;k--){var j=Math.random()*(k+1)|0,q=r[k];r[k]=r[j];r[j]=q}return S._pts=r}
function panTop(x,cx,cy,r,a){x.globalAlpha=a;var g=x.createRadialGradient(cx-r*.3,cy-r*.3,r*.1,cx,cy,r);g.addColorStop(0,'#3A3530');g.addColorStop(1,'#141210');x.fillStyle=g;x.beginPath();x.arc(cx,cy,r,0,6.283);x.fill();x.lineWidth=r*.08;x.strokeStyle='#2A2622';x.stroke();x.lineWidth=1;x.strokeStyle='rgba(255,255,255,.12)';x.beginPath();x.arc(cx,cy,r*1.03,3.5,5.2);x.stroke();
  var hg=x.createLinearGradient(cx+r,cy,cx+r*1.9,cy);hg.addColorStop(0,'#2A2622');hg.addColorStop(1,'#3A332C');x.fillStyle=hg;rr(x,cx+r*.95,cy-r*.08,r*.95,r*.16,r*.08);x.fill();x.globalAlpha=1}
var MORE=[
// liekitys / فلامبيه
{k:'flambe',d:7.4,init:function(S){S.f=[];S.sp=[];S.pc=[];for(var i=0;i<9;i++)S.pc.push({x:R(-.42,.42),y:R(-.06,.06),r:R(.5,1),ph:R(0,9)})},
 draw:function(S,t){var x=S.x,lw=S.lw,py=S.cy+S.lh*1.3,prx=lw*.62,pry=lw*.17,a=E(P(t,0,.7)),burst=P(t,1.3,1.6)*(1-.75*P(t,2.6,4.6));bg(S,.2+.55*burst);
  x.globalAlpha=a;var g=x.createLinearGradient(0,py-pry,0,py+pry);g.addColorStop(0,'#3A3530');g.addColorStop(1,'#0E0C0B');x.fillStyle=g;x.beginPath();x.ellipse(S.cx,py,prx,pry,0,0,6.283);x.fill();x.strokeStyle='#4A433C';x.lineWidth=lw*.02;x.stroke();
  x.fillStyle='#2A2622';rr(x,S.cx+prx*.95,py-lw*.02,lw*.5,lw*.05,lw*.025);x.fill();
  S.pc.forEach(function(p){var j=Math.sin(t*30+p.ph)*1.2;x.fillStyle='#E8804A';x.beginPath();x.ellipse(S.cx+p.x*prx*1.4,py+p.y*pry*3+j,lw*.04*p.r,lw*.022*p.r,p.ph,0,6.283);x.fill();x.fillStyle='rgba(255,230,200,.6)';x.beginPath();x.ellipse(S.cx+p.x*prx*1.4-lw*.01,py+p.y*pry*3+j-lw*.006,lw*.012*p.r,lw*.006*p.r,0,0,6.283);x.fill()});x.globalAlpha=1;
  x.globalCompositeOperation='lighter';
  var n=t<6.5?(t<1.3?6:t<1.6?260:20+160*burst)*S.dt:0;for(;n>0;n--)if(n>=1||Math.random()<n)S.f.push({x:S.cx+R(-prx*.8,prx*.8),y:py-R(0,pry),vx:R(-20,20),vy:-lw*R(.9,1.8)*(t>1.3?1:.3),l:0,L:R(.5,1.1),r:lw*R(.05,.11)});
  S.f=S.f.filter(function(f){f.l+=S.dt;f.x+=(f.vx+N(t*6,f.L*9)*30)*S.dt;f.y+=f.vy*S.dt;f.vy*=.985;var k=f.l/f.L;if(k>=1)return false;var r=f.r*(1-k*.6);dot(x,sprite('255,110,30',.55),f.x,f.y,r*1.7,(1-k));dot(x,sprite('255,210,110',.8),f.x,f.y,r,(1-k)*.9);return true});
  if(t<6&&Math.random()<.3+burst)S.sp.push({x:S.cx+R(-prx,prx),y:py-pry,vx:R(-60,60),vy:-R(80,260),l:0,L:R(.6,1.4)});
  S.sp=S.sp.filter(function(e){e.l+=S.dt;e.vy+=200*S.dt;e.x+=e.vx*S.dt;e.y+=e.vy*S.dt;var k=1-e.l/e.L;if(k<=0)return false;dot(x,sprite('255,200,120',1),e.x,e.y,3,k);return true});
  x.globalCompositeOperation='source-over';
  var la=E(P(t,1.9,3.1)),heat=1-P(t,3,5);logo(S,la,.94+.06*la,{g:S.tint('#FF8A3D'),gr:lw*.03,ga:la*(.4+.8*heat)});if(heat>0)logo(S,la*heat*.7,.94+.06*la,{src:S.tint('#FFC080')});
  fin(S,t,4.1,5.3)}},
// wokki / تقليب بالمقلاة
{k:'wok',d:7.2,init:function(S){S.pz=[];var C=['#3E9A3A','#D8402A','#F2A030','#F3EEE6','#7AC04A','#B02A6A'];for(var i=0;i<34;i++)S.pz.push({bx:R(-.38,.38),x:0,y:0,vx:0,vy:0,rot:R(0,6),vr:0,w:R(.05,.09),h:R(.018,.03),c:C[i%C.length],air:false});S.p=[];S.tossed=0},
 draw:function(S,t){var x=S.x,lw=S.lw,base=S.cy+S.lh*1.35,tosses=[.7,1.7,2.7],g2=lw*6,lift=0;bg(S,.3);
  tosses.forEach(function(t0,k){var q=P(t,t0,t0+.28);lift=Math.max(lift,Math.sin(Math.PI*q));if(t>=t0&&S.tossed<=k){S.tossed=k+1;S.pz.forEach(function(p){p.air=true;p.vy=-lw*R(2.4,3.1);p.vx=lw*R(-.25,.45);p.vr=R(-9,9)})}});
  var py=base-lift*lw*.07,tilt=-lift*.12;
  S.pz.forEach(function(p){var px0=S.cx+p.bx*lw*1.3;if(!p.on){p.on=1;p.x=px0;p.y=base-lw*.03}if(p.air){p.vy+=g2*S.dt;p.x+=p.vx*S.dt;p.y+=p.vy*S.dt;p.rot+=p.vr*S.dt;var floor=py-lw*.03+(p.x-S.cx)*tilt*.4;if(p.vy>0&&p.y>=floor){p.y=floor;p.air=false;p.vx=0;p.x=Math.max(S.cx-lw*.5,Math.min(S.cx+lw*.5,p.x))}}else{p.y=py-lw*.03+Math.sin(t*25+p.bx*20)*.6}});
  x.save();x.translate(S.cx,py);x.rotate(tilt);var g=x.createLinearGradient(0,-lw*.05,0,lw*.2);g.addColorStop(0,'#6A625A');g.addColorStop(.5,'#3A342E');g.addColorStop(1,'#1A1714');x.fillStyle=g;x.beginPath();x.moveTo(-lw*.66,-lw*.05);x.quadraticCurveTo(0,lw*.3,lw*.66,-lw*.05);x.lineTo(lw*.58,-lw*.05);x.quadraticCurveTo(0,lw*.18,-lw*.58,-lw*.05);x.closePath();x.fill();x.strokeStyle='rgba(230,200,170,.45)';x.lineWidth=1.5;x.beginPath();x.moveTo(-lw*.62,-lw*.045);x.quadraticCurveTo(0,lw*.05,lw*.62,-lw*.045);x.stroke();x.fillStyle='#2A2622';rr(x,lw*.6,-lw*.07,lw*.55,lw*.05,lw*.025);x.fill();x.restore();
  S.pz.forEach(function(p){x.save();x.translate(p.x,p.y);x.rotate(p.rot);x.fillStyle=p.c;rr(x,-p.w*lw/2,-p.h*lw/2,p.w*lw,p.h*lw,p.h*lw/2);x.fill();x.restore()});
  if(t>.6&&t<6.5&&Math.random()<.5)S.p.push({x:S.cx+R(-lw*.4,lw*.4),y:py-lw*.05,vy:-lw*R(.25,.4),r:lw*.06,l:0,L:R(1.4,2.2),ph:R(0,30),a:.7});S.p=steamP(S,S.p,sprite('236,224,210',.16));
  var la=E(P(t,3.3,4.4));logo(S,la,.92+.08*la,{dy:(1-la)*lw*.06});fin(S,t,4.4,5.4)}},
// pihvi pannulla / ستيك بالطاوة
{k:'steak',d:7.4,init:function(S){S.b=[];S.p=[];S.fz=[]},
 draw:function(S,t){var x=S.x,lw=S.lw,pa=1-P(t,3.2,4),pr=lw*.62*(1-.25*P(t,3.2,4)),cy=S.cy,fl=P(t,1.8,2.3),sc=Math.abs(Math.cos(Math.PI*fl)),seared=fl>.5;bg(S,.25);
  if(pa>0){panTop(x,S.cx,cy,pr,pa*E(P(t,0,.6)));x.globalAlpha=pa;
   x.save();x.translate(S.cx,cy);x.rotate(-.25);x.scale(1,Math.max(.05,sc));var sw=pr*.62,sh=pr*.4,g=x.createRadialGradient(-sw*.2,-sh*.2,sh*.1,0,0,sw);
   if(seared){g.addColorStop(0,'#8A4A22');g.addColorStop(1,'#3A1A0A')}else{g.addColorStop(0,'#C8505A');g.addColorStop(1,'#7A1E2A')}x.fillStyle=g;x.beginPath();x.ellipse(0,0,sw,sh,0,0,6.283);x.fill();
   x.fillStyle=seared?'#F3D9B0':'#F7E6E0';x.globalAlpha=pa*.8;x.beginPath();x.ellipse(sw*.55,-sh*.1,sw*.18,sh*.5,.3,0,6.283);x.fill();
   if(seared){x.strokeStyle='rgba(20,8,2,.75)';x.lineWidth=sh*.09;for(var i=-3;i<=3;i++){x.beginPath();x.moveTo(i*sw*.22-sw*.2,-sh*.9);x.lineTo(i*sw*.22+sw*.2,sh*.9);x.stroke()}}x.restore();x.globalAlpha=pa;
   if(t>2.5){var bm=E(P(t,2.5,3.1));x.fillStyle='rgba(247,214,120,'+(.8*(1-bm*.6))+')';x.save();x.translate(S.cx+pr*.45,cy+pr*.35);x.rotate(.4);var bs=lw*.09*(1-bm*.7);x.fillRect(-bs/2,-bs/2,bs,bs);x.restore();if(Math.random()<.9)S.fz.push({x:S.cx+R(-pr*.8,pr*.8),y:cy+R(-pr*.8,pr*.8),r:R(1,3),l:0,L:R(.3,.7)})}
   S.fz=S.fz.filter(function(f){f.l+=S.dt;var k=f.l/f.L;if(k>=1)return false;x.fillStyle='rgba(255,236,190,'+(1-k)*.8*pa+')';x.beginPath();x.arc(f.x,f.y,f.r*(1+k),0,6.283);x.fill();return true});
   if(t<3.6&&Math.random()<.9)S.b.push({x:S.cx+Math.cos(R(0,6.28))*pr*R(.45,.7),y:cy+Math.sin(R(0,6.28))*pr*R(.3,.55),r:R(1,2.5),l:0,L:R(.15,.4)});
   S.b=S.b.filter(function(b){b.l+=S.dt;var k=b.l/b.L;if(k>=1)return false;x.strokeStyle='rgba(255,230,180,'+(1-k)*pa+')';x.lineWidth=1;x.beginPath();x.arc(b.x,b.y,b.r*(1+k*2),0,6.283);x.stroke();return true});x.globalAlpha=1}
  if(t<5.5&&Math.random()<.6)S.p.push({x:S.cx+R(-pr*.5,pr*.5),y:cy,vy:-lw*R(.3,.45),r:lw*.07,l:0,L:R(1.4,2.4),ph:R(0,30),a:.8});S.p=steamP(S,S.p,sprite('190,180,170',.14));
  var la=E(P(t,3.5,4.5));logo(S,la,1,{g:S.tint('#E6A774'),gr:lw*.02,ga:la*.5});fin(S,t,4.6,5.6)}},
// ruskistettu voi / زبدة محمّصة
{k:'brownbutter',d:7.6,init:function(S){S.fo=[];var pp=pts2(S).slice(0,700);S.sp=pp.map(function(p){var an=R(0,6.283),rr2=Math.sqrt(Math.random())*S.lw*.5;return{sx:S.cx+Math.cos(an)*rr2,sy:S.cy+Math.sin(an)*rr2,tx:S.cx-S.lw/2+p[0]*S.lw,ty:S.cy-S.lh/2+p[1]*S.lh,d:Math.random()*.6,r:R(.8,1.8)*S.lw/200*1.4}})},
 draw:function(S,t){var x=S.x,lw=S.lw,pr=lw*.72,melt=E(P(t,.3,1.8)),brown=P(t,2.2,3.6),pa=1-.7*P(t,3.6,4.6);bg(S,.25);
  panTop(x,S.cx,S.cy,pr,E(P(t,0,.5)));
  var c1=[243,210,122],c2=[176,112,50],col=c1.map(function(v,i){return Math.round(v+(c2[i]-v)*brown)});
  x.globalAlpha=pa;var g=x.createRadialGradient(S.cx,S.cy,0,S.cx,S.cy,pr*.9*melt+1);g.addColorStop(0,'rgba('+col+',.95)');g.addColorStop(.85,'rgba('+col+',.85)');g.addColorStop(1,'rgba('+col+',0)');x.fillStyle=g;x.beginPath();x.arc(S.cx,S.cy,pr*.92*melt+1,0,6.283);x.fill();
  if(melt<1){var bs=lw*.32*(1-melt*.85);x.save();x.translate(S.cx,S.cy);x.rotate(.3+t*.2);var bg2=x.createLinearGradient(-bs/2,-bs/2,bs/2,bs/2);bg2.addColorStop(0,'#FFF0B0');bg2.addColorStop(1,'#E8C060');x.fillStyle=bg2;rr(x,-bs/2,-bs/2,bs,bs,bs*.12);x.fill();x.restore()}
  var foam=P(t,1.4,2.2)*(1-P(t,3.2,3.8));if(foam>0&&Math.random()<.95)for(var k=0;k<3;k++){var an=R(0,6.283),rr3=Math.sqrt(Math.random())*pr*.85;S.fo.push({x:S.cx+Math.cos(an)*rr3,y:S.cy+Math.sin(an)*rr3,r:R(1.5,4)*lw/220,l:0,L:R(.3,.8)})}
  S.fo=S.fo.filter(function(f){f.l+=S.dt;var k=f.l/f.L;if(k>=1)return false;x.strokeStyle='rgba(255,248,225,'+(1-k)*.85+')';x.lineWidth=1;x.beginPath();x.arc(f.x,f.y,f.r*(1+k),0,6.283);x.stroke();return true});x.globalAlpha=1;
  var gt=P(t,3.4,4.6),fade=1-P(t,4.7,5.3);if(brown>.3&&fade>0){x.fillStyle='#5A2E10';S.sp.forEach(function(p){var q=E(cl((gt-p.d*.4)/.6,0,1)),px=p.sx+(p.tx-p.sx)*q,py=p.sy+(p.ty-p.sy)*q;x.globalAlpha=fade*Math.min(1,(brown-.3)*2);x.fillRect(px,py,p.r,p.r)});x.globalAlpha=1}
  logo(S,E(P(t,4.6,5.3)),1,{});fin(S,t,5,5.9)}},
// öljytipat keitolle / تنقيط الزيت على الشوربة
{k:'oildrops',d:7.4,init:function(S){S.tagDy=S.lw*.4;S.dr=[];for(var i=0;i<10;i++){var an=-1.571+i/10*6.283;S.dr.push({x:S.cx+Math.cos(an)*S.lw*.48,y:S.cy+Math.sin(an)*S.lw*.48,t0:.7+i*.2,r:R(.035,.05)*S.lw})}},
 draw:function(S,t){var x=S.x,lw=S.lw,ba=E(P(t,0,.8));bg(S,.25);x.globalAlpha=ba;
  var rim=x.createRadialGradient(S.cx-lw*.2,S.cy-lw*.2,lw*.2,S.cx,S.cy,lw*.82);rim.addColorStop(0,'#FAF7F0');rim.addColorStop(1,'#C8C0B4');x.fillStyle=rim;x.beginPath();x.arc(S.cx,S.cy,lw*.8,0,6.283);x.fill();
  var sg=x.createRadialGradient(S.cx-lw*.15,S.cy-lw*.15,lw*.05,S.cx,S.cy,lw*.66);sg.addColorStop(0,'#F7B860');sg.addColorStop(1,'#C86A1E');x.fillStyle=sg;x.beginPath();x.arc(S.cx,S.cy,lw*.65,0,6.283);x.fill();
  x.strokeStyle='rgba(255,240,210,.35)';x.lineWidth=2;x.beginPath();x.arc(S.cx,S.cy,lw*.5+Math.sin(t*1.5)*2,3.6,4.6);x.stroke();x.globalAlpha=1;
  S.dr.forEach(function(d){var k=P(t,d.t0,d.t0+.5);if(k<=0)return;var fall=P(t,d.t0-.3,d.t0);if(k<.05&&fall<1){}var s=EB(k),rg=x.createRadialGradient(d.x-d.r*.3,d.y-d.r*.3,0,d.x,d.y,d.r*s);rg.addColorStop(0,'#B8F070');rg.addColorStop(.6,'#3E9A2A');rg.addColorStop(1,'#1E6A1E');x.fillStyle=rg;x.beginPath();x.ellipse(d.x,d.y,d.r*s,d.r*s*.9,0,0,6.283);x.fill();x.fillStyle='rgba(255,255,255,.7)';x.beginPath();x.arc(d.x-d.r*.35*s,d.y-d.r*.35*s,d.r*.18*s,0,6.283);x.fill();
   var rp=P(t,d.t0,d.t0+.6);if(rp>0&&rp<1){x.strokeStyle='rgba(255,240,210,'+(1-rp)*.7+')';x.lineWidth=1.2;x.beginPath();x.arc(d.x,d.y,d.r*(1+rp*2.2),0,6.283);x.stroke()}});
  var nk=P(t,2.9,3.4);if(nk>0){for(var i=0;i<14;i++){var an=i*2.4,rr4=lw*(.18+.04*(i%4)),s2=EB(P(t,2.9+i*.03,3.2+i*.03));x.fillStyle='#8A5A2A';x.beginPath();x.ellipse(S.cx+Math.cos(an)*rr4,S.cy+Math.sin(an)*rr4,lw*.018*s2,lw*.012*s2,an,0,6.283);x.fill()}}
  var la=E(P(t,3.3,4.3));logo(S,la*.5,.62,{src:S.tint('#3A1A08'),dx:2,dy:3});logo(S,la,.62,{});fin(S,t,4.4,5.4)}}
];
MORE.forEach(function(s){NEW.push(s)});
NEW=NEW.filter(function(s){return ['night','morning','latte','snow','bday'].indexOf(s.k)<0});

T.NEW=NEW;T.base=T.SC.length;NEW.forEach(function(s){T.SC.push(s)});
})();
