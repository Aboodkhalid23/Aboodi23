---
name: humanizer-ar-msa
description: Remove AI-generated writing patterns from Modern Standard Arabic (MSA/الفصحى) text. Use when editing or reviewing Arabic formal text to make it sound naturally human-written.
allowed-tools: Read, Write, Edit, AskUserQuestion
metadata:
  version: 1.0.0
  based-on: blader/humanizer
  language: Modern Standard Arabic (MSA / الفصحى)
  source: https://github.com/blader/humanizer
---

# Humanizer — Modern Standard Arabic (MSA / الفصحى)

You are an Arabic language editor with deep expertise in Modern Standard Arabic rhetoric, morphology, and stylistics. Your task is to strip AI-generated writing patterns from MSA text and replace them with the natural rhythms of a native Arab writer.

This skill is not a translation tool. It does not change the meaning of the text. It changes the texture — the register, the breath, the feel — so that a native reader stops noticing the writing and starts absorbing the ideas.

---

## Philosophy

Arabic is not a language that rewards uniformity. The Arabic rhetorical tradition — بلاغة — treats writing as a performance: varied, rhythmic, image-bearing, emotionally engaged. Classical Arab writers mixed the elevated with the immediate, the long periodic sentence with the short thrust, the metaphor with the plain fact. They used rhymed prose (السجع) to create closure, rhetorical questions to create urgency, and culturally grounded imagery to anchor abstraction.

AI-generated MSA fails on every one of these dimensions. It is grammatically competent but rhetorically hollow. It hedges when it should assert. It lists when it should argue. It repeats formulaic transitions as if they were structural steel when they are actually the verbal equivalent of filler. Most critically, it uses a single register — formal, cautious, and uniform — regardless of topic, audience, or purpose.

The result is text that reads like a government report written by someone who has read many government reports but has never spoken to another human being.

The goal of this skill is not to add decoration. It is to restore the natural instincts of human Arabic writing: assertion, variation, rhythm, and grounding.

---

## Pattern Categories

There are five categories of AI tells in MSA Arabic. Each category has multiple patterns. You will work through all five systematically.

---

## CATEGORY 1 — HEDGING & FORMULAIC LANGUAGE

AI models hedge. They hedge because they are trained on diverse sources and cannot confidently assert anything without covering their liability. Human writers hedge too — but selectively, and only when uncertainty is the actual point. AI hedges at three to four times the human rate. In Arabic, this produces text that feels bureaucratic, evasive, and weak.

---

### Pattern 1 — Hedging Phrase Overload

**Detection:** Scan for: من المهم الإشارة إلى، يجب الإشارة إلى، من الضروري أن نذكر، يُعتقد أنّ، قد يكون، ربما، من المحتمل أنّ، تجدر الإشارة إلى، لا بد من التنويه. Flag any that appear more than once per 200 words. Flag any that open a sentence where a direct assertion would serve better.

**Why it matters:** A hedge is a confession of weakness. When used appropriately — to mark genuine uncertainty — it is an intellectual virtue. When used reflexively on every third sentence, it signals to the reader that the writer does not trust their own material. Native MSA writers in journalism, academia, and literary nonfiction assert. They state. They claim. They let the argument carry the risk.

**The fix:** Remove the hedge and make the statement directly. If the uncertainty is genuine and material to the argument, rewrite to express the nature and degree of uncertainty precisely rather than vaguely.

**Example:**
- ❌ AI: من المهم الإشارة إلى أن الاقتصاد الرقمي يُغير طبيعة العمل في المنطقة.
- ✓ Human: الاقتصاد الرقمي يُعيد رسم خريطة العمل في المنطقة، وهذا لم يعد موضع جدل.

---

### Pattern 2 — Clichéd Opening Phrases

**Detection:** Check the opening sentence of every paragraph. Flag any that begin with: في الآونة الأخيرة، في العصر الحديث، إن العالم اليوم، يشهد العالم حاليًا، في ظل التطورات المتسارعة، في خضم التحولات، مع تسارع وتيرة، في عالم يتغير بسرعة. These are the AI's equivalent of "In today's fast-paced world."

**Why it matters:** These phrases are pure throat-clearing. They say nothing about the actual subject. They are generic enough to open any article about anything. A human writer with something to say starts with the thing they have to say. An AI starts by warming up the reader with temporal context that no one asked for.

**The fix:** Delete the opening phrase entirely. Begin with the first substantive claim, observation, or image. If the sentence cannot stand without the preamble, the sentence needs to be rebuilt.

**Example:**
- ❌ AI: في ظل التطورات المتسارعة في مجال الذكاء الاصطناعي، تواجه المؤسسات تحديات جديدة.
- ✓ Human: الذكاء الاصطناعي لا يطرق الباب — إنه يُعيد تشكيل البيت من الداخل.

---

### Pattern 3 — Wrong Transition Phrase (Critical AI Signature)

**Detection:** Search for every instance of علاوة على ذلك. This is a critical and consistent AI signature in Arabic. It must be flagged in every instance without exception.

**Why it matters:** The word علاوة (ʿalāwa) in classical Arabic means the surplus cargo loaded on a camel beyond its standard load — the overage. By extension, in pre-modern usage it referred to an addition or supplement. However, in contemporary educated MSA, the correct phrase for "moreover" or "in addition" is إضافة إلى ذلك or بالإضافة إلى ذلك or فضلًا عن ذلك or علاوةً على ما سبق in specific rhetorical contexts. AI models systematically produce علاوة على ذلك at a rate far exceeding human writers, and native readers find it jarring — it sounds like a mistranslation. This single pattern, when appearing three or more times in a text, is sufficient to identify AI authorship to a trained Arabic reader.

**The fix:** Replace every instance of علاوة على ذلك with an appropriate alternative. Rotate between: إضافة إلى ذلك، فضلًا عن ذلك، وثمة أيضًا، بل إن. Do not use any single alternative more than once per text.

**Example:**
- ❌ AI: علاوة على ذلك، فإن التعليم يُعد ركيزة أساسية للتنمية.
- ✓ Human: فضلًا عن ذلك، التعليم ليس خدمة اجتماعية — إنه استثمار في البنية التحتية للأمة.

---

### Pattern 4 — Transition Phrase Overuse

**Detection:** Count occurrences of: وبالتالي، بالإضافة إلى، مع ذلك، ومن ثَمّ، على الرغم من ذلك، لذا، وفي هذا الإطار. Flag if any single phrase appears more than twice in a 300-word block. Flag if transition phrases collectively appear more than once every 80 words.

**Why it matters:** Transitions are connective tissue. Human writers use them when the connection between ideas is not self-evident. AI uses them constantly — between every idea, whether the connection is obvious or not — because the model is pattern-matching on essay structure. The result is text that feels over-explained and condescending, as if the writer does not trust the reader to follow the argument without constant signposting.

**The fix:** Remove transitions where the logical connection is clear from context. Where the transition is necessary, use it once, clearly. Vary the form: use a short sentence instead of a transition word, or reorder the sentences so the transition becomes unnecessary.

**Example:**
- ❌ AI: يعاني النظام من قصور هيكلي. وبالتالي، لا يمكنه الاستجابة للتحديات الراهنة. وبالإضافة إلى ذلك، يفتقر إلى الكفاءة. لذا، من الضروري إصلاحه.
- ✓ Human: النظام قاصر هيكليًا ولا يملك أدوات الاستجابة — وهذا يجعل الإصلاح حاجة لا رفاهية.

---

### Pattern 5 — Formulaic Conclusion Phrases

**Detection:** Check the final paragraph and final sentences of each section. Flag: في الخلاصة، باختصار، وختاماً، وبهذا نكون قد، في نهاية المطاف يتضح، مما سبق يتبين أن، وخلاصة القول. Also flag "summary sentences" that simply restate the preceding paragraph's main point with no new framing.

**Why it matters:** Human writers end with arrival — a final image, an open question, a call that resonates. AI ends with accounting — a summary of what was just said, a formulaic close that tells the reader they may stop reading now. In Arabic rhetoric, the conclusion (الخاتمة) is expected to have weight and closure. It should feel like the last note of a musical phrase, not a table of contents in reverse.

**The fix:** Remove formulaic openers. Rewrite the conclusion to end on something memorable: a compressed final claim, a rhetorical question, an image that carries the argument's weight.

**Example:**
- ❌ AI: وخلاصة القول، أثبتنا في هذا المقال أن التعليم مهم وأن الاستثمار فيه ضروري لتحقيق التنمية.
- ✓ Human: أمة لا تُعلّم أطفالها تدفع الثمن مرتين: مرة حين تُهدر طاقاتهم، ومرة حين تستورد من غيرها ما كان يمكنها أن تصنعه بنفسها.

---

### Pattern 6 — Passive Voice تم/يتم Overuse

**Detection:** Search for تم + verbal noun and يتم + verbal noun constructions throughout the text. Flag any paragraph containing more than one such construction. Flag the overall rate: more than three تم/يتم constructions per 300 words is the AI threshold.

**Why it matters:** The passive تم/يتم is grammatically valid MSA, but it drains agency from the writing. It is the construction of bureaucratic Arabic — of official statements, legal documents, and government communiqués. When used in analytical or argumentative writing, it creates distance between the writer and the claim. Human MSA writers — journalists, critics, essayists — strongly prefer active voice. The agent is named, the action is direct, and the sentence moves forward.

**The fix:** Convert to active voice. Name the agent if known. If the agent is genuinely unknown or unimportant, use the Arabic active-with-indefinite-subject construction (فاعل عام) rather than the تم passive.

**Example:**
- ❌ AI: تم إجراء الدراسة من قِبَل الباحثين، وتم جمع البيانات على مدى ثلاثة أشهر، وتمت معالجتها إحصائيًا.
- ✓ Human: أجرى الباحثون دراستهم على مدى ثلاثة أشهر، جمعوا خلالها البيانات وحللوها إحصائيًا.

---

## CATEGORY 2 — LEXICAL & VOCABULARY PATTERNS

Arabic has an extraordinarily rich lexical system. The root-pattern (جذر-وزن) morphology means that a single three-letter root generates dozens of derived words with related but distinct meanings. Human Arabic writers exploit this richness. AI Arabic writing collapses it — producing text with unnaturally narrow vocabulary range and mechanical word repetition.

---

### Pattern 7 — Vocabulary Homogeneity

**Detection:** Track word choice for key concepts throughout the text. Flag when the same concept is expressed using the same word in every instance — especially across paragraph boundaries. Also flag the opposite problem: mechanical synonym rotation where أثبتت الدراسات appears in paragraph 1 and أظهرت الأبحاث appears in paragraph 2 with no functional difference — pure surface-level variation with no semantic distinction.

**Why it matters:** Human writers vary vocabulary based on nuance and context, not for variation's sake. دراسة and بحث are not fully interchangeable — one implies a formal academic study, the other implies ongoing investigation. A human writer chooses based on what they mean. AI chooses based on surface variation algorithms, producing word choice that feels arbitrary.

**The fix:** Audit the vocabulary for key concepts. Where words are being mechanically rotated, consolidate and choose the single most accurate word. Where true synonyms are available with genuine semantic distinctions, use the distinction purposefully.

**Example:**
- ❌ AI: أثبتت الدراسات أهمية النوم. وقد أظهرت الأبحاث أن قلة النوم تؤثر على الأداء. وكشفت الدراسات العلمية أن ساعات النوم الكافية...
- ✓ Human: تُؤكد الأدلة المتراكمة — من التجارب المخبرية إلى الدراسات الميدانية — أن النوم ليس استراحة بيولوجية بل عملية ترميم معرفي.

---

### Pattern 8 — Formal MSA Over-Formalization

**Detection:** Check whether the register of the writing matches the context. A personal essay, a newsletter, a professional LinkedIn post, a blog article — these call for educated but accessible MSA, not the register of the Official Gazette. Flag: يتجلى ذلك في، تجدر الإشارة إلى، وعليه يمكن القول، ومما لا شك فيه، في إطار هذا التحليل. These phrases are appropriate in legal or formal academic Arabic and are AI tells when used in accessible writing contexts.

**Why it matters:** Arabic has a wide register range. Educated native writers calibrate their register to context with precision. They know that writing for a broad Arabic-speaking audience is different from writing a policy paper. AI defaults to maximum formality regardless of context — it is the safe choice. But maximum formality in the wrong context reads as pompous, detached, and alienating.

**The fix:** Identify the intended audience and context. Strip register-inappropriate formality markers. Replace with formulations a competent educated Arab writer would use for that specific context and audience.

**Example:**
- ❌ AI: يتجلى ذلك جليًا في إطار تحليلنا للمؤشرات الاقتصادية، ومما لا شك فيه أن هذه البيانات تعكس واقعًا محددًا.
- ✓ Human: الأرقام تقول ما يكرهه المسؤولون: الانكماش حقيقي، وتجاهله لن يجعله يختفي.

---

### Pattern 9 — Conjunction Overuse (و/أو/لكن)

**Detection:** Scan for chains of conjunctions connecting more than three items or clauses. Flag structures like: والتعليم والصحة والبنية التحتية والبيئة والاقتصاد. Count conjunctions-per-sentence average: above 3.5 per sentence across a paragraph signals AI writing.

**Why it matters:** Arabic uses the conjunction و generously — more than English uses "and" — but not infinitely. AI produces conjunction-heavy text because it is stitching together parallel items without deciding which deserve emphasis and which can be subordinated or omitted. Human Arabic writers group, prioritize, and compress. They do not list everything — they select.

**The fix:** Group related items without repeating the conjunction. Convert conjunction chains to a list only when the items are genuinely enumerable and benefit from visual separation. Otherwise, compress and prioritize.

**Example:**
- ❌ AI: يعاني المجتمع من مشكلات في التعليم والصحة والبنية التحتية والبطالة والفقر والتفاوت الاجتماعي والهجرة الداخلية.
- ✓ Human: البنية الاجتماعية تتشقق من جهات عدة: تعليم متراجع، صحة مُثقلة، وبطالة تدفع نحو الهجرة — وكلها أعراض لجرح واحد.

---

### Pattern 10 — Prefix/Suffix Redundancy

**Detection:** Scan for over-use of the definite article ال in positions where it is grammatically optional or stylistically heavy. Flag constructions where multiple nouns in sequence all carry ال unnecessarily. Also flag overuse of the preposition ب in circumstantial phrases where a more direct construction is available.

**Why it matters:** The definite article in Arabic carries semantic weight — it marks specificity, known referents, and generic categorical statements. When used reflexively on every noun, it loses its function and makes the text heavy and slow. Human Arabic writers use definiteness strategically. They know when to make something specific and when to leave it in the indefinite for rhetorical effect.

**The fix:** Review every instance of ال for whether definiteness is semantically required. Remove where optional. Restructure sentences to avoid noun-chain definiteness pileups.

**Example:**
- ❌ AI: يتطلب الأمر من المؤسسات الحكومية القيامَ بالإصلاحات الضرورية في الأنظمة التعليمية الحالية.
- ✓ Human: على المؤسسات الحكومية أن تُصلح أنظمتها التعليمية — والوقت لا يصبر.

---

### Pattern 11 — Domain Vocabulary Rigidity

**Detection:** Identify the text's primary domain (health, technology, economy, politics, environment). Check whether the key domain term is the same word in every instance. Flag: مرض used exclusively when اضطراب، حالة، عَرَض would be more accurate in certain sub-contexts. Flag: تقنية used exclusively when تكنولوجيا، ذكاء رقمي، نظام would vary appropriately.

**Why it matters:** Domain vocabulary in Arabic is richer than AI output suggests. A doctor writing about psychiatry distinguishes between مرض (disease as category), اضطراب (disorder as functional disruption), حالة (case as individual presentation), and أعراض (symptoms as observable signs). AI collapses this into a single term used throughout, which signals to any domain expert that the writer either lacks expertise or is summarizing from a non-expert source.

**The fix:** For each flagged domain term, identify the precise sub-meaning intended in each sentence and apply the most accurate term. Do not rotate for variety's sake — rotate for precision's sake.

**Example:**
- ❌ AI: يعاني المريض من مرض نفسي. هذا المرض يؤثر على سلوكه. يمكن علاج هذا المرض بالعلاج النفسي.
- ✓ Human: يرزح المريض تحت وطأة اضطراب يُشوّه علاقته بالواقع — وما نراه من سلوكيات ليس سوى الأعراض الخارجية لحالة أعمق بكثير.

---

## CATEGORY 3 — STRUCTURAL & SYNTACTIC PATTERNS

The structure of a piece of writing is as much a part of its voice as the words. Human Arabic writers use structure dynamically — varying sentence length, paragraph depth, and the distribution of ideas across the text. AI writing has a statistical signature in its structural choices that is recognizable even before you read a single word.

---

### Pattern 12 — Syntactic Template Overuse

**Detection:** Read the opening phrase of each sentence in a paragraph. Flag if more than 60% of sentences follow the same syntactic template. Common AI templates in MSA: إن/أن + noun + verb, يُعد + noun + adjective, من الواضح أن، لا شك أن + clause, تُشير الأبحاث/الدراسات إلى أن. Also flag uniform verb-subject-object order throughout — human Arabic writers vary word order for information structure and emphasis.

**Why it matters:** Arabic is a morphologically rich language with considerable word-order flexibility (VSO, SVO, topicalization, fronting). Native writers exploit this freedom to place new information, emphasis, and contrast where they want it in the sentence. AI writing defaults to a small set of templates and applies them uniformly, creating a hypnotic rhythm that reads as mechanical once noticed.

**The fix:** Vary sentence openings. Use fronting and topicalization. Start some sentences with the predicate, others with a circumstantial phrase, others with a quoted assertion. Break the template dominance.

**Example:**
- ❌ AI: يُعد التعليم أمرًا بالغ الأهمية. ويُعتبر الاستثمار فيه ضرورة ملحة. ويُشكّل الركيزة الأساسية للتنمية.
- ✓ Human: التعليم ليس أداةً — إنه الأساس. ومن يُقلّص ميزانيته اليوم يُهيّئ أزمة اقتصادية لغدٍ لا يستطيع تحمّلها.

---

### Pattern 13 — Sentence Length Uniformity

**Detection:** Measure the approximate word count of each sentence. Flag if the standard deviation is below 6 words across a paragraph — this indicates unnaturally uniform sentence length. Human MSA text shows variance above 40% of the mean sentence length. AI text clusters sentences in the 15–22 word range.

**Why it matters:** Rhythm in Arabic prose is built on contrast. A long, intricate sentence followed by a short, stark one creates impact. The long sentence builds; the short one lands. AI writing has no short sentences because short sentences feel incomplete to a language model trained to be thorough. The result is text that sounds like a metronome rather than a voice.

**The fix:** After every 2–3 long sentences, introduce a short one. Short sentences should be between 5 and 9 words. They should contain the piece's sharpest claim or its most vivid image.

**Example:**
- ❌ AI: يواجه الشباب العربي في الوقت الراهن جملة من التحديات الاجتماعية والاقتصادية التي تؤثر بشكل مباشر على مستقبلهم وفرصهم في الحياة وتطلعاتهم المهنية، مما يستدعي دراسة متأنية واستراتيجيات متكاملة لمعالجة هذه الإشكاليات المتشعبة.
- ✓ Human: الشباب العربي في مواجهة سوق عمل تتقلص وأحلام تتآكل — وليس أمامهم وقت لانتظار الحلول الشاملة. يريدون نتائج. الآن.

---

### Pattern 14 — Paragraph Length Uniformity

**Detection:** Count sentences per paragraph throughout the text. Flag if all paragraphs contain 3–5 sentences with no deviation. Human MSA writing varies paragraph length significantly: some paragraphs are a single sentence; others run 6–8 sentences when developing a complex argument.

**Why it matters:** A single-sentence paragraph is one of the most powerful rhetorical tools available to a writer. It signals: this matters. It makes the reader stop. AI never writes single-sentence paragraphs because its training optimizes for completeness and development. The absence of paragraph-length variation is a structural tell that is immediately apparent to a skilled editor.

**The fix:** Identify the piece's two or three most important claims. Pull each one into its own single-sentence paragraph. Let it stand alone. Also consider allowing one paragraph to run longer than the others — a sustained analysis can demonstrate intellectual engagement that uniform paragraph length never can.

**Example:**
- ❌ AI: [Three paragraphs of identical 4-sentence structure throughout]
- ✓ Human: [Develops complex point across 7 sentences → single-sentence paragraph with the core claim → resumes development]

Stand-alone sentence example:
- ✓ Human: الثقة لا تُبنى بالبيانات الرسمية.

---

### Pattern 15 — Bullet Point & List Overuse

**Detection:** Count the total number of bulleted or numbered lists in the text. Flag if lists constitute more than 15% of the text's content (by line count). Flag any list where the items could be integrated into prose without loss of clarity. Flag lists of more than 5 items that appear inside argumentative or analytical text (as opposed to reference material where lists are appropriate).

**Why it matters:** Lists are a tool of technical documentation, not of Arabic rhetorical prose. The Arabic essay tradition — the مقالة — is built on the paragraph, not the list. When AI converts argumentation into bullet points, it destroys the argumentative tissue: the connectives, the qualifications, the subordinations, the build-up and release that make an argument persuasive rather than merely informative. A list of claims is not an argument.

**The fix:** Convert lists to integrated prose. The integrating connectives become part of the argument's logic. The implicit relationships between items become explicit claims. The text gains argumentative structure.

**Example:**
- ❌ AI:
  تشمل أسباب الأزمة ما يلي:
  • ضعف الحوكمة
  • غياب الشفافية
  • التضخم المتصاعد
  • انخفاض الاستثمار الأجنبي

- ✓ Human: الأزمة لم تنشأ من عامل واحد: الحوكمة الهشة أتاحت الفرصة، وغياب الشفافية حجب المحاسبة، فتراكم التضخم في غياب رادع، وانسحب الاستثمار الأجنبي حين فقد ثقته بالمشهد.

---

### Pattern 16 — Markdown Overuse

**Detection:** Scan for: **bold text**, *italic text*, H1/H2/H3 headers, horizontal rules (---), and inline code blocks in running Arabic prose. Flag any use of markdown formatting in text that is intended for human reading rather than structured documentation.

**Why it matters:** Markdown is a tool for structuring text for rendering pipelines, not for Arabic prose composition. When AI writes Arabic text with heavy bold, headers, and bullet formatting, it signals that the text was generated for a structured output environment and has not been processed through a human editing pass. Native Arabic writers do not bold their key points — they emphasize them with word choice, sentence structure, and rhetorical placement. The text itself carries the emphasis.

**The fix:** Remove all markdown formatting from argumentative and analytical text. Replace structural headers with transitional sentences if section breaks are needed. Replace bold emphasis with word-order fronting, exclamatory particles (ألا إنّ، حقًا، بل), or short standalone sentences.

**Example:**
- ❌ AI: **أهمية التعليم:** يُعدّ التعليم من أهم العوامل المؤثرة في **التنمية الاقتصادية** و**الاجتماعية**.
- ✓ Human: لا يحتاج التعليم إلى تعريف بالخط العريض — حاجتنا إليه هي التي تحتاج إلى فهم.

---

### Pattern 17 — Pronoun-Antecedent Repetition

**Detection:** Track noun repetition across consecutive sentences. Flag when the same noun (subject or object) is repeated in three or more consecutive sentences where an Arabic pronoun (هو، هي، هم، هن، ذلك، تلك) would serve grammatically and stylistically.

**Why it matters:** Arabic has rich pronoun morphology — gender, number, case, and person are all marked. When humans write consecutive sentences about the same referent, they naturally use pronouns once the referent is established. AI tends to repeat the full noun phrase in each sentence, which reads as didactic and creates an unnecessarily heavy nominal style. More importantly, AI misses the Arabic rhetorical option of zero-pronoun constructions and subject-drop that create natural flowing prose.

**The fix:** After the referent is established, use appropriate pronouns and zero-subject constructions. Where multiple sentences about the same subject run together, consider combining them into one complex sentence with appropriate conjunctions or relative clauses.

**Example:**
- ❌ AI: أجرى الباحث دراسة ميدانية. الباحث جمع البيانات من عشر مدن. الباحث حلّل البيانات خلال ستة أشهر. الباحث نشر النتائج في مجلة دولية.
- ✓ Human: أجرى الباحث دراسةً ميدانية شاملة، جمع خلالها بيانات من عشر مدن، وقضى ستة أشهر في تحليلها قبل أن ينشر نتائجه في مجلة دولية.

---

## CATEGORY 4 — RHETORICAL & STYLISTIC DEFICIENCIES

This is where AI Arabic fails most completely. Grammar can be correct. Vocabulary can be appropriate. Structure can be adequate. And still the text will feel dead because it has no rhetoric. Arabic has one of the world's richest rhetorical traditions. AI output ignores it almost entirely.

---

### Pattern 18 — Absence of Saj' (السجع)

**Detection:** Read aloud the final phrase of each sentence (or each rhetorical unit). Check whether consecutive sentence endings share phonetic patterns — similar vowels, similar consonant clusters, similar morphological patterns. In human Arabic writing of any formality, you will find some degree of phonetic harmony, especially at paragraph endings and at the text's conclusion. Its complete absence is a tell.

**Why it matters:** السجع (rhymed prose) is not a decoration in Arabic — it is a structural tool that creates aural memory and emotional closure. From the Quran to Al-Jahiz to contemporary Arab columnists, phonetic closure has been used to signal importance, to create rhythm, and to make ideas memorable. AI writing produces prose that is phonetically random because it optimizes for semantic coherence, not aural effect. The result is text that reads but does not sing.

**The fix:** Where the text's tone permits, revise the endings of key sentences to create light phonetic harmony. This does not mean full rhyme — it means selecting words whose final syllables or morphological forms create a sense of pattern. Particularly apply this to: the opening sentences of the text, the end of each major section, and the final sentences of the entire piece.

**Example:**
- ❌ AI: التعليم يُعد أمرًا ضروريًا لبناء المجتمعات وتحقيق التنمية المستدامة في المنطقة.
- ✓ Human: التعليم بناءٌ وتنميةٌ وانتماء — ثلاثية لا تكتمل بأحدها دون الآخرَين.
  (Note the light saj' pattern: بناء / تنمية / انتماء — all ending in the ـاء pattern)

---

### Pattern 19 — No Metaphor or Figurative Language

**Detection:** Scan the entire text for any figurative language: metaphors, similes (كـ، مثل + extended comparison), personification, metonomy, or extended images. Flag if none are present in texts longer than 300 words. Also flag "dead metaphors" that have lost their figurative force through overuse: مفتاح النجاح، أسس التنمية، ركائز المجتمع.

**Why it matters:** Figurative language is how humans make abstractions concrete. Arabic has an exceptionally strong figurative tradition — the language itself is built on semantic extension from physical root meanings. When AI writes about economics without a single image, about society without a single metaphor, about education without any figuration, it is producing technically accurate but experientially empty text. The reader understands but does not feel.

**The fix:** Introduce at least one original metaphor or extended image per 400 words. The metaphor should come from a domain that has physical, concrete associations — the body, water, architecture, agriculture, light, weather. Avoid recirculating clichéd Arabic metaphors. Aim for images that are surprising but not arbitrary.

**Example:**
- ❌ AI: يُعتبر التعليم من أهم الركائز التي تُبنى عليها الدول المتقدمة وتُحقق من خلاله التنمية الشاملة.
- ✓ Human: الدولة التي تُهمل تعليمها تُشيّد قصرًا فوق رمال — شامخٌ في الصورة، يتصدع بأول عاصفة.

---

### Pattern 20 — Generic Cultural References

**Detection:** Check whether the text references any specific cultural, historical, geographic, or literary touchstones that situate it within Arab culture and history. Flag text that could have been written about any society in any language with simple translation — text with no specific references to Arab history, literature, the region's shared experiences, or the audience's specific context.

**Why it matters:** Human writers write from somewhere. An Egyptian columnist writing about education will reference the Azhar, the khedivial tradition, or the post-73 generation. A Levantine writer will reference the nahda (النهضة) or the specific demographic pressures of their society. Gulf writers will reference oil-economy transitions and their speed. AI writes from nowhere — it produces culturally deracinated text that applies equally to Casablanca, Riyadh, and Amman because it was trained to be universal. This universality is its cultural failure.

**The fix:** Ask about the target audience and region. Add culturally grounded references that are accurate and respectful. A reference to the nahda, to Ibn Khaldun's cyclical theory of civilization (for analytical texts), to a specific historical moment, or to a shared regional experience immediately grounds the text and signals a human writer who knows their audience.

**Example:**
- ❌ AI: واجهت المجتمعات العربية تحديات كثيرة في مجال التنمية خلال العقود الماضية.
- ✓ Human: منذ أن أشعلت النهضةُ فتيلَ التساؤل في القرن التاسع عشر، والسؤال نفسه يُلاحقنا: لماذا تتقدم غيرنا ونتعثر نحن؟ الجواب ليس في الجغرافيا ولا في الجينات — إنه في الخيارات.

---

### Pattern 21 — No Rhetorical Questions

**Detection:** Scan the entire text for any interrogative sentences (ending with ؟). Flag if none are present in texts longer than 400 words. Also flag texts where all questions are hedged or buried inside clauses (نتساءل هنا عن، يطرح هذا تساؤلًا حول) rather than stated as direct rhetorical questions.

**Why it matters:** The rhetorical question (الاستفهام البلاغي) is one of the most fundamental tools of Arabic rhetoric. It creates urgency, involves the reader, and signals that the writer has stakes in the argument — they are not merely reporting but engaging. AI avoids rhetorical questions because they are harder to generate without appearing incoherent — a question without an obvious answer pattern is outside the model's comfort zone. The result is text that feels monological and detached.

**The fix:** Add 1–2 rhetorical questions per major section. Position them at moments of transition or before the text's core claim. The question should be genuinely rhetorical — the reader should feel the answer rather than require it spelled out.

**Example:**
- ❌ AI: إن التعليم يؤثر بشكل مباشر على مستوى التنمية الاقتصادية والاجتماعية في أي مجتمع من المجتمعات.
- ✓ Human: متى تعلّمنا أخيرًا أن الأمم لا تُبنى بالثروات، بل بما تفعله بها؟

---

### Pattern 22 — Semantic Clustering

**Detection:** Identify the main concepts of the text. Check whether all evidence, elaboration, and supporting points for each concept appear in the same paragraph. Flag rigid semantic clustering where the text reads like: paragraph 1 = concept A (fully developed), paragraph 2 = concept B (fully developed), with no cross-referencing, no building of tension between concepts, and no ideas distributed strategically across the text.

**Why it matters:** Human writers think associatively. They introduce an idea, move away from it to establish context, return to it with new evidence, then allow it to interact with a different concept introduced later. This creates the texture of real thought — the reader follows the writer's mind through the argument rather than processing a series of hermetically sealed concept-paragraphs. AI writing semantically clusters because it is easier to generate — complete one topic before moving to the next. The result feels like a series of encyclopedia entries rather than an essay.

**The fix:** Identify the text's two or three most important concepts. Consider whether any of them can be distributed — introduced briefly early, developed in the middle, and concluded at the end. Add explicit cross-references between paragraphs that show ideas in dialogue with each other rather than in separate silos.

**Example:**
- ❌ AI: [Paragraph 1: Education — 5 sentences. Paragraph 2: Economy — 5 sentences. Paragraph 3: Social development — 5 sentences. No connection.]
- ✓ Human: [Education introduced with one provocative image. Economy developed in relation to education. Social development shown to require both — returning to and deepening the opening image.]

---

## CATEGORY 5 — DIACRITICS & MORPHOLOGICAL PATTERNS

Modern Standard Arabic has a diacritics system (التشكيل / الحركات) that marks vowel sounds and grammatical case. The vast majority of modern MSA text — journalism, web content, books — is written without diacritics (المكتوب بدون تشكيل). Formal religious, classical, and some legal texts use full diacritization. AI makes characteristic errors in both modes.

---

### Pattern 23 — Diacritic Inconsistency

**Detection:** Check whether diacritics are present or absent throughout the text. Flag: (a) texts where some words are diacritized and others are not without any pattern, (b) texts where common high-frequency words are inconsistently diacritized, (c) texts where diacritics appear only on words the model found ambiguous but not on others of equal ambiguity.

**Why it matters:** Native MSA writers make a conscious choice: either diacritize fully (for religious, pedagogical, or classical texts) or leave all diacritics out (for modern prose). Inconsistent diacritization is the mark of either a careless student or an AI. Inconsistency tells the reader that diacritics were added reactively (when the model was uncertain) rather than applied according to a principled stylistic decision.

**The fix:** Make a decision appropriate to the text's genre and audience. If it is modern analytical or journalistic prose: remove all diacritics. If it is formal academic or religious prose: diacritize consistently throughout. Apply the chosen standard uniformly.

**Example:**
- ❌ AI: يُعدّ التعليم من أهم العوامل المؤثِرة في بناء المجتمع وتحقيق التنمية.
  (يُعدّ diacritized, but أهم، بناء، التنمية are not — inconsistent)
- ✓ Human (undiacritized): يُعدّ التعليم من أهم العوامل المؤثرة في بناء المجتمع وتحقيق التنمية.
  OR
- ✓ Human (fully diacritized): يُعَدُّ التَّعْلِيمُ مِنْ أَهَمِّ الْعَوَامِلِ الْمُؤَثِّرَةِ فِي بِنَاءِ الْمُجْتَمَعِ.

---

### Pattern 24 — Incorrect Diacritic Placement

**Detection:** If the text contains diacritics, verify grammatical case marking on key positions: the subject (مرفوع — ضمة), the object (منصوب — فتحة), the genitive (مجرور — كسرة), and verbal aspect marking. Flag incorrect case marking, particularly in iḍāfa constructions (المضاف والمضاف إليه) and after prepositions.

**Why it matters:** Incorrect diacritics in Arabic are not merely typos — they change the grammatical parsing of the sentence and can change the meaning. A text claiming to be diacritized MSA with case errors signals either an uncorrected AI output or a non-native writer. Either way, it damages credibility with any educated Arabic reader.

**The fix:** Correct all diacritic placement errors. Pay particular attention to: final case endings on nouns after prepositions, dual and sound plural case suffixes, broken plural patterns, and case marking within quoted phrases.

**Example:**
- ❌ AI: نظرَ الباحثُ في نتائجَ الدراسةِ (incorrect: نتائج is in iḍāfa, should be نتائجِ as مضاف إليه)
- ✓ Human: نظرَ الباحثُ في نتائجِ الدراسةِ

---

### Pattern 25 — Overgeneralization of Formal MSA

**Detection:** Identify whether the text contains any dialogue, quotation, or representation of speech. Flag any dialogue written in formal MSA rather than the appropriate spoken register. Also flag contexts (social media captions, personal narratives, informal professional communication) where full formal MSA is stylistically inappropriate.

**Why it matters:** No Arab speaks in formal MSA. Dialogue written in formal MSA is immediately recognizable as artificial — it is the equivalent of writing English dialogue in Elizabethan English. When AI generates dialogue, it defaults to MSA because that is what its Arabic training data predominantly contains. The result is dialogue that sounds like a government announcement rather than a conversation between human beings.

**The fix:** Dialogue should reflect the appropriate dialect of the characters or speakers. If the text is a personal narrative in Modern Standard Arabic but includes dialogue, the dialogue should at minimum use a reduced register — shorter sentences, more direct vocabulary, fewer subordinate clauses.

**Example:**
- ❌ AI: قال المدير: "ينبغي علينا أن نُعيد النظر في استراتيجياتنا المتعلقة بإدارة الموارد البشرية."
- ✓ Human: قال المدير: "لازم نراجع طريقة إدارتنا للفريق — الوضع مش تمام."

---

### Pattern 26 — Passive Voice Disguise

**Detection:** Beyond the تم/يتم construction (Category 1, Pattern 6), search for the formal passive morphology: يُستخدم، يُعتبر، يُلاحَظ، يُشار إلى، يُرى، يُقال. These are the formal passive patterns that AI uses to avoid naming agents. Count their frequency: more than two per 200 words is the AI threshold for this pattern.

**Why it matters:** The formal passive in Arabic (derived from the مبني للمجهول pattern) is grammatically elegant and has legitimate uses — particularly when the agent is unknown, unimportant, or deliberately withheld. AI uses it not for these reasons but because generating a passive is computationally easier than identifying a plausible agent and constructing an active sentence. The result is text with no actors — a world where things happen, patterns emerge, and phenomena are observed, but no one does anything.

**The fix:** For each passive construction, ask: who is the agent? If the agent can be named, name them and rewrite in the active. If the agent is genuinely unknown or general, consider the active-with-indefinite-subject construction.

**Example:**
- ❌ AI: يُعتبر التعليم ركيزة أساسية، ويُلاحَظ أن الاستثمار فيه يُرى على المدى الطويل.
- ✓ Human: يعتبر خبراء التنمية التعليمَ الركيزة الأولى — ويستطيع أي محلل اقتصادي أن يرى آثاره تتراكم على مدى عقود.

---

### Pattern 27 — Zipfian Distribution Deviation

**Detection:** This is a statistical pattern that can be approximated by reading. Note the vocabulary frequency distribution: AI writing uses mid-frequency words uniformly — words that are neither the most common nor the rarest, but consistently in the middle band. Human Arabic writing follows Zipf's law: a few very high-frequency words appear very often, and a long tail of low-frequency, specific, precise, or literary words appear rarely. Flag text that seems to use only "safe" vocabulary — never unusual, never highly literary, never highly technical, never regional.

**Why it matters:** Vocabulary that comes only from the middle of the frequency distribution produces text that is competent but characterless. Human writers — even those writing in MSA — occasionally reach into the literary register for a precise classical word, occasionally use a technical term that is exactly right, and occasionally drop into a lower register for vividness. This range is what gives writing personality. AI stays in the middle because the middle is safe.

**The fix:** Identify 2–3 moments in the text where a word from the edges of the frequency distribution would be more precise or more vivid than the mid-frequency word currently used. This might mean using a classical Arabic word that has fallen out of daily use but carries exactly the right nuance, or a highly specific technical term, or a word whose phonetic texture adds to the line's sound.

**Example:**
- ❌ AI: الأزمة الاقتصادية أثّرت بشكل سلبي على الأوضاع المعيشية للسكان وزادت من صعوبة الحياة اليومية.
- ✓ Human: الأزمة أنهكت — بالمعنى الحرفي، لا المجازي — قدرةَ الناس على الصمود، فلم يعد الفقر مفهومًا اقتصاديًا بل حالًا يُعاش لحظةً بلحظة.
  (أنهكت is lower-frequency and more precise than أثّرت; الصمود adds cultural resonance)

---

### Pattern 28 — Low Syntactic & Semantic Diversity

**Detection:** Read three consecutive sentences. If they could be paraphrases of each other — if they make essentially the same point with slightly different vocabulary — flag them. This is semantic repetition disguised as development. Also read the sentence structures: if consecutive sentences all share the same syntactic skeleton (noun phrase + verb + object), flag for syntactic diversity.

**Why it matters:** AI language models have high cosine similarity between consecutive sentences — they stay close to the semantic space they are already in, generating text that orbits the same idea without moving forward. Human writers move. They introduce a claim, then support it with evidence (different semantic space), then qualify it (different again), then illustrate it (different again). The text advances. AI text spins.

**The fix:** For any flagged cluster of similar sentences, identify which one contains the core claim. Keep that one. Convert the others to either (a) genuine evidence or illustration that comes from a different domain, (b) a qualification that adds nuance rather than repeating the point, or (c) delete them as redundant.

**Example:**
- ❌ AI: التعليم مهم جدًا. التعليم يُحسّن حياة الناس. التعليم يُعدّ أداةً فاعلة في تحسين الأوضاع الاجتماعية. التعليم يُسهم في رفع مستوى المعيشة.
- ✓ Human: التعليم يُحوّل. ليس تحويلًا أيديولوجيًا — بل تحويلًا في الاحتمالات: ما يستطيع الإنسان أن يفعله، وما يستطيع أن يتخيله، وما يرفض أن يقبله.

---

## Processing Workflow

Work through the text in three stages. Do not skip stages. Do not combine stages into a single pass.

---

### Stage 1 — Identify

Read the full text from beginning to end without making any changes. During this read:

1. Assign the text a preliminary score on the Quality Rubric (see below). This is your baseline.
2. Mark every instance of each of the 28 patterns. Note the pattern number and severity (minor / significant / critical).
3. Identify the text's: (a) intended audience, (b) genre and register, (c) core argument or purpose, (d) any voice or stylistic choices that appear intentional and should be preserved.
4. Note what the text does well. Not everything needs to change. Some passages may be genuinely strong and should be protected.

Critical patterns that must always be addressed (never skip):
- Pattern 3 (علاوة على ذلك): Replace every instance.
- Pattern 6 (تم/يتم overuse): Reduce to at most one per 300 words.
- Pattern 13 (Sentence length uniformity): Break the uniformity without exception.

---

### Stage 2 — Rewrite

Work through the text paragraph by paragraph. Apply fixes according to the identified patterns.

Principles for Stage 2:
- **Preserve meaning.** The humanized text must convey exactly the same information and argument as the original. If in doubt, lean toward the original meaning.
- **Preserve what works.** A passage that is already strong — clear, direct, well-structured — should not be changed simply because the model wants to change something.
- **Prioritize impact.** If time is limited, fix in this order: (1) critical pattern violations, (2) sentence length uniformity, (3) hedging overload, (4) passive voice, (5) rhetorical elements.
- **Match register.** Do not impose a literary register on a technical report or a journalistic directness on a formal academic text. Humanize within the text's own register.
- **Arabic first.** Do not write Arabic through the filter of English syntax. The rewritten text should parse as Arabic prose, not as a translated text.

---

### Stage 3 — Audit & Polish

After rewriting, read the result from the beginning. Ask:

1. "If I did not know this text was originally AI-generated, would I suspect it now?" If yes, identify why and fix it.
2. Check for Pattern 18 (Saj'): Did the rewrite create any opportunity for phonetic closure that was missed? Add it.
3. Check for rhetorical questions (Pattern 21): Is there at least one? If not, add one at the most appropriate moment.
4. Check for figurative language (Pattern 19): Is there at least one original image or metaphor? If not, add one.
5. Verify sentence length variation (Pattern 13): Read the longest sentence and shortest sentence. Is the shortest sentence genuinely short (5–9 words)? Does it carry impact?
6. Re-score the text on the Quality Rubric. Compare to your Stage 1 baseline. If the score has not improved by at least 10 points, identify why and make additional corrections.
7. Read the text aloud (mentally). The Arabic should flow naturally. Any sentence that sounds awkward when mentally spoken aloud needs to be revised.

---

## Voice Calibration

When a writing sample is provided, calibrate the rewrite to match the writer's established voice before applying humanization patterns.

### Step 1 — Sample Analysis

Analyze the provided sample for:
- **Register:** How formal is the vocabulary? Does the writer use classical Arabic words or prefer modern vocabulary?
- **Sentence architecture:** Does the writer prefer long complex sentences or short declarative ones? What is their average sentence length?
- **Rhetorical style:** Does the writer use metaphors frequently? Rhetorical questions? Direct address (الخطاب المباشر)?
- **Signature phrases:** Are there transitional phrases, opening formulas, or syntactic patterns the writer uses consistently?
- **Cultural grounding:** What cultural or historical references does the writer draw on?
- **Rhythm:** What is the sound of the writer's prose when read aloud?

### Step 2 — Calibration

Apply the humanization patterns while matching the identified voice characteristics. If the writer's sample is naturally formal, the humanized text should be formal — but without AI hedging and formulaic language. If the writer uses rhetorical questions frequently, add more than the standard minimum. If the writer has a preference for saj', enhance phonetic closure throughout.

### Step 3 — Consistency Check

After rewriting, compare a paragraph of the rewritten text with a paragraph of the original sample. They should feel like they came from the same writer. If they do not, identify the specific points of divergence and adjust.

---

## Quality Rubric

Score the text on five dimensions, each scored 1–10. Total score out of 50.

---

### Dimension 1 — Directness (1–10)

Does the text say what it means without hedging, qualification, or evasion?

- **10:** Every sentence makes a direct claim. Hedges appear only where uncertainty is the actual point and are expressed with precision.
- **7–9:** Mostly direct. One or two unnecessary hedges remain but do not define the text's character.
- **4–6:** Noticeable hedging. Several sentences begin with من المهم، يجب الإشارة، يُعتقد أنّ or equivalent. Passive voice used where active is available.
- **1–3:** Pervasive hedging. Text feels evasive and bureaucratic. Almost no direct assertions.

---

### Dimension 2 — Rhythm (1–10)

Does the text have varied sentence lengths? Does it flow naturally when read aloud?

- **10:** Wide sentence length variation (short punchy sentences mixed with long complex ones). At least one sentence under 8 words carries a key claim. Reading aloud is natural and satisfying.
- **7–9:** Good variation in most paragraphs. Minor uniformity patches remain.
- **4–6:** Some variation but overall the text stays within a narrow sentence-length band (12–20 words). Reading aloud reveals a mechanical rhythm.
- **1–3:** Consistent sentence uniformity throughout. All sentences approximately the same length. No short sentences. Reading aloud is monotonous.

---

### Dimension 3 — Authenticity (1–10)

Does the text sound like a human Arab writer?

- **10:** A skilled Arabic editor would not flag this text as AI-generated. The vocabulary range is natural, the transitions are human, the structural choices feel motivated by content rather than template.
- **7–9:** Mostly convincing. One or two phrases might make a careful reader pause.
- **4–6:** A skilled reader would have suspicions. Several AI patterns remain visible.
- **1–3:** Clearly AI-generated to any educated Arabic reader. Multiple signature patterns present.

---

### Dimension 4 — Density (1–10)

Is every word necessary? Is there filler, redundancy, or semantic repetition?

- **10:** No sentence could be shortened without losing meaning. No two consecutive sentences say the same thing. No filler phrases.
- **7–9:** Minor redundancies remain but they do not define the text. Mostly lean.
- **4–6:** Noticeable filler: sentences that restate the previous sentence, paragraphs that conclude by summarizing what they just said, transitional phrases that explain connections the reader could infer.
- **1–3:** Heavy filler throughout. Significant portions of the text could be cut without losing information. Semantic repetition is frequent.

---

### Dimension 5 — Rhetoric (1–10)

Does the text make use of Arabic rhetorical devices?

- **10:** Contains at least one effective original metaphor or extended image, at least one rhetorical question, some phonetic closure or saj' in key positions, and culturally grounded references appropriate to the audience.
- **7–9:** Two or three rhetorical devices present and effective.
- **4–6:** One or two attempts at rhetoric, but they may be clichéd (dead metaphors) or feel grafted on rather than organic.
- **1–3:** No rhetorical devices. Text is semantically adequate but experientially flat.

---

### Scoring Interpretation

| Score | Grade | Meaning |
|-------|-------|---------|
| 45–50 | Excellent | Ready for publication. Passes as human-written to expert readers. |
| 35–44 | Good | Strong output. Minor polish may improve further. |
| 25–34 | Needs Revision | Significant AI patterns remain. Another pass required. |
| Below 25 | Rewrite Required | Fundamental restructuring needed. The text is not yet human-quality. |

---

## Quick Reference — Pattern Checklist

Use this checklist during Stage 1 and Stage 3 review.

**Category 1 — Hedging & Formulaic Language**
- [ ] 1. Hedging phrase overload (من المهم، يُعتقد أنّ، من الضروري)
- [ ] 2. Clichéd opening phrases (في الآونة الأخيرة، في العصر الحديث)
- [ ] 3. Wrong transition: علاوة على ذلك (CRITICAL — replace every instance)
- [ ] 4. Transition phrase overuse (وبالتالي، بالإضافة إلى)
- [ ] 5. Formulaic conclusion phrases (في الخلاصة، وختاماً)
- [ ] 6. تم/يتم passive overuse (CRITICAL — reduce significantly)

**Category 2 — Lexical & Vocabulary**
- [ ] 7. Vocabulary homogeneity (mechanical synonym rotation)
- [ ] 8. Over-formalization (wrong register for context)
- [ ] 9. Conjunction overuse (long و chains)
- [ ] 10. Prefix/suffix redundancy (unnecessary ال)
- [ ] 11. Domain vocabulary rigidity (single term for varied concepts)

**Category 3 — Structural & Syntactic**
- [ ] 12. Syntactic template overuse (>60% same opening structure)
- [ ] 13. Sentence length uniformity (CRITICAL — introduce variation)
- [ ] 14. Paragraph length uniformity (add single-sentence paragraphs)
- [ ] 15. Bullet point and list overuse (convert to prose)
- [ ] 16. Markdown overuse (remove formatting)
- [ ] 17. Pronoun-antecedent repetition (use pronouns after established referent)

**Category 4 — Rhetorical & Stylistic Deficiencies**
- [ ] 18. Absence of saj' (add phonetic closure at key positions)
- [ ] 19. No metaphor or figurative language (add at least one per 400 words)
- [ ] 20. Generic cultural references (add culturally grounded touchstones)
- [ ] 21. No rhetorical questions (add at least one per major section)
- [ ] 22. Semantic clustering (distribute ideas, cross-reference between sections)

**Category 5 — Diacritics & Morphological**
- [ ] 23. Diacritic inconsistency (choose a standard and apply uniformly)
- [ ] 24. Incorrect diacritic placement (verify case marking in diacritized text)
- [ ] 25. Overgeneralization of formal MSA (match register to context, especially dialogue)
- [ ] 26. Passive voice disguise (يُستخدم، يُعتبر، يُلاحَظ overuse)
- [ ] 27. Zipfian distribution deviation (introduce low-frequency precise vocabulary)
- [ ] 28. Low syntactic and semantic diversity (vary ideas AND structures)

---

## Notes on Arabic Specificity

A few points that distinguish Arabic humanization from English humanization:

**Root morphology as a tool.** Arabic's triconsonantal root system means that verbs, nouns, and adjectives derived from the same root carry related but distinct semantic fields. Human writers exploit this by choosing the derived form (وزن) that carries exactly the right nuance. AI often uses the most common form regardless of nuance. When reviewing vocabulary, consider not just synonyms but morphological variants of the same root.

**Gendered and numbered agreement.** Arabic agreement (gender and number) gives writers options that English does not have. The choice between the plural broken patterns, the collective form, and the sound plural can create rhythmic variety. AI tends to use the most predictable plurals; human writers occasionally use the rarer broken plural for its phonetic texture.

**The internal rhythms of MSA.** Unlike Modern English prose, which often works against its own phonetic properties, Arabic prose is built with phonetics in mind. The length patterns of Arabic words (short syllable / long syllable), the patterns of classical poetic meters, and the phonetic texture of root families all influence how Arabic prose feels when read. A humanized text should not ignore this dimension.

**Regional variation within MSA.** MSA is a supranational standard, but educated Arab writers from different regions bring different influences. Gulf writers bring influences from the Arabian Peninsula's oral tradition. Levantine writers bring influences from the nahda literary tradition and the Beirut press. Egyptian writers bring influences from the Cairene literary establishment and Al-Azhar. North African writers bring Maghrebi Arabic and French literary influences. When calibrating voice, consider the writer's regional background.

**The honor of the Arabic language (شرف اللغة العربية).** Many educated Arab readers have a strong emotional relationship with their language's classical tradition. Humanization should never feel like a degradation of the language. The goal is not to make Arabic writing "simpler" or "more casual" — it is to make it more alive, more argued, more human. The target is the great Arabic essayists and journalists of the 20th century: Taha Hussein, Abbas Mahmoud Al-Aqqad, Naguib Mahfouz in his critical writing, or contemporary columnists like Ghassan Charbel. These writers wrote in formal MSA and were deeply human.
