---
name: remotion-design-system
description: 口播 MG 设计系统硬约束：token 语义、组件规格、铁律。做任何包装元素/视觉决策前必读。触发词：设计系统、组件、token、字体、配色。
---

# Remotion 口播包装设计系统（v1 hub）

风格目标：复刻基准片的口播 HUD 包装（参考图库在项目 `refs/`）。本文件是硬约束 hub：铁律 + tokens 语义 + 组件速查 + 错题集；板块细则在 `references/`（2026-07-16 深度对比 77 条差距的沉淀落点）。**没有写在体系里的视觉决策，先补充进对应板块文件再写代码。**

## 板块路由表（做什么读哪个文件）

| 板块 | 文件 | 管什么 |
|---|---|---|
| **规格表（先查再写）** | references/specs.md | 基准片实测数值真源：卡宽/字号/位置/动效帧数装配前必查，表里没有才现测并回填，**禁止目测** |
| 版式构图 | references/layout.md | 三区、takeover 机制（A 级不带 PiP、压暗升格已否决）、一屏一重心、编组模板、咬合位 |
| 字体排印 | references/typography.md | 唯一最大字、h1 义务、hero 三明治、SideLabel title 变体 |
| 色彩质感 | references/texture.md | 果冻块/glow、SURFACE 亮暗变体、印章规格唯一线、同屏色系 ≤2、**亮面禁裸字细则** |
| 动效 | references/motion.md | useEnter/useExit、分拍、build-up、服役区间、Breathe、净屏 |
| 信息设计 | references/infographic.md | 图表选件、比喻图形化、waffle、大数字三层、微图形词汇 |
| 叙事/节奏/字幕/素材/声音 | remotion-assembly 的 references/ | narrative / rhythm / subtitle / broll / audio |
| **错题集（症状→修法索引）** | 独立 skill `remotion-gotchas-index` | 全文「错题 #NN」的修法位置查这里；渲染异常/画面不对先查 |

## 工程底座清单（substrate —— 冷启动 / 新片起步前先确认在位）

**本设计系统是全仓共享的底座，不是每片重建。**下列文件是整套流程（assembly「输入验收→出帧→三道闸」+ motion §12 门控）的运行前提；一个新片默认**复用**它们，只新增自己的 composition + 字幕 + Scene，不重造底座。冷启动读者（禁读 src/）常在此扑空——先按此表确认文件在位、要取具体数值就打开对应文件读，别指望 skill 抄给你。

| 底座文件 | 装的什么 | 冷启动怎么用 |
|---|---|---|
| `src/design/tokens.ts` | **数值唯一真源**：COLOR（四语义 + 基础色 hex）、SURFACE、FONT、GRADIENT、`SIZE` 阶梯（kicker…mega）、GRID、RADIUS、SAFE、MOTION 帧数 | 要 `SIZE.mega`、语义色 hex 等**具体像素/颜色，直接读这个文件取**——skill 故意不抄（防快照与代码漂移，见 §1）；文件不在＝底座缺失，先建底座 |
| `src/design/*.tsx` | 组件库（§3 全表：SideLabel/HeroText/Chip…）+ `FontGuard.tsx`（字体门卫，错题 #01）+ `qc.tsx`（**QC 探针 `QcProbe`**：逐帧读 `[data-qc]` 盒判重叠，错题 #29） | 写包装元素前查 §3 组件表定位文件 |
| `src/design/motion.ts` | `useEnter/useExit/usePop` 底层 hook + MOTION 常量 | motion.md 规则引用的 hook 都在此 |
| `src/design/fonts.ts` | `@fontsource` 本地字体注册（错题 #01：webfont 走网络会静默出宋体） | package.json `sideEffects` 必含它 |
| `src/koubo/scenes/shared.tsx` | **装配层门控四件套** `Enter/DimAfter/Exit/ClearOut`（motion §12）+ `Place` 定位盒 + `qcAllow` QC 咬合白名单（assembly §2.5 闸①） | 装配写 Scene 直接套这些包装器，勿手搓 opacity |
| `src/Root.tsx` | composition 注册处（现有 `<Composition id="Koubo-0715-01" fps={30} …/>`） | **新片在此加一条 `<Composition>`**，id 自定；段渲脚本要对上这个 id（见 assembly §6 render-service 改 id） |
| `src/koubo/` | **每片专属**：`subtitles-<片名>.ts` / `SubtitleTrack.tsx` / `<片名主组件>.tsx` / `scenes/SceneNN.tsx` | 新片只在这层新增文件（结构见 assembly §4） |

**真·从零 bootstrap（src/ 完全为空）**：底座在位前 assembly 流程无法起步（取不到任何 token、出不了第一帧、落不了三道闸）。顺序＝先建底座再谈装配：① `tokens.ts` 定数值真源 → ② `fonts.ts` + `FontGuard.tsx`（错题 #01）→ ③ `motion.ts` 三 hook → ④ §3 组件库 → ⑤ `src/koubo/scenes/shared.tsx` 门控四件套 + `Place`/`qcAllow` → ⑥ `src/design/qc.tsx` QC 探针 → ⑦ `src/Root.tsx` 注册 composition。以本仓 `src/design` 为参考实现移植；移植后**数值仍从 `tokens.ts` 读取**，不回填进 skill。

## 0. 六条铁律

1. **信息区默认在左，人物在右**：信息区默认在左（用户裁定的作者默认）、HUD 锚定左侧竖向生长、人物区禁入；但**每片构图先问用户、别自作主张**，三区坐标与 takeover 例外机制见 references/layout.md 规则 1。
2. **一切文字双层结构**：英文 UPPERCASE 宽字距 kicker（小）+ 中文粗黑（大）。只有一层文字的组件视为未完成。
3. **一句话只高亮一个词**：中文标题里换色/强调词最多一处，颜色必须取自四色语义系统。
4. **真素材为主体，Remotion 是合成器不是绘图板**（2026-07-16 seg01 定案升级）：「产品体验」类画面（打字/生成/界面/演示）一律真素材剪辑——自录屏 > 官方视频 > 网页截图 > UI 模拟卡；手绘只做 HUD 层（侧标/字幕/图表/印章/比喻图形）。用 CSS 手搓专业 motion 团队的作品必败，「怎么调都差点意思/差很远」的根源就是拿绘图板打合成器的仗。采集与剪辑管线见 assembly references/broll.md。
5. **亮面禁裸字**（2026-07-16 深度对比裁决，横跨 6 个板块的头号跨界规则）：亮背景（白板/白墙/浅色接管底）上禁止无底文字——一切文字必须坐在深色底板（SURFACE.darkPlate）、卡体或 light 表面变体上，textShadow 不算方案。细则见 references/texture.md。
6. **一屏一个主导层**：每个信息屏有且只有一个「最大字/最大件」，主区之外最多 2 个芯片级小元素。细则见 references/typography.md 与 layout.md。

## 1. Design Tokens

**唯一真源 = `src/design/tokens.ts`，所有组件只允许 import 那里的值。本节只写语义与使用规则，不抄数值——此前快照与代码漂移过一次（2026-07-16 发现 kicker/h1 等多处对不上），以代码为准。**

- **四色语义**（唯一允许的强调色）：blue=定义/方法/中性推进；green=正面/低门槛/已生效；yellow=机会/警示/争议/转折；red=负面/陷阱/危机。基础色另有 white/grey/greyDim/cardBg/cardStroke。
- **字体**（分两层，别混）：**MG 包装层**——`FONT.zh`=Noto Sans SC（包装层中文唯一字体，标题一律 `FONT.zhHeavy`）；`FONT.en`=Inter（kicker/正文/数字）；`FONT.enTitle`=Archivo Black（英文标题与大字结论，窄方超黑，weight 一律 400——Inter 撑不起大字气势，2026-07 字形对比结论）。**底部字幕层**——`FONT.subZh`=PingFang SC 400 / `FONT.subEn`=Inter 300（2026-07-26 五档实拍对照后用户裁定）：字幕是跟读层不是包装层，细体才有苹果字幕的质感，且与 MG 粗黑标题拉开层次、不抢注意力；旧版整条用 Noto 700 显得像贴纸。**PingFang SC 是 macOS 系统字体，不走 `@fontsource` 打包**——本机渲染没问题，Windows/Linux 环境会回退到打包的 Noto Sans SC 400 细档（fonts.ts 已引入，观感相近但非同款），跨机器渲染前先渲一帧确认字幕观感。字幕英文行必须用比例西文字体，见错题 #42。
- 大字结论一律纯语义色 + textShadow，禁止 backgroundClip:text 渐变字（错题 #06）；`GRADIENT` 仅用于色块/描边类用途。
- **字号**只允许用 `SIZE` 阶梯（kicker / subSmall / chip / subZh / subEn / card / h2 / h1 / mega），禁止阶梯外字号；1080p 基准，4K 输出等比 ×2。
- **间距**一律 `GRID`（8px）的倍数；圆角用 `RADIUS`；安全区用 `SAFE`（侧标锚点、堆栈左缘、字幕距底；常驻卡不越 x55%，人物禁入区/右区坐标见 layout.md；字幕禁区 y>82%，左区元素底边 ≤y840 是比 y82% 更严的左区硬线）。

## 2. 章节侧标 SideLabel（全片常驻，最高优先级组件）

- 结构：`│`（4px 竖线，语义色）+ `ENGLISH KICKER · 中文短语`（第一行，英文用 kicker 规格+语义色，中文白色 34px）+ 第二行灰色 24px 补充说明。
- 位置：固定 `SAFE.sideLabel`，切换时旧标签淡出 12 帧、新标签左滑入 15 帧。
- 命名带编号体系：`SCENE 01`、`PATH 1/2/3`、正反对仗（`DISSOLVED·01..` vs `IMMUNE·01..`）。
- 颜色 = 本段情绪语义，见 tokens 注释。参考：`refs/01-版式与侧标/`。

## 3. 组件规格速查（详规格随实现补充，先看参考图再写）

| 组件 | 关键规格 | 参考 |
|---|---|---|
| BilingualSub | 中 52 白+黑影 / 英 28 纯白，底部居中，永远在最上层 | 任意 refs |
| HeroText | kicker + 中文 h1/h2，高亮词换语义色；变体：红删除线纠偏、黄笔刷下划线、倾斜印章 | refs/02 |
| Chip | 黑卡 RADIUS.chip + 彩色图标 + 34px 文字，可一处换色词 | refs/03 |
| Checklist | Chip 纵向堆叠，逐条弹入；未激活条目 opacity 0.35 | refs/03 |
| InfoCard | 图标 + kicker + 44px 标题 + 蓝色高亮词 | refs/01 |
| StepList | ①②③圆圈编号 + 中文 + 英文小 kicker，逐步点亮 | refs/04 |
| FlowChain | 黑卡 + → 箭头串联，逐节点出现 | refs/04 |
| CompareCard | logo + 名称 + 红 × 弱点 chip + 绿 ✓ 强项 chip，纵向堆叠 | refs/04 |
| Formula | 大字 A 符号 B（>、»、⇄、=），符号用语义色 | refs/05 |
| BigNumber | Inter 大数字 + 单位小字 + kicker；计数器用 spring 滚动 | refs/05 |
| BarChart | 数据条 8px 圆角；重点条变黄 + 顶部皇冠 chip；其余灰 | refs/05 |
| CurveOverlay | 2–3px 黄色曲线直接叠 B-roll，右端点标注 | refs/05 |
| Timeline | 两端点区间型 / 事件挂红绿结果 chip 型 | refs/05 |
| ScoreBoard | 绿:红大数字比分 | refs/05 |
| PhoneMockup | iPhone 外框 + 渐变描边发光 + 内嵌截图长图滚动 | refs/06 |
| WindowCard | mac 红绿灯 + app 图标 + 功能 chip，内容动态 | refs/04 |
| QuoteDoc | 白底截图卡 + 黄荧光高亮 + 黑底中文译条浮层 | refs/07 |
| TweetCard | 头像 + 身份 kicker + 红色大字结论 + views chip | refs/07 |
| PersonCard | 圆头像 + 名字 + 身份小字 + 机构 chip | refs/07 |
| Stamp | 倾斜 -8°~-6° 描边印章字（红/绿），盖章动画=scale 1.3→1 + 轻震 | refs/08 |
| MatrixIcon | 方块矩阵图标：红=会被溶解阵营 / 绿=免疫阵营 | refs/08 |
| CardWall | 白色小卡 3→20 张逐张铺满，模拟需求爆炸 | refs/06 |
| BeforeAfter | 两个图标卡 + 蓝色箭头 + 下挂结论 chip | refs/04 |
| Breathe | idle 微动效包装器：呼吸 scale ±0.6% + 浮动 ±3px，`phase` 错开相位防同步；包在主角元素外层 | src/design/Breathe.tsx |
| BrickWall | 错缝金砖横墙逐块砌起 + 中央标签，「建墙/硬性门槛」比喻 | src/design/BrickWall.tsx |
| UnitMatrix | N 组方块矩阵逐格点亮；`fillRatio` waffle 模式（73% 数据场） | src/design/UnitMatrix.tsx |
| CloneCascade | 源图标卡 + 仿品依次淡入 + 警示 chip，「被抄袭/蒸馏」比喻 | src/design/CloneCascade.tsx |

### 批量线 Scene 内联件（2026-07-17 批量生产新增，尚未提升共享件）

下列件当前只活在单个 Scene 里，标注「**Scene 内联，第二次复用时提升 src/design 共享件并补 specs 规格行**」——写新片撞到同类需求时先查这里，别重造：

| 内联件 | 位置 | 做什么 | 提升条件 |
|---|---|---|---|
| DissolveGrid | scenes/Scene08.tsx | 溶解网格：会被溶解阵营方块逐格溶散、中央 ⚡ 底板淡出后白轮廓悬空 | 第二次「阵营溶解」比喻复用时 |
| VerdictBox（决算框） | scenes/Scene17.tsx | 红绿镜像决算框：≈400×170 描边空框先立 + 框内 header + 横排 3 chip 分批入框（红先满绿后满，制造「你站哪边」悬置） | 第二次「VS 决算」升格时 |
| NamePlate + CtaBadge（CTA 徽章排） | scenes/Scene19.tsx | 片尾 CTA 底部一条横排：名牌先落定当锚点 → 四动作徽章逐枚弹入（评论徽章末位最宽=强调） | 第二次片尾 CTA 收尾时 |

### 图标规范

- 图标一律用 **lucide-react** 线性 SVG 图标，颜色取语义色（`COLOR[accent]`），`strokeWidth 2.5` 左右；**禁止 emoji**（彩色圆角块与基准片的单色线性风格冲突，2026-07 第三批验收教训）。
- Chip / Checklist / SideLabel 的 `icon` prop 均接受 ReactNode：`icon={<Lock size={26} strokeWidth={2.5} />}`。

### 质感规范 → references/texture.md

果冻块渐变、同色 glow、vignette、真 logo、SURFACE 亮暗变体、印章规格唯一线全部在 texture.md（2026-07-16 起它是质感唯一真源，本节旧文已迁走）。

## 4. 动效规则 → references/motion.md

useEnter/useExit、分拍入场、服役区间、Breathe、章间净屏、禁止项全部在 motion.md（2026-07-16 起它是动效唯一真源，本节旧文已迁走；注意旧规则「旧信息降透明常驻」已被「服役区间+退场纪律」取代）。

## 5. 导出前自检（每次渲染前跑一遍）

1. grep 检查是否有组件内联了 tokens 之外的色值/字号/字体。
2. 所有常驻卡是否越过 faceZone / subtitleZone。
3. 每句标题高亮词是否 ≤ 1 处；英文 kicker 是否全大写加字距。
4. 截取 3–5 个关键帧与 refs/ 对应参考图并排对比，不像就说明差在哪一条 token，改 token 不改组件内联。

## 6. 错题集

### #01 中文静默退化成宋体（2026-07-15 · 设计系统首日）

- **症状**：渲染/截图里中文变宋体，英文正常；同一组件有时正常有时不正常（看运气）。
- **原因**：三层，最后一层才是真凶。① `@remotion/google-fonts` 运行时从 gstatic 拉字体，国内网络拉不到，静默 fallback；② 中文 webfont 按 unicode-range 分包，加载与截图有竞态；③ **树摇**：`package.json` 的 `sideEffects: ["*.css"]` 使只被副作用导入的 `fonts.ts` 在生产打包时被整个剔除，字体 CSS 根本不在渲染 bundle 里（`document.fonts.size === 0`）——Studio 开发模式不树摇，所以「Studio 正常、渲染翻车」。
- **修法**：① 字体走 `@fontsource` 本地包（`src/design/fonts.ts`）；② `package.json` 的 `sideEffects` 必须包含 `"src/design/fonts.ts"`；③ 任何含文字的合成挂 `<FontGuard/>`：load→check 循环验证，且必须同查 `document.fonts.size > 0`（**`fonts.check()` 在零字体注册时会空洞返回 true**），超时直接 cancelRender 报错，绝不静默出宋体帧。
- **教训**：「Studio 正常、导出翻车」优先怀疑生产打包差异（树摇/压缩），不是玄学竞态；验收字体必须靠 FontGuard 硬门槛，人眼靠不住缩略图。

### #02 `remotion still` 输出「○」= 复用旧图

- **症状**：改了代码重渲，输出文件看起来毫无变化；命令行显示 `○` 而不是 `+`。
- **修法**：验收渲染前先删旧输出（或渲到新文件名）；必要时加 `--bundle-cache=false`。`+`=真渲染，`○`=可疑。
- **教训**：对比验收必须基于确认新鲜的渲染产物，否则会误诊「修复无效」（本次因此多绕了两轮）。

### #03 缩略对比图会骗人

- **症状**：并排对比小图里中文看着像宋体，原图实际正常。
- **修法**：判断字体/描边细节时必须裁切原分辨率局部放大看，不要用整帧缩略图下结论。

### #04 JSX 属性字符串不解析 `\uXXXX` 转义

- **症状**：`<Chip icon="\u2705" />` 画面上显示字面 `\u2705` 而不是 ✅。
- **原因**：JSX 属性的字符串字面量是 HTML 式文本，不走 JS 转义解析；只有 JS 表达式里的字符串（`icon={'\u2705'}`）才解析转义。用脚本批量写 TSX 时最容易踩。
- **修法**：emoji/特殊字符在 JSX 属性里直接写真字符（`icon="✅"`）；确需转义时写成 `icon={'\u2705'}`。

### #06 `backgroundClip: text` 渐变字渲染发暗

- **症状**：大字标题用 backgroundImage 渐变 + WebkitBackgroundClip:'text' + WebkitTextFillColor:'transparent'，Studio 里尚可，渲染出图颜色发暗发闷（亮红变砖红），用户一眼否掉。
- **修法**：大字结论一律纯语义色 `COLOR[semantic]` + textShadow；想要层次感靠阴影和字重，不靠渐变填充。tokens.GRADIENT 仅留给色块/描边类用途。

### #08 成片 MG 文字边缘晕影、涂抹感（「加了 MG 画质变差」）（2026-07-16 · 0715-01 v3）

- **症状**：用户看成片说画质差；放大看 MG 文字边缘有 JPEG 蚊噪/晕影，越锐利的元素越明显。素材本身 15 Mbps HEVC 很干净。
- **原因**：Remotion 默认管线双重压缩——每帧用质量 80 的 JPEG 截图，再以 CRF 18 压 H264。MG 大字/细线是高频信号，最先出压缩伪影。加 MG 前伪影藏在实拍纹理里不显眼，所以被误诊为「MG 导致画质差」。
- **修法**：`remotion.config.ts` 固化 `Config.setJpegQuality(100)` + `Config.setCrf(15)`（本项目已设，勿回退）。体积约 +20%，渲染略慢，值得。
- **诊断法**：同一帧从素材/旧成片/新参数测试段各截一张，裁同一 MG 文字区域放大并排看；先渲 5 秒测试段验证参数再渲全片。

### #09 长渲染中途消失、mp4 成残片（2026-07-16 · 0715-01 v3）

- **症状**：渲染跑了很久后「进程还在」但产物文件长时间不增长；或渲染无声无息消失，留下打不开的 mp4。
- **原因**：① 渲染挂在 AI 会话的子进程里，会话重启/退出连带杀掉渲染（本次在 90% 处被杀）；② 检测进程用 `pgrep -f "remotion render"` 会匹配到检测脚本自身（命令行里含同样字符串），造成「进程还活着」的假象。
- **修法**：① 超过几分钟的渲染一律 `nohup npx remotion render … > /tmp/xx.log 2>&1 & disown` 脱离会话；② 完成判据认日志里的 `+ 输出文件名` 行（`+`=真渲染成功），不认进程存在性；③ 检测进程要排除自匹配（看 CPU 占用或用精确 PID）；④ 重渲前删掉残片。
- **教训**：残片 mp4（时长/体积对不上）绝不交付，先 `ffprobe` 验时长与音轨再给用户看。
