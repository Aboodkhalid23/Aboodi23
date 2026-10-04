// Screenshot a real article and find the sentence to highlight (articles.py → node article-shot.mjs job.json).
// job.json: {url, quote, out, width?, height?}. Prints one JSON line:
// {ok, title, site, date, found, rects: [[x, y, w, h] in screenshot pixels], width, height, rtl} or {error}.
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {execSync} from 'node:child_process';

const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch {
  pw = require(execSync('npm root -g').toString().trim() + '/playwright');
}
const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const W = job.width ?? 1600, H = job.height ?? 1000;
// Full Chromium (not the headless shell): it trusts the session's certificate store (NSS), and goes
// through the session proxy like every other tool here.
const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
// Trust exactly the session's own CA (the same certificate every other tool here is pointed at):
// Chromium takes it as a public-key pin. Verification stays on for everything else.
const args = [];
const CA = '/root/.ccr/agent-proxy-ca.crt';
if (fs.existsSync(CA)) {
  const {X509Certificate, createHash} = await import('node:crypto');
  const spki = new X509Certificate(fs.readFileSync(CA)).publicKey.export({type: 'spki', format: 'der'});
  args.push(`--ignore-certificate-errors-spki-list=${createHash('sha256').update(spki).digest('base64')}`);
}
const browser = await pw.chromium.launch({channel: 'chromium', executablePath: process.env.EDITOR_CHROME || undefined,
  proxy: proxy ? {server: proxy} : undefined, args});
try {
  const page = await browser.newPage({viewport: {width: W, height: H}, deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36',
    locale: 'en-US'});
  await page.goto(job.url, {waitUntil: 'domcontentloaded', timeout: 45000});
  await page.waitForTimeout(2500);
  // cookie / consent walls: press the accept button if there is one
  for (const name of [/accept all/i, /accept/i, /agree/i, /allow all/i, /got it/i, /^ok$/i, /موافق/, /قبول/]) {
    const b = page.getByRole('button', {name}).first();
    if (await b.isVisible().catch(() => false)) { await b.click({timeout: 2000}).catch(() => {}); await page.waitForTimeout(800); break; }
  }
  const info = await page.evaluate((quote) => {
    // drop floating bars, pop-ups and ads that would cover the text
    for (const el of Array.from(document.querySelectorAll('body *'))) {
      const s = getComputedStyle(el);
      if ((s.position === 'fixed' || s.position === 'sticky') && el.tagName !== 'BODY') el.remove();
    }
    const norm = (t) => t.replace(/\s+/g, ' ').trim().toLowerCase();
    const want = norm(quote || '').slice(0, 80);
    let rects = [], found = false, rtl = false;
    if (want) {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
      let best = null;
      while (walker.nextNode()) {
        const el = walker.currentNode;
        if (!['P', 'H1', 'H2', 'H3', 'LI', 'BLOCKQUOTE', 'SPAN', 'DIV'].includes(el.tagName)) continue;
        const text = norm(el.textContent || '');
        if (text.includes(want) && (!best || text.length < norm(best.textContent).length)) best = el;
      }
      if (best) {
        found = true;
        rtl = getComputedStyle(best).direction === 'rtl';
        best.scrollIntoView({block: 'center'});
        // exact rectangles of the quote's lines
        const full = best.textContent;
        const idx = norm(full).indexOf(want);
        const range = document.createRange();
        const nodes = []; const tw = document.createTreeWalker(best, NodeFilter.SHOW_TEXT);
        while (tw.nextNode()) nodes.push(tw.currentNode);
        // map normalised offset back to raw text nodes (approximate: normalise node by node)
        let pos = 0, start = null, end = null; const target = [idx, idx + norm(quote).length];
        for (const n of nodes) {
          const t = n.textContent.replace(/\s+/g, ' ');
          if (start === null && pos + t.length > target[0]) start = [n, Math.max(0, target[0] - pos)];
          if (start !== null && pos + t.length >= target[1]) { end = [n, Math.min(t.length, target[1] - pos)]; break; }
          pos += t.length;
        }
        if (start && end) {
          try { range.setStart(start[0], start[1]); range.setEnd(end[0], end[1]); } catch { range.selectNodeContents(best); }
        } else range.selectNodeContents(best);
        rects = Array.from(range.getClientRects()).filter((r) => r.width > 4).map((r) => [r.x, r.y, r.width, r.height]);
      }
    } else window.scrollTo(0, 0);
    const meta = (p) => document.querySelector(`meta[property="${p}"],meta[name="${p}"]`)?.getAttribute('content') || '';
    return {title: meta('og:title') || document.title, site: meta('og:site_name') || location.hostname,
      date: meta('article:published_time') || meta('date') || '', found, rects, rtl};
  }, job.quote);
  await page.waitForTimeout(600);
  await page.screenshot({path: job.out});
  const k = 2;   // deviceScaleFactor: rects are CSS pixels, the screenshot is twice as big
  console.log(JSON.stringify({ok: true, ...info, rects: info.rects.map((r) => r.map((v) => v * k)), width: W * k, height: H * k}));
} catch (e) {
  console.log(JSON.stringify({error: String(e).slice(0, 400)}));
} finally {
  await browser.close();
}
