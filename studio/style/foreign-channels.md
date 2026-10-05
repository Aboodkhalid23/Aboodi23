# شلون يكتبون أقوى القنوات الأجنبية سكربتاتهم؟

> ملف مرجعي للكاتب والمحرر. نستلهم **التقنية** بس، ما ننسخ النص.
> تاريخ البحث: 2026/10/5. الأرقام والاقتباسات مأخوذة من ترجمات الفيديوهات (captions) المحفوظة بأرشيف الإنترنت، ومن مقابلات ومقالات (المصادر بآخر الملف).
> القواعد الثابتة بـ `studio/script-rules.md` تبقى هي الأعلى. هذا الملف يضيف أدوات، ما يلغي قواعد.

---

## 1. القنوات الي درسناها، وليش

| القناة | نوعها | ليش تهمنا |
|---|---|---|
| **Johnny Harris** | تحقيقات وجغرافيا سياسية، هو يطلع بالكاميرا | أقرب شي لصاحب القناة: وجه + سؤال + تحقيق. أحسن مثال لـ"سلّم الأسئلة" |
| **Veritasium** (Derek Muller) | علوم وقصص اختراعات | دكتوراه بشلون الناس تتعلم من الفيديو. يبدي بالفهم الغلط ويكسره |
| **LEMMiNO** | ألغاز وقضايا غامضة | سرد بارد ودقيق، يبني اللغز خطوة خطوة ويخلي النهاية مفتوحة بصدق |
| **MagnatesMedia** | قصص شركات (صعود وسقوط وفضائح) | نفس نوع محتوانا الأول بالضبط: "القصة المظلمة لشركة مشهورة" |
| **ColdFusion** | تكنولوجيا، شركات، احتيال، ذكاء اصطناعي | يفتح بسؤال "منو؟ ووين؟" ويسوي القصة مطاردة |
| **Wendover Productions** | اقتصاد ولوجستيات "شلون يشتغل الشي" | يبدي من مشهد صغير دقيق (شخص واحد، ساعة محددة) ويكبّر للعالم كله |
| **Kurzgesagt** | علوم مبسطة | سؤال غريب + "أغرب مما تتوقع" + يبسّط بأمثلة من حياتك |
| **Species - Documenting AGI** (Drew Spartz) | ذكاء اصطناعي بأسلوب وثائقي | يوصفون نفسهم "Johnny Harris بس للذكاء الاصطناعي". أقصر جمل وأعلى توتر بكل القنوات |

---

## 2. أرقام: شلون إيقاعهم فعلياً؟

حللنا ترجمات 13 فيديو (تقريباً 80 ألف كلمة). ملاحظة: الترقيم بالترجمات التلقائية مو دقيق 100%، فالأرقام تقريبية بس الفرق بين القنوات واضح.

| الفيديو | متوسط طول الجملة (كلمة) | جمل قصيرة (8 كلمات أو أقل) | أسئلة بكل 1000 كلمة | "But" بكل 1000 كلمة |
|---|---|---|---|---|
| Species: AIs Compete for Control | **9.3** | **53%** | 1.5 | **11.0** |
| Species: AI Parasites | 10.2 | 48% | 5.1 | 10.6 |
| Veritasium: LSD و PCR | 13.6 | 31% | 3.1 | 7.9 |
| Veritasium: مفارقة Newcomb | 14.6 | 31% | **8.8** | 7.1 |
| Johnny Harris: المليارديرية والانتخابات | 14.6 | 32% | 6.5 | 8.2 |
| Johnny Harris: هل الفاشية رجعت؟ | 14.5 | 29% | 2.5 | 7.7 |
| LEMMiNO: Cicada 3301 | 17.3 | 16% | 5.4 | 8.7 |
| LEMMiNO: MH370 | 20.1 | 9% | 0.3 | 5.5 |
| MagnatesMedia: Volkswagen | 21.9 | 7% | 0.4 | 7.9 |
| Wendover: التنبؤ بالطقس | 30.1 | 6% | 0 | 5.3 |

**شنو نتعلم من الجدول:**
- القنوات الي "يحچي بيها شخص للكاميرا" (Johnny, Derek) جملها أقصر وبيها أسئلة أكثر من القنوات الي "يقرا بيها راوي" (Wendover, LEMMiNO).
- **Species هي الأسرع:** نص جملها 8 كلمات أو أقل. هذا بالضبط شرط صاحب القناة (3-8 كلمات). يعني أسلوبنا مو غريب، هو أسلوب أنجح قناة ذكاء اصطناعي هسه.
- كلمة **"But" (بس)** تتكرر 7-11 مرة بكل 1000 كلمة بكل القنوات. يعني تقريباً **كل 100-140 كلمة اكو "بس" تقلب الاتجاه.** هذا قانون "بس/فلهذا" (القسم 4) شغّال بالأرقام.
- سكربتنا 2800 كلمة = لازم يكون بيه تقريباً **20-30 "بس" تقلب القصة**، ومو أقل من 15 سؤال.

---

## 3. السكربت ينكتب حتى ينحچى، مو حتى ينقرا

### شنو يسوون بالضبط
1. **يحچي ويه نفسه وويه المشاهد.** Johnny Harris يگول بنص التحقيق:
   > "Okay, we're getting somewhere, but who paid for the ad?"
   > (زين، دا نوصل لشي، بس منو الي دفع على الإعلان؟)

   كلمات مثل "Okay"، "So"، "I mean"، "Like" = نفس "زين"، "يعني"، "اسمع"، "لا لا لحظة". تخلي الكلام يبين مو مقروه من ورقة.

2. **يعترف إنه ما يعرف.** بداية فيديو الفاشية:
   > "And I have a confession to make, which is, I don't totally understand it. I feel kind of naive."
   > (وعندي اعتراف: آني ما فاهمها زين. أحس روحي ساذج شوية.)

   المقدم مو "أستاذ"، هو "واحد مثلك قرر يحفر". هذا يخلي المشاهد يمشي وياه.

3. **تعليقات جانبية تكسر الجدية** (Johnny Harris عن خريطة الشرق الأوسط):
   > "The Middle East, the part of Asia that Europeans see as the middle of what they see as the east. Sort of arbitrary. Whatever, we call it the Middle East."
   > (الشرق الأوسط، يعني الجزء الي الأوروبيين شافوه بنص الشي الي هم شافوه شرق. شي عشوائي. المهم، نسميه الشرق الأوسط.)

4. **جمل قصيرة ورا بعض للضربة** (Species):
   > "Three companies. Three shots at building a god."
   > (ثلث شركات. ثلث محاولات حتى يصنعون إله.)

5. **ملموس، مو مجرد.** Johnny Harris بالبودكاست "How I Write" گال إن كتابته لازم تكون: بصرية، بسيطة، ملموسة، ومكتوبة للصوت. يكتب السكربت والصورة سوه، والصورة هي الي تحچي القصة والكلام يسندها.

6. **أرقام تنحس بالجسم** (Wendover):
   > "...their payload, about the weight of a grapefruit..."
   > (الجهاز الي بيه، تقريباً بوزن حبة گريب فروت.)

   ما گال "500 غرام". گال شي تتخيله بإيدك.

### القاعدة إلنا
- اقرا كل جملة بصوت عالي. إذا تلعثمت بيها، اقطعها.
- كل 3-4 جمل قصيرة، جملة وحدة أطول "للتنفس" (موجودة بـ script-rules القسم 6).
- حط "زين"، "يعني"، "لحظة لحظة"، "اسمع هاي" بس بمكانها، مو بكل سطر.

---

## 4. محرك التوتر: شلون يخلون المشاهد تحت ضغط من أول ثانية لآخر ثانية

### 4.1 سلّم الأسئلة (Question Ladder)
**الفكرة:** كل جواب يسد سؤال صغير، ويفتح سؤال أكبر منه. المشاهد ما يحس إنه "خلص" ولا مرة.

**أحسن مثال حقيقي:** Johnny Harris، فيديو "How billionaires stole America's elections". هاي الأسئلة بالترتيب بأول 12% من الفيديو:

| مكانها بالفيديو | السؤال | ترجمة |
|---|---|---|
| 0% | "Why did someone put a bunch of effort into scrubbing it from the entire internet?" | ليش واحد تعب حتى يمسح هذا الفيديو من كل الإنترنت؟ |
| 1% | "But who paid for the ad?" | بس منو دفع على الإعلان؟ |
| 2% | "So did she pay for it?" (الإعلان مكتوب عليه اسم قاضية ميتة) | يعني هي دفعت؟ (هي ميتة من 4 سنين!) |
| 4% | "Who is May Mailman?" | منو هاي الي اسمها May Mailman؟ |
| 5% | "...how do they spend $20 million?" | ماعدهم ولا فلس، شلون صرفوا 20 مليون؟ |
| 7% | "So what is Elon Musk Revocable Trust?" | لعد شنو هذا الصندوق الي باسم Elon Musk؟ |
| 11% | "But how much is $15 billion? Like, is that a lot?" | زين 15 مليار شگد؟ يعني هواي؟ |
| 12% | "How is it that some people are spending hundreds of millions?" | شلون ناس تصرف مئات الملايين؟ |

**لاحظ:** بدأ بسؤال صغير جداً (فيديو انمسح)، وكل خطوة كبّرت السؤال، لحد ما وصل لسؤال الحلقة الكبير (شلون الفلوس تشتري الانتخابات). هذا هو السلّم.

Veritasium يسوي نفس الشي بفيديو LSD: "شلون تقرا الـDNA؟" (2%) ← "شلون تفحص حرف واحد بين 6 مليار حرف؟" (14%) ← "بس شلون هذا يساعد؟" (15%) ← "لو ما جان ماخذ LSD، جان اخترع PCR؟" (43%).

### 4.2 قانون "بس / فلهذا" (But / Therefore)
مؤلفين South Park (Trey Parker و Matt Stone) گالوها بصف كتابة بجامعة NYU:
> "If the words 'and then' belong between those beats, you're f\*\*\*ed... You've got something pretty boring."
> (إذا بين مشهد ومشهد تگدر تحط "وبعدين"، انت ضايع. عندك شي ممل.)
>
> "This happens, and therefore this happens. But this happens, therefore this happens."
> (صار هذا، فلهذا صار هذا. بس صار هذا، فلهذا صار هذا.)

**التطبيق علينا:** قبل الكتابة، اكتب الفصول سطر سطر، وبين كل سطرين لازم تنحط "بس" أو "فلهذا". إذا اللي ينحط "وبعدين"، احذف الفصل أو غيّره.

- ❌ "الشركة تأسست. وبعدين كبرت. وبعدين فتحت فروع."
- ✅ "الشركة تأسست. **بس** ماكو بنك رضى يقرضها. **فلهذا** المؤسس رهن بيته. **بس** بعد سنة..."

### 4.3 الحلقات المفتوحة (Open Loops)
- MagnatesMedia يفتح النهاية من البداية: بفيديو Volkswagen گال بأول 40 ثانية إن القصة توصل لـ"طلب شخصي من Adolf Hitler"، وما فسّر هاي الجملة إلا بعد دقايق.
- Species بأول 20 ثانية: "بس هل ذكاء خارق راح يخلّي نفسه ينطفي؟ لو... راح يقاوم؟" والجواب بس بآخر الفيديو.
- القانون الموجود بـ script-rules (حلقة مفتوحة كل 150-200 كلمة) متطابق ويا الي يسوونه.

### 4.4 تصعيد الرهان (Stakes Escalation)
- Species بفيديو "AI Parasites": يبدي بشي مضحك (ChatGPT يمدح فكرة مطعم كورن فليكس معجّن)، وبعدين ذهان، وبعدين حسابات ناس تتغيّر، وبعدين ذكاء يتواصل ويه ذكاء ثاني بشفرة، وبعدين "الجاي أذكى وما راح ينكشف".
- **كل فصل لازم يكون أخطر من الي گبله:** فلوس شخص ← فلوس شركة ← حياة ناس ← العالم كله.

### 4.5 ابدأ بالغلط الي يصدقه الكل (Derek Muller)
Derek سوّى دكتوراه بشلون الناس تتعلم من الفيديو. لگه إن الشرح الواضح المباشر يخلي الطلاب **واثقين أكثر بس ما تعلموا شي**، لأن عدهم فكرة غلط بروسهم وما انكسرت. الفيديوهات الي **تعرض الفهم الغلط أول، وبعدين تكسره**، الطلاب گالوا عنها "محيّرة"، بس **درجاتهم تقريباً تضاعفت**.

**التطبيق:** بكل موضوع، اسأل: "شنو الشي الي الناس متأكدين منه وهو غلط؟" وابدأ منه.
مثال Veritasium (فيديو سرعة الضوء): "طلاب الفيزياء يتعلمون إن سرعة الضوء ثابتة... بس محد قاسها باتجاه واحد أبداً."

### 4.6 فجوة الفضول (العلم وراها)
George Loewenstein (جامعة Carnegie Mellon) سنة 1994: الفضول يصير لما المخ يحس بـ"فجوة" بين الي يعرفه والي يريد يعرفه. والأهم: **الفضول يكون أقوى لما الفجوة صغيرة**. إذا ما تعرف شي أبد، ما تهتم. إذا تعرف نص الشي، تموت حتى تعرف الباقي.

**التطبيق:** أعطِ المشاهد **80% من المعلومة** واحجب الـ20% المهمة. مو تحجب كلشي.
- ❌ "اكو سر عن شركة كبيرة." (ما يعرف شي، ما يهتم)
- ✅ "Volkswagen، شركة الخنفسة الحلوة، بلشت بطلب شخصي من Hitler. شنو كان الطلب؟" (يعرف نصها، يريد الباقي)

---

## 5. الهوك (أول 30 ثانية): أنواعهم بأمثلة حقيقية

| النوع | القناة | الجملة الأصلية | الترجمة |
|---|---|---|---|
| **تحقيق شخصي يبدي بنص الحدث** | Johnny Harris | "I've been looking for a video that has almost entirely disappeared from the internet, but I finally got a copy." | صارلي فترة أدوّر على فيديو تقريباً انمسح من كل الإنترنت، وأخيراً حصلت نسخة. |
| **"الكل يشوفه ومحد يفهمه"** | Veritasium | "Can you explain how a sewing machine works? I mean, think about it. We've all seen them." | تگدر تشرح شلون تشتغل ماكنة الخياطة؟ يعني فكر بيها. كلنا شفناها. |
| **شي مستحيل + بطل غريب** | Veritasium | "...if not for one man who took a lot of drugs and stumbled upon a discovery that unlocked DNA forever. Also, he was kind of a jerk." | ...لولا رجال واحد أخذ هواي مخدرات ولگه بالصدفة اكتشاف فتح الـDNA للأبد. وبالمناسبة، جان شوية وگح. |
| **جدال/انقسام** | Veritasium | "There is a problem that I can't bring up without starting a fight." | اكو مسألة ما أگدر أطرحها إلا وتصير عركة. |
| **تناقض صادم** | Species | "For the first time in history, every major nation agrees on something. It's time to shut it all down." | لأول مرة بالتاريخ، كل الدول الكبيرة متفقة على شي واحد: لازم نطفي كلشي. |
| **المقدم متردد يحچي** | Species | "Guys, I debated about whether I should even make this video. Because it sounds so unbelievable. But everything I'm about to show you is real." | يا جماعة، ترددت هواي أسوي هالفيديو لو لا، لأن ما ينصدگ. بس كل شي راح أراويكم إياه حقيقي. |
| **النهاية المظلمة أولاً** | MagnatesMedia | "Deception… Slavery… and unimaginable cruelty. There are many companies with dark origin stories, but the story of Volkswagen may be the most horrifying." | خداع... عبودية... وقسوة ما تنتخيل. هواي شركات بداياتها مظلمة، بس قصة Volkswagen يمكن أبشعهن. |
| **لغز "منو؟ ووين؟"** | ColdFusion | "In 2016, a large amount of Bitcoin was stolen from an exchange... But who stole the money? And where were they?" | سنة 2016 انسرگت كمية هائلة من البتكوين... بس منو الي سرگها؟ ووين راحوا؟ |
| **تاريخ ومكان بالضبط** | LEMMiNO | "On the 4th of January, 2012, a user on 4chan posted this image..." | بـ2012/1/4، واحد بموقع 4chan نزّل هاي الصورة... |
| **مشهد صغير دقيق** | Wendover | "It's 4:55 AM on a March day at the National Weather Service's Twin Cities forecast facility..." | الساعة 4:55 الفجر، بمحطة أرصاد بأمريكا، باب گراج ينفتح... |
| **سؤال غريب بنبرة جدية مضحكة** | Kurzgesagt | "Today we are answering an age-old very scientific and important question: What if the moon crashes into earth? It's more interesting and weird than you probably think." | اليوم راح نجاوب على سؤال علمي ومهم جداً: شيصير إذا القمر وگع على الأرض؟ أغرب مما تتوقع. |

**شي مشترك بكل الهوكات:**
1. **ماكو ترحيب ولا مقدمة.** يبدي بنص الحدث. (حتى ColdFusion، الي عنده جملة ترحيب ثابتة، يخليها جملة وحدة وبسرعة يدخل بالقصة.)
2. **وعد واضح:** Veritasium گال: "وأوعدك لما تعرف، راح تحس براحة غريبة." يعني يگول للمشاهد شنو راح يطلع بيه.
3. **MrBeast** بملف شركته الداخلي: الدقيقة الأولى هي الأهم بالفيديو كله لأن بيها أكثر ناس تطلع. لازم تطابق وعد العنوان والصورة المصغرة، وتحط بيها أكبر كمية من المعلومة.

---

## 6. هيكل فيديو 15-25 دقيقة (مجمّع من كل القنوات)

| الوقت | الاسم | شنو يصير | مثال من القنوات |
|---|---|---|---|
| 0:00-0:30 | **الهوك** | نص الحدث + لغز ما ينسد إلا بالنهاية + وعد | Johnny: الفيديو الممسوح |
| 0:30-2:00 | **ليش يهمك + خريطة الرحلة** | شنو على المحك، وشلون راح نمشي | Veritasium: "كل قطعة ملابس لبستها انخيطت بهالماكنة" |
| 2:00-3:00 | **أول جواب صغير** | تكافئ المشاهد بسرعة حتى يثق إن الفيديو يوفي | Johnny يلگه اسم الي دفع بأول دقيقتين |
| 3:00 | **إعادة شد (Re-engagement)** | MrBeast يسميها "re-engagement": مفاجأة تخلي المشاهد يگول "لا لا هاي ما توقعتها" | ColdFusion: الحرامية طلعوا زوج وزوجته، وهي "رابر" |
| 3:00-12:00 | **السلّم** | 3-4 فصول، كل فصل: سؤال ← بحث ← جواب جزئي ← سؤال أكبر | Johnny: الإعلان ← الصندوق ← المحكمة العليا ← 1970s |
| 40-60% | **نقطة الانقلاب** | أكبر مفاجأة. القصة تتقلب على المشاهد | Veritasium LSD: الاكتشاف صار لأن ماكنة أخذت شغله |
| 60-85% | **التصعيد للحاضر** | الرهان يكبر. وين وصل هالشي هسه، وشنو الجاي | Species: "الموديلات الجديدة أذكى، وما راح تنكشف" |
| 85-95% | **الجواب الكبير + المعنى** | يسد لغز الهوك، ويربطه بحياة المشاهد | Veritasium: من PCR لـ"الذكاء الاصطناعي ياخذ شغلك" |
| آخر 30 ثانية | **الضربة الأخيرة + فيديو جاي** | جملة ترجع للهوك، وطلب واحد | Species: "إذا تريد تشوف أمثلة حقيقية... شوف هالفيديو" |

**ملاحظات:**
- Johnny Harris يرجع كل فترة لـ"الأوراق المطبوعة على الطاولة" كأنه محقق. هذا **جهاز بصري ثابت** يربط الفصول. إحنا نگدر نسوي نفس الشي (لوح، ملف، شاشة).
- Johnny يستخدم شخصية ثانية (Johnald، نسخة شريرة منه) تحچي بلسان الطرف الثاني. هذا يخلي الحجة المعاكسة تنسمع بدون ملل.
- MagnatesMedia بنص الفيديو يسوي **انتقال للإعلان مربوط بالقصة** ("شفنا شلون رجعوا بنوا الشركة، بس انت شلون تبني مشروعك؟"). ما يقطع القصة فجأة.

---

## 7. النهايات الي توفي بوعد الهوك

| التقنية | المثال | ليش تشتغل |
|---|---|---|
| **ترجع لجملة الهوك نفسها** | Veritasium (ماكنة الخياطة): بدأ بـ"حتى نخترع الماكنة لازم نخترع طريقة خياطة جديدة"، وختم: "All it took was inventing a completely new way to sew." (كل الي احتاجته: طريقة خياطة جديدة تماماً.) | الدائرة تنسد، المخ يرتاح |
| **ربط القصة القديمة بخوف المشاهد اليوم** | Veritasium (LSD): "Mullis اكتشف PCR لأن ماكنة أخذت شغله... وكلنا هسه قدام مستقبل الماكنات بيه تاخذ شغلنا، خصوصاً ويه الذكاء الاصطناعي. وهذا مخيف. بس يمكن يجبرنا نفكر بأفكار أكبر." | قصة من الستينات صارت عن مستقبلك انت |
| **قلب الأدوار (النهاية الساخرة)** | Johnny Harris (المليارديرية): بالنهاية يحچي بلسان الملياردير: "I hope you find this whole thing super boring... I hope you don't care, because that is how I continue to win." (أتمنى هالموضوع يضوجك... أتمنى ما تهتم، لأن هيچ أبقى أربح.) | المشاهد يحس بالتحدي، ويشارك الفيديو |
| **الصدق بأن اللغز ما انحل** | LEMMiNO (MH370): "For now, it seems, the vanishing of Flight 370 will remain a mystery." (حالياً، يبين اختفاء الرحلة 370 راح يبقى لغز.) بس بعد ما عرض كل النظريات ورتبها وگال رأيه | يحترم عقل المشاهد. ما يكذب حتى يسد |
| **سؤال يرجع على المشاهد** | Species: "The question isn't whether something like this could happen. The question is, what are we going to do about it?" (السؤال مو إذا ممكن يصير. السؤال: شنو راح نسوي؟) | يطلع المشاهد وهو يفكر، ويكتب تعليق |
| **"هذا مو آخر كلام"** | Johnny Harris (الفاشية): "This video isn't the final word on fascism. It's just where my understanding starts." (هذا الفيديو مو الكلمة الأخيرة، هذا بس بداية فهمي.) | تواضع يزيد الثقة |

---

## 8. ملاحظات خاصة لمواضيع الذكاء الاصطناعي (من Species و ColdFusion)
- **حوّل الخبر التقني لقصة بيها شخصيات:** Species ما يگول "نموذج لغوي متملق". يگول "النسخة اسمها HH، فريق الأمان گال اكو مشكلة، بس المستخدمين رجعوا أكثر، فنزّلوها."
- **"ودكم تعرفون؟ هذا كله موثق":** بكل فيديو يأكد إن كلشي حقيقي وموثق، لأن الموضوع يبين خيال علمي.
- **أسماء ونسخ وتواريخ دقيقة** (أبريل 2025، نسخة GG، Sam Altman گال بـ X). الدقة هي الي تصنع الخوف، مو المبالغة.
- **انتبه:** Species أحياناً يبالغ بالدراما (عليه انتقادات). إحنا ناخذ الإيقاع بس، وكل ادعاء ننسبه لمصدره حسب script-rules القسم 7.

---

## 9. 15 تقنية نسرقها ونعدلها

كل تقنية وياها مثال بلهجتنا (المواضيع أمثلة بس، مو حقائق للاستخدام بدون بحث).

1. **سلّم الأسئلة** (Johnny Harris): كل جواب يفتح سؤال أكبر منه.
   > "لگيت منو دفع. بس هنا المصيبة: هذا الشخص ماعنده ولا دينار بحسابه. لعد منين جابها؟"

2. **قانون بس/فلهذا** (South Park): ممنوع "وبعدين" بين الفصول.
   > "الشركة جانت رابحة. بس بليلة وحدة طلع تقرير. فلهذا السهم وگع 40%."

3. **ابدأ بالغلط الي الكل يصدقه** (Veritasium): اعرض الفكرة الغلط أول، وبعدين اكسرها.
   > "انت متأكد إن الإعلانات بالتلفون تتسمّعك؟ اسمع، الحقيقة أغرب وأخوف من هيچ."

4. **"الكل يشوفه ومحد يفهمه"** (Veritasium): شي يومي بسيط بس محد يعرف شلون يشتغل.
   > "كل يوم تمسح بطاقتك وتطلع فلوس. بس شلون الفلوس توصل بثانية وحدة لبلد ثاني؟"

5. **المقدّم المحقق** (Johnny Harris): انت مو أستاذ، انت واحد قرر يحفر.
   > "صارلي أسبوع أدوّر على هالورقة. وأخيراً حصلتها. وصدگني، الي بيها ما يتصدگ."

6. **الاعتراف إنك ما تعرف** (Johnny Harris): تواضع يسحب المشاهد وياك.
   > "بصراحة؟ آني ما جنت فاهم هالموضوع. فقررت أفهمه للآخر."

7. **التناقض الصادم بجملة وحدة** (Species): شيئين ما يصيرن سوه، صاروا سوه.
   > "لأول مرة، أمريكا والصين متفقات على شي واحد. والشي هذا يخوّف."

8. **النهاية المظلمة أولاً** (MagnatesMedia): گول وين راح توصل القصة، بس لا تگول شلون.
   > "هالشركة الي تحبها، بدايتها جانت بطلب شخصي من دكتاتور. شنو جان الطلب؟ هسه أگلك."

9. **"منو؟ ووين؟"** (ColdFusion): حوّل الموضوع لمطاردة.
   > "4 مليار دولار اختفت بليلة. السؤال مو شلون. السؤال: منو؟ ووين راحوا؟"

10. **مشهد صغير دقيق يكبر للعالم** (Wendover): شخص واحد، ساعة وحدة، وبعدين الكوكب كله.
    > "الساعة خمسة الفجر. موظف واحد يضغط زر. وهالزر يحدد شگد تدفع انت على البانزين."

11. **رقم تحسه بإيدك** (Wendover): بدل الرقم المجرد، شي تتخيله.
    > "هالشريحة أصغر من حبة رز. وسعرها أغلى من بيت."

12. **سلّم الرهان** (Species): كل فصل أخطر من الي گبله.
    > "بالبداية جان الموضوع نكتة. بعدين صار فلوس. وهسه صار حياة ناس."

13. **إعادة الشد بالدقيقة 3** (MrBeast): مفاجأة تكسر توقع المشاهد قبل ما يمل.
    > "لحظة لحظة. الحرامي الي دورت عليه الشرطة 6 سنين؟ طلع زوج وزوجته يسكنون بشقة عادية."

14. **قلب الأدوار بالنهاية** (Johnny Harris): احچي بلسان الطرف الثاني حتى تهز المشاهد.
    > "ولو آني صاحب الشركة، أتمنى إنت تنسى هالفيديو. لأن نسيانك هو الي يخليني أربح."

15. **الدائرة المسدودة** (Veritasium + قاعدتنا): آخر جملة ترجع لكلمة أو رقم من أول جملة.
    > "بدينا بـ4 مليار اختفت. وهسه تعرف: ما اختفت. جانت قدام عيوننا من أول يوم."

---

## 10. شلون نستخدم هالملف
- **الكاتب:** قبل ما يكتب، يرسم سلّم الأسئلة (8-12 سؤال) ويكتب "بس/فلهذا" بين الفصول.
- **المحرر:** يعد "بس" (لازم 15 أو أكثر بسكربت 2800 كلمة) والأسئلة، ويقرا السكربت بصوت عالي.
- **المدقق:** يتأكد إن النهاية ترجع للهوك، وإن كل ادعاء منسوب لمصدر.
- نوع الهوك يتغير كل حلقة (شوف `episodes/log.md`)، وجدول القسم 5 بيه 11 نوع نختار منها.

---

## المصادر

**ترجمات الفيديوهات (Internet Archive):**
- Veritasium: The Surprising Genius of Sewing Machines: https://archive.org/details/youtube-RQYuyHNLPTQ
- Veritasium: The Man Who Took LSD and Changed The World: https://archive.org/details/youtube-zaXKQ70q4KQ
- Veritasium: This Paradox Splits Smart People 50/50: https://archive.org/details/youtube-Ol18JoeXlVI
- Veritasium: Why No One Has Measured The Speed Of Light: https://www.veritasium.com/videos/2020/10/31/why-no-one-has-measured-the-speed-of-light
- Johnny Harris: How billionaires stole America's elections: https://archive.org/details/youtube--NuXpwB2DV4
- Johnny Harris: Is Fascism Back?: https://archive.org/details/youtube-GV8KGcFqeLc
- Johnny Harris: The Modern Middle East, Explained: https://archive.org/details/youtube-bLOEhycMG78
- LEMMiNO: Cicada 3301: https://archive.org/details/cicada-3301-an-internet-mystery
- LEMMiNO: The Vanishing of Flight 370: https://archive.org/details/the-vanishing-of-flight-370
- MagnatesMedia: The Evil Crimes of Volkswagen: https://archive.org/details/youtube-bS6iXtarkv8
- Wendover Productions: How Weather Forecasting Works: https://archive.org/details/youtube-V0Xx0E8cs7U
- Kurzgesagt: What Happens if the Moon Crashes into Earth?: https://archive.org/details/youtube-lheapd7bgLA
- Species: When Superhuman AIs Compete for Control: https://archive.org/details/youtube-gwfCWDO4LbM
- Species: AI Parasites Are Infecting The Internet: https://archive.org/details/youtube-POtESzTaz0k
- ColdFusion: Bitfinex heist (transcript): https://podscripts.co/podcasts/coldfusion/married-couple-steals-45-billion-in-bitcoin-heist-bitfinex

**مقابلات وتحليلات:**
- Trey Parker & Matt Stone، صف NYU: https://speakola.com/arts/matt-stone-trey-parker-nyu-writing-class-2014
- Johnny Harris، بودكاست How I Write: https://podwise.ai/dashboard/episodes/3299864
- Derek Muller وأبحاث الفهم الغلط: https://fnoschese.wordpress.com/2011/03/17/khan-academy-and-the-effectiveness-of-science-videos/ و https://www.openculture.com/2012/06/expert_gently_asks_whether_khan_academy_videos_promote_meaningful_learning.html و https://www.bobvanvliet.com/notes/designing-effective-multimedia-for-physics-education/
- Veritasium، Clickbait is Unreasonably Effective: https://www.imdb.com/title/tt15251060/
- ملف MrBeast الداخلي: https://www.danielscrivner.com/how-to-succeed-in-mrbeast-production-summary/ و https://www.dexerto.com/youtube/leaked-mrbeast-pdf-reveals-youtubers-secrets-to-video-success-2900841/
- Paddy Galloway عن التغليف: https://www.colinandsamir.com/resources/the-new-rules-of-youtube-from-paddy-galloway
- Loewenstein وفجوة المعلومات: https://psychologyfanatic.com/information-gap-theory/ و https://nautil.us/curiosity-depends-on-what-you-already-know-235803
- Species (Drew Spartz): https://luma.com/r6dfa9fr
- MagnatesMedia وأسلوب الصعود والسقوط: https://faceless.my/youtube/top-faceless-youtube-channels/
- Kurzgesagt وطريقة البحث والتبسيط: https://www.phdnet.mpg.de/208764/episode-25-kurzgesagt-and-visual-science-ft-philipp-dettmer
