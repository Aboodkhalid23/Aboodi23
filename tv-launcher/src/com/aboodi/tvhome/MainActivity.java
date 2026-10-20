package com.aboodi.tvhome;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
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
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextClock;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * الشاشة الرئيسية بستايل آبل تي في:
 * خلفية ضبابية بلون التطبيق المختار، واسمه كبير، وجوه صف واحد من تطبيقاتك المفضلة بس.
 * "كل التطبيقات" تفتح شبكة بباقي التطبيقات. كلها عناصر أندرويد أصلية، خفيفة وسريعة.
 */
public class MainActivity extends Activity {
    private static final int GRID_COLS = 6;
    private static final int INK = 0xFFF5F5F7;
    private static final int INK_DIM = 0xA6F5F5F7;
    private static final String ALL = "@all";

    /** نخلي القائمة بالذاكرة، فلما ترجع للرئيسية تطلع فوراً بدون تحميل. */
    private static List<AppEntry> sApps;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final DecelerateInterpolator ease = new DecelerateInterpolator(2f);

    private float u; // وحدة القياس: 1 = بكسل وحد على شاشة 1920 عرض
    private FrameLayout root;
    private ImageView wallA, wallB; // خلفيتين نبدل بيناتهن بنعومة
    private boolean wallAOnTop = true;
    private TextView heroTitle, heroHint, langPill, settingsPill;
    private LinearLayout dock;
    private FrameLayout allPanel;
    private LinearLayout allGrid;
    private TextView allTitle;
    private WallpaperFeed feed;
    private final ExecutorService net = Executors.newSingleThreadExecutor(); // تنزيل الصور بخيط وحده
    private boolean visible;
    private int phraseIndex;
    private long lastFetch;

    /** كلمات يابانية تتبدل ويا الصور: الكتابة، النطق، والمعنى. */
    private static final String[][] PHRASES = {
            {"東京", "Tōkyō", "طوكيو", "Tokyo"},
            {"夜の街", "Yoru no machi", "مدينة الليل", "City at night"},
            {"桜", "Sakura", "زهرة الكرز", "Cherry blossom"},
            {"夢", "Yume", "حلم", "Dream"},
            {"侍", "Samurai", "ساموراي", "Samurai"},
            {"一期一会", "Ichigo ichie", "كل لقاء يصير مرة وحدة بالعمر", "Once in a lifetime"},
            {"頑張って", "Ganbatte", "شد حيلك", "Keep going"},
            {"七転び八起き", "Nana korobi ya oki", "توگع سبع مرات وتگوم ثمانية", "Fall seven, rise eight"},
            {"静けさ", "Shizukesa", "الهدوء", "Stillness"},
            {"光", "Hikari", "ضوء", "Light"},
            {"富士山", "Fujisan", "جبل فوجي", "Mount Fuji"},
            {"ありがとう", "Arigatō", "شكراً", "Thank you"},
    };

    private final Runnable rotate = new Runnable() {
        @Override public void run() {
            if (!visible) return;
            nextWallpaper();
            main.postDelayed(this, 25000); // صورة جديدة كل 25 ثانية
        }
    };
    private boolean userMoved; // المستخدم ضغط شي بالريموت؟

    private final BroadcastReceiver packagesChanged = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { reload(); }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Window w = getWindow();
        w.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        w.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);

        DisplayMetrics dm = getResources().getDisplayMetrics();
        u = Math.max(dm.widthPixels, dm.heightPixels) / 1920f;

        buildScreen();
        applyLanguage();
        setContentView(root);

        if (sApps != null) showApps(sApps);
        reload();

        IntentFilter f = new IntentFilter();
        f.addAction(Intent.ACTION_PACKAGE_ADDED);
        f.addAction(Intent.ACTION_PACKAGE_REMOVED);
        f.addAction(Intent.ACTION_PACKAGE_CHANGED);
        f.addDataScheme("package");
        registerReceiver(packagesChanged, f);
    }

    @Override
    protected void onResume() {
        super.onResume();
        visible = true;
        main.removeCallbacks(rotate);
        main.post(rotate);
    }

    /** أول ما يفتح تطبيق ثاني (مباراة، نتفلكس): نوقف كلشي، ولا بايت نت. */
    @Override
    protected void onPause() {
        visible = false;
        main.removeCallbacks(rotate);
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        unregisterReceiver(packagesChanged);
        worker.shutdownNow();
        net.shutdownNow();
        super.onDestroy();
    }

    /** زر الرئيسية بالريموت وإحنا أصلاً بالرئيسية: نسد "كل التطبيقات" ونرجع لأول تطبيق. */
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        closeAll();
        focusFirst();
    }

    /** زر الرجوع: يسد "كل التطبيقات" إذا مفتوحة، وغير هيچ ما يسوي شي. */
    @Override
    public void onBackPressed() {
        if (allPanel.getVisibility() == View.VISIBLE) closeAll();
        else focusFirst();
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        userMoved = true;
        return super.dispatchKeyEvent(e);
    }

    private void focusFirst() {
        if (dock.getChildCount() > 0) dock.getChildAt(0).requestFocus();
    }

    // ---------- بناء الشاشة ----------

    private void buildScreen() {
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        // الخلفية: صور اليابان تتبدل وتتحرك ببطء
        feed = new WallpaperFeed(this);
        root.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{0xFF0B1530, 0xFF1B2C55, 0xFF3D4F7C})); // لحد ما توصل أول صورة
        wallA = wallView();
        wallB = wallView();
        wallB.setAlpha(0f);
        root.addView(wallB, new FrameLayout.LayoutParams(-1, -1));
        root.addView(wallA, new FrameLayout.LayoutParams(-1, -1));
        View dim = new View(this);
        dim.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{0x8C000000, 0x14000000, 0x00000000, 0x33000000, 0xD9000000}));
        root.addView(dim, new FrameLayout.LayoutParams(-1, -1));

        // كلمة يابانية كبيرة ويا نطقها ومعناها
        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        heroTitle = text(110, INK, false);
        heroTitle.setTypeface(Typeface.create("sans-serif-light", Typeface.NORMAL));
        heroTitle.setShadowLayer(px(30), 0, px(4), 0x99000000);
        heroHint = text(30, INK_DIM, false);
        heroHint.setShadowLayer(px(16), 0, px(2), 0x99000000);
        hero.addView(heroTitle);
        hero.addView(heroHint);
        FrameLayout.LayoutParams hLp = new FrameLayout.LayoutParams(px(1300), -2, Gravity.TOP | Gravity.START);
        hLp.topMargin = px(150);
        hLp.setMarginStart(px(120));
        root.addView(hero, hLp);

        TextView credit = text(18, 0x80FFFFFF, false);
        credit.setText("Wikimedia Commons");
        FrameLayout.LayoutParams cLp = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.END);
        cLp.bottomMargin = px(36);
        cLp.setMarginEnd(px(120));
        root.addView(credit, cLp);

        // فوگ: الساعة + اللغة + الإعدادات
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextClock clock = new TextClock(this);
        clock.setFormat12Hour("h:mm");
        clock.setFormat24Hour("H:mm");
        clock.setTextColor(INK);
        clock.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(40));
        clock.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        top.addView(clock, new LinearLayout.LayoutParams(0, -2, 1));
        langPill = pill();
        langPill.setOnClickListener(v -> {
            Prefs.setArabic(this, !Prefs.arabic(this));
            applyLanguage();
        });
        settingsPill = pill();
        settingsPill.setOnClickListener(v -> open(new Intent(Settings.ACTION_SETTINGS)));
        LinearLayout.LayoutParams pl = new LinearLayout.LayoutParams(-2, px(56));
        pl.setMarginStart(px(14));
        top.addView(langPill, pl);
        top.addView(settingsPill, new LinearLayout.LayoutParams(pl));
        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(-1, -2, Gravity.TOP);
        topLp.topMargin = px(48);
        topLp.leftMargin = topLp.rightMargin = px(120);
        root.addView(top, topLp);

        // الصف: تطبيقاتك المفضلة بس، كبار
        dock = new LinearLayout(this);
        dock.setClipChildren(false);
        dock.setPadding(px(120), px(40), px(120), px(40));
        android.widget.HorizontalScrollView dockScroll = new android.widget.HorizontalScrollView(this);
        dockScroll.setHorizontalScrollBarEnabled(false);
        dockScroll.setClipChildren(false);
        dockScroll.setClipToPadding(false);
        dockScroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        dockScroll.addView(dock, new FrameLayout.LayoutParams(-2, -2));
        FrameLayout.LayoutParams dLp = new FrameLayout.LayoutParams(-1, -2, Gravity.TOP);
        dLp.topMargin = px(780);
        root.addView(dockScroll, dLp);
        root.setClipChildren(false);

        // لوحة "كل التطبيقات"
        allPanel = new FrameLayout(this);
        allPanel.setBackgroundColor(0xF20B0B0D);
        allPanel.setVisibility(View.GONE);
        allTitle = text(48, INK, true);
        FrameLayout.LayoutParams atLp = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.START);
        atLp.topMargin = px(56);
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
        dock.removeAllViews();

        int tileW = px(250), tileH = px(150), gap = px(40);
        View restore = null;
        List<AppEntry> favs = favorites(apps);
        for (int i = 0; i <= favs.size(); i++) {
            AppEntry app = i < favs.size() ? favs.get(i) : null; // الأخير = كل التطبيقات
            View t = app != null ? tile(app, tileW, tileH, 24, true) : allAppsTile(tileW, tileH);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(tileW, -2);
            if (i > 0) lp.setMarginStart(gap);
            dock.addView(t, lp);
            if (keep != null && keep.equals(t.getTag())) restore = t;
        }
        if (allPanel.getVisibility() == View.VISIBLE) fillAll();
        else if (restore != null) restore.requestFocus();
        else if (!userMoved || focused == null) focusFirst();
    }

    private void fillAll() {
        allGrid.removeAllViews();
        int gap = px(40);
        int contentW = Math.round(1920 * u) - px(240);
        int w = (contentW - gap * (GRID_COLS - 1)) / GRID_COLS;
        int h = w * 3 / 5;
        LinearLayout row = null;
        List<AppEntry> apps = sApps != null ? sApps : new ArrayList<>();
        for (int i = 0; i < apps.size(); i++) {
            if (i % GRID_COLS == 0) {
                row = new LinearLayout(this);
                row.setClipChildren(false);
                LinearLayout.LayoutParams rl = new LinearLayout.LayoutParams(-1, -2);
                rl.bottomMargin = px(30);
                allGrid.addView(row, rl);
            }
            View t = tile(apps.get(i), w, h, 24, false);
            LinearLayout.LayoutParams tl = new LinearLayout.LayoutParams(w, -2);
            if (i % GRID_COLS != 0) tl.setMarginStart(gap);
            row.addView(t, tl);
        }
        if (allGrid.getChildCount() > 0) ((LinearLayout) allGrid.getChildAt(0)).getChildAt(0).requestFocus();
    }

    private void openAll() {
        allTitle.setText(Prefs.arabic(this) ? "كل التطبيقات" : "All apps");
        allPanel.setAlpha(0f);
        allPanel.setVisibility(View.VISIBLE);
        allPanel.animate().alpha(1f).setDuration(160).start();
        fillAll();
    }

    private void closeAll() {
        if (allPanel.getVisibility() != View.VISIBLE) return;
        allPanel.setVisibility(View.GONE);
        allGrid.removeAllViews();
        focusFirst();
    }

    /** مربع تطبيق: صورته العريضة إذا عنده، وإلا أيقونته على لونه. */
    private View tile(AppEntry app, int w, int h, float labelSize, boolean onHome) {
        FrameLayout card = new FrameLayout(this);
        GradientDrawable bg = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{lighten(app.color, 0.15f), darken(app.color, 0.65f)});
        bg.setCornerRadius(px(onHome ? 26 : 20));
        card.setBackground(bg);
        ImageView img = new ImageView(this);
        if (app.banner != null) {
            img.setImageDrawable(copy(app.banner));
            img.setScaleType(ImageView.ScaleType.CENTER_CROP);
            card.addView(img, new FrameLayout.LayoutParams(-1, -1));
        } else {
            img.setImageDrawable(copy(app.icon));
            img.setScaleType(ImageView.ScaleType.FIT_CENTER);
            card.addView(img, new FrameLayout.LayoutParams(h * 3 / 5, h * 3 / 5, Gravity.CENTER));
        }
        View box = wrap(card, w, h, app.label, labelSize);
        box.setTag(app.pkg);
        box.setOnFocusChangeListener((v, has) -> {
            lift(v, has);
        });
        box.setOnClickListener(v -> {
            Prefs.countLaunch(this, app.pkg);
            open(app.launch);
        });
        // ضغطة طويلة: بالرئيسية تشيله منها، وبكل التطبيقات تضيفه للرئيسية
        box.setOnLongClickListener(v -> {
            toggleFavorite(app);
            return true;
        });
        return box;
    }

    private View allAppsTile(int w, int h) {
        FrameLayout card = new FrameLayout(this);
        card.setBackground(roundRect(0x33FFFFFF, px(26)));
        GridGlyph glyph = new GridGlyph(this, px(14));
        card.addView(glyph, new FrameLayout.LayoutParams(h * 2 / 5, h * 2 / 5, Gravity.CENTER));
        View box = wrap(card, w, h, Prefs.arabic(this) ? "كل التطبيقات" : "All apps", 24);
        box.setTag(ALL);
        box.setOnFocusChangeListener((v, has) -> {
            lift(v, has);
        });
        box.setOnClickListener(v -> openAll());
        return box;
    }

    /** يلف المربع ويا اسمه تحته، ويخليه يتأشر عليه بالريموت. */
    private View wrap(FrameLayout card, int w, int h, String label, float labelSize) {
        card.setOutlineProvider(ViewOutlineProvider.BACKGROUND);
        card.setClipToOutline(true);
        card.setElevation(px(8));
        View shine = new View(this);
        shine.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0x40FFFFFF, 0x00FFFFFF, 0x00FFFFFF}));
        shine.setAlpha(0f);
        card.addView(shine, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_HORIZONTAL);
        box.setClipChildren(false);
        box.setFocusable(true);
        box.setClickable(true);
        box.addView(card, new LinearLayout.LayoutParams(w, h));
        TextView name = text(labelSize, INK, false);
        name.setText(label);
        name.setSingleLine(true);
        name.setEllipsize(TextUtils.TruncateAt.END);
        name.setGravity(Gravity.CENTER);
        name.setAlpha(0f);
        LinearLayout.LayoutParams nl = new LinearLayout.LayoutParams(-1, -2);
        nl.topMargin = px(18);
        box.addView(name, nl);
        return box;
    }

    /** لما يتأشر عليه: يكبر ويرتفع ويطلع اسمه، مثل آبل تي في. */
    private void lift(View box, boolean has) {
        View card = ((LinearLayout) box).getChildAt(0);
        View shine = ((FrameLayout) card).getChildAt(((FrameLayout) card).getChildCount() - 1);
        View name = ((LinearLayout) box).getChildAt(1);
        card.animate().scaleX(has ? 1.12f : 1f).scaleY(has ? 1.12f : 1f)
                .translationZ(has ? px(30) : 0).setDuration(160).setInterpolator(ease).start();
        shine.animate().alpha(has ? 1f : 0f).setDuration(160).start();
        name.animate().alpha(has ? 1f : 0f).translationY(has ? px(12) : 0).setDuration(160).start();
    }

    /** الصورة الجاية: نقراها بخيط جانبي، وننزل وحدة جديدة كل دقيقتين إذا الشاشة مفتوحة. */
    private void nextWallpaper() {
        String[] ph = PHRASES[phraseIndex++ % PHRASES.length];
        boolean ar = Prefs.arabic(this);
        heroTitle.setText(ph[0]);
        heroHint.setText(ph[1] + "  ·  " + (ar ? ph[2] : ph[3]));
        heroTitle.setAlpha(0f);
        heroTitle.animate().alpha(1f).setDuration(900).start();
        int maxW = getResources().getDisplayMetrics().widthPixels;
        boolean fetch = System.currentTimeMillis() - lastFetch > 120000;
        if (fetch) lastFetch = System.currentTimeMillis();
        net.execute(() -> {
            android.graphics.Bitmap bmp = feed.next(maxW);
            if (bmp == null) { feed.fetchOne(); bmp = feed.next(maxW); } // أول مرة
            else if (fetch) feed.fetchOne();
            final android.graphics.Bitmap show = bmp;
            if (show != null) main.post(() -> { if (visible) crossfade(show); });
        });
    }

    /** نبدل الخلفية بنعومة، والجديدة تتقرب ببطء (حركة مثل الأفلام الوثائقية). */
    private void crossfade(android.graphics.Bitmap next) {
        ImageView shown = wallAOnTop ? wallA : wallB;
        ImageView hidden = wallAOnTop ? wallB : wallA;
        hidden.animate().cancel();
        hidden.setImageBitmap(next);
        hidden.setScaleX(1f);
        hidden.setScaleY(1f);
        hidden.setTranslationX(0);
        boolean left = phraseIndex % 2 == 0;
        android.animation.ObjectAnimator.ofFloat(hidden, View.ALPHA, hidden.getAlpha(), 1f).setDuration(1200).start();
        hidden.animate().scaleX(1.12f).scaleY(1.12f).translationX(px(left ? -60 : 60))
                .setDuration(26000).setInterpolator(new android.view.animation.LinearInterpolator()).withLayer().start();
        android.animation.ObjectAnimator out = android.animation.ObjectAnimator.ofFloat(shown, View.ALPHA, shown.getAlpha(), 0f);
        out.setDuration(1200);
        out.addListener(new android.animation.AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(android.animation.Animator a) {
                shown.animate().cancel();
                shown.setImageDrawable(null); // نفرّغ الذاكرة
            }
        });
        out.start();
        wallAOnTop = !wallAOnTop;
    }

    private void toggleFavorite(AppEntry app) {
        List<String> favs = new ArrayList<>(Prefs.favorites(this));
        boolean ar = Prefs.arabic(this);
        String msg;
        if (favs.remove(app.pkg)) {
            msg = ar ? "انشال من الرئيسية" : "Removed from Home";
        } else {
            favs.add(app.pkg);
            msg = ar ? "انضاف للرئيسية" : "Added to Home";
        }
        Prefs.setFavorites(this, favs);
        Toast.makeText(this, app.label + ": " + msg, Toast.LENGTH_SHORT).show();
        if (sApps != null) {
            boolean panel = allPanel.getVisibility() == View.VISIBLE;
            View f = getCurrentFocus();
            showApps(sApps);
            if (panel && f != null) f.requestFocus();
        }
    }

    private void applyLanguage() {
        boolean ar = Prefs.arabic(this);
        root.setLayoutDirection(ar ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        langPill.setText(ar ? "English" : "عربي");
        settingsPill.setText(ar ? "الإعدادات" : "Settings");
        if (sApps != null) showApps(sApps);
    }

    private void open(Intent intent) {
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            reload(); // التطبيق انحذف أو ما يقبل ينفتح: نحدّث القائمة
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

    /** كل صورة تنرسم بأكثر من مكان لازم نسخة خاصة بيها. */
    private Drawable copy(Drawable d) {
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

    private TextView pill() {
        TextView p = text(24, INK, true);
        p.setGravity(Gravity.CENTER);
        p.setPadding(px(26), 0, px(26), 0);
        p.setFocusable(true);
        p.setClickable(true);
        StateListDrawable s = new StateListDrawable();
        s.addState(new int[]{android.R.attr.state_focused}, roundRect(INK, px(28)));
        s.addState(new int[]{}, roundRect(0x2EFFFFFF, px(28)));
        p.setBackground(s);
        p.setTextColor(new ColorStateList(
                new int[][]{{android.R.attr.state_focused}, {}},
                new int[]{Color.BLACK, INK}));
        p.setOnFocusChangeListener((v, has) ->
                v.animate().scaleX(has ? 1.1f : 1f).scaleY(has ? 1.1f : 1f).setDuration(120).start());
        return p;
    }

    private static GradientDrawable roundRect(int color, float radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(radius);
        return d;
    }

    private static int darken(int c, float k) {
        return Color.rgb(Math.round(Color.red(c) * k), Math.round(Color.green(c) * k), Math.round(Color.blue(c) * k));
    }

    private static int lighten(int c, float k) {
        return Color.rgb(Color.red(c) + Math.round((255 - Color.red(c)) * k),
                Color.green(c) + Math.round((255 - Color.green(c)) * k),
                Color.blue(c) + Math.round((255 - Color.blue(c)) * k));
    }

    /** أيقونة "كل التطبيقات": 9 مربعات صغيرة. */
    static final class GridGlyph extends View {
        private final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final float r;

        GridGlyph(Context c, float radius) {
            super(c);
            r = radius;
            paint.setColor(INK);
        }

        @Override
        protected void onDraw(android.graphics.Canvas c) {
            float cell = getWidth() / 3f, pad = cell * 0.14f;
            for (int y = 0; y < 3; y++) {
                for (int x = 0; x < 3; x++) {
                    c.drawRoundRect(x * cell + pad, y * cell + pad, (x + 1) * cell - pad, (y + 1) * cell - pad, r / 2, r / 2, paint);
                }
            }
        }
    }
}
