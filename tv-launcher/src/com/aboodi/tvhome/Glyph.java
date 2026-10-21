package com.aboodi.tvhome;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.View;

/** أيقونات خاصة مرسومة بالكود (خطوط حديثة رفيعة)، ونفس الشي لشعارات التطبيقات المفضلة. */
final class Glyph extends View {
    static final int WIFI = 1, LANG = 2, MOON = 3, SUN = 4, GEAR = 5, GRID = 6, NETFLIX = 7, YOUTUBE = 8,
            DAR = 9, SPOTIFY = 10, UPDATE = 11, BALL = 12, CLEAN = 13, POWER = 14, CLOUD = 15, RAIN = 16, SNOW = 17, TROPHY = 18;

    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final RectF r = new RectF();
    int kind;
    int color = 0xFFFFFFFF;
    int level = 4; // قوة الوايفاي 0..4، و -1 = مقطوع

    Glyph(Context c, int kind) {
        super(c);
        this.kind = kind;
    }

    static int forPackage(String pkg) {
        if (pkg.startsWith("com.netflix")) return NETFLIX;
        if (pkg.startsWith("com.google.android.youtube")) return YOUTUBE;
        if (pkg.startsWith("com.mbm_soft")) return DAR;
        if (pkg.startsWith("com.spotify")) return SPOTIFY;
        return 0;
    }

    void set(int k) { kind = k; invalidate(); }

    void tint(int c) { color = c; invalidate(); }

    @Override
    protected void onDraw(Canvas c) {
        float s = Math.min(getWidth(), getHeight()) / 24f; // نرسم على شبكة 24×24
        c.save();
        c.translate((getWidth() - 24 * s) / 2f, (getHeight() - 24 * s) / 2f);
        c.scale(s, s);
        p.reset();
        p.setAntiAlias(true);
        p.setColor(color);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.8f);
        p.setStrokeCap(Paint.Cap.ROUND);
        p.setStrokeJoin(Paint.Join.ROUND);
        switch (kind) {
            case WIFI: wifi(c); break;
            case LANG: lang(c); break;
            case MOON:
                // هلال: دائرة ناقص دائرة
                path.reset();
                path.addCircle(11.5f, 12.5f, 8.5f, Path.Direction.CW);
                Path bite = new Path();
                bite.addCircle(16.5f, 8f, 7f, Path.Direction.CW);
                path.op(bite, Path.Op.DIFFERENCE);
                c.drawPath(path, p);
                break;
            case SUN:
                c.drawCircle(12, 12, 4.2f, p);
                for (int i = 0; i < 8; i++) {
                    double a = Math.PI / 4 * i;
                    c.drawLine(12 + (float) Math.cos(a) * 7.2f, 12 + (float) Math.sin(a) * 7.2f,
                            12 + (float) Math.cos(a) * 9.4f, 12 + (float) Math.sin(a) * 9.4f, p);
                }
                break;
            case GEAR: gear(c); break;
            case GRID:
                p.setStyle(Paint.Style.FILL);
                for (int y = 0; y < 3; y++) for (int x = 0; x < 3; x++) {
                    r.set(4 + x * 6, 4 + y * 6, 8.4f + x * 6, 8.4f + y * 6);
                    c.drawRoundRect(r, 1.4f, 1.4f, p);
                }
                break;
            case UPDATE:
                c.drawLine(12, 4, 12, 15, p);
                path.reset(); path.moveTo(7.5f, 10.5f); path.lineTo(12, 15); path.lineTo(16.5f, 10.5f);
                c.drawPath(path, p);
                c.drawLine(5, 19.5f, 19, 19.5f, p);
                break;
            case BALL: ball(c); break;
            case CLOUD: cloud(c, 0); break;
            case TROPHY:
                // كأس: الجام والمقابض والقاعدة
                path.reset();
                path.moveTo(7, 4); path.lineTo(17, 4); path.lineTo(17, 9);
                path.quadTo(17, 14.5f, 12, 14.5f); path.quadTo(7, 14.5f, 7, 9); path.close();
                c.drawPath(path, p);
                path.reset(); path.moveTo(7, 6); path.quadTo(3, 6, 3.6f, 9); path.quadTo(4.4f, 11.5f, 7.6f, 11.6f); c.drawPath(path, p);
                path.reset(); path.moveTo(17, 6); path.quadTo(21, 6, 20.4f, 9); path.quadTo(19.6f, 11.5f, 16.4f, 11.6f); c.drawPath(path, p);
                c.drawLine(12, 14.5f, 12, 18, p);
                r.set(8, 18, 16, 20.5f);
                c.drawRoundRect(r, 1, 1, p);
                break;
            case RAIN:
                cloud(c, -3);
                for (int i = 0; i < 3; i++) c.drawLine(8.5f + i * 3.5f, 16.5f, 7.3f + i * 3.5f, 20.5f, p);
                break;
            case SNOW:
                cloud(c, -3);
                p.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 3; i++) c.drawCircle(8.5f + i * 3.5f, 18.5f + (i % 2) * 1.6f, 1.1f, p);
                p.setStyle(Paint.Style.STROKE);
                break;
            case CLEAN:
                // نجمة لمعة كبيرة وصغيرة: "نظيف"
                sparkle(c, 10f, 13f, 7.5f);
                sparkle(c, 18.5f, 5.5f, 3.2f);
                break;
            case POWER:
                r.set(5, 5.5f, 19, 19.5f);
                c.drawArc(r, -60, 300, false, p);
                c.drawLine(12, 3.5f, 12, 11.5f, p);
                break;
            case NETFLIX:
                p.setStyle(Paint.Style.FILL);
                p.setColor(0xFFE50914);
                p.setShadowLayer(1.2f, 0, 0.6f, 0x66000000);
                // حرف N بثلاث شرائط مثل الشعار
                path.reset();
                path.moveTo(6.5f, 3); path.lineTo(10, 3); path.lineTo(10, 21); path.lineTo(6.5f, 21.6f); path.close();
                path.moveTo(14, 3); path.lineTo(17.5f, 3); path.lineTo(17.5f, 21.6f); path.lineTo(14, 21); path.close();
                c.drawPath(path, p);
                p.setColor(0xFFB1060F);
                path.reset();
                path.moveTo(6.5f, 3); path.lineTo(10, 3); path.lineTo(17.5f, 21.6f); path.lineTo(14, 21); path.close();
                c.drawPath(path, p);
                break;
            case YOUTUBE:
                p.setStyle(Paint.Style.FILL);
                p.setColor(0xFFFF0033);
                p.setShadowLayer(1.2f, 0, 0.6f, 0x66000000);
                r.set(1.5f, 5, 22.5f, 19);
                c.drawRoundRect(r, 4.5f, 4.5f, p);
                p.clearShadowLayer();
                p.setColor(0xFFFFFFFF);
                path.reset(); path.moveTo(10, 8.8f); path.lineTo(15.6f, 12); path.lineTo(10, 15.2f); path.close();
                c.drawPath(path, p);
                break;
            case DAR:
                p.setStyle(Paint.Style.FILL);
                p.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
                p.setTextSize(9.5f);
                p.setTextAlign(Paint.Align.CENTER);
                p.setLetterSpacing(0.06f);
                p.setShadowLayer(3f, 0, 0, 0xE63C8CFF);
                c.drawText("DAR", 12, 15.4f, p);
                break;
            case SPOTIFY:
                p.setStyle(Paint.Style.FILL);
                p.setColor(0xFF1ED760);
                p.setShadowLayer(1.2f, 0, 0.6f, 0x66000000);
                c.drawCircle(12, 12, 10.5f, p);
                p.clearShadowLayer();
                p.setStyle(Paint.Style.STROKE);
                p.setColor(0xFF000000);
                p.setStrokeWidth(1.9f);
                arc(c, 6f, 9.4f, 18.6f, 10.6f, 2.6f);
                p.setStrokeWidth(1.6f);
                arc(c, 6.8f, 12.8f, 17.6f, 13.8f, 2.1f);
                p.setStrokeWidth(1.35f);
                arc(c, 7.6f, 16f, 16.4f, 16.8f, 1.6f);
                break;
        }
        c.restore();
    }

    private void arc(Canvas c, float x1, float y1, float x2, float y2, float bend) {
        path.reset();
        path.moveTo(x1, y1);
        path.quadTo((x1 + x2) / 2, y1 - bend, x2, y2);
        c.drawPath(path, p);
    }

    private void wifi(Canvas c) {
        float[] rad = {3.2f, 7.4f, 11.6f};
        int on = level < 0 ? 0 : level;
        for (int i = 0; i < 3; i++) {
            p.setAlpha(i < on - 1 || on == 4 ? 255 : 80);
            r.set(12 - rad[i], 19.6f - rad[i], 12 + rad[i], 19.6f + rad[i]);
            c.drawArc(r, -135, 90, false, p);
        }
        p.setAlpha(on > 0 ? 255 : 80);
        p.setStyle(Paint.Style.FILL);
        c.drawCircle(12, 19.6f, 1.5f, p);
        if (level < 0) {
            p.setStyle(Paint.Style.STROKE);
            p.setAlpha(255);
            c.drawLine(4, 4, 20, 20, p);
        }
    }

    /** غيمة ناعمة: ثلاث دواير ومستطيل مدموجين، نرسم حافتها بس. */
    private void cloud(Canvas c, float dy) {
        path.reset();
        path.addCircle(8.5f, 14f + dy, 4f, Path.Direction.CW);
        Path q = new Path();
        q.addCircle(13f, 11f + dy, 5.5f, Path.Direction.CW);
        path.op(q, Path.Op.UNION);
        q.reset();
        q.addCircle(17.5f, 14.5f + dy, 3.5f, Path.Direction.CW);
        path.op(q, Path.Op.UNION);
        q.reset();
        r.set(8.5f, 13f + dy, 17.5f, 18f + dy);
        q.addRect(r, Path.Direction.CW);
        path.op(q, Path.Op.UNION);
        c.drawPath(path, p);
    }

    private void sparkle(Canvas c, float x, float y, float s) {
        float k = s * 0.22f;
        path.reset();
        path.moveTo(x, y - s);
        path.quadTo(x + k, y - k, x + s, y);
        path.quadTo(x + k, y + k, x, y + s);
        path.quadTo(x - k, y + k, x - s, y);
        path.quadTo(x - k, y - k, x, y - s);
        path.close();
        c.drawPath(path, p);
    }

    /** كرة قدم: دائرة وبنصها خماسي مليان، وخطوط منه للحافة. */
    private void ball(Canvas c) {
        c.drawCircle(12, 12, 9.6f, p);
        path.reset();
        float[] xs = new float[5], ys = new float[5];
        for (int i = 0; i < 5; i++) {
            double a = -Math.PI / 2 + i * 2 * Math.PI / 5;
            xs[i] = 12 + (float) Math.cos(a) * 3.6f;
            ys[i] = 12 + (float) Math.sin(a) * 3.6f;
            if (i == 0) path.moveTo(xs[i], ys[i]); else path.lineTo(xs[i], ys[i]);
            c.drawLine(xs[i], ys[i], 12 + (float) Math.cos(a) * 9.6f, 12 + (float) Math.sin(a) * 9.6f, p);
        }
        path.close();
        p.setStyle(Paint.Style.FILL);
        c.drawPath(path, p);
        p.setStyle(Paint.Style.STROKE);
    }

    private void lang(Canvas c) {
        c.drawLine(3.5f, 5.5f, 12.5f, 5.5f, p);
        c.drawLine(8, 3, 8, 5.5f, p);
        path.reset(); path.moveTo(5.6f, 5.5f); path.quadTo(7, 11, 12, 13.5f); c.drawPath(path, p);
        path.reset(); path.moveTo(10.6f, 5.5f); path.quadTo(9, 11.5f, 4, 14); c.drawPath(path, p);
        path.reset(); path.moveTo(13, 21); path.lineTo(17, 11); path.lineTo(21, 21); c.drawPath(path, p);
        c.drawLine(14.6f, 17.4f, 19.4f, 17.4f, p);
    }

    private void gear(Canvas c) {
        c.drawCircle(12, 12, 3.2f, p);
        path.reset();
        int teeth = 8;
        for (int i = 0; i < teeth * 2; i++) {
            double a = Math.PI * i / teeth - Math.PI / 2;
            double a2 = Math.PI * (i + 1) / teeth - Math.PI / 2;
            float ro = (i % 2 == 0) ? 9.3f : 7.2f;
            float x1 = 12 + (float) Math.cos(a) * ro, y1 = 12 + (float) Math.sin(a) * ro;
            float x2 = 12 + (float) Math.cos(a2) * ro, y2 = 12 + (float) Math.sin(a2) * ro;
            if (i == 0) path.moveTo(x1, y1); else path.lineTo(x1, y1);
            path.lineTo(x2, y2);
        }
        path.close();
        c.drawPath(path, p);
    }
}
