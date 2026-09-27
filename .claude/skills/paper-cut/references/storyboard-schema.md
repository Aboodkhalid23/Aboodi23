# Storyboard and project schema

## Project state

```json
{
  "schemaVersion": 1,
  "slug": "example",
  "stage": "storyboard-review",
  "video": {"width": 1920, "height": 1080, "fps": 30, "durationSeconds": 50, "language": "zh-CN"},
  "style": {"mood": "editorial, tactile", "palette": [], "paperTreatment": ""},
  "approvals": {
    "storyboard": {"approved": false, "note": "", "at": null},
    "assets": {
      "approved": false,
      "note": "",
      "at": null,
      "providers": {},
      "attemptCaps": {"image": 0, "voice": 0, "video": 0, "sound": 0},
      "attemptUsage": {"image": 0, "voice": 0, "video": 0, "sound": 0}
    },
    "preview": {"approved": false, "note": "", "at": null}
  },
  "scenes": []
}
```

## Scene record

```json
{
  "id": "scene-01",
  "start": 0,
  "duration": 4.8,
  "purpose": "state the mechanism",
  "voiceover": "旁白原文",
  "heroFrame": "可直接用于生图的完整构图说明",
  "background": "scene-01-cleanplate",
  "fixedElements": ["environment", "decorative-clouds"],
  "movingLayers": ["sun", "heat-waves"],
  "onScreenText": ["为什么这么热？"],
  "motion": {"hero": "sun drops", "secondary": "heat waves reveal", "camera": "slow push 4%"},
  "transition": {"type": "overlapping-paper-push", "duration": 0.35},
  "safety": "no sensitive geographic boundary"
}
```

Scene starts must be monotonic, durations positive, and the full composition long enough to contain every scene. Keep 0.1–0.3 seconds before the first entrance. Plan build, breathe, resolve, and transition phases. Earlier scenes exit through their transition; only the final scene may use a deliberate final exit.
