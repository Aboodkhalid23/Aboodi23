# مكتبة سكيلزات المونتاج

## المنصّبة (تشتغل هسه)
| الغرض | السكيلزات |
|---|---|
| **قواعد الصنعة (اقراها أول)** | `editor/CRAFT.md` · `clip-skills` (كورس MediaStorm) · `video-use` |
| **ستايل Vox (قصاصات ورق)** | `vox-director` · `vox-collage` · `paper-cut` · `map-animation` (خرائط Vox) |
| **مونتاج فيديوهات الكلام** | `video-talkcraft` (108 وصفة حركة، ضد شكل "البوربوينت") · `package-talking-head-video` · `motiontalk` · `ghost-editor` (7 ستايلات، ويقلّد مونتاج تعجبك) · `talking-head-image-overlays` |
| **خط إنتاج يوتيوب (قص ← گرافيكس ← صوت)** | `yt-clean-cut` · `yt-make-tsx` · `yt-clean-audio` · `yt-suggest-sfx` |
| **تجميع Remotion (مونتاج الكلام بالصيني)** | `remotion-assembly` · `remotion-design-system` · `remotion-broll` · `remotion-sfx` · `remotion-gotchas-index` |
| **الحركة والإخراج** | `remotion-motion-graphics` · `motioner` · `animation-principles` · `motion-art-direction` · `design-motion-principles` · `shot-composition` · `diagram-animation` · `bang-motion` · `remotion-video-director` · `remotion-best-practices` |
| **الإيقاع والاحتفاظ بالمشاهد** | `beat-sync-editing` · `retention-pass` (مبنية على Kurzgesagt) · `edl-tighten` |
| **الألوان** | `color-grading` (يطبّق، مثل HDR وLUT والتصحيح) · `color-motion` (يقرر) |
| **الصوت** | `sound-design` · `sound-design-film` (Walter Murch) · `yt-clean-audio` · `yt-suggest-sfx` · `remotion-sfx` |
| **الفحص** | `video-qa` |
| **الذكاء الاصطناعي (شغّال)** | `visual-image-prompts` · `visual-video-prompts` (الوصف) + Higgsfield (التوليد، بموافقة صاحب القناة) |
| **الشورتس (الجزء 3)** | `claude-shorts` |
| **أدوات** | `ffmpeg-recipes` |

## بالفهرس (ما منصّبة، ننزلها وقت الحاجة)
الإضافة: سطر بـ `skills.manifest`، بعدين `bash scripts/update-skills.sh`. كلها مقيّمة **SAFE** بفهرس [awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills).

| المشروع | ليش ممكن نحتاجه |
|---|---|
| `heygen-com/hyperframes` (40 سكيل) | محرك بديل لـ Remotion (HTML وGSAP). بعض السكيلزات فوگ تستخدمه (`paper-cut`، `bang-motion`) |
| `vibe-motion/skills` (15) | حركة ومونتاج بأسلوب "vibe" |
| `iart-ai/motion-skills` (50) | مكتبة حركة كبيرة: خط متحرك، ورسوم بيانات، وWebGL |
| `iart-ai/explainer-video-skills` | رسم على سبورة، وأيزومتري، وملخص السنة |
| `adithya-s-k/manim_skill` | رسوم رياضية بأسلوب 3Blue1Brown (تحتاج Manim) |
| `Anil-matcha/vox-ai-motion-graphics-generator` | Vox كامل، بس يحتاج مفتاح muapi (مدفوع) |
| `darrenli6/JJKoubo` | مونتاج كلام بالصيني (kbcut) |
| `lemomo-ai/lemo-opuscar` | 39 ستايل أفلام، كل واحد وياه وصف جاهز |
| `calesthio/OpenMontage` | استوديو كامل (700+ ملف معرفة). جبير (160 ميگا)، ناخذ منه أجزاء |
| `Vincentwei1021/video-shotcraft` | 152 وصفة لقطة، لفيديوهات المنتجات |
| `AbubakrChan/product-launch-motion` | تشطيب سينمائي وصوت بمستوى التلفزيون |
| `DenisHumen/cinema-skills` | ألوان، ومحاكاة أفلام، ومطابقة لقطات |
| `kajisho5/ffmpeg-skill` | 42 أداة ffmpeg (تشتغل ويه `color-grading`) |
| `hypit-ai/hypit` | يستنسخ فيديو منتشر (الوجه والكلام والبي-رول) |
| `FireRedTeam/FireRed-OpenStoryline`، `0xsline/OpenChatCut` | برامج مونتاج كاملة للوكلاء (تطبيقات مو سكيلزات) |
| `hetpatel-11/Adobe_Premiere_Pro_MCP` | يتحكم ببريمير (يحتاج بريمير على حاسبة) |

## مفاتيح اختيارية تفتح قدرات أكثر (كلها تكلف فلوس، اسأل صاحب القناة قبل)
- `ELEVENLABS_API_KEY`: تنظيف صوت احترافي بالذكاء الاصطناعي، ومؤثرات وموسيقى مولّدة.
- `GEMINI_API_KEY`: `video-qa` "يشوف ويسمع" الفيديو ويطلع المشاكل.
- `PEXELS_API_KEY`: صور ومقاطع مجانية أكثر (المفتاح نفسه ببلاش).
- المفاتيح تنحط بإعدادات البيئة السرية، **ما تنحط بالريبو أبداً**.
