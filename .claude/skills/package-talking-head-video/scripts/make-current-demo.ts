import {spawnSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

// A geometric stand-in, not a real person or a factual demonstration.
const out = resolve('.tmp/current-demo-source');
mkdirSync(out, {recursive: true});
const result = spawnSync('ffmpeg', [
  '-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0xE6E8ED:s=1920x1080:r=30:d=8',
  '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=8',
  '-vf', 'drawgrid=w=120:h=120:t=1:c=0xD8DCE5,drawbox=x=810:y=160:w=300:h=290:c=0xA4AEBD:t=fill,drawbox=x=710:y=480:w=500:h=390:c=0xA4AEBD:t=fill',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', resolve(out, 'input.mp4'),
], {stdio: 'inherit', shell: false, windowsHide: true});
if (result.status !== 0) throw new Error('Failed to generate the geometric demo source');
