package com.aboodi.tvhome;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Random;

/**
 * خلفيات اليابان: صور احترافية مجانية من ويكيميديا كومنز (Quality images)، تنزل وحدة وحدة
 * وتنحفظ بالتلفزيون، فتبقى تشتغل حتى بدون نت. ينادونه بس والشاشة الرئيسية مفتوحة.
 */
final class WallpaperFeed {
    private static final String UA = "AboodTV/2 (https://github.com/Aboodkhalid23/Aboodi23)";
    private static final int KEEP = 60; // كم صورة نخلي بالذاكرة
    /** شوارع ومباني حديثة بالليل: طوكيو أكثر شي، وويّاها مدن ثانية بنفس الجو. */
    private static final String[] TOPICS = {
            "Shinjuku night", "Shibuya night", "Shibuya Crossing night", "Tokyo night skyline", "Ginza night",
            "Akihabara night", "Roppongi night", "Kabukicho night", "Tokyo Skytree night", "Tokyo Tower night",
            "Tokyo neon", "Odaiba night", "Shinjuku skyscrapers night", "Tokyo street night", "Osaka Dotonbori night",
            "Hong Kong night skyline", "Seoul night", "Shanghai skyline night", "Dubai night skyline",
            "Singapore Marina Bay night", "New York night skyline", "Taipei night"
    };

    private final File dir;
    private final Context ctx;
    private final Random random = new Random();
    private final List<String> queue = new ArrayList<>();
    private int shown;

    WallpaperFeed(Context ctx) {
        this.ctx = ctx.getApplicationContext();
        dir = new File(ctx.getFilesDir(), "walls");
        //noinspection ResultOfMethodCallIgnored
        dir.mkdirs();
    }

    /** الصورة الجاية من الي محفوظة. يرجع null إذا بعد ماكو ولا وحدة. */
    Bitmap next(int maxWidth) {
        File[] files = dir.listFiles((d, n) -> n.endsWith(".jpg"));
        if (files == null || files.length == 0) return null;
        Arrays.sort(files, (a, b) -> Long.compare(b.lastModified(), a.lastModified()));
        // الجديدة أول مرة، وبعدين بالترتيب العشوائي
        File f = shown < files.length && shown < 3 ? files[shown] : files[random.nextInt(files.length)];
        shown++;
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(f.getPath(), o);
        o.inSampleSize = 1;
        while (o.outWidth / (o.inSampleSize * 2) >= maxWidth) o.inSampleSize *= 2;
        o.inJustDecodeBounds = false;
        o.inPreferredConfig = Bitmap.Config.RGB_565; // نص الذاكرة، والصورة نفس الحلاوة
        return BitmapFactory.decodeFile(f.getPath(), o);
    }

    /** ينزّل صورة جديدة وحدة إذا اكو نت. يشتغل بخيط جانبي. */
    void fetchOne() {
        if (!online()) return;
        try {
            if (queue.isEmpty()) refill(true);
            if (queue.isEmpty()) refill(false); // إذا البحث الدقيق ما رجّع شي، نبحث أوسع
            while (!queue.isEmpty()) {
                String url = queue.remove(0);
                File out = new File(dir, Integer.toHexString(url.hashCode()) + ".jpg");
                if (out.exists()) continue;
                download(url, out);
                if (tooBright(out)) { //noinspection ResultOfMethodCallIgnored
                    out.delete(); continue; } // نريد بس صور داكنة بالليل
                trim();
                return;
            }
        } catch (Exception ignored) {
            // النت قاطع أو الموقع ما رد: نكمل بالصور المحفوظة
        }
    }

    int count() {
        String[] n = dir.list((d, name) -> name.endsWith(".jpg"));
        return n == null ? 0 : n.length;
    }

    /** نصغّر الصورة لـ 32×18 ونحسب معدل الضوء؛ إذا فاتحة (نهار) نرميها. */
    private static boolean tooBright(File f) {
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inSampleSize = 32;
        Bitmap b = BitmapFactory.decodeFile(f.getPath(), o);
        if (b == null) return true;
        Bitmap s = Bitmap.createScaledBitmap(b, 32, 18, true);
        double sum = 0;
        for (int y = 0; y < 18; y++) for (int x = 0; x < 32; x++) {
            int p = s.getPixel(x, y);
            sum += 0.2126 * ((p >> 16) & 255) + 0.7152 * ((p >> 8) & 255) + 0.0722 * (p & 255);
        }
        if (s != b) s.recycle();
        b.recycle();
        return sum / (32 * 18) > 105; // من 255
    }

    private void refill(boolean strict) throws Exception {
        String topic = TOPICS[random.nextInt(TOPICS.length)];
        String search = strict ? topic + " incategory:Quality_images filetype:bitmap filew:>1900" : topic + " filetype:bitmap filew:>1600";
        String api = "https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
                + "&gsrnamespace=6&gsrlimit=20&gsroffset=" + (strict ? random.nextInt(120) : random.nextInt(40))
                + "&gsrsearch=" + URLEncoder.encode(search, "UTF-8")
                + "&prop=imageinfo&iiprop=url&iiurlwidth=1920";
        JSONObject pages = new JSONObject(get(api)).optJSONObject("query");
        if (pages == null) return;
        pages = pages.optJSONObject("pages");
        if (pages == null) return;
        for (Iterator<String> it = pages.keys(); it.hasNext(); ) {
            JSONObject info = pages.getJSONObject(it.next()).getJSONArray("imageinfo").getJSONObject(0);
            int w = info.optInt("thumbwidth"), h = info.optInt("thumbheight");
            String thumb = info.optString("thumburl", "");
            if (w > h * 1.3f && w >= 1280 && !thumb.isEmpty()) queue.add(thumb); // بس الصور العريضة
        }
        java.util.Collections.shuffle(queue, random);
    }

    private boolean online() {
        ConnectivityManager cm = (ConnectivityManager) ctx.getSystemService(Context.CONNECTIVITY_SERVICE);
        @SuppressWarnings("deprecation") NetworkInfo n = cm != null ? cm.getActiveNetworkInfo() : null;
        return n != null && n.isConnected();
    }

    private static HttpURLConnection open(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setRequestProperty("User-Agent", UA);
        c.setConnectTimeout(8000);
        c.setReadTimeout(15000);
        return c;
    }

    private static String get(String url) throws Exception {
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

    private static void download(String url, File out) throws Exception {
        File tmp = new File(out.getPath() + ".part");
        HttpURLConnection c = open(url);
        try (InputStream in = c.getInputStream(); OutputStream os = new FileOutputStream(tmp)) {
            byte[] b = new byte[16384];
            for (int n; (n = in.read(b)) > 0; ) os.write(b, 0, n);
        } finally {
            c.disconnect();
        }
        //noinspection ResultOfMethodCallIgnored
        tmp.renameTo(out);
    }

    /** نخلي آخر 60 صورة بس، حتى ما تملي ذاكرة التلفزيون. */
    private void trim() {
        File[] files = dir.listFiles();
        if (files == null || files.length <= KEEP) return;
        Arrays.sort(files, (a, b) -> Long.compare(a.lastModified(), b.lastModified()));
        for (int i = 0; i < files.length - KEEP; i++) //noinspection ResultOfMethodCallIgnored
            files[i].delete();
    }
}
