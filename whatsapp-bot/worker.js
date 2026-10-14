// جسر واتساب ⇄ Claude
// Kapso يدز رسالة الواتساب لهنا (webhook)، نسأل Claude، ونرجع الجواب للواتساب.
// يشتغل على Cloudflare Workers (مجاني). خطوات التشغيل بـ README.md بنفس المجلد.
//
// المتغيرات (تنحط بإعدادات الـ Worker، مو بالكود، لأن الريبو عام):
//   ANTHROPIC_API_KEY      مفتاح Claude (سري)
//   KAPSO_API_KEY          مفتاح Kapso (سري)
//   KAPSO_WEBHOOK_SECRET   سر توقيع الـ webhook من Kapso (سري)
//   ALLOWED_NUMBERS        أرقامك المسموحة، مفصولة بفارزة، بدون + (مثال: 9647701234567)
//   CLAUDE_MODEL           اختياري، الافتراضي claude-opus-5-5
// وربط KV اختياري باسم MEMORY حتى Claude يتذكر آخر المحادثة.

const SYSTEM_PROMPT = `انت مساعد شخصي لصانع محتوى يوتيوب عراقي، تحچي وياه بالواتساب.
قناته تحچي عن مواضيع عالمية (قصص شركات، وثائقيات، ترندات، أسئلة غريبة) باللهجة العراقية.
رد باللهجة العراقية، بكلام بسيط ومختصر يناسب الواتساب. لا تستخدم إنگليزي إلا لأسماء علم.
ساعده بأفكار الحلقات، والهوكات، والعناوين، وأي سؤال ثاني.`;

const MAX_HISTORY = 20; // آخر كم رسالة نتذكرها
const WHATSAPP_LIMIT = 4000; // حد طول رسالة الواتساب تقريباً

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") return new Response("شغّال ✅", { status: 200 });

    const raw = await request.text();
    const ok = await verifySignature(raw, request.headers.get("x-webhook-signature"), env.KAPSO_WEBHOOK_SECRET);
    if (!ok) return new Response("bad signature", { status: 401 });

    if (request.headers.get("x-webhook-event") !== "whatsapp.message.received") {
      return new Response("ignored", { status: 200 });
    }

    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      return new Response("bad json", { status: 400 });
    }

    // Kapso يرد 200 خلال 10 ثواني، فنرد فوراً ونكمل الشغل بالخلفية.
    const events = body.batch ? body.data : [body];
    ctx.waitUntil(Promise.all(events.map((e) => handleEvent(e, env).catch((err) => console.error(err)))));
    return new Response("ok", { status: 200 });
  },
};

async function handleEvent(event, env) {
  const msg = event.message;
  const phoneNumberId = event.phone_number_id || event.conversation?.phone_number_id;
  const from = msg?.from || event.conversation?.phone_number;
  if (!msg || !phoneNumberId || !from) return;

  // بس أرقامك تگدر تحچي وياه، حتى محد غريب يصرف من رصيدك.
  const allowed = (env.ALLOWED_NUMBERS || "").split(",").map((n) => n.trim().replace(/^\+/, "")).filter(Boolean);
  if (!allowed.includes(from)) return;

  // Kapso ممكن يدز نفس الرسالة مرتين، فنتجاهل المكررة.
  if (env.MEMORY && msg.id) {
    if (await env.MEMORY.get(`seen:${msg.id}`)) return;
    await env.MEMORY.put(`seen:${msg.id}`, "1", { expirationTtl: 86400 });
  }

  const text = msg.text?.body || msg.kapso?.content;
  if (!text) {
    await sendWhatsApp(env, phoneNumberId, from, "هسه أفتهم بس الرسائل المكتوبة 🙏");
    return;
  }

  if (text.trim() === "/جديد") {
    if (env.MEMORY) await env.MEMORY.delete(`chat:${from}`);
    await sendWhatsApp(env, phoneNumberId, from, "تمام، بدينا محادثة جديدة 🆕");
    return;
  }

  const history = env.MEMORY ? JSON.parse((await env.MEMORY.get(`chat:${from}`)) || "[]") : [];
  history.push({ role: "user", content: text });

  const reply = await askClaude(env, history);
  history.push({ role: "assistant", content: reply });

  if (env.MEMORY) {
    // نخلي البداية دائماً رسالة منه (user) مثل ما يطلب Claude.
    let trimmed = history.slice(-MAX_HISTORY);
    while (trimmed.length && trimmed[0].role !== "user") trimmed = trimmed.slice(1);
    await env.MEMORY.put(`chat:${from}`, JSON.stringify(trimmed), { expirationTtl: 7 * 86400 });
  }

  for (const part of splitText(reply, WHATSAPP_LIMIT)) {
    await sendWhatsApp(env, phoneNumberId, from, part);
  }
}

async function askClaude(env, messages) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      // إذا Claude رفض طلب لأسباب أمان، يحوّله تلقائياً لنموذج ثاني.
      "anthropic-beta": "server-side-fallback-2026-07-01",
    },
    body: JSON.stringify({
      model: env.CLAUDE_MODEL || "claude-opus-5-5",
      max_tokens: 4000,
      system: SYSTEM_PROMPT,
      output_config: { effort: "low" }, // جواب سريع ورخيص يناسب الدردشة
      fallbacks: "default",
      messages,
    }),
  });

  if (!res.ok) {
    console.error("Claude error", res.status, await res.text());
    return "صار خلل بالاتصال بـ Claude، جرّب بعد شوية 🙏";
  }
  const data = await res.json();
  if (data.stop_reason === "refusal") return "ما أگدر أساعد بهذا الطلب.";
  const out = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
  return out || "ما طلع عندي جواب، عيد السؤال بطريقة ثانية.";
}

async function sendWhatsApp(env, phoneNumberId, to, body) {
  const res = await fetch(`https://api.kapso.ai/meta/whatsapp/${phoneNumberId}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": env.KAPSO_API_KEY },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      recipient_type: "individual",
      to,
      type: "text",
      text: { preview_url: false, body },
    }),
  });
  if (!res.ok) console.error("Kapso error", res.status, await res.text());
}

async function verifySignature(raw, signature, secret) {
  if (!secret || !signature) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw));
  const expected = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const given = signature.replace(/^sha256=/, "").toLowerCase();
  if (given.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ given.charCodeAt(i);
  return diff === 0;
}

function splitText(text, limit) {
  const parts = [];
  for (let i = 0; i < text.length; i += limit) parts.push(text.slice(i, i + limit));
  return parts;
}
