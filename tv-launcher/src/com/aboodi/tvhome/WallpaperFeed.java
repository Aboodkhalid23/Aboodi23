package com.aboodi.tvhome;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * الخلفيات من مكانين:
 * 1) صور عبود الخاصة: ينحطن بمجلد التطبيق على التلفزيون (ملف التسريع ينقلهن من الماك).
 * 2) قائمة روابط walls.txt بالريبو: التلفزيون يقراها كل يوم وينزّل صورة وحدة كل مرة،
 *    وبس والشاشة الرئيسية مفتوحة. الصور تنحفظ، فتشتغل حتى بدون نت.
 */
final class WallpaperFeed {
    static final String RAW = "https://raw.githubusercontent.com/Aboodkhalid23/Aboodi23/claude/project-thread-4ztr10/tv-launcher/";
    private static final String UA = "AboodTV/8 (https://github.com/Aboodkhalid23/Aboodi23)";
    private static final int KEEP = 150; // كم صورة منزّلة نخلي
    private static final long LIST_EVERY = 6L * 3600 * 1000; // نشوف إذا اكو صور جديدة كل 6 ساعات

    private final Context ctx;
    private final File cache, mine, listFile;
    private final Random random = new Random();
    private final List<File> bag = new ArrayList<>(); // نخلط الصور ونمشي عليهن وحدة وحدة بدون تكرار
    private final List<File> fresh = new ArrayList<>(); // صور توها نزلت: تطلع أول شي
    /** يصير true أول ما تطلع من الرئيسية: أي تنزيل صورة يوقف بنفس اللحظة، حتى النت كله للتطبيق. */
    static volatile boolean stop;
    private static final Bitmap BAD = Bitmap.createBitmap(1, 1, Bitmap.Config.ALPHA_8); // علامة: ملف خربان

    WallpaperFeed(Context c) {
        ctx = c.getApplicationContext();
        cache = new File(ctx.getFilesDir(), "walls2");
        //noinspection ResultOfMethodCallIgnored
        cache.mkdirs();
        File ext = ctx.getExternalFilesDir("mywalls");
        mine = ext != null ? ext : new File(ctx.getFilesDir(), "mywalls");
        listFile = new File(ctx.getFilesDir(), "walls.txt");
        deleteDir(new File(ctx.getFilesDir(), "walls")); // صور النسخ القديمة (ويكيميديا)
    }

    /** الصورة الجاية بدقة الشاشة الكاملة. null إذا بعد ماكو ولا صورة. */
    Bitmap next(int screenW, int screenH) {
        synchronized (fresh) {
            while (!fresh.isEmpty()) {
                File f = fresh.remove(0);
                bag.remove(f);
                Bitmap b = f.exists() ? decode(f, screenW, screenH) : null;
                if (b != null && b != BAD) return b;
            }
        }
        if (bag.isEmpty()) {
            List<File> all = new ArrayList<>();
            addJpgs(mine, all);
            addJpgs(cache, all);
            Collections.shuffle(all, random);
            // صور عبود أول بكل دورة
            List<File> own = new ArrayList<>();
            addJpgs(mine, own);
            all.removeAll(own);
            Collections.shuffle(own, random);
            bag.addAll(own);
            bag.addAll(all);
        }
        while (!bag.isEmpty()) {
            File f = bag.remove(0);
            Bitmap b = decode(f, screenW, screenH);
            if (b == null) { System.gc(); continue; } // ما گدرنا هسة، نكمل بالي بعدها
            if (b != BAD) return b;
            //noinspection ResultOfMethodCallIgnored
            f.delete(); // صورة خربانة
        }
        return null;
    }

    int count() {
        String[] a = cache.list(), b = mine.list();
        return (a == null ? 0 : a.length) + (b == null ? 0 : b.length);
    }

    /** ينزّل صورة جديدة وحدة من القائمة إذا اكو نت. يشتغل بخيط جانبي. */
    void fetchOne() {
        if (stop || !online()) return;
        try {
            List<String> urls = urls();
            prune(urls);
            Collections.shuffle(urls, random);
            for (String url : urls) {
                File out = new File(cache, Integer.toHexString(url.hashCode()) + ".jpg");
                if (out.exists()) continue;
                download(url, out);
                synchronized (fresh) { fresh.add(out); }
                trim();
                return;
            }
        } catch (Exception ignored) {
            // النت قاطع: نكمل بالمحفوظة
        }
    }

    /** أي صورة منزّلة انشالت من القائمة (ما حلوة) نمسحها من التلفزيون هم. */
    private void prune(List<String> urls) {
        if (urls.isEmpty()) return;
        java.util.Set<String> keep = new java.util.HashSet<>();
        for (String u : urls) keep.add(Integer.toHexString(u.hashCode()) + ".jpg");
        File[] fs = cache.listFiles();
        if (fs != null) for (File f : fs) if (!keep.contains(f.getName())) //noinspection ResultOfMethodCallIgnored
            f.delete();
    }

    /** القائمة من الريبو، نجددها كل 6 ساعات. */
    private List<String> urls() throws Exception {
        if (!listFile.exists() || System.currentTimeMillis() - listFile.lastModified() > LIST_EVERY) {
            try { download(RAW + "walls.txt", listFile); } catch (Exception ignored) { }
        }
        List<String> out = new ArrayList<>();
        if (!listFile.exists()) return out;
        for (String line : new String(readAll(listFile), "UTF-8").split("\n")) {
            line = line.trim();
            if (line.startsWith("http")) out.add(line);
        }
        return out;
    }

    /**
     * نقرا الصورة بدقة الشاشة بالضبط وبألوان كاملة (ARGB_8888). التصغير يصير وقت القراءة نفسها،
     * فما نحجز صورة 4K كاملة بالرام (هذا الي چان يخلص الذاكرة ويخلي الصور ما تتبدل).
     */
    private static Bitmap decode(File f, int w, int h) {
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(f.getPath(), o);
        if (o.outWidth <= 0) return BAD;
        o.inSampleSize = 1;
        while (o.outWidth / (o.inSampleSize * 2) >= w && o.outHeight / (o.inSampleSize * 2) >= h) o.inSampleSize *= 2;
        float s = Math.max((float) w / (o.outWidth / o.inSampleSize), (float) h / (o.outHeight / o.inSampleSize));
        if (s < 1f) { // نصغر للشاشة وقت القراءة
            o.inScaled = true;
            o.inDensity = 10000;
            o.inTargetDensity = Math.max(1, Math.round(10000 * s));
        }
        o.inJustDecodeBounds = false;
        o.inPreferredConfig = Bitmap.Config.ARGB_8888;
        try {
            Bitmap b = BitmapFactory.decodeFile(f.getPath(), o);
            return b != null ? b : BAD;
        } catch (OutOfMemoryError e) {
            return null; // الرام مليانة هسة: الصورة سليمة، نجربها بعدين
        }
    }

    private static void addJpgs(File dir, List<File> into) {
        File[] fs = dir.listFiles();
        if (fs == null) return;
        for (File f : fs) {
            String n = f.getName().toLowerCase(java.util.Locale.ROOT);
            if (n.endsWith(".jpg") || n.endsWith(".jpeg") || n.endsWith(".png") || n.endsWith(".webp")) into.add(f);
        }
    }

    private boolean online() {
        ConnectivityManager cm = (ConnectivityManager) ctx.getSystemService(Context.CONNECTIVITY_SERVICE);
        @SuppressWarnings("deprecation") NetworkInfo n = cm != null ? cm.getActiveNetworkInfo() : null;
        return n != null && n.isConnected();
    }

    static HttpURLConnection open(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setRequestProperty("User-Agent", UA);
        c.setConnectTimeout(8000);
        c.setReadTimeout(20000);
        return c;
    }

    static void download(String url, File out) throws Exception {
        File tmp = new File(out.getPath() + ".part");
        HttpURLConnection c = open(url);
        try (InputStream in = c.getInputStream(); OutputStream os = new FileOutputStream(tmp)) {
            if (c.getResponseCode() != 200) throw new java.io.IOException("HTTP " + c.getResponseCode());
            byte[] b = new byte[32768];
            for (int n; (n = in.read(b)) > 0; ) {
                if (stop) throw new java.io.IOException("stopped"); // انفتح تطبيق: نوقف التنزيل فوراً
                os.write(b, 0, n);
            }
        } finally {
            c.disconnect();
        }
        if (!tmp.renameTo(out)) throw new java.io.IOException("rename");
    }

    static String get(String url) throws Exception {
        HttpURLConnection c = open(url);
        try (InputStream in = c.getInputStream()) {
            java.io.ByteArrayOutputStream buf = new java.io.ByteArrayOutputStream();
            byte[] b = new byte[8192];
            for (int n; (n = in.read(b)) > 0; ) buf.write(b, 0, n);
            return buf.toString("UTF-8");
        } finally {
            c.disconnect();
        }
    }

    private static byte[] readAll(File f) throws Exception {
        try (InputStream in = new java.io.FileInputStream(f)) {
            java.io.ByteArrayOutputStream buf = new java.io.ByteArrayOutputStream();
            byte[] b = new byte[8192];
            for (int n; (n = in.read(b)) > 0; ) buf.write(b, 0, n);
            return buf.toByteArray();
        }
    }

    /** نخلي آخر 60 صورة منزّلة بس، حتى ما تملي ذاكرة التلفزيون. */
    private void trim() {
        File[] files = cache.listFiles();
        if (files == null || files.length <= KEEP) return;
        java.util.Arrays.sort(files, (a, b) -> Long.compare(a.lastModified(), b.lastModified()));
        for (int i = 0; i < files.length - KEEP; i++) //noinspection ResultOfMethodCallIgnored
            files[i].delete();
    }

    private static void deleteDir(File d) {
        File[] fs = d.listFiles();
        if (fs != null) for (File f : fs) //noinspection ResultOfMethodCallIgnored
            f.delete();
        //noinspection ResultOfMethodCallIgnored
        d.delete();
    }
}
