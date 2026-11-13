# إضافة الوصفات الجديدة تلقائياً (تعليمات للمهمة المجدولة)

هذا الملف تقراه مهمة Claude المجدولة كل ساعة. الشيفات يصوّرون وصفة من داخل التطبيق، والصورة تنحفظ بمجلد بالدرايف، والمهمة تضيفها للتطبيق.

## الملفات
- `apps/tinta/data.js`: كل الوصفات (المصدر الوحيد). عدّل هنا بس.
- `apps/tinta/app.js` و`apps/tinta/src.html`: كود التطبيق وشكله.
- `apps/tinta/build.py`: يبني `links/tinta/index.html` من الملفات فوگ.
- `links/tinta/config.js`: رابط استلام الصور (`window.TINTA_UPLOAD`).
- الفرع الي ينشر الموقع: `claude/github-skills-development-3orc6c` (أي push لـ `links/**` ينشر خلال دقيقتين).

## الخطوات
1. اقرا الرابط من `links/tinta/config.js`. إذا فارغ: وقّف، ماكو شي تسويه.
2. `curl -sL "<الرابط>"` يرجّع `{"ok":true,"files":[...]}`. كل ملف بيه `id` و`desc` (JSON: `group` و`name` و`page` و`pages`). إذا القائمة فارغة: وقّف بدون commit.
3. جمّع الملفات حسب `group`. كل مجموعة = وصفة وحدة (الصفحات بالترتيب حسب `page`).
4. نزّل كل صورة: `curl -sL "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t" -o <ملف>` واقراها (كبّر المنطقة إذا بيها لمعة، ولا تخمّن أرقام).
5. إذا الصورة مو وصفة (صورة غلط، فارغة، ما تنقرا): لا تضيف شي، بس علّمها مخلّصة (خطوة 8).
6. أضف الوصفة لآخر مصفوفة `R` بـ `data.js` بنفس الشكل الموجود:
   `{id:'...',c:'<قسم>',n:['اسم فنلندي','English name'],f:'<id أول صورة>',added:'YYYY-MM-DD',p:[{i:[[كمية,'وحدة','فنلندي','English'],...],s:[['خطوة فنلندي','English step'],...]}]}`
   - الأقسام: kastike, majo, oljy, pesto, voi, liemi, keitto, pohja, lisuke, mari, sailyke, mauste, jalki.
   - الوحدات: g, kg, ml, cl, dl, l, tl, rkl, kpl, prk, pss, pnt, rss, tlk, levy, tuubi, osa. الكمية بدون رقم = `null` ووحدة `''`.
   - `v:1` إذا الوصفة نباتية. `note:['فنلندي','English']` لأي ملاحظة مهمة.
   - إذا الورقة ما بيها طريقة تحضير: اكتب طريقة معقولة وحط `gen:1` بالجزء.
   - إذا رقم ما ينقرا أو مشكوك: حط ملاحظة `note` تگول "tarkista" ولا تخمّن.
   - لا تحط أسماء موظفين ولا كلمات وسخة. `id` لازم يكون فريد.
   - إذا نفس الوصفة موجودة (نفس الاسم): حدّث الموجودة بدل ما تكررها.
7. `python3 apps/tinta/build.py && node --check /tmp/tinta-check.js`، وغيّر `tinta-vN` بـ `links/tinta/sw.js` لرقم أعلى، وcommit وpush للفرع فوگ.
8. بعد ما ينجح الـ push، علّم كل صورة مخلّصة: `curl -sL -X POST -d '{"action":"done","id":"<id>"}' "<الرابط>"`.
