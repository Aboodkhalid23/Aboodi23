# 声音设计（audio）

本文件是「声音设计」板块唯一真源。来源：深度对比报告「声音设计」7 条 + assembly SKILL §5 音效管线（已搬入，按 v4 现状更新）+ 修改单-04 勘误裁决 5 / B14。

> 目录：适用时机 · 1 SFX 高频穿透（8kHz+ ≥+6dB）· 2 出片母带链 · 3 人声压缩 · 4 零停顿空洞 · 5 连击模式 · 6 素材电平 -3dBFS · 7 默认无 BGM · 8 音效管线操作规范（定稿库 v2 / 采样管线 / A-G 挂载）· 9 ffmpeg 验收命令集 · 边界

## 适用时机

装配流程三个节点必读：

1. **写 cue 表时**（挂 SFX 之前）：规则 4-6 决定哪里配、配几发、用什么素材。
2. **渲染出片后母带处理时**：规则 2-3 是固定后期链路，不可跳过。
3. **交付前验收时**：规则 8 的 ffmpeg 命令集逐项跑，任一不达标即打回。

总原则：本风格声音三支柱 = **人声压缩贴顶、SFX 高频穿透、零停顿空洞**。差距全在后期链路，可纯代码/流程修复。

## 规则（按重要度排序）

### 1. [sev5] SFX 必须高频穿透：命中点 8kHz+ 峰值 ≥ 人声齿音基线 +6dB

- 观众能不能听见 SFX，取决于 8kHz 以上频段能否穿出人声，不取决于全频段响度。基准片的 SFX 是混音里最亮的元素：命中点 8kHz+ 峰比其语音齿音基线高 10dB；v3 的 88 个 cue 只有 10 个在 12kHz+ 穿出 -25dB，听感等于没有音效。
- 验收硬标准：**loudnorm 后产物**抽 ≥3 个命中点，8kHz+ 峰值比人声齿音基线高 ≥6dB（修改单-04 B14 裁决口径）；出片后用 `highpass=f=12000` + `silencedetect=noise=-25dB` 计数，可听事件数应接近 cue 数。
- **阈值待重标定（2026-07-20 BASE_VOL 降档后）**：降档前实测重锤 +12.9dB 被终审裁「太响」、+4.2dB 可听——「≥+6dB」与新音量档已冲突。降档后验收先以「逐 cue 可听可辨 + 用户终审耳朵」为准（可听事件计数照跑），量化阈值待下一片 loudnorm 后实测回填，勿为凑 +6dB 调回音量。
- 素材选型：必须含高频瞬态（亮质感、能量延伸到 12kHz+），whoosh/pop 类偏暗素材不合格。
- 历史现状（勘误重基线，勿重复执行）：SfxTrack.tsx 的 BASE_VOL 曾上调到（whoosh 0.8 / pop 0.85 / stamp 1.0 / rise 0.8 / trans 0.55 / ding 0.9），**再乘系数会削波**。⚠️ 此上调值已于 **2026-07-20 终审整体降档为 0.3-0.55（重锤上限 0.55）**——上列旧值即被裁定「声音太大」的那一版，勿再当基线沿用，现基准见规则 8 音量条与 remotion-sfx SKILL §4.4。

### 2. [sev4] 出片必过母带链：压缩 + 定量增益 + 限幅（v4 实测定稿）

- **实测可用命令（v4 出片验证，直接复用）**，分两步：
  1. 测量：`ffmpeg -i in.mp4 -af "acompressor=threshold=-18dB:ratio=3:attack=10:release=120,loudnorm=I=-16:print_format=json" -f null -` → 记下 `input_i`。
  2. 出片：`ffmpeg -i in.mp4 -af "acompressor=threshold=-18dB:ratio=3:attack=10:release=120,volume=<(-16 - input_i)>dB,alimiter=limit=0.75:attack=4:release=60:level=false" -c:v copy -c:a aac -b:a 256k out-master.mp4`（v4 实测 gain=7.2dB → 产物 -16.1 LUFS / -1.1 dBTP）。
- **坑（v4 实测）**：① loudnorm 两遍式线性模式在 TP 余量不足时会静默回退 dynamic，真峰不可控（目标 -1.5 实出 -0.5），所以第二遍不用 loudnorm，用 volume+alimiter 手动等效；② acompressor 的 `makeup=6` 会把真峰推到 +12dB，母带链里的压缩器**不带 makeup**（增益统一交给 volume 步骤）。
- v3 教训：无母带链导致综合响度 -22 LUFS（比基准片低 2.8LU）、真峰 +0.1dBTP 裸触 0dBFS；基准片 -19.2 LUFS / TP 稳贴 -1.0dB。
- 验收：ebur128 测母带产物，TP 在 -2~-1dB、integrated 在 -17~-15.5 LUFS。

### 3. [sev4] 口播人声进装配前先过压缩

- 人声素材导入 Remotion 前预处理：`acompressor=threshold=-18dB:ratio=3:attack=10:release=120:makeup=6`。先压缩再 loudnorm 限幅，效果最接近基准片的「贴脸感」。
- v3 教训：无压缩导致同一人声轨峰值忽高忽低（0.6s 语音窗峰值 -13.7dB vs 基准片 -3.1dB，相差 13.7dB 动态散乱），响处削波、轻处发虚。
- 验收：任意 0.6s 语音窗峰值波动范围 ≤ 6dB。

### 4. [sev3] 零停顿空洞：-30dB 停顿超限打回，-40dB 死空气零容忍

- 基准片全片 356s 无一处 >0.4s 低于 -30dB 的停顿，停顿期声底稳定约 -34dB mean（房间底噪+压缩抬升），听感永远「有东西」；v3 有 40 处共 21s 停顿空洞，节奏发死。
- 验收硬标准：`silencedetect=noise=-30dB:d=0.4` 超过 10 处或总时长超过 8s 即打回；`-40dB` 以下完全静音一处都不允许（多为人声轨剪辑断口，单独查补）。
- 长期方案：粗剪交付时就紧剪呼吸停顿；短期兜底：装配层垫一条约 -38dB 的 room-tone/氛围 bed 盖住空洞。

### 5. [sev3] 连击模式：3+ 同类元素依次入场，SFX 逐个跟发

- **2026-07-20 终审收窄（sfx §4.4 审计闸覆盖本条旧默认）**：0.15-0.3s 逐个跟发只用于 **≤4 件**的语义 stagger（此时禁止只在第一个元素上发一发）；**>4 件批量点亮默认整组首记一发**（0715-02 事故：逐格跟发致 pop 占比 52%、听感「快门连拍」被终审打回；密度 ≥2.5s/发与单音色 ≤35% 两道线优先）。基准片的高频事件呈爆发簇（6-7 连击、间隔约 0.2s），形成机关枪式节奏；v3 全表最小间隔 1.5s+，只有单发。
- 实现注意：现 `SfxCue` 类型为 `{at, sfx, vol?}`（src/koubo/sfx-0715-01.ts），连击写多条 cue，或扩展 `{at, sfx, count, gap}` 语法糖（尚未实现，扩展时改 SfxTrack.tsx）。

### 6. [sev2] SFX 素材电平标准：入库峰值统一 -3dBFS，系数只表达类型层级

- 所有 SFX 素材入库前统一 normalize 到峰值 -3dBFS，用 `volumedetect` 验证；BASE_VOL 系数只负责类型间的相对关系（重锤 > 入场 > 轻点 > 转场），不用来补素材电平差，否则混音落点不可控。
- 现状（2026-07-21 认可池转正后）：**在役十音色** glass/pop(←fav20)/tick2(←fav33)/pop2(←fav14)/stamp/rise/whoosh/shutter/bright(←fav02)/lowthud(←fav13) 峰值 -3dB 达标（旧 pop/pop2 存 spare/prev-*）；**rise.wav 已于 2026-07-21 重制**（认可池 fav29 tick 连滚 1.2s，-3dB 达标，坏件存 spare/rise-broken-91db.wav；同日 0721-01 终审复听收账：连续 tick 累积响度大，BASE_VOL 单独压 0.1、全片 ≤4-5 处防扎堆，硬线见 sfx §4.4）；trans/ding 已弃用移 spare/；认可池 jy-fav/ 19 件均 -3dB 达标（详见规则 8）。
- 合成注意（重合成时）：whoosh 带通滤波后电平会掉到 -38dB，必须补增益 + alimiter，合成后一律 volumedetect 验峰值。

### 7. [sev2] 本风格默认无 BGM，氛围靠 SFX 密度

- **事实勘误（2026-07-21 用户指正 + 双片实测）：基准片有 BGM**——连续低频床，头/中/尾恒定 -26~-30dB，估相对人声 ≤-15dB（docs/基准片配声谱v2.md §4）；旧「实测无 BGM」为单片停顿段误读（所谓 200Hz 哼声线疑即 BGM 低频床）。**「本风格默认无 BGM」维持**——它是用户裁定的风格差异，非基准片语法；用户要加时起点参考：相对人声 -15dB 以下、全片恒定不做戏剧起伏（修改单-04 裁决 5 + 本勘误）。
- 不要为了像而加：加 BGM 反而糊掉信息密度。声音预算全部投给 SFX 穿透力和响度链。

### 8. 音效管线操作规范（2026-07-16 三次迭代定稿：专业音效库制）

- **音源三路裁决史**：① ffmpeg 合成 → 用户否（沙沙声廉价感）；② 参考片音轨采样 → 用户否（高通去人声后单薄发虚）；③ **专业音效库 = 正解**——基准片这类 hits 本来就出自商用包，行业没人自己合成。
- **音源优先级**：a. 剪映本地缓存盘库（用户指定首选，盘库方法见 remotion-sfx SKILL §1）→ b. `@remotion/sfx` 官方包（npm 装完 d.ts 里就是直链 URL，`curl remotion.media/<名>.wav`；whip/whoosh/switch/mouse-click/page-turn/ding 可用，其余多为梗音效）→ c. Mixkit 免费商用（category 页 grep `assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3` 直链可下）→ d. Pixabay/kenney.nl CC0 → e. 用户购买商用包（Artlist/Epidemic，质感天花板）。
- **选型铁律：音效质感 AI 判断不了，必须用户试听挑选**——做「试听板」交付：每候选归一 -3dB + 截 1.6s + 编号名称上屏，ffmpeg concat 成一条视频（本片 previews/sfx-试听板.mp4，24 候选 48s），用户报编号后再上片。两次全盘被否的教训：AI 只能筛掉频谱级硬伤（噪底/人声残留），「好不好听」零判断力。
- **定稿库 v2（2026-07-16 终版，用户三轮试听选定；剪映系为主保证音色成套）**：glass=剪映 J08（带音高提示 blip，证据卡显影）、pop=剪映 J01（干净单 tick）、pop2=剪映 J09（软落位）、stamp=剪映 J13（低频闷击）、rise=剪映 J41 微粒子 40ms 连滚 1.5s 铺满滚动期、~~trans=Mixkit impact-788(首轮 21 号) 裁 1.6s~~（2026-07-20 弃用）、whoosh=@remotion/sfx whoosh(首轮 01 号，清场软扫)、~~ding=@remotion/sfx ding(22 号)~~（2026-07-20 弃用）、shutter=shutter-modern(12 号，留「拍照定格」语义)。spare/：剪映 J03/J04/J12/J15、prev-* 上一版五件、whip/impact-1143/pop-2925/interface-1109。剪映选定编号全记录：J01/03/04/08/09/12/13/15/41。**挂载必须按 A-G 配声语法查表**（remotion-sfx skill §4 / 音效设计谱.md）：音色成套、音量克制、一事一声、数字落定不配重击。换片沿用此库，新角色先过试听板。
- **2026-07-20 试听复审（0715-02 终审轮，九音色试听板用户裁定）**：**trans、ding 弃用**（移 spare/；E 章节转场位暂按「就近归族」用 whoosh 轻档顶位 vol≤0.5、收尾拍留白，正式补源走本规则采样管线+用户试听）；**rise.wav 实测坏文件**（max_volume -91dB 实质无声，按 remotion-sfx §3 连滚配方用剪映 J41 重制后须复过试听）；shutter 文件正常（-3.5dB/0.49s），试听板该条无声属拼接生成问题——但用户对「咔嚓」类听感敏感（sfx §4.4 stamp 慎用同源），非「拍照定格」语义不挂。
- **2026-07-21 认可池扩库（用户剪映收藏，42 段试听板裁定 19 件可用）**：入库 `public/sfx/jy-fav/`（fav 编号+缓存哈希+档位分组登记在目录内 SOURCES.md，全部 normalize -3dBFS/48k 单声道）；rise.wav 用 fav29 tick 按 remotion-sfx §3 配方重制。**音量裁定：「音效基本音量都要 -15dB 左右」→ BASE_VOL 基准 ≈0.25**（真源 sfx §4.4）。库原则用户校准：基准片常用音色也就十几个、音效不能喧宾夺主——认可池可备多，同片在役音色克制。**2026-07-21 转正落库**：pop←fav20（B 换源）、pop2←fav14（G 换源）、新角色 tick2←fav33 / bright←fav02（高亮划线位）/ lowthud←fav13（物理撞入位），旧件存 spare/prev-*，**在役十音色**；听感终校仍在段终审。
- **采样管线（seg02 实战验证，全命令可复现）**：
  1. 提取参考片音轨 `ffmpeg -vn -ac 1 -ar 48000`；
  2. 扫音效命中点：`highpass=f=12000,silencedetect=noise=-25dB:d=0.08`（12kHz 阈值排除人声齿音）；
  3. 每个命中点测人声频段安静度：`bandpass=f=800:w=2600,volumedetect` 取 max_volume，**按安静度排序挑人声间隙里的干净 hit**（片尾 CTA 段、转场空拍是金矿：0715 参考片 356.03s 人声 -47dB）；
  4. 切片 0.1-0.5s + `highpass=f=900` 去残留人声基频 + 首尾 afade，**showspectrumpic 出频谱图逐张读图验货**（人声=底部横向谐波纹；噪底放大=全幅横向涂抹，增益补偿 >20dB 的源基本是噪底，弃）；
  5. 归一 -3dBFS 入库（规则 6）。
  6. 特殊件合成法：数字滚动 rise = 采样 tick 裁 45ms `-stream_loop 29` 连滚 1.35s + 音量 ramp 0.3→1——基准片的「滚动声」本质是 tick 连击不是音调 riser。
- **定稿库九角色语义**（放 `public/sfx/`，编号见本规则定稿库 v2；挂载按 A-G 配声语法查表）：glass=证据卡/截图显影(A)、pop=chip 轻点(B)、pop2=名牌·徽章落位软 pop(G)、stamp=盖章重锤(D)、rise=数字滚动 tick 连滚(C)、~~trans=章节转场·接管进入(E)~~（2026-07-20 弃用，E 位暂 whoosh 轻档顶位 vol≤0.5）、whoosh=清场·退场软扫(F，比入场轻一档)、~~ding=收尾~~（弃用，收尾拍留白）、shutter=拍照定格。版权口径：短音效采样自评论对象影片或商用库，与素材引用同尺度。
- **挂载**：`src/koubo/sfx-<片名>.ts` cue 表（`{at 全局秒, sfx, vol?}`）+ `src/koubo/SfxTrack.tsx` 按 cue 挂 `<Audio>`，主合成顶层挂一次。
- **音量**：人声在素材音轨，SFX 不许压人声；**BASE_VOL 基准 2026-07-21 定为 ≈0.25（有效峰值 ≈-15dBFS，用户裁定「基本音量 -15dB 左右」）、重锤上限 0.55**（演进：0.8-1.0「太大」→ 0.3-0.55 → 0.25，真源见 remotion-sfx SKILL §4.4「全片音效审计闸」），逐条可用 `vol` 覆盖。
- **密度**：主元素配音效 + 列表连击（规则 5，2026-07-20 已收窄见该条）；章节转场每章一响；参照基准片双片实测全片 4-5s/发（2-3s 仅密集段节拍，docs/基准片配声谱v2.md），硬下限 ≥2.5s/发、目标带 3.5-5s（sfx §4.4 审计闸），验收看规则 1 的事件计数。

### 9. ffmpeg 定量验收命令集（交付前逐项跑，测 loudnorm 后产物）

```bash
# ① 母带链（规则 2）：两步——acompressor 测量 input_i → volume 定量增益 + alimiter 限幅（禁两遍式 loudnorm，linear 模式会静默回退 dynamic、真峰失控）
ffmpeg -i in.mp4 -af "acompressor=threshold=-18dB:ratio=3:attack=10:release=120,loudnorm=I=-16:print_format=json" -f null -   # 记下 input_i
ffmpeg -i in.mp4 -af "acompressor=threshold=-18dB:ratio=3:attack=10:release=120,volume=<(-16 - input_i)>dB,alimiter=limit=0.75:attack=4:release=60:level=false" -c:v copy -c:a aac -b:a 256k out.mp4

# ② 响度验收（双边窗口，与规则 2 对齐）：TP 在 -2~-1dB、integrated 在 -17~-15.5 LUFS
ffmpeg -i out.mp4 -af ebur128 -f null -

# ③ SFX 可听事件计数：事件数应接近 cue 数
ffmpeg -i out.mp4 -af "highpass=f=12000,silencedetect=noise=-25dB:d=0.05" -f null -

# ④ SFX 穿透定点抽测（≥3 个 cue 点 vs 邻近纯人声段；≥6dB 阈值待重标定见规则 1，暂以可听可辨为准）
ffmpeg -ss <cue秒> -t 0.5 -i out.mp4 -af "highpass=f=8000,volumedetect" -f null -
ffmpeg -ss <纯人声秒> -t 0.5 -i out.mp4 -af "highpass=f=8000,volumedetect" -f null -

# ⑤ 停顿空洞：-30dB 超 10 处或总 8s 打回；-40dB 一处都不许
ffmpeg -i out.mp4 -af silencedetect=noise=-30dB:d=0.4 -f null -
ffmpeg -i out.mp4 -af silencedetect=noise=-40dB:d=0.3 -f null -

# ⑥ 人声压缩验收：任意 0.6s 语音窗峰值波动 ≤ 6dB（多点抽测取 max_volume 对比）
ffmpeg -ss <t> -t 0.6 -i out.mp4 -af volumedetect -f null -

# ⑦ SFX 素材入库电平：max_volume 应为 -3dB
ffmpeg -i public/sfx/<name>.wav -af volumedetect -f null -
```

## 边界

- SFX cue 与元素入场同帧对齐（cue 表 at 值直接取元素 enterAt 换算秒）→ remotion-sfx SKILL §4.5。
- 渲染画质参数与交付流程 → assembly SKILL §6。
