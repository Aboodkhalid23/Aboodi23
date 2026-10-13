# أدوات المستوى الثاني لفريقنا

> تاريخ البحث: 2026/10/6. هذا الملف يكمّل `studio/style/process-and-tools.md`، والأدوات الي انذكرت هناك ما رجعتلها.
> أسماء الأدوات والروابط تبقى إنگليزي، والشرح كله عربي.
> **ما ثبّتت ولا شي، وما عدّلت `skills.manifest`.** هذا تقرير بس، والقرار إلك.

---

## شلون فحصت

1. حمّلت كل ريبو (repo يعني مجلد مشروع على GitHub) بمجلد مؤقت بعيد عن مشروعنا، وقريت ملفاته.
2. دوّرت بالكود على أي شي خطر: إرسال بيانات لمكان غريب، أوامر مثل `curl | bash` (تنزيل كود وتشغيله بدون ما تشوفه)، مفاتيح أو أسرار، سكربتات تثبيت تسوي شغلات غريبة.
3. الأدوات المهمة **جرّبتها فعلاً** بالحاوية (الحاوية يعني الكمبيوتر السحابي الي أشتغل عليه):
   - صوت عراقي من `edge-tts` طلع ملف صوت 4.8 ثانية بصوت "باسل" العراقي.
   - `faster-whisper` حوّل نفس الصوت لكتابة عربية.
   - `google-trends` جاب ترندات العراق بدون مفتاح.
   - `yt-viral` رتّب فيديوهات MagnatesMedia: "The $47 Billion Cult" سوّى 3.74 ضعف معدل القناة.
   - `ia` لگى أفلام أرشيفية قديمة عن النفط بمكتبة Prelinger.
   - `trafilatura` سحب نص مقال نظيف.

### الموجود هسه بالحاوية
| الأداة | الحالة |
|---|---|
| `yt-dlp` (يسحب معلومات وفيديوهات يوتيوب) | ✅ موجود (نسخة 2026.8.19) |
| `ffmpeg` (يقص ويحوّل الصوت والفيديو) | ✅ موجود |
| `youtube-transcript-api` (يسحب ترجمة أي فيديو يوتيوب) | ✅ موجود |
| `node` و`npm` (لتشغيل أدوات جافاسكربت) | ✅ موجود (نسخة 22) |
| `whisper` أو `faster-whisper` (صوت ← كتابة) | ❌ مو موجود |
| `edge-tts` (كتابة ← صوت) | ❌ مو موجود |
| مدقق إملائي عربي (`hunspell-ar`) | ❌ مو موجود |

---

## الجزء الأول: السكيلزات الي أنصح بيها (9 + واحد مساعد)

| # | السكيل | شنو يسوي | الرخصة | الأمان | الكلفة | منو يستفيد بالفريق |
|---|---|---|---|---|---|---|
| 1 | **verified-research** من [JalalD/verified-research](https://github.com/JalalD/verified-research) | بحث بعدة باحثين بنفس الوقت، وبعدين **واحد ما كتب الجواب يفتح كل مصدر من جديد** ويتأكد إن المصدر فعلاً يگول هالشي. وبالأخير يطلع تقرير بيه درجة ثقة لكل معلومة، وقائمة بالي ما انثبت. وبيه سكربت يفحص الروابط المكسورة. | MIT | ✅ تعليمات، و3 سكربتات بايثون بمكتبات أساسية بس. الاتصال الوحيد بالإنترنت هو فتح روابط المصادر نفسها. ماكو مفاتيح. | مجاني | `researcher`، `fact-checker`، `source-verifier` |
| 2 | **osint-investigation** من [reichaves/osint-investigation](https://github.com/reichaves/osint-investigation) | OSINT يعني تحقيق من مصادر مفتوحة للعامة. يحدد مكان صورة أو فيديو (geolocation)، ويتحقق من صورة إذا قديمة أو مزورة، ويبني ملف عن شخص أو شركة من مصادر عامة. يطلع "ورقة خيوط" بيها درجة ثقة وسلسلة أدلة وأسئلة للمتابعة. مبني على بروتوكول Berkeley وبيه قواعد أخلاقية. | MIT | ✅ ملفات تعليمات بس، ماكو كود. | مجاني | `source-hunter`، `source-verifier` |
| 3 | **web-archiving** من [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) | يرجّع صفحات انحذفت عن طريق Wayback Machine (أرشيف الإنترنت) وArchive.today، ويطلع **كل النسخ القديمة لصفحة** عن طريق CDX API (يعني تشوف شلون تغيّر بيان شركة أو تغريدة عبر السنين)، ويحفظ الدليل قبل لا ينحذف. | MIT | ✅ تعليمات بس. بيه مفتاح اختياري لـ Perma.cc ما نحتاجه. نفس الريبو الي عدنه منه `fact-check-workflow`. | مجاني | `source-hunter`، `timeline-builder` |
| 4 | **social-media-intelligence** (نفس الريبو) | يتتبع شلون انتشرت إشاعة أو تغريدة، ويكشف الحسابات الوهمية والحملات المنظمة، ويحفظ التغريدات كدليل. | MIT | ✅ تعليمات بس. | مجاني | `source-verifier`، `phenomenon-analyst` |
| 5 | **content-access** (نفس الريبو) | طرق قانونية توصل بيها لمقالات مدفوعة وأبحاث علمية (مثل Unpaywall ونسخ المؤلفين المجانية). | MIT | ✅ تعليمات بس. | مجاني | `researcher` |
| 6 | **google-trends** من [terryds/google-trends-skill](https://github.com/terryds/google-trends-skill) | ترندات Google اليومية واللحظية لأي بلد، وشنو الناس تدوّر بكل منطقة، والبحوث المرتبطة، واقتراحات الإكمال التلقائي. **جرّبته وجاب ترندات العراق بدون مفتاح.** | MIT (مكتوبة بالـ README) | ✅ سكربت جافاسكربت واحد بمكتبات Node الأساسية بس، يتصل بموقع Google Trends بس. | مجاني | `topic-scout`، `growth-analyst` |
| 7 | **yt-viral** من [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) | يرتّب فيديوهات المنافسين حسب **كم مرة تفوقت على معدل قناتها نفسها**، مو حسب عدد المشاهدات (فيديو بـ400 ألف بقناة معدلها 30 ألف أهم من مليون بقناة كبيرة). يشتغل ويا `yt-dlp` الموجود. **جرّبته واشتغل.** | MIT | ✅ بايثون بمكتبات أساسية، يقرا ملف محلي بس. نفس الريبو الي عدنه منه `yt-retention`. | مجاني | `topic-scout`، `growth-analyst`، `hook-miner` |
| 7ب | **yt-script** (نفس الريبو، **مساعد بس**) | `yt-viral` يحتاج ملف `hooks.json` الي بمجلد هذا السكيل، وبدونه ما يشتغل. نثبّته حتى يشتغل `yt-viral`، **مو حتى نكتب بيه**: الكتابة تبقى بـ `studio`. | MIT | ✅ | مجاني | (مساعد) |
| 8 | **yt-chapters** (نفس الريبو) | يطلع فصول الفيديو (chapters) من ملف الترجمة، ويتأكد من شروط يوتيوب: أول فصل 00:00، وأقل شي 3 فصول، وكل فصل 10 ثواني أو أكثر. يعتمد على `yt-edit` الموجود عدنه. | MIT | ✅ بايثون بمكتبات أساسية. | مجاني | `packager` |
| 9 | **audio-tldr** من [AugustusW/audio-tldr-skill](https://github.com/AugustusW/audio-tldr-skill) | ينطيه رابط يوتيوب أو بودكاست أو ملف، فيحوّل الصوت لكتابة **على جهازنا** (يحفظ النتيجة حتى ما يعيدها)، ويطلع ملخص أو ترجمة، و**ملف ترجمة `.srt`** إذا ردنا. ينفع لدراسة فيديوهات المنافسين ومقابلات المصادر، ولترجمة حلقاتنا. | MIT | ✅ بايثون. يتصل بس بـ `yt-dlp` وبموقع Apple للبودكاست. ومكتوب بيه صراحة إنه ما يثبّت أي شي بدون موافقتك. | مجاني (يحتاج `faster-whisper`، شوف الجزء الثاني) | `researcher`، `growth-analyst` |

### اختياري (إذا تريد)
- **yt-package** (نفس ريبو Jakeschincariol): يفحص العنوان ونص الغلاف كوحدة وحدة. يحسب الطول: 60 حرف حد البحث بالكمبيوتر، و40 حد الموبايل. ويتأكد إن نص الغلاف ما يكرر العنوان، و3 كلمات بالغلاف كحد أقصى. ينفع `packager`، بس يتداخل شوية ويا `titles-and-thumbnails`.

### الأسطر الجاهزة لـ `skills.manifest`
```
# بحث وتحقق وOSINT — المستوى الثاني (مفحوصة 2026/10/6: تعليمات، أو بايثون/نود بمكتبات أساسية، ماكو مفاتيح)
JalalD/verified-research             skills/verified-research
reichaves/osint-investigation        .                                                osint-investigation
jamditis/claude-skills-journalism    research-toolkit/skills/web-archiving
jamditis/claude-skills-journalism    journalism-core/skills/social-media-intelligence
jamditis/claude-skills-journalism    research-toolkit/skills/content-access

# ترند ومنافسين (مجاني بدون مفاتيح)
terryds/google-trends-skill          .                                                google-trends
Jakeschincariol/youtube-agent-skill  skills/yt-viral
Jakeschincariol/youtube-agent-skill  skills/yt-script
Jakeschincariol/youtube-agent-skill  skills/yt-chapters

# إنتاج: صوت ← كتابة وترجمة
AugustusW/audio-tldr-skill           skills/audio-tldr

# اختياري:
# Jakeschincariol/youtube-agent-skill  skills/yt-package
```

---

## الجزء الثاني: أدوات سطر الأوامر (CLI)

CLI يعني برنامج يشتغل بأوامر مكتوبة بدل الأزرار.

| # | الأداة | شنو تسوي لنا | الرخصة | الكلفة | جرّبتها؟ |
|---|---|---|---|---|---|
| 1 | **`edge-tts`** ([rany2/edge-tts](https://github.com/rany2/edge-tts)) | **تسمع السكربت بصوت عراقي قبل التصوير.** بيها صوتين عراقيين: `ar-IQ-BasselNeural` (رجل) و`ar-IQ-RanaNeural` (مرة). ومنها نعرف **طول الحلقة الحقيقي**: نحوّل السكربت كله صوت ونشوف مدته. ينفع `delivery-tester` حتى يسمع وين اللسان يتعثر. | LGPL-3.0 | مجاني، بدون مفتاح | ✅ طلع صوت باسل |
| 2 | **`faster-whisper`** ([SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)) | صوت ← كتابة بالعربي، **وملفات ترجمة `.srt` لحلقاتنا**. يشتغل على جهازنا بدون إنترنت بعد ما ينزل النموذج. ملاحظة: النموذج الصغير (`small`) غلط بكلمات عراقية مثل "أحچيلكم"، فللحلقات نستخدم `large-v3-turbo` أو `medium`. | MIT | مجاني | ✅ |
| 3 | **`trafilatura`** ([adbar/trafilatura](https://github.com/adbar/trafilatura)) | يسحب نص المقال نظيف من أي رابط خبر، بدون إعلانات وقوائم، وتاريخ النشر واسم الكاتب. ويقرا قوائم أخبار المواقع (RSS) حتى نلگى الأخبار الصغيرة. ينفع `researcher` و`source-hunter`. | Apache-2.0 | مجاني | ✅ |
| 4 | **`internetarchive`** (أمر `ia`) ([jjjake/internetarchive](https://github.com/jjjake/internetarchive)) | يدوّر وينزّل من **أرشيف الإنترنت**: أفلام قديمة ملكيتها عامة (Prelinger)، وإعلانات قديمة، وأخبار تلفزيون، وكتب. هذا مصدر B-roll (لقطات تغطية) مجاني وقانوني لحلقات قصص الشركات. | AGPL-3.0 | مجاني (البحث والتنزيل بدون حساب) | ✅ لگى "Drilling for Oil" |
| 5 | **`hunspell-ar`** (اختياري) | مدقق إملائي عربي. **انتبه:** مبني للفصحى، فيعلّم على كلمات اللهجة. نستخدمه بس للعنوان والنصوص المكتوبة على الشاشة والاقتباسات الفصحى. | GPL | مجاني | ما جربته |

### أوامر التثبيت
```bash
# أدوات بايثون (الأربعة الأساسية)
pip install faster-whisper edge-tts trafilatura internetarchive

# مهم بهالحاوية بس: edge-tts ما يقرا شهادة الأمان مال الحاوية، فنضيفها مرة وحدة
cat /root/.ccr/ca-bundle.crt >> "$(python3 -c 'import certifi; print(certifi.where())')"

# مدقق إملائي (اختياري)
apt-get install -y hunspell hunspell-ar
```

### أمثلة تشغيل
```bash
# اسمع مقطع من السكربت بصوت عراقي
edge-tts --voice ar-IQ-BasselNeural --file studio/episodes/<الحلقة>/04-script.txt --write-media preview.mp3
ffprobe -v error -show_entries format=duration -of csv=p=0 preview.mp3   # طول الحلقة بالثواني

# ترجمة حلقة لملف srt (بسكربت بايثون صغير أو عن طريق audio-tldr)
python3 .claude/skills/audio-tldr/scripts/transcribe.py video.mp4 --language ar --format srt

# أفلام أرشيفية عن موضوع
ia search 'collection:prelinger AND title:(oil)' --itemlist

# نص مقال نظيف
trafilatura -u "https://example.com/article"

# ترندات العراق (بهالحاوية لازم هالمتغيرين حتى يمر من البروكسي، يعني الوسيط الي يمر منه الإنترنت)
NODE_USE_ENV_PROXY=1 NODE_EXTRA_CA_CERTS=/root/.ccr/ca-bundle.crt node .claude/skills/google-trends/scripts/trends.mjs daily-trends --geo IQ

# منافسين: اسحب آخر 30 فيديو وحللهم بـ yt-viral
yt-dlp --flat-playlist -J --playlist-end 30 "https://www.youtube.com/@CHANNEL/videos" > raw.json
```

---

## الجزء الثالث: كل محور وشنو لگيت

### 1. البحث العميق وOSINT والتحقق
- **أقوى إضافة:** `verified-research` (التحقق المستقل من كل مصدر) و`osint-investigation` (تحديد مكان الصور وملفات الكيانات) و`web-archiving` (الصفحات المحذوفة وتاريخ الصفحات).
- **وثائق المحاكم والشركات:** ما لگيت سكيل نظيف ومستقل. البديل: `free-apis-catalog` من نفس ريبو jamditis بيه قائمة APIs مجانية، ونگدر نوصل مباشرة لـ CourtListener (أحكام المحاكم الأمريكية) وSEC EDGAR (ملفات الشركات الأمريكية) بالبحث العادي. اكو [courtlistener-mcp](https://github.com/blakeox/courtlistener-mcp) بس هو MCP (يعني خادم أدوات منفصل يحتاج إعداد ومفتاح)، فأجّلته.

### 2. هيكل القصة والاحتفاظ
- **ما لگيت سكيل أفضل من الي عدنا.** أغلب الموجود للروايات أو يكرر `long-form-youtube` و`storytelling`.
- **فكرة نأخذها (مو تثبيت):** طريقة **MICE** من [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) (MIT). تقسم كل خيط بالقصة لأربع أنواع: مكان، سؤال، شخصية، حدث. والقاعدة: **الخيوط تنسد بعكس ترتيب فتحها**، وأي خيط ما انسد هو وعد مكسور للمشاهد. ومعاها "قالب السؤال المفتوح" (السؤال، الأدلة، وين ينجاوب). أقترح نضيفها كجدول "دفتر الحلقات المفتوحة" لشغل `tension-auditor`: كل سؤال ينفتح بالسكربت، بأي دقيقة، ووين ينسد.

### 3. الهوك والعنوان والغلاف
- `yt-package` (اختياري) يفحص العنوان والغلاف كوحدة.
- `hookscore.py` بسكيل `yt-script` يقيّم الهوك، بس **مبني على كلمات إنگليزية** فما ينفع لسكربتنا. نستخدم `yt-script` بس كمساعد لـ `yt-viral`.
- عدنا هسه أدوات vidIQ متصلة (`score_title` و`score_thumbnail`)، بس تخلص رصيد، فقبل ما نستخدمها نسألك.

### 4. أدوات اللغة العربية
- **أفضل شي:** `edge-tts` بالصوت العراقي (مجاني) و`faster-whisper`.
- **سهولة القراءة:** ماكو مكتبة عربية جيدة لقياس سهولة القراءة. الأحسن نقيس بطريقتنا: طول الجملة بالكلمات، وعدد الكلمات بالدقيقة من مدة صوت `edge-tts`.
- **الإملاء:** `hunspell-ar` للفصحى بس (العنوان والنص على الشاشة).
- [SawtakArabi/skill](https://github.com/SawtakArabi/skill) بيه **لهجة عراقية وصوت أقرب للطبيعي**، بس **مدفوع** (يحتاج مفتاح ورصيد). إذا ردت صوت أحسن بعدين، هذا الخيار. **قرارك لأن بيه فلوس.**

### 5. تحليل يوتيوب والترندات والمنافسين
- `google-trends` و`yt-viral` ويا `yt-dlp`: كله مجاني وبدون مفاتيح.
- منافس جيد للمستقبل: [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) (MIT). يبحث بـ Reddit وHacker News وYouTube وPolymarket (سوق توقعات) وGitHub لآخر 30 يوم بدون مفاتيح. بس **ثقيل** (135 ملف)، ويحاول يقرا كوكيز المتصفح (ملفات الدخول) بموافقتك، ويروّج لتسجيل بخدمة ScrapeCreators. أجّلته، وإذا ثبتناه نشغّله بخيار `--no-browser-cookies`.

### 6. مساعدات الإنتاج
- **الترجمة (subtitles):** `faster-whisper` + `audio-tldr` يطلعون `.srt`، و`captions-and-clipping` الموجود ينظّفها.
- **التلقين (teleprompter):** المشاريع المفتوحة الي فحصتها ([zhang-brook/web-teleprompter](https://github.com/zhang-brook/web-teleprompter) وغيره) **ما تدعم العربي** بالمتابعة الصوتية. أقترح نبني صفحة تلقين بسيطة إلنا: من اليمين لليسار، وسرعة ثابتة، وقلب للمراية، وحجم خط كبير. نسويها بـ `frontend-design` بساعة شغل.
- **B-roll:** `ia` (أرشيف الإنترنت)، وWikimedia Commons (صور وفيديو بتراخيص مفتوحة). وعدنا Higgsfield وartlist للقطات المولّدة بالذكاء الاصطناعي.

---

## الجزء الرابع: فحصتها وما نصحت بيها

| الأداة | ليش لا |
|---|---|
| [madeinoz67/madeinoz-osint-skill](https://github.com/madeinoz67/madeinoz-osint-skill) | مشروع TypeScript ثقيل، **ماكو رخصة**، ومركّز على تتبع الأشخاص (أرقام وإيميلات وتسريبات). خطر على الخصوصية ومو حاجتنا. |
| [criscatalyst/outliers-skill](https://github.com/criscatalyst/outliers-skill) | **ماكو رخصة**، ويحتاج مفتاح YouTube API. `yt-viral` يسوي نفس الشغلة مجاناً. |
| [jftuga/transcript-critic](https://github.com/jftuga/transcript-critic) | بيه `install.sh`، ويعتمد على whisper.cpp ومبني للماك. |
| [bholmesdev/skills](https://github.com/bholmesdev/skills) `transcribe` | مبني للماك (يفتح Finder). `audio-tldr` أحسن. |
| [louisedesadeleer/b-roll-finder](https://github.com/louisedesadeleer/b-roll-finder) | MIT، بس مبني للبودكاست، ويعتمد على مقاطع يوتيوب (خطر حقوق نشر). وبيه قاعدة "تشغيل السكيل يعتبر موافقة دائمة"، وهذا ما يعجبني. ممكن نقرا جدول "نوع الجملة ← نوع اللقطة" كإلهام بس. |
| [rubenespitia/claude-skill-broll](https://github.com/rubenespitia/claude-skill-broll) | ماكو رخصة، مبني للألعاب والأفلام، ويحتاج مفاتيح Pexels وPixabay. |
| [soreavis/research-entity](https://github.com/soreavis/research-entity) | ضخم (746 KB)، مخصص لتقارير الشركات الاستثمارية، ومربوط بـ Notion وConfluence. |
| [Abaco3300/trendcite](https://github.com/Abaco3300/trendcite) | MIT ونظيف، بس مخصص لترندات التقنية والشركات الناشئة (HN وGitHub). |
| [Albrrak773/agent-skills](https://github.com/Albrrak773/agent-skills) `arabic-copy` | لهجة نجدية لنصوص التطبيقات. ناخذ قاعدة وحدة منه لـ `dialect-editor`: **"كل جملة بلهجة وحدة، لا تخلط فصحى ولهجة بنفس الجملة"**. |
| [wuwangzhang1216/DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL) | MIT وتعليمات بس. ممتاز لقائمة لقطات الفيديو المولّد بالذكاء الاصطناعي، بس كبير (1.2 MB) ومو أولوية. نرجعله إذا صار عدنا لقطات AI كثيرة. |
| [SawtakArabi/skill](https://github.com/SawtakArabi/skill) | مدفوع (شوف المحور 4). |
| `pytrends` و`waybackpy` (مكتبات بايثون) | قديمة: `pytrends` آخر تحديث 2023 وGoogle يحجبه، و`waybackpy` آخر تحديث 2022. البديل `google-trends` و`web-archiving`. |

---

## الخطوات الجاية (قرارك)
1. توافق نضيف الأسطر العشرة فوق لـ `skills.manifest` ونشغّل `scripts/update-skills.sh`؟
2. توافق نثبّت الأدوات الأربع (`pip install faster-whisper edge-tts trafilatura internetarchive`)؟
3. نحدّث ملفات الفريق بعدها: `researcher` و`fact-checker` يستخدمون `verified-research`، و`source-hunter` يستخدم `web-archiving` و`osint-investigation`، و`topic-scout` يستخدم `google-trends` و`yt-viral`، و`delivery-tester` يسمع السكربت بـ `edge-tts`، و`tension-auditor` يضيف دفتر الحلقات المفتوحة (MICE).
4. نبني صفحة تلقين عربية.

---

## المصادر
- [JalalD/verified-research](https://github.com/JalalD/verified-research) · [reichaves/osint-investigation](https://github.com/reichaves/osint-investigation) · [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) · [terryds/google-trends-skill](https://github.com/terryds/google-trends-skill) · [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) · [AugustusW/audio-tldr-skill](https://github.com/AugustusW/audio-tldr-skill)
- [rany2/edge-tts](https://github.com/rany2/edge-tts) · [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [adbar/trafilatura](https://github.com/adbar/trafilatura) · [jjjake/internetarchive](https://github.com/jjjake/internetarchive)
- [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) · [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) · [SawtakArabi/skill](https://github.com/SawtakArabi/skill) · [zhang-brook/web-teleprompter](https://github.com/zhang-brook/web-teleprompter) · [blakeox/courtlistener-mcp](https://github.com/blakeox/courtlistener-mcp)
- [madeinoz67/madeinoz-osint-skill](https://github.com/madeinoz67/madeinoz-osint-skill) · [criscatalyst/outliers-skill](https://github.com/criscatalyst/outliers-skill) · [jftuga/transcript-critic](https://github.com/jftuga/transcript-critic) · [louisedesadeleer/b-roll-finder](https://github.com/louisedesadeleer/b-roll-finder) · [rubenespitia/claude-skill-broll](https://github.com/rubenespitia/claude-skill-broll) · [soreavis/research-entity](https://github.com/soreavis/research-entity) · [Abaco3300/trendcite](https://github.com/Abaco3300/trendcite) · [Albrrak773/agent-skills](https://github.com/Albrrak773/agent-skills) · [wuwangzhang1216/DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL)
