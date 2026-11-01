package com.aboodi.tvhome;

import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;

/**
 * صوت خفيف وناعم للتنقل والضغط، نصنعه بالكود (موجة ناعمة تخفت بسرعة) بدون أي ملف صوت.
 * التنقل: "تِك" زجاجية صغيرة. الضغط: نغمتين ناعمات.
 */
final class Sound {
    private static final int RATE = 44100;
    private static AudioTrack move, press;

    private Sound() {}

    static void init() {
        if (move != null) return;
        move = track(tone(new float[]{1568f, 3136f}, new float[]{1f, 0.18f}, 0.045f, 90f, 0.22f));
        press = track(concat(tone(new float[]{1175f, 2350f}, new float[]{1f, 0.2f}, 0.07f, 45f, 0.26f),
                tone(new float[]{1760f, 3520f}, new float[]{1f, 0.2f}, 0.11f, 30f, 0.24f)));
    }

    static void move() { play(move); }

    static void press() { play(press); }

    private static void play(AudioTrack t) {
        if (t == null) return;
        try {
            t.stop();
            t.reloadStaticData();
            t.play();
        } catch (Exception ignored) { }
    }

    /** نغمة: جيوب (sin) بترددات وأوزان، تبدأ ناعمة (بدون طگة) وتخفت بسرعة. */
    private static short[] tone(float[] hz, float[] amp, float secs, float decay, float vol) {
        int n = Math.round(RATE * secs);
        short[] out = new short[n];
        int attack = RATE / 400; // 2.5 ملي ثانية
        for (int i = 0; i < n; i++) {
            double t = (double) i / RATE, v = 0;
            for (int k = 0; k < hz.length; k++) v += amp[k] * Math.sin(2 * Math.PI * hz[k] * t);
            double env = Math.exp(-decay * t) * Math.min(1.0, (double) i / attack);
            env *= Math.min(1.0, (n - i) / (double) attack); // نهاية ناعمة
            out[i] = (short) Math.round(v * env * vol * 32767 / 1.2);
        }
        return out;
    }

    private static short[] concat(short[] a, short[] b) {
        short[] o = new short[a.length + b.length];
        System.arraycopy(a, 0, o, 0, a.length);
        System.arraycopy(b, 0, o, a.length, b.length);
        return o;
    }

    private static AudioTrack track(short[] pcm) {
        try {
            AudioTrack t = new AudioTrack(
                    new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(),
                    new AudioFormat.Builder().setSampleRate(RATE).setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                            .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build(),
                    pcm.length * 2, AudioTrack.MODE_STATIC, 0);
            t.write(pcm, 0, pcm.length);
            return t;
        } catch (Exception e) {
            return null;
        }
    }
}
