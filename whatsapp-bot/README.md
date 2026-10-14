# رقم واتساب خاص بـ Claude (عن طريق Kapso)

## شلون يشتغل
```
انت تدز رسالة واتساب ← Kapso يستلمها ← يدزها للجسر (worker.js على Cloudflare)
← الجسر يسأل Claude ← يرجّع الجواب لـ Kapso ← يوصلك على الواتساب
```

> ⚠️ هذا Claude عن طريق الـ API (مثل دردشة)، مو نفس جلسة Claude Code الي تشتغل على الريبو.
> يعني يجاوبك ويساعدك بالأفكار، بس ما يگدر يعدّل ملفات أو يسوي commit.

## الي تحتاجه (كلها حسابات باسمك)
| الشي | منين | الكلفة |
|---|---|---|
| حساب Kapso + رقم واتساب | kapso.ai | حسب خطتهم |
| مفتاح Claude API | console.anthropic.com | تدفع على الاستخدام (رسالة الدردشة تكلف أجزاء من السنت) |
| حساب Cloudflare | dash.cloudflare.com | مجاني |

**رقم الواتساب:** لازم رقم مو مسجّل بواتساب عادي (شريحة جديدة، أو رقم تشتريه من Kapso إذا متوفر).

## الخطوات

### 1. Kapso
1. سوّ حساب بـ kapso.ai وربّط رقم من **WhatsApp ← Phone numbers**.
2. من **Integrations ← API keys** سوّ مفتاح، واحفظه (هذا `KAPSO_API_KEY`).

### 2. مفتاح Claude
من console.anthropic.com ← **API Keys** سوّ مفتاح (هذا `ANTHROPIC_API_KEY`)، وحط رصيد صغير (5 دولار تكفي هواية).

### 3. Cloudflare (مكان يشتغل بيه الجسر 24 ساعة)
1. بـ dash.cloudflare.com ← **Workers & Pages ← Create ← Worker**، سمّيه `claude-whatsapp`، واضغط **Deploy**.
2. اضغط **Edit code**، امسح الموجود، والصق كل محتوى `worker.js`، واضغط **Deploy**.
3. انسخ رابط الـ Worker (مثل `https://claude-whatsapp.اسمك.workers.dev`).
4. **Settings ← Variables and Secrets** وأضف (كلها نوع **Secret**):
   - `ANTHROPIC_API_KEY`
   - `KAPSO_API_KEY`
   - `KAPSO_WEBHOOK_SECRET` (تاخذه من الخطوة 4 الجاية)
   - `ALLOWED_NUMBERS` = رقمك الشخصي بدون + (مثال `9647701234567`). إذا أكثر من رقم افصلهم بفارزة.
5. (للذاكرة، مستحسن) **Storage ← KV ← Create namespace**، وبعدين بالـ Worker: **Settings ← Bindings ← Add ← KV**، واسم الربط لازم يكون `MEMORY`.

### 4. اربط Kapso بالجسر
بـ Kapso ← **Webhooks ← Add webhook**:
- الرابط: رابط الـ Worker.
- الحدث: `whatsapp.message.received`.
- انسخ الـ Secret مالته وحطه بـ `KAPSO_WEBHOOK_SECRET` بالخطوة 3.

### 5. جرّب
دز "هلو" من رقمك الشخصي لرقم Kapso. لازم يجيك رد خلال ثواني.
- `/جديد` يمسح الذاكرة ويبدي محادثة جديدة.

## أمان
- المفاتيح تنحط بـ Cloudflare بس، **أبداً** مو بالكود (الريبو عام).
- الجسر يرفض أي رسالة بدون توقيع Kapso الصحيح، ويتجاهل أي رقم مو بـ `ALLOWED_NUMBERS`، حتى محد يصرف من رصيدك.

## إذا ما اشتغل
بالـ Worker ← **Logs** تشوف الأخطاء:
- `bad signature`: الـ Secret غلط أو ناقص.
- `Claude error 401`: مفتاح Claude غلط. `400` ممكن الرصيد خالص.
- `Kapso error`: مفتاح Kapso غلط، أو مرّت 24 ساعة من آخر رسالة منك (واتساب يسمح بالرد بس خلال 24 ساعة من رسالتك).
