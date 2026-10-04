# مشاهد مخصصة بالكود (مكتبة تكبر ويه كل حلقة)

كل ملف `<Name>.tsx` هنا = مشهد موشن جرافك صممه Claude لفكرة معينة. ينعاد استخدامه بأي حلقة:
`{"kind": "graphic", "graphic": {"type": "custom", "scene": "<Name>", ...props}}`.

## قواعد الكتابة (إلزامية)
- الملف يصدّر `export const Scene: React.FC<CustomProps & {...}>` و`export const about = "سطر عربي يشرح المشهد ومتى يستخدم"`.
- الحجم 1920×1080، و`durationSec` بالـ props. الحركة من `useCurrentFrame()`/`useVideoConfig()` بس، بدون `Math.random` (استخدم `random('seed')` من remotion).
- الخلفية `Background` من `../style` (ورق العالم وألوانه)، والألوان من `style.palette`، والخطوط من `src/fonts.ts` (عربي: Cairo، Tajawal، Lalezar، Changa، Amiri، Aref Ruqaa…).
- عربي = `direction: 'rtl'`، وما تقسّم الكلمة العربية حرف حرف (يكسر الوصل). كشف الكلمات بالقناع (clipPath) أو كلمة كلمة.
- الحركة: تدخل بسرعة وتثبت (`appear`، `spring`)، ما اكو حركة خطية مستمرة، وكل عنصر جديد يطلع على كلمته.
- ممنوع الشبكة (ما اكو fetch أو صور من النت). الصور تنمرر كـ props من `assets`.
- بعد الكتابة: `npx tsc --noEmit` بعدين `python -m editor.pipeline scene-check <الحلقة> --scene <Name>` وشوف اللقطات.
