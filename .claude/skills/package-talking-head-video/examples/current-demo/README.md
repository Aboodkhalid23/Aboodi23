# 当前渲染示例

这是三版式工作流的合成示例：8秒、1920×1080、30fps，使用几何图形代替人物，配一条测试音轨。字幕是示例文案，不涉及真实人物、平台能力或业务效果。

在仓库根目录执行：

```bash
npx tsx scripts/make-current-demo.ts
npm run verify:lite -- .tmp/current-demo-source/input.mp4 examples/current-demo/input.srt .tmp/current-demo-render examples/current-demo/direction.json
```

生成标题、侧卡、流程三种版式截图，dark/paper两种配色截图、测试MP4与检查记录。第二次运行请更换输出目录；工具不会覆盖已有测试视频。

README展示的图片复制自 `layout-title.png`、`layout-card.png`、`layout-flow.png` 和 `paper.png`；简笔画示例复制自第一段的中段截图。它们由当前项目渲染器实际生成，图片哈希记录在 `preview-manifest.json`。几何源画面与测试MP4留在被Git忽略的 `.tmp/` 中。

真实口播需要准确同步的SRT与人物位置检查，合成示例不能代替真人成片验收。
