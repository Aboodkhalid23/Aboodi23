package com.aboodi.tvhome;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.Drawable;

import java.text.Collator;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;

/** يجيب التطبيقات المنصبة ويرتبها: الأكثر استخداماً أول. يشتغل بخيط جانبي حتى الشاشة ما تعلگ. */
final class AppLoader {
    private static final String[] CATEGORIES = {
            Intent.CATEGORY_LEANBACK_LAUNCHER, // تطبيقات التلفزيون أول، لأن عدها بانر
            Intent.CATEGORY_LAUNCHER
    };

    private AppLoader() {}

    static List<AppEntry> load(Context ctx) {
        PackageManager pm = ctx.getPackageManager();
        LinkedHashMap<String, AppEntry> byPkg = new LinkedHashMap<>();
        for (String category : CATEGORIES) {
            Intent query = new Intent(Intent.ACTION_MAIN).addCategory(category);
            for (ResolveInfo ri : pm.queryIntentActivities(query, 0)) {
                ActivityInfo ai = ri.activityInfo;
                if (ai.packageName.equals(ctx.getPackageName()) || byPkg.containsKey(ai.packageName)) continue;
                AppEntry e = new AppEntry();
                e.pkg = ai.packageName;
                e.label = String.valueOf(ri.loadLabel(pm)).trim();
                e.launch = new Intent(Intent.ACTION_MAIN)
                        .addCategory(category)
                        .setClassName(ai.packageName, ai.name)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                e.banner = ai.loadBanner(pm);
                if (e.banner == null) e.banner = ai.applicationInfo.loadBanner(pm);
                e.icon = ri.loadIcon(pm);
                e.color = toneColor(e.banner != null ? e.banner : e.icon);
                e.wall = tiny(e.banner != null ? e.banner : e.icon, e.color);
                byPkg.put(e.pkg, e);
            }
        }
        List<AppEntry> apps = new ArrayList<>(byPkg.values());
        sort(ctx, apps);
        return apps;
    }

    static void sort(Context ctx, List<AppEntry> apps) {
        SharedPreferences prefs = Prefs.of(ctx);
        Collator collator = Collator.getInstance();
        Collections.sort(apps, (a, b) -> {
            int ua = prefs.getInt("use:" + a.pkg, 0), ub = prefs.getInt("use:" + b.pkg, 0);
            if (ua != ub) return ub - ua;
            return collator.compare(a.label, b.label);
        });
    }

    /** يرسم الصورة بحجم 32×18 بكسل؛ لما تتكبر على الشاشة كلها تطلع ضبابية ناعمة مثل آبل تي في. */
    private static Bitmap tiny(Drawable d, int color) {
        Bitmap bmp = Bitmap.createBitmap(32, 18, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        c.drawColor(color);
        if (d != null) {
            boolean wide = d.getIntrinsicWidth() > d.getIntrinsicHeight() * 1.3f;
            if (wide) d.setBounds(0, 0, 32, 18); else d.setBounds(7, 0, 25, 18);
            d.draw(c);
        }
        return bmp;
    }

    /** ياخذ معدل لون الصورة ويخليه غامج شوية حتى الكتابة البيضة تنقرا فوگه. */
    private static int toneColor(Drawable d) {
        if (d == null) return 0xFF2C2C2E;
        int size = 24;
        Bitmap bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        d.setBounds(0, 0, size, size);
        d.draw(c);
        long r = 0, g = 0, b = 0, n = 0;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int p = bmp.getPixel(x, y);
                if (Color.alpha(p) < 128) continue;
                r += Color.red(p); g += Color.green(p); b += Color.blue(p); n++;
            }
        }
        bmp.recycle();
        if (n == 0) return 0xFF2C2C2E;
        float[] hsv = new float[3];
        Color.RGBToHSV((int) (r / n), (int) (g / n), (int) (b / n), hsv);
        if (hsv[1] > 0.12f) hsv[1] = Math.max(hsv[1], 0.45f);
        hsv[2] = Math.min(Math.max(hsv[2], 0.38f), 0.62f);
        return Color.HSVToColor(hsv);
    }
}
