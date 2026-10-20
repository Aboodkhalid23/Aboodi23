package com.aboodi.tvhome;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.widget.FrameLayout;

import java.util.ArrayList;
import java.util.List;

/**
 * زجاج مثل آبل: كل لوح زجاجي يرسم نسخة مضببة من الخلفية الي وراه بالضبط،
 * وفوگها لمعة خفيفة وحافة بيضة. نضبب صورة صغيرة (160 بكسل) مرة وحدة لكل خلفية، فما يثقل.
 */
final class Glass {
    private Glass() {}

    /** الخلفية المضببة المشتركة بين كل ألواح الزجاج. */
    static final class Backdrop {
        private static Bitmap cur, prev;
        private static int fullW = 1, fullH = 1; // أبعاد الصورة الأصلية
        private static float mix = 1f;
        static boolean dark;
        private static final List<GlassFrame> views = new ArrayList<>();
        private static ValueAnimator anim;

        static void set(Bitmap full) {
            prev = cur;
            fullW = full.getWidth();
            fullH = full.getHeight();
            cur = blur(full);
            if (anim != null) anim.cancel();
            anim = ValueAnimator.ofFloat(0f, 1f).setDuration(1400);
            anim.addUpdateListener(a -> { mix = (float) a.getAnimatedValue(); invalidateAll(); });
            anim.start();
        }

        static void invalidateAll() {
            for (GlassFrame v : views) v.invalidate();
        }

        /** نصغر الصورة لـ 160 عرض ونضببها بثلاث مرات تمويه سريع. */
        private static Bitmap blur(Bitmap src) {
            int w = 160, h = Math.max(1, Math.round(160f * src.getHeight() / src.getWidth()));
            Bitmap s = Bitmap.createScaledBitmap(src, w, h, true).copy(Bitmap.Config.ARGB_8888, true);
            int[] px = new int[w * h];
            s.getPixels(px, 0, w, 0, 0, w, h);
            for (int i = 0; i < 3; i++) boxBlur(px, w, h, 4);
            s.setPixels(px, 0, w, 0, 0, w, h);
            return s;
        }

        private static void boxBlur(int[] p, int w, int h, int r) {
            int[] t = new int[p.length];
            pass(p, t, w, h, r, true);
            pass(t, p, w, h, r, false);
        }

        private static void pass(int[] in, int[] out, int w, int h, int r, boolean horiz) {
            int len = horiz ? w : h, lines = horiz ? h : w;
            for (int l = 0; l < lines; l++) {
                int sr = 0, sg = 0, sb = 0;
                for (int k = -r; k <= r; k++) {
                    int c = in[idx(l, clamp(k, len), horiz, w)];
                    sr += (c >> 16) & 255; sg += (c >> 8) & 255; sb += c & 255;
                }
                int n = 2 * r + 1;
                for (int i = 0; i < len; i++) {
                    out[idx(l, i, horiz, w)] = 0xFF000000 | ((sr / n) << 16) | ((sg / n) << 8) | (sb / n);
                    int a = in[idx(l, clamp(i - r, len), horiz, w)], b = in[idx(l, clamp(i + r + 1, len), horiz, w)];
                    sr += ((b >> 16) & 255) - ((a >> 16) & 255);
                    sg += ((b >> 8) & 255) - ((a >> 8) & 255);
                    sb += (b & 255) - (a & 255);
                }
            }
        }

        private static int idx(int line, int i, boolean horiz, int w) { return horiz ? line * w + i : i * w + line; }

        private static int clamp(int i, int len) { return i < 0 ? 0 : i >= len ? len - 1 : i; }
    }

    /** لوح زجاجي: تحط بيه أي شي، وهو يرسم الزجاج وراه. */
    static final class GlassFrame extends FrameLayout {
        private final Paint img = new Paint(Paint.FILTER_BITMAP_FLAG);
        private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint edge = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path clip = new Path();
        private final RectF box = new RectF();
        private final Matrix m = new Matrix();
        private final int[] loc = new int[2], rootLoc = new int[2];
        private final float radius;
        private static final ColorMatrixColorFilter LIGHT = filter(false), DARK = filter(true);
        float glow; // 0 = عادي، 1 = متأشر عليه (أفتح وألمع)

        GlassFrame(Context c, float radius) {
            super(c);
            this.radius = radius;
            setWillNotDraw(false);
            edge.setStyle(Paint.Style.STROKE);
        }

        @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); Backdrop.views.add(this); }

        @Override protected void onDetachedFromWindow() { Backdrop.views.remove(this); super.onDetachedFromWindow(); }

        void setGlow(float g) { glow = g; invalidate(); }

        @Override
        protected void onDraw(Canvas c) {
            int w = getWidth(), h = getHeight();
            box.set(0, 0, w, h);
            clip.reset();
            clip.addRoundRect(box, radius, radius, Path.Direction.CW);
            c.save();
            c.clipPath(clip);

            // 1) الخلفية المضببة بنفس مكانها على الشاشة
            getLocationOnScreen(loc);
            getRootView().getLocationOnScreen(rootLoc);
            int sw = getRootView().getWidth(), sh = getRootView().getHeight();
            boolean dark = Backdrop.dark;
            img.setColorFilter(dark ? DARK : LIGHT);
            if (Backdrop.prev != null && Backdrop.mix < 1f) drawBackdrop(c, Backdrop.prev, sw, sh, 255);
            if (Backdrop.cur != null) drawBackdrop(c, Backdrop.cur, sw, sh, Math.round(255 * (Backdrop.prev == null ? 1f : Backdrop.mix)));

            // 2) لون الزجاج ولمعته
            int a1 = dark ? 0x8C : 0x42, a2 = dark ? 0x73 : 0x14;
            int base = dark ? 0x141420 : 0xFFFFFF;
            float g = glow;
            if (!dark) { a1 += Math.round(g * 0x50); a2 += Math.round(g * 0x30); }
            else { base = blend(0x141420, 0x5A5A68, g); }
            fill.setShader(new LinearGradient(0, 0, w * 0.35f, h, (a1 << 24) | base, (a2 << 24) | base, Shader.TileMode.CLAMP));
            c.drawRect(box, fill);
            c.restore();

            // 3) حافة مضيئة: أقوى فوگ، أخف جوه
            float sw2 = Math.max(1.5f, h / 80f) + g * 2.5f;
            edge.setStrokeWidth(sw2);
            int top = dark ? 0x40 : 0x9C, bot = dark ? 0x18 : 0x30;
            top += Math.round(g * (255 - top));
            edge.setShader(new LinearGradient(0, 0, 0, h, Color.argb(top, 255, 255, 255), Color.argb(bot + Math.round(g * 90), 255, 255, 255), Shader.TileMode.CLAMP));
            float i = sw2 / 2;
            box.set(i, i, w - i, h - i);
            c.drawRoundRect(box, radius - i, radius - i, edge);
        }

        private void drawBackdrop(Canvas c, Bitmap b, int sw, int sh, int alpha) {
            // نفس حسابات CENTER_CROP للخلفية الحقيقية
            float s = Math.max((float) sw / Backdrop.fullW, (float) sh / Backdrop.fullH);
            float dx = (sw - Backdrop.fullW * s) / 2f, dy = (sh - Backdrop.fullH * s) / 2f;
            float k = s * Backdrop.fullW / b.getWidth();
            m.reset();
            m.postScale(k, k);
            m.postTranslate(dx - (loc[0] - rootLoc[0]), dy - (loc[1] - rootLoc[1]));
            // تكبير البطاقة المتأشر عليها: نرجعه حتى الضباب يبقى بمكانه
            float sx = getScaleX(), sy = getScaleY();
            if (sx != 1f || sy != 1f) m.postScale(1f / sx, 1f / sy);
            img.setAlpha(alpha);
            c.drawBitmap(b, m, img);
        }

        /** نزيد التشبع شوية (مثل زجاج آبل)، وبالداكن نغمّق. */
        private static ColorMatrixColorFilter filter(boolean dark) {
            ColorMatrix cm = new ColorMatrix();
            cm.setSaturation(1.5f);
            if (dark) cm.postConcat(scale(0.55f));
            return new ColorMatrixColorFilter(cm);
        }

        private static ColorMatrix scale(float k) {
            ColorMatrix cm = new ColorMatrix();
            cm.setScale(k, k, k, 1f);
            return cm;
        }

        private static int blend(int a, int b, float t) {
            int r = Math.round(((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
            int g = Math.round(((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
            int bl = Math.round((a & 255) * (1 - t) + (b & 255) * t);
            return (r << 16) | (g << 8) | bl;
        }
    }
}
