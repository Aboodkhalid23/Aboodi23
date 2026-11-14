import re,base64,sys
import os
A=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(A))
s=open(A+'/src.html').read()
s=re.sub(r'<script>\n.*</script>', lambda m:'<script>\n'+open(A+'/data.js').read()+'\n'+open(A+'/dish.js').read()+'\n'+open(A+'/app.js').read()+'</script>', s, count=1, flags=re.S)
s=s.replace('SPLASH_JS',open(A+'/splash.js').read()+'\n'+open(A+'/splash-extra.js').read())
d='data:image/png;base64,'+base64.b64encode(open(A+'/logo-sm.png','rb').read()).decode()
a=s.replace('LOGO_DATA',d)
open('/tmp/tinta-check.js','w').write(re.search(r'<script>\n(.*?)</script>',a,re.S).group(1))
# pages version
head='''<!doctype html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Tintå">
<meta name="theme-color" content="#0E0D0C">
<meta name="robots" content="noindex">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<script src="config.js"></script>
<script>window.TINTA_VER='__VER__';</script>
'''
p=a
for x in ['<meta name="claude:viewport-fit-sides" content="cover">\n','<meta name="apple-mobile-web-app-capable" content="yes">\n','<meta name="apple-mobile-web-app-title" content="Tintå">\n','<meta name="theme-color" content="#0E0D0C">\n']:
    p=p.replace(x,'',1)
i=p.index('<div class="wrap">')
p=head+p[:i]+'</head>\n<body>\n'+p[i:]+"\n<script>if('serviceWorker' in navigator){var _r=!!navigator.serviceWorker.controller;navigator.serviceWorker.register('sw.js',{updateViaCache:'none'}).then(function(g){g.update();}).catch(function(){});}</script>\n</body>\n</html>\n"
open(ROOT+'/links/tinta/index.html','w').write(p)

import time
ver=str(int(time.time()))
p=open(ROOT+'/links/tinta/index.html').read().replace('__VER__',ver)
open(ROOT+'/links/tinta/index.html','w').write(p)
open(ROOT+'/links/tinta/version.txt','w').write(ver+'\n')
