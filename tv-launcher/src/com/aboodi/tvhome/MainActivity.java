package com.aboodi.tvhome;

import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.ActivityManager;
import android.content.ActivityNotFoundException;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.TrafficStats;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.OvershootInterpolator;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextClock;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * شاشة عبود 5: خلفيات أنمي وطوكيو بدقة عالية تتبدل كل 20 ثانية، وفوگها زجاج مثل آبل:
 * الساعة والوايفاي واللغة والوضع الداكن والإعدادات بالزاوية، والتطبيقات بشريط زجاجي عائم تحت.
 * وتنظف التلفزيون بنفسها كل ما ترجع للرئيسية، وتحدّث نفسها.
 */
public class MainActivity extends Activity {
    private static final int GRID_COLS = 6;
    private static final int INK = 0xFFFFFFFF;
    private static final String ALL = "@all";
    private static final long AMBIENT_AFTER = 3 * 60 * 1000; // بعد 3 دقايق بدون ريموت: تبين الصورة بس
    /** هذني ما نسكرهن أبداً بالتنظيف: دار (المباريات) وسبوتيفاي (الأغاني) وخدمات النظام. */
    private static final Set<String> KEEP = new HashSet<>(java.util.Arrays.asList(
            "com.mbm_soft.darplayer", "com.spotify.tv.android", "com.google.android.gms",
            "com.google.android.katniss", "com.google.android.tvlauncher", "com.android.vending"));

    private static final String DAR = "com.mbm_soft.darplayer";
    private static final long MATCH_FOR = 3 * 3600 * 1000; // وضع المباراة يظل 3 ساعات
    /** بوضع المباراة نسكر حتى سبوتيفاي، ونخلي بس دار وخدمات النظام. */
    private static final Set<String> MATCH_KEEP = new HashSet<>(java.util.Arrays.asList(
            DAR, "com.google.android.gms", "com.google.android.katniss", "com.android.vending"));

    private static List<AppEntry> sApps;
    private static long matchUntil; // static: يظل حتى لو النظام سوّى للشاشة إعادة بناء

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final ExecutorService net = Executors.newSingleThreadExecutor(); // تنزيلات (بطيئة)
    private final ExecutorService pics = Executors.newSingleThreadExecutor(); // تجهيز الصور (سريع)
    private Bitmap ready, readyBlur; // الصورة الجاية جاهزة مقدماً، فالتبديل فوري
    private final Handler main = new Handler(Looper.getMainLooper());
    private final OvershootInterpolator pop = new OvershootInterpolator(1.3f);
    private final DecelerateInterpolator ease = new DecelerateInterpolator(2f);

    private float u;
    private int screenW, screenH;
    private FrameLayout root;
    private ImageView wallA, wallB;
    private boolean wallAOnTop = true;
    private View dim;
    private TextView phrase, phraseHint, dateText, focusLabel, allTitle;
    private TextClock clock;
    private LinearLayout topBar, dock, allGrid;
    private Glass.GlassFrame dockGlass, allPanel, updateChip;
    private Glyph wifiGlyph, darkGlyph, ballGlyph;
    private TextView speedText, ramText;
    private long lastRx = -1, lastRxAt;
    private boolean testing;
    private WallpaperFeed feed;
    private boolean visible, ambient;
    private int phraseIndex;
    private long lastFetch, lastClean, lastKey = System.currentTimeMillis(), lastWeather;
    private String weather = "";

    private static final String[][] PHRASES = {
            {"夜の東京", "طوكيو بالليل", "Tokyo at night"},
            {"おかえり", "هلا بيك برجعتك", "Welcome home"},
            {"桜", "زهرة الكرز", "Cherry blossom"},
            {"夢", "حلم", "Dream"},
            {"侍", "ساموراي", "Samurai"},
            {"一期一会", "كل لقاء يصير مرة وحدة بالعمر", "Once in a lifetime"},
            {"頑張って", "شد حيلك", "Keep going"},
            {"七転び八起き", "توگع سبع مرات وتگوم ثمانية", "Fall seven, rise eight"},
            {"静けさ", "الهدوء", "Stillness"},
            {"光", "ضوء", "Light"},
            {"富士山", "جبل فوجي", "Mount Fuji"},
            {"ありがとう", "شكراً", "Thank you"},
    };

    private final Runnable rotate = new Runnable() {
        @Override public void run() {
            if (!visible) return;
            nextWallpaper();
            main.postDelayed(this, 20000);
        }
    };

    private final Runnable dateTick = this::updateDate;

    /** كل ثانيتين: سرعة النت هسة والرام الفاضية (بس والرئيسية مفتوحة). */
    private final Runnable statsTick = new Runnable() {
        @Override public void run() {
            if (!visible) return;
            updateStats();
            main.postDelayed(this, 2000);
        }
    };

    private final Runnable ambientCheck = new Runnable() {
        @Override public void run() {
            if (!visible) return;
            if (!ambient && System.currentTimeMillis() - lastKey > AMBIENT_AFTER && allPanel.getVisibility() != View.VISIBLE) setAmbient(true);
            main.postDelayed(this, 15000);
        }
    };

    private final BroadcastReceiver packagesChanged = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { reload(); }
    };

    private final BroadcastReceiver netChanged = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { updateWifi(); }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Window w = getWindow();
        w.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        w.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);

        DisplayMetrics dm = getResources().getDisplayMetrics();
        screenW = Math.max(dm.widthPixels, dm.heightPixels);
        screenH = Math.min(dm.widthPixels, dm.heightPixels);
        u = screenW / 1920f;
        feed = new WallpaperFeed(this);
        Glass.Backdrop.dark = Prefs.dark(this);

        buildScreen();
        applyLanguage();
        applyDark(false);
        setContentView(root);

        if (sApps != null) showApps(sApps);
        reload();

        IntentFilter f = new IntentFilter();
        f.addAction(Intent.ACTION_PACKAGE_ADDED);
        f.addAction(Intent.ACTION_PACKAGE_REMOVED);
        f.addAction(Intent.ACTION_PACKAGE_CHANGED);
        f.addDataScheme("package");
        registerReceiver(packagesChanged, f);
        IntentFilter nf = new IntentFilter(ConnectivityManager.CONNECTIVITY_ACTION);
        nf.addAction(WifiManager.RSSI_CHANGED_ACTION);
        registerReceiver(netChanged, nf);
    }

    @Override
    protected void onResume() {
        super.onResume();
        visible = true;
        lastKey = System.currentTimeMillis();
        setAmbient(false);
        updateWifi();
        main.removeCallbacks(rotate);
        main.post(rotate);
        main.removeCallbacks(ambientCheck);
        main.postDelayed(ambientCheck, 15000);
        main.postDelayed(this::cleanUp, 1500);
        lastRx = -1;
        main.removeCallbacks(statsTick);
        main.post(statsTick);
        applyMatch();
        if (matchMode()) return; // وضع المباراة: ولا طلب نت من الشاشة
        net.execute(() -> {
            int v = Updater.check(this);
            main.post(() -> updateChip.setVisibility(v > 0 ? View.VISIBLE : View.GONE));
            loadWeather();
        });
    }

    /** أول ما يفتح تطبيق ثاني: نوقف كلشي، ولا بايت نت. */
    @Override
    protected void onPause() {
        visible = false;
        main.removeCallbacks(rotate);
        main.removeCallbacks(ambientCheck);
        main.removeCallbacks(statsTick);
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        unregisterReceiver(packagesChanged);
        unregisterReceiver(netChanged);
        worker.shutdownNow();
        net.shutdownNow();
        pics.shutdownNow();
        super.onDestroy();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        closeAll();
        focusFirst();
    }

    @Override
    public void onBackPressed() {
        if (allPanel.getVisibility() == View.VISIBLE) closeAll();
        else focusFirst();
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        lastKey = System.currentTimeMillis();
        if (ambient) { // أول ضغطة بعد وضع العرض بس ترجّع الواجهة
            if (e.getAction() == KeyEvent.ACTION_UP) setAmbient(false);
            return true;
        }
        return super.dispatchKeyEvent(e);
    }

    private void focusFirst() {
        if (dock.getChildCount() > 0) dock.getChildAt(0).requestFocus();
    }

    // ---------- بناء الشاشة ----------

    private void buildScreen() {
        root = new FrameLayout(this);
        root.setClipChildren(false);
        root.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0xFF0B1028, 0xFF1C1F4A, 0xFF3A2856})); // لحد ما توصل أول صورة
        wallA = wallView();
        wallB = wallView();
        wallB.setAlpha(0f);
        root.addView(wallB, new FrameLayout.LayoutParams(-1, -1));
        root.addView(wallA, new FrameLayout.LayoutParams(-1, -1));
        dim = new View(this);
        root.addView(dim, new FrameLayout.LayoutParams(-1, -1));

        // يسار فوگ: كلمة يابانية صغيرة ومعناها
        LinearLayout left = new LinearLayout(this);
        left.setOrientation(LinearLayout.VERTICAL);
        left.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        phrase = text(30, INK, false);
        phrase.setShadowLayer(px(14), 0, px(2), 0x99000000);
        phraseHint = text(20, 0xCCFFFFFF, false);
        phraseHint.setShadowLayer(px(10), 0, px(2), 0x99000000);
        left.addView(phrase);
        left.addView(phraseHint);
        FrameLayout.LayoutParams lLp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.LEFT);
        lLp.topMargin = px(52);
        lLp.leftMargin = px(70);
        root.addView(left, lLp);

        // يمين فوگ: أزرار زجاجية + الساعة
        topBar = new LinearLayout(this);
        topBar.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setClipChildren(false);
        updateChip = new Glass.GlassFrame(this, px(36));
        LinearLayout uc = new LinearLayout(this);
        uc.setGravity(Gravity.CENTER_VERTICAL);
        uc.setPadding(px(22), 0, px(26), 0);
        Glyph ug = new Glyph(this, Glyph.UPDATE);
        uc.addView(ug, new LinearLayout.LayoutParams(px(30), px(30)));
        TextView ut = text(22, INK, true);
        ut.setTag("upd");
        LinearLayout.LayoutParams utl = new LinearLayout.LayoutParams(-2, -2);
        utl.leftMargin = px(10);
        uc.addView(ut, utl);
        updateChip.addView(uc, new FrameLayout.LayoutParams(-2, -1));
        updateChip.setVisibility(View.GONE);
        button(updateChip, null, v -> {
            Toast.makeText(this, Prefs.arabic(this) ? "دا أنزّل التحديث..." : "Downloading update...", Toast.LENGTH_SHORT).show();
            net.execute(() -> {
                try { Updater.install(this); }
                catch (Exception e) {
                    main.post(() -> Toast.makeText(this, Prefs.arabic(this) ? "ما گدرت أنزّل التحديث، جرب بعدين" : "Update failed, try later", Toast.LENGTH_LONG).show());
                }
            });
        });
        addTop(updateChip, -2);

        ballGlyph = new Glyph(this, Glyph.BALL);
        addTop(iconButton(ballGlyph, v -> toggleMatch()), px(72));
        addTop(iconButton(Glyph.GEAR, v -> open(new Intent(Settings.ACTION_SETTINGS))), px(72));
        darkGlyph = new Glyph(this, Glyph.MOON);
        addTop(iconButton(darkGlyph, v -> { Prefs.setDark(this, !Prefs.dark(this)); applyDark(true); }), px(72));
        addTop(iconButton(Glyph.LANG, v -> { Prefs.setArabic(this, !Prefs.arabic(this)); applyLanguage(); }), px(72));
        wifiGlyph = new Glyph(this, Glyph.WIFI);
        addTop(iconButton(wifiGlyph, v -> {
            Intent wi = new Intent(Settings.ACTION_WIFI_SETTINGS);
            if (wi.resolveActivity(getPackageManager()) == null) wi = new Intent(Settings.ACTION_SETTINGS);
            open(wi);
        }), px(72));

        // جنب الوايفاي: سرعة النت هسة والرام الفاضية. تضغطه = فحص سرعة
        Glass.GlassFrame stats = new Glass.GlassFrame(this, px(36));
        LinearLayout sc = new LinearLayout(this);
        sc.setOrientation(LinearLayout.VERTICAL);
        sc.setGravity(Gravity.CENTER);
        sc.setPadding(px(22), 0, px(22), 0);
        speedText = text(19, INK, true);
        ramText = text(17, 0xD9FFFFFF, false);
        sc.addView(speedText);
        sc.addView(ramText);
        stats.addView(sc, new FrameLayout.LayoutParams(-2, -1));
        button(stats, null, v -> speedTest());
        addTop(stats, -2);

        LinearLayout clockBox = new LinearLayout(this);
        clockBox.setOrientation(LinearLayout.VERTICAL);
        clockBox.setGravity(Gravity.RIGHT);
        clock = new TextClock(this);
        clock.setFormat12Hour("h:mm");
        clock.setFormat24Hour("H:mm");
        clock.setTextColor(INK);
        clock.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(64));
        clock.setTypeface(Typeface.create("sans-serif-light", Typeface.NORMAL));
        clock.setIncludeFontPadding(false);
        clock.setShadowLayer(px(16), 0, px(2), 0x73000000);
        dateText = text(22, 0xE6FFFFFF, false);
        dateText.setShadowLayer(px(12), 0, px(2), 0x99000000);
        clockBox.addView(clock);
        clockBox.addView(dateText);
        LinearLayout.LayoutParams cbl = new LinearLayout.LayoutParams(-2, -2);
        cbl.leftMargin = px(24);
        topBar.addView(clockBox, cbl);
        FrameLayout.LayoutParams tLp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.RIGHT);
        tLp.topMargin = px(44);
        tLp.rightMargin = px(60);
        root.addView(topBar, tLp);

        // تحت: شريط زجاجي عائم بيه التطبيقات
        dockGlass = new Glass.GlassFrame(this, px(44));
        dockGlass.setClipChildren(false);
        dockGlass.setClipToPadding(false);
        dock = new LinearLayout(this);
        dock.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        dock.setClipChildren(false);
        dock.setClipToPadding(false);
        dock.setPadding(px(32), px(28), px(32), px(28));
        dockGlass.addView(dock, new FrameLayout.LayoutParams(-2, -2));
        shadow(dockGlass, px(44), px(14));
        FrameLayout.LayoutParams dLp = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        dLp.bottomMargin = px(96);
        root.addView(dockGlass, dLp);

        focusLabel = text(24, INK, false);
        focusLabel.setShadowLayer(px(10), 0, px(2), 0xCC000000);
        focusLabel.setAlpha(0f);
        FrameLayout.LayoutParams flLp = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.LEFT);
        flLp.bottomMargin = px(44);
        root.addView(focusLabel, flLp);

        // لوحة "كل التطبيقات": زجاج على الشاشة كلها
        allPanel = new Glass.GlassFrame(this, 0);
        allPanel.setVisibility(View.GONE);
        View shade = new View(this);
        shade.setBackgroundColor(0x66000000);
        allPanel.addView(shade, new FrameLayout.LayoutParams(-1, -1));
        allTitle = text(46, INK, true);
        FrameLayout.LayoutParams atLp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.START);
        atLp.topMargin = px(60);
        atLp.setMarginStart(px(120));
        allPanel.addView(allTitle, atLp);
        ScrollView sv = new ScrollView(this);
        sv.setVerticalScrollBarEnabled(false);
        sv.setClipToPadding(false);
        sv.setClipChildren(false);
        allGrid = new LinearLayout(this);
        allGrid.setOrientation(LinearLayout.VERTICAL);
        allGrid.setClipChildren(false);
        allGrid.setPadding(px(120), px(40), px(120), px(120));
        sv.addView(allGrid, new FrameLayout.LayoutParams(-1, -2));
        FrameLayout.LayoutParams svLp = new FrameLayout.LayoutParams(-1, -1);
        svLp.topMargin = px(150);
        allPanel.addView(sv, svLp);
        root.addView(allPanel, new FrameLayout.LayoutParams(-1, -1));
    }

    private void addTop(View v, int size) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(size == -2 ? -2 : size, px(72));
        lp.leftMargin = px(16);
        topBar.addView(v, lp);
    }

    private View iconButton(int kind, View.OnClickListener click) { return iconButton(new Glyph(this, kind), click); }

    /** زر دائري زجاجي: لما يتأشر عليه يصير أبيض والأيقونة غامجة، ويكبر بنطّة ناعمة. */
    private View iconButton(Glyph g, View.OnClickListener click) {
        Glass.GlassFrame b = new Glass.GlassFrame(this, px(36));
        b.addView(g, new FrameLayout.LayoutParams(px(34), px(34), Gravity.CENTER));
        button(b, g, click);
        return b;
    }

    private void button(Glass.GlassFrame b, Glyph g, View.OnClickListener click) {
        b.setFocusable(true);
        b.setClickable(true);
        b.setOnClickListener(click);
        b.setOnFocusChangeListener((v, has) -> {
            glow(b, has);
            if (g != null) g.tint(has && !Prefs.dark(this) ? 0xFF15151A : INK);
            v.animate().scaleX(has ? 1.15f : 1f).scaleY(has ? 1.15f : 1f).setDuration(180).setInterpolator(pop).start();
        });
    }

    private void glow(Glass.GlassFrame f, boolean on) {
        ValueAnimator a = ValueAnimator.ofFloat(f.glow, on ? 1f : 0f).setDuration(220);
        a.addUpdateListener(x -> f.setGlow((float) x.getAnimatedValue()));
        a.start();
    }

    private void shadow(View v, int radius, int elevation) {
        v.setOutlineProvider(new ViewOutlineProvider() {
            @Override public void getOutline(View view, Outline o) {
                o.setRoundRect(0, 0, view.getWidth(), view.getHeight(), radius);
                o.setAlpha(0.35f);
            }
        });
        v.setElevation(elevation);
    }

    private ImageView wallView() {
        ImageView v = new ImageView(this);
        v.setScaleType(ImageView.ScaleType.CENTER_CROP);
        return v;
    }

    private void reload() {
        worker.execute(() -> {
            List<AppEntry> apps = AppLoader.load(getApplicationContext());
            main.post(() -> {
                if (isDestroyed()) return;
                boolean same = sameOrder(sApps, apps);
                sApps = apps;
                if (!same || dock.getChildCount() == 0) showApps(apps);
            });
        });
    }

    private List<AppEntry> favorites(List<AppEntry> apps) {
        List<AppEntry> favs = new ArrayList<>();
        for (String pkg : Prefs.favorites(this)) {
            for (AppEntry a : apps) if (a.pkg.equals(pkg)) { favs.add(a); break; }
        }
        if (favs.isEmpty()) favs.addAll(apps.subList(0, Math.min(3, apps.size())));
        return favs;
    }

    private void showApps(List<AppEntry> apps) {
        View focused = getCurrentFocus();
        Object keep = focused != null ? focused.getTag() : null;
        boolean focusInDock = focused != null && focused.getParent() == dock;
        dock.removeAllViews();
        int w = px(200), h = px(124), gap = px(28);
        View restore = null;
        List<AppEntry> favs = favorites(apps);
        for (int i = 0; i <= favs.size(); i++) {
            AppEntry app = i < favs.size() ? favs.get(i) : null; // الأخير = كل التطبيقات
            View t = app != null ? dockTile(app, w, h) : allAppsTile(w, h);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(w, h);
            if (i > 0) lp.leftMargin = gap;
            dock.addView(t, lp);
            if (keep != null && keep.equals(t.getTag())) restore = t;
        }
        if (allPanel.getVisibility() == View.VISIBLE) fillAll();
        else if (restore != null) restore.requestFocus();
        else if (focused == null || focusInDock) focusFirst();
    }

    /** مربع زجاجي بالشريط: شعار خاص للتطبيقات المعروفة، وأيقونة التطبيق لغيرها. */
    private View dockTile(AppEntry app, int w, int h) {
        Glass.GlassFrame card = new Glass.GlassFrame(this, px(30));
        int k = Glyph.forPackage(app.pkg);
        if (k != 0) {
            card.addView(new Glyph(this, k), new FrameLayout.LayoutParams(px(k == Glyph.DAR ? 92 : 64), px(k == Glyph.DAR ? 92 : 64), Gravity.CENTER));
        } else {
            ImageView img = new ImageView(this);
            img.setImageDrawable(copy(app.icon));
            img.setScaleType(ImageView.ScaleType.FIT_CENTER);
            card.addView(img, new FrameLayout.LayoutParams(px(72), px(72), Gravity.CENTER));
        }
        card.setTag(app.pkg);
        tileBehaviour(card, app.label, px(30));
        card.setOnClickListener(v -> launch(app));
        card.setOnLongClickListener(v -> { toggleFavorite(app); return true; });
        return card;
    }

    private View allAppsTile(int w, int h) {
        Glass.GlassFrame card = new Glass.GlassFrame(this, px(30));
        card.addView(new Glyph(this, Glyph.GRID), new FrameLayout.LayoutParams(px(52), px(52), Gravity.CENTER));
        card.setTag(ALL);
        tileBehaviour(card, null, px(30));
        card.setOnClickListener(v -> openAll());
        return card;
    }

    /** لما يتأشر عليه: يكبر ويرتفع بنطّة ناعمة، والزجاج يفتح ويلمع، واسمه يطلع تحت الشريط. */
    private void tileBehaviour(Glass.GlassFrame card, String label, int radius) {
        card.setFocusable(true);
        card.setClickable(true);
        shadow(card, radius, px(4));
        card.setOnFocusChangeListener((v, has) -> {
            glow(card, has);
            v.animate().scaleX(has ? 1.14f : 1f).scaleY(has ? 1.14f : 1f)
                    .translationY(has ? -px(8) : 0).translationZ(has ? px(22) : 0)
                    .setDuration(200).setInterpolator(pop).start();
            if (has && v.getParent() == dock) showLabel(v, label);
        });
    }

    private void showLabel(View tile, String label) {
        String text = label != null ? label : (Prefs.arabic(this) ? "كل التطبيقات" : "All apps");
        focusLabel.setText(text);
        focusLabel.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED);
        tile.post(() -> {
            // مكان المربع بدون التكبير، حتى الاسم يبقى بالنص تحته
            float x = dockGlass.getLeft() + dock.getLeft() + tile.getLeft() + tile.getWidth() / 2f - focusLabel.getMeasuredWidth() / 2f;
            focusLabel.animate().cancel();
            focusLabel.setTranslationX(x);
            focusLabel.setAlpha(0f);
            focusLabel.animate().alpha(1f).setDuration(200).start();
        });
    }

    private void fillAll() {
        allGrid.removeAllViews();
        int gap = px(36);
        int contentW = screenW - px(240);
        int w = (contentW - gap * (GRID_COLS - 1)) / GRID_COLS;
        int h = w * 3 / 4;
        LinearLayout row = null;
        List<AppEntry> apps = sApps != null ? sApps : new ArrayList<>();
        for (int i = 0; i < apps.size(); i++) {
            if (i % GRID_COLS == 0) {
                row = new LinearLayout(this);
                row.setClipChildren(false);
                LinearLayout.LayoutParams rl = new LinearLayout.LayoutParams(-1, -2);
                rl.bottomMargin = px(32);
                allGrid.addView(row, rl);
            }
            AppEntry app = apps.get(i);
            Glass.GlassFrame card = new Glass.GlassFrame(this, px(28));
            LinearLayout in = new LinearLayout(this);
            in.setOrientation(LinearLayout.VERTICAL);
            in.setGravity(Gravity.CENTER);
            int k = Glyph.forPackage(app.pkg);
            View icon;
            if (k != 0) icon = new Glyph(this, k);
            else {
                ImageView img = new ImageView(this);
                img.setImageDrawable(copy(app.icon));
                img.setScaleType(ImageView.ScaleType.FIT_CENTER);
                icon = img;
            }
            in.addView(icon, new LinearLayout.LayoutParams(px(76), px(76)));
            TextView name = text(22, INK, false);
            name.setText(app.label);
            name.setSingleLine(true);
            name.setEllipsize(TextUtils.TruncateAt.END);
            name.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams nl = new LinearLayout.LayoutParams(-1, -2);
            nl.topMargin = px(14);
            nl.leftMargin = nl.rightMargin = px(12);
            in.addView(name, nl);
            card.addView(in, new FrameLayout.LayoutParams(-1, -1));
            card.setTag(app.pkg);
            tileBehaviour(card, app.label, px(28));
            card.setOnClickListener(v -> launch(app));
            card.setOnLongClickListener(v -> { toggleFavorite(app); return true; });
            LinearLayout.LayoutParams tl = new LinearLayout.LayoutParams(w, h);
            if (i % GRID_COLS != 0) tl.setMarginStart(gap);
            row.addView(card, tl);
        }
        if (allGrid.getChildCount() > 0) ((LinearLayout) allGrid.getChildAt(0)).getChildAt(0).requestFocus();
    }

    private void openAll() {
        allTitle.setText(Prefs.arabic(this) ? "كل التطبيقات" : "All apps");
        allPanel.setAlpha(0f);
        allPanel.setVisibility(View.VISIBLE);
        allPanel.animate().alpha(1f).setDuration(200).setInterpolator(ease).start();
        focusLabel.setAlpha(0f);
        fillAll();
    }

    private void closeAll() {
        if (allPanel.getVisibility() != View.VISIBLE) return;
        allPanel.setVisibility(View.GONE);
        allGrid.removeAllViews();
        focusFirst();
    }

    private void launch(AppEntry app) {
        Prefs.countLaunch(this, app.pkg);
        open(app.launch);
    }

    // ---------- الخلفيات ----------

    private void nextWallpaper() {
        String[] ph = PHRASES[phraseIndex++ % PHRASES.length];
        phrase.setText(ph[0]);
        phraseHint.setText(Prefs.arabic(this) ? ph[1] : ph[2]);
        phrase.setAlpha(0f);
        phrase.animate().alpha(1f).setDuration(900).start();
        // بالبداية ننزل ويا كل تبديل لحد ما يصير عدنا 30 صورة، وبعدين وحدة كل دقيقتين
        boolean fetch = !matchMode() && (feed.count() < 30 || System.currentTimeMillis() - lastFetch > 120000);
        if (fetch) lastFetch = System.currentTimeMillis();
        if (fetch) net.execute(feed::fetchOne); // التنزيل بخيط وحده، ما يأخر الصور
        pics.execute(() -> {
            Bitmap bmp = ready, blur = readyBlur;
            ready = readyBlur = null;
            if (bmp == null) { bmp = feed.next(screenW, screenH); blur = bmp != null ? Glass.Backdrop.blur(bmp) : null; }
            if (bmp == null && !matchMode()) { feed.fetchOne(); bmp = feed.next(screenW, screenH); blur = bmp != null ? Glass.Backdrop.blur(bmp) : null; }
            final Bitmap show = bmp, showBlur = blur;
            if (show != null) main.post(() -> { if (visible) crossfade(show, showBlur); });
            // نجهز الي بعدها من هسة
            Bitmap n = feed.next(screenW, screenH);
            if (n != null) { readyBlur = Glass.Backdrop.blur(n); ready = n; }
        });
    }

    /** نبدل الخلفية بنعومة (تلاشي ثانية ونص)، والزجاج يتبدل وياها. */
    private void crossfade(Bitmap next, Bitmap blurred) {
        ImageView shown = wallAOnTop ? wallA : wallB;
        ImageView hidden = wallAOnTop ? wallB : wallA;
        hidden.setImageBitmap(next);
        Glass.Backdrop.set(next, blurred);
        ObjectAnimator.ofFloat(hidden, View.ALPHA, hidden.getAlpha(), 1f).setDuration(1500).start();
        ObjectAnimator out = ObjectAnimator.ofFloat(shown, View.ALPHA, shown.getAlpha(), 0f).setDuration(1500);
        out.addListener(new android.animation.AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(android.animation.Animator a) {
                shown.setImageDrawable(null); // نفرّغ الذاكرة
            }
        });
        out.start();
        wallAOnTop = !wallAOnTop;
    }

    // ---------- الوضع الداكن، اللغة، الوايفاي، الطقس ----------

    private void applyDark(boolean animate) {
        boolean dark = Prefs.dark(this);
        Glass.Backdrop.dark = dark;
        darkGlyph.set(dark ? Glyph.SUN : Glyph.MOON);
        GradientDrawable g = new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, dark
                ? new int[]{0xB3000000, 0x8C000000, 0x8C000000, 0xB3000000}
                : new int[]{0x55000000, 0x00000000, 0x00000000, 0x40000000});
        dim.setBackground(g);
        if (animate) { dim.setAlpha(0f); dim.animate().alpha(1f).setDuration(400).start(); }
        Glass.Backdrop.invalidateAll();
        View f = getCurrentFocus();
        if (f != null && f.getParent() == topBar) f.getOnFocusChangeListener().onFocusChange(f, true);
    }

    private void applyLanguage() {
        boolean ar = Prefs.arabic(this);
        root.setLayoutDirection(ar ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        TextView ut = updateChip.findViewWithTag("upd");
        if (ut != null) ut.setText(ar ? "تحديث جديد" : "Update");
        updateDate();
        if (phraseIndex > 0) {
            String[] ph = PHRASES[(phraseIndex - 1) % PHRASES.length];
            phraseHint.setText(ar ? ph[1] : ph[2]);
        }
        if (sApps != null) showApps(sApps);
    }

    private void updateDate() {
        boolean ar = Prefs.arabic(this);
        java.util.Locale loc = ar ? new java.util.Locale("ar", "IQ") : java.util.Locale.ENGLISH;
        String d = new java.text.SimpleDateFormat(ar ? "EEEE، d MMMM" : "EEEE, d MMMM", loc).format(new java.util.Date());
        if (ar) d = toLatinDigits(d);
        dateText.setText(weather.isEmpty() ? d : d + "   " + weather);
        main.removeCallbacks(dateTick);
        main.postDelayed(dateTick, 60000);
    }

    private static String toLatinDigits(String s) {
        StringBuilder b = new StringBuilder();
        for (char ch : s.toCharArray()) b.append(ch >= '٠' && ch <= '٩' ? (char) ('0' + ch - '٠') : ch);
        return b.toString();
    }

    @SuppressWarnings("deprecation")
    private void updateWifi() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
        NetworkInfo n = cm != null ? cm.getActiveNetworkInfo() : null;
        int level;
        if (n == null || !n.isConnected()) level = -1;
        else if (n.getType() == ConnectivityManager.TYPE_WIFI) {
            WifiManager wm = (WifiManager) getApplicationContext().getSystemService(WIFI_SERVICE);
            int rssi = wm != null ? wm.getConnectionInfo().getRssi() : -50;
            level = Math.max(1, WifiManager.calculateSignalLevel(rssi, 5));
        } else level = 4; // كيبل
        wifiGlyph.level = level;
        wifiGlyph.invalidate();
    }

    /** الطقس من open-meteo (مجاني وبدون حساب)، كل ساعة، لمدينة توركو بفنلندا. */
    private void loadWeather() {
        if (System.currentTimeMillis() - lastWeather < 3600000) return;
        try {
            JSONObject j = new JSONObject(WallpaperFeed.get(
                    "https://api.open-meteo.com/v1/forecast?latitude=60.45&longitude=22.27&current=temperature_2m,weather_code"));
            JSONObject c = j.getJSONObject("current");
            int t = (int) Math.round(c.getDouble("temperature_2m"));
            int code = c.getInt("weather_code");
            lastWeather = System.currentTimeMillis();
            main.post(() -> {
                boolean ar = Prefs.arabic(this);
                weather = (ar ? "توركو " : "Turku ") + t + "° " + sky(code, ar);
                updateDate();
            });
        } catch (Exception ignored) { }
    }

    private static String sky(int code, boolean ar) {
        if (code == 0) return ar ? "صافي" : "Clear";
        if (code <= 3) return ar ? "غيوم خفيفة" : "Partly cloudy";
        if (code <= 48) return ar ? "ضباب" : "Fog";
        if (code <= 67 || (code >= 80 && code <= 82)) return ar ? "مطر" : "Rain";
        if (code <= 77) return ar ? "ثلج" : "Snow";
        return ar ? "عاصفة" : "Storm";
    }

    // ---------- السرعة ----------

    /**
     * التنظيف التلقائي: كل ما ترجع للرئيسية، نسكر التطبيقات الي ظلت شغالة بالخلفية
     * (يوتيوب، نتفلكس...) حتى ترجع الرام فاضية. دار وسبوتيفاي ما نمسهن.
     */
    private void cleanUp() {
        if (!visible || System.currentTimeMillis() - lastClean < 30000) return;
        lastClean = System.currentTimeMillis();
        kill(matchMode() ? MATCH_KEEP : KEEP);
    }

    private void kill(Set<String> keep) {
        if (sApps == null) return;
        final List<String> pkgs = new ArrayList<>();
        for (AppEntry a : sApps) if (!keep.contains(a.pkg)) pkgs.add(a.pkg);
        worker.execute(() -> {
            ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
            if (am == null) return;
            for (String p : pkgs) {
                try { am.killBackgroundProcesses(p); } catch (Exception ignored) { }
            }
        });
    }

    // ---------- وضع المباراة ----------

    private static boolean matchMode() { return System.currentTimeMillis() < matchUntil; }

    /**
     * وضع المباراة: نسكر كل شي بالخلفية (حتى سبوتيفاي)، ونوقف تنزيل الصور والطقس والتحديث،
     * ونفتح دار مباشرة. هيچ كل النت يروح للمباراة. نضغطه مرة ثانية يطفي.
     */
    private void toggleMatch() {
        boolean ar = Prefs.arabic(this);
        if (matchMode()) {
            matchUntil = 0;
            applyMatch();
            Toast.makeText(this, ar ? "طفى وضع المباراة" : "Match mode off", Toast.LENGTH_SHORT).show();
            return;
        }
        AppEntry dar = null;
        if (sApps != null) for (AppEntry a : sApps) if (a.pkg.equals(DAR)) { dar = a; break; }
        if (dar == null) {
            Toast.makeText(this, ar ? "تطبيق دار مو منصب" : "DAR is not installed", Toast.LENGTH_LONG).show();
            return;
        }
        matchUntil = System.currentTimeMillis() + MATCH_FOR;
        applyMatch();
        kill(MATCH_KEEP);
        lastClean = System.currentTimeMillis();
        Toast.makeText(this, ar ? "⚽ وضع المباراة: كل النت لدار" : "⚽ Match mode: all bandwidth to DAR", Toast.LENGTH_SHORT).show();
        launch(dar);
    }

    /** زر الكرة يصير أخضر لما وضع المباراة شغال. */
    private void applyMatch() {
        ballGlyph.tint(matchMode() ? 0xFF3DDC84 : INK);
    }

    // ---------- سرعة النت والرام ----------

    private void updateStats() {
        boolean ar = Prefs.arabic(this);
        long rx = TrafficStats.getTotalRxBytes(), now = System.currentTimeMillis();
        if (!testing && rx != TrafficStats.UNSUPPORTED) {
            if (lastRx >= 0 && now > lastRxAt) {
                double mbps = (rx - lastRx) * 8.0 / 1e6 / ((now - lastRxAt) / 1000.0);
                speedText.setText("↓ " + speed(mbps) + (ar ? " ميگابت" : " Mb/s"));
            } else if (speedText.length() == 0) speedText.setText("↓ …");
            lastRx = rx;
            lastRxAt = now;
        }
        ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
        if (am == null) return;
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        am.getMemoryInfo(mi);
        boolean low = mi.lowMemory || mi.availMem < mi.totalMem * 0.15;
        String gb = String.format(java.util.Locale.ROOT, "%.1f", mi.availMem / 1073741824.0);
        ramText.setText(ar ? "رام فاضية " + gb + " گيگا" : "Free RAM " + gb + " GB");
        ramText.setTextColor(low ? 0xFFFFB74D : 0xD9FFFFFF);
        if (low) cleanUp(); // الرام قلت: ننظف بنفسنا (مرة كل 30 ثانية بالأكثر)
    }

    private static String speed(double mbps) {
        return String.format(java.util.Locale.ROOT, mbps < 10 ? "%.1f" : "%.0f", Math.max(0, mbps));
    }

    /** فحص سرعة: ننزل لحد 25 ميگابايت أو 4 ثواني من كلاودفلير ونحسب السرعة الحقيقية. */
    private void speedTest() {
        if (testing || matchMode()) return;
        testing = true;
        boolean ar = Prefs.arabic(this);
        speedText.setText(ar ? "دا أفحص..." : "Testing...");
        net.execute(() -> {
            double mbps = -1;
            try {
                java.net.HttpURLConnection c = WallpaperFeed.open("https://speed.cloudflare.com/__down?bytes=25000000");
                long start = System.nanoTime(), got = 0;
                try (java.io.InputStream in = c.getInputStream()) {
                    byte[] b = new byte[65536];
                    for (int n; (n = in.read(b)) > 0; ) {
                        got += n;
                        if (System.nanoTime() - start > 4_000_000_000L) break;
                    }
                } finally { c.disconnect(); }
                mbps = got * 8.0 / 1e6 / ((System.nanoTime() - start) / 1e9);
            } catch (Exception ignored) { }
            final double r = mbps;
            main.post(() -> {
                testing = false;
                lastRx = -1;
                speedText.setText(r < 0 ? (ar ? "ماكو نت" : "No internet")
                        : (ar ? "السرعة " + speed(r) + " ميگابت" : "Speed " + speed(r) + " Mb/s"));
                main.removeCallbacks(statsTick);
                main.postDelayed(statsTick, 6000); // نخلي النتيجة تبين 6 ثواني
            });
        });
    }

    /** وضع العرض: بعد 3 دقايق بدون ريموت تختفي الأزرار وتبقى الصورة والساعة. */
    private void setAmbient(boolean on) {
        if (ambient == on) return;
        ambient = on;
        float a = on ? 0f : 1f;
        dockGlass.animate().alpha(a).translationY(on ? px(40) : 0).setDuration(700).start();
        focusLabel.animate().alpha(on ? 0f : focusLabel.getAlpha()).setDuration(400).start();
        for (int i = 0; i < topBar.getChildCount() - 1; i++) topBar.getChildAt(i).animate().alpha(a).setDuration(700).start();
        ((View) phrase.getParent()).animate().alpha(on ? 0.6f : 1f).setDuration(700).start();
    }

    private void toggleFavorite(AppEntry app) {
        List<String> favs = new ArrayList<>(Prefs.favorites(this));
        boolean ar = Prefs.arabic(this);
        String msg;
        if (favs.remove(app.pkg)) msg = ar ? "انشال من الرئيسية" : "Removed from Home";
        else { favs.add(app.pkg); msg = ar ? "انضاف للرئيسية" : "Added to Home"; }
        Prefs.setFavorites(this, favs);
        Toast.makeText(this, app.label + ": " + msg, Toast.LENGTH_SHORT).show();
        if (sApps != null) {
            boolean panel = allPanel.getVisibility() == View.VISIBLE;
            View f = getCurrentFocus();
            showApps(sApps);
            if (panel && f != null) f.requestFocus();
        }
    }

    private void open(Intent intent) {
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            reload();
        }
    }

    // ---------- أدوات صغيرة ----------

    private static boolean sameOrder(List<AppEntry> a, List<AppEntry> b) {
        if (a == null || a.size() != b.size()) return false;
        for (int i = 0; i < a.size(); i++) {
            if (!a.get(i).pkg.equals(b.get(i).pkg) || !a.get(i).label.equals(b.get(i).label)) return false;
        }
        return true;
    }

    private android.graphics.drawable.Drawable copy(android.graphics.drawable.Drawable d) {
        if (d == null || d.getConstantState() == null) return d;
        return d.getConstantState().newDrawable(getResources()).mutate();
    }

    private int px(float design) { return Math.round(design * u); }

    private TextView text(float size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setTextColor(color);
        t.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(size));
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    @SuppressWarnings("unused")
    private static int alpha(int c, float a) { return Color.argb(Math.round(255 * a), Color.red(c), Color.green(c), Color.blue(c)); }
}
