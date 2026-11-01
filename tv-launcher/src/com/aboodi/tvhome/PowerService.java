package com.aboodi.tvhome;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;

/**
 * التطبيقات العادية ما يسمحلها اندرويد تسوي ريستارت. بس خدمة "إمكانية الوصول" تگدر تفتح
 * قائمة الطاقة نفسها (الي بيها إعادة التشغيل). ملف التسريع يشغّل هذي الخدمة مرة وحدة.
 */
public class PowerService extends AccessibilityService {
    private static PowerService sInstance;

    @Override protected void onServiceConnected() { sInstance = this; }

    @Override public boolean onUnbind(android.content.Intent i) { sInstance = null; return super.onUnbind(i); }

    @Override public void onAccessibilityEvent(AccessibilityEvent e) { }

    @Override public void onInterrupt() { }

    /** يفتح قائمة الطاقة. يرجع false إذا الخدمة بعدها مو مشغلة. */
    static boolean powerMenu() {
        return sInstance != null && sInstance.performGlobalAction(GLOBAL_ACTION_POWER_DIALOG);
    }
}
