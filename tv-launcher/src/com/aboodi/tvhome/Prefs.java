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

    static void countLaunch(Context ctx, String pkg) {
        SharedPreferences p = of(ctx);
        p.edit().putInt("use:" + pkg, p.getInt("use:" + pkg, 0) + 1).apply();
    }
}
