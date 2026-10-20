package com.aboodi.tvhome;

import android.content.Context;
import android.content.SharedPreferences;

/** الإعدادات المحفوظة: اللغة، وكم مرة انفتح كل تطبيق. */
final class Prefs {
    private Prefs() {}

    static SharedPreferences of(Context ctx) {
        return ctx.getSharedPreferences("home", Context.MODE_PRIVATE);
    }

    static boolean arabic(Context ctx) {
        return "ar".equals(of(ctx).getString("lang", "ar"));
    }

    static void setArabic(Context ctx, boolean ar) {
        of(ctx).edit().putString("lang", ar ? "ar" : "en").apply();
    }

    static boolean dark(Context ctx) { return of(ctx).getBoolean("dark", false); }

    static void setDark(Context ctx, boolean d) { of(ctx).edit().putBoolean("dark", d).apply(); }

    /** تطبيقات الشاشة الرئيسية. أول مرة: نتفلكس ويوتيوب وDAR. */
    static java.util.List<String> favorites(Context ctx) {
        String saved = of(ctx).getString("favs", "com.netflix.ninja,com.google.android.youtube.tv,com.mbm_soft.darplayer,com.spotify.tv.android");
        java.util.List<String> out = new java.util.ArrayList<>();
        for (String p : saved.split(",")) if (!p.isEmpty()) out.add(p);
        return out;
    }

    static void setFavorites(Context ctx, java.util.List<String> pkgs) {
        of(ctx).edit().putString("favs", android.text.TextUtils.join(",", pkgs)).apply();
    }

    static void countLaunch(Context ctx, String pkg) {
        SharedPreferences p = of(ctx);
        p.edit().putInt("use:" + pkg, p.getInt("use:" + pkg, 0) + 1).apply();
    }
}
