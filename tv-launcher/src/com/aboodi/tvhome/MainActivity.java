package com.aboodi.tvhome;

import android.animation.ArgbEvaluator;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.DecelerateInterpolator;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextClock;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * الشاشة الرئيسية بستايل آبل تي في:
 * فوگ "رف" كبير يعرض التطبيق المختار، وجوه شبكة تطبيقات تكبر لما تأشر عليها.
 * كلها عناصر أندرويد أصلية (بدون متصفح ولا مكتبات) حتى تكون خفيفة وسريعة.
 */
public class MainActivity extends Activity {
    private static final int COLS = 6;
    private static final int GROUND = 0xFF08090B;
    private static final int INK = 0xFFF5F5F7;
    private static final int INK_DIM = 0x9EF5F5F7;

    /** نخلي القائمة بالذاكرة، فلما ترجع للرئيسية تطلع فوراً بدون تحميل. */
    private static List<AppEntry> sApps;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    private float u; // وحدة القياس: 1 = بكسل وحد على شاشة 1920 عرض
    private FrameLayout root;
    private View shelfBg;
    private GradientDrawable shelfGradient;
    private ImageView shelfArt;
    private TextView shelfKicker, shelfTitle, langPill, settingsPill;
    private CalmScrollView scroll;
    private LinearLayout gridBox;
    private final List<View> tiles = new ArrayList<>();
    private int shelfColor = 0xFF1C1C1E;
    private ValueAnimator shelfAnim;
    private boolean resortOnResume;
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
    protected void onDestroy() {
        unregisterReceiver(packagesChanged);
        worker.shutdownNow();
        super.onDestroy();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (resortOnResume && sApps != null) {
            resortOnResume = false;
            List<AppEntry> copy = new ArrayList<>(sApps);
            AppLoader.sort(this, copy);
            sApps = copy;
            showApps(copy);
        }
    }

    /** زر الرئيسية بالريموت وإحنا أصلاً بالرئيسية: نرجع لأول تطبيق. */
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        goTop();
    }

    /** زر الرجوع بالرئيسية ما يطلع لمكان، بس يرجعك لفوگ. */
    @Override
    public void onBackPressed() {
        goTop();
    }

    private void goTop() {
        scroll.smoothScrollTo(0, 0);
        if (!tiles.isEmpty()) tiles.get(0).requestFocus();
    }

    // ---------- بناء الشاشة ----------

    private void buildScreen() {
        root = new FrameLayout(this);
        root.setBackgroundColor(GROUND);
        root.setClipChildren(false);

        // الرف الفوگاني: خلفية بلون التطبيق المختار + البانر مالته + اسمه
        shelfGradient = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{shelfColor, darken(shelfColor, 0.45f), GROUND});
        shelfBg = new View(this);
        shelfBg.setBackground(shelfGradient);
        root.addView(shelfBg, new FrameLayout.LayoutParams(-1, px(640)));

        shelfArt = new ImageView(this);
        shelfArt.setScaleType(ImageView.ScaleType.FIT_CENTER);
        shelfArt.setAlpha(0.95f);
        FrameLayout.LayoutParams artLp = new FrameLayout.LayoutParams(px(620), px(349), Gravity.TOP | Gravity.END);
        artLp.topMargin = px(120);
        artLp.setMarginEnd(px(110));
        roundCorners(shelfArt, px(26));
        root.addView(shelfArt, artLp);

        View fade = new View(this);
        fade.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{0x0008090B, 0xC008090B, GROUND}));
        FrameLayout.LayoutParams fadeLp = new FrameLayout.LayoutParams(-1, px(300));
        fadeLp.topMargin = px(340);
        root.addView(fade, fadeLp);

        LinearLayout shelfText = new LinearLayout(this);
        shelfText.setOrientation(LinearLayout.VERTICAL);
        shelfKicker = text(26, INK_DIM, false);
        shelfTitle = text(80, INK, true);
        shelfTitle.setMaxLines(1);
        shelfTitle.setEllipsize(TextUtils.TruncateAt.END);
        shelfText.addView(shelfKicker);
        shelfText.addView(shelfTitle);
        FrameLayout.LayoutParams stLp = new FrameLayout.LayoutParams(px(900), -2, Gravity.TOP | Gravity.START);
        stLp.topMargin = px(300);
        stLp.setMarginStart(px(110));
        root.addView(shelfText, stLp);

        // الشريط الفوگاني: الساعة + زر اللغة + زر الإعدادات
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextClock clock = new TextClock(this);
        clock.setFormat12Hour("h:mm");
        clock.setFormat24Hour("H:mm");
        clock.setTextColor(INK);
        clock.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(40));
        top.addView(clock, new LinearLayout.LayoutParams(0, -2, 1));
        langPill = pill();
        langPill.setOnClickListener(v -> {
            Prefs.setArabic(this, !Prefs.arabic(this));
            applyLanguage();
        });
        settingsPill = pill();
        settingsPill.setOnClickListener(v -> open(new Intent(Settings.ACTION_SETTINGS)));
        LinearLayout.LayoutParams pl = new LinearLayout.LayoutParams(-2, px(58));
        pl.setMarginStart(px(14));
        top.addView(langPill, pl);
        top.addView(settingsPill, new LinearLayout.LayoutParams(pl));
        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(-1, -2, Gravity.TOP);
        topLp.topMargin = px(44);
        topLp.leftMargin = topLp.rightMargin = px(110);
        root.addView(top, topLp);

        // شبكة التطبيقات: تتمرر فوگ الرف مثل آبل تي في
        scroll = new CalmScrollView(this);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        scroll.setClipChildren(false);
        scroll.setClipToPadding(false);
        gridBox = new LinearLayout(this);
        gridBox.setOrientation(LinearLayout.VERTICAL);
        gridBox.setClipChildren(false);
        scroll.addView(gridBox, new FrameLayout.LayoutParams(-1, -2));
        FrameLayout.LayoutParams sLp = new FrameLayout.LayoutParams(-1, -1);
        sLp.topMargin = px(130); // تحت الشريط الفوگاني
        root.addView(scroll, sLp);
        gridBox.setPadding(px(110), px(430), px(110), px(120));
    }

    private void reload() {
        worker.execute(() -> {
            List<AppEntry> apps = AppLoader.load(getApplicationContext());
            main.post(() -> {
                if (isDestroyed()) return;
                boolean same = sameOrder(sApps, apps);
                sApps = apps;
                if (!same || tiles.isEmpty()) showApps(apps);
            });
        });
    }

    private void showApps(List<AppEntry> apps) {
        View focused = getCurrentFocus();
        String keepPkg = focused != null && focused.getTag() instanceof AppEntry ? ((AppEntry) focused.getTag()).pkg : null;
        gridBox.removeAllViews();
        tiles.clear();

        int gap = px(44);
        int contentW = Math.round(1920 * u) - px(220);
        int cardW = (contentW - gap * (COLS - 1)) / COLS;
        int cardH = cardW * 9 / 16;

        LinearLayout row = null;
        View restore = null;
        for (int i = 0; i < apps.size(); i++) {
            if (i % COLS == 0) {
                row = new LinearLayout(this);
                row.setClipChildren(false);
                LinearLayout.LayoutParams rl = new LinearLayout.LayoutParams(-1, -2);
                rl.bottomMargin = px(36);
                gridBox.addView(row, rl);
            }
            View t = tile(apps.get(i), i / COLS, cardW, cardH);
            LinearLayout.LayoutParams tl = new LinearLayout.LayoutParams(cardW, -2);
            if (i % COLS != 0) tl.setMarginStart(gap);
            row.addView(t, tl);
            tiles.add(t);
            if (apps.get(i).pkg.equals(keepPkg)) restore = t;
        }
        if (restore == null && !tiles.isEmpty() && (!userMoved || focused == null || focused.getTag() instanceof AppEntry)) {
            restore = tiles.get(0);
        }
        if (restore != null) restore.requestFocus();
    }

    private View tile(AppEntry app, int rowIndex, int cardW, int cardH) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_HORIZONTAL);
        box.setClipChildren(false);
        box.setFocusable(true);
        box.setClickable(true);
        box.setTag(app);

        FrameLayout card = new FrameLayout(this);
        GradientDrawable bg = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{lighten(app.color, 0.18f), darken(app.color, 0.7f)});
        bg.setCornerRadius(px(22));
        card.setBackground(bg);
        card.setOutlineProvider(ViewOutlineProvider.BACKGROUND);
        card.setClipToOutline(true);
        card.setElevation(px(6));
        ImageView img = new ImageView(this);
        if (app.banner != null) {
            img.setImageDrawable(app.banner);
            img.setScaleType(ImageView.ScaleType.CENTER_CROP);
            card.addView(img, new FrameLayout.LayoutParams(-1, -1));
        } else {
            img.setImageDrawable(app.icon);
            img.setScaleType(ImageView.ScaleType.FIT_CENTER);
            card.addView(img, new FrameLayout.LayoutParams(cardH * 11 / 20, cardH * 11 / 20, Gravity.CENTER));
        }
        View shine = new View(this);
        shine.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0x47FFFFFF, 0x00FFFFFF, 0x00FFFFFF}));
        shine.setAlpha(0f);
        card.addView(shine, new FrameLayout.LayoutParams(-1, -1));
        box.addView(card, new LinearLayout.LayoutParams(cardW, cardH));

        TextView label = text(24, INK, false);
        label.setText(app.label);
        label.setSingleLine(true);
        label.setEllipsize(TextUtils.TruncateAt.END);
        label.setGravity(Gravity.CENTER);
        label.setAlpha(0f);
        LinearLayout.LayoutParams ll = new LinearLayout.LayoutParams(-1, -2);
        ll.topMargin = px(14);
        box.addView(label, ll);

        DecelerateInterpolator ease = new DecelerateInterpolator(2f);
        box.setOnFocusChangeListener((v, has) -> {
            card.animate().scaleX(has ? 1.15f : 1f).scaleY(has ? 1.15f : 1f)
                    .translationY(has ? -px(6) : 0).translationZ(has ? px(28) : 0)
                    .setDuration(150).setInterpolator(ease).start();
            shine.animate().alpha(has ? 1f : 0f).setDuration(150).start();
            label.animate().alpha(has ? 1f : 0f).translationY(has ? px(10) : 0).setDuration(150).start();
            if (has) {
                showOnShelf(app);
                View rowView = (View) v.getParent();
                scroll.smoothScrollTo(0, rowIndex <= 1 ? 0 : rowView.getTop() - gridBox.getChildAt(1).getTop());
            }
        });
        box.setOnClickListener(v -> {
            Prefs.countLaunch(this, app.pkg);
            resortOnResume = true;
            open(app.launch);
        });
        // ضغطة طويلة: صفحة معلومات التطبيق (منها تحذفه أو توقفه)
        box.setOnLongClickListener(v -> {
            open(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + app.pkg))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            return true;
        });
        return box;
    }

    private void showOnShelf(AppEntry app) {
        shelfTitle.setText(app.label);
        shelfArt.setImageDrawable(app.banner != null ? app.banner : app.icon);
        shelfArt.setScaleType(app.banner != null ? ImageView.ScaleType.CENTER_CROP : ImageView.ScaleType.FIT_CENTER);
        shelfArt.setBackground(app.banner != null ? null : roundRect(darken(app.color, 0.8f), px(26)));
        if (shelfAnim != null) shelfAnim.cancel();
        int from = shelfColor, to = app.color;
        shelfAnim = ValueAnimator.ofObject(new ArgbEvaluator(), from, to);
        shelfAnim.setDuration(260);
        shelfAnim.addUpdateListener(a -> {
            shelfColor = (int) a.getAnimatedValue();
            shelfGradient.setColors(new int[]{shelfColor, darken(shelfColor, 0.45f), GROUND});
        });
        shelfAnim.start();
    }

    private void applyLanguage() {
        boolean ar = Prefs.arabic(this);
        root.setLayoutDirection(ar ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        langPill.setText(ar ? "English" : "عربي");
        settingsPill.setText(ar ? "الإعدادات" : "Settings");
        shelfKicker.setText(ar ? "اضغط OK حتى تفتح" : "Press OK to open");
    }

    private void open(Intent intent) {
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            // التطبيق انحذف أو ما يقبل ينفتح: نحدّث القائمة
            reload();
        }
    }

    @Override
    public boolean dispatchKeyEvent(android.view.KeyEvent e) {
        userMoved = true;
        return super.dispatchKeyEvent(e);
    }

    private static boolean sameOrder(List<AppEntry> a, List<AppEntry> b) {
        if (a == null || a.size() != b.size()) return false;
        for (int i = 0; i < a.size(); i++) {
            if (!a.get(i).pkg.equals(b.get(i).pkg) || !a.get(i).label.equals(b.get(i).label)) return false;
        }
        return true;
    }

    // ---------- أدوات صغيرة ----------

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
        s.addState(new int[]{android.R.attr.state_focused}, roundRect(INK, px(29)));
        s.addState(new int[]{}, roundRect(0x24FFFFFF, px(29)));
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

    private static void roundCorners(View v, int radius) {
        v.setOutlineProvider(new ViewOutlineProvider() {
            @Override public void getOutline(View view, android.graphics.Outline o) {
                o.setRoundRect(0, 0, view.getWidth(), view.getHeight(), radius);
            }
        });
        v.setClipToOutline(true);
    }

    private static int darken(int c, float k) {
        return Color.rgb(Math.round(Color.red(c) * k), Math.round(Color.green(c) * k), Math.round(Color.blue(c) * k));
    }

    private static int lighten(int c, float k) {
        return Color.rgb(Color.red(c) + Math.round((255 - Color.red(c)) * k),
                Color.green(c) + Math.round((255 - Color.green(c)) * k),
                Color.blue(c) + Math.round((255 - Color.blue(c)) * k));
    }

    /** سكرول ما يتحرك وحده لما يتغير التركيز؛ إحنا نحركه بهدوء من الكود. */
    static final class CalmScrollView extends android.widget.ScrollView {
        CalmScrollView(Context c) { super(c); }

        @Override
        protected int computeScrollDeltaToGetChildRectOnScreen(android.graphics.Rect rect) { return 0; }
    }
}
