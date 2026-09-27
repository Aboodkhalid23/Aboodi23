---
name: remotion-broll
description: 素材工程执行 skill：自采/下载/截图/选段/嵌入/调色。触发词：素材、B-roll、录屏、yt-dlp、截图、调色。装配判定真素材段时调用。
---

# 素材工程（可执行管线）

> 定位：这是**干活的 skill**，不是规则文档——判定、命令、验收一条龙执行。完整规则真源在 `remotion-assembly/references/broll.md`（四级优先级细则/每案例素材清单义务/引用规格），冲突以彼为准。

## 何时调用

- 分段工坊第 2 步判出「真素材段」（产品体验类画面：打字/生成/界面/演示/操作）
- 装配方案表定稿前的素材清单收集（每案例 1 张产品截图或 5s 录屏，AI 自采不等供料）
- 用户给了录屏/实拍素材要嵌入正片

## 执行管线（每步都有验收，逐步走）

**① 定级**：按四级优先级选路——用户自录屏 > 官方视频 > 网页截图 > UI 模拟卡。有公开官网/官方频道的案例禁止直接掉到第 4 级。

**② 采集**
- 官方视频：`yt-dlp --print "%(channel)s | %(title)s | %(duration)ss | %(id)s" "ytsearch8:<产品名> official"` 认准官方频道 → `yt-dlp -f "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/b[vcodec^=avc1]/b" -o "public/broll/<名>.mp4" <url>`（`[vcodec^=avc1]` 过滤默认 AV1，与 HEVC 同罪不入库，见 broll.md 2c）；403 依次试 UA / `--cookies-from-browser` / 代理。
- 网页截图：`node_modules/.remotion/chrome-headless-shell/*/chrome-headless-shell*/chrome-headless-shell --headless --screenshot=<out.png> --window-size=1920,1080 --virtual-time-budget=10000 <url>`。

**③ 验真（不可跳过）**：`file <文件>` 防「PNG 实是 HTML」；视频 `ffprobe` 验编码，HEVC 先转 H.264（防黑屏）；截图肉眼 Read 确认非登录墙/Cookie 弹窗。

**④ 选段**：`ffmpeg -vf fps=0.5` 抽帧拼 contact sheet，**Read 逐帧读图**，选与口播语义同步的 3-8s 镜头段（输入→动作→等待→结果），记录起止秒。

**⑤ 嵌入**：Takeover 内 `<Sequence from={beat(x)}>` + `<OffthreadVideo muted src={staticFile('broll/….mp4')} startFrom={F(起点秒)}>`（muted 必加）；接管不带 PiP（用户裁定）；截图装 ShotCard/WindowCard。含媒体 Sequence 加 `premountFor≈fps` 防首帧黑，**但该 Sequence 禁设 `layout="none"`（去包裹层后 premount 失效）；外层若 `return null` 门控容器可见性，null 须早开 ≥premountFor 帧（seg06 实测：容器 `frame<enterAt-30 return null` 配内层 `premountFor={30}`），否则父级 null 砍掉预载窗、premount 白做**。

**⑥ 调色统一**：素材层加 `filter: brightness(0.9-0.92) saturate(0.95)`（按正片明暗微调），原色直出=贴片感（错题 #18）；**接管段统一档 `brightness(.92) saturate(.95)`（seg06 实测定档，勿逐段目测微调）**。

**⑦ 剪辑加工**：强调处 punch-in（crop+scale 到关键区，关键句字高 ≥40px）、挑帧、变速；引用类走「先全卡 2-3s → punch-in 关键句」二段式。**接管窗贴合素材自然时长、优先自然速率**——素材短于窗先收窗+提前叠化，不为填窗慢放；`playbackRate<1` 仅界面滚动类且窗不可收时末选（≥0.7）。**烧入高亮/译条素材无干净帧** → 遮罩揭示法（白遮罩 `scaleX 1→0` 揭开，且入库须在 SOURCES.md 登记「配遮罩揭示法」，见 broll.md 8.5）。

**⑧ 段渲验收**：只渲该段 `--frames=a-b`，抽帧读图查：贴片感（调色）、可读性（≥16px）、骑线（白板安全框）、与口播对拍。

## 落盘约定

视频 `public/broll/`；截图 `public/assets/`；缺口写进装配方案表交用户供料。版权口径：官方宣传素材用于评论性视频。

## 人名必配人像（用户裁定 2026-07-22，铁律级）

**口播提到具体人名时，人物卡的头像圈里尽可能放该人物的真实照片**，不用首字母 monogram 顶替（用户原话：「这种提到人名的，尽可能都放一个图片，你可以自己去网上找这个人物最有代表性的图片，放到这个头像的圈里」）。monogram/图标只作为拿不到图时的兜底。

**取图口径（分两类，别混）**：
- **公众人物**（乔布斯、马斯克等）：AI 自行取图，但**只从明确标注可商用授权的来源**取——首选 Wikimedia Commons 的 CC BY / CC BY-SA / Public Domain 条目，其次官方新闻稿素材。**禁随手抓搜索引擎图**（多为权利不明的商业摄影，用户片子是要发布的）。取图后必须在 `public/broll/<片名>/SOURCES.md` 登记：文件名 / 来源 URL / 授权类型 / 摄影者署名。CC BY-SA 需在片尾或简介署名的，交付时一并告知用户。
- **非公众人物**（如口播提到的老师、朋友、同事）：**AI 不得自行网上找图**——既无法确认是本人，也无授权。走「点名要素材」流程请用户提供；用户不提供则维持手绘名牌/monogram，并在交付时说明原因。

**这条覆盖旧口径**：早期方案里「乔布斯禁肖像、只用文字/icon chip」的写法是版权顾虑下的保守做法，现按用户裁定改为「用授权清楚的真实照片」，版权问题靠**选授权来源**解决而不是靠不放图。

## AI 生成拼贴 B-roll（无真实素材的情绪/隐喻场景，0722-01 定型）

真素材四级里没有、又需要情绪或抽象隐喻画面（复读、手术、刷手机、注意力碎裂这类无法录屏也无官方视频的段落）时，走本流程：Codex `image_gen` 生静帧 → Grok `image_to_video` 活化 → 接进正片。执行走 `gbro-collage-broll` skill 的三闸（Gate1 隐喻 / Gate2 静帧 / Gate3 视频），**但节奏、承载、构图口径以本节为准（覆盖 gbro 默认值）**。

**① 承载：默认右区卡片，不是整屏**。B-roll 放三区版式的右区证据卡里（16:9 等比 `objectFit:contain` 整幅显示、**不裁切**——用户裁定「等比例缩小」），人物常驻在场，左区保留侧标+时间线 HUD。整屏接管只在「无任何信息需与素材并置」时用（A-roll 铁律：整屏是唯一可切人物处，见 layout §2）。承载件参考 `src/koubo/scenes-0722-01/CollageBroll.tsx`（卡片 + OffthreadVideo，描边跟章色）。**别默认做整屏**——0722-01 误做整屏被用户否决重来。

**② 节奏：一句口播一张图，切点给节奏，不靠镜头内揭示**。密集口播里每张只活 1-3s，**禁 assemble-from-empty 组装动画**（从空场拼起、末帧才完整＝信息永远慢半拍，与语速曲线打架，8 条视频因此作废）。要「活化」——静帧构图第 0 帧就完整，Grok 只叠**持续微动**（纸片飘/齿轮转/光带滑/雾气涌），构图一帧不许变。

**③ 静帧构图规律（Codex image_gen）**：
- **比例分型**（一刀切会翻车）：**物件驱动隐喻**（病床/药片/日历/碎片/书堆——人只是元素）人物占高 45-60%；**人物驱动隐喻**（在工作/端坐/按按钮/发呆——人是主体）必须近景 65-80%，远景直接失效。
- 硬红线：无假字/可读字母数字/logo/水印/UI；**四边缘同样查**（Codex 自查会漏检边缘假字，主会话必须 ffmpeg 裁四边放大独立复验）。
- 身份参考图用户指定（0722-01 用 `my-face-studio-default.JPG`）；表情按叙事，低谷段多用侧影/低头/仰躺规避违和，不笑不愁苦。
- 每批生成后 `md5` 去重，防串档。

**④ Grok 活化三坑（错题 #39 详）**：
- **分辨率**：grok CLI `image_to_video` 的 `resolution_name` **只有 480p/720p 两档、无 1080p**（2026-07-24 实测确认，请求 1080p 会回退 720p）；xAI API 侧 grok-imagine-video-1.5 支持 1080p i2v（官方文档）。**整屏需 1080p ＝ CLI 做不到**：走 xAI API 1.5 档、换真素材或其他生成器（Sora 2 / Veo / Kling / Seedance；ChatCut MCP 内置 Seedance/Kling）。指令必须**显式写死分辨率**才拿满档位——不写默认落 **736×400**（更糊）。**720p 够不够看承载模式**：卡片/画中画（显示区常 <720px）720p 有余、清晰；**整屏铺满 1920×1080** 时 720p 放大 1.5× 会软。成片是 1080p，B-roll 无需 4K（显示不出、除非大幅推近）。
- **morph 增生**：易崩元素（齿轮/圆环/日历格）prompt 末尾加锁定约束（保持单个原尺寸/格数颜色不变/圆环连续不断线）。
- **硬性补全**：「稀疏元素+大片空背景+空心人形+露脸碎片」触发模型填满空地/填实空洞/长出人脸，**改构图**而非加禁令。
- **调用**：headless 需 `--always-approve --permission-mode bypassPermissions --max-turns 10`；多 agent 共享 cwd 禁用 `grok --continue`（会串会话把 A 条成片写到 B 条路径）；交付前全批 md5 去重。

**⑤ 环境前置**：Codex 项目必须建在其可写工作区内（本机＝`~/Documents/remotion剪辑/` 下），建在 `~/hyperframes-projects/` 会 image_gen 成功却存盘被拒；多条目任务一条一个 agent 并行发，别让一个 agent 串行做全部（会做到一半判完成收工）。
