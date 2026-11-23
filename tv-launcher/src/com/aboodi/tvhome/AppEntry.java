package com.aboodi.tvhome;

import android.content.Intent;
import android.graphics.drawable.Drawable;

/** تطبيق واحد منصب على التلفزيون، ويا الي نحتاجه حتى نرسمه ونفتحه. */
final class AppEntry {
    String pkg;
    String label;
    Intent launch;
    Drawable banner;   // صورة عريضة 16:9 (تطبيقات التلفزيون عدها وحدة)
    Drawable icon;     // الأيقونة العادية، إذا ماكو بانر
    int color;         // لون التطبيق، للخلفية فوگ
    android.graphics.Bitmap wall; // نسخة صغيرة جداً من صورته، نكبّرها فتصير خلفية ضبابية
}
