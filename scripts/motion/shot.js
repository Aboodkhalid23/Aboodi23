// يصوّر صفحة المحرك: إما صورة معاينة (لقطات مجمّعة) أو فيديو كامل (الإطارات تروح مباشرة لـ ffmpeg)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
(async () => {
  const [html, mode, out, a1, a2, a3] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  p.on('pageerror', e => { console.error('خطأ بالصفحة:', e.message); process.exit(2); });
  await p.goto('file://' + html);
  await p.evaluate(async () => { await document.fonts.ready; await new Promise(r => { const i = new Image(); i.onload = r; i.onerror = r; i.src = window.D.icon; }); });
  await p.waitForTimeout(150);
  const grab = async t => Buffer.from((await p.evaluate(t => { window.R(t); return document.getElementById('c').toDataURL('image/jpeg', .9); }, t)).split(',')[1], 'base64');
  if (mode === 'preview') {
    const ts = JSON.parse(a1), dir = out.replace(/\.png$/, '');
    const fs = require('fs'); fs.mkdirSync(dir, { recursive: true });
    const files = [];
    for (let i = 0; i < ts.length; i++) { const f = `${dir}/${i}.jpg`; fs.writeFileSync(f, await grab(ts[i])); files.push(f); }
    await b.close();
    const args = ['-v', 'error', '-y']; files.forEach(f => args.push('-i', f));
    args.push('-filter_complex', files.map((_, i) => `[${i}]scale=240:-1[s${i}]`).join(';') + ';' + files.map((_, i) => `[s${i}]`).join('') + `hstack=${files.length}`, out);
    spawn('ffmpeg', args, { stdio: 'inherit' }).on('exit', c => process.exit(c));
    return;
  }
  const fps = +a1, total = +a2, audio = a3, N = Math.ceil(total * fps);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-i', audio,
    '-vf', 'scale=540:960:flags=lanczos', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-crf', '29', '-tune', 'animation', '-c:a', 'copy', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) { const buf = await grab(i / fps); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); }
  ff.stdin.end(); await b.close();
  ff.on('exit', c => process.exit(c));
})();
