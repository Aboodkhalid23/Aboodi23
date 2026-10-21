package com.aboodi.tvhome;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * صفحة المباريات: تفتحها من الشريط، تختار اليوم، وتشوف مباريات دورياتك وفرقك بتوقيت التلفزيون.
 * تضغط على اسم فريق = يصير من "فرقي" (⭐) ومبارياته تطلع أول شي. "دورياتي" = تختار الدوريات.
 * المصدر: نتائج ESPN المجانية، وتنجاب بس لما تفتح الصفحة (ولا بايت نت بغير وكت).
 */
final class Matches {
    private static final String API = "https://site.api.espn.com/apis/site/v2/sports/soccer/";

    /** الدوريات والبطولات الي تگدر تختارها: الرمز، الاسم بالعربي، الاسم بالإنگليزي. */
    static final String[][] LEAGUES = {
            {"uefa.champions", "دوري أبطال أوروبا", "Champions League"},
            {"eng.1", "الدوري الإنگليزي", "Premier League"},
            {"esp.1", "الدوري الإسباني", "LaLiga"},
            {"ita.1", "الدوري الإيطالي", "Serie A"},
            {"ger.1", "الدوري الألماني", "Bundesliga"},
            {"fra.1", "الدوري الفرنسي", "Ligue 1"},
            {"ksa.1", "الدوري السعودي", "Saudi Pro League"},
            {"uefa.europa", "الدوري الأوروبي", "Europa League"},
            {"uefa.europa.conf", "دوري المؤتمر الأوروبي", "Conference League"},
            {"afc.champions", "دوري أبطال آسيا", "AFC Champions League"},
            {"fifa.world", "كأس العالم", "World Cup"},
            {"fifa.worldq.afc", "تصفيات كأس العالم: آسيا", "WC Qualifiers: Asia"},
            {"fifa.worldq.uefa", "تصفيات كأس العالم: أوروبا", "WC Qualifiers: Europe"},
            {"afc.asian.cup", "كأس آسيا", "Asian Cup"},
            {"uefa.euro", "بطولة أوروبا", "Euro"},
            {"uefa.nations", "دوري الأمم الأوروبية", "Nations League"},
            {"conmebol.america", "كوبا أمريكا", "Copa América"},
            {"fifa.cwc", "كأس العالم للأندية", "Club World Cup"},
            {"fifa.friendly", "مباريات ودية دولية", "International friendlies"},
            {"eng.fa", "كأس الاتحاد الإنگليزي", "FA Cup"},
            {"eng.league_cup", "كأس الرابطة الإنگليزية", "Carabao Cup"},
            {"esp.copa_del_rey", "كأس ملك إسبانيا", "Copa del Rey"},
            {"ita.coppa_italia", "كأس إيطاليا", "Coppa Italia"},
            {"ger.dfb_pokal", "كأس ألمانيا", "DFB Pokal"},
            {"ned.1", "الدوري الهولندي", "Eredivisie"},
            {"por.1", "الدوري البرتغالي", "Primeira Liga"},
            {"tur.1", "الدوري التركي", "Super Lig"},
            {"fin.1", "الدوري الفنلندي", "Veikkausliiga"},
    };

    static final String DEFAULT_LEAGUES = "uefa.champions,eng.1,esp.1,ita.1,ger.1,fra.1,ksa.1,uefa.europa,"
            + "fifa.world,fifa.worldq.afc,fifa.worldq.uefa,afc.asian.cup,uefa.nations,fifa.friendly";

    private final Activity a;
    private final float u;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService pool = Executors.newFixedThreadPool(4);
    final Glass.GlassFrame panel;
    private final LinearLayout list, dayBar;
    private final TextView title;
    private final ScrollView scroll;
    private int day; // 0 = اليوم، 1 = باچر، 2 = بعد باچر، -1 = أمس
    private boolean settings;
    private int generation; // حتى نتايج طلب قديم ما تخربط الجديد

    private static final class Game {
        String id, league, homeId, homeName, awayId, awayName, homeScore, awayScore, state, clock;
        long time;
    }

    private final Runnable liveTick = new Runnable() {
        @Override public void run() { if (visible() && !settings) load(false); }
    };

    Matches(Activity act, float unit) {
        a = act;
        u = unit;
        panel = new Glass.GlassFrame(a, 0);
        panel.setVisibility(View.GONE);
        View shade = new View(a);
        shade.setBackgroundColor(0x8C000000);
        panel.addView(shade, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout col = new LinearLayout(a);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(px(120), px(56), px(120), 0);
        LinearLayout head = new LinearLayout(a);
        head.setGravity(Gravity.CENTER_VERTICAL);
        title = text(46, 0xFFFFFFFF, true);
        head.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
        dayBar = new LinearLayout(a);
        dayBar.setClipChildren(false);
        head.addView(dayBar);
        col.addView(head);

        scroll = new ScrollView(a);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.setClipToPadding(false);
        list = new LinearLayout(a);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(px(10), px(30), px(10), px(140));
        list.setClipChildren(false);
        scroll.addView(list, new FrameLayout.LayoutParams(-1, -2));
        col.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        panel.addView(col, new FrameLayout.LayoutParams(-1, -1));
    }

    boolean visible() { return panel.getVisibility() == View.VISIBLE; }

    void open() {
        day = 0;
        settings = false;
        panel.setAlpha(0f);
        panel.setVisibility(View.VISIBLE);
        panel.animate().alpha(1f).setDuration(200).start();
        buildDayBar();
        load(true);
    }

    /** زر الرجوع: من الإعدادات للمباريات، ومن المباريات للرئيسية. يرجع true إذا الصفحة لساتها مفتوحة. */
    boolean back() {
        if (settings) { settings = false; buildDayBar(); load(true); return true; }
        close();
        return false;
    }

    void close() {
        main.removeCallbacks(liveTick);
        generation++;
        panel.setVisibility(View.GONE);
        list.removeAllViews();
    }

    // ---------- الأزرار فوگ ----------

    private void buildDayBar() {
        boolean ar = Prefs.arabic(a);
        title.setText(settings ? (ar ? "دورياتي" : "My leagues") : (ar ? "المباريات" : "Matches"));
        dayBar.removeAllViews();
        if (!settings) {
            String[] names = ar ? new String[]{"أمس", "اليوم", "باچر", "بعد باچر"} : new String[]{"Yesterday", "Today", "Tomorrow", "After"};
            for (int i = -1; i <= 2; i++) {
                final int d = i;
                TextView b = pill(names[i + 1], d == day);
                b.setOnClickListener(v -> { Sound.press(); day = d; buildDayBar(); load(true); dayBar.getChildAt(d + 1).requestFocus(); });
                addBar(b);
            }
        }
        TextView s = pill(settings ? (ar ? "رجوع" : "Back") : (ar ? "⚙ دورياتي" : "⚙ My leagues"), false);
        s.setOnClickListener(v -> { Sound.press(); if (settings) back(); else { settings = true; buildDayBar(); showSettings(); } });
        addBar(s);
    }

    private void addBar(View v) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, px(64));
        lp.setMarginStart(px(14));
        dayBar.addView(v, lp);
    }

    // ---------- جلب المباريات ----------

    private void load(boolean showLoading) {
        main.removeCallbacks(liveTick);
        final int gen = ++generation;
        boolean ar = Prefs.arabic(a);
        if (showLoading) message(ar ? "دا أجيب المباريات..." : "Loading matches...");
        final Set<String> picked = leagues(a);
        final Map<String, String[]> favs = favTeams(a);
        final Set<String> slugs = new HashSet<>(picked);
        for (String[] f : favs.values()) if (f.length > 2 && !f[2].isEmpty()) slugs.add(f[2]);
        final long[] range = dayRange(day);
        SimpleDateFormat q = new SimpleDateFormat("yyyyMMdd", Locale.ROOT);
        q.setTimeZone(TimeZone.getTimeZone("America/New_York")); // ESPN يقسّم الأيام بتوقيت أمريكا
        final Set<String> dates = new HashSet<>(); // يوم التلفزيون ممكن يغطي يومين بتوقيت أمريكا
        dates.add(q.format(new Date(range[0])));
        dates.add(q.format(new Date(range[1] - 1)));
        pool.execute(() -> {
            List<Future<List<Game>>> jobs = new ArrayList<>();
            for (String slug : slugs) for (String dt : dates) jobs.add(pool.submit(() -> fetch(slug, dt)));
            List<Future<List<Game>>> alls = new ArrayList<>();
            if (!favs.isEmpty()) for (String dt : dates) alls.add(pool.submit(() -> fetch("all", dt)));
            Map<String, Game> games = new LinkedHashMap<>();
            boolean failed = true;
            for (Future<List<Game>> f : jobs) {
                try { for (Game g : f.get()) { games.put(g.id, g); } failed = false; } catch (Exception ignored) { }
            }
            for (Future<List<Game>> all : alls) {
                try {
                    for (Game g : all.get()) {
                        failed = false;
                        if (!games.containsKey(g.id) && (favs.containsKey(g.homeId) || favs.containsKey(g.awayId))) games.put(g.id, g);
                    }
                } catch (Exception ignored) { }
            }
            List<Game> out = new ArrayList<>();
            for (Game g : games.values()) if (g.time >= range[0] && g.time < range[1]) out.add(g);
            Collections.sort(out, (x, y) -> Long.compare(x.time, y.time));
            final boolean bad = failed && !slugs.isEmpty();
            main.post(() -> { if (gen == generation && visible() && !settings) show(out, picked, favs, bad); });
        });
    }

    private static List<Game> fetch(String slug, String date) throws Exception {
        JSONObject d = new JSONObject(WallpaperFeed.get(API + slug + "/scoreboard?limit=200&dates=" + date));
        JSONArray ev = d.optJSONArray("events");
        List<Game> out = new ArrayList<>();
        if (ev == null) return out;
        for (int i = 0; i < ev.length(); i++) {
            try {
                JSONObject e = ev.getJSONObject(i);
                JSONObject c = e.getJSONArray("competitions").getJSONObject(0);
                Game g = new Game();
                g.id = e.getString("id");
                g.league = slug;
                g.time = parseTime(e.getString("date"));
                JSONObject st = c.optJSONObject("status");
                if (st == null) st = e.getJSONObject("status");
                g.state = st.getJSONObject("type").optString("state", "pre");
                g.clock = st.optString("displayClock", "");
                JSONArray cs = c.getJSONArray("competitors");
                for (int k = 0; k < cs.length(); k++) {
                    JSONObject t = cs.getJSONObject(k);
                    JSONObject team = t.getJSONObject("team");
                    boolean home = "home".equals(t.optString("homeAway"));
                    String id = team.optString("id"), name = team.optString("displayName"), score = t.optString("score", "");
                    if (home) { g.homeId = id; g.homeName = name; g.homeScore = score; }
                    else { g.awayId = id; g.awayName = name; g.awayScore = score; }
                }
                if (g.homeName != null && g.awayName != null) out.add(g);
            } catch (Exception ignored) { }
        }
        return out;
    }

    private static long parseTime(String s) throws Exception {
        for (String f : new String[]{"yyyy-MM-dd'T'HH:mm'Z'", "yyyy-MM-dd'T'HH:mm:ss'Z'"}) {
            try {
                SimpleDateFormat p = new SimpleDateFormat(f, Locale.ROOT);
                p.setTimeZone(TimeZone.getTimeZone("UTC"));
                return p.parse(s).getTime();
            } catch (Exception ignored) { }
        }
        throw new Exception("date");
    }

    /** بداية ونهاية اليوم المختار بتوقيت التلفزيون. */
    private static long[] dayRange(int offset) {
        Calendar c = Calendar.getInstance();
        c.set(Calendar.HOUR_OF_DAY, 0);
        c.set(Calendar.MINUTE, 0);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        c.add(Calendar.DAY_OF_YEAR, offset);
        long start = c.getTimeInMillis();
        c.add(Calendar.DAY_OF_YEAR, 1);
        return new long[]{start, c.getTimeInMillis()};
    }

    // ---------- عرض المباريات ----------

    private void show(List<Game> games, Set<String> picked, Map<String, String[]> favs, boolean failed) {
        boolean ar = Prefs.arabic(a);
        list.removeAllViews();
        if (failed) { message(ar ? "ما گدرت أجيب المباريات. تأكد من النت وجرب مرة ثانية." : "Couldn't load matches. Check the internet."); return; }
        List<Game> mine = new ArrayList<>();
        Map<String, List<Game>> byLeague = new LinkedHashMap<>();
        for (String[] l : LEAGUES) byLeague.put(l[0], new ArrayList<>());
        boolean live = false;
        for (Game g : games) {
            if ("in".equals(g.state)) live = true;
            if (favs.containsKey(g.homeId) || favs.containsKey(g.awayId)) mine.add(g);
            else if (picked.contains(g.league) && byLeague.containsKey(g.league)) byLeague.get(g.league).add(g);
        }
        View first = null;
        if (!mine.isEmpty()) {
            header(ar ? "⭐ فرقي" : "⭐ My teams");
            for (Game g : mine) { View r = row(g, favs, true); if (first == null) first = r; }
        }
        for (String[] l : LEAGUES) {
            List<Game> gs = byLeague.get(l[0]);
            if (gs.isEmpty()) continue;
            header(ar ? l[1] : l[2]);
            for (Game g : gs) { View r = row(g, favs, false); if (first == null) first = r; }
        }
        if (list.getChildCount() == 0) {
            message(ar ? "ماكو مباريات بهذا اليوم بدورياتك. تگدر تضيف دوريات من \"دورياتي\"." : "No matches this day in your leagues.");
        } else if (first != null && !dayBar.hasFocus()) {
            first.requestFocus();
        }
        if (live) main.postDelayed(liveTick, 60000); // اكو مباراة هسة: نحدث النتيجة كل دقيقة
    }

    private void header(String s) {
        TextView h = text(26, 0xCCFFFFFF, true);
        h.setText(s);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, -2);
        lp.topMargin = px(list.getChildCount() == 0 ? 0 : 30);
        lp.bottomMargin = px(12);
        list.addView(h, lp);
    }

    /** سطر المباراة: الفريق الأول | الوكت أو النتيجة | الفريق الثاني. تضغط على فريق = ⭐ */
    private View row(Game g, Map<String, String[]> favs, boolean showLeague) {
        boolean ar = Prefs.arabic(a);
        LinearLayout r = new LinearLayout(a);
        r.setGravity(Gravity.CENTER_VERTICAL);
        r.setLayoutDirection(ar ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        r.setBackground(round(0x1AFFFFFF, 26));
        r.setPadding(px(10), px(8), px(10), px(8));
        TextView home = team(g.homeId, g.homeName, g.league, favs);
        TextView away = team(g.awayId, g.awayName, g.league, favs);
        LinearLayout mid = new LinearLayout(a);
        mid.setOrientation(LinearLayout.VERTICAL);
        mid.setGravity(Gravity.CENTER);
        TextView big = text(34, 0xFFFFFFFF, true);
        TextView small = text(18, 0xB3FFFFFF, false);
        big.setGravity(Gravity.CENTER);
        small.setGravity(Gravity.CENTER);
        String time = new SimpleDateFormat("HH:mm", Locale.ROOT).format(new Date(g.time));
        if ("pre".equals(g.state)) {
            big.setText(time);
            small.setText(showLeague ? leagueName(g.league, ar) : (ar ? "ما بدت" : "Upcoming"));
        } else {
            big.setText(g.homeScore + "  -  " + g.awayScore);
            if ("in".equals(g.state)) {
                small.setText((ar ? "● مباشر " : "● LIVE ") + g.clock);
                small.setTextColor(0xFFFF5A5F);
            } else small.setText(ar ? "خلصت" : "Full time");
        }
        mid.addView(big);
        mid.addView(small);
        r.addView(home, new LinearLayout.LayoutParams(0, px(76), 1));
        r.addView(mid, new LinearLayout.LayoutParams(px(240), -2));
        r.addView(away, new LinearLayout.LayoutParams(0, px(76), 1));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = px(12);
        list.addView(r, lp);
        return home;
    }

    private TextView team(String id, String name, String league, Map<String, String[]> favs) {
        boolean ar = Prefs.arabic(a);
        TextView t = text(28, 0xFFFFFFFF, false);
        boolean fav = favs.containsKey(id);
        t.setText((fav ? "⭐ " : "") + (ar ? arabicName(name) : name));
        t.setGravity(Gravity.CENTER);
        t.setSingleLine(true);
        t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        t.setPadding(px(16), 0, px(16), 0);
        t.setFocusable(true);
        t.setClickable(true);
        t.setBackground(round(0x00000000, 22));
        t.setOnFocusChangeListener((v, has) -> {
            if (has) Sound.move();
            t.setBackground(round(has ? 0xF2FFFFFF : 0x00000000, 22));
            t.setTextColor(has ? 0xFF15151A : 0xFFFFFFFF);
            v.animate().scaleX(has ? 1.05f : 1f).scaleY(has ? 1.05f : 1f).setDuration(150).start();
        });
        t.setOnClickListener(v -> {
            Sound.press();
            toggleFav(a, id, name, league);
            boolean nowFav = favTeams(a).containsKey(id);
            android.widget.Toast.makeText(a, (ar ? arabicName(name) : name) + (nowFav ? (ar ? ": صار من فرقك ⭐" : ": added ⭐") : (ar ? ": انشال من فرقك" : ": removed")), android.widget.Toast.LENGTH_SHORT).show();
            load(false);
        });
        return t;
    }

    private void message(String s) {
        list.removeAllViews();
        TextView m = text(30, 0xE6FFFFFF, false);
        m.setText(s);
        list.addView(m);
    }

    // ---------- اختيار الدوريات ----------

    private void showSettings() {
        main.removeCallbacks(liveTick);
        generation++;
        boolean ar = Prefs.arabic(a);
        list.removeAllViews();
        header(ar ? "اختار الدوريات والبطولات (المنتخبات بالبطولات الدولية)" : "Pick leagues and tournaments");
        Set<String> picked = leagues(a);
        View first = null;
        for (String[] l : LEAGUES) {
            TextView t = option((picked.contains(l[0]) ? "✓  " : "     ") + (ar ? l[1] : l[2]));
            t.setOnClickListener(v -> {
                Sound.press();
                Set<String> p = leagues(a);
                if (!p.remove(l[0])) p.add(l[0]);
                Prefs.of(a).edit().putString("leagues", android.text.TextUtils.join(",", p)).apply();
                t.setText((p.contains(l[0]) ? "✓  " : "     ") + (ar ? l[1] : l[2]));
            });
            if (first == null) first = t;
        }
        Map<String, String[]> favs = favTeams(a);
        header(ar ? "⭐ فرقي (اضغط حتى تشيله). تضيف فريق من صفحة المباريات بالضغط على اسمه" : "⭐ My teams (press to remove)");
        if (favs.isEmpty()) {
            TextView m = text(24, 0xB3FFFFFF, false);
            m.setText(ar ? "بعد ما اخترت فرق." : "No teams yet.");
            list.addView(m);
        }
        for (String[] f : favs.values()) {
            TextView t = option("⭐  " + (ar ? arabicName(f[1]) : f[1]));
            t.setOnClickListener(v -> { Sound.press(); toggleFav(a, f[0], f[1], ""); list.removeView(t); });
        }
        if (first != null) first.requestFocus();
        scroll.scrollTo(0, 0);
    }

    private TextView option(String s) {
        TextView t = text(28, 0xFFFFFFFF, false);
        t.setText(s);
        t.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        t.setPadding(px(28), 0, px(28), 0);
        t.setFocusable(true);
        t.setClickable(true);
        t.setBackground(round(0x1AFFFFFF, 22));
        t.setOnFocusChangeListener((v, has) -> {
            if (has) Sound.move();
            t.setBackground(round(has ? 0xF2FFFFFF : 0x1AFFFFFF, 22));
            t.setTextColor(has ? 0xFF15151A : 0xFFFFFFFF);
        });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, px(70));
        lp.bottomMargin = px(10);
        list.addView(t, lp);
        return t;
    }

    private TextView pill(String s, boolean selected) {
        TextView t = text(24, 0xFFFFFFFF, selected);
        t.setText(s);
        t.setGravity(Gravity.CENTER);
        t.setPadding(px(28), 0, px(28), 0);
        t.setFocusable(true);
        t.setClickable(true);
        int idle = selected ? 0x59FFFFFF : 0x1FFFFFFF;
        t.setBackground(round(idle, 32));
        t.setOnFocusChangeListener((v, has) -> {
            if (has) Sound.move();
            t.setBackground(round(has ? 0xF2FFFFFF : idle, 32));
            t.setTextColor(has ? 0xFF15151A : 0xFFFFFFFF);
        });
        return t;
    }

    // ---------- الحفظ ----------

    static Set<String> leagues(Activity a) {
        Set<String> s = new HashSet<>();
        for (String x : Prefs.of(a).getString("leagues", DEFAULT_LEAGUES).split(",")) if (!x.isEmpty()) s.add(x);
        return s;
    }

    /** فرقي: رقم الفريق ← {الرقم، الاسم، الدوري الي انختار منه}. */
    static Map<String, String[]> favTeams(Activity a) {
        Map<String, String[]> m = new LinkedHashMap<>();
        for (String x : Prefs.of(a).getString("teams", "").split("\n")) {
            String[] f = x.split("\\|", -1);
            if (f.length >= 3 && !f[0].isEmpty()) m.put(f[0], f);
        }
        return m;
    }

    static void toggleFav(Activity a, String id, String name, String league) {
        Map<String, String[]> m = favTeams(a);
        if (m.remove(id) == null) m.put(id, new String[]{id, name.replace("|", " "), league});
        StringBuilder b = new StringBuilder();
        for (String[] f : m.values()) b.append(f[0]).append('|').append(f[1]).append('|').append(f[2]).append('\n');
        Prefs.of(a).edit().putString("teams", b.toString()).apply();
    }

    private static String leagueName(String slug, boolean ar) {
        for (String[] l : LEAGUES) if (l[0].equals(slug)) return ar ? l[1] : l[2];
        return "";
    }

    // ---------- أسماء الفرق بالعربي ----------

    private static final Map<String, String> AR = new HashMap<>();
    static {
        String[] p = {
                "Real Madrid", "ريال مدريد", "Barcelona", "برشلونة", "Atlético Madrid", "أتلتيكو مدريد", "Atletico Madrid", "أتلتيكو مدريد",
                "Sevilla", "إشبيلية", "Valencia", "فالنسيا", "Villarreal", "فياريال", "Real Betis", "ريال بيتيس", "Real Sociedad", "ريال سوسيداد",
                "Athletic Club", "أتلتيك بلباو", "Girona", "جيرونا", "Manchester City", "مانشستر سيتي", "Manchester United", "مانشستر يونايتد",
                "Liverpool", "ليفربول", "Arsenal", "أرسنال", "Chelsea", "تشيلسي", "Tottenham Hotspur", "توتنهام", "Newcastle United", "نيوكاسل",
                "Aston Villa", "أستون فيلا", "West Ham United", "وست هام", "Everton", "إيفرتون", "Brighton & Hove Albion", "برايتون",
                "Bayern Munich", "بايرن ميونخ", "Borussia Dortmund", "بوروسيا دورتموند", "Bayer Leverkusen", "باير ليفركوزن", "RB Leipzig", "لايبزيغ",
                "Paris Saint-Germain", "باريس سان جيرمان", "Marseille", "مارسيليا", "Lyon", "ليون", "Monaco", "موناكو", "AS Monaco", "موناكو", "Lille", "ليل",
                "Juventus", "يوفنتوس", "AC Milan", "ميلان", "Internazionale", "إنتر ميلان", "Inter Milan", "إنتر ميلان", "Napoli", "نابولي",
                "AS Roma", "روما", "Roma", "روما", "Lazio", "لاتسيو", "Atalanta", "أتالانتا", "Fiorentina", "فيورنتينا", "Como", "كومو",
                "Ajax", "أياكس", "PSV Eindhoven", "آيندهوفن", "Feyenoord", "فينورد", "Benfica", "بنفيكا", "FC Porto", "بورتو", "Sporting CP", "سبورتنغ لشبونة",
                "Galatasaray", "غلطة سراي", "Fenerbahce", "فنربخشة", "Besiktas", "بشكتاش", "Celtic", "سيلتك", "Rangers", "رينجرز",
                "Al Hilal", "الهلال", "Al-Hilal", "الهلال", "Al Nassr", "النصر", "Al-Nassr", "النصر", "Al Ittihad", "الاتحاد", "Al-Ittihad", "الاتحاد",
                "Al Ahli", "الأهلي", "Al-Ahli", "الأهلي", "Al Shabab", "الشباب", "Al Qadsiah", "القادسية", "Al Ettifaq", "الاتفاق",
                "Iraq", "العراق", "Saudi Arabia", "السعودية", "Qatar", "قطر", "United Arab Emirates", "الإمارات", "Jordan", "الأردن", "Syria", "سوريا",
                "Lebanon", "لبنان", "Kuwait", "الكويت", "Bahrain", "البحرين", "Oman", "عُمان", "Palestine", "فلسطين", "Iran", "إيران", "Japan", "اليابان",
                "South Korea", "كوريا الجنوبية", "Australia", "أستراليا", "China", "الصين", "Uzbekistan", "أوزبكستان",
                "Egypt", "مصر", "Morocco", "المغرب", "Algeria", "الجزائر", "Tunisia", "تونس", "Libya", "ليبيا", "Sudan", "السودان",
                "Brazil", "البرازيل", "Argentina", "الأرجنتين", "Uruguay", "الأوروغواي", "Colombia", "كولومبيا", "Chile", "تشيلي", "Mexico", "المكسيك",
                "United States", "أمريكا", "USA", "أمريكا", "Canada", "كندا", "France", "فرنسا", "Germany", "ألمانيا", "Spain", "إسبانيا",
                "England", "إنگلترا", "Italy", "إيطاليا", "Portugal", "البرتغال", "Netherlands", "هولندا", "Belgium", "بلجيكا", "Croatia", "كرواتيا",
                "Switzerland", "سويسرا", "Denmark", "الدنمارك", "Sweden", "السويد", "Norway", "النرويج", "Finland", "فنلندا", "Poland", "بولندا",
                "Turkey", "تركيا", "Türkiye", "تركيا", "Austria", "النمسا", "Scotland", "اسكتلندا", "Wales", "ويلز", "Serbia", "صربيا",
                "Ukraine", "أوكرانيا", "Czechia", "التشيك", "Greece", "اليونان", "Senegal", "السنغال", "Nigeria", "نيجيريا", "Ghana", "غانا",
                "Cameroon", "الكاميرون", "Ivory Coast", "ساحل العاج", "HJK Helsinki", "هلسنكي", "FC Inter Turku", "إنتر توركو", "TPS Turku", "تي بي إس توركو"};
        for (int i = 0; i + 1 < p.length; i += 2) AR.put(p[i], p[i + 1]);
    }

    private static String arabicName(String n) {
        String v = AR.get(n);
        return v != null ? v : n;
    }

    // ---------- أدوات ----------

    private int px(float d) { return Math.round(d * u); }

    private TextView text(float size, int color, boolean bold) {
        TextView t = new TextView(a);
        t.setTextColor(color);
        t.setTextSize(TypedValue.COMPLEX_UNIT_PX, px(size));
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    private GradientDrawable round(int color, int r) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(px(r));
        return g;
    }
}
