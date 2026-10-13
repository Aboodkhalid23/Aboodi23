# الأدوات المدفوعة الي تقوّي سكربتاتنا

> تاريخ البحث: 2026/10/8. هذا الملف يكمّل `tools-level2.md` (الأدوات المجانية).
> الأسعار بالدولار، وأغلبها شفتها من صفحة الشركة نفسها بنفس اليوم. الي ما گدرت أفتح صفحتها كتبت جنبها **(مصدر ثانوي)** أو **(ما متأكد)**.
> **ما اشتريت ولا شي، وما سوّيت commit.** هذا تقرير، والقرار إلك لأن بيه فلوس.

---

## قبل كلشي: شي لازم تعرفه

1. **الأدوات تقوّي البحث والمعلومة والتغليف، مو القصة نفسها.** الدحيح وعمر عبد الرب وJohnny Harris وMagnatesMedia يفوزون بـ: معلومة محد يعرفها، وسؤال يمشي ويا المشاهد لآخر الفيديو، ومصدر أصلي (وثيقة، محكمة، تقرير). فأقوى شي نشتريه هو الي يجيب **مصادر أصلية أعمق وأسرع**. الكتابة تبقى عند فريقنا (`studio`).
2. **عدنا 3 أدوات بحث مثبتة جاهزة، بس ناقصها مفتاح:** Tavily وExa وBright Data. يعني بمجرد ما تحط المفتاح، تشتغل فوراً بدون أي تثبيت.
3. **المفتاح (API key)** يعني رقم سري تعطيه الشركة حتى البرنامج يستخدم حسابك. **الريبو عام**، فالمفتاح **ما ينحط بأي ملف أبداً**، ولا تلصقه بالشات. ينحط بإعدادات البيئة السحابية بس (الشرح تحت).
4. **الدفع من العراق:** أغلب هالشركات تحتاج بطاقة Visa أو Mastercard دولية تشتغل أونلاين. إذا بطاقتك ترفض، هاي أول مشكلة راح تواجهك.

---

## شلون تضيف أي مفتاح (نفس الخطوات لكل أداة)

1. سوّي حساب بموقع الشركة، وروح لصفحة **API Keys**، واضغط إنشاء مفتاح، وانسخه.
2. **حط حد صرف شهري** (spending limit) بصفحة الفوترة (Billing) حتى ما تنصدم بفاتورة. أكتبلك الحد المقترح لكل أداة.
3. بجلسة Claude Code: افتح قائمة **البيئة السحابية** من شريط العنوان فوق، واضغط **Edit**، وبقسم **Network secrets** (أو **Environment variables** إذا ما موجود) أضف سطر بالاسم الي أكتبه لك بالضبط، والقيمة هي المفتاح.
4. افتح جلسة جديدة، وگلي "جرّب المفاتيح"، وأني أفحصها.

---

## قائمة الشراء المرتبة

### 🥇 أولوية 1 (هذني يغيرون السكربت فعلاً)

| # | الأداة | الكلفة الشهرية | شنو تغيّر بسكربتاتنا | الدعم العربي | اسم المتغير |
|---|---|---|---|---|---|
| 1 | **Gemini API** (لسكيل `deep-research` المثبت عدنا) | حسب الاستخدام: **2 إلى 5$ للبحث الواحد**. لحلقتين بالأسبوع تقريباً **40 إلى 80$** | تقرير بحث عميق بمصادر خلال 5 إلى 10 دقايق قبل ما يبدأ الكاتب. يلگى زوايا ومعلومات ثانوية ما تطلع ببحث عادي. الأسعار: Gemini 3.1 Pro إدخال 2$ وإخراج 12$ لكل مليون توكن، وبحث Google أول 5,000 بالشهر مجاناً وبعدها 14$ لكل ألف | ✅ يقرا ويكتب عربي زين، والمصادر أغلبها إنگليزي وهذا الي نريده | `GEMINI_API_KEY` |
| 2 | **Exa** ([exa.ai](https://exa.ai/pricing)) | حسب الاستخدام: البحث 7$ لكل ألف، والبحث العميق 12 إلى 15$ لكل ألف، وقراءة الصفحات 1$ لكل ألف. نتوقع **20 إلى 40$** | بحث "بالمعنى" مو بالكلمات: تگله "شهادة موظف سابق عن انهيار الشركة الفلانية" فيجيب مقالات ومدونات وأوراق ما تطلع بـ Google. **أقوى أداة للمعلومة الي محد يعرفها.** ومثبت عدنا (`exa`) | ⚠️ يفهم العربي، بس قوته بالمصادر الإنگليزية | `EXA_API_KEY` |
| 3 | **Tavily** ([tavily.com](https://docs.tavily.com/documentation/api-credits)) | خطة **Project بـ 30$** (4,000 رصيد). البحث العادي رصيد واحد، والمتقدم رصيدين، والبحث العميق 15 إلى 250 رصيد | بحث سريع بنتائج نظيفة جاهزة للذكاء الاصطناعي، وسحب نص الصفحات، وتتبّع موقع كامل (مثلاً كل بيانات شركة على موقعها). يخلي `researcher` و`fact-checker` يفتحون مصادر أكثر بنفس الوقت. ومثبت عدنا (`tavily`) | ⚠️ نفس Exa | `TAVILY_API_KEY` |
| 4 | **ElevenLabs** ([elevenlabs.io](https://elevenlabs.io/pricing)) | **Creator بـ 22$** (أول شهر 11$). إذا ردت أكثر: **Pro بـ 99$** | (أ) **نستنسخ صوتك** (Professional Voice Clone، موجود من خطة Creator)، فتسمع الهوك والسكربت **بصوتك وبلهجتك** قبل التصوير، وتعرف وين يثقل الكلام. هذا أدق بهواية من صوت "باسل" المجاني. (ب) **Scribe** يحوّل حلقات المنافسين لكتابة بـ 0.22$ للساعة حتى نحلل هيكلهم | ✅ يدعم العربي (مكتوب: سعودي وإماراتي). اللهجة العراقية تطلع زينة لأن الصوت المستنسخ صوتك انت. دقة Scribe بالعربي "جيدة" (خطأ 10 إلى 20%) | `ELEVENLABS_API_KEY` |
| 5 | **vidIQ** (متصل عدنا هسه) | هسه انت على الخطة المحدودة (150 رصيد بالشهر، يتجدد 7 تشرين الثاني). **Boost تقريباً 39$ شهري** **(مصدر ثانوي)**، و**Max تقريباً 79 جنيه إسترليني (حوالي 100$)** **(مصدر ثانوي، ما متأكد)** | رصيد أكثر لأدوات متصلة عدنا: فيديوهات المنافسين الي نجحت أكثر من معدلها (outliers)، وتقييم العنوان والغلاف، وسحب ترجمة أي فيديو. هسه نخاف نستخدمها حتى ما يخلص الرصيد | ✅ يشتغل على أي فيديو بأي لغة | **ماكو مفتاح**: ترقّي الخطة من حسابك بموقع vidIQ، وهي تشتغل وحدها بنفس الربط |

**الي لازم تسويه للأولوية 1:**
- Gemini: افتح [aistudio.google.com](https://aistudio.google.com) ← Get API key ← فعّل الفوترة (Billing) بـ Google Cloud ← حد صرف **100$**.
- Exa: [dashboard.exa.ai](https://dashboard.exa.ai) ← API Keys ← اشحن رصيد **50$** أول مرة.
- Tavily: [app.tavily.com](https://app.tavily.com) ← اشترك بـ Project ← انسخ المفتاح.
- ElevenLabs: اشترك بـ Creator ← انسخ المفتاح من Developers ← وبعدين **سجّل 30 دقيقة من صوتك** وانت تحچي طبيعي (أني أجهزلك نص تقراه) حتى نسوي الاستنساخ.
- vidIQ: رقّي الخطة من موقعهم، وگلي حتى أتأكد من الرصيد.

### 🥈 أولوية 2 (تقوية واضحة، بس بيها تداخل)

| # | الأداة | الكلفة الشهرية | شنو تضيف | العربي | اسم المتغير |
|---|---|---|---|---|---|
| 6 | **Perplexity Sonar API** ([الأسعار](https://docs.perplexity.ai/getting-started/pricing)) | حسب الاستخدام. sonar-pro: إدخال 3$ وإخراج 15$ لكل مليون توكن + 6 إلى 14$ لكل ألف طلب. sonar-deep-research: 5$ لكل ألف بحث + توكنز. نتوقع **20 إلى 50$** | "رأي ثاني" بمصادر مختلفة عن Gemini. لما محركين بحث يتفقون على معلومة، الثقة أعلى. مفيد لـ `fact-checker` | ✅ زين بالعربي | `PERPLEXITY_API_KEY` |
| 7 | **Bright Data** ([الأسعار](https://brightdata.com/pricing/serp)) | **أول 5,000 طلب بالشهر مجاناً**، وبعدها 1.5$ لكل ألف. نتوقع **0 إلى 15$** | يفتح المواقع الي تحجب البرامج، ويجيب نتائج Google **من بلد معيّن** (شنو يشوف الأمريكي عن الموضوع)، ويسحب تعليقات يوتيوب وتيك توك. ومثبت عدنا (`brightdata-plugin`) | ✅ | `BRIGHTDATA_API_TOKEN` |
| 8 | **Storyblocks** ([الأسعار](https://www.storyblocks.com/pricing)) | **Unlimited All Access بـ 30$** (اشتراك سنوي) | لقطات B-roll وموسيقى بلا حد. ما يغيّر السكربت، بس يخلي الكاتب يكتب "مشهد" ويعرف إنه موجود | لا يهم | ماكو مفتاح للأفراد (موقع بس) |
| 9 | **Artlist Max** (متصل عدنا للتوليد) | تقريباً **40$** سنوي **(مصدر ثانوي)** | لقطات 8K وموسيقى ومؤثرات وتوليد صور وفيديو بالذكاء الاصطناعي. إذا عندك اشتراك، كمّل بيه بدل Storyblocks، مو الاثنين | لا يهم | ماكو مفتاح (الربط موجود) |
| 10 | **ميزانية أرشيف لكل حلقة** | **50 إلى 150$ للحلقة** حسب الحاجة | لقطات تاريخية أصلية: [CriticalPast](https://www.criticalpast.com/) (حروب، فضاء، الحرب الباردة، ترخيص دائم، السعر بالسلة)، وPond5 (تقريباً 59$ للقطة العادية و149$ للمميزة **(مصدر ثانوي)**)، وBritish Pathé وAP Archive وGetty (سعر بالطلب، غالي). نشتري **بس لما الحلقة تحتاج لقطة ما موجودة مجاناً** بأرشيف الإنترنت | لا يهم | ماكو مفتاح |

### 🥉 أولوية 3 (اختياري، أو بس للباقة القصوى)

| الأداة | الكلفة | ليش بالآخر |
|---|---|---|
| **OpenAI API** (بحث عميق وتحويل صوت لكتابة) | البحث بالويب 10$ لكل ألف، والتحويل من 0.0045$ للدقيقة. سعر نماذج البحث العميق **ما گدرت أتأكد منه** | محرك بحث ثالث. يفيد بس إذا ردنا 3 محركات تتأكد من بعض. المتغير `OPENAI_API_KEY` |
| **1of10** ([الأسعار](https://1of10.com/pricing)) | Basic بـ 15$، Pro بـ 69$ | يلگى فيديوهات انفجرت أكثر من معدل قناتها، وأفكار تغليف. **ما بيه ربط بالفريق** (موقع بس)، وأداة `yt-viral` المجانية عدنا تسوي نفس الفكرة |
| **Firecrawl** ([الأسعار](https://www.firecrawl.dev/pricing)) | Hobby بـ 19$ | يسحب ملفات PDF وصفحات معقدة. Tavily وBright Data يغطونه. المتغير `FIRECRAWL_API_KEY` |
| **ViewStats** (مال MrBeast) | Pro تقريباً 50$ شهري أو 40$ سنوي **(مصدر ثانوي)** | تحليل ممتاز، بس موقع بس وماكو ربط بالفريق، ويتداخل ويا vidIQ |
| **SawtakArabi** ([الريبو](https://github.com/SawtakArabi/skill)) | رصيد مسبق، **السعر ما منشور** | صوت عربي بلهجات، بس **ما مكتوب إنه يدعم العراقي** (مثالهم مصري). صوتك المستنسخ بـ ElevenLabs أحسن. المتغير `SAWTAK_API_KEY` |
| **Pangram** (كاشف كتابة الذكاء الاصطناعي) | 20$ | يگولون يدعم لغات كثيرة، بس **ما گدرت أتأكد من العربي**. شوف الملاحظة تحت |

### ❌ ما أنصح بيها

| الأداة | ليش لا |
|---|---|
| **Spotter Studio** (49$ شهري) | **مشروط تكون من أمريكا أو كندا أو بريطانيا أو أستراليا أو أوروبا** (مصدر ثانوي). العراق ما مشمول |
| **Subscribr** (99 إلى 499$) | يكتب سكربتات بنفسه، وما مذكور إنه يدعم العربي. فريقنا يسوي هالشغلة أحسن وبلهجتك |
| **TubeBuddy Legend** | السعر ما ظهر بالصفحة، ويتداخل ويا vidIQ |
| **Social Blade** | الصفحة حجبتني. الإحصائيات الأساسية مجانية وتكفي |
| **GPTZero وOriginality.ai** | **ما مذكور العربي** بأي وحدة منهم. Originality بـ 14.95$ شهري |
| **NewsAPI** (449$ شهري) | غالي هواية. GDELT (أرشيف أخبار عالمي) **مجاني** ويسوي الشغلة |
| **SerpAPI** (25 إلى 75$) | Bright Data يسوي نفس الشي وأرخص |
| **Deepgram** (0.0043$ للدقيقة) | الصفحة ما تگول إنه يدعم العربي. ElevenLabs Scribe و`faster-whisper` المجاني يكفون |
| **Azure TTS** | الأسعار ما ظهرت، وأداة `edge-tts` المجانية تستخدم نفس أصوات Azure العراقية |
| **أسواق السكيلزات المدفوعة** (KissMySkills بـ 14.99$ للسكيل، Claude Protocol بـ 3.99$، Agensi Pro بـ 9$ شهري) | الجودة ما مضمونة، وكل سكيل لازم ينفحص أمنياً، والمجاني الي عدنا أقوى. ماكو متجر رسمي مدفوع من Anthropic |

**ملاحظة عن كاشفات "الكتابة الآلية":** كلها مدربة على الإنگليزي، والعربي العامي (اللهجة العراقية) نقطتها العمياء. فنتيجتها على سكربتنا ما تنصدّق. الأحسن: سكيل `anti-ai-writing` المثبت عدنا، وتسمع السكربت بصوتك المستنسخ، و**قاعدة ذهبية: إذا جملة ما تگولها انت بحياتك، تنشال.**

---

## الباقات

### 💪 الباقة القوية: تقريباً **180$ بالشهر**
| الأداة | الكلفة |
|---|---|
| Gemini (البحث العميق) | 50$ |
| Exa | 30$ |
| Tavily Project | 30$ |
| ElevenLabs Creator | 22$ |
| vidIQ Boost | 39$ |
| Bright Data | 0 إلى 10$ |
| **المجموع** | **حوالي 180$** |

هذي تغطي: بحث أعمق 3 مرات، ومصادر أصلية، وتسمع السكربت بصوتك، وتحليل منافسين بلا خوف من الرصيد.

### 🚀 الباقة القصوى: تقريباً **920$ بالشهر**
| الأداة | الكلفة |
|---|---|
| Gemini | 100$ |
| Exa | 80$ |
| Tavily Bootstrap (15,000 رصيد) | 100$ |
| Perplexity Sonar | 50$ |
| OpenAI (محرك ثالث) | 50$ |
| ElevenLabs Pro | 99$ |
| vidIQ Max | حوالي 100$ |
| 1of10 Pro | 69$ |
| Artlist Max أو Storyblocks | 40$ |
| Bright Data | 30$ |
| Firecrawl Hobby | 19$ |
| ميزانية أرشيف (حلقة أو اثنين) | 150$ |
| **المجموع** | **حوالي 890 إلى 920$** |

**رأيي الصريح:** الفرق بين القوية والقصوى بجودة السكربت **صغير**. القصوى تضيف سرعة ولقطات أرشيف ورأي ثالث بالمعلومة. ابدأ بالقوية شهر، ونقيس، وبعدين نزيد.

---

## شنو أسوي أني بعد ما تحط المفاتيح
1. أفحص كل مفتاح يشتغل (بدون ما أطبعه).
2. أحدّث الفريق: `researcher` يبدأ بـ Gemini، وبعدين Exa للمصادر الأصلية، و`fact-checker` يتأكد بـ Tavily (وPerplexity إذا اشتريته)، و`delivery-tester` يسمع السكربت بصوتك.
3. أكتب تقرير صرف شهري صغير حتى تعرف كل أداة شگد كلفت وشگد فادت.

---

## المصادر
- [Tavily credits](https://docs.tavily.com/documentation/api-credits) · [Exa pricing](https://exa.ai/pricing) · [Perplexity pricing](https://docs.perplexity.ai/getting-started/pricing) · [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Firecrawl pricing](https://www.firecrawl.dev/pricing) · [Bright Data SERP](https://brightdata.com/pricing/serp) · [SerpAPI pricing](https://serpapi.com/pricing) · [NewsAPI pricing](https://newsapi.org/pricing) · [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- [ElevenLabs pricing](https://elevenlabs.io/pricing) · [ElevenLabs API pricing](https://elevenlabs.io/pricing/api) · [ElevenLabs TTS languages](https://elevenlabs.io/docs/overview/capabilities/text-to-speech) · [ElevenLabs Scribe languages](https://elevenlabs.io/docs/overview/capabilities/speech-to-text) · [Deepgram pricing](https://deepgram.com/pricing) · [SawtakArabi/skill](https://github.com/SawtakArabi/skill)
- [1of10 pricing](https://1of10.com/pricing) · [Subscribr pricing](https://subscribr.ai/pricing) · [ViewStats pricing](https://www.viewstats.com/pricing) · [TubeBuddy pricing](https://www.tubebuddy.com/pricing) · مصادر ثانوية: [vidIQ (alanspicer)](https://alanspicer.com/vidiq-pricing-2026/) · [vidIQ (1of10 blog)](https://1of10.com/blog/vidiq-pricing/) · [ViewStats (outlierkit)](https://outlierkit.com/resources/viewstats-pricing/) · [Spotter (outlierkit)](https://outlierkit.com/resources/spotter-studio-pricing/)
- [Originality.ai pricing](https://originality.ai/pricing) · [GPTZero pricing](https://gptzero.me/pricing) · [Pangram pricing](https://www.pangram.com/pricing)
- [Storyblocks pricing](https://www.storyblocks.com/pricing) · [CriticalPast](https://www.criticalpast.com/) · [British Pathé copyright](https://www.britishpathe.com/copyright) · مصادر ثانوية: [Artlist (cchound)](https://www.cchound.com/artlist/artlist-subscription-plans-and-pricing/) · [Pond5 (footagesecrets)](https://www.footagesecrets.com/agencies/pond5/)
- أسواق السكيلزات (مصادر ثانوية من البائعين نفسهم): [kissmyskills](https://kissmyskills.com/blogs/news/best-claude-skills-marketplaces) · [claudeprotocol](https://claudeprotocol.com/blog/where-to-buy-claude-skills)
