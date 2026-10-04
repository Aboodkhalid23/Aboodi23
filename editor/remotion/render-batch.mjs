// Render many compositions with ONE browser (graphics.py → render_batch). Starting node + Chromium
// for every beat cost ~5 s each; a 20-minute episode has hundreds of graphics.
//   node render-batch.mjs jobs.json
// jobs.json: {serveUrl, browserExecutable, concurrency, items: [{comp, props, out, scale, still}]}
// Prints one JSON line per item: {"ok": out} or {"error": out, "message": "..."}.
import fs from 'node:fs';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const {serveUrl, browserExecutable, concurrency = 4} = job;
const browser = await openBrowser('chrome', {browserExecutable});
let failed = 0;
for (const it of job.items) {
  const common = {serveUrl, inputProps: it.props, puppeteerInstance: browser, browserExecutable, logLevel: 'error',
    timeoutInMilliseconds: 120000};
  for (let attempt = 0; attempt < 2; attempt++) {   // a busy machine can miss a frame deadline once
    try {
      const composition = await selectComposition({...common, id: it.comp});
      if (it.still) {
        await renderStill({...common, composition, output: it.out, scale: it.scale ?? 1, overwrite: true});
      } else {
        await renderMedia({...common, composition, codec: 'h264', crf: 10, outputLocation: it.out, muted: true,
          concurrency, scale: it.scale ?? 1, overwrite: true});
      }
      console.log(JSON.stringify({ok: it.out}));
      break;
    } catch (e) {
      if (attempt === 1) {
        failed++;
        console.log(JSON.stringify({error: it.out, message: String(e?.stack ?? e).slice(0, 800)}));
      }
    }
  }
}
await browser.close({silent: true});
process.exit(failed ? 2 : 0);
