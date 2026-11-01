package com.aboodi.tvhome;

import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.os.Build;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * التحديث التلقائي: كل ساعة نشوف version.txt بالريبو. إذا اكو نسخة أجدد
 * نطلّع زر "تحديث جديد"، ولما تضغطه ننزّلها ونطلب من النظام ينصبها (يطلع سؤال تأكيد بالتلفزيون).
 */
final class Updater {
    private static final long EVERY = 3600 * 1000; // نشوف إذا اكو تحديث كل ساعة
    private static final String ACTION = "com.aboodi.tvhome.INSTALLED";

    private Updater() {}

    /** يرجع رقم النسخة الجديدة إذا أجدد من المنصبة، وإلا 0. يشتغل بخيط جانبي. */
    static int check(Context c) {
        android.content.SharedPreferences p = Prefs.of(c);
        long last = p.getLong("upd_check", 0);
        int known = p.getInt("upd_latest", 0);
        if (System.currentTimeMillis() - last > EVERY) {
            try {
                known = Integer.parseInt(WallpaperFeed.get(WallpaperFeed.RAW + "version.txt").trim());
                p.edit().putLong("upd_check", System.currentTimeMillis()).putInt("upd_latest", known).apply();
            } catch (Exception ignored) { }
        }
        return known > current(c) ? known : 0;
    }

    @SuppressWarnings("deprecation")
    static int current(Context c) {
        try { return c.getPackageManager().getPackageInfo(c.getPackageName(), 0).versionCode; }
        catch (PackageManager.NameNotFoundException e) { return 0; }
    }

    /** ينزّل النسخة الجديدة وينصبها. يشتغل بخيط جانبي. */
    @android.annotation.SuppressLint({"UnspecifiedRegisterReceiverFlag", "UnsafeIntentLaunch"})
    static void install(Context ctx) throws Exception {
        Context c = ctx.getApplicationContext();
        File apk = new File(c.getCacheDir(), "update.apk");
        WallpaperFeed.download(WallpaperFeed.RAW + "release/AboodTV.apk", apk);
        PackageInstaller pi = c.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams sp = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        int id = pi.createSession(sp);
        try (PackageInstaller.Session s = pi.openSession(id)) {
            try (InputStream in = new FileInputStream(apk); OutputStream out = s.openWrite("base.apk", 0, apk.length())) {
                byte[] b = new byte[65536];
                for (int n; (n = in.read(b)) > 0; ) out.write(b, 0, n);
                s.fsync(out);
            }
            BroadcastReceiver done = new BroadcastReceiver() {
                @Override public void onReceive(Context x, Intent i) {
                    if (i.getIntExtra(PackageInstaller.EXTRA_STATUS, -99) == PackageInstaller.STATUS_PENDING_USER_ACTION) {
                        Intent confirm = i.getParcelableExtra(Intent.EXTRA_INTENT);
                        if (confirm != null) x.startActivity(confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                    } else {
                        try { x.unregisterReceiver(this); } catch (Exception ignored) { }
                    }
                }
            };
            if (Build.VERSION.SDK_INT >= 33) c.registerReceiver(done, new IntentFilter(ACTION), Context.RECEIVER_NOT_EXPORTED);
            else c.registerReceiver(done, new IntentFilter(ACTION));
            int flags = PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 31 ? PendingIntent.FLAG_MUTABLE : 0);
            PendingIntent pi2 = PendingIntent.getBroadcast(c, id, new Intent(ACTION).setPackage(c.getPackageName()), flags);
            s.commit(pi2.getIntentSender());
        }
    }
}
