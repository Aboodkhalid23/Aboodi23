# أدوات المستوى الثالث: التشويق والقصة + البحث العميق

> تاريخ البحث: 2026/10/8. هذا الملف يكمّل `tools-level2.md` و`process-and-tools.md`، **وما رجعت لأي شي انذكر هناك أو مثبّت عدنا** (مثل `storytelling` و`long-form-youtube` و`viral-hooks` و`hook-writer` و`yt-script` و`verified-research` و`web-archiving`).
> أسماء الأدوات والروابط تبقى إنگليزي، والشرح كله عربي.
> **ما ثبّتت ولا شي، وما عدّلت `skills.manifest`، وما سويت commit.** هذا تقرير، والقرار إلك.

---

## شلون فحصت

1. دوّرت بالإنترنت على سكيلزات (ملفات تعليمات لـ Claude) تخص التشويق والقصة.
2. حمّلت كل ريبو مرشّح (repo يعني مجلد مشروع على GitHub) بمجلد مؤقت بعيد عن مشروعنا، وقريت ملفاته.
3. فحصت كل مجلد سكيل: هل بيه كود؟ هل يرسل بيانات لمكان غريب؟ هل بيه أوامر مثل `curl | bash` (تنزيل كود وتشغيله بدون ما تشوفه)؟ هل بيه مفاتيح أو أسرار؟ هل بيه حروف مخفية تخدع Claude بأوامر سرية؟
4. **النتيجة: كل السكيلزات الي أنصح بيها تحت هي ملفات تعليمات بس، ماكو بيها ولا سطر كود، وماكو اتصال بالإنترنت ولا مفاتيح.**
5. أدوات البحث: **جرّبت كل وحدة فعلاً** من الحاوية (الحاوية يعني الكمبيوتر السحابي الي أشتغل عليه)، وكتبت سكربت يجمعها كلها.

---

## الجزء الأول: سكيلزات التشويق والقصة

### الفجوة الي عدنا
عدنا أدوات للهوك والهيكل العام والاحتفاظ. بس **ماكو أداة متخصصة بـ**:
- التشويق داخل المشهد (المشاهد يعرف شي والشخصية ما تعرفه، العد التنازلي).
- الافتتاحية الباردة (cold open: نبدأ من نص الحدث قبل أي مقدمة).
- النص المحچي للوثائقي (narration: شلون نربط المقاطع والصور بصوت الراوي).
- الجسور بين الفصول.
- قوالب الهيكل الكلاسيكية (Save the Cat، دائرة Dan Harmon).

### الي أنصح بيها (6)

| # | السكيل | شنو يسوي | الرخصة | الأمان | منو يستفيد |
|---|---|---|---|---|---|
| 1 | **cw-hitchcock** من [EveryInc/compound-writing](https://github.com/EveryInc/compound-writing) | يفحص أي مقطع ويدوّر **"القنبلة تحت الطاولة"**: قاعدة هيتشكوك، المفاجأة تدوم 10 ثواني، بس التشويق يدوم 5 دقايق إذا المشاهد شاف القنبلة والشخصيات ما شافتها. بيه 7 تقنيات بجدول: الزرع المبكر، المفارقة الدرامية (المشاهد يعرف أكثر من الشخصية)، **العد التنازلي** (ticking clock)، الفجوة بين الي يريده والي عنده، **التأخير قبل الكشف**، **الارتياح الكاذب** ("أخيراً كلشي تمام. بعدين وصل الإيميل")، والتقريب على التفاصيل الصغيرة بلحظة الخطر. ويطلع درجة توتر + اقتراحات + نسخة معدّلة. | MIT | ✅ ملف واحد (8KB)، تعليمات بس. الشركة Every (ناشر معروف). آخر تحديث 2026/9/15. | `tension-auditor` المقترح، `writer`، `creative-director` |
| 2 | **cw-sorkin** (نفس الريبو) | يفحص **الإيقاع والزخم**: هل القصة "تمشي وتحچي" لو "واگفة تشرح"؟ مثال: بدل "خلّي أشرحلكم شلون يشتغل النظام"، نگول "النظام جان دا ينهار من وصلت. ومن فهمت ليش، جان الوقت فات". هذا بالضبط علاج المناطق الميتة الي يكشفها `script-check.py`. | MIT | ✅ ملف واحد، تعليمات بس. | `writer`، `tension-auditor` |
| 3 | **cold-open-writer** من [ur-grue/autopunk-media-skills](https://github.com/ur-grue/autopunk-media-skills) | يكتب **افتتاحية باردة** للوثائقي بـ3 ضربات: نوگع المشاهد بنص الحدث، نفتح السؤال الكبير بدون جواب، وجملة أخيرة قبل العنوان "تستاهل". الشكل جاهز للتصوير: عمود **[الصورة]** وعمود **[الكلام]**، ومدة محسوبة. ممنوع بيه أي خلفية أو شرح. | MIT | ✅ ملف تعليمات + ملف أمثلة اختبار. ماكو كود. | `writer`، `hook-miner` |
| 4 | **documentary-narration-writer** (نفس الريبو) | يكتب **نص الراوي** الي يربط المقابلات والأصوات الحقيقية والصور، بلغة مكتوبة للأذن مو للعين. | MIT | ✅ تعليمات بس. | `writer`، `dialect-editor` |
| 5 | **transition-narration-writer** (نفس الريبو) | يكتب **جسور** بين فصول الحلقة، حتى ما يحس المشاهد إن الموضوع "انقطع" (هنا أغلب الناس تطلع من الفيديو). | MIT | ✅ تعليمات بس. | `writer` |
| 6 | **beat-sheet-builder** (نفس الريبو) | يطلع خريطة **Save the Cat** الكاملة (15 ضربة: الصورة الأولى، الحدث المحرّك، نقطة المنتصف، "كلشي ضاع"، الختام...) ويحط كل ضربة بنسبتها من الطول. ويأشّر على الضربات الضعيفة بالقصة. ينفع لحلقات قصص الشركات (صعود، غرور، سقوط). | MIT | ✅ تعليمات بس. | `creative-director` (مرحلة الخطة `02-plan.md`) |

**ملاحظة على ur-grue:** الريبو ضخم (412 سكيل لكل أنواع الإعلام)، بس سكربت التحديث مالتنا ينسخ **بس المجلد الي نحدده**، فما ينزل الباقي. كل سكيل مكتوب بنفس القالب ومعاه ملف اختبارات. آخر تحديث 2026/8/31.

### اختياري (إذا تريد أكثر)

| السكيل | ليش اختياري |
|---|---|
| **plot-structure** من [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) (MIT) | بمجلده ملف `structure-models.md` بيه **دائرة Dan Harmon** (8 خطوات: راحة، حاجة، يروح، يتكيف، ياخذ، يدفع الثمن، يرجع، تغيّر)، وSave the Cat، والهيكل الياباني ذو الأربع مراحل (Kishōtenketsu)، ومنحنى Fichtean (أزمات متصاعدة من أول دقيقة، ممتاز للوثائقي). ومعاه طريقة **MICE** الي ذكرتها بالمستوى الثاني. بس السكيل نفسه مبني للروايات ويطلب أداة خاصة بيه (تشتغل يدوياً إذا ما موجودة). |
| **thriller-writing** من [pajamadot/thriller](https://github.com/pajamadot/thriller) (MIT) | أقوى شي لگيته عن **"سلّم كشف المعلومات"** (information release ladder: شنو نكشف وبأي ترتيب)، وتوزيع الأدلة بعدالة، وتسلسل الكشف. ينفع لحلقات الجرائم والفضائح. **بس مكتوب بالصيني** و264KB، ومبني للروايات. المجلد نفسه بدون كود (الكود بمجلدات ثانية بالريبو ما ننسخها). |
| **sw-story-structure** و **sw-scene-craft** من [jtydhr88/screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills) (MIT) | خلاصة McKee وSyd Field وSave the Cat، وقاعدة "كل مشهد لازم يقلب قيمة (من أمل ليأس مثلاً)، وإذا ما قلب شي، احذفه". يجاوب بلغة السؤال، بس **مكتوب بالصيني** ويأشّر على ملف مصطلحات بمجلد ثاني ما راح يكون موجود. |
| **cw-promise** (EveryInc) | يكتب 3 "وعود" تخلي المشاهد ينتظر الجاي ("بآخر الحلقة راح تعرف ليش..."). يشتغل لوحده، بس يدوّر على ملف جمهور اختياري ما عدنا. |
| **arabic-hooks-library** من [smeseik-ai/arabic-content-studio](https://github.com/smeseik-ai/arabic-content-studio) (MIT بالـ README) | مكتبة هوكات **عربية** (فجوة فضول، تحدي هوية، عكس المتوقع...). مفيدة كأمثلة، بس **بالفصحى وللتسويق**، ويتداخل ويا `hook-writer` و`viral-hooks`. |
| **storygen** من [kashyab12/storygen-skill](https://github.com/kashyab12/storygen-skill) (MIT) | فكرة **"غرفة Pixar"**: 6 مراجعين (هيكل، عاطفة، شخصيات، عالم، **توتر**، صوت) يقرون المسودة بنفس الوقت. بس مبني لكتابة قصص خيالية، وفريقنا بـ `studio` يسوي نفس الشي. ناخذ منه أسئلة مراجع التوتر بس: "شنو على المحك؟ هل المشاهد يعرف؟ هل الخطر يكبر؟ وين المقاطع الي ماكو بيها ضغط؟". |

### فحصتها وما نصحت بيها

| الأداة | ليش لا |
|---|---|
| [alchaincyf/mrbeast-skill](https://github.com/alchaincyf/mrbeast-skill) | MIT، بس **تمثيل شخصية MrBeast بالصيني**، وبيه سكربتات وصورة إعلان (QR). ودليل MrBeast نفسه حللناه بـ `process-and-tools.md`. |
| [mediabubble-adv/arabic-skill](https://github.com/mediabubble-adv/arabic-skill) (`arabic-iraqi`) | MIT وبيه قسم للهجة العراقية، **بس بيه أغلاط واضحة**: يگول النفي العراقي "ما كتبش" (هذا مصري/شامي مو عراقي). ما نثق بيه للهجة. |
| [CK42BB/vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill) | يصنع فيديو Vox كامل، بس يحتاج **خدمات مدفوعة** (Atlas Cloud وxAI). |
| [tenfoldmarc/script-skill](https://github.com/tenfoldmarc/script-skill) | فكرته حلوة (يتعلم صوتك من فيديوهاتك)، بس **ماكو رخصة**. |
| [jwynia/agent-skills](https://github.com/jwynia/agent-skills) | بيه سكيلزات قصة جيدة (`key-moments`، `speech-adaptation`) بس **ماكو رخصة**. |
| [dglogan42/Claude-Skills](https://github.com/dglogan42/Claude-Skills) `screenplay-creation` | للأفلام الخيالية والكوميديا، مو للوثائقي. |
| [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills) | Apache-2.0، بس ذاكرة وتخطيط للروايات الطويلة. |
| valorinvestigator `investigative-narrative-writer` | الريبو خاص (private)، ما گدرت أحمّله وأفحصه. |
| مكتبات `danjdewhurst/story-skills` الثانية | انذكرت بالمستوى الثاني. |

### الأسطر الجاهزة لـ `skills.manifest`
```
# المستوى الثالث — تشويق وقصة ووثائقي (مفحوصة 2026/10/8: ملفات تعليمات بس، ماكو كود ولا إنترنت ولا مفاتيح)
EveryInc/compound-writing        skills/cw-hitchcock
EveryInc/compound-writing        skills/cw-sorkin
ur-grue/autopunk-media-skills    skills/writing/broadcast/cold-open-writer
ur-grue/autopunk-media-skills    skills/radio-audio/scripting/documentary-narration-writer
ur-grue/autopunk-media-skills    skills/writing/broadcast/transition-narration-writer
ur-grue/autopunk-media-skills    skills/screenwriting/development/beat-sheet-builder

# اختياري:
# danjdewhurst/story-skills        skills/plot-structure
# EveryInc/compound-writing        skills/cw-promise
# pajamadot/thriller               thriller-writing
# jtydhr88/screenwriting-skills    plugins/screenwriting/skills/sw-story-structure
# smeseik-ai/arabic-content-studio skills/arabic-hooks-library
```

### شلون يربطها الفريق (اقتراح)
- `tension-auditor` (المسودة بالمستوى الثاني) يشغّل `cw-hitchcock` على كل فصل، و`cw-sorkin` على المناطق الميتة.
- `writer` يكتب أول 30 ثانية بقالب `cold-open-writer` (ونحوّل العمودين لنفس شكل `04-script`)، ويستخدم `transition-narration-writer` بين الفصول.
- `creative-director` يبني الخطة بـ `beat-sheet-builder` (أو منحنى Fichtean من `plot-structure`).
- **انتباه:** كلها تكتب إنگليزي افتراضياً. لازم نگولها بالتعليمات: "اكتب بالعراقي حسب `studio/script-rules.md`"، و`dialect-editor` يراجع بعدها.

---

## الجزء الثاني: أدوات البحث العميق داخل الحاوية

### 1. أدوات البحث المدفوعة الي موجودة كإضافات (plugins)
فحصت إعداداتها، ومتغيرات البيئة (ماكو ولا مفتاح بحث محفوظ)، وجربت اتصال صغير بكل وحدة:

| الأداة | تشتغل بدون مفتاح؟ | شنو صار بالتجربة |
|---|---|---|
| **Exa** | ✅ **إي** | خادمها العام `mcp.exa.ai` جاوب، وجاب مدونة Hugging Face التقنية عن الاختراق، وتقرير Reuters، وصفحة ويكيبيديا للحادثة. **هذا أقوى مصدر مجاني لگيته.** عليه حد استخدام مجاني بس ما وصلناله. |
| Tavily | ❌ | يرفض (401 يعني "لازم تسجيل دخول"). يحتاج مفتاح `TAVILY_API_KEY`. |
| Nimble | ❌ | يرفض (401). يحتاج تسجيل دخول بحساب. |
| Bright Data | ❌ | يرفض (401). يحتاج مفتاح `BRIGHTDATA_API_KEY`. |
| TinyFish | ❌ | يرفض: "لازم تسجيل دخول". يحتاج مفتاح `TINYFISH_API_KEY`. |

> ما سجلت بأي خدمة. إذا بيوم تريد Tavily أو Bright Data، بيهم خطط مجانية صغيرة بس تحتاج تسجيل وتحط المفتاح بإعدادات البيئة (**مو بالريبو لأنه عام**). قرارك.

### 2. واجهات مجانية بدون مفتاح (API يعني باب برمجي نسحب منه معلومات)
جربتها كلها من الحاوية:

| المصدر | شنو يعطينا | النتيجة | ملاحظة |
|---|---|---|---|
| **GDELT** | أخبار العالم بأكثر من 65 لغة، ونگدر نطلب العربي بس | ✅ اشتغل (جاب خبر moneycontrol عن الاختراق) | **صارم:** طلب واحد كل 5 ثواني، وجهازنا يشارك عنوان إنترنت ويا غيره، فأحياناً يرفض (429 يعني "كثّرت طلبات، استنى"). |
| **Google News (RSS)** | أخبار بالإنگليزي **وبالعربي** | ✅ ممتاز | جاب أخبار عربية عن الحادثة. |
| **Wikipedia / Wikidata** | مقالات عربية وإنگليزية، ومعلومات منظمة عن الشركات والأشخاص | ✅ يشتغل | أحياناً 429، السكربت يعيد المحاولة. |
| **Hacker News** | نقاشات أهل التقنية | ✅ | جاب خبر BleepingComputer عن الاختراق. |
| **Wayback CDX** | كل النسخ القديمة لأي صفحة | ✅ | لگى نسخة محفوظة لمدونة Hugging Face من 2026/7/28. |
| **SEC EDGAR (بحث نصي)** | ملفات الشركات الأمريكية الرسمية | ✅ | **لگى ملفات تمويل Hugging Face الرسمية (Form D) من 2018 و2019**، وتقرير NVIDIA. يحتاج "هوية" بالطلب فيها إيميل (السكربت يحط إيميل وهمي، وتگدر تغيّره). |
| **CourtListener** | أحكام وقضايا المحاكم الأمريكية | ✅ بحدود | بدون مفتاح: 50 طلب بالساعة و125 باليوم، ومشتركة ويا غيرنا، فأحياناً يرفض. |
| **arXiv** | أبحاث علمية | ✅ | جاب 3 أبحاث عن الحادثة. |
| **Common Crawl** | أرشيف ضخم لصفحات الإنترنت | ✅ (فهرس الأرشيف يفتح) | مفيد للمحترفين، ما حطيته بالسكربت لأنه بطيء. |
| Reddit | نقاشات الناس | ❌ | Reddit **يحجب** الحاوية (403). والبديل PullPush يرفض الوكلاء الآليين. نستخدم Exa بداله، أو تفتحه انت من المتصفح. |
| Google Fact Check Tools | قاعدة تدقيق الحقائق العالمية | ❌ | **يحتاج مفتاح Google** (مجاني بس يحتاج حساب Google Cloud). |

### أمثلة بايثون صغيرة (مجرّبة)
```python
import requests  # البروكسي والشهادة يشتغلن تلقائياً بالحاوية

# أخبار GDELT بالعربي (آخر 6 أشهر)
requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params={
    "query": '"Hugging Face" breach sourcelang:arabic', "mode": "artlist",
    "format": "json", "maxrecords": 10, "timespan": "6m"}).json()

# ويكيبيديا العربية
requests.get("https://ar.wikipedia.org/w/rest.php/v1/search/page",
             params={"q": "أوبن أيه آي", "limit": 5},
             headers={"User-Agent": "Aboodi23-research/1.0"}).json()["pages"]

# Hacker News
requests.get("https://hn.algolia.com/api/v1/search",
             params={"query": "Hugging Face breach", "tags": "story"}).json()["hits"]

# كل نسخ صفحة بأرشيف الإنترنت
requests.get("https://web.archive.org/cdx/search/cdx",
             params={"url": "huggingface.co/blog/agent-intrusion-technical-timeline",
                     "output": "json"}).json()

# ملفات الشركات الأمريكية (لازم هوية بالطلب)
requests.get("https://efts.sec.gov/LATEST/search-index", params={"q": '"Hugging Face"'},
             headers={"User-Agent": "Aboodi23 research research@example.org"}).json()

# أحكام المحاكم الأمريكية
requests.get("https://www.courtlistener.com/api/rest/v4/search/",
             params={"q": '"Hugging Face"', "type": "o"}).json()["results"]

# أبحاث arXiv (يرجع XML)
requests.get("https://export.arxiv.org/api/query",
             params={"search_query": "all:agent AND all:security", "max_results": 5}).text
```

### 3. السكربت الجديد: `scripts/deep-search.py`
**شنو يسوي:** تنطيه موضوع، فيدوّر بـ **9 مصادر بنفس الوقت** (Exa، GDELT بالإنگليزي والعربي، Google News بالإنگليزي والعربي، ويكيبيديا العربية والإنگليزية، Hacker News، Reddit، ملفات SEC، المحاكم، arXiv)، ويشيل المكرر، ويرتّب النتايج من الأحدث للأقدم: **المصدر، التاريخ، العنوان، الرابط**. وبالأخير يفحص أول 5 روابط إذا إلها نسخة محفوظة بأرشيف الإنترنت (حتى لو انحذفت بعدين، عدنا الدليل).

```bash
python3 scripts/deep-search.py "Hugging Face breach AI agents"
python3 scripts/deep-search.py "Theranos" --sources gdelt,wiki,edgar,court --limit 8
python3 scripts/deep-search.py "Nokia collapse" --langs english,arabic,french --json > out.json
```

**التجربة الحقيقية** على "Hugging Face breach AI agents": طلع **27 نتيجة مختلفة** بحوالي 3 دقايق: بيان OpenAI الرسمي، ومدونة Hugging Face التقنية، وReuters وBBC وNBC وNew York Times، و5 أخبار من مواقع عربية، و3 أبحاث arXiv، وملفات تمويل Hugging Face الرسمية بـ SEC، و4 نسخ محفوظة بالأرشيف. المصادر الي كانت مزحومة وقتها (GDELT، ويكيبيديا، المحاكم) طبع سببها بسطر وكمّل الباقي. إذا صار هيچ، نعيد بعد دقايق بس للمصادر الفاشلة: `--sources gdelt,wiki,court`.

**مهم:** النتايج **خيوط للبحث مو حقائق جاهزة**. كل معلومة تدخل السكربت لازم تمر على `fact-checker` و`verified-research` مثل العادة. ونتائج البحث "التقريبية" (مثل بعض نتايج Hacker News أو SEC) ممكن تكون بعيدة عن الموضوع.

**منو يستفيد:** `researcher` و`source-hunter` يشغّلونه أول خطوة بأي حلقة، و`topic-scout` يشوف بيه شكد الموضوع منتشر بالعربي مقابل الإنگليزي.

---

## الخطوات الجاية (قرارك)
1. توافق نضيف الأسطر الستة لـ `skills.manifest` ونشغّل `scripts/update-skills.sh`؟
2. نحدّث ملفات الفريق: `writer` و`tension-auditor` و`creative-director` يستخدمون السكيلزات الجديدة، و`researcher` يبدأ بـ `deep-search.py`.
3. نضيف سطر بجدول السكيلزات بـ `CLAUDE.md`: "بحث سريع بعدة مصادر ← `python3 scripts/deep-search.py "الموضوع"`".
4. (اختياري، بيه حساب) مفتاح Google مجاني لـ Fact Check Tools، أو مفتاح Tavily.

---

## المصادر
- [EveryInc/compound-writing](https://github.com/EveryInc/compound-writing) · [ur-grue/autopunk-media-skills](https://github.com/ur-grue/autopunk-media-skills) · [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) · [pajamadot/thriller](https://github.com/pajamadot/thriller) · [jtydhr88/screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills) · [smeseik-ai/arabic-content-studio](https://github.com/smeseik-ai/arabic-content-studio) · [kashyab12/storygen-skill](https://github.com/kashyab12/storygen-skill)
- [alchaincyf/mrbeast-skill](https://github.com/alchaincyf/mrbeast-skill) · [mediabubble-adv/arabic-skill](https://github.com/mediabubble-adv/arabic-skill) · [CK42BB/vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill) · [tenfoldmarc/script-skill](https://github.com/tenfoldmarc/script-skill) · [jwynia/agent-skills](https://github.com/jwynia/agent-skills) · [dglogan42/Claude-Skills](https://github.com/dglogan42/Claude-Skills) · [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills)
- [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) · [Wikimedia REST](https://www.mediawiki.org/wiki/API:REST_API) · [HN Algolia API](https://hn.algolia.com/api) · [Wayback CDX](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server) · [SEC EDGAR full-text search](https://efts.sec.gov/LATEST/search-index) · [CourtListener API](https://www.courtlistener.com/help/api/rest/) · [arXiv API](https://info.arxiv.org/help/api/) · [Common Crawl Index](https://index.commoncrawl.org/) · [Google Fact Check Tools](https://developers.google.com/fact-check/tools/api) · [Exa](https://exa.ai)
