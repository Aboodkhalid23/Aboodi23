---
name: remotion-gotchas-index
description: 错题集：症状→修法索引，短修法行内、长修法指向专业 skill。渲染异常、画面不对、排版翻车时先查。触发词：错题、翻车、坑。
---

# 错题集索引（症状 → 修法位置）

> 规则：每条坑修复并经人眼验收后立案。修法有专业 skill 归属的写进该 skill、此处只留指针；**无专属归属的（工程工作流/渲染管线类）允许行内存短修法**（查坑时一眼到修法，免二跳），但超过五行须落到专业文件再改回指针。本文件不超 150 行，超了先把最长的行内修法搬家。

**同族导航（先定家族再查条目，防在近亲条目间来回跳）**：
- **渲染卡死/挂起/消失族**：先跑 `render-service.cjs` 起跑自检（2026-07-24 起自动拦 #37 public 体积、#38 签名挂死、chrome 打不开自动兜底系统 Chrome）；自检过了还挂 → 按 #23 并发死锁 → #25 dataless → #26 harness 回收 → #24 npm 坏包排查。
- **QC 假阳族**：#29 幽灵盒（null 门控）/ #31 冷启动字体虚胖（qcAllow 豁免）/ #32 Place 盒撑高（目视判假放行）；QC 报「零违规」先看覆盖率（#35）。

| # | 类别 | 症状 | 修法位置 |
|---|---|---|---|
| 01 | 画面渲染 | 中文静默变宋体 / 时好时坏 | remotion-design-system §6 #01（fonts.ts + FontGuard） |
| 02 | 工程工作流 | `remotion still` 输出 ○，改代码后图不变 | remotion-design-system §6 #02 |
| 03 | 工程工作流 | 缩略对比图误判字体细节 | remotion-design-system §6 #03 |
| 04 | 画面渲染 | JSX 属性里 `\uXXXX` 按字面显示（如 icon="✅"） | remotion-design-system §6 #04 |
| 05 | 设计语言 | 组件自绘占位复刻「感觉差不少」 | remotion-design-system §0 铁律 4（真素材为主体） |
| 06 | 画面渲染 | backgroundClip:text 渐变字出图发暗 | remotion-design-system §6 #06（纯色+textShadow） |
| 07 | 设计语言 | 纯平色块/纯平黑底/假 logo 显廉价 | remotion-design-system references/texture.md（果冻块+glow+暗角+真 logo） |
| 08 | 导出 | 成片 MG 文字边缘晕影/涂抹，「加了 MG 画质变差」 | remotion-design-system §6 #08（jpeg100+crf15 固化 config） |
| 34 | 设计审美 | 用户说「不高级 / 粗糙 / 像失误 / 不自然 / 不连贯 / 不丝滑」 | design-system references/motion.md「丝滑感五律」——归因表：①预铺骨架（未讲到的结构提前显形）②为避让把连续物切碎③边界穿过或悬空留缝（>2px 即断开）④等速运动无减速停靠⑤状态瞬时整体突变。逐条对号入座，禁凭感觉调参数；改一条注意别踩另一条（0722-01 修「线不穿圆」时踩了「切碎」+「露骨架」，返工两轮） |
| 09 | 工程工作流 | 长渲染中途消失 / mp4 残片 / pgrep 误判进程还活着 | remotion-design-system §6 #09（nohup 脱离 + 认日志 `+` 行） |
| 10 | 长片装配 | 画面裸奔/长时间静止、MG 全缩左区没气势 | remotion-design-system references/layout.md（takeover/主角时刻）+ remotion-assembly references/rhythm.md（密度审计） |
| 11 | 音效 | 全片无声效 / 音效被埋听不见 / 响度不达标 | remotion-assembly references/audio.md（音量规范+母带 loudnorm） |
| 12 | 长片装配 | 元素进场后一动不动显死板 / 章节一帧硬切消失 | remotion-design-system references/motion.md（Breathe + useExit 退场纪律） |
| 13 | 设计语言 | 亮背景上文字发灰不可读（裸字压白板） | remotion-design-system §0 铁律 5 + references/texture.md |
| 14 | 长片装配 | 左上角标头/眉线叠字 | remotion-design-system references/layout.md（标头互斥占位） |
| 15 | 字幕 | 字幕词内断裂 / 英文碎片 / 无底衬 | remotion-assembly references/subtitle.md（语义断句+底衬箱+校验脚本） |
| 16 | 素材抓取 | 手绘复刻产品画面「怎么调都差很远」 | remotion-assembly references/broll.md §0 总纲（合成器不是绘图板；素材四级+采集剪辑管线） |
| 17 | 长片装配 | AI 自查说很像、用户一看差很远（静帧盲区/目测缩水） | remotion-assembly SKILL §2.5 分段工坊（先测量后写码+用户动态终审） |
| 18 | 素材抓取 | 素材段像「贴片」融不进正片 | remotion-assembly references/broll.md 管线第 5 步（调色统一层） |
| 19 | 动画时序 | 全片入场拖沓像 PPT / 动效时长与设计不符 | remotion-design-system references/motion.md §0（帧数按 60fps 口径写而合成是 30fps，先秒后帧换算） |
| 20 | 设计语言 | 装配尺寸「怎么调都比参考小」 | remotion-design-system references/specs.md（先查规格表再写码，禁止目测） |
| 21 | 音效 | 音效廉价感/发虚，合成与参考片采样两路全被否 | remotion-assembly references/audio.md 规则 8（正解=专业音效库：剪映缓存盘库→@remotion/sfx→Mixkit→CC0→商用包；质感必须用户过试听板挑编号，AI 只能筛频谱硬伤） |
| 22 | 工程工作流 | 试听板/拼接视频越往后音画对不上 | remotion-sfx SKILL §2 拼接铁律（禁 `-c copy` 拼接与 `-shortest`：段长微差累积成漂移，必须锁死等长+整条重编码） |
| 23 | 工程工作流 | 渲染莫名挂起/超时，反复重试反复挂 | 同项目渲染禁并发（预警雷区「并发崩」实锤）：多会话/孤儿进程互撞死锁。诊断=`ps -o etime,pcpu`（etime 超预期数倍+持续 0% CPU=僵死，杀）；工具超时只杀 bash 会留孤儿 node 连环撞，渲染必须 nohup 真后台+认日志 `+` 行（错题 #09 同族）；起渲前先查场，**但查场模式必须防自匹配**：`pgrep -f "remotion render|render-service"` 会匹配到「正在等渲的那条 shell 自身」（命令行含同样字符串），多 agent 并行时互相看见对方的等待进程 → **全体死锁空等，实际根本没有渲染在跑**（2026-07-23 0722-01 四路并行实锤）。正确写法用字符类打断自匹配：`pgrep -f "render-servic[e].cjs"`，并排除 zsh/bash（`pgrep -f ... | xargs ps -o comm= | grep -v -E "zsh|bash"`）。查场结果存疑时以「有没有新帧产出/日志在长」为准，别只信 pgrep；机器负载（iCloud 同步/重型 App）也会把 1 分钟渲染拖到 7 分钟，杀前先看 uptime 负载 |
| 24 | 工程工作流 | 渲染报 `Named export not found`/`plugin is not a function` 等包内部错 | npm 并发安装可致包损坏（多会话同时 npm i / 进程互杀中断写盘）：症状=require 返回空导出、依赖树内部 TypeError；修法=坏包 `rm -rf node_modules/<包>`+`npm cache clean --force`+重装，多处腐坏直接 `rm -rf node_modules && npm ci`（先把 node_modules/.remotion 浏览器二进制挪出保住再删）；纪律=同项目同时只允许一个会话动 npm |
| 25 | 工程工作流 | 渲染永久卡在 Bundling 固定百分比、进程树全 0% CPU、换 Node/重装依赖都无效 | **素材文件被同步盘驱逐成 dataless 空壳**（2026-07-16 血案：第三方同步 App 卸载时把 747MB 主素材驱逐，bundle 复制 public/ 读文件永久阻塞，全晚渲染连环挂）。诊断=`ls -lO public/**` 看 `dataless` 标志；修复=从原件/下载源恢复实体（brctl 对已卸载 provider 无效）；预防=素材入库验真加查 dataless（broll.md 2b）、项目不放同步盘管理目录。**变体（2026-07-28，iCloud 驱逐 node_modules）**：CLI/Studio 启动即 0% CPU 静默挂死、连版本号都打不出（「优化 Mac 存储」驱逐依赖文件，@remotion 包内近万 dataless，require 逐文件等云端下载）；修法=依赖重装进 `node_modules.nosync/` 实体目录+同名软链（`*.nosync` 命名 iCloud 不同步，根治复发）；旧目录**必须移出项目树**（进 `../.trash/`）——改名留在项目内会被 Studio watcher 递归扫描、二次挂死 |
| 26 | 工程工作流 | 渲染进程随子代理/agent 回合结束「凭空消失」，既非并发死锁（#23）也非长渲染中途断（#09） | 子代理回合一结束，harness 会回收它在前台或未完全脱离的子进程链→渲染半途被杀留残片。修法属 #09 族：起渲必须完全脱离父 shell（nohup + run_in_background/`setsid`、重定向所有 fd），判完成只认日志 `+`/尾行不认 agent 是否还活着；子代理内起长渲染尤其致命（回合边界＝进程死期），必要时拆「本回合起渲脱离 → 下回合认日志」两步 |
| 27 | 工程工作流 | 渲染服务 `.mjs`/ESM 入口 `import '@remotion/renderer'` 报 `does not provide an export named 'Fragment'` | package.json 无 `type:module` 时用 ESM 入口加载 renderer 会触发其 ESM 构建的 react/jsx-runtime 互操作断裂（Node 24 实锤）；修法=服务脚本改 `.cjs` + `require` 走 CommonJS 构建绕开（证据：scripts/render-service.cjs 顶注） |
| 28 | 工程工作流 | `<Sequence layout="none" premountFor={N}>` 过 tsc 报 premountFor 不存在/类型不匹配 | Remotion `SequenceProps` 是判别联合：`premountFor` 只在默认/`layout:"absolute-fill"` 分支（`AbsoluteFillLayout`）合法，`{layout:"none"}` 分支无此属性（类型见 node_modules/remotion `Sequence.d.ts` 的 `LayoutAndStyle`）。修法=要 premount 的媒体必须包在默认布局 Sequence 里（不写 layout 或写 `absolute-fill`）；需 `layout="none"` 定位时把该媒体单独嵌一层默认布局 Sequence 承接预挂载。承官方雷区 ③（premountFor）实操衍生 |
| 29 | 工程工作流 | QC 探针报「幽灵重叠」假阳：当帧该元素肉眼根本看不见 | QC 探针（`src/design/qc.tsx`）逐帧对 `[data-qc]` 取 getBoundingClientRect 判重叠；元素不可见期若仍挂在 DOM（非标准隐藏或全不透明但视觉已让位），rect 照样在→报假重叠（seg05 S5Appear 命中）。探针侧只过滤 opacity<0.15 与 w/h<3，占位型幽灵挡不住。修法=元素不可见期组件直接 `return null`（null 门控法），无节点即无 rect；防重叠占位规则详见 remotion-design-system references/layout.md §10.5。另一变体（Place 盒撑高）已单列 #32，修法以 #32 为准 |
| 30 | 工程工作流 | Bash 写的文件「命令成功」但转眼消失 / Read 看不见刚生成的文件 / 渲完的成片 ls 不存在 | 新会话默认沙箱执行：未授权的 Bash 写入落在沙箱临时副本、命令结束即蒸发（0719-01 测试实锤：字幕数据、18 个 Scene、590MB 成片全部蒸发，只有 Write 工具写的 3 个文件存活）；经 /tmp 软链路径写项目会加剧重定向。修法=开工前必过 assembly SKILL §0.5 第 0 步环境自检，不过即停、让用户授权 Bash/编辑权限后再开工；**禁止**软链绕中文路径（路径整体加双引号即可）、禁止 dangerouslyDisableSandbox 自救、禁止把项目复制到 /tmp 干活；文件产物一律优先用 Write 工具写 |
| 31 | 工程工作流 | QC 仅在段首几帧报重叠、目视无叠（常见 sub-zh × 卡框） | 冷启动首几帧字体未加载、文字盒按回退字体测量虚胖上撑，rect 相交属测量假阳（0715-01 seg03 与 0715-02 S04 两次实锤，#29 幽灵家族变体）。修法=目视核清后 `qcAllow` 白名单豁免该元素对（其余断言保留），勿为几帧假阳改布局 |
| 32 | 工程工作流 | 全片 QC 报大批 `place@72,*` 左区盒重叠、渲帧目视元素并不叠 | 分页式/编组左区 Place 盒 bounding 高于视觉内容（容器撑高），盒相交≠视觉相交（0715-02 全片 QC 15 类违规抽查全为此类）。修法=渲帧目视判假后放行；根治=Place 盒高度贴实际内容或该组挂 qcAllow；sub-clearance 越净空线另判真伪，不在此列 |
| 33 | 画面渲染/导出 | 成片某段人物/视频冻成静帧、原片同段在动（4K 铺底多发）；肉眼看是「人物不动」，但 md5/mpdecimate 查不出 | 4K 铺底 OffthreadVideo 渲染时解码卡顿吐重复帧（叠加复杂 SVG 动画段更易触发）→ **转 1080p H264 铺底源**（合成本就 1080p，4K 纯浪费还拖垮解码），主组件改引 1080p 源重渲即解。诊断**必用 `ffmpeg -vf freezedetect=n=-50dB:d=0.3`**——md5 全不同 ≠ 画面在动（静止帧的压缩噪声也让每帧 md5 不同，会骗人）、mpdecimate 同样被噪声干扰不可靠，只有 freezedetect 有噪声容差才准；素材接管段（人物退场、素材卡本身静止）报 freeze 属正常、非 bug（0721-01 实锤：63-69s 人物段冻帧，4K→1080p 源后 freezedetect 零冻结）。附：交付编码建议 `-bf 0 -g 30 -movflags +faststart` 提升播放器兼容（Remotion 默认大量 B 帧，部分播放器 seek 时解码卡顿） |
| 34 | 画面渲染 | 素材段成片卡内大面积纯黑/死黑条/空玻璃、只剩边缘一条竖条；占位与真素材都会中招；渲后自审还容易漏（抽帧点没落在素材在场窗口） | OffthreadVideo「超大盒 style width + objectFit/translate」裁切写法渲染端 width 不生效→内容按卡宽渲染再被位移截断（0721-01 六段实锤：S02/S06/S07/S10/S13/S16，唯一正确的 S14 用「video 100% 铺卡 + transform scale 过冲」）。修法与渲后验收闸＝remotion-assembly references/broll.md 规则 12 |
| 35 | 工程工作流 | 集成员/QC 报「全片零违规」但实际有大量重叠——**假过闸** | QC 探针（`src/design/qc.tsx`）挂在每个 Scene 内、只在该段帧范围跑；Scene 漏挂 `<QcProbe/>`（只声明 `qc?:boolean` 却不消费）→ 该段无任何断言→ summary 干净属**假过闸**（0722-01 血案：20 段仅 1 段挂探针，报零违规实则 8 类真违规）。修法已固化：探针每帧发覆盖心跳 `QC{hb:1,n}`，`render-service.cjs qc` 核「覆盖帧数/渲染帧数」，<90% 或全程 0 元素 → 判 `[FAIL] 覆盖不足` 而非「零违规」。纪律：**「零违规」必须能区分「测了没问题」与「根本没测」**；生产模式集成阶段先跑一小段 qc 确认覆盖率达标再全片。**补（2026-07-24 审查发现）**：探针必须**根挂载**（装配根 `{qc ? <QcProbe/> : null}`，如 Koubo072101/072201）——Scene 内挂载时 `useCurrentFrame` 经 Sequence 返回**局部帧**（0 起算），心跳帧号与全局帧范围错位：全片/跨段 QC 覆盖率会假 FAIL（各段局部帧互相重叠、去重后 ≪ 总帧数），单段漏挂也可能被邻段局部帧掩成假 PASS；render-service 已加帧号范围过滤，但全局覆盖只有根挂载能保证。单段 QC 短跑测不出这个坑——**验护栏要用会触发失败的场景测**（跨段范围/故意摘一个探针），别只测正常段 |
| 36 | 设计语言 | 左区信息 MG 文字糊在亮背景上近乎不可读，scrim 像没生效 | `InfoScrim`（`src/design/InfoScrim.tsx`）渐变默认**从左透明→右压暗**，只压右侧；信息 MG 放**左侧**的片（用户裁定左信息）→ 左区 MG 全程裸露在最亮区（白柜/亮墙）无衬底（0722-01 实锤；0715-02 曾撞同坑但只在单段就地打补丁、底座缺口未补）。修法=`InfoScrim` 加 `side` 参数（默认 `'right'` 兼容旧片），信息在左的片传 `side="left"`。**教训：底座缺陷补底座或立案，禁只在单段打补丁——就地补丁＝把坑留给下一片** |
| 37 | 工程工作流 | 渲染卡在 Bundling 出不来，`copyfile ... ETIMEDOUT`，进程活着但无输出 | `public/footage/` 堆多片旧素材（0722-01 时 2GB/6 片），Remotion bundle 每次把整个 public/ 复制进临时目录→copyfile 超时（与 #25 dataless 区分：这是**体积/复制耗时**，文件本身实体存在）。修法=只保留当前片素材在 `public/footage/`，其余移到 `../footage-hold/`（2GB→466MB，bundle 从卡死→1.8s）。**纪律：修复措施交付后别无脑回滚——回滚前问「这片还要再渲吗」**（0722-01 同坑因交付后移回素材踩了两次） |
| 38 | 工程工作流 | 任何碰文件的进程永久挂起、`kill -9` 无效、UE 僵尸越堆越多；重装依赖/换 Node 全无效 | macOS 代码签名校验守护进程（amfid/syspolicyd）挂死→需签名校验的二进制无法 exec（与 #25 dataless、#37 体积、#23 死锁均不同，是**系统级**）。诊断法：`ffprobe -version`（系统）正常但 `node_modules/@remotion/compositor-darwin-arm64/ffprobe -version` 永久挂住 = 签名卡死；`ps -axo pid,stat,comm|awk '$2~/UE/'` 数 UE 僵尸。修法=**只能重启机器**（或 root 杀 amfid/syspolicyd），用户态无解。要点：**早做对照诊断**，别在卡死上反复重试空等（0722-01 当晚为此浪费大量时间） |
| 39 | 素材抓取 | Grok 图生视频三类翻车：默认低分辨率 736×400 放大糊 / 元素自己变形增生(morph) / 特定构图被强行「填补」 | ① **分辨率**：不显式提就走默认 736×400（2.6x 放大糊掉 halftone/裁切边）——指令必写死 720p(1280×720)，实测 4/4 命中；CLI `resolution_name` 只有 480p/720p 两档、请求 1080p 会回退（2026-07-24 实测），1080p 须走 xAI API（grok-imagine-video-1.5）或换工具。② **morph 增生**：齿轮长大/日历多格/圆环碎裂——prompt 末尾追加针对该条易崩元素的锁定约束（「保持单个原尺寸禁增生」「格数颜色不变」「圆环连续不断线」）。③ **硬性补全**：「稀疏元素+大片空背景+空心人形+露脸碎片」触发模型填满空地、填实空洞、长出完整人脸（14 号跑 6 版全崩）——**不要继续加禁令，去改触发它的输入构图**（碎片铺满/负空间用描边界定/去掉露脸碎片，改完一次跑通）。gbro headless 调用还需 `--always-approve --permission-mode bypassPermissions --max-turns 10` 才触发视频工具。详见 remotion-broll SKILL「AI 生成拼贴 B-roll」节 |
| 40 | 画面渲染 | 名牌小圆头像看着歪、金环内露背景楔形，CSS 调角度越调越歪 | **禁在小圆裁窗内用 CSS `rotate`+偏移修头像歪**——旋转绕 img 中心、可视窗又偏离中心，两者叠加放大歪感且旋出露边（0724-01 两轮才修对）。正解=**离线烘图**：PIL 把形象照回正（±几度）后裁「脸居中的正方形」存资产，`NamePlate avatarImgStyle` 用 100%/left:0/top:0 满窗直贴；全局资产 `public/assets/author-avatar.png` 已备，直接引用 |
| 41 | 工程工作流 | render-service segment 全片渲报 `frame range 0-N is not inbetween 0-(N-1)` | segment/splice 的起止参数是**含界帧号**：全片＝`0 (durationInFrames-1)`（1355 帧合成传 `0 1354`），照抄 durationInFrames 必报错 |
| 42 | 设计语言 | 用户说字幕「不够好看」但说不出哪里不对 | 先查**英文行是不是用中文字体渲的**——中文字体的拉丁字形只是补齐用，字宽字距全错，是「说不出哪里怪」的头号来源（`BilingualSub` 旧版 en 行用 `FONT.zh` 渲染，2026-07-26 实锤）。修法＝英文行必须用比例西文字体 `FONT.subEn`（Inter）；顺带查中文行字重，字幕层用 `FONT.subZh`（PingFang SC）400 细体，别用包装层的 700。**判断字体质感必须 1:1 裁局部看，缩略图看不出来（同 #03）**；改版前先出多档同帧对照让用户挑，别自己赌一档 |
| 43 | 长片装配 | qc-master 零 FAIL 零 WARN，用户却说「质感差特别多 / 动效越来越丑 / 字幕跟 skill 说的不一样」 | **技术验收查「片子有没有坏」，不查「片子有没有用上底座」**——两件事，别拿前者的绿灯当后者的证明。0727-01 实锤：25 段自建 324 行 `_kit.tsx` 重造卡片、动效只有 quad 淡入位移 0、`design/motion` 零引用、25 段只有 8 段做了退场，字幕 77 条 en 全空退化成单行中文；qc-master 全 PASS 照放。修法＝装配 ⓪ 闸 `node scripts/check-scenes.mjs src/koubo/scenes-<片名>`（motion 零引用 / 零退场件即 FAIL）+ `check-subs.mjs` 的 en 缺失检查，两道都在写码后起渲前跑。**诊断顺序：先查缺了什么手法，再查参数对不对**——check-scenes 一条命令能看出是不是在重造轮子，但它只覆盖「底座没用上」这一种丑法；配色/节奏/字体/构图各有各的真源（typography/rhythm/#42/layout），别把单条路径当万能诊断。⚠️ 附带教训：当时 `check-subs` 命令参数传错（传片名而非文件路径）报了 ENOENT，**看到报错直接往下走**，于是行首悬挂单字、超宽 16.5 字两条也一起漏了——**校验脚本报错 ≠ 校验通过，跑不起来就是没跑** |

分类参考（按基准片体系预留）：画面渲染 / 动画时序 / Studio 本地运行 / 导出 / 音效 / 素材抓取 / 长片装配 / 设计语言 / 工程工作流。

## 预警雷区（错题目录 44 条，2026-07-16 用户提供截图）

> 规矩：这里是**雷区地图不是错题**——只有症状名、无修法、我们多数未踩。命中任何一条后：修复+人眼验收，再升级为上表正式编号。已与我们既有错题对上号的，直接标了归属。

| 类别 | 的坑（原文） | 我们的状态 |
|---|---|---|
| 画面渲染 | LOGO 频闪 / 视频静帧 / 透明 ProRes 黑边 / 动效锁死左上 / 图片拉伸 / 网页 chrome / 人脸遮挡 / 撞字幕 / Emoji / Logo 黑吃黑 | **已有对应**：撞字幕=#14 叠字；Emoji=#04+图标规范（lucide 真图标）；人脸遮挡=三区人物禁入（layout.md）；Logo 黑吃黑=logo dark/light 双版本规范（texture.md）。其余 6 条未踩，警惕：视频静帧（OffthreadVideo 卡帧）、图片拉伸（objectFit）、网页 chrome（截图带浏览器边框上卡） |
| 动画/时序 | Phase 索引漏 break / 动效对不上口播 / spring overshoot | **已有对应**：动效对不上口播=§2.5 词级对齐+主视觉对 SRT；spring overshoot=motion.md §11 禁止项。Phase 索引漏 break 未踩（switch 分支漏写类问题） |
| Studio/本地运行 | Studio 秒退（SIGPIPE）/ EMFILE 句柄爆 / staticBase hash 过期 / HEVC 黑屏 / id 下划线 / Studio+still 并发崩 | 全部未踩。警惕两条高概率：HEVC 黑屏（iPhone 录屏素材是 HEVC，入库先转 H.264）、Studio+still 并发崩（开着 Studio 时跑 still/render 可能撞车——我们工作流常并发，中招了别先怀疑代码） |
| 导出 | C 盘爆盘 / OOM / 画质糊 / 渲染慢 / Encoded 误判 | **已有对应**：画质糊=#08（jpeg100+crf15）；Encoded 误判=#09 完成判据只认日志 `+` 行（同类：日志字样≠成功）。OOM/渲染慢未踩（长片 4K 时警惕并发帧数） |
| 音效 | impact-heavy 满全片 / 群组各配 whoosh / 音在前动在后 | **已有对应**：impact-heavy 满全片=audio.md 重锤 SFX 全片 ≤2 处（用户否决开场 whoosh 同源教训）；群组各配 whoosh=连击应逐 item 轻 pop 而非每组一记重音。「音在前动在后」未踩，存疑待核（疑指 SFX 帧与动效帧错位的时序规矩，命中时再定义） |
| 素材抓取 | yt-dlp 403 / fetch 不走代理 / Wikimedia GFW / Firefox cookie / PNG 实是 HTML | 部分已有：yt-dlp 采集管线在 broll.md（我们下载 Lovable 未遇 403，遇到时先加 cookie/UA/代理三件套）。「PNG 实是 HTML」典型坑：下载的"图片"其实是防盗链返回的 HTML 页——**入库前 `file` 命令验真**，这条直接采纳为素材管线固定步骤 |
| 长片装配 | 章节没呼吸口 / Host 卡↔Chip 撞 | **已有对应**：章节没呼吸口=motion.md §1/§2 章间净屏；Host 卡↔Chip 撞=layout.md 规则 9 互斥占位（同类叠压） |
| 设计语言 | 不复刻 House Style / kicker overclaim / 长宽比没算 / 字幕复读 | 不复刻 House Style=我们整个 design-system 的存在理由。kicker overclaim（kicker 文案夸大到口播没说的程度）、长宽比没算（素材变形）、字幕复读（字幕与 MG 文字重复念同句）三条未踩——字幕复读警惕：我们判词 chip 与 Stamp 不重复的裁决是同一原理 |
| **官方雷区**（remotion-dev/skills 明文，2026-07-16 对照产出，详见 docs/官方skills对照.md） | ① CSS transition/animation/Tailwind 动画类=渲染必坏（官方 FORBIDDEN，派 codex 写码最易混入）② ffmpeg 裁剪不重编码=片头冻帧（基准片「视频静帧」成因之一，`-c copy` 裁剪禁用）③ 含媒体的 Sequence 不加 premountFor=首帧卡顿/黑帧 ④ @remotion/transitions 吃总时长（两景交叠，SRT 硬对齐体系会全片错位）⑤ fetch 外部数据不包 delayRender=渲出空帧 | ①②④⑤未踩，写码前置检查项；③ premountFor 已按规采用（Scene06 防首帧黑）→ 实操衍生新坑 **#28**（premountFor 与 `layout='none'` 类型互斥） |
| 工程工作流 | 修改范围扩大 / 字号<48px / 自动跑 4K render | 修改范围扩大=分段工坊「只渲该段/只改该段」纪律的反面教材；字号<48px（1080p 下小于 48px 的正文观众读不到，与 specs.md 最小说明字 20-22px 需区分场景：他指的应是信息主体）；自动跑 4K render（未经确认自动起大渲染烧机器）——这条直接采纳为纪律：**渲染只按用户/方案确认的范围起** |

